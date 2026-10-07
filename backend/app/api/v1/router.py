"""API v1 router composition."""

from fastapi import APIRouter
from app.api.v1.endpoints import profile

api_v1_router = APIRouter()
api_v1_router.include_router(profile.router)
