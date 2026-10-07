"""Compatibility bridge exporting SQLAlchemy models from adapters.db.models."""

from app.adapters.db.base import Base
from app.adapters.db.models import GUID, ProfileFile, Project, Skill, StudentProfile, User

__all__ = [
    "Base",
    "GUID",
    "User",
    "StudentProfile",
    "Skill",
    "Project",
    "ProfileFile",
]
