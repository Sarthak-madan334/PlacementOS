"""Tests for health liveness and readiness endpoints."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.adapters.db.session import get_db


def test_health_live(client: TestClient):
    """Test process liveness endpoint."""
    response = client.get("/health/live")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "alive"}


def test_health_ready_success(client: TestClient):
    """Test dependency readiness endpoint when DB is available."""
    response = client.get("/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_health_ready_database_failure():
    """Test readiness returns 503 when database connectivity fails."""
    def broken_db():
        class BrokenSession:
            def execute(self, stmt):
                raise RuntimeError("Database connection timed out")
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/health/ready")
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["code"] == "service_unavailable"
    finally:
        app.dependency_overrides.clear()
