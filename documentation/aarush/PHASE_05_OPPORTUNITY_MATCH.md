# Aarush — Phase 05: Opportunity and Role Matching

**Owner:** Aarush  
**Can start:** Immediately, with example job descriptions and profile fixtures  
**Deployable result:** Stand-alone FastAPI match demo  
**Status:** **COMPLETE**

---

## 1. Outcome & Scope

An explicit, explainable comparison between student evidence and a target role or job description, plus hard eligibility checks when criteria are supplied.

Phase 05 is an **evidence comparison system**, not a hiring prediction system. It answers:
> *"How well does the student's currently available evidence match this opportunity?"*

It never produces hiring probabilities, interview prediction, or candidate rankings.

---

## 2. Core Architecture (`rm-v1`)

The matching engine is implemented in `app.services.matching_engine` as a pure, deterministic domain service.

### 2.1 Skill Normalization & Versioned Alias Vocabulary
- **Model Version:** `rm-v1`
- Canonicalizes common naming differences, punctuation, and abbreviations into stable identifiers (e.g., `py`, `python3` -> `python`; `js`, `ecmascript` -> `javascript`; `postgres`, `pg` -> `postgresql`; `k8s` -> `kubernetes`; `fast api` -> `fastapi`).
- Preserves original job description phrases in all evaluation outputs.
- Never conflates distinct technologies (e.g., `Java` != `JavaScript`, `React` != `React Native`, `C` != `C++` != `C#`).

### 2.2 Requirement Classification
Skill requirements are classified only when the text provides evidence:
- **`required`**: Explicit in `required_skills` or under headings such as *Requirements*, *Must have*, *Mandatory*, *Essential*, *Minimum qualifications*.
- **`preferred`**: Explicit in `preferred_skills` or under headings such as *Preferred*, *Nice to have*, *Bonus*, *Good to have*, *Plus*, *Desired*.
- **`unspecified`**: Found in general text without explicit required/preferred section markers.

### 2.3 3-State Evidence Matching
Each requirement is evaluated against candidate evidence (profile skills, parsed resume skills, project descriptions with repository links, experience):
- **`matched`**: Supported by student evidence. Output includes evidence source metadata (e.g., `profile_skill, resume_skill, project:E-Commerce API`).
- **`missing`**: Not demonstrated in available student evidence. Explained safely as *"not demonstrated in available evidence"*, never *"candidate cannot do"*.
- **`unknown`**: Insufficient reliable evidence or ambiguous matching.

### 2.4 Role Match Score Formula
$$\text{Role Match Score} = \text{round}\left(\frac{\text{Matched Assessable Required Skills}}{\text{Total Assessable Required Skills}} \times 100\right)$$

- **No Usable Requirements Case:** When no usable required skills are specified or extracted from the opportunity:
  - `score = null`
  - `reason_code = "NO_ASSESSABLE_REQUIREMENTS"`
  - `explanation = "No usable required skills were specified or extracted from the opportunity."`
- **Preferred Skills:** Evaluated separately for positive coaching insights without lowering the required score or causing hard eligibility failures.

### 2.5 Hard Eligibility Checks
Hard eligibility constraints are evaluated independently from readiness and role-match scores:
- **Minimum CGPA:** Exact boundary checks (`>= min_cgpa`). Missing CGPA yields `unknown` with `CGPA_MISSING`. Below minimum yields `not_eligible` with `CGPA_BELOW_MINIMUM`.
- **Eligible Branches:** Alias-normalized branch matching (`CSE` == `Computer Science and Engineering`). Missing branch yields `unknown` with `BRANCH_MISSING`. Ineligible branch yields `not_eligible` with `BRANCH_NOT_ELIGIBLE`.
- **Graduation Year:** Allowed batch constraint check. Missing year yields `unknown` with `GRADUATION_YEAR_MISSING`. Ineligible year yields `not_eligible` with `GRADUATION_YEAR_NOT_ELIGIBLE`.
- **Precedence:** High readiness and 100% role match **never** override a `not_eligible` status.

---

## 3. Reason Codes

| Code | Status | Meaning |
| :--- | :--- | :--- |
| `NO_ASSESSABLE_REQUIREMENTS` | `score = null` | No usable required skills extracted from opportunity |
| `CGPA_BELOW_MINIMUM` | `not_eligible` | Student CGPA is strictly below the required minimum |
| `BRANCH_NOT_ELIGIBLE` | `not_eligible` | Student branch does not match allowed branch list |
| `GRADUATION_YEAR_NOT_ELIGIBLE` | `not_eligible` | Student graduation batch is not in allowed batches |
| `CGPA_MISSING` | `unknown` | Opportunity requires minimum CGPA but student CGPA is not provided |
| `BRANCH_MISSING` | `unknown` | Opportunity requires eligible branches but student branch is empty |
| `GRADUATION_YEAR_MISSING` | `unknown` | Opportunity requires graduation batch but student year is empty |

---

## 4. API Specification

Base path: `/api/v1/opportunities`

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/opportunities` | Save opportunity requirements and criteria | Yes |
| `GET` | `/api/v1/opportunities` | List owned opportunities | Yes |
| `GET` | `/api/v1/opportunities/{id}` | Read single owned opportunity | Yes |
| `POST` | `/api/v1/opportunities/extract-requirements` | Extract & classify requirements from raw JD text | Yes |
| `POST` | `/api/v1/opportunities/match` | Standalone match demo (profile & opp in payload) | Yes |
| `POST` | `/api/v1/opportunities/{id}/match` | Match authenticated student profile against saved opportunity | Yes |

### Match Response Sample
```json
{
  "matching_version": "rm-v1",
  "eligibility": {
    "status": "eligible",
    "reasons": []
  },
  "role_match": {
    "score": 100,
    "matched_required": ["Git", "Python", "SQL"],
    "missing_required": [],
    "unknown_required": [],
    "matched_preferred": ["Docker"],
    "missing_preferred": ["AWS"],
    "total_required": 3,
    "total_preferred": 2,
    "explanation": "Matched 3 of 3 assessable required skill(s) (100%).",
    "reason_code": null
  },
  "requirements": [
    {
      "original_phrase": "Python",
      "normalized_skill": "python",
      "category": "required",
      "status": "matched",
      "evidence_source": "profile_skill, resume_skill, project:E-Commerce API (with repository link)",
      "matched_text": "Python",
      "explanation": "Demonstrated in student evidence (profile_skill, resume_skill, project:E-Commerce API (with repository link))."
    }
  ],
  "strengths": [
    {
      "label": "Python",
      "evidence": "Demonstrated in student evidence (profile_skill, resume_skill, project:E-Commerce API (with repository link)).",
      "importance": "required",
      "confidence": "high"
    }
  ],
  "gaps": [
    {
      "label": "AWS",
      "importance": "preferred",
      "reason": "Preferred skill for this role."
    }
  ],
  "created_at": "2026-10-07T12:00:00Z"
}
```

---

## 5. Fixtures & CLI Evaluation

- **Fixtures:** `backend/fixtures/role_matching_fixtures.json`
  - Software Engineer (Python, SQL, Git, Docker, AWS)
  - AI/ML Intern (Python, Machine Learning, Statistics, PyTorch, TensorFlow)
  - Data Analyst (SQL, Excel, Data Analysis, Power BI, Tableau)
  - Unspecified requirements edge case
- **CLI Utility:** `backend/app/cli/evaluate_match.py`
  ```bash
  python -m app.cli.evaluate_match
  ```

---

## 6. Verification and Test Results

- **Unit Tests:** `backend/tests/test_matching_engine.py` (10 tests)
- **API Tests:** `backend/tests/test_matching_api.py` (4 tests)
- **Total Backend Suite:** **95 passed, 0 failed**
