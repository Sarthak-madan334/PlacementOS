from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ProjectEvidence(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    url: str | None = Field(default=None, max_length=1024)


class ProfileSnapshot(BaseModel):
    branch: str | None = Field(default=None, max_length=255)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    cgpa: float | None = Field(default=None, ge=0, le=100)
    cgpa_scale: float | None = Field(default=None, gt=0, le=100)
    target_role: str | None = Field(default=None, max_length=255)
    skills: list[str] = Field(default_factory=list, max_length=50)
    projects: list[ProjectEvidence] = Field(default_factory=list, max_length=20)
    resume_sections: list[str] | None = Field(default=None, max_length=20)
    github_profile_url: str | None = Field(default=None, max_length=500)
    linkedin_profile_url: str | None = Field(default=None, max_length=500)

    @field_validator("skills", "resume_sections")
    @classmethod
    def clean_terms(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @field_validator("github_profile_url")
    @classmethod
    def validate_github_url(cls, value: str | None) -> str | None:
        return _profile_url(value, "github.com", r"/[A-Za-z0-9-]{1,39}/?")

    @field_validator("linkedin_profile_url")
    @classmethod
    def validate_linkedin_url(cls, value: str | None) -> str | None:
        return _profile_url(value, "linkedin.com", r"/in/[A-Za-z0-9_%.-]+/?")

    @model_validator(mode="after")
    def validate_cgpa_scale(self) -> "ProfileSnapshot":
        if self.cgpa is not None and self.cgpa_scale is not None and self.cgpa > self.cgpa_scale:
            raise ValueError("CGPA cannot exceed the declared grading scale")
        return self


class OpportunitySnapshot(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=20000)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    preferred_skills: list[str] = Field(default_factory=list, max_length=50)
    minimum_cgpa: float | None = Field(default=None, ge=0, le=100)
    cgpa_scale: float | None = Field(default=None, gt=0, le=100)
    eligible_branches: list[str] = Field(default_factory=list, max_length=50)
    graduation_years: list[int] = Field(default_factory=list, max_length=20)

    @field_validator("required_skills", "preferred_skills", "eligible_branches")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @model_validator(mode="after")
    def validate_cgpa_criteria(self) -> "OpportunitySnapshot":
        if self.minimum_cgpa is not None and self.cgpa_scale is None:
            raise ValueError("CGPA scale is required when a minimum CGPA is provided")
        if self.minimum_cgpa is not None and self.cgpa_scale is not None and self.minimum_cgpa > self.cgpa_scale:
            raise ValueError("Minimum CGPA cannot exceed its grading scale")
        return self


class AssessmentPreviewRequest(BaseModel):
    profile: ProfileSnapshot
    opportunity: OpportunitySnapshot = Field(default_factory=OpportunitySnapshot)


class FactorResult(BaseModel):
    key: str
    label: str
    score: int | None
    weight: float
    available: bool
    evidence: list[str] = Field(default_factory=list)
    explanation: str


class AssessmentPreviewResponse(BaseModel):
    id: UUID
    eligibility: dict
    readiness: dict
    role_match: dict
    profile_links: dict
    strengths: list[dict]
    gaps: list[dict]
    next_actions: list[dict]
    created_at: datetime


def _profile_url(value: str | None, host: str, path_pattern: str) -> str | None:
    if value is None or not value.strip():
        return None
    import re

    candidate = value.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parts = urlsplit(candidate)
    try:
        valid_port = parts.port in (None, 443)
    except ValueError:
        valid_port = False
    allowed_hosts = {host, f"www.{host}"}
    if parts.scheme != "https" or parts.hostname not in allowed_hosts or not valid_port or not re.fullmatch(path_pattern, parts.path):
        raise ValueError(f"Enter a valid https://{host} profile URL")
    return urlunsplit(("https", host, parts.path.rstrip("/"), "", ""))


