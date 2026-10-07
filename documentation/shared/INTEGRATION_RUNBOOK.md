# CampusProof — Integration and Release Runbook

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for provider-specific Vercel, Render, and Supabase setup values.

## Environment mapping

| Environment | Frontend | Backend | Data/storage |
|---|---|---|---|
| Local | Next.js local server or fixtures | FastAPI local server | Local PostgreSQL/test fixtures; local upload stub |
| Preview | Vercel preview URL | Render preview URL | Separate non-production PostgreSQL project/database and private bucket |
| Production | Vercel production domain | Render production URL | Production PostgreSQL and private storage, independent credentials |

## Connect preview services

1. Confirm frontend fixtures and backend OpenAPI match `SRD.md`.
2. Configure frontend `NEXT_PUBLIC_API_BASE_URL` for the Render preview; turn off fixture mode only for the integration preview.
3. Add the exact Vercel preview origin to backend `CORS_ORIGINS`.
4. Configure matching identity issuer/audience and verify JWT server-side. Use synthetic preview accounts/data.
5. Configure preview-only database and private storage secrets on Render. Never send service-role credentials to Vercel browser variables.
6. Apply migrations, verify `/health/live` and `/health/ready`, and confirm API docs are not publicly exposing sensitive data.
7. Run the smoke checklist below and record commit SHAs, migration revision, URLs, and results.

## End-to-end smoke checklist

- [ ] Landing and demo mode load on mobile and desktop.
- [ ] Sign-in/out works for persisted preview data; guest demo remains synthetic and does not persist.
- [ ] Profile create/update/read works; invalid CGPA/required fields show useful messages.
- [ ] Optional resume parse handles a valid PDF and rejected/oversized/corrupt file; extracted fields require student review.
- [ ] Opportunity with no hard rules produces an assessment without invented eligibility.
- [ ] Missing CGPA against a minimum returns `unknown`; below-minimum CGPA returns `not_eligible` even with high readiness.
- [ ] Assessment shows score factors, confidence, skill match, evidence provenance, gaps, and up to three actions.
- [ ] No JD produces no fabricated role-match score.
- [ ] Another test account cannot access the first account's profile, assessment, or resume object.
- [ ] Resume deletion and profile deletion remove or queue cleanup of the corresponding private object.
- [ ] Browser console and service logs contain no secrets, tokens, resume text, or unhandled errors.

## Release sequence

1. Require relevant CI checks and review before merge.
2. Apply backward-compatible migrations to the target database.
3. Deploy and verify backend readiness; retain deployed commit and migration revision.
4. Deploy/promote frontend configured for that backend.
5. Run smoke checks with synthetic or approved test accounts.
6. Promote only after results are recorded.

## Rollback

Roll back application versions independently when safe. Do not automatically reverse destructive database migrations. Use backward-compatible migrations, a forward fix, or a tested provider restore process. Preserve a record of the last known good app commit and schema revision.
