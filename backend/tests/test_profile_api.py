"""Tests for student profile and evidence API (Phase 02)."""

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
        {
            "display_name": "Python",
            "self_reported_level": "advanced",
            "source": "self_reported",
        },
        {
            "display_name": "FastAPI",
            "self_reported_level": "advanced",
            "source": "self_reported",
        },
    ],
    "projects": [
        {
            "title": "CampusProof",
            "description": "Placement readiness engine and deterministic scoring module.",
            "url": "https://github.com/Sarthak-madan334/PlacementOS",
            "start_date": "2025-01-01",
            "end_date": "2025-05-01",
        }
    ],
}


def test_get_profile_not_found(client: TestClient, auth_headers_user1: dict):
    """GET /api/v1/me/profile returns 404 when profile has not been created."""
    response = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "profile_not_found"


def test_create_profile_success(client: TestClient, auth_headers_user1: dict):
    """PUT /api/v1/me/profile creates a new profile with skills and projects."""
    response = client.put(
        "/api/v1/me/profile",
        headers=auth_headers_user1,
        json=SAMPLE_PROFILE_PAYLOAD,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Aarush Sharma"
    assert data["branch"] == "Computer Science"
    assert data["graduation_year"] == 2026
    assert data["cgpa"] == 8.75
    assert data["cgpa_scale"] == 10.0
    assert data["target_role"] == "Backend Engineer"
    assert len(data["skills"]) == 2
    assert len(data["projects"]) == 1
    assert data["projects"][0]["title"] == "CampusProof"
    assert data["projects"][0]["url"] == "https://github.com/Sarthak-madan334/PlacementOS"


def test_get_profile_after_creation(client: TestClient, auth_headers_user1: dict):
    """GET /api/v1/me/profile returns persisted profile data."""
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)

    response = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Aarush Sharma"
    assert len(data["skills"]) == 2
    assert len(data["projects"]) == 1


def test_profile_upsert_idempotency_and_no_duplicate_skills(client: TestClient, auth_headers_user1: dict):
    """Repeated PUT requests with same skills do not duplicate skill rows."""
    # First PUT
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)

    # Second PUT with repeated skill entries in payload
    repeated_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    repeated_payload["skills"] = [
        {"display_name": "Python"},
        {"display_name": "python"},  # Duplicate case
        {"display_name": "FastAPI"},
        {"display_name": "Docker"},
    ]

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=repeated_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Skills should be deduplicated: Python, FastAPI, Docker (3 skills, not 4)
    assert len(data["skills"]) == 3
    skill_names = [s["normalized_name"] for s in data["skills"]]
    assert sorted(skill_names) == ["docker", "fastapi", "python"]


def test_cross_user_isolation(client: TestClient, auth_headers_user1: dict, auth_headers_user2: dict):
    """User 2 cannot access or see User 1's profile."""
    # User 1 creates profile
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)

    # User 2 tries to GET their profile - should be 404 (not User 1's data)
    response_user2 = client.get("/api/v1/me/profile", headers=auth_headers_user2)
    assert response_user2.status_code == status.HTTP_404_NOT_FOUND

    # User 2 creates their own profile
    user2_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    user2_payload["full_name"] = "Priya Patel"
    user2_payload["target_role"] = "Full Stack Engineer"

    client.put("/api/v1/me/profile", headers=auth_headers_user2, json=user2_payload)

    # Verify User 1 data remains untouched
    resp1 = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert resp1.json()["full_name"] == "Aarush Sharma"

    # Verify User 2 data is separate
    resp2 = client.get("/api/v1/me/profile", headers=auth_headers_user2)
    assert resp2.json()["full_name"] == "Priya Patel"


def test_validation_cgpa_exceeds_scale(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if CGPA exceeds CGPA scale."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["cgpa"] = 10.5
    invalid_payload["cgpa_scale"] = 10.0

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["code"] == "validation_error"


def test_validation_graduation_year_out_of_bounds(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if graduation year is out of range."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["graduation_year"] = 1850

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


def test_validation_invalid_project_url(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if project URL is not a valid http/https URL."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["projects"] = [
        {
            "title": "Invalid URL Project",
            "description": "Test",
            "url": "ftp://not-allowed.com",
        }
    ]

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


def test_validation_negative_cgpa(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if CGPA is negative."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["cgpa"] = -1.5

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


def test_validation_future_unrealistic_graduation_year(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if graduation year is unrealistic (> 2100)."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["graduation_year"] = 2150

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


def test_validation_empty_required_strings(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if full_name or branch are blank/whitespace."""
    for field in ["full_name", "branch"]:
        invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
        invalid_payload[field] = "   "
        response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["code"] == "validation_error"


def test_validation_blank_skill_or_project_fields(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if skill display_name or project title/description are blank."""
    # Blank skill
    invalid_skill_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_skill_payload["skills"] = [{"display_name": "   "}]
    res1 = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_skill_payload)
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Blank project title
    invalid_proj_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_proj_payload["projects"] = [{"title": "   ", "description": "Valid description"}]
    res2 = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_proj_payload)
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_validation_excessive_string_length(client: TestClient, auth_headers_user1: dict):
    """Validation fails with 422 if string exceeds max length."""
    invalid_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    invalid_payload["full_name"] = "A" * 256

    response = client.put("/api/v1/me/profile", headers=auth_headers_user1, json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"


def test_cross_user_delete_isolation(client: TestClient, auth_headers_user1: dict, auth_headers_user2: dict):
    """User 2 deleting their profile does not affect User 1's profile."""
    # Both create profiles
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)
    user2_payload = dict(SAMPLE_PROFILE_PAYLOAD)
    user2_payload["full_name"] = "Priya Patel"
    client.put("/api/v1/me/profile", headers=auth_headers_user2, json=user2_payload)

    # User 2 deletes their profile
    res_del = client.delete("/api/v1/me/profile", headers=auth_headers_user2)
    assert res_del.status_code == status.HTTP_200_OK

    # User 1 profile is still intact
    res_get1 = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert res_get1.status_code == status.HTTP_200_OK
    assert res_get1.json()["full_name"] == "Aarush Sharma"

    # User 2 profile is gone
    res_get2 = client.get("/api/v1/me/profile", headers=auth_headers_user2)
    assert res_get2.status_code == status.HTTP_404_NOT_FOUND


def test_delete_profile(client: TestClient, auth_headers_user1: dict):
    """DELETE /api/v1/me/profile removes profile and child records."""
    # Create profile
    client.put("/api/v1/me/profile", headers=auth_headers_user1, json=SAMPLE_PROFILE_PAYLOAD)

    # Delete profile
    del_resp = client.delete("/api/v1/me/profile", headers=auth_headers_user1)
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json()["status"] == "deleted"

    # Subsequent GET returns 404
    get_resp = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    # Subsequent DELETE returns 404
    del_again = client.delete("/api/v1/me/profile", headers=auth_headers_user1)
    assert del_again.status_code == status.HTTP_404_NOT_FOUND

