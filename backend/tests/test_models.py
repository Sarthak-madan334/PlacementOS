"""Tests for database models, cascading behavior, and constraints."""

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.adapters.db.models import User, StudentProfile, Skill, Project


def test_user_and_profile_cascade_delete(db_session: Session):
    """Deleting a User cascades to delete StudentProfile, Skills, and Projects."""
    # Create user
    user = User(auth_subject="auth0|cascade_test", email="cascade@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create profile
    profile = StudentProfile(
        user_id=user.id,
        full_name="Cascade Test",
        branch="CS",
        graduation_year=2026,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Add skill and project
    skill = Skill(
        profile_id=profile.id,
        normalized_name="python",
        display_name="Python",
    )
    project = Project(
        profile_id=profile.id,
        title="Test Project",
        description="Description",
    )
    db_session.add_all([skill, project])
    db_session.commit()

    profile_id = profile.id
    skill_id = skill.id
    project_id = project.id

    # Verify rows exist
    assert db_session.get(StudentProfile, profile_id) is not None
    assert db_session.get(Skill, skill_id) is not None
    assert db_session.get(Project, project_id) is not None

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify cascades
    assert db_session.get(StudentProfile, profile_id) is None
    assert db_session.get(Skill, skill_id) is None
    assert db_session.get(Project, project_id) is None
