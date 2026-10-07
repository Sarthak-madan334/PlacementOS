# CampusProof — Product Requirements Document

**Document purpose:** The single product direction for Phase Zero and the implementation agent. Read this before creating or changing application code. Supporting system, architecture, design, and implementation documents are linked below.

## 1. Product definition

CampusProof is an evidence-backed campus placement readiness system for university students. It helps a student answer:

> For the role I want, am I eligible, what evidence shows I am ready, what is holding me back, and what should I do next?

The product turns scattered preparation signals into a focused loop:

**Profile and evidence → role-specific readiness → gaps → prioritized action → reassessment → opportunity match**

The earlier **PlacementOS** name describes this broader product idea. **ResumeSignal** describes the first resume-analysis module/prototype concept. The project name used in code, UI, and deployment is **CampusProof**.

## 2. Users and problem

### Primary user

A university student preparing for internships or campus placements who has coursework, projects, skills, and possibly a resume, but cannot tell which gap matters most for a specific target role or job description.

### Problem

Students use separate tools for coding practice, projects, resumes, applications, and interview preparation. Counts such as CGPA or solved problems do not explain readiness for a particular role. Generic resume scores are hard to trust, and students receive little guidance about the next useful action.

### Product promise

CampusProof gives a transparent, role-specific snapshot and a small number of practical next steps. It explains which input or evidence supports each finding. It does not promise a job, predict hiring outcomes, or claim that an unverified skill is proven.

## 3. MVP scope

The first usable release supports this end-to-end flow:

1. A student enters branch, graduation year, optional CGPA (with its scale), target role, skills, and projects.
2. The student uploads an optional resume (PDF, DOCX, TXT; Markdown may be accepted for local/demo analysis) and reviews extracted information before it is used.
3. The student enters or pastes an optional job description, or selects a saved opportunity with explicit eligibility criteria.
4. CampusProof reports hard eligibility as **Eligible**, **Not eligible**, or **Unknown**; a role-specific readiness score; role-match score when a job description exists; evidence confidence; strengths; critical gaps; and prioritized next actions.
5. The student can correct profile/extracted data and rerun the assessment.

### MVP capabilities

- Student profile and skills/projects evidence.
- Resume parsing and transparent resume quality analysis; parsing is assistive and user-confirmed.
- Role/job-description skill matching with matched and missing requirements.
- Explainable, deterministic readiness factors and recommendations.
- Responsive dashboard with synthetic demo data when no account/backend is configured.
- Optional private resume file storage when upload persistence is enabled.

### Explicitly out of scope for MVP

- Social feed, messaging, generic job board, or automatic scraping of job sites.
- Full learning management system or large question bank.
- College placement administration or multi-tenant institution management.
- Automated application submission or a comprehensive application tracker.
- Machine-learning hiring prediction, fabricated confidence, or claims of guaranteed score improvement.
- LLM dependency for core scoring. The core experience must work without a paid API.

An application timeline, assessment history learning, GitHub evidence sync, interview assessments, and optional AI-assisted rewriting can be considered later, after the core loop is validated.

## 4. Scoring and recommendation rules

- Keep **eligibility**, **readiness**, and **role match** as separate outputs. Failed hard eligibility must never be hidden by a high readiness score.
- Use explicit, versioned, deterministic rules in the MVP. Return the factor scores, weights, evidence, and plain-language reasons behind each result.
- Readiness describes available evidence and preparedness signals; it is not a probability of getting hired. Role match describes overlap with stated requirements, not the employer's actual decision.
- Missing information yields **Unknown** where needed and lowers evidence confidence; it must not silently count as a negative skill or be presented as proof of weakness.
- Resume parsing produces candidate facts with source snippets/locations where practical. The student can correct them. Never treat parser output as verified truth.
- Rank actions using requirement importance, evidence gap, and practical effort. Label time estimates as estimates and omit numerical score-impact promises until measured.
- Store a scoring version and a compact assessment input snapshot so a result can be explained later.

The exact score-factor weights and skill taxonomy are Phase Zero decisions recorded in `SRD.md`; do not invent different formulas independently in frontend and backend.

## 5. Success criteria

The MVP is successful when a student can complete the primary flow on mobile or desktop; correct extracted facts; understand eligibility and score reasons; see which requirements are matched/missing; identify a first action; and retry after recoverable errors. A new contributor can run or preview the UI with synthetic data without waiting for a live backend.

## 6. Team ownership

| Name | Ownership |
|---|---|
| Sarthak | Frontend and student experience |
| Aarush | Backend, parsing, scoring, and API |
| Sejal | System design, data model, and integration/release criteria |

Each owner can start independently against the contracts in `SRD.md` and `ARCHITECTURE.md`. The first deliverables are parallel; integrated release verification follows them.

## 7. Required reading

1. This product brief.
2. [`REQUIREMENTS.md`](REQUIREMENTS.md) and [`TECH_STACK.md`](TECH_STACK.md) — requirement traceability and approved stack.
3. [`SRD.md`](SRD.md) — functional/non-functional requirements and API/scoring contract.
4. [`ARCHITECTURE.md`](ARCHITECTURE.md) — runtime boundaries, data, and identity.
5. [`DESIGN.md`](DESIGN.md) — UI behavior and visual system.
6. [`IMPLEMENTATION_GUIDE.md`](IMPLEMENTATION_GUIDE.md) — SOLID, security, testing, deployment, and independent delivery rules.
7. [`PHASES.md`](PHASES.md) — eight independent workstreams and shared completion criteria.
8. [`SCORING_AND_PARSING.md`](SCORING_AND_PARSING.md) — detailed, versioned analysis rules.
9. [`INTEGRATION_RUNBOOK.md`](INTEGRATION_RUNBOOK.md) — preview connection, smoke checks, and release/rollback steps.

## 8. Direction for Antigravity

Treat the shared specs plus the assigned member specification as the agreed source of truth. Before coding, summarize the chosen MVP flow, proposed repository layout, and any conflict with the contracts. Then implement a runnable vertical slice with fixtures; preserve the API and scoring contract; do not add out-of-scope features or credentials; and show loading, empty, error, and success states. If an implementation detail is genuinely unspecified, choose the simplest reversible option and document it. Do not silently change product behavior or scoring rules.

For phase work, open the owner-prefixed brief linked from [`PHASES.md`](PHASES.md) and [`INTEGRATION_RUNBOOK.md`](INTEGRATION_RUNBOOK.md) when connecting previews. All numbered phases are independently startable; integration is a shared release checkpoint, not a prerequisite between workstreams.
