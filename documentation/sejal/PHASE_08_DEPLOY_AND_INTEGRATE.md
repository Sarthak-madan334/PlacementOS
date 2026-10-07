# Sejal — Phase 08: Deployment and Integration Harness

**Owner:** Sejal
**Can start:** Immediately with placeholder apps and contract fixtures
**Deployable result:** Reproducible preview setup and smoke workflow

## Outcome

Prepare a repeatable path for each application component to deploy independently and for compatible versions to connect in an isolated preview. It does not own unfinished feature implementation. Follow [`../../docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md) for provider-specific setup.

## Build

- Document/create Vercel frontend and Render FastAPI preview configurations with separate preview/production environment values.
- Add backend live/readiness checks and a frontend fixture-mode route so both deploy before integration is available.
- Define exact CORS origin configuration and API base URL per environment.
- Provision a non-production PostgreSQL database and private storage bucket; use separate credentials and synthetic records.
- Add a GitHub workflow for lint/type/build/backend tests and migration checks. Keep provider deploy steps documented and reproducible.
- Add the integration smoke script/checklist in [`../../docs/INTEGRATION_RUNBOOK.md`](../../docs/INTEGRATION_RUNBOOK.md).
- Record deployed commit, migration revision, preview URLs, and pass/fail status for each release candidate.

## Acceptance

- Frontend and backend deploy independently and show their own health/demo path.
- Preview can connect using the SRD contract without exposing service keys in browser configuration.
- Database migrations apply to an empty preview DB; readiness status responds correctly.
- Smoke checklist covers profile, optional parse, opportunity, assessment, error/missing-data paths, cross-user access, and private file cleanup when uploads are enabled.
- Rollback instructions identify app rollback and safe forward-fix/restore approach for database changes.

## Independence contract

Start with hello-world app skeletons, mock endpoint, and synthetic DB schema. Building deployment scaffolding does not wait for feature completion. Full end-to-end smoke verification is a later release gate, not a blocker for this workstream's independent deploy setup.
