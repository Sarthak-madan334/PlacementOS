# Sarthak — Phase 06: Results Dashboard and Action Plan

**Owner:** Sarthak
**Can start:** Immediately, with fixtures from [`../../docs/SRD.md`](../../docs/SRD.md)
**Deployable result:** Vercel preview

## Outcome

A readable results experience that helps a student understand eligibility, evidence, role match, readiness factors, and their next action without needing the live backend.

## Build

- Put eligibility state/reasons and next best action near the top of the page.
- Show readiness score, confidence, scoring version/disclosure, and factor breakdown with text equivalents.
- Show role-match matched/missing/unknown skills; hide the numeric match when requirements are unavailable.
- Label evidence sources (self-report, resume, project) and distinguish missing evidence from lack of skill.
- Show no more than three prioritized actions, each with rationale and completion evidence.
- Add fixture variants for eligible, not eligible, unknown, no JD, sparse profile, parse warning, API error, and prior assessment stale after edits.

## Acceptance

- UI displays API values without recalculating eligibility or scores.
- All result states are keyboard-accessible, color-independent, responsive, and understandable without chart interaction.
- Error/retry retains student input; changes to profile indicate that the displayed assessment is from an older snapshot.
- Preview is fully navigable and demonstrable in fixture mode with the backend offline.

## Independence contract

Use fixture objects validated against [`../../docs/SRD.md`](../../docs/SRD.md). Do not wait for scoring, matching, storage, or database implementation.
