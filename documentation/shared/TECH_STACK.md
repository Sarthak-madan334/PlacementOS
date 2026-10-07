# PlacementOS — Technology Stack

This is the agreed MVP stack. Keep provider choices configurable, but choose one provider set per environment and avoid building multi-provider failover.

## Approved stack

| Layer | Technology | Deployment / responsibility |
|---|---|---|
| Web application | Next.js + TypeScript | Vercel; UI, forms, typed API client, fixture/demo mode |
| API | FastAPI + Python | Render; validation, identity checks, parsing orchestration, scoring, persistence |
| Database | PostgreSQL | Neon or Supabase; relational source of truth |
| Managed authentication | Supabase Auth by default | Browser sign-in and API JWT verification; if using Neon, select another compatible managed identity provider |
| Resume storage | Supabase Storage or Cloudinary | Private objects, short-lived access, random object keys |
| Database access | SQLAlchemy 2.x + Alembic | ORM/session handling and schema migrations |
| Source control | GitHub | Owner folders, feature branches, pull requests, CI |

## Default first deployment

Use **Supabase PostgreSQL + Supabase Auth + private Supabase Storage**, **Next.js on Vercel**, and **FastAPI on Render**. This minimizes service setup while staying within the stack already selected. Neon + a compatible managed auth provider + Cloudinary remains supported when deliberately chosen.

## Runtime constraints

- Core profile, parsing, eligibility, readiness, and role matching must work without paid APIs.
- Use deterministic in-process parsing/scoring for the MVP. No queue, Redis, microservices, or hosted LLM in the critical path.
- Keep provider credentials on the backend. Browser-visible Supabase configuration may contain only the public URL and anon/publishable key; never expose the service-role key.
- Use separate local, preview, and production credentials, databases, and storage buckets.
- Pin supported package versions in the actual package manifests/lockfiles when code is added. This specification intentionally avoids inventing versions before implementation.

## Service boundaries

The browser calls FastAPI over HTTPS using the `/api/v1` contract in `SRD.md`. FastAPI owns authoritative validation and scores. PostgreSQL stores structured user data and assessments; object storage stores private resume files. See `ARCHITECTURE.md`, [`../aarush/BACKEND.md`](../aarush/BACKEND.md), and [`../sarthak/FRONTEND.md`](../sarthak/FRONTEND.md) for implementation details.
