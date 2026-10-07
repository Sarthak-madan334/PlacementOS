"""Database engine, session management, and dependency injection."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Configure SQLite connect_args if using SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
