"""Integration tests for Phase 05 Opportunity & Matching API endpoints.

Tests /api/v1/opportunities/extract-requirements, /api/v1/opportunities/match (standalone),
/api/v1/opportunities/{id}/match (authenticated profile vs saved opportunity),
and security/ownership boundaries.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTH_HEADER_USER_A = {"Authorization": "Bearer student_user_a_sub"}
AUTH_HEADER_USER_B = {"Authorization": "Bearer student_user_b_sub"}


def test_extract_requirements_endpoint():
    """Verify POST /api/v1/opportunities/extract-requirements parses and classifies requirements."""
    payload = {
        "jd_text": """
        Software Engineer
        
        Requirements:
        - Strong proficiency in Python
        - Experience with PostgreSQL
        
        Nice to have:
        - Docker and Kubernetes
        """
    }

    response = client.post(
        "/api/v1/opportunities/extract-requirements",
        json=payload,
        headers=AUTH_HEADER_USER_A,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 4
    by_skill = {r["normalized_skill"]: r for r in data["requirements"]}
    assert by_skill["python"]["category"] == "required"
    assert by_skill["postgresql"]["category"] == "required"
    assert by_skill["docker"]["category"] == "preferred"
    assert by_skill["kubernetes"]["category"] == "preferred"


def test_standalone_match_endpoint():
    """Verify POST /api/v1/opportunities/match runs standalone evaluation without DB records."""
    payload = {
        "profile": {
            "full_name": "Aarush Sharma",
            "branch": "Computer Science and Engineering",
            "graduation_year": 2026,
            "cgpa": 8.5,
            "skills": ["Python", "SQL", "Git", "Docker"],
            "projects": [
                {
                    "title": "API Backend",
                    "description": "Engineered REST APIs in Python using PostgreSQL and Git.",
                    "url": "https://github.com/example/api",
                }
            ],
            "resume_skills": ["Python", "SQL", "Git"],
        },
        "opportunity": {
            "role_title": "Software Engineer",
            "company": "TechCorp",
            "required_skills": ["Python", "SQL", "Git"],
            "preferred_skills": ["Docker", "AWS"],
            "explicit_criteria": {
                "min_cgpa": 7.5,
                "allowed_branches": ["Computer Science", "Computer Science and Engineering"],
            },
        },
    }

    response = client.post(
        "/api/v1/opportunities/match",
        json=payload,
        headers=AUTH_HEADER_USER_A,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matching_version"] == "rm-v1"
    assert data["eligibility"]["status"] == "eligible"
    assert data["role_match"]["score"] == 100
    assert sorted(data["role_match"]["matched_required"]) == ["Git", "Python", "SQL"]
    assert data["role_match"]["matched_preferred"] == ["Docker"]
    assert data["role_match"]["missing_preferred"] == ["AWS"]


def test_authenticated_student_opportunity_match_flow():
    """Verify matching current student profile against saved opportunity with ownership checks."""
    # 1. Create Profile for User A
    profile_payload = {
        "full_name": "Aarush Sharma",
        "branch": "Computer Science",
        "graduation_year": 2026,
        "cgpa": 8.2,
        "target_role": "Backend Engineer",
        "skills": [{"display_name": "Python"}, {"display_name": "SQL"}, {"display_name": "FastAPI"}],
        "projects": [
            {
                "title": "Backend Microservice",
                "description": "Developed microservice with Python and FastAPI.",
                "url": "https://github.com/example/microservice",
            }
        ],
    }
    prof_resp = client.put("/api/v1/me/profile", json=profile_payload, headers=AUTH_HEADER_USER_A)
    assert prof_resp.status_code in (200, 201)

    # 2. Create Opportunity for User A
    opp_payload = {
        "role_title": "Backend Engineer",
        "company": "CloudNet",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker"],
        "explicit_criteria": {"min_cgpa": 7.0},
    }
    opp_resp = client.post("/api/v1/opportunities", json=opp_payload, headers=AUTH_HEADER_USER_A)
    assert opp_resp.status_code == 201
    opp_id = opp_resp.json()["id"]

    # 3. Match against saved opportunity
    match_resp = client.post(f"/api/v1/opportunities/{opp_id}/match", headers=AUTH_HEADER_USER_A)
    assert match_resp.status_code == 200
    match_data = match_resp.json()
    assert match_data["eligibility"]["status"] == "eligible"
    assert match_data["role_match"]["score"] == 100
    assert sorted(match_data["role_match"]["matched_required"]) == ["FastAPI", "Python"]

    # 4. User B cannot match against User A's private opportunity (404 owner isolation)
    user_b_resp = client.post(f"/api/v1/opportunities/{opp_id}/match", headers=AUTH_HEADER_USER_B)
    assert user_b_resp.status_code == 404
    assert user_b_resp.json()["detail"] == "Opportunity not found"


def test_match_unauthenticated_rejected():
    """Verify that match endpoints reject unauthenticated calls with 401."""
    resp = client.post("/api/v1/opportunities/extract-requirements", json={"jd_text": "Python"})
    assert resp.status_code == 401

    resp2 = client.post("/api/v1/opportunities/match", json={"profile": {}, "opportunity": {}})
    assert resp2.status_code == 401
