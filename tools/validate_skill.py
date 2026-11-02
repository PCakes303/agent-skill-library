#!/usr/bin/env python3
"""Schema-backed validator for declarative Agent Skill packages."""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

MAX_FILE_BYTES = 256 * 1024
MAX_DEPTH = 32
MAX_STEPS = 50
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]{2,127}$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
STEP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ACTIONS = {"tool.invoke", "agent.delegate", "human.approval", "data.transform"}

class SkillValidationError(ValueError):
    """Raised when a package violates the local skill contract."""

def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SkillValidationError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result

def _reject_constant(value):
    raise SkillValidationError(f"non-finite JSON number is not allowed: {value}")

def _depth(value, level=0):
    if level > MAX_DEPTH:
        raise SkillValidationError(f"JSON nesting exceeds {MAX_DEPTH}")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise SkillValidationError("JSON object keys must be strings")
            _depth(item, level + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, level + 1)
    elif isinstance(value, float) and not math.isfinite(value):
        raise SkillValidationError("non-finite JSON number is not allowed")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise SkillValidationError(f"unsupported JSON value: {type(value).__name__}")

def _load(path):
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise SkillValidationError(f"{path.name} exceeds {MAX_FILE_BYTES} bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates,
                           parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise SkillValidationError(f"invalid UTF-8 JSON in {path.name}: {exc}") from exc
    _depth(value)
    if not isinstance(value, dict):
        raise SkillValidationError(f"{path.name} must contain a JSON object")
    return value

def _validate_schema(document, schema_name, document_name):
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(document),
            key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SkillValidationError(f"{schema_name} is unavailable or invalid: {type(exc).__name__}") from exc
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise SkillValidationError(f"{document_name} schema violation at {location}: {error.message}")

def validate_package(directory):
    directory = Path(directory)
    resource_path = directory / "resource.json"
    workflow_path = directory / "workflow.json"
    if not resource_path.is_file() or not workflow_path.is_file():
        raise SkillValidationError("package must contain resource.json and workflow.json")
    resource = _load(resource_path)
    workflow = _load(workflow_path)
    _validate_schema(resource, "resource-manifest.schema.json", "resource.json")
    _validate_schema(workflow, "skill-workflow.schema.json", "workflow.json")

    required_resource = {"manifest_version", "id", "kind", "name", "version"}
    missing = sorted(required_resource - resource.keys())
    if missing:
        raise SkillValidationError("resource manifest missing: " + ", ".join(missing))
    if resource["manifest_version"] != "1.0" or resource["kind"] != "skill":
        raise SkillValidationError("resource manifest must use version 1.0 and kind 'skill'")
    if not isinstance(resource["id"], str) or not ID_RE.fullmatch(resource["id"]):
        raise SkillValidationError("resource id has invalid format")
    if not isinstance(resource["name"], str) or not 1 <= len(resource["name"]) <= 160:
        raise SkillValidationError("resource name must contain 1-160 characters")
    if not isinstance(resource["version"], str) or not SEMVER_RE.fullmatch(resource["version"]):
        raise SkillValidationError("resource version must be semantic X.Y.Z")
    if resource.get("entrypoint", "workflow.json") != "workflow.json":
        raise SkillValidationError("entrypoint must be workflow.json")
    permissions = resource.get("permissions", [])
    if not isinstance(permissions, list) or any(not isinstance(x, str) for x in permissions):
        raise SkillValidationError("resource permissions must be an array of strings")
    if len(set(permissions)) != len(permissions):
        raise SkillValidationError("resource permissions must be unique")

    if workflow.get("workflow_version") != "1.0":
        raise SkillValidationError("workflow_version must be '1.0'")
    if workflow.get("skill_id") != resource["id"] or workflow.get("skill_version") != resource["version"]:
        raise SkillValidationError("resource and workflow identity/version must match")
    steps = workflow.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise SkillValidationError(f"workflow must contain 1-{MAX_STEPS} steps")

    seen = set()
    requested_scopes = set()
    for index, step in enumerate(steps):
        label = f"steps[{index}]"
        if not isinstance(step, dict):
            raise SkillValidationError(f"{label} must be an object")
        step_id = step.get("id")
        if not isinstance(step_id, str) or not STEP_ID_RE.fullmatch(step_id):
            raise SkillValidationError(f"{label}.id has invalid format")
        if step_id in seen:
            raise SkillValidationError(f"duplicate step id: {step_id}")
        seen.add(step_id)
        action = step.get("action")
        if action not in ACTIONS:
            raise SkillValidationError(f"{label}.action is not supported")
        if action == "tool.invoke":
            for key in ("adapter_id", "capability"):
                if not isinstance(step.get(key), str) or not step[key]:
                    raise SkillValidationError(f"{label}.{key} is required for tool.invoke")
        if action == "human.approval" and not isinstance(step.get("prompt"), str):
            raise SkillValidationError(f"{label}.prompt is required for human.approval")
        policy = step.get("policy")
        if not isinstance(policy, dict) or not all(isinstance(policy.get(k), str) and policy[k] for k in ("action", "resource")):
            raise SkillValidationError(f"{label}.policy requires action and resource strings")
        scopes = policy.get("scopes")
        if not isinstance(scopes, list) or len(scopes) > 100 or any(not isinstance(s, str) or not s for s in scopes):
            raise SkillValidationError(f"{label}.policy.scopes must be an array of non-empty strings")
        if len(set(scopes)) != len(scopes):
            raise SkillValidationError(f"{label}.policy.scopes must be unique")
        requested_scopes.update(scopes)
        inputs = step.get("inputs", {})
        if not isinstance(inputs, dict) or len(inputs) > 64:
            raise SkillValidationError(f"{label}.inputs must be an object with at most 64 properties")
        _depth(inputs)

    missing_scopes = sorted(requested_scopes - set(permissions))
    if missing_scopes:
        raise SkillValidationError("resource permissions omit requested workflow scopes: " + ", ".join(missing_scopes))
    return {"skill_id": resource["id"], "version": resource["version"], "steps": len(steps), "result": "valid"}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="directory containing resource.json and workflow.json")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_package(args.package), indent=2))
    except (OSError, SkillValidationError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
