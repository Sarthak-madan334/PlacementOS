"""Authentication, JWT verification, and user identity resolution."""

from typing import Optional
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.db.models import User
from app.adapters.db.session import get_db
from app.core.config import settings
from app.core.exceptions import UnauthorizedException


def extract_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract token string from Authorization: Bearer <token> header."""
    if not authorization:
        raise UnauthorizedException("Authentication token required", code="unauthorized")

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedException("Invalid authorization header format. Expected 'Bearer <token>'", code="unauthorized")

    return parts[1]


def verify_jwt_token(token: str) -> dict:
    """Validate JWT token signature, issuer, audience, and expiration.
    Returns token payload if valid, otherwise raises UnauthorizedException.
    """
    # Local/Testing mock token fallback ONLY when explicitly enabled via ALLOW_MOCK_AUTH in local/test env
    if settings.ALLOW_MOCK_AUTH and settings.APP_ENV in ("local", "test"):
        return {
            "sub": token,
            "email": f"{token}@example.com" if "@" not in token else token,
        }

    # If mock auth is not enabled, require valid JWT configuration and decode
    if not settings.SUPABASE_JWT_SECRET and not settings.AUTH_ISSUER_URL:
        raise UnauthorizedException("Authentication service is not configured", code="auth_not_configured")

    # Standard JWT validation with Supabase or configured issuer
    try:
        decode_kwargs = {
            "algorithms": ["HS256", "RS256"],
            "options": {"verify_exp": True, "verify_sub": True},
        }
        if settings.AUTH_AUDIENCE:
            decode_kwargs["audience"] = settings.AUTH_AUDIENCE
        if settings.AUTH_ISSUER_URL:
            decode_kwargs["issuer"] = settings.AUTH_ISSUER_URL

        secret = settings.SUPABASE_JWT_SECRET or ""
        payload = jwt.decode(token, secret, **decode_kwargs)
        if not payload.get("sub"):
            raise UnauthorizedException("Token missing subject (sub) claim", code="unauthorized")
        return payload
    except PyJWTError as e:
        raise UnauthorizedException(f"Invalid authentication token: {str(e)}", code="unauthorized")


def get_current_user(
    token: str = Depends(extract_bearer_token),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return internal authenticated User record from verified JWT subject."""
    payload = verify_jwt_token(token)
    auth_subject = str(payload["sub"])
    email = payload.get("email")

    # Find or create User record
    stmt = select(User).where(User.auth_subject == auth_subject)
    user = db.scalar(stmt)

    if not user:
        user = User(auth_subject=auth_subject, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
