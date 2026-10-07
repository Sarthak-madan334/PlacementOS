"""Opportunity and job requirements endpoints for authenticated students."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.db.models import Opportunity, User
from app.adapters.db.session import get_db
from app.api.v1.schemas.opportunity import OpportunityCreate, OpportunityRead
from app.core.exceptions import NotFoundException
from app.core.security import get_current_user

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


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
