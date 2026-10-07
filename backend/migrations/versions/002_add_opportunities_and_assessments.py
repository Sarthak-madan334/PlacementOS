"""Add opportunities and assessments schema

Revision ID: 002_add_opportunities_and_assessments
Revises: 001_initial_profile_schema
Create Date: 2026-10-07 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.adapters.db.models import GUID

revision: str = "002_add_opportunities_and_assessments"
down_revision: Union[str, None] = "001_initial_profile_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. opportunities table
    op.create_table(
        "opportunities",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("jd_text", sa.Text(), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("preferred_skills", sa.JSON(), nullable=False),
        sa.Column("explicit_criteria", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_opportunities_user_id"), "opportunities", ["user_id"], unique=False)

    # 2. assessments table
    op.create_table(
        "assessments",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", GUID(), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", GUID(), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("eligibility_result", sa.JSON(), nullable=False),
        sa.Column("readiness_result", sa.JSON(), nullable=False),
        sa.Column("role_match_result", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("next_actions", sa.JSON(), nullable=False),
        sa.Column("scoring_version", sa.String(length=50), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_assessments_user_id"), "assessments", ["user_id"], unique=False)
    op.create_index(op.f("ix_assessments_profile_id"), "assessments", ["profile_id"], unique=False)
    op.create_index(op.f("ix_assessments_opportunity_id"), "assessments", ["opportunity_id"], unique=False)


def downgrade() -> None:
    op.drop_table("assessments")
    op.drop_table("opportunities")
