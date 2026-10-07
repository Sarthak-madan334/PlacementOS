"""SQLAlchemy models for PlacementOS profile, evidence, and user identity."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR

from app.adapters.db.base import Base


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(str(value)))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    files: Mapped[List["ProfileFile"]] = relationship(
        "ProfileFile",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cgpa_scale: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Skill.normalized_name",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Project.created_at",
    )


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("profile_id", "normalized_name", name="uq_profile_skill_normalized"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    self_reported_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), default="self_reported", nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="skills")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="projects")


class ProfileFile(Base):
    __tablename__ = "profile_files"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")
