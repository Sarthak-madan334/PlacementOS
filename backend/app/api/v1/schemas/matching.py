"""Pydantic schemas for Phase 05 Opportunity & Role Matching API."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RequirementExtractRequest(BaseModel):
    jd_text: str = Field(..., min_length=1, max_length=50000, description="Raw job description text")


class ExtractedRequirementRead(BaseModel):
    original_phrase: str
    normalized_skill: str
    category: str  # required, preferred, unspecified
    source_context: str = ""


class RequirementExtractResponse(BaseModel):
    requirements: List[ExtractedRequirementRead] = Field(default_factory=list)
    total_count: int


class EligibilityReasonSchema(BaseModel):
    code: str
    message: str


class EligibilityResultSchema(BaseModel):
    status: str  # eligible, not_eligible, unknown
    reasons: List[EligibilityReasonSchema] = Field(default_factory=list)


class RoleMatchSummarySchema(BaseModel):
    score: Optional[int] = None
    matched_required: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    unknown_required: List[str] = Field(default_factory=list)
    matched_preferred: List[str] = Field(default_factory=list)
    missing_preferred: List[str] = Field(default_factory=list)
    total_required: int
    total_preferred: int
    explanation: str
    reason_code: Optional[str] = None


class RequirementMatchItemSchema(BaseModel):
    original_phrase: str
    normalized_skill: str
    category: str
    status: str  # matched, missing, unknown
    evidence_source: Optional[str] = None
    matched_text: Optional[str] = None
    explanation: str


class MatchStrengthSchema(BaseModel):
    label: str
    evidence: str
    importance: str = "required"
    confidence: str = "medium"


class MatchGapSchema(BaseModel):
    label: str
    importance: str
    reason: str


class MatchResponse(BaseModel):
    matching_version: str = "rm-v1"
    eligibility: EligibilityResultSchema
    role_match: RoleMatchSummarySchema
    requirements: List[RequirementMatchItemSchema] = Field(default_factory=list)
    strengths: List[MatchStrengthSchema] = Field(default_factory=list)
    gaps: List[MatchGapSchema] = Field(default_factory=list)
    created_at: str


class StandaloneMatchRequest(BaseModel):
    """Payload for standalone match demonstration without requiring saved DB records."""
    profile: Dict[str, Any] = Field(
        ...,
        description="Candidate profile evidence including full_name, branch, graduation_year, cgpa, skills, projects, resume_skills",
    )
    opportunity: Dict[str, Any] = Field(
        ...,
        description="Opportunity requirements including role_title, company, required_skills, preferred_skills, jd_text, explicit_criteria",
    )
