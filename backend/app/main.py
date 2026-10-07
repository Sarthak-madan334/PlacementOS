"""PlacementOS FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.db.base import Base
from app.adapters.db.session import engine
from app.api.v1.endpoints import health
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables only for local/testing mode if needed
    if settings.APP_ENV in ("local", "test"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PlacementOS API",
    description="PlacementOS Backend & Intelligence Layer (Aarush) — Profile, Evidence, Resume Parsing, Readiness Engine, and Role Matching.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Exception handlers with standard {"detail": "...", "code": "..."} format
register_exception_handlers(app)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & Health routes
app.include_router(health.router)

# Versioned API routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root index")
def read_root():
    return {
        "service": "PlacementOS API",
        "version": "1.0.0",
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs",
    }
