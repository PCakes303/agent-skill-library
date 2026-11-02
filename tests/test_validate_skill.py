import json
import tempfile
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from tools.validate_skill import SkillValidationError, validate_package

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "echo"

class SkillValidatorTests(unittest.TestCase):
    def test_example_is_valid(self):
        result = validate_package(EXAMPLE)
        self.assertEqual(result["result"], "valid")
        self.assertEqual(result["steps"], 1)

    def make_package(self, mutate=None, raw_workflow=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        target = Path(temp.name)
        resource = json.loads((EXAMPLE / "resource.json").read_text())
        workflow = json.loads((EXAMPLE / "workflow.json").read_text())
        if mutate:
            mutate(resource, workflow)
        (target / "resource.json").write_text(json.dumps(resource), encoding="utf-8")
        (target / "workflow.json").write_text(
            raw_workflow if raw_workflow is not None else json.dumps(workflow), encoding="utf-8")
        return target

    def test_resource_workflow_identity_must_match(self):
        path = self.make_package(lambda r, w: w.update(skill_id="other.skill"))
        with self.assertRaisesRegex(SkillValidationError, "identity/version"):
            validate_package(path)

    def test_resource_must_be_skill_kind(self):
        path = self.make_package(lambda r, w: r.update(kind="tool"))
        with self.assertRaisesRegex(SkillValidationError, "kind"):
            validate_package(path)

    def test_semantic_version_required(self):
        path = self.make_package(lambda r, w: r.update(version="latest"))
        with self.assertRaisesRegex(SkillValidationError, "semantic"):
            validate_package(path)

    def test_step_ids_must_be_unique(self):
        def change(r, w):
            w["steps"].append(dict(w["steps"][0]))
        path = self.make_package(change)
        with self.assertRaisesRegex(SkillValidationError, "duplicate step"):
            validate_package(path)

    def test_step_limit(self):
        def change(r, w):
            w["steps"] = [dict(w["steps"][0], id=f"step-{i}") for i in range(51)]
        path = self.make_package(change)
        with self.assertRaisesRegex(SkillValidationError, "steps"):
            validate_package(path)

    def test_unknown_action_rejected(self):
        path = self.make_package(lambda r, w: w["steps"][0].update(action="shell.exec"))
        with self.assertRaisesRegex(SkillValidationError, "steps.0.action"):
            validate_package(path)

    def test_tool_step_requires_adapter_and_capability(self):
        path = self.make_package(lambda r, w: w["steps"][0].pop("adapter_id"))
        with self.assertRaisesRegex(SkillValidationError, "adapter_id"):
            validate_package(path)

    def test_every_step_requires_policy(self):
        path = self.make_package(lambda r, w: w["steps"][0].pop("policy"))
        with self.assertRaisesRegex(SkillValidationError, "policy"):
            validate_package(path)

    def test_declared_permissions_must_cover_requested_scopes(self):
        path = self.make_package(lambda r, w: r.update(permissions=[]))
        with self.assertRaisesRegex(SkillValidationError, "omit requested"):
            validate_package(path)

    def test_human_approval_requires_prompt(self):
        def change(r, w):
            w["steps"][0] = {"id":"approval","action":"human.approval","policy":{"action":"approve","resource":"task","scopes":[]}}
        path = self.make_package(change)
        with self.assertRaisesRegex(SkillValidationError, "prompt"):
            validate_package(path)

    def test_duplicate_json_keys_rejected(self):
        raw = '{"workflow_version":"1.0","workflow_version":"1.0","skill_id":"example.echo.workflow","skill_version":"0.1.0","steps":[]}'
        path = self.make_package(raw_workflow=raw)
        with self.assertRaisesRegex(SkillValidationError, "duplicate JSON"):
            validate_package(path)

    def test_non_finite_numbers_rejected(self):
        raw = '{"workflow_version":"1.0","skill_id":"example.echo.workflow","skill_version":"0.1.0","steps":[{"id":"x","action":"data.transform","policy":{"action":"x","resource":"y","scopes":[]},"inputs":{"n":NaN}}]}'
        path = self.make_package(raw_workflow=raw)
        with self.assertRaisesRegex(SkillValidationError, "non-finite"):
            validate_package(path)

    def test_nested_input_limit(self):
        deep = {}
        current = deep
        for _ in range(35):
            current["x"] = {}
            current = current["x"]
        path = self.make_package(lambda r, w: w["steps"][0].update(inputs=deep))
        with self.assertRaisesRegex(SkillValidationError, "nesting"):
            validate_package(path)

    def test_invalid_utf8_rejected(self):
        path = self.make_package()
        (path / "workflow.json").write_bytes(b"\xff")
        with self.assertRaisesRegex(SkillValidationError, "invalid UTF-8"):
            validate_package(path)

    def test_workflow_file_size_limit(self):
        path = self.make_package()
        (path / "workflow.json").write_text(" " * (256 * 1024 + 1))
        with self.assertRaisesRegex(SkillValidationError, "exceeds"):
            validate_package(path)

    def test_inputs_must_be_object(self):
        path = self.make_package(lambda r, w: w["steps"][0].update(inputs=["not", "object"]))
        with self.assertRaisesRegex(SkillValidationError, "steps.0.inputs"):
            validate_package(path)

    def test_policy_scopes_must_be_unique(self):
        path = self.make_package(lambda r, w: w["steps"][0]["policy"].update(scopes=["a","a"]))
        with self.assertRaisesRegex(SkillValidationError, "steps.0.policy.scopes"):
            validate_package(path)

    def test_unknown_properties_rejected_at_every_contract_level(self):
        cases = [
            lambda r, w: r.update(unexpected=True),
            lambda r, w: w.update(unexpected=True),
            lambda r, w: w["steps"][0].update(unexpected=True),
            lambda r, w: w["steps"][0]["policy"].update(unexpected=True),
        ]
        for mutate in cases:
            path = self.make_package(mutate)
            with self.subTest(mutate=mutate):
                with self.assertRaises(SkillValidationError):
                    validate_package(path)

    def test_schema_bounds_reject_oversized_fields(self):
        cases = [
            lambda r, w: w["steps"][0].update(adapter_id="a" * 129),
            lambda r, w: w["steps"][0].update(capability="c" * 257),
            lambda r, w: w["steps"][0]["policy"].update(action="a" * 257),
            lambda r, w: w["steps"][0]["policy"].update(resource="r" * 513),
            lambda r, w: w["steps"][0].update(prompt="p" * 2001),
            lambda r, w: w.update(description="d" * 2001),
            lambda r, w: w["steps"][0]["policy"].update(scopes=["s" * 129]),
            lambda r, w: r.update(permissions=["p" * 129]),
        ]
        for mutate in cases:
            path = self.make_package(mutate)
            with self.subTest(mutate=mutate):
                with self.assertRaises(SkillValidationError):
                    validate_package(path)

    def test_examples_pass_normative_draft_2020_12_schemas(self):
        resource_schema = json.loads((ROOT / "schemas" / "resource-manifest.schema.json").read_text(encoding="utf-8"))
        workflow_schema = json.loads((ROOT / "schemas" / "skill-workflow.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(resource_schema)
        Draft202012Validator.check_schema(workflow_schema)
        resource = json.loads((EXAMPLE / "resource.json").read_text(encoding="utf-8"))
        workflow = json.loads((EXAMPLE / "workflow.json").read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(resource_schema).iter_errors(resource)), [])
        self.assertEqual(list(Draft202012Validator(workflow_schema).iter_errors(workflow)), [])

if __name__ == "__main__":
    unittest.main()
