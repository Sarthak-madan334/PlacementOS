"""Pydantic schemas for opportunities, job descriptions, and criteria."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpportunityCreate(BaseModel):
    role_title: str = Field(..., min_length=1, max_length=255, description="Job title / role name")
    company: Optional[str] = Field(None, max_length=255, description="Company or organization name")
    jd_text: Optional[str] = Field(None, max_length=20000, description="Raw job description text")
    required_skills: List[str] = Field(default_factory=list, description="Explicitly required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred or bonus skills")
    explicit_criteria: Dict[str, Any] = Field(default_factory=dict, description="Hard criteria: min_cgpa, allowed_branches, allowed_years")

    @field_validator("role_title")
    @classmethod
    def validate_role_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Role title cannot be blank")
        return cleaned


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role_title: str
    company: Optional[str] = None
    jd_text: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    explicit_criteria: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
