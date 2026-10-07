# Aarush — Backend Specification

## Purpose

Build a focused FastAPI + Python service for profile evidence, resume analysis, deterministic readiness, and role matching. Deploy to Render. Keep `../shared/SRD.md`, `../shared/ARCHITECTURE.md`, and `../shared/TECH_STACK.md` as the source contracts.

## Service shape

- One FastAPI application, versioned routes under `/api/v1`, Pydantic schemas, SQLAlchemy 2.x, PostgreSQL, and Alembic migrations.
- Keep clear, modest boundaries: API routes/schemas; core identity/settings; pure scoring domain; parser adapters; small use-case orchestration; persistence/storage adapters.
- Avoid microservices, Redis, queues, plugin systems, and generic repositories in the MVP.
- Expose `/health/live` and `/health/ready`; readiness checks the database with a short timeout.

## Required capabilities

- Owner-scoped profile CRUD, skills, and projects.
- Resume parse endpoint for PDF/DOCX/TXT up to 5 MiB; deterministic extraction, candidate facts, warnings, stable error codes, and no auto-confirm.
- Opportunity/JD storage and requirements extraction with a small versioned skill alias vocabulary.
- `cp-v1` readiness scoring with exact factors/weights and missing-factor renormalization as specified in `../shared/SRD.md`.
- Separate eligibility (`eligible`, `not_eligible`, `unknown`) and role match; explain factors, confidence, evidence source, gaps, and up to three actions.
- Assessment persistence with scoring version and compact input snapshot.
- Optional private file upload/signing and deletion through one configured provider adapter.

## Identity, data, and safety

- Default to Supabase Auth; verify JWT signature, issuer, audience, expiry, and subject in the API. If another auth provider is selected, preserve this validation boundary.
- Resolve internal user identity from the verified subject. Include owner constraints in every query; never accept trusted user IDs from request bodies or object keys.
- Validate resume type, signature where feasible, and byte limit. Treat contents as untrusted; never execute embedded content or log resume text.
- Keep storage private, generate random object keys, and use short-lived signed links. Profile deletion removes related rows and file objects or records retryable cleanup.
- Return stable safe error codes; never expose stack traces, secrets, tokens, or whether another user's record exists.

## Testing and deployable completion

- Unit tests: parser formats/failures, skill alias normalization, eligibility boundaries, weighted score bounds/renormalization, and output explanations.
- API tests: validation, identity, ownership, error shapes, and health behavior.
- Database tests: clean migration and foreign-key/deletion behavior.
- Deploy independently to Render with synthetic data, documented curl examples, OpenAPI, and working health endpoints. Frontend is not required for demonstration.
- Use environment configuration from `../shared/IMPLEMENTATION_GUIDE.md`; never commit real secrets.
