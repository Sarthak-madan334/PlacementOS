# Aarush — Phase 02: Profile and Evidence API

**Owner:** Aarush
**Can start:** Immediately, using the profile schema in [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
**Deployable result:** FastAPI preview on Render

## Outcome

A small owner-scoped API for student profile, skills, and projects. It runs independently of the frontend and resume parser.

## Build

- Create FastAPI app with `/health/live`, `/health/ready`, and `/api/v1/me/profile` GET/PUT/DELETE routes as specified in [`../../docs/SRD.md`](../../docs/SRD.md).
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

## Implementation Status

- **Status**: Implemented and locally tested; PostgreSQL/Render deployment acceptance is not yet verified.
- **Modules Created**:
  - `backend/app/main.py`: FastAPI application entrypoint with CORS, OpenAPI at `/api/v1/openapi.json`, and lifespan table initialization.
  - `backend/app/core/config.py`: Environment configuration for DB, CORS, Auth, and upload bounds.
  - `backend/app/core/security.py`: JWT token verification and owner identity mapping from `sub` claim.
  - `backend/app/core/exceptions.py`: Uniform error responses `{"detail": "...", "code": "..."}` with unhandled error shielding.
  - `backend/app/adapters/db/models.py`: SQLAlchemy 2.x models for `User`, `StudentProfile`, `Skill`, `Project`, and `ProfileFile` with cascading foreign keys and indexes.
  - `backend/app/api/v1/schemas/profile.py`: Pydantic schemas validating graduation years, CGPA/scale bounds, URLs, and string constraints.
  - `backend/app/api/v1/endpoints/health.py`: Liveness (`/health/live`) and database readiness (`/health/ready`).
  - `backend/app/api/v1/endpoints/profile.py`: `/api/v1/me/profile` GET/PUT/DELETE routes with idempotent upsert and deduplication.
  - `backend/migrations/`: Alembic configuration and initial migration `001_initial_profile_schema.py`.
  - `backend/fixtures/synthetic_profiles.json`: Synthetic profile fixtures for frontend and local development.
  - `backend/tests/`: 17 automated tests covering health, auth, CRUD, idempotency, cross-user isolation, validations, cascades, and migrations.

