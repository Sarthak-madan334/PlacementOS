# CampusProof Frontend

Phase 1 student-facing Next.js app. The complete profile-to-results flow runs from synthetic fixtures without the API.

## Run locally

```bash
npm install
copy .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. For a production build, run `npm run typecheck` and `npm run build`.

## Demo behavior

`NEXT_PUBLIC_DEMO_MODE=true` (the default when unset) uses typed `cp-v1` sample results. Profile changes are session-only, and selected files are not uploaded. This isolated fixture path works without the backend.

### Connected local synthetic preview

The backend now provides a stateless `POST /api/v1/assessments/preview` and an in-memory resume parser. To exercise them locally without configuring Supabase, start the backend from `backend/` as described in its README, then start the frontend with:

```powershell
$env:NEXT_PUBLIC_DEMO_MODE = "false"
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm run dev -- --port 3001
```

This preview computes results from the entered profile, explicit required skills, and eligibility rules. Resume facts remain suggestions until copied into editable fields. The preview does not persist profile or resume data; use synthetic data only. The default fixture mode remains available for isolated frontend demos.

## Deploy

Import this repository into Vercel and set the project Root Directory to `frontend`. Add `NEXT_PUBLIC_DEMO_MODE=true` for an independent preview deployment. No backend, database or private secret is needed for the synthetic demo.

## Reference contracts

- `../docs/SRD.md`
- `../docs/DESIGN.md`
- `../documentation/sarthak/PHASE_01_PRODUCT_SHELL.md`
