from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="CampusProof API",
    description="Backend API for CampusProof readiness scoring",
    version="1.0.0",
)

# Configure CORS for strict allowed domains (Phase 07 Security Requirement)
# In production, this should be the specific Vercel frontend domains.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/health/live")
def health_live():
    """Process liveness check"""
    return {"status": "ok"}

@app.get("/health/ready")
def health_ready():
    """Dependency readiness check (database connectivity to be added)"""
    return {"status": "ok"}
