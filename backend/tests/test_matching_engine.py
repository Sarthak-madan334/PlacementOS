"""Unit tests for Phase 05 Opportunity & Role Matching Engine (rm-v1).

Tests skill normalization, requirement extraction, 3-state matching (matched/missing/unknown),
role-match score mathematics, hard eligibility checks, and engine determinism.
"""

from typing import Any, Dict, List
import pytest

from app.services.matching_engine import (
    MATCHING_VERSION,
    ExtractedRequirement,
    MatchingEngine,
    RequirementExtractor,
    normalize_branch_name,
    normalize_skill_name,
)


def test_skill_normalization_and_aliases():
    """Verify skill name normalization, case/whitespace handling, and alias mapping."""
    # Programming languages
    assert normalize_skill_name("Python") == "python"
    assert normalize_skill_name("  python3  ") == "python"
    assert normalize_skill_name("PY") == "python"
    assert normalize_skill_name("JavaScript") == "javascript"
    assert normalize_skill_name("js") == "javascript"
    assert normalize_skill_name("TypeScript") == "typescript"
    assert normalize_skill_name("ts") == "typescript"
    assert normalize_skill_name("golang") == "go"
    assert normalize_skill_name("C++") == "cpp"
    assert normalize_skill_name("C#") == "csharp"
    assert normalize_skill_name(".NET") == "dotnet"

    # Databases
    assert normalize_skill_name("PostgreSQL") == "postgresql"
    assert normalize_skill_name("postgres") == "postgresql"
    assert normalize_skill_name("pg") == "postgresql"
    assert normalize_skill_name("MongoDB") == "mongodb"
    assert normalize_skill_name("mongo") == "mongodb"

    # Frameworks & Tools
    assert normalize_skill_name("React.js") == "react"
    assert normalize_skill_name("reactjs") == "react"
    assert normalize_skill_name("FastAPI") == "fastapi"
    assert normalize_skill_name("fast api") == "fastapi"
    assert normalize_skill_name("Node.js") == "nodejs"
    assert normalize_skill_name("K8s") == "kubernetes"
    assert normalize_skill_name("AWS") == "amazon web services"
    assert normalize_skill_name("GCP") == "google cloud platform"
    assert normalize_skill_name("Power BI") == "power bi"
    assert normalize_skill_name("powerbi") == "power bi"
    assert normalize_skill_name("MS Excel") == "excel"


def test_distinct_technologies_not_conflated():
    """Verify distinct technologies are not conflated (e.g. java != javascript, react != react native)."""
    assert normalize_skill_name("Java") != normalize_skill_name("JavaScript")
    assert normalize_skill_name("React") != normalize_skill_name("React Native")
    assert normalize_skill_name("C") != normalize_skill_name("C++")
    assert normalize_skill_name("C++") != normalize_skill_name("C#")


def test_branch_normalization():
    """Verify branch name normalization and degree stripping."""
    assert normalize_branch_name("Computer Science and Engineering") == "computer science and engineering"
    assert normalize_branch_name("B.Tech CSE") == "computer science and engineering"
    assert normalize_branch_name("B.E. Computer Science") == "computer science"
    assert normalize_branch_name("Information Technology") == "information technology"
    assert normalize_branch_name("B.Tech IT") == "information technology"
    assert normalize_branch_name("Electronics and Communication Engineering") == "electronics and communication engineering"
    assert normalize_branch_name("B.Tech ECE") == "electronics and communication engineering"


def test_requirement_extraction_from_jd_sections():
    """Verify that requirement extractor identifies required, preferred, and unspecified skills."""
    jd_text = """
    Software Engineer - Backend
    
    Requirements:
    - Strong proficiency in Python
    - Hands-on experience with SQL and PostgreSQL
    
    Nice to have:
    - Experience with Docker and AWS
    - Knowledge of Redis
    
    About the team:
    We build distributed services using Git and Linux.
    """

    extracted = RequirementExtractor.extract_from_text(jd_text)
    by_norm = {item.normalized_skill: item for item in extracted}

    # Required section
    assert "python" in by_norm
    assert by_norm["python"].category == "required"
    assert "sql" in by_norm
    assert by_norm["sql"].category == "required"
    assert "postgresql" in by_norm
    assert by_norm["postgresql"].category == "required"

    # Preferred section
    assert "docker" in by_norm
    assert by_norm["docker"].category == "preferred"
    assert "amazon web services" in by_norm
    assert by_norm["amazon web services"].category == "preferred"
    assert "redis" in by_norm
    assert by_norm["redis"].category == "preferred"

    # Unspecified section
    assert "git" in by_norm
    assert by_norm["git"].category == "unspecified"
    assert "linux" in by_norm
    assert by_norm["linux"].category == "unspecified"


def test_role_match_score_exact_calculation():
    """Verify role match score formula: (matched_required / total_required) * 100."""
    candidate = {
        "skills": ["Python", "SQL", "Git"],
        "projects": [
            {
                "title": "Backend Service",
                "description": "Built REST APIs in Python using PostgreSQL and Git.",
                "url": "https://github.com/example/backend",
            }
        ],
        "resume_skills": ["Python", "SQL", "Git"],
    }

    # Case 1: 4 required skills, candidate has 3 (75%)
    opportunity_4req = {
        "required_skills": ["Python", "SQL", "Git", "Docker"],
        "preferred_skills": ["AWS"],
        "explicit_criteria": {},
    }
    report1 = MatchingEngine.evaluate(candidate, opportunity_4req)
    assert report1.role_match.score == 75
    assert sorted(report1.role_match.matched_required) == ["Git", "Python", "SQL"]
    assert sorted(report1.role_match.missing_required) == ["Docker"]
    assert report1.role_match.total_required == 4
    assert report1.role_match.total_preferred == 1

    # Case 2: 3 required skills, candidate has all 3 (100%)
    opportunity_3req = {
        "required_skills": ["Python", "SQL", "Git"],
        "preferred_skills": [],
        "explicit_criteria": {},
    }
    report2 = MatchingEngine.evaluate(candidate, opportunity_3req)
    assert report2.role_match.score == 100
    assert len(report2.role_match.missing_required) == 0

    # Case 3: 0 matched required skills (0%)
    opportunity_nomatch = {
        "required_skills": ["Ruby", "Kotlin", "Swift"],
        "preferred_skills": [],
        "explicit_criteria": {},
    }
    report3 = MatchingEngine.evaluate(candidate, opportunity_nomatch)
    assert report3.role_match.score == 0
    assert len(report3.role_match.matched_required) == 0
    assert len(report3.role_match.missing_required) == 3


def test_no_usable_requirements_returns_null():
    """When opportunity contains no usable skill requirements, role_match.score is None with explanation."""
    candidate = {"skills": ["Python", "SQL"]}
    opportunity = {
        "role_title": "General Role",
        "required_skills": [],
        "preferred_skills": [],
        "jd_text": "We are looking for passionate individuals.",
    }

    report = MatchingEngine.evaluate(candidate, opportunity)
    assert report.role_match.score is None
    assert report.role_match.reason_code == "NO_ASSESSABLE_REQUIREMENTS"
    assert "No usable required skills" in report.role_match.explanation


def test_missing_evidence_semantics():
    """Verify that missing skills are explained as not demonstrated, not unable to perform."""
    candidate = {"skills": ["Python"]}
    opportunity = {"required_skills": ["Python", "SQL"]}

    report = MatchingEngine.evaluate(candidate, opportunity)
    req_items = {r.original_phrase: r for r in report.requirements}

    assert req_items["Python"].status == "matched"
    assert req_items["SQL"].status == "missing"
    assert "was not demonstrated in the available evidence" in req_items["SQL"].explanation


def test_preferred_skills_do_not_penalize_required_score():
    """Preferred skills are evaluated separately and do not lower the required match score."""
    candidate = {
        "skills": ["Python", "SQL"],
        "projects": [],
        "resume_skills": ["Python", "SQL"],
    }
    opportunity = {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Docker", "Kubernetes", "AWS"],  # All 3 preferred missing
    }

    report = MatchingEngine.evaluate(candidate, opportunity)
    # Required skills are 2/2 = 100%, even though preferred skills are missing
    assert report.role_match.score == 100
    assert report.role_match.matched_required == ["Python", "SQL"]
    assert report.role_match.missing_preferred == ["AWS", "Docker", "Kubernetes"]


def test_hard_eligibility_cgpa_boundary_and_reasons():
    """Verify CGPA eligibility criteria boundaries (above, equal, below, missing)."""
    criteria = {"min_cgpa": 7.5}

    # 1. Above minimum -> Eligible
    cand_above = {"cgpa": 8.0, "branch": "CS", "graduation_year": 2026}
    res_above = MatchingEngine.evaluate_eligibility(cand_above, criteria)
    assert res_above.status == "eligible"
    assert len(res_above.reasons) == 0

    # 2. Exactly at minimum -> Eligible
    cand_exact = {"cgpa": 7.5, "branch": "CS", "graduation_year": 2026}
    res_exact = MatchingEngine.evaluate_eligibility(cand_exact, criteria)
    assert res_exact.status == "eligible"

    # 3. Below minimum -> Not Eligible
    cand_below = {"cgpa": 7.49, "branch": "CS", "graduation_year": 2026}
    res_below = MatchingEngine.evaluate_eligibility(cand_below, criteria)
    assert res_below.status == "not_eligible"
    assert len(res_below.reasons) == 1
    assert res_below.reasons[0].code == "CGPA_BELOW_MINIMUM"
    assert "7.49" in res_below.reasons[0].message

    # 4. Missing CGPA -> Unknown
    cand_missing = {"cgpa": None, "branch": "CS", "graduation_year": 2026}
    res_missing = MatchingEngine.evaluate_eligibility(cand_missing, criteria)
    assert res_missing.status == "unknown"
    assert len(res_missing.reasons) == 1
    assert res_missing.reasons[0].code == "CGPA_MISSING"


def test_hard_eligibility_branch_constraints():
    """Verify branch eligibility constraints and normalization."""
    criteria = {
        "allowed_branches": ["Computer Science", "Information Technology"],
    }

    # 1. CSE matches Computer Science
    cand_cse = {"branch": "Computer Science and Engineering", "cgpa": 8.0}
    res_cse = MatchingEngine.evaluate_eligibility(cand_cse, criteria)
    assert res_cse.status == "eligible"

    # 2. IT matches Information Technology
    cand_it = {"branch": "B.Tech IT", "cgpa": 8.0}
    res_it = MatchingEngine.evaluate_eligibility(cand_it, criteria)
    assert res_it.status == "eligible"

    # 3. Civil Engineering fails
    cand_civil = {"branch": "Civil Engineering", "cgpa": 8.0}
    res_civil = MatchingEngine.evaluate_eligibility(cand_civil, criteria)
    assert res_civil.status == "not_eligible"
    assert res_civil.reasons[0].code == "BRANCH_NOT_ELIGIBLE"

    # 4. Missing branch -> unknown
    cand_no_branch = {"branch": None, "cgpa": 8.0}
    res_no_branch = MatchingEngine.evaluate_eligibility(cand_no_branch, criteria)
    assert res_no_branch.status == "unknown"
    assert res_no_branch.reasons[0].code == "BRANCH_MISSING"


def test_hard_eligibility_graduation_year_constraints():
    """Verify graduation year constraints."""
    criteria = {"allowed_years": [2026, 2027]}

    cand_2026 = {"graduation_year": 2026}
    assert MatchingEngine.evaluate_eligibility(cand_2026, criteria).status == "eligible"

    cand_2025 = {"graduation_year": 2025}
    res_2025 = MatchingEngine.evaluate_eligibility(cand_2025, criteria)
    assert res_2025.status == "not_eligible"
    assert res_2025.reasons[0].code == "GRADUATION_YEAR_NOT_ELIGIBLE"

    cand_no_yr = {"graduation_year": None}
    res_no_yr = MatchingEngine.evaluate_eligibility(cand_no_yr, criteria)
    assert res_no_yr.status == "unknown"
    assert res_no_yr.reasons[0].code == "GRADUATION_YEAR_MISSING"


def test_hard_ineligibility_with_100_percent_role_match():
    """High role match cannot override hard ineligibility."""
    candidate = {
        "full_name": "Priya",
        "branch": "Computer Science",
        "graduation_year": 2026,
        "cgpa": 6.8,  # Below 7.5
        "skills": ["Python", "SQL", "Git"],
        "projects": [
            {
                "title": "Backend Services",
                "description": "Built microservices with Python, SQL, and Git.",
                "url": "https://github.com/example/p",
            }
        ],
        "resume_skills": ["Python", "SQL", "Git"],
    }
    opportunity = {
        "required_skills": ["Python", "SQL", "Git"],
        "explicit_criteria": {"min_cgpa": 7.5},
    }

    report = MatchingEngine.evaluate(candidate, opportunity)
    assert report.role_match.score == 100
    assert report.eligibility.status == "not_eligible"
    assert report.eligibility.reasons[0].code == "CGPA_BELOW_MINIMUM"


def test_matching_engine_determinism_multi_run():
    """Identical inputs produce 100% identical match outputs across multiple executions."""
    candidate = {
        "full_name": "Aarush",
        "branch": "Computer Science",
        "graduation_year": 2026,
        "cgpa": 8.5,
        "skills": ["Python", "SQL", "Docker", "FastAPI"],
        "projects": [
            {
                "title": "API Engine",
                "description": "Engineered backend in Python with FastAPI and SQL.",
                "url": "https://github.com/example/api",
            }
        ],
    }
    opportunity = {
        "role_title": "Backend Engineer",
        "required_skills": ["Python", "FastAPI", "SQL"],
        "preferred_skills": ["Docker", "AWS"],
        "explicit_criteria": {"min_cgpa": 7.0, "allowed_branches": ["Computer Science"]},
    }

    report_initial = MatchingEngine.evaluate(candidate, opportunity)
    for _ in range(5):
        report_iter = MatchingEngine.evaluate(candidate, opportunity)
        assert report_iter.matching_version == MATCHING_VERSION
        assert report_iter.eligibility.status == report_initial.eligibility.status
        assert report_iter.role_match.score == report_initial.role_match.score
        assert report_iter.role_match.matched_required == report_initial.role_match.matched_required
        assert report_iter.role_match.missing_required == report_initial.role_match.missing_required
        assert report_iter.role_match.matched_preferred == report_initial.role_match.matched_preferred
        assert report_iter.role_match.missing_preferred == report_initial.role_match.missing_preferred
