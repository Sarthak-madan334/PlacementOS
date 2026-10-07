from fastapi import APIRouter
from app.api.v1.endpoints import assessment, opportunity, profile, resume

api_v1_router = APIRouter()
api_v1_router.include_router(profile.router)
api_v1_router.include_router(resume.router)
api_v1_router.include_router(opportunity.router)
api_v1_router.include_router(assessment.router)
