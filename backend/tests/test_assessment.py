from app.services.assessment import build_assessment
from app.api.v1.schemas.assessment import AssessmentPreviewRequest


def assess(profile: dict, opportunity: dict | None = None) -> dict:
    request = AssessmentPreviewRequest.model_validate({"profile": profile, "opportunity": opportunity or {}})
    return build_assessment(request)


def test_no_role_requirements_are_reported_as_unavailable_not_zero():
    result = assess({"target_role": "Engineer", "skills": ["Python"]})
    assert result["role_match"]["score"] is None
    factor = next(item for item in result["readiness"]["factors"] if item["key"] == "role_skill_coverage")
    assert factor["score"] is None
    assert not factor["available"]


def test_empty_profile_has_no_fabricated_readiness_score():
    result = assess({})
    assert result["readiness"]["score"] is None
    assert result["readiness"]["confidence"] == "low"


def test_role_match_recognizes_aliases_and_project_evidence():
    result = assess(
        {"skills": ["React"], "projects": [{"title": "Web app", "description": "Built a TypeScript app with React."}]},
        {"required_skills": ["react.js", "TypeScript", "SQL"]},
    )
    assert result["role_match"]["matched"] == ["React", "TypeScript"]
    assert result["role_match"]["missing"] == ["SQL"]
    assert result["role_match"]["score"] == 67


def test_explicit_eligibility_rules_distinguish_unknown_and_ineligible():
    opportunity = {"minimum_cgpa": 8.0, "cgpa_scale": 10, "eligible_branches": ["Computer Science"], "graduation_years": [2027]}
    unknown = assess({"branch": "Computer Science", "graduation_year": 2027}, opportunity)
    assert unknown["eligibility"]["status"] == "unknown"
    ineligible = assess({"branch": "Mechanical", "graduation_year": 2027, "cgpa": 9, "cgpa_scale": 10}, opportunity)
    assert ineligible["eligibility"]["status"] == "not_eligible"


def test_cgpa_criteria_compare_equivalent_scales():
    result = assess({"cgpa": 8, "cgpa_scale": 10}, {"minimum_cgpa": 3.2, "cgpa_scale": 4})
    assert result["eligibility"]["status"] == "eligible"


def test_explicit_minimum_cgpa_and_graduation_boundaries():
    below = assess({"cgpa": 7.9, "cgpa_scale": 10, "graduation_year": 2027}, {"minimum_cgpa": 8, "cgpa_scale": 10, "graduation_years": [2027]})
    wrong_year = assess({"cgpa": 8, "cgpa_scale": 10, "graduation_year": 2028}, {"minimum_cgpa": 8, "cgpa_scale": 10, "graduation_years": [2027]})
    assert below["eligibility"]["status"] == "not_eligible"
    assert wrong_year["eligibility"]["status"] == "not_eligible"


def test_preferred_skills_do_not_change_required_match_score():
    result = assess({"skills": ["React"]}, {"required_skills": ["React", "SQL"], "preferred_skills": ["Docker"]})
    assert result["role_match"]["score"] == 50
    assert result["role_match"]["preferred"] == ["Docker"]


def test_readiness_renormalizes_available_factors_and_caps_actions():
    result = assess(
        {"target_role": "Developer", "branch": "CS", "graduation_year": 2027, "skills": ["Python"]},
        {"required_skills": ["SQL", "React", "Unmapped framework"]},
    )
    assert result["readiness"]["score"] is not None
    assert "resume_clarity" in result["readiness"]["excluded_factors"]
    assert len(result["next_actions"]) <= 3
    assert result["role_match"]["unknown"] == ["Unmapped framework"]


def test_assessment_preview_api_returns_contract(client):
    response = client.post(
        "/api/v1/assessments/preview",
        json={
            "profile": {"target_role": "Developer", "skills": ["Python"]},
            "opportunity": {"required_skills": ["Python", "SQL"]},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["scoring_version"] == "cp-v1"
    assert payload["role_match"]["score"] == 50
    assert "user_id" not in payload


def test_description_term_extraction_does_not_double_count_aliases():
    result = assess({"skills": ["Testing"]}, {"description": "Experience with REST API and unit testing."})
    assert result["role_match"]["missing"] == ["REST API", "Unit testing"]
