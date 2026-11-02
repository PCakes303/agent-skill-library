# Security Policy

## Scope

This repository contains a declarative workflow format and local validator. It is not an execution engine or security enforcement boundary.

## Reporting

Use GitHub private vulnerability reporting when enabled. Do not publish suspected vulnerabilities in public issues. Include the affected commit, impact, and minimal reproduction; do not include secrets or unrelated personal data.

## Security expectations

- Treat skill packages and their referenced artifacts as untrusted.
- Authenticate publishers and verify artifact digests/signatures outside this repository before trust decisions.
- Re-evaluate authorization at execution time for every step; declared scopes are requests, not grants.
- Do not execute skill-supplied code or load arbitrary modules.
- Enforce isolation, timeouts, resource limits, and network/filesystem policy in a separate sandboxed runtime.
- Keep CI permissions read-only and pin third-party actions to immutable commits.
