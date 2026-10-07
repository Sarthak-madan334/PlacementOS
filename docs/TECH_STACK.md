# PlacementOS — Technology Stack

This is the agreed MVP stack. Keep provider choices configurable, but choose one provider set per environment and avoid building multi-provider failover.

## Approved stack

| Layer | Technology | Deployment / responsibility |
|---|---|---|
| Web application | Next.js + TypeScript | Vercel; UI, forms, typed API client, fixture/demo mode |
| API | FastAPI + Python | Render; validation, identity checks, parsing orchestration, scoring, persistence |
| Database | Supabase PostgreSQL | Relational source of truth; separate preview and production projects |
| Managed authentication | Supabase Auth | Browser sign-in and API JWT verification |
| Resume storage | Supabase Storage | Private bucket, short-lived access, random object keys |
| Database access | SQLAlchemy 2.x + Alembic | ORM/session handling and schema migrations |
| Source control | GitHub | Owner folders, feature branches, pull requests, CI |

## Default first deployment

Use **Supabase PostgreSQL + Supabase Auth + private Supabase Storage**, **Next.js on Vercel**, and **FastAPI on Render**. This is the deployment target for PlacementOS; do not configure Neon or Cloudinary for this project.

## Runtime constraints

- Core profile, parsing, eligibility, readiness, and role matching must work without paid APIs.
- Use deterministic in-process parsing/scoring for the MVP. No queue, Redis, microservices, or hosted LLM in the critical path.
- Keep provider credentials on the backend. Browser-visible Supabase configuration may contain only the public URL and anon/publishable key; never expose the service-role key.
- Use separate local, preview, and production credentials, databases, and storage buckets.
- Pin supported package versions in the actual package manifests/lockfiles when code is added. This specification intentionally avoids inventing versions before implementation.

## Service boundaries

The browser calls FastAPI over HTTPS using the `/api/v1` contract in `SRD.md`. FastAPI owns authoritative validation and scores. Supabase PostgreSQL stores structured user data and assessments; Supabase Storage holds private resume files. See `ARCHITECTURE.md`, [`../documentation/aarush/BACKEND.md`](../documentation/aarush/BACKEND.md), [`../documentation/sarthak/FRONTEND.md`](../documentation/sarthak/FRONTEND.md), and [`DEPLOYMENT.md`](DEPLOYMENT.md) for implementation details.
