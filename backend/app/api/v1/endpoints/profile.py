"""Profile and evidence endpoints for authenticated students."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.adapters.db.models import ProfileFile, Project, Skill, StudentProfile, User
from app.adapters.db.session import get_db
from app.api.v1.schemas.profile import ProfileCreateOrUpdate, ProfileRead
from app.core.exceptions import NotFoundException
from app.core.security import get_current_user

router = APIRouter(prefix="/me/profile", tags=["Profile"])


@router.get("", response_model=ProfileRead, summary="Get current student's profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the authenticated student's profile, including skills and projects.
    Owner-constrained by authenticated user id.
    """
    stmt = (
        select(StudentProfile)
        .options(joinedload(StudentProfile.skills), joinedload(StudentProfile.projects))
        .where(StudentProfile.user_id == current_user.id)
    )
    profile = db.scalar(stmt)
    if not profile:
        raise NotFoundException("Profile has not been created yet for this student", code="profile_not_found")
    return profile


@router.put("", response_model=ProfileRead, summary="Create or update current student's profile")
def upsert_my_profile(
    payload: ProfileCreateOrUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotently create or update the authenticated student's profile, skills, and projects.
    Replaces existing skills and projects cleanly to prevent duplicate entries.
    """
    stmt = (
        select(StudentProfile)
        .options(joinedload(StudentProfile.skills), joinedload(StudentProfile.projects))
        .where(StudentProfile.user_id == current_user.id)
    )
    profile = db.scalar(stmt)

    if not profile:
        profile = StudentProfile(
            user_id=current_user.id,
            full_name=payload.full_name,
            branch=payload.branch,
            graduation_year=payload.graduation_year,
            cgpa=payload.cgpa,
            cgpa_scale=payload.cgpa_scale,
            target_role=payload.target_role,
        )
        db.add(profile)
        db.flush()  # Generate profile.id
    else:
        profile.full_name = payload.full_name
        profile.branch = payload.branch
        profile.graduation_year = payload.graduation_year
        profile.cgpa = payload.cgpa
        profile.cgpa_scale = payload.cgpa_scale
        profile.target_role = payload.target_role

        # Clear existing skills and projects for clean idempotent replacement
        profile.skills.clear()
        profile.projects.clear()
        db.flush()

    # Add skills
    for skill_in in payload.skills:
        skill = Skill(
            profile_id=profile.id,
            normalized_name=skill_in.normalized_name,
            display_name=skill_in.display_name,
            self_reported_level=skill_in.self_reported_level,
            source=skill_in.source or "self_reported",
        )
        profile.skills.append(skill)

    # Add projects
    for proj_in in payload.projects:
        proj = Project(
            profile_id=profile.id,
            title=proj_in.title,
            description=proj_in.description,
            url=proj_in.url,
            start_date=proj_in.start_date,
            end_date=proj_in.end_date,
        )
        profile.projects.append(proj)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("", status_code=status.HTTP_200_OK, summary="Delete current student's profile")
def delete_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the authenticated student's profile and all associated evidence.
    Cascade handles skills and projects. Also cleans up associated user profile files.
    """
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    profile = db.scalar(stmt)

    if not profile:
        raise NotFoundException("Profile not found", code="profile_not_found")

    # Clean up associated profile files/resumes for this user
    files_stmt = select(ProfileFile).where(ProfileFile.user_id == current_user.id)
    user_files = db.scalars(files_stmt).all()
    for uf in user_files:
        db.delete(uf)

    db.delete(profile)
    db.commit()

    return {
        "status": "deleted",
        "detail": "Profile and all associated evidence successfully deleted",
    }
