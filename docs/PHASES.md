# CampusProof — Parallel Phase Plan

These are **independent workstreams**, not a sequence of prerequisites. All eight can start in parallel from the five Phase Zero documents. Each owner can use synthetic fixtures and a stub for any service that is not ready. The only shared rule is the interface contract in `SRD.md`; propose changes there and update both producer and consumer fixtures together.

Every workstream must finish as a runnable, testable, independently demonstrable deployment or artifact. Local completion alone is not done. Shared integration happens after independently deployable work is ready; it does not block workstream development.

## Workstream map

| Phase | Deliverable | Owner | Independent demonstration |
|---|---|---|---|
| 01 | [Sarthak — Product shell and responsive design system](../documentation/sarthak/PHASE_01_PRODUCT_SHELL.md) | Sarthak | Vercel preview with navigable screens and fixture mode |
| 02 | [Aarush — Profile and evidence API](../documentation/aarush/PHASE_02_PROFILE_EVIDENCE_API.md) | Aarush | Render preview; API requests against isolated PostgreSQL or local synthetic mode |
| 03 | [Aarush — Resume parsing and review contract](../documentation/aarush/PHASE_03_RESUME_PARSER.md) | Aarush | Stand-alone parser API/demo with sample files and no database requirement |
| 04 | [Aarush — Explainable readiness scoring engine](../documentation/aarush/PHASE_04_READINESS_ENGINE.md) | Aarush | Deterministic CLI/API demo with fixtures and unit tests |
| 05 | [Aarush — Opportunity and role matching](../documentation/aarush/PHASE_05_OPPORTUNITY_MATCH.md) | Aarush | Stand-alone API/demo with fixture profiles and JDs |
| 06 | [Sarthak — Results dashboard and action plan](../documentation/sarthak/PHASE_06_RESULTS_DASHBOARD.md) | Sarthak | Vercel preview rendering contract fixtures, including all result states |
| 07 | [Sejal — System, security, and data design validation](../documentation/sejal/PHASE_07_SYSTEM_SECURITY_DATA.md) | Sejal | Reviewed schema, threat/privacy notes, and deploy checklist in Markdown |
| 08 | [Sejal — Deployment and integration harness](../documentation/sejal/PHASE_08_DEPLOY_AND_INTEGRATE.md) | Sejal | Preview environments, health/smoke workflow, and reproducible integration instructions |

Each phase brief is stored in its owner's folder so independent edits stay separated.

## Definition of done for every phase

1. Scope and acceptance checks in its phase brief are met.
2. Input/output shapes match `SRD.md`; demo data is synthetic.
3. Validation and expected failure states are visible and handled.
4. Relevant automated checks pass and are recorded.
5. A preview URL or versioned reviewable artifact exists.
6. The deliverable can be shown without waiting for another phase.
7. Secrets and real student data are absent from source control and demos.

## Shared integration gate

After workstreams independently meet their completion criteria, connect the frontend to the API, use an isolated preview database/storage bucket, verify auth and CORS, then follow `INTEGRATION_RUNBOOK.md`. Integration is a release checkpoint; do not turn it into a blocking dependency for parallel implementation.
