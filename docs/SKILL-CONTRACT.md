# Agent Skill Package Contract v1.0

## Package shape

A package directory contains exactly the two required contract documents:

- `resource.json`: a Resource Manifest v1.0 object with `kind: skill`.
- `workflow.json`: an Agent Skill Workflow v1.0 object.

The resource manifest is the portable resource identity. The workflow is the declarative sequence. Their `id` and `version` values MUST match. The resource manifest's `entrypoint` SHOULD be `workflow.json`. Its `permissions` MUST include every scope requested by a workflow step.

## Workflow document

Required top-level fields: `workflow_version`, `skill_id`, `skill_version`, and `steps`.

A workflow has 1–50 ordered steps. Each step has a unique stable `id`, a supported `action`, and a `policy` request containing `action`, `resource`, and unique `scopes`.

Supported declarative actions:

- `tool.invoke`: requires `adapter_id` and `capability`. These are references, not proof the adapter exists or is safe.
- `agent.delegate`: declares a delegation intent; a runtime must authenticate the recipient and authorize delegation.
- `human.approval`: declares a human approval checkpoint; this repository does not implement or enforce the checkpoint.
- `data.transform`: describes a bounded transformation intent; executable transformation code is not allowed in the workflow.

Step `inputs` are JSON data only. The validator rejects duplicate object keys, non-finite numbers, excessive nesting, non-object inputs, and oversized workflow files. Consumers SHOULD impose stricter context-specific limits.

## Policy semantics

Per-step policy fields map conceptually to the Policy Engine decision request: `principal_id`, `action`, `resource`, and `scopes`. A skill package does not supply an authoritative principal identity or a policy decision. The execution environment MUST bind the authenticated principal itself and obtain a fresh decision from its trusted policy enforcement path before each step. Missing, malformed, stale, or unavailable decisions MUST fail closed.

## Versioning

Workflow schema version and skill package semantic version are separate. Breaking required-field or security-semantic changes require a major workflow contract version. Additive optional fields/actions require a minor version and compatibility review. Editorial fixes use patch versions.

## Integrity and trust

The Resource Manifest can carry an integrity digest, but a string in a manifest is not self-verifying. A trusted distribution pipeline must compute the digest over a precisely defined artifact, verify signatures against trusted publisher keys, check revocation/freshness, and bind the result to an authenticated publisher. Those mechanisms are not implemented here.
