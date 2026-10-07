"""Health endpoints for liveness and dependency readiness."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health/live", summary="Process liveness check")
def health_live():
    """Liveness probe: verifies the web process is running. Does not depend on the database."""
    return {"status": "alive"}


@router.get("/health/ready", summary="Dependency readiness check")
def health_ready(db: Session = Depends(get_db)):
    """Readiness probe: verifies database connectivity with a prompt check."""
    try:
        # Execute quick heartbeat query
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "detail": "Database connectivity check failed",
                "code": "service_unavailable",
            },
        )
