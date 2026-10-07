# PlacementOS — Vercel, Render, and Supabase Deployment

## Deployment target

```text
GitHub main
  ├─ frontend/  → Vercel (Next.js)
  └─ backend/   → Render (FastAPI)
                    └─ Supabase (PostgreSQL + Auth + private Storage)
```

Use Supabase for this project’s database, authentication, and resume-file storage. Use separate Supabase projects for preview and production, with separate credentials and synthetic preview data. Do not use production student data in preview deployments.

> **Current repository state:** Runnable frontend and backend apps, tests, a Render Blueprint, and a GitHub CI workflow are in source control. This does not prove provider deployment. No Vercel, Render, or Supabase preview URL has been recorded or end-to-end verified. Provider secrets, databases, auth settings, and deployment permissions still need an owner to configure them.

## 1. Create Supabase environments

Create one Supabase project for preview and one for production. Select a region near the Render service. In each project:

1. Enable Supabase Auth and set the production Site URL to the real Vercel production origin.
2. Add exact local and production auth redirect URLs. For Vercel previews, add a wildcard matching the Vercel account/team slug, such as `https://*-<team-or-account-slug>.vercel.app/**`; do not use a broad production wildcard.
3. Create a private Storage bucket for resumes. Set allowed MIME types to PDF, DOCX, and plain text, and set the maximum object size to 5 MiB.
4. Apply database migrations from `backend/` with Alembic. Keep schema migrations in source control and apply them to preview before production.
5. Add database ownership constraints and use the API's verified user identity for all personal-data operations. A Supabase service-role key bypasses RLS: keep it only on Render and enforce owner checks in the API. Never expose it to Vercel/browser code.
6. Copy project URL, public anon/publishable key, and database connection string from the Supabase dashboard. Use the `Connect` panel to choose a connection mode; do not construct pooler hostnames by hand.

For the persistent Render API, use Supabase's direct connection if Render can reach the project's IPv6 endpoint. If the service network is IPv4-only, use Supabase's shared **session** pooler. Do not use transaction mode for the long-running SQLAlchemy API unless the driver/session behavior is deliberately configured for transaction pooling. Require SSL. Use the direct connection for migrations when reachable; otherwise verify the chosen supported migration connection path in preview.

## 2. Deploy the FastAPI backend to Render

Connect the GitHub repository through Render's Git provider integration so pushes can trigger deploys.

| Render setting | Value after the backend app exists |
|---|---|
| Service type | Web Service |
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health/ready` |
| Production branch | `main` |

The start command assumes `backend/app/main.py` exposes the FastAPI instance as `app`. If the implementation uses another module layout, update the command to match that actual import path. Bind to `0.0.0.0` and Render's injected `$PORT`.

Set Render environment variables through its environment/secret settings, not committed files:

- `APP_ENV=preview` or `production`
- `DATABASE_URL` (Supabase URL selected for that environment; SSL enabled)
- `AUTH_ISSUER_URL=https://<project-ref>.supabase.co/auth/v1` and `AUTH_AUDIENCE=authenticated` for Supabase Auth JWT verification. Asymmetric ES256/RS256 keys are verified using the issuer's JWKS; set `SUPABASE_JWT_SECRET` only for a project still using legacy HS256 signing.
- `CORS_ORIGINS` with the exact corresponding Vercel origin(s)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`
- `MAX_RESUME_BYTES=5242880`
- `GITHUB_TOKEN` — optional GitHub API token for public profile lookup rate limits; store only as a Render secret and omit it if unused.

Use least privilege and a small SQLAlchemy connection pool. Run Alembic migrations as an explicit release step before code that depends on the changed schema. Verify `/health/live` and `/health/ready`, then check Render logs for startup or database errors.

## 3. Deploy the Next.js frontend to Vercel

Import the same GitHub repository into Vercel and configure:

| Vercel setting | Value after the frontend app exists |
|---|---|
| Framework Preset | Next.js |
| Root Directory | `frontend` |
| Production Branch | `main` |
| Build | Next.js detected build; package scripts and lockfile committed under `frontend/` |

Configure separate Preview and Production values:

- `NEXT_PUBLIC_API_BASE_URL` — matching Render API base URL.
- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (or publishable key) — browser-safe Supabase Auth configuration; never use the service-role key here.
- `NEXT_PUBLIC_SITE_URL` — the canonical site origin for auth callback generation.
- `NEXT_PUBLIC_DEMO_MODE` — enable only when the deployment should use synthetic fixture mode; disable for the connected deployment.

Connect Vercel to GitHub so feature branches produce Preview deployments and `main` produces Production deployment. Add Preview origins to Supabase Auth redirects and Render CORS only as needed; keep production origins exact. Any changed Vercel environment variable applies to subsequent deployments, so redeploy after configuration changes.

## 4. Configure auth, CORS, storage, and database together

- **Auth:** Supabase Site URL is the production frontend origin. Allow localhost for development, exact production callback paths, and a Vercel-preview wildcard scoped to the account/team slug. Confirm email confirmation and password reset return to the correct environment.
- **CORS:** Render allows only the exact Vercel production origin and the required preview origins. Do not use `*` for credentialed/personal-data APIs.
- **Storage:** the resume bucket stays private. Upload size/type restrictions are set in the bucket and checked again by the API. Authorize each object by owner; provide only short-lived signed URLs when the frontend needs a download.
- **Database:** each deployment points to its matching Supabase project. Set SSL and conservative SQLAlchemy pool sizing. Keep migration credentials and runtime credentials separate where practicable.
- **Secrets:** Supabase service-role key, DB URL, and any signing credentials exist only in Render's secret settings. No secret is committed to GitHub or placed in a `NEXT_PUBLIC_*` variable.

## 5. Release verification

1. Confirm the GitHub commit contains runnable `frontend/` and `backend/` applications and lock/dependency files; require `.github/workflows/ci.yml` to pass.
2. Apply migrations to the preview Supabase project.
3. Deploy Render preview and verify readiness; record its URL.
4. Deploy Vercel preview with the Render preview URL and preview Supabase public Auth settings.
5. Run the full checklist in `INTEGRATION_RUNBOOK.md`: sign in, save profile, optionally parse a synthetic resume, create an opportunity, assess, inspect explanations, test missing-data and ineligible cases, verify cross-user denial, and delete a test resume.
6. Repeat with production settings and only synthetic/approved test accounts before announcing launch.
7. Record Vercel URL, Render URL, Supabase project reference (never its keys), commit SHA, migration revision, and smoke-check result.

The system is considered deployed only after frontend and backend URLs both work and the connected Supabase-backed user journey passes. Provider setup screens or a successful build alone do not count as an end-to-end deployment.

## Official provider references

- [Next.js on Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs)
- [Deploy a FastAPI app on Render](https://render.com/docs/deploy-fastapi)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Connect to Supabase Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase Auth redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
- [Supabase JWT signing keys and JWKS verification](https://supabase.com/docs/guides/auth/signing-keys)
- [Supabase Storage bucket access models](https://supabase.com/docs/guides/storage/buckets/fundamentals)
