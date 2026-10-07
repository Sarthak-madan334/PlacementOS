# CampusProof — Implementation, Quality, and Delivery Guide

This is the implementation agent's operating guide. Follow `README.md`, `SRD.md`, `ARCHITECTURE.md`, and `DESIGN.md` as product contracts.

## 1. Stack and repository boundaries

- Frontend: Next.js + TypeScript, deploy to Vercel.
- Backend: FastAPI + Python, deploy to Render.
- Data: PostgreSQL via Neon or Supabase; migrations with Alembic.
- Files: private Supabase Storage or Cloudinary, selected by environment.
- Source: GitHub. A monorepo or separate repositories are acceptable; use clear `frontend/` and `backend/` boundaries in a monorepo.
- Core resume parsing, eligibility, readiness, and matching work without a paid API.

Keep the backend a single service with focused modules. Do not add microservices, Redis, queues, plugin frameworks, generalized repositories, or cloud abstractions without a measured requirement.

## 2. SOLID principles in this project

Use SOLID as practical design guidance, not a requirement to create a class/interface for every function. Prefer cohesive modules and plain functions where they fit. Apply the principles at real change boundaries:

| Principle | CampusProof application |
|---|---|
| **S — Single Responsibility** | Keep HTTP routing/serialization, profile persistence, resume extraction, scoring, and storage operations in focused modules. A scoring rule change should not require changing upload or UI rendering code. |
| **O — Open/Closed** | Add a parser format or storage provider through a small adapter while keeping its normalized contract stable. Do not build an extension framework before a second real implementation is needed. |
| **L — Liskov Substitution** | Parser/storage implementations preserve the same outcomes and failure semantics; PDF and DOCX adapters return the same normalized result shape, and storage providers honor private-object and deletion behavior. |
| **I — Interface Segregation** | Keep contracts narrow: parsing, object storage, and identity verification are separate capabilities. Components should not depend on methods they do not use. |
| **D — Dependency Inversion** | Core scoring depends on normalized inputs and rule data, not FastAPI, SQLAlchemy, a storage vendor, or an LLM. API routes orchestrate dependencies; provider-specific details sit at the edges. |

For frontend, separate view components from API transport and score presentation. TypeScript types at the API boundary match OpenAPI. Avoid an abstraction when there is only one use and no meaningful boundary. This practical interpretation follows [SOLID Design Principles](https://principles.design/examples/solid-design-principles); Fowler's [DIP in the Wild](https://martinfowler.com/articles/dipInTheWild.html) discusses dependency direction and boundaries in real code.

## 3. Suggested minimal module layout

```text
frontend/
  app/                  routes and page composition
  components/           reusable presentation components
  features/             profile, resume review, opportunity, results
  lib/api/              typed HTTP client and fixture adapter
backend/
  app/api/v1/            route handlers and schemas
  app/core/              settings and identity dependencies
  app/domain/            normalized models and cp-v1 scoring rules
  app/services/          use-case orchestration and resume analysis
  app/adapters/          SQLAlchemy persistence and storage/parser adapters
  migrations/            Alembic versions
  tests/                 domain, API, and integration tests
```

Adapt names to framework conventions; preserve boundaries and avoid unnecessary layering.

## 4. Independent work and integration

These workstreams start in parallel and must not block one another:

| Owner | First independent deliverable |
|---|---|
| Sarthak | Complete Next.js flow using fixture JSON conforming to `SRD.md`, including all states in `DESIGN.md`; deploy a Vercel preview. |
| Aarush | FastAPI OpenAPI routes, synthetic data, parser/scoring modules, migrations, and tests; deploy a Render preview independently. |
| Sejal | Validate provider/config choices, migrations and ownership model, privacy review, and acceptance checklist; keep contracts and integration decisions recorded in these docs. |

Each owner uses mock data or stubs until another component is ready. First agree to the SRD response shape, then connect frontend and backend in staging. For integration: set the frontend API URL, add its exact origin to backend CORS, configure matching identity issuer/audience, use isolated preview DB/storage, apply migrations, then run smoke checks. Breaking contract changes require coordinated updates to SRD, OpenAPI, frontend types, and fixtures.

## 5. Configuration and secrets

Frontend browser-visible configuration:

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Matching API origin/base path |
| `NEXT_PUBLIC_DEMO_MODE` | Optional explicit fixture/demo mode; contains no secret |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase Auth client configuration when Supabase is selected; the anon/publishable key is not a service-role key |

Backend configuration:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `local`, `preview`, or `production` |
| `DATABASE_URL` | TLS PostgreSQL connection URL |
| `CORS_ORIGINS` | Exact comma-separated allowed frontend origins |
| `AUTH_ISSUER_URL` / `AUTH_AUDIENCE` | Verified JWT issuer/audience; required for persisted user data |
| `STORAGE_PROVIDER` | `supabase` or `cloudinary` when uploads are enabled |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET` | Server-only Supabase storage settings |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Server-only Cloudinary settings |
| `MAX_RESUME_BYTES` | Upload bound; default 5242880 |

Commit placeholders only in `.env.example`; keep actual values in ignored local files and provider secret settings. Never put service-role keys, DB URLs, or provider secrets in `NEXT_PUBLIC_*`, client code, logs, or screenshots. Use separate preview and production credentials. Default to Supabase Auth for the first Supabase deployment; finalize provider settings before protected user data is deployed.

## 6. Security, privacy, and reliability

- Require authenticated identity for persisted personal data; verify JWT signature, issuer, audience, expiry, and subject server-side. Demo fixtures contain synthetic data only.
- Enforce ownership predicates on every profile, assessment, and file operation. Use parameterized ORM queries; never trust client owner IDs.
- Keep resume objects private, use random object keys and short-lived signed URLs, enforce type/signature/size limits, and delete objects when profile data is deleted. Do not log resume text, tokens, signed URLs, or personal information.
- Explain collection and retention; make resume optional; define retention/deletion behavior and privacy notice before production launch.
- Configure HTTPS, exact CORS origins, safe error messages, request/upload bounds, and dependency/security updates.
- Keep `/health/live` independent of dependencies and `/health/ready` short and bounded. Use provider logs/metrics; log request ID, route, status, and duration without sensitive fields.
- Enable managed PostgreSQL backups and document a restore rehearsal. Add pagination/indexes/worker processing only when usage or measured latency warrants them.

## 7. Quality and acceptance

Before merge, run checks applicable to the changed component:

- Frontend: type check, production build, responsive states, keyboard/focus review, fixture-mode full flow.
- Backend: tests for `cp-v1` factor boundaries, eligibility unknown/ineligible rules, response schema, parser failures, and owner access; migrations apply to a clean PostgreSQL database.
- Integration: profile → resume review (optional) → opportunity/JD → assessment → explainable results; missing-data and hard-ineligibility cases; cross-user denial; file privacy/delete if enabled.
- Deployment: deployed URL responds, health/readiness pass, smoke flow verified with synthetic data, and deployed commit/migration revision recorded.

No workstream is done merely because it runs locally. Each component can be deployed and demonstrated independently; the combined production candidate gets an additional integrated smoke check. Keep a recoverable rollback path and use backward-compatible migrations.

## 8. Antigravity working rules

1. Read all five project documents before generating features.
2. Preserve product scope, route shapes, scoring contract, and visual direction. Update the relevant document first if an agreed contract must change.
3. Build a runnable, narrow vertical slice and keep demo fixtures so frontend progress never waits on backend readiness.
4. Validate on both sides of the API; do not trust browser validation for security or scoring.
5. Do not invent fake evidence, guaranteed impact numbers, hiring probabilities, or unrequested product areas.
6. Keep modules cohesive and use SOLID at real boundaries without speculative abstractions.
7. Report what runs, which checks passed, deployment URL/state, and any incomplete integration plainly.
