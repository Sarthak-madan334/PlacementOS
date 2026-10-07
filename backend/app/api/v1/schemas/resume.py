"""Pydantic schemas for resume parser output and candidate facts."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContactFacts(BaseModel):
    name: Optional[str] = Field(None, description="Extracted candidate name")
    email: Optional[str] = Field(None, description="Extracted email address")
    phone: Optional[str] = Field(None, description="Extracted phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile handle or URL")
    github: Optional[str] = Field(None, description="GitHub profile handle or URL")
    website: Optional[str] = Field(None, description="Personal website or portfolio URL")


class EducationFact(BaseModel):
    institution: Optional[str] = Field(None, description="College or university name")
    degree: Optional[str] = Field(None, description="Degree name (e.g. B.Tech, B.S.)")
    branch: Optional[str] = Field(None, description="Field of study or major")
    graduation_year: Optional[int] = Field(None, description="Graduation year if explicitly mentioned")
    cgpa: Optional[float] = Field(None, description="CGPA or GPA score if explicitly present")
    cgpa_scale: Optional[float] = Field(None, description="Grading scale if explicitly present")
    source_snippet: Optional[str] = Field(None, description="Source snippet from resume")


class SkillFact(BaseModel):
    display_name: str = Field(..., description="Skill name as displayed")
    normalized_name: str = Field(..., description="Normalized lowercase skill name")
    source_snippet: Optional[str] = Field(None, description="Contextual snippet where skill appeared")
    section: Optional[str] = Field("Skills", description="Section where skill was detected")
    page: Optional[int] = Field(1, description="Page number where skill appeared")


class ProjectFact(BaseModel):
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description or bullet points")
    url: Optional[str] = Field(None, description="Repository or live URL if found")
    source_snippet: Optional[str] = Field(None, description="Source snippet from resume")


class ExperienceFact(BaseModel):
    organization: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job or internship role title")
    dates: Optional[str] = Field(None, description="Employment dates if detected")
    description: str = Field(..., description="Responsibilities and achievements")
    source_snippet: Optional[str] = Field(None, description="Source snippet from resume")


class CandidateFacts(BaseModel):
    contact: ContactFacts = Field(default_factory=ContactFacts)
    education: List[EducationFact] = Field(default_factory=list)
    skills: List[SkillFact] = Field(default_factory=list)
    projects: List[ProjectFact] = Field(default_factory=list)
    experience: List[ExperienceFact] = Field(default_factory=list)


class QualitySignal(BaseModel):
    signal: str = Field(..., description="Signal identifier (e.g. action_verb, quantified_outcome, missing_section)")
    category: str = Field(..., description="Category: language, impact, completeness")
    observed_text: str = Field(..., description="Observed text or evidence snippet")
    rule_or_reason: str = Field(..., description="Deterministic heuristic or reason")


class ResumeParseResponse(BaseModel):
    """Normalized response contract for resume parsing review."""
    model_config = ConfigDict(from_attributes=True)

    candidate_facts: CandidateFacts = Field(default_factory=CandidateFacts)
    sections_detected: List[str] = Field(default_factory=list)
    quality_signals: List[QualitySignal] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
