# Threat Model

## Assets

- Skill package metadata and workflow definitions.
- Downstream agent principals, tools, data, and delegated authority.
- Integrity and provenance of published skill artifacts.

## Trust boundaries

All package files, repository references, adapter identifiers, capability names, input values, and publisher metadata are untrusted until independently authenticated and validated. Schema conformance only establishes structural validity.

## Threats and mitigations

| Threat | Current mitigation | Residual risk |
|---|---|---|
| Malformed or ambiguous JSON | Duplicate-key rejection, non-finite number rejection, size and depth limits | Consumer-specific parsing differences remain |
| Workflow abuse or resource exhaustion | Maximum 50 steps; bounded inputs | Runtime must impose execution budgets and cancellation |
| Capability/adapter spoofing | References are treated as labels only | Runtime must resolve trusted adapters and verify identity |
| Privilege escalation | Per-step policy intent is mandatory | No policy decision or enforcement is implemented here |
| Malicious skill publisher | No execution or trust decision in validator | Publisher authentication, signatures, revocation and review are external |
| Prompt or instruction injection | No trusted instruction channel is defined | Consumers must isolate untrusted skill content from system/developer instructions |
| Unsafe side effects | Declarative action vocabulary only | Runtime must mediate every side effect and use sandbox isolation |

## Explicit non-goals

No workflow execution, dynamic code loading, package installation, network access, secret handling, publisher authentication, cryptographic signature verification, authorization enforcement, durable audit, or sandbox implementation.

## Deployment requirements for consumers

Authenticate the publisher; verify artifact integrity and signature freshness; validate against pinned schemas; resolve dependencies from trusted sources; derive principal identity from authenticated context; request a fresh default-deny policy decision per step; require enforceable human approval where appropriate; and execute through a separately reviewed sandbox with timeouts, filesystem/network controls, resource quotas, and audit evidence.
