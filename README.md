# Agent Skill Library

**Maturity:** experimental reference format and validator  
**Initial deployment:** 2026-11-02  
**Owner:** MrCakes931 / PCakes303  
**License:** [Scoped mixed-license policy](LICENSE.md).

A machine-discoverable catalog format for reusable, versioned, declarative agent workflows. A skill package separates its portable Resource Manifest from a constrained workflow document.

## What this release provides

- A skill package contract with stable identifiers and semantic versions.
- A workflow schema with bounded, ordered, declarative steps.
- Per-step policy-intent metadata and explicit tool-adapter references.
- A schema-backed Python validator and negative regression tests.
- A synthetic example package.

This repository validates declarations. It does **not** execute workflows, authenticate publishers, authorize principals, enforce policy, resolve or install dependencies, or isolate tools.

## Development validation

Install the pinned schema validator and run the regression suite:

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_skill.py examples/echo
python -m unittest discover -s tests -v
```

## Quick start

Requires Python 3.10+; the validator uses only the standard library.

```bash
python tools/validate_skill.py examples/echo
python -m unittest discover -s tests -v
```

## Package layout

- `resource.json`: Resource Manifest v1.0 skill resource.
- `workflow.json`: Agent Skill Workflow v1.0 declarative steps.
- `schemas/skill-workflow.schema.json`: Draft 2020-12 workflow schema.

The Resource Manifest contract is maintained by [agent-resource-manifest](https://github.com/PCakes303/agent-resource-manifest). Workflow schemas are intended for cataloguing through [agent-schema-registry](https://github.com/PCakes303/agent-schema-registry).

## Security model

A valid skill is untrusted metadata, not executable authority. Consumers must authenticate the publisher, validate integrity and dependencies, obtain a real policy decision for each operation, and invoke tools only through a separately secured execution boundary. The current tool-adapter reference library is in-process and experimental; it is not a sandbox. Human approval steps are declarations only and are not enforced here.

See [SKILL-CONTRACT.md](docs/SKILL-CONTRACT.md) and [THREAT-MODEL.md](docs/THREAT-MODEL.md).

## Dependencies

The master registry declares Resource Manifest, Schema Registry, Policy Engine, and Tool Adapters as contract dependencies. No runtime integration with those repositories is claimed or tested by this release.

## Development

```bash
python tools/validate_skill.py examples/echo
python -m unittest discover -s tests -v
```

This repository documents the ecosystem's intended scoped mixed-license policy: Apache-2.0 for eligible original code and machine-readable contracts, and CC BY 4.0 for eligible original human-readable documentation. Its manifest remains `pending-review` until contributor authority, file-level provenance and third-party notices are checked. Do not assume every file is cleared for redistribution. Third-party material retains upstream terms; data, evidence, fixtures, sample payloads and media receive no blanket license. See [LICENSE.md](LICENSE.md).
