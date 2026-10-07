# PlacementOS Documentation

## Shared product and technical direction

- [`PRODUCT_REQUIREMENTS.md`](shared/PRODUCT_REQUIREMENTS.md) — product goal, MVP scope, and Antigravity direction.
- [`REQUIREMENTS.md`](shared/REQUIREMENTS.md) — concise requirement IDs and release traceability.
- [`TECH_STACK.md`](shared/TECH_STACK.md) — approved technologies and default provider configuration.
- [`SRD.md`](shared/SRD.md) — functional requirements, scoring contract, API shapes, and acceptance cases.
- [`ARCHITECTURE.md`](shared/ARCHITECTURE.md) — components, data model, identity, and hosting boundaries.
- [`DESIGN.md`](shared/DESIGN.md) — glassmorphism visual direction, screens, responsive behavior, and UI states.
- [`IMPLEMENTATION_GUIDE.md`](shared/IMPLEMENTATION_GUIDE.md) — SOLID practices, security, quality, configuration, and delivery.
- [`SCORING_AND_PARSING.md`](shared/SCORING_AND_PARSING.md) — detailed deterministic scoring and resume parser rules.
- [`INTEGRATION_RUNBOOK.md`](shared/INTEGRATION_RUNBOOK.md) — connecting previews, smoke checks, release, and rollback.
- [`PHASES.md`](shared/PHASES.md) — all eight parallel workstreams and their completion criteria.

## Member-owned phase documents

- [Sarthak](sarthak/) — [frontend specification](sarthak/FRONTEND.md), product shell, and results dashboard.
- [Aarush](aarush/) — [backend specification](aarush/BACKEND.md), profile API, resume parser, readiness engine, and opportunity matching.
- [Sejal](sejal/) — system/security review and deployment/integration harness.

Every phase can start with fixtures and be demonstrated independently. The shared integration check is a release checkpoint, not a development prerequisite. See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for branch and ownership workflow.
