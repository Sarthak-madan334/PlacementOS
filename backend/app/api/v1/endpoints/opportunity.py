"""Opportunity, job requirements, and role matching endpoints for authenticated students."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.adapters.db.models import Opportunity, StudentProfile, User
from app.adapters.db.session import get_db
from app.api.v1.schemas.matching import (
    ExtractedRequirementRead,
    MatchResponse,
    RequirementExtractRequest,
    RequirementExtractResponse,
    StandaloneMatchRequest,
)
from app.api.v1.schemas.opportunity import OpportunityCreate, OpportunityRead
from app.core.exceptions import NotFoundException
from app.core.security import get_current_user
from app.services.matching_engine import (
    MatchingEngine,
    RequirementExtractor,
)

router = APIRouter(prefix="/opportunities", tags=["Opportunities & Role Matching"])


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED, summary="Save opportunity requirements")
def create_opportunity(
    payload: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a job opportunity, JD text, and explicit eligibility criteria. Owner-constrained."""
    opp = Opportunity(
        user_id=current_user.id,
        role_title=payload.role_title,
        company=payload.company,
        jd_text=payload.jd_text,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        explicit_criteria=payload.explicit_criteria,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


@router.get("/{opportunity_id}", response_model=OpportunityRead, summary="Get an owned opportunity")
def get_opportunity(
    opportunity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve an opportunity by ID. Owner-isolated."""
    stmt = select(Opportunity).where(
        Opportunity.id == opportunity_id,
        Opportunity.user_id == current_user.id,
    )
    opp = db.scalar(stmt)
    if not opp:
        raise NotFoundException("Opportunity not found", code="opportunity_not_found")
    return opp


@router.get("", response_model=List[OpportunityRead], summary="List owned opportunities")
def list_opportunities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all saved opportunities for the authenticated student."""
    stmt = select(Opportunity).where(Opportunity.user_id == current_user.id).order_by(Opportunity.created_at.desc())
    return db.scalars(stmt).all()


@router.post(
    "/extract-requirements",
    response_model=RequirementExtractResponse,
    summary="Extract requirements from job description text",
)
def extract_requirements(
    payload: RequirementExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse raw JD text and return classified skill requirements (required, preferred, unspecified)."""
    extracted = RequirementExtractor.extract_from_text(payload.jd_text)
    items = [
        ExtractedRequirementRead(
            original_phrase=item.original_phrase,
            normalized_skill=item.normalized_skill,
            category=item.category,
            source_context=item.source_context,
        )
        for item in extracted
    ]
    return RequirementExtractResponse(
        requirements=items,
        total_count=len(items),
    )


@router.post(
    "/match",
    response_model=MatchResponse,
    summary="Evaluate role matching standalone (without requiring database persistence)",
)
def match_standalone(
    payload: StandaloneMatchRequest,
    current_user: User = Depends(get_current_user),
):
    """Perform deterministic role matching and eligibility evaluation using provided profile and opportunity payloads."""
    report = MatchingEngine.evaluate(
        candidate_evidence=payload.profile,
        opportunity_data=payload.opportunity,
    )
    return report


@router.post(
    "/{opportunity_id}/match",
    response_model=MatchResponse,
    summary="Match authenticated student profile against a saved opportunity",
)
def match_student_opportunity(
    opportunity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare authenticated student's profile & evidence against a saved opportunity."""
    # 1. Fetch opportunity (owner-isolated)
    opp_stmt = select(Opportunity).where(
        Opportunity.id == opportunity_id,
        Opportunity.user_id == current_user.id,
    )
    opp = db.scalar(opp_stmt)
    if not opp:
        raise NotFoundException("Opportunity not found", code="opportunity_not_found")

    # 2. Fetch student profile with skills and projects
    prof_stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(
            joinedload(StudentProfile.skills),
            joinedload(StudentProfile.projects),
        )
    )
    profile = db.scalar(prof_stmt)
    if not profile:
        raise NotFoundException("Student profile not found. Please create a profile first.", code="profile_not_found")

    # 3. Format candidate evidence
    candidate_evidence: Dict[str, Any] = {
        "full_name": profile.full_name,
        "branch": profile.branch,
        "graduation_year": profile.graduation_year,
        "cgpa": profile.cgpa,
        "cgpa_scale": profile.cgpa_scale,
        "target_role": profile.target_role,
        "skills": [{"name": s.display_name, "normalized_name": s.normalized_name} for s in profile.skills],
        "projects": [{"title": p.title, "description": p.description, "url": p.url} for p in profile.projects],
        "resume_skills": [],
    }

    # 4. Format opportunity data
    opportunity_data: Dict[str, Any] = {
        "role_title": opp.role_title,
        "company": opp.company,
        "jd_text": opp.jd_text,
        "required_skills": opp.required_skills or [],
        "preferred_skills": opp.preferred_skills or [],
        "explicit_criteria": opp.explicit_criteria or {},
    }

    report = MatchingEngine.evaluate(
        candidate_evidence=candidate_evidence,
        opportunity_data=opportunity_data,
    )
    return report
