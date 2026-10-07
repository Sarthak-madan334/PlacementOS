# Sarthak — Frontend Specification

## Purpose

Build the student-facing PlacementOS/CampusProof experience in Next.js + TypeScript. The interface makes role-specific readiness understandable and actionable, with a polished glassmorphism dashboard. Use `../shared/DESIGN.md`, `../shared/SRD.md`, and `../shared/TECH_STACK.md` as the visual and technical contracts.

## User flow and screens

1. **Landing/demo:** explain readiness, evidence, and next actions; let the user start manually or open clearly labeled synthetic demo data.
2. **Profile:** branch, graduation year, optional CGPA and scale, target role, skills, and projects. Keep resume optional.
3. **Resume review:** upload progress; supported type/size; extracted editable fields and parser warnings; explicit confirm action.
4. **Opportunity:** target role, optional company/JD, and explicit eligibility criteria where known.
5. **Results:** eligibility/reasons first, readiness score/confidence/factors, role match, strengths/gaps, and up to three next actions.
6. **Edit/reassess:** preserve student input, mark old results as based on a previous snapshot, and allow rerun.

## Visual specification

- Use deep navy/ink canvas, restrained violet/blue gradients, selective translucent glass cards, fine borders, subtle blur, and soft shadows.
- Keep dense forms and explanatory text on sufficiently opaque surfaces for contrast. Use teal for positive evidence, amber for unknown/caution, and red only for explicit failed criteria; every color state has a text label.
- Use clear sans-serif type, large readable result score, concise headings, consistent spacing, medium-radius controls, and restrained animation.
- Respect `prefers-reduced-motion`. Avoid motion or copy that implies guaranteed readiness improvement or hiring results.
- At 360 px, stack result panels, keep key actions reachable, and avoid horizontal scrolling.

## Implementation boundaries

- Keep UI components presentational where practical; keep API transport and fixture selection in `lib/api` or an equivalent small module.
- Define TypeScript types from or aligned with FastAPI OpenAPI. Fixtures conform to `../shared/SRD.md`.
- Use `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_DEMO_MODE`. Browser configuration must never contain database or storage service secrets.
- Do not calculate authoritative eligibility, readiness, or role match in the browser. Render backend response fields as returned.
- For persisted data, use the selected managed auth client and pass tokens through the API client using the documented secure flow. Guest demo uses synthetic data and makes no persistence call.
- Preserve form values on validation, parse, or network errors. Prevent duplicate submissions and provide actionable retry.

## Required UI states

Initial/empty, loading, field validation, upload progress, parse warning, parse failure, API/network failure, unknown eligibility, not eligible, no usable JD, success, and stale result after profile edits. Provide labels, keyboard focus, useful screen-reader names/values for score bars, and text alternatives for graphics.

## Completion checks

- Build and type checks pass; fixture mode demonstrates the entire journey while backend is offline.
- All result variants in Phase 06 render accurately without invented defaults.
- Mobile/desktop and keyboard checks pass; color is never the only status cue.
- Deploy a Vercel preview and record its URL and commit in the release notes.
