# CampusProof — Software Requirements and Interface Specification

## 1. Purpose and boundaries

This document converts the product brief into behavior that frontend and backend can implement independently. MVP services use Next.js + TypeScript on Vercel, FastAPI + Python on Render, and Supabase PostgreSQL, Auth, and private Storage. GitHub is the source repository. Core analysis must not require paid APIs.

## 2. User journeys and requirements

### J1 — Build or edit a student profile

Student can explore the synthetic demo without an account. To persist personal data, student signs in through managed auth, then enters full name, branch, graduation year, CGPA and scale if known, target role, skills, and projects. The profile can be saved without a resume. Validate required fields in the browser for feedback and again in the API. Preserve entries after recoverable errors.

### J2 — Add resume evidence

Student selects a supported file, sees accepted types and size before upload, and receives upload/parse progress. The parser returns extracted facts and warnings; student reviews and edits before accepting. A parse failure leaves the profile usable and offers manual entry/retry. Resume is optional.

### J3 — Evaluate against a role

Student supplies a target role and optionally a job description. When explicit opportunity criteria exist, the system checks minimum CGPA, eligible branches, and graduation years. Missing criteria/profile values produce `unknown`, not a guessed pass/fail.

### J4 — Understand and act

Results put eligibility status and its reasons first, then readiness and role-match scores, confidence, factors, evidence, gaps, and next actions. Each action ties to a specific gap and is achievable. Student can revise inputs and reassess.

## 3. Functional requirements

- **FR-01 Profile:** Create/read/update the authenticated student's own profile, skills, and projects. Never accept a trusted owner ID from the client.
- **FR-00 Identity:** Use managed authentication for saved student data. Guest demo uses synthetic fixtures and does not persist personal information. API verifies access tokens for every persisted-data endpoint.
- **FR-02 Resume:** Accept PDF/DOCX/TXT up to 5 MiB in the first hosted release. Validate extension, content type, and file signature where applicable. Show unsupported, too-large, empty, corrupt, and parse-failed states.
- **FR-03 Review extraction:** Return extracted fields with parser warnings and allow student edits before assessment. Do not auto-overwrite confirmed profile data without consent.
- **FR-04 Role match:** Normalize target role/JD requirements against a versioned skill vocabulary; return matched skills, missing skills, and unknown requirements. Keep original wording available for explanation.
- **FR-05 Eligibility:** Return exactly `eligible`, `not_eligible`, or `unknown`, plus reason codes and readable reasons. A failed explicit hard rule yields `not_eligible`; an unknown required value yields `unknown` unless another known hard rule already proves ineligibility.
- **FR-06 Readiness:** Return a 0–100 deterministic score, factor breakdown, evidence references, confidence (`low`, `medium`, `high`), and scoring version. Do not equate missing evidence with confirmed lack of skill.
- **FR-07 Recommendations:** Return up to three prioritized actions. Each action names the gap, rationale, and suggested completion evidence. Do not claim guaranteed score increase or job outcome.
- **FR-08 History:** Persist assessments for the owner, including version and compact inputs needed to explain the result. No public profile is exposed.
- **FR-09 Delete:** Allow account/profile deletion and remove relational data plus stored resume objects; report partial cleanup safely and provide retryable operational cleanup.
- **FR-10 Health:** Expose liveness and readiness routes. Liveness checks the process; readiness checks essential database connectivity with a short timeout.

## 4. Scoring contract for MVP (`cp-v1`)

These weights are product heuristics for transparent coaching, not validated hiring predictors. Use them consistently in code and UI; change them only through a documented scoring version update.

| Factor | Weight | What can support it |
|---|---:|---|
| Role skill coverage | 30% | Explicit role/JD requirements mapped to student skills and evidence |
| Demonstrated project/work evidence | 25% | Projects, internships, hackathons, achievements with descriptions/links |
| Resume clarity and completeness | 20% | Parsed structure, sections, readable dates/contact/experience; no aesthetic bias |
| Technical skill evidence | 15% | Student claims plus linked project/resume evidence; claims alone have lower confidence |
| Profile completeness | 10% | Relevant profile fields needed to assess the chosen role |

Each factor is 0–100 and weighted into the total, rounded to an integer. If a factor cannot be assessed, mark it unavailable and renormalize only across assessable factors; show excluded factors and reduce confidence. Eligibility is never part of readiness arithmetic. Academic thresholds are used only for explicit eligibility criteria; CGPA is not a general employability penalty.

Role match is separate: matched required skills / assessable required skills × 100. Return `null` with an explanation when no usable requirements exist. Distinguish required from preferred JD terms when extraction can determine that reliably; otherwise mark priority `unspecified`.

Evidence confidence reflects source quality: self-reported claim < resume mention < described project/work with link or measurable result < directly verified external evidence (not part of MVP unless specifically implemented). Never label unverified content as verified.

## 5. API contract

Base path: `/api/v1`; OpenAPI generated by FastAPI is authoritative. JSON uses UUIDs and UTC ISO 8601 timestamps. All user-data routes require verified identity. Standard error body: `{"detail":"Readable message","code":"stable_code"}`. No stack traces or provider details are returned.

| Method/path | Behavior |
|---|---|
| `GET /health/live` | Process liveness |
| `GET /health/ready` | Dependency readiness |
| `GET /api/v1/me/profile` | Get current student's profile |
| `PUT /api/v1/me/profile` | Create/update current student's profile |
| `POST /api/v1/resumes/parse` | Parse uploaded file or authorized storage object; return reviewable extracted facts |
| `POST /api/v1/assessments/preview` | Guest, non-persistent assessment of a supplied synthetic profile/opportunity snapshot; no history is created |
| `POST /api/v1/opportunities` | Save role/JD and explicit eligibility criteria |
| `POST /api/v1/assessments` | Assess current profile against target role/opportunity |
| `GET /api/v1/assessments/{id}` | Read an owned assessment |
| `DELETE /api/v1/me/profile` | Delete profile and dependent data/files |

Assessment response shape:

```json
{
  "id": "uuid",
  "eligibility": {"status": "unknown", "reasons": [{"code": "cgpa_missing", "message": "Add CGPA to check this requirement."}]},
  "readiness": {
    "score": 72,
    "confidence": "medium",
    "scoring_version": "cp-v1",
    "factors": [{"key": "role_skill_coverage", "score": 70, "weight": 0.3, "available": true, "evidence": ["skill:python"]}],
    "excluded_factors": []
  },
  "role_match": {"score": 78, "matched": ["Python"], "missing": ["SQL"], "unknown": []},
  "strengths": [{"label": "Python", "evidence": "Listed in profile and project description", "confidence": "medium"}],
  "gaps": [{"label": "SQL", "importance": "required", "reason": "Required in the opportunity description."}],
  "next_actions": [{"title": "Add SQL evidence", "rationale": "SQL is a required role skill without project evidence.", "completion_evidence": "Link a project or describe a query-based task."}],
  "created_at": "2026-10-07T12:00:00Z"
}
```

Return `422` for invalid fields, `401` for missing/invalid identity, `403` for forbidden access, `404` for absent/other-owner resources, and safe `5xx` errors for unexpected failures. Never reveal whether another user's resource exists.

## 6. Non-functional requirements

- **Responsive:** Core flow usable at 360 px viewport width and larger.
- **Accessible:** Keyboard navigation, visible focus, form labels, semantic landmarks, reduced-motion support, color-independent statuses, and text alternatives for charts.
- **Performance:** No synchronous paid service calls. Keep ordinary assessment requests responsive; show progress for file parsing and bound external-service timeouts.
- **Privacy:** Resume upload is optional; files private; identity and ownership enforced on server; only necessary information retained.
- **Reliability:** Parser/storage failure must not prevent manual profile analysis. Frontend can run a complete demo with fixtures.
- **Maintainability:** Typed API boundaries, deterministic scoring module, migrations, and meaningful tests for scoring and access control.
- **Deployment:** Each component can be built and previewed independently. Integrated release requires public URL checks and smoke verification.

## 7. Acceptance scenarios

1. Missing CGPA plus a minimum CGPA rule returns `unknown` with a request to add CGPA.
2. CGPA below an explicit minimum returns `not_eligible`, even if readiness is high.
3. No JD yields readiness results and `role_match.score = null` with an explanation.
4. Unparsed/empty resume does not prevent manual profile and project analysis.
5. Missing SQL evidence appears as a role gap only if the target requires SQL; it is not reported as proven inability.
6. A student cannot read or delete another student's profile, assessment, or file by guessing an ID.
7. Frontend fixtures can demonstrate loading, empty, parse failure, unknown eligibility, and completed assessment with backend offline.
