# CampusProof — Scoring and Resume Analysis Details

This document specifies implementation boundaries for the two most trust-sensitive outputs. `SRD.md` remains the API and factor contract.

## Resume analysis stages

1. **Validate:** enforce 5 MiB maximum and allowed type (PDF, DOCX, TXT); reject empty or corrupt input with stable error codes.
2. **Extract:** format adapter returns text, page/paragraph locations where available, and extraction warnings.
3. **Normalize:** normalize whitespace and line breaks while preserving the original content for traceability; do not log full text.
4. **Detect:** identify likely sections (education, experience, projects, skills, achievements), dates, measurable quantities, action verbs, and configured skill aliases.
5. **Explain:** every quality signal points to an observed section/text or a named heuristic. Distinguish absent section from failed extraction.
6. **Review:** return candidate facts; student edits and confirms before profile persistence or readiness scoring.

### Parser output principles

- Treat resume content as untrusted text; never execute macros, links, scripts, or embedded objects.
- Do not infer a skill from a job title alone. A detected skill is “mentioned,” not verified.
- Do not penalize nonstandard but readable layouts as though they were objectively inferior. Explain structural checks as heuristics.
- Partial extraction returns partial results plus warnings; total failure leaves manual entry available.
- Keep PII out of application logs and analytics. Temporary parser memory is preferable to durable raw-text storage.

## `cp-v1` calculation

Each factor scores 0–100 using explicit, test-covered rules. Total is the weighted average of available factors:

```text
total = round(sum(factor_score * factor_weight for available factors)
              / sum(factor_weight for available factors))
```

Factor weights: role skill coverage 0.30; demonstrated project/work evidence 0.25; resume clarity/completeness 0.20; technical skill evidence 0.15; profile completeness 0.10. An unavailable factor is excluded from numerator and denominator, listed in `excluded_factors`, and lowers confidence. If no factors are assessable, return score null and confidence low; do not fabricate zero.

Keep the factor subrules explicit and versioned in code/config. Inputs need provenance: `self_reported`, `resume_mentioned`, `project_described`, or `externally_verified`. MVP normally uses the first three only. Stronger provenance may raise evidence confidence but cannot claim independent verification unless a verification mechanism exists.

## Eligibility and role match are separate

- Eligibility only evaluates explicit opportunity criteria. Missing required profile data produces unknown unless another known criterion already proves ineligibility.
- Role match counts assessable required terms. Keep preferred terms separately visible and do not mix them into the required match denominator.
- If skill taxonomy cannot map a JD term, return it under unknown for review. Do not silently discard or mark it absent.
- Readiness is an evidence-based coaching index, not a probability of interview or offer.

## Recommendation ranking

Rank no more than three actions using this ordered logic:

1. A failed hard eligibility rule yields a clarify/fix-eligibility action only when the student can supply or correct the information; never recommend an impossible workaround.
2. Prefer explicitly required JD gaps over preferred or unspecified items.
3. Prefer gaps with weak/missing evidence that can be addressed using a concrete project, assessment, or resume correction.
4. Break ties with lower estimated effort, if effort data exists; label effort as an estimate.
5. Explain why each action is listed and what would count as completion evidence.

Do not present estimated readiness-point increases until the team has outcome data and a documented validation method.

### Implemented deterministic preview rules

`backend/app/services/assessment.py` is the current reference implementation. These simple coaching heuristics are intentionally visible and are not empirically validated:

- **Role skill coverage:** matched supported required skills divided by supported required skills. Skills can be entered explicitly or recognized from the role description. Unknown explicitly entered terms are returned separately and excluded from the denominator. Preferred terms do not affect this score.
- **Project/work evidence:** average per-project rule score: 35 for a supplied project, +20 for a description of at least 20 words, +20 for a link, +15 for a quantified result, and +10 when a listed profile skill appears in the description; cap each project at 100.
- **Resume clarity:** 25 points each for detected Education, Experience, Projects, and Skills sections. The factor is unavailable until a parse result is supplied; resume upload is optional.
- **Technical skill evidence:** 40 points for at least one self-reported skill, plus 20 for each listed skill mentioned in project descriptions; cap at 100. This is not verification.
- **Profile completeness:** 25 points each for target role, branch, graduation year, and at least one skill. CGPA, projects, and resume are not completeness requirements.
- **Eligibility:** only explicit entered CGPA, branch, or graduation-year criteria are evaluated. CGPA values are compared as a proportion of their declared grading scales. A known failed rule takes precedence over missing values; otherwise missing required values return `unknown`.

The API exposes these rules through `POST /api/v1/assessments/preview`. It is an unauthenticated, non-persistent guest preview and must receive synthetic data only. Persisted, authenticated assessment history remains unimplemented.

## Public profile context

- A submitted GitHub URL is validated as a `github.com/{username}` profile. The backend reports the public profile's repository count, summarizes primary-language labels across at most 100 recently updated public repositories owned by the user, and samples public push events for distinct visible commit SHAs. The event sample is bounded (one page, at most 100 events) and is not total commits, total contributions, or a skill-quality score. Private activity is not available. GitHub API failure does not block the assessment.
- Optional `GITHUB_TOKEN` is a backend-only secret that can raise GitHub API rate limits. Never expose it in a `NEXT_PUBLIC_*` variable.
- LinkedIn handling validates and echoes only an `linkedin.com/in/{profile}` URL. It does not fetch, scrape, or verify LinkedIn profile content or activity; “link detected” means only that a syntactically valid URL was supplied.
- Profile-link results are returned with the non-persistent assessment response and are not saved. The UI must disclose that a user-submitted URL is checked when assessment runs.
