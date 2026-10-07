# Aarush — Phase 02: Profile and Evidence API

**Owner:** Aarush
**Can start:** Immediately, using the profile schema in [`../shared/ARCHITECTURE.md`](../shared/ARCHITECTURE.md)
**Deployable result:** FastAPI preview on Render

## Outcome

A small owner-scoped API for student profile, skills, and projects. It runs independently of the frontend and resume parser.

## Build

- Create FastAPI app with `/health/live`, `/health/ready`, and `/api/v1/me/profile` GET/PUT/DELETE routes as specified in [`../shared/SRD.md`](../shared/SRD.md).
- Use Pydantic request/response schemas; validate graduation year, CGPA bounds/scale, string lengths, project URLs, and skill names.
- Persist through SQLAlchemy 2.x and Alembic; add owner foreign keys, uniqueness and indexes.
- Use managed identity validation for persisted profile endpoints. Owner ID comes only from verified identity context.
- Provide synthetic seed/demo fixtures for local work; do not create a production bypass for auth.

## Acceptance

- Migrations apply to a clean PostgreSQL database.
- Profile upsert is idempotent for a user and does not duplicate skills on repeated requests.
- Unauthenticated requests receive 401; cross-user access is denied without disclosing resource existence.
- Invalid fields receive stable 422 details; unexpected errors do not expose traces or secrets.
- Health liveness does not depend on the database; readiness fails promptly when the database is unavailable.
- Deploy to Render and verify health endpoints and documented request examples.

## Independence contract

Use curl/OpenAPI and synthetic users. No UI, resume parser, scoring service, or opportunity service is required to demonstrate profile read/write behavior.
