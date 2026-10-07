"""Pydantic schemas for student profile, skills, projects, and validation rules."""

import re
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


URL_REGEX = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


class SkillBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255, description="Display name of the skill")
    self_reported_level: Optional[str] = Field(None, max_length=50, description="Self-reported proficiency level")
    source: Optional[str] = Field("self_reported", max_length=50, description="Evidence source")

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Skill display name cannot be blank")
        return cleaned


class SkillCreate(SkillBase):
    normalized_name: Optional[str] = Field(None, max_length=255, description="Normalized skill name (lowercased)")

    @model_validator(mode="after")
    def populate_normalized_name(self) -> "SkillCreate":
        if not self.normalized_name:
            self.normalized_name = re.sub(r"\s+", " ", self.display_name.lower().strip())
        else:
            self.normalized_name = re.sub(r"\s+", " ", self.normalized_name.lower().strip())
        return self


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    normalized_name: str
    display_name: str
    self_reported_level: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Project title")
    description: str = Field(..., min_length=1, max_length=5000, description="Detailed project description")
    url: Optional[str] = Field(None, max_length=1024, description="Project or repository URL")
    start_date: Optional[str] = Field(None, max_length=50, description="Start date (YYYY-MM or string)")
    end_date: Optional[str] = Field(None, max_length=50, description="End date (YYYY-MM or string)")

    @field_validator("title", "description")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not URL_REGEX.match(cleaned):
            raise ValueError(f"Invalid URL format: '{cleaned}'. Must start with http:// or https://")
        return cleaned


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileCreateOrUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255, description="Student's full name")
    branch: str = Field(..., min_length=1, max_length=255, description="Branch of study (e.g. Computer Science)")
    graduation_year: int = Field(..., ge=1900, le=2100, description="Expected graduation year (1900-2100)")
    cgpa: Optional[float] = Field(None, ge=0.0, le=100.0, description="Cumulative Grade Point Average")
    cgpa_scale: Optional[float] = Field(None, ge=1.0, le=100.0, description="CGPA grading scale (e.g. 10.0 or 4.0)")
    target_role: Optional[str] = Field(None, max_length=255, description="Target job role")
    skills: List[SkillCreate] = Field(default_factory=list, description="List of student skills")
    projects: List[ProjectCreate] = Field(default_factory=list, description="List of student projects")

    @field_validator("full_name", "branch")
    @classmethod
    def validate_required_strings(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned

    @field_validator("target_role")
    @classmethod
    def validate_optional_string(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None

    @model_validator(mode="after")
    def validate_cgpa_bounds_and_scale(self) -> "ProfileCreateOrUpdate":
        if self.cgpa is not None:
            # If scale is given, CGPA must not exceed scale
            if self.cgpa_scale is not None:
                if self.cgpa > self.cgpa_scale:
                    raise ValueError(f"CGPA ({self.cgpa}) cannot exceed CGPA scale ({self.cgpa_scale})")
            else:
                # Default scale assumption check
                if self.cgpa > 10.0 and self.cgpa <= 100.0:
                    # Likely percentage or 100-point scale
                    pass
                elif self.cgpa > 10.0:
                    raise ValueError(f"CGPA ({self.cgpa}) exceeds maximum standard scale without explicit scale definition")

        # Deduplicate skills by normalized_name to guarantee idempotency
        seen_skills = set()
        deduped_skills: List[SkillCreate] = []
        for s in self.skills:
            norm = s.normalized_name or s.display_name.lower().strip()
            if norm not in seen_skills:
                seen_skills.add(norm)
                deduped_skills.append(s)
        self.skills = deduped_skills

        return self


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    branch: str
    graduation_year: int
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = None
    target_role: Optional[str] = None
    skills: List[SkillRead] = Field(default_factory=list)
    projects: List[ProjectRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
