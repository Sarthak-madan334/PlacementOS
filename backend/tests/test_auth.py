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


def test_auth_fails_closed_when_mock_auth_disabled(client: TestClient):
    """When ALLOW_MOCK_AUTH is False and no JWT secret is configured, mock tokens are rejected."""
    from app.core.config import settings
    orig_mock = settings.ALLOW_MOCK_AUTH
    orig_secret = settings.SUPABASE_JWT_SECRET
    try:
        settings.ALLOW_MOCK_AUTH = False
        settings.SUPABASE_JWT_SECRET = None
        settings.AUTH_ISSUER_URL = None

        response = client.get("/api/v1/me/profile", headers={"Authorization": "Bearer mock-token-123"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["code"] == "auth_not_configured"
    finally:
        settings.ALLOW_MOCK_AUTH = orig_mock
        settings.SUPABASE_JWT_SECRET = orig_secret


def test_auth_fails_closed_in_production_env(client: TestClient):
    """In production env, mock tokens are rejected even if ALLOW_MOCK_AUTH is set."""
    from app.core.config import settings
    orig_env = settings.APP_ENV
    orig_secret = settings.SUPABASE_JWT_SECRET
    try:
        settings.APP_ENV = "production"
        settings.SUPABASE_JWT_SECRET = None
        settings.AUTH_ISSUER_URL = None

        response = client.get("/api/v1/me/profile", headers={"Authorization": "Bearer mock-token-123"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        settings.APP_ENV = orig_env
        settings.SUPABASE_JWT_SECRET = orig_secret


def test_jwt_valid_signature_verification(client: TestClient):
    """Valid JWT signed with SUPABASE_JWT_SECRET is accepted."""
    import jwt
    import time
    from app.core.config import settings

    orig_secret = settings.SUPABASE_JWT_SECRET
    orig_mock = settings.ALLOW_MOCK_AUTH
    try:
        test_secret = "test-secret-key-1234567890123456"
        settings.SUPABASE_JWT_SECRET = test_secret
        settings.ALLOW_MOCK_AUTH = False

        payload = {
            "sub": "jwt-user-uuid-1",
            "email": "jwt@example.com",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, test_secret, algorithm="HS256")

        response = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {token}"})
        # Resolves user and finds no profile -> 404 profile_not_found (proves auth succeeded)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["code"] == "profile_not_found"
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret
        settings.ALLOW_MOCK_AUTH = orig_mock


def test_supabase_asymmetric_jwt_uses_issuer_jwks(client: TestClient, monkeypatch):
    import time
    import jwt
    from types import SimpleNamespace
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from app.core import security
    from app.core.config import settings

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public_pem = private_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    jwks_client = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=public_pem))
    requested_urls = []
    monkeypatch.setattr(security, "get_jwks_client", lambda url: (requested_urls.append(url), jwks_client)[1])
    original = (settings.APP_ENV, settings.AUTH_ISSUER_URL, settings.AUTH_AUDIENCE, settings.SUPABASE_JWT_SECRET, settings.ALLOW_MOCK_AUTH)
    issuer = "https://example.supabase.co/auth/v1"
    try:
        settings.APP_ENV = "production"
        settings.AUTH_ISSUER_URL = issuer
        settings.AUTH_AUDIENCE = "authenticated"
        settings.SUPABASE_JWT_SECRET = None
        settings.ALLOW_MOCK_AUTH = False
        token = jwt.encode({"sub": "asymmetric-user", "iss": issuer, "aud": "authenticated", "exp": int(time.time()) + 600}, private_pem, algorithm="ES256", headers={"kid": "test-key"})
        response = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404
        assert response.json()["code"] == "profile_not_found"
        assert requested_urls == [f"{issuer}/.well-known/jwks.json"]
    finally:
        settings.APP_ENV, settings.AUTH_ISSUER_URL, settings.AUTH_AUDIENCE, settings.SUPABASE_JWT_SECRET, settings.ALLOW_MOCK_AUTH = original


def test_jwt_expired_token_rejected(client: TestClient):
    """Expired JWT is rejected with 401."""
    import jwt
    import time
    from app.core.config import settings

    orig_secret = settings.SUPABASE_JWT_SECRET
    orig_mock = settings.ALLOW_MOCK_AUTH
    try:
        test_secret = "test-secret-key-1234567890123456"
        settings.SUPABASE_JWT_SECRET = test_secret
        settings.ALLOW_MOCK_AUTH = False

        payload = {
            "sub": "jwt-user-uuid-1",
            "email": "jwt@example.com",
            "exp": int(time.time()) - 3600,  # Expired
        }
        token = jwt.encode(payload, test_secret, algorithm="HS256")

        response = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["code"] == "unauthorized"
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret
        settings.ALLOW_MOCK_AUTH = orig_mock


def test_jwt_invalid_secret_rejected(client: TestClient):
    """JWT signed with wrong secret is rejected with 401."""
    import jwt
    import time
    from app.core.config import settings

    orig_secret = settings.SUPABASE_JWT_SECRET
    orig_mock = settings.ALLOW_MOCK_AUTH
    try:
        settings.SUPABASE_JWT_SECRET = "correct-secret-123"
        settings.ALLOW_MOCK_AUTH = False

        payload = {
            "sub": "jwt-user-uuid-1",
            "email": "jwt@example.com",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, "wrong-secret-456", algorithm="HS256")

        response = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["code"] == "unauthorized"
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret
        settings.ALLOW_MOCK_AUTH = orig_mock
