"""Pydantic schemas for readiness evaluation and assessment results."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FactorDetail(BaseModel):
    key: str
    name: str
    score: int
    weight: float
    available: bool
    evidence: List[str] = Field(default_factory=list)
    explanation: str


class ReadinessScoreDetail(BaseModel):
    score: Optional[int] = None
    confidence: str = Field(..., description="Evidence confidence: low, medium, or high")
    scoring_version: str = Field("cp-v1", description="Scoring rule version")
    factors: List[FactorDetail] = Field(default_factory=list)
    excluded_factors: List[str] = Field(default_factory=list)


class EligibilityReasonSchema(BaseModel):
    code: str
    message: str


class EligibilityDetail(BaseModel):
    status: str = Field(..., description="Eligibility status: eligible, not_eligible, or unknown")
    reasons: List[EligibilityReasonSchema] = Field(default_factory=list)


class RoleMatchDetail(BaseModel):
    score: Optional[int] = None
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    unknown: List[str] = Field(default_factory=list)


class StrengthDetail(BaseModel):
    label: str
    evidence: str
    confidence: str = "medium"


class GapDetail(BaseModel):
    label: str
    importance: str = "required"
    reason: str


class NextActionDetail(BaseModel):
    title: str
    rationale: str
    completion_evidence: str


class AssessmentCreate(BaseModel):
    opportunity_id: Optional[uuid.UUID] = Field(None, description="Optional ID of saved opportunity")
    target_role: Optional[str] = Field(None, description="Inline target role title")
    jd_text: Optional[str] = Field(None, description="Inline job description text")
    required_skills: Optional[List[str]] = Field(default=None, description="Inline required skills list")
    explicit_criteria: Optional[Dict[str, Any]] = Field(default=None, description="Inline eligibility criteria")
    resume_text: Optional[str] = Field(None, description="Optional raw text of resume for ad-hoc assessment")


class AssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    eligibility: EligibilityDetail
    readiness: ReadinessScoreDetail
    role_match: Optional[RoleMatchDetail] = None
    strengths: List[StrengthDetail] = Field(default_factory=list)
    gaps: List[GapDetail] = Field(default_factory=list)
    next_actions: List[NextActionDetail] = Field(default_factory=list)
    scoring_version: str
    created_at: datetime
