# Aarush — Phase 05: Opportunity and Role Matching

**Owner:** Aarush
**Can start:** Immediately, with example job descriptions and profile fixtures
**Deployable result:** Stand-alone FastAPI match demo

## Outcome

An explicit, explainable comparison between student evidence and a target role or job description, plus hard eligibility checks when criteria are supplied.

## Build

- Define a versioned, small skill alias vocabulary and retain original JD phrases in outputs.
- Separate required, preferred, and unspecified-priority terms when the text clearly supports that distinction. Do not guess priority when ambiguous.
- Return matched, missing, and unknown terms; absence in the resume means “not shown,” not “cannot do.”
- Compute role match as matched assessable required skills divided by assessable required skills; return null with an explanation if no usable requirements exist.
- Check branch, graduation year, and minimum CGPA only when the opportunity has explicit criteria. Return eligible/not_eligible/unknown with reason codes.
- Provide sample role and JD fixtures for Software Engineer, AI/ML Intern, and Data Analyst. Avoid scraping job sites.

## Acceptance

- Tests cover alias matching, duplicates, case/whitespace, unknown terms, no usable requirements, and each eligibility boundary.
- High readiness cannot override a failed hard eligibility rule.
- No requirement is silently dropped from the explanation.
- Deploy endpoint/demo independently of profile persistence, resume parser, and frontend.

## Independence contract

Use hand-authored profile and JD JSON fixtures matching [`../shared/SRD.md`](../shared/SRD.md). This phase can run even if profile CRUD and parser are unfinished.
