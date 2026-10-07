# Sarthak — Phase 01: Product Shell and Responsive Design System

**Owner:** Sarthak
**Can start:** Immediately, using synthetic fixtures
**Deployable result:** Vercel preview

## Outcome

A polished CampusProof Next.js + TypeScript shell that communicates role-specific readiness and supports navigation through the key screens. It must remain demonstrable with the backend offline.

## Build

- Set up Next.js app structure, shared layout, navigation, typography, color tokens, spacing, glass surfaces, buttons, cards, form controls, badges, and accessible focus states from [`../shared/DESIGN.md`](../shared/DESIGN.md).
- Add landing/demo entry, profile setup, resume review, opportunity setup, and results routes. Screens may use fixtures at this phase.
- Add explicit fixture mode (`NEXT_PUBLIC_DEMO_MODE`) and typed fixture data matching [`../shared/SRD.md`](../shared/SRD.md).
- Implement responsive layout starting at 360 px; support keyboard navigation and reduced motion.
- Add loading, empty, validation, parse failure, API unavailable, unknown eligibility, not-eligible, and success states.

## Acceptance

- `npm run build` and the configured type/lint checks pass.
- All routes are reachable; fixture mode completes a sample profile-to-results journey.
- Layout does not horizontally overflow at 360 px; controls have labels and visible focus.
- Score meaning and eligibility do not rely on color alone.
- No secrets or real student information appear in the browser bundle or fixtures.

## Independence contract

Use local typed fixtures with `cp-v1` response structure. Do not wait for live API or database. Keep transport behind an API client boundary so changing from fixture to HTTP mode does not rewrite views.
