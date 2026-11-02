# Security Policy

## Scope

This repository contains a declarative workflow format and local validator. It is not an execution engine or security enforcement boundary.

## Reporting

Do not publish suspected vulnerabilities or exploitable details in public issues. Use GitHub private vulnerability reporting or a private security advisory only if enabled for this repository. No dedicated private reporting address is published here; if GitHub private reporting is unavailable, the owner must configure an approved private reporting channel before production use. Do not include secrets or unrelated personal data in public channels.

## Security expectations

- Treat skill packages and their referenced artifacts as untrusted.
- Authenticate publishers and verify artifact digests/signatures outside this repository before trust decisions.
- Re-evaluate authorization at execution time for every step; declared scopes are requests, not grants.
- Do not execute skill-supplied code or load arbitrary modules.
- Enforce isolation, timeouts, resource limits, and network/filesystem policy in a separate sandboxed runtime.
- Keep CI permissions read-only and pin third-party actions to immutable commits.
