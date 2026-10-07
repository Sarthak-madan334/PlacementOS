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

`NEXT_PUBLIC_DEMO_MODE=true` (the default when unset) uses typed `cp-v1` synthetic data. The resume selector validates file type and size but does not upload or parse files. Profile changes are session-only. Set `NEXT_PUBLIC_API_BASE_URL` and disable demo mode only after the API assessment request contract and authentication flow are implemented and agreed with the backend owner.

## Deploy

Import this repository into Vercel and set the project Root Directory to `frontend`. Add `NEXT_PUBLIC_DEMO_MODE=true` for an independent preview deployment. No backend, database or private secret is needed for the synthetic demo.

## Reference contracts

- `../docs/SRD.md`
- `../docs/DESIGN.md`
- `../documentation/sarthak/PHASE_01_PRODUCT_SHELL.md`
