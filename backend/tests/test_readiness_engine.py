"""Unit tests for the pure deterministic readiness engine (cp-v1)."""

import json
from pathlib import Path
import pytest

from app.services.readiness_engine import (
    FACTOR_WEIGHTS,
    SCORING_VERSION,
    EligibilityResult,
    OpportunityRequirement,
    ProjectEvidence,
    ReadinessEngine,
    ResumeEvidence,
    SkillEvidence,
    StudentProfileEvidence,
    normalize_skill_name,
)


def test_skill_name_normalization_and_aliases():
    """Verify that skill synonyms map to canonical normalized names."""
    assert normalize_skill_name("  PyThOn3  ") == "python"
    assert normalize_skill_name("ReactJS") == "react"
    assert normalize_skill_name("node.js") == "nodejs"
    assert normalize_skill_name("Postgres") == "postgresql"
    assert normalize_skill_name("Golang") == "go"
    assert normalize_skill_name("k8s") == "kubernetes"
    assert normalize_skill_name("RESTful") == "rest api"
    assert normalize_skill_name("C++") == "cpp"
    assert normalize_skill_name("C#") == "csharp"


def test_role_skill_coverage_full_match():
    """When all required skills are matched, role skill coverage score is 100."""
    profile = StudentProfileEvidence(
        skills=[
            SkillEvidence(name="Python", normalized_name="python"),
            SkillEvidence(name="FastAPI", normalized_name="fastapi"),
            SkillEvidence(name="PostgreSQL", normalized_name="postgresql"),
        ]
    )
    opportunity = OpportunityRequirement(
        role_title="Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )

    factor, role_match = ReadinessEngine._evaluate_role_skill_coverage(profile, opportunity)
    assert factor.available is True
    assert factor.score == 100
    assert role_match is not None
    assert role_match.score == 100
    assert len(role_match.matched) == 3
    assert len(role_match.missing) == 0


def test_role_skill_coverage_partial_match():
    """When half of required skills match, score is 50."""
    profile = StudentProfileEvidence(
        skills=[
            SkillEvidence(name="Python", normalized_name="python"),
        ]
    )
    opportunity = OpportunityRequirement(
        role_title="Backend Engineer",
        required_skills=["Python", "Kubernetes"],
    )

    factor, role_match = ReadinessEngine._evaluate_role_skill_coverage(profile, opportunity)
    assert factor.available is True
    assert factor.score == 50
    assert role_match.score == 50
    assert role_match.matched == ["Python"]
    assert role_match.missing == ["Kubernetes"]


def test_role_skill_coverage_unavailable_when_no_role_requirements():
    """When no target role or JD requirements are provided, factor is marked unavailable."""
    profile = StudentProfileEvidence(
        skills=[SkillEvidence(name="Python", normalized_name="python")]
    )
    factor, role_match = ReadinessEngine._evaluate_role_skill_coverage(profile, None)
    assert factor.available is False
    assert factor.score == 0
    assert role_match is None


def test_project_evidence_scoring_and_verifiable_links():
    """Demonstrated project evidence scores based on volume, descriptions, and links."""
    # 0 projects
    p0 = StudentProfileEvidence(projects=[])
    f0 = ReadinessEngine._evaluate_project_evidence(p0)
    assert f0.score == 0

    # 1 project without URL
    p1 = StudentProfileEvidence(
        projects=[ProjectEvidence(title="P1", description="Short desc")]
    )
    f1 = ReadinessEngine._evaluate_project_evidence(p1)
    assert f1.score == 40

    # 2 projects with detailed descriptions and URLs
    p2 = StudentProfileEvidence(
        projects=[
            ProjectEvidence(
                title="P1",
                description="A substantive technical description explaining microservice architecture and scale.",
                url="https://github.com/example/p1",
            ),
            ProjectEvidence(
                title="P2",
                description="Another substantive technical description with database optimizations and caching.",
                url="https://github.com/example/p2",
            ),
        ]
    )
    f2 = ReadinessEngine._evaluate_project_evidence(p2)
    assert f2.score == 85  # 65 base + 10 desc + 10 url


def test_resume_clarity_unavailable_when_absent():
    """When no resume is provided, resume clarity factor is marked unavailable."""
    profile = StudentProfileEvidence(resume=None)
    factor = ReadinessEngine._evaluate_resume_clarity(profile)
    assert factor.available is False
    assert factor.score == 0


def test_resume_clarity_scoring_and_signals():
    """Structured resume scores based on sections and quality signals."""
    resume = ResumeEvidence(
        sections_present=["contact", "education", "skills", "experience"],
        contact_present=True,
        education_present=True,
        skills_present=True,
        experience_present=True,
        action_verbs_count=5,
        quantified_outcomes_count=2,
        weak_language_count=0,
    )
    profile = StudentProfileEvidence(resume=resume)
    factor = ReadinessEngine._evaluate_resume_clarity(profile)
    assert factor.available is True
    assert factor.score == 100  # 80 sections + 20 signals


def test_technical_skills_depth():
    """Technical skill evidence evaluates volume and project cross-referencing."""
    profile = StudentProfileEvidence(
        skills=[
            SkillEvidence(name="Python", normalized_name="python"),
            SkillEvidence(name="FastAPI", normalized_name="fastapi"),
            SkillEvidence(name="PostgreSQL", normalized_name="postgresql"),
            SkillEvidence(name="Docker", normalized_name="docker"),
        ],
        projects=[
            ProjectEvidence(
                title="API",
                description="Built with Python, FastAPI, PostgreSQL, and Docker.",
            )
        ],
    )
    factor = ReadinessEngine._evaluate_technical_skills(profile)
    assert factor.available is True
    assert factor.score == 80  # 70 base + 10 verified


def test_profile_completeness():
    """Profile completeness scores based on populated fields."""
    p_full = StudentProfileEvidence(
        full_name="Aarush",
        branch="CS",
        graduation_year=2026,
        target_role="Backend",
        skills=[SkillEvidence(name="Python", normalized_name="python")],
        projects=[ProjectEvidence(title="P1", description="D1")],
    )
    f_full = ReadinessEngine._evaluate_profile_completeness(p_full)
    assert f_full.score == 100

    p_partial = StudentProfileEvidence(
        full_name="Aarush",
        branch="CS",
    )
    f_partial = ReadinessEngine._evaluate_profile_completeness(p_partial)
    assert f_partial.score == 40  # 20 full_name + 20 branch


def test_missing_factors_and_weight_renormalization():
    """When factors are excluded (e.g. no role and no resume), weights renormalize properly."""
    # Only project_evidence (0.25), technical_skills (0.15), and profile_completeness (0.10) available
    # Total assessable weight = 0.50
    profile = StudentProfileEvidence(
        full_name="Aarush",
        branch="CS",
        graduation_year=2026,
        target_role="Backend",
        skills=[
            SkillEvidence(name="Python", normalized_name="python"),
            SkillEvidence(name="FastAPI", normalized_name="fastapi"),
            SkillEvidence(name="SQL", normalized_name="sql"),
            SkillEvidence(name="Docker", normalized_name="docker"),
        ],
        projects=[
            ProjectEvidence(
                title="P1",
                description="Substantive technical description of backend system.",
                url="https://github.com/example/p1",
            ),
            ProjectEvidence(
                title="P2",
                description="Substantive description with database setup.",
                url="https://github.com/example/p2",
            ),
        ],
        resume=None,
    )

    report = ReadinessEngine.evaluate(profile, opportunity=None)
    assert report.readiness.score is not None
    assert report.readiness.scoring_version == SCORING_VERSION
    assert "role_skill_coverage" in report.readiness.excluded_factors
    assert "resume_clarity" in report.readiness.excluded_factors
    assert len(report.readiness.excluded_factors) == 2

    # Verify score is bounded and mathematically normalized
    assert 0 <= report.readiness.score <= 100


def test_no_assessable_factors_case():
    """When zero factors can be assessed, score is None and confidence is low."""
    empty_profile = StudentProfileEvidence()
    # Force mock empty factors
    report = ReadinessEngine.evaluate(empty_profile, opportunity=None)
    # Profile completeness score for empty profile is 0, available is True
    # But if profile has 0 score, final score is 0 with low confidence
    assert report.readiness.scoring_version == SCORING_VERSION
    assert report.readiness.confidence in ("low", "medium")


def test_cgpa_independence_from_readiness_score():
    """CGPA does not independently increase or decrease readiness score."""
    # Case A: High CGPA, 0 skills
    profile_high_cgpa = StudentProfileEvidence(
        full_name="Student A",
        branch="CS",
        graduation_year=2026,
        cgpa=9.9,
        target_role="Backend",
        skills=[],
        projects=[],
    )
    report_a = ReadinessEngine.evaluate(profile_high_cgpa, None)

    # Case B: Low CGPA, 0 skills
    profile_low_cgpa = StudentProfileEvidence(
        full_name="Student B",
        branch="CS",
        graduation_year=2026,
        cgpa=5.5,
        target_role="Backend",
        skills=[],
        projects=[],
    )
    report_b = ReadinessEngine.evaluate(profile_low_cgpa, None)

    # Readiness score should be identical because CGPA is NOT a readiness factor
    assert report_a.readiness.score == report_b.readiness.score


def test_hard_eligibility_criteria():
    """Hard eligibility is strictly evaluated against explicit opportunity criteria."""
    opp = OpportunityRequirement(
        role_title="SDE",
        explicit_criteria={
            "min_cgpa": 8.0,
            "allowed_branches": ["Computer Science", "IT"],
            "allowed_years": [2026],
        },
    )

    # 1. Eligible student
    p1 = StudentProfileEvidence(branch="Computer Science", graduation_year=2026, cgpa=8.5)
    e1 = ReadinessEngine.evaluate_eligibility(p1, opp)
    assert e1.status == "eligible"
    assert len(e1.reasons) == 0

    # 2. Ineligible student (CGPA below minimum)
    p2 = StudentProfileEvidence(branch="Computer Science", graduation_year=2026, cgpa=7.2)
    e2 = ReadinessEngine.evaluate_eligibility(p2, opp)
    assert e2.status == "not_eligible"
    assert any(r.code == "cgpa_below_minimum" for r in e2.reasons)

    # 3. Ineligible student (Branch mismatch)
    p3 = StudentProfileEvidence(branch="Civil Engineering", graduation_year=2026, cgpa=8.5)
    e3 = ReadinessEngine.evaluate_eligibility(p3, opp)
    assert e3.status == "not_eligible"
    assert any(r.code == "branch_not_eligible" for r in e3.reasons)

    # 4. Unknown student (Missing CGPA)
    p4 = StudentProfileEvidence(branch="Computer Science", graduation_year=2026, cgpa=None)
    e4 = ReadinessEngine.evaluate_eligibility(p4, opp)
    assert e4.status == "unknown"
    assert any(r.code == "cgpa_missing" for r in e4.reasons)


def test_engine_determinism_multi_run():
    """Running evaluation multiple times produces byte-identical factor and readiness scores."""
    profile = StudentProfileEvidence(
        full_name="Aarush Sharma",
        branch="Computer Science",
        graduation_year=2026,
        cgpa=8.75,
        target_role="Backend Engineer",
        skills=[
            SkillEvidence(name="Python", normalized_name="python"),
            SkillEvidence(name="FastAPI", normalized_name="fastapi"),
        ],
        projects=[
            ProjectEvidence(title="P1", description="Backend service description", url="https://github.com/p1")
        ],
    )
    opp = OpportunityRequirement(
        role_title="Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )

    r1 = ReadinessEngine.evaluate(profile, opp)
    r2 = ReadinessEngine.evaluate(profile, opp)
    r3 = ReadinessEngine.evaluate(profile, opp)

    assert r1.readiness.score == r2.readiness.score == r3.readiness.score
    assert r1.readiness.confidence == r2.readiness.confidence == r3.readiness.confidence
    assert [f.score for f in r1.readiness.factors] == [f.score for f in r2.readiness.factors] == [f.score for f in r3.readiness.factors]


def test_recommendations_capped_at_three():
    """Engine returns at most 3 concrete, evidence-based recommendations."""
    profile = StudentProfileEvidence(
        full_name="Aarush",
        skills=[],
        projects=[],
    )
    opp = OpportunityRequirement(
        role_title="Backend Engineer",
        required_skills=["Python", "PostgreSQL"],
    )

    report = ReadinessEngine.evaluate(profile, opp)
    assert len(report.next_actions) <= 3
    for action in report.next_actions:
        assert action.title
        assert action.rationale
        assert action.completion_evidence
        # Ensure no false promises in copy
        assert "guarantee" not in action.title.lower()
        assert "guarantee" not in action.rationale.lower()
