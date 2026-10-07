# PlacementOS — Requirements and Traceability

This document gives a compact, testable requirements checklist. `SRD.md` remains the detailed functional, API, scoring, and acceptance contract; `PRODUCT_REQUIREMENTS.md` defines product scope.

## Product requirements

| ID | Requirement | Verification |
|---|---|---|
| PR-01 | Help a student assess readiness for a chosen campus placement role. | End-to-end synthetic student and role scenario produces an explained result. |
| PR-02 | Make eligibility, readiness, and role match distinct concepts. | A failed hard criterion remains visible even when readiness is high. |
| PR-03 | Use evidence and show why each gap/action appears. | Every result factor points to evidence or an explicit unavailable reason. |
| PR-04 | Give the student a practical next step. | Up to three actions include rationale and completion evidence. |
| PR-05 | Keep resume analysis optional and correctable. | Manual workflow succeeds without a file; extracted data requires student review. |

## System requirements

| ID | Requirement | Owner / trace |
|---|---|---|
| SYS-01 | Browser UI uses Next.js + TypeScript and deploys independently to Vercel. | Sarthak; [`FRONTEND.md`](../sarthak/FRONTEND.md), Phase 01 and 06 |
| SYS-02 | API uses FastAPI + Python and deploys independently to Render. | Aarush; [`BACKEND.md`](../aarush/BACKEND.md), Phases 02–05 |
| SYS-03 | PostgreSQL is the durable source of truth; changes use migrations. | Shared; `ARCHITECTURE.md`, `BACKEND.md` |
| SYS-04 | PDF/DOCX/TXT resume parsing returns reviewable candidates and warnings. | Aarush; `SCORING_AND_PARSING.md`, Phase 03 |
| SYS-05 | `cp-v1` scoring and role matching are deterministic, bounded, and explainable. | Aarush; `SRD.md`, `SCORING_AND_PARSING.md`, Phases 04–05 |
| SYS-06 | Each member has a separate work folder and can build against fixtures. | All; `PHASES.md`, `CONTRIBUTING.md` |
| SYS-07 | Each workstream has an independent preview/demo and completion checks. | Owner; `PHASES.md` and corresponding phase brief |
| SYS-08 | Persisted personal data requires verified identity and owner-scoped access. | Backend; `ARCHITECTURE.md`, `BACKEND.md` |

## Non-functional requirements

- **Accessibility:** keyboard operation, visible focus, semantic labels, reduced-motion support, and color-independent status.
- **Responsive:** primary flows work from 360 px mobile width through desktop without horizontal scrolling.
- **Reliability:** failures preserve user input; parsing failure does not block manual analysis; health/readiness endpoints have bounded behavior.
- **Privacy:** optional resume, private storage, minimum necessary retention, account deletion behavior, and sensitive-log redaction.
- **Maintainability:** focused modules, typed API boundary, migrations, deterministic domain logic, and tests for scoring/ownership.
- **Deployability:** Vercel and Render previews use isolated non-production credentials/data; integration is verified with synthetic data.

## Release acceptance

The release candidate must pass all applicable checks from `SRD.md` and `INTEGRATION_RUNBOOK.md`: profile flow, optional resume review, role/JD match, unknown and not-eligible rules, explanation display, cross-account denial, responsive/accessibility review, health checks, and private file deletion if uploads are enabled.
