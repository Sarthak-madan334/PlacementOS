"""Tests for authentication, JWT security, and user context."""

from fastapi import status
from fastapi.testclient import TestClient


def test_missing_auth_header(client: TestClient):
    """Requests to /api/v1/me/profile without auth header must return 401."""
    response = client.get("/api/v1/me/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "unauthorized"


def test_missing_auth_header_put(client: TestClient):
    """PUT /api/v1/me/profile without auth header must return 401."""
    response = client.put("/api/v1/me/profile", json={"full_name": "Test", "branch": "CS", "graduation_year": 2026})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["code"] == "unauthorized"


def test_missing_auth_header_delete(client: TestClient):
    """DELETE /api/v1/me/profile without auth header must return 401."""
    response = client.delete("/api/v1/me/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["code"] == "unauthorized"


def test_malformed_auth_header(client: TestClient):
    """Requests with malformed auth headers must return 401."""
    response = client.get(
        "/api/v1/me/profile",
        headers={"Authorization": "InvalidFormatToken"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "unauthorized"


def test_authenticated_user_resolution(client: TestClient, auth_headers_user1: dict):
    """Authenticated requests create or resolve user context without error."""
    # When no profile exists yet, it should return 404 (not 401 or 500)
    response = client.get("/api/v1/me/profile", headers=auth_headers_user1)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "profile_not_found"
