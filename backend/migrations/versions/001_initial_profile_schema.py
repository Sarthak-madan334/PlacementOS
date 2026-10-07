"""Initial profile, evidence, and user schema

Revision ID: 001_initial_profile_schema
Revises: 
Create Date: 2026-10-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.adapters.db.models import GUID

revision: str = "001_initial_profile_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("auth_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_users_auth_subject"), "users", ["auth_subject"], unique=True)

    # 2. student_profiles table
    op.create_table(
        "student_profiles",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("branch", sa.String(length=255), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("cgpa", sa.Float(), nullable=True),
        sa.Column("cgpa_scale", sa.Float(), nullable=True),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_student_profiles_user_id"), "student_profiles", ["user_id"], unique=True)

    # 3. skills table
    op.create_table(
        "skills",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("profile_id", GUID(), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("self_reported_level", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("profile_id", "normalized_name", name="uq_profile_skill_normalized"),
    )
    op.create_index(op.f("ix_skills_profile_id"), "skills", ["profile_id"], unique=False)

    # 4. projects table
    op.create_table(
        "projects",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("profile_id", GUID(), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=True),
        sa.Column("end_date", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_projects_profile_id"), "projects", ["profile_id"], unique=False)

    # 5. profile_files table
    op.create_table(
        "profile_files",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_profile_files_user_id"), "profile_files", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("profile_files")
    op.drop_table("projects")
    op.drop_table("skills")
    op.drop_table("student_profiles")
    op.drop_table("users")
