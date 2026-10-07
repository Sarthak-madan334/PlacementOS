"""Tests for Opportunity and Readiness Assessment endpoints (Phase 04)."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

SAMPLE_PROFILE_PAYLOAD = {
    "full_name": "Aarush Sharma",
    "branch": "Computer Science",
    "graduation_year": 2026,
    "cgpa": 8.75,
    "cgpa_scale": 10.0,
    "target_role": "Backend Engineer",
    "skills": [
        {"display_name": "Python", "self_reported_level": "advanced"},
        {"display_name": "FastAPI", "self_reported_level": "advanced"},
        {"display_name": "PostgreSQL", "self_reported_level": "intermediate"},
    ],
    "projects": [
        {
            "title": "CampusProof Backend",
            "description": "Deterministic readiness scoring engine and REST API.",
            "url": "https://github.com/Sarthak-madan334/PlacementOS",
            "start_date": "2025-01-01",
            "end_date": "2025-05-01",
        }
    ],
}

SAMPLE_OPPORTUNITY_PAYLOAD = {
    "role_title": "Backend Software Engineer",
    "company": "Tech Corp",
    "jd_text": "Looking for a Python/FastAPI backend engineer with PostgreSQL experience.",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "Kubernetes"],
    "explicit_criteria": {
        "min_cgpa": 7.5,
        "allowed_branches": ["Computer Science", "Information Technology"],
        "allowed_years": [2026, 2027],
    },
}


def test_create_and_get_opportunity(client: TestClient, auth_headers_user1: dict):
    """Test saving and retrieving an opportunity."""
    create_res = client.post(
        "/api/v1/opportunities",
        headers=auth_headers_user1,
        json=SAMPLE_OPPORTUNITY_PAYLOAD,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    opp_data = create_res.json()
    opp_id = opp_data["id"]
    assert opp_data["role_title"] == "Backend Software Engineer"
    assert opp_data["company"] == "Tech Corp"
    assert len(opp_data["required_skills"]) == 3

    # Retrieve opportunity
    get_res = client.get(f"/api/v1/opportunities/{opp_id}", headers=auth_headers_user1)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == opp_id


def test_create_assessment_without_profile_returns_404(client: TestClient, auth_headers_user1: dict):
    """Assessment requires an existing student profile, returns 404 if missing."""
    res = client.post("/api/v1/assessments", headers=auth_headers_user1, json={})
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["code"] == "profile_not_found"


def test_create_assessment_full_flow(client: TestClient, auth_headers_user1: dict):
    """Full assessment execution against saved opportunity and resume text."""
    # 1. Create profile
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)

    # 2. Create opportunity
    opp_res = client.post("/api/v1/opportunities", headers=auth_headers_user1, json=SAMPLE_OPPORTUNITY_PAYLOAD)
    opp_id = opp_res.json()["id"]

    # 3. Create assessment
    sample_resume = """
    Aarush Sharma
    Email: aarush@example.com | Phone: 1234567890
    Education: B.Tech Computer Science, 2026
    Skills: Python, FastAPI, PostgreSQL, Git
    Experience: Backend Developer Intern
    - Engineered high performance API endpoints reducing latency by 35%
    - Implemented database migrations and queries
    """

    assess_payload = {
        "opportunity_id": opp_id,
        "resume_text": sample_resume,
    }
    assess_res = client.post("/api/v1/assessments", headers=auth_headers_user1, json=assess_payload)
    assert assess_res.status_code == status.HTTP_201_CREATED
    data = assess_res.json()

    assert data["scoring_version"] == "cp-v1"
    assert data["eligibility"]["status"] == "eligible"
    assert data["readiness"]["score"] is not None
    assert 0 <= data["readiness"]["score"] <= 100
    assert data["readiness"]["confidence"] in ("medium", "high")
    assert len(data["readiness"]["factors"]) == 5
    assert data["role_match"] is not None
    assert data["role_match"]["score"] == 100
    assert len(data["next_actions"]) <= 3

    # 4. Get assessment by ID
    assess_id = data["id"]
    get_res = client.get(f"/api/v1/assessments/{assess_id}", headers=auth_headers_user1)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == assess_id


def test_cross_user_opportunity_and_assessment_isolation(
    client: TestClient,
    auth_headers_user1: dict,
    auth_headers_user2: dict,
):
    """User 2 cannot access or view User 1's opportunity or assessment."""
    # User 1 creates profile, opportunity, and assessment
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)
    opp_res = client.post("/api/v1/opportunities", headers=auth_headers_user1, json=SAMPLE_OPPORTUNITY_PAYLOAD)
    opp_id = opp_res.json()["id"]

    assess_res = client.post("/api/v1/assessments", headers=auth_headers_user1, json={"opportunity_id": opp_id})
    assess_id = assess_res.json()["id"]

    # User 2 tries to GET User 1's opportunity -> 404
    opp_user2 = client.get(f"/api/v1/opportunities/{opp_id}", headers=auth_headers_user2)
    assert opp_user2.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to GET User 1's assessment -> 404
    assess_user2 = client.get(f"/api/v1/assessments/{assess_id}", headers=auth_headers_user2)
    assert assess_user2.status_code == status.HTTP_404_NOT_FOUND
