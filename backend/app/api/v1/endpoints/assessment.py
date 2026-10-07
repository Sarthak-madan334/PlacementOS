"""Assessment and readiness evaluation endpoints for authenticated students."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.adapters.db.models import Assessment, Opportunity, StudentProfile, User
from app.adapters.db.session import get_db
from app.api.v1.schemas.assessment import (
    AssessmentCreate,
    AssessmentRead,
    EligibilityDetail,
    EligibilityReasonSchema,
    FactorDetail,
    GapDetail,
    NextActionDetail,
    ReadinessScoreDetail,
    RoleMatchDetail,
    StrengthDetail,
)
from app.core.exceptions import NotFoundException
from app.core.security import get_current_user
from app.services.readiness_engine import (
    OpportunityRequirement,
    ProjectEvidence,
    ReadinessEngine,
    ResumeEvidence,
    SkillEvidence,
    StudentProfileEvidence,
)
from app.services.resume_parser import parse_resume_bytes

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def _build_profile_evidence(profile: StudentProfile, resume_text: Optional[str] = None) -> StudentProfileEvidence:
    """Map DB profile entity into pure scoring StudentProfileEvidence domain object."""
    skills_evidence = [
        SkillEvidence(
            name=s.display_name,
            normalized_name=s.normalized_name,
            source=s.source or "self_reported",
            self_reported_level=s.self_reported_level,
        )
        for s in profile.skills
    ]

    projects_evidence = [
        ProjectEvidence(
            title=p.title,
            description=p.description,
            url=p.url,
            start_date=p.start_date,
            end_date=p.end_date,
        )
        for p in profile.projects
    ]

    resume_evidence: Optional[ResumeEvidence] = None
    if resume_text and resume_text.strip():
        # Parse text resume using Phase 03 parser
        parsed = parse_resume_bytes(
            resume_text.encode("utf-8"),
            filename="student_resume.txt",
        )
        facts = parsed.candidate_facts
        has_contact = bool(facts.contact.email or facts.contact.phone or facts.contact.name)
        has_education = len(facts.education) > 0
        has_skills = len(facts.skills) > 0
        has_experience = len(facts.experience) > 0 or len(facts.projects) > 0

        action_verbs_count = sum(1 for q in parsed.quality_signals if q.signal == "action_verb")
        quantified_count = sum(1 for q in parsed.quality_signals if q.signal == "quantified_outcome")
        weak_count = sum(1 for q in parsed.quality_signals if q.signal == "weak_language")

        resume_evidence = ResumeEvidence(
            sections_present=parsed.sections_detected,
            contact_present=has_contact,
            education_present=has_education,
            skills_present=has_skills,
            experience_present=has_experience,
            extracted_skills=[s.display_name for s in facts.skills],
            action_verbs_count=action_verbs_count,
            quantified_outcomes_count=quantified_count,
            weak_language_count=weak_count,
            raw_text=resume_text,
        )

    return StudentProfileEvidence(
        full_name=profile.full_name,
        branch=profile.branch,
        graduation_year=profile.graduation_year,
        cgpa=profile.cgpa,
        cgpa_scale=profile.cgpa_scale,
        target_role=profile.target_role,
        skills=skills_evidence,
        projects=projects_evidence,
        resume=resume_evidence,
    )


@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED, summary="Evaluate and save placement readiness assessment")
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run deterministic readiness evaluation for current authenticated student and save result."""
    # 1. Fetch current student's profile
    stmt = (
        select(StudentProfile)
        .options(joinedload(StudentProfile.skills), joinedload(StudentProfile.projects))
        .where(StudentProfile.user_id == current_user.id)
    )
    profile = db.scalar(stmt)
    if not profile:
        raise NotFoundException("Profile has not been created yet for this student", code="profile_not_found")

    # 2. Fetch or construct opportunity requirements
    opportunity_record: Optional[Opportunity] = None
    opp_req: Optional[OpportunityRequirement] = None

    if payload.opportunity_id:
        opp_stmt = select(Opportunity).where(
            Opportunity.id == payload.opportunity_id,
            Opportunity.user_id == current_user.id,
        )
        opportunity_record = db.scalar(opp_stmt)
        if not opportunity_record:
            raise NotFoundException("Opportunity not found", code="opportunity_not_found")

        opp_req = OpportunityRequirement(
            role_title=opportunity_record.role_title,
            company=opportunity_record.company,
            jd_text=opportunity_record.jd_text,
            required_skills=opportunity_record.required_skills or [],
            preferred_skills=opportunity_record.preferred_skills or [],
            explicit_criteria=opportunity_record.explicit_criteria or {},
        )
    elif payload.target_role or payload.required_skills or payload.jd_text or payload.explicit_criteria:
        opp_req = OpportunityRequirement(
            role_title=payload.target_role or profile.target_role,
            jd_text=payload.jd_text,
            required_skills=payload.required_skills or [],
            preferred_skills=[],
            explicit_criteria=payload.explicit_criteria or {},
        )
    elif profile.target_role:
        # Default to student's declared target role
        opp_req = OpportunityRequirement(
            role_title=profile.target_role,
            required_skills=[],
            preferred_skills=[],
            explicit_criteria={},
        )

    # 3. Build pure scoring evidence domain object
    profile_evidence = _build_profile_evidence(profile, payload.resume_text)

    # 4. Pure deterministic evaluation
    report = ReadinessEngine.evaluate(profile_evidence, opp_req)

    # 5. Persist assessment record in database
    input_snapshot = {
        "profile_id": str(profile.id),
        "target_role": opp_req.role_title if opp_req else profile.target_role,
        "cgpa": profile.cgpa,
        "branch": profile.branch,
        "graduation_year": profile.graduation_year,
        "skills_count": len(profile.skills),
        "projects_count": len(profile.projects),
        "has_resume": bool(profile_evidence.resume is not None),
    }

    eligibility_dict = {
        "status": report.eligibility.status,
        "reasons": [{"code": r.code, "message": r.message} for r in report.eligibility.reasons],
    }

    readiness_dict = {
        "score": report.readiness.score,
        "confidence": report.readiness.confidence,
        "scoring_version": report.readiness.scoring_version,
        "factors": [
            {
                "key": f.key,
                "name": f.name,
                "score": f.score,
                "weight": f.weight,
                "available": f.available,
                "evidence": f.evidence,
                "explanation": f.explanation,
            }
            for f in report.readiness.factors
        ],
        "excluded_factors": report.readiness.excluded_factors,
    }

    role_match_dict = None
    if report.role_match:
        role_match_dict = {
            "score": report.role_match.score,
            "matched": report.role_match.matched,
            "missing": report.role_match.missing,
            "unknown": report.role_match.unknown,
        }

    strengths_list = [{"label": s.label, "evidence": s.evidence, "confidence": s.confidence} for s in report.strengths]
    gaps_list = [{"label": g.label, "importance": g.importance, "reason": g.reason} for g in report.gaps]
    actions_list = [
        {"title": a.title, "rationale": a.rationale, "completion_evidence": a.completion_evidence}
        for a in report.next_actions
    ]

    assessment = Assessment(
        user_id=current_user.id,
        profile_id=profile.id,
        opportunity_id=opportunity_record.id if opportunity_record else None,
        eligibility_result=eligibility_dict,
        readiness_result=readiness_dict,
        role_match_result=role_match_dict,
        strengths=strengths_list,
        gaps=gaps_list,
        next_actions=actions_list,
        scoring_version=report.scoring_version,
        input_snapshot=input_snapshot,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # 6. Return response matching exact schema
    return AssessmentRead(
        id=assessment.id,
        eligibility=EligibilityDetail(
            status=report.eligibility.status,
            reasons=[EligibilityReasonSchema(code=r.code, message=r.message) for r in report.eligibility.reasons],
        ),
        readiness=ReadinessScoreDetail(
            score=report.readiness.score,
            confidence=report.readiness.confidence,
            scoring_version=report.readiness.scoring_version,
            factors=[
                FactorDetail(
                    key=f.key,
                    name=f.name,
                    score=f.score,
                    weight=f.weight,
                    available=f.available,
                    evidence=f.evidence,
                    explanation=f.explanation,
                )
                for f in report.readiness.factors
            ],
            excluded_factors=report.readiness.excluded_factors,
        ),
        role_match=RoleMatchDetail(
            score=report.role_match.score,
            matched=report.role_match.matched,
            missing=report.role_match.missing,
            unknown=report.role_match.unknown,
        ) if report.role_match else None,
        strengths=[StrengthDetail(label=s.label, evidence=s.evidence, confidence=s.confidence) for s in report.strengths],
        gaps=[GapDetail(label=g.label, importance=g.importance, reason=g.reason) for g in report.gaps],
        next_actions=[
            NextActionDetail(title=a.title, rationale=a.rationale, completion_evidence=a.completion_evidence)
            for a in report.next_actions
        ],
        scoring_version=report.scoring_version,
        created_at=assessment.created_at,
    )


@router.get("/{assessment_id}", response_model=AssessmentRead, summary="Get an owned assessment")
def get_assessment(
    assessment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve an assessment by ID. Owner-isolated."""
    stmt = select(Assessment).where(
        Assessment.id == assessment_id,
        Assessment.user_id == current_user.id,
    )
    assessment = db.scalar(stmt)
    if not assessment:
        raise NotFoundException("Assessment not found", code="assessment_not_found")

    return AssessmentRead(
        id=assessment.id,
        eligibility=EligibilityDetail(
            status=assessment.eligibility_result.get("status", "unknown"),
            reasons=[
                EligibilityReasonSchema(code=r.get("code", ""), message=r.get("message", ""))
                for r in assessment.eligibility_result.get("reasons", [])
            ],
        ),
        readiness=ReadinessScoreDetail(
            score=assessment.readiness_result.get("score"),
            confidence=assessment.readiness_result.get("confidence", "low"),
            scoring_version=assessment.readiness_result.get("scoring_version", "cp-v1"),
            factors=[
                FactorDetail(
                    key=f.get("key", ""),
                    name=f.get("name", ""),
                    score=f.get("score", 0),
                    weight=f.get("weight", 0.0),
                    available=f.get("available", False),
                    evidence=f.get("evidence", []),
                    explanation=f.get("explanation", ""),
                )
                for f in assessment.readiness_result.get("factors", [])
            ],
            excluded_factors=assessment.readiness_result.get("excluded_factors", []),
        ),
        role_match=RoleMatchDetail(
            score=assessment.role_match_result.get("score") if assessment.role_match_result else None,
            matched=assessment.role_match_result.get("matched", []) if assessment.role_match_result else [],
            missing=assessment.role_match_result.get("missing", []) if assessment.role_match_result else [],
            unknown=assessment.role_match_result.get("unknown", []) if assessment.role_match_result else [],
        ) if assessment.role_match_result else None,
        strengths=[
            StrengthDetail(
                label=s.get("label", ""),
                evidence=s.get("evidence", ""),
                confidence=s.get("confidence", "medium"),
            )
            for s in (assessment.strengths or [])
        ],
        gaps=[
            GapDetail(
                label=g.get("label", ""),
                importance=g.get("importance", "required"),
                reason=g.get("reason", ""),
            )
            for g in (assessment.gaps or [])
        ],
        next_actions=[
            NextActionDetail(
                title=a.get("title", ""),
                rationale=a.get("rationale", ""),
                completion_evidence=a.get("completion_evidence", ""),
            )
            for a in (assessment.next_actions or [])
        ],
        scoring_version=assessment.scoring_version,
        created_at=assessment.created_at,
    )


@router.get("", response_model=List[AssessmentRead], summary="List owned assessments")
def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent assessments for the authenticated student."""
    stmt = select(Assessment).where(Assessment.user_id == current_user.id).order_by(Assessment.created_at.desc())
    assessments = db.scalars(stmt).all()
    results = []
    for assessment in assessments:
        results.append(
            AssessmentRead(
                id=assessment.id,
                eligibility=EligibilityDetail(
                    status=assessment.eligibility_result.get("status", "unknown"),
                    reasons=[
                        EligibilityReasonSchema(code=r.get("code", ""), message=r.get("message", ""))
                        for r in assessment.eligibility_result.get("reasons", [])
                    ],
                ),
                readiness=ReadinessScoreDetail(
                    score=assessment.readiness_result.get("score"),
                    confidence=assessment.readiness_result.get("confidence", "low"),
                    scoring_version=assessment.readiness_result.get("scoring_version", "cp-v1"),
                    factors=[
                        FactorDetail(
                            key=f.get("key", ""),
                            name=f.get("name", ""),
                            score=f.get("score", 0),
                            weight=f.get("weight", 0.0),
                            available=f.get("available", False),
                            evidence=f.get("evidence", []),
                            explanation=f.get("explanation", ""),
                        )
                        for f in assessment.readiness_result.get("factors", [])
                    ],
                    excluded_factors=assessment.readiness_result.get("excluded_factors", []),
                ),
                role_match=RoleMatchDetail(
                    score=assessment.role_match_result.get("score") if assessment.role_match_result else None,
                    matched=assessment.role_match_result.get("matched", []) if assessment.role_match_result else [],
                    missing=assessment.role_match_result.get("missing", []) if assessment.role_match_result else [],
                    unknown=assessment.role_match_result.get("unknown", []) if assessment.role_match_result else [],
                ) if assessment.role_match_result else None,
                strengths=[
                    StrengthDetail(
                        label=s.get("label", ""),
                        evidence=s.get("evidence", ""),
                        confidence=s.get("confidence", "medium"),
                    )
                    for s in (assessment.strengths or [])
                ],
                gaps=[
                    GapDetail(
                        label=g.get("label", ""),
                        importance=g.get("importance", "required"),
                        reason=g.get("reason", ""),
                    )
                    for g in (assessment.gaps or [])
                ],
                next_actions=[
                    NextActionDetail(
                        title=a.get("title", ""),
                        rationale=a.get("rationale", ""),
                        completion_evidence=a.get("completion_evidence", ""),
                    )
                    for a in (assessment.next_actions or [])
                ],
                scoring_version=assessment.scoring_version,
                created_at=assessment.created_at,
            )
        )
    return results
