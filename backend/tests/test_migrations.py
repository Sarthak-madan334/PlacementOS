"""Tests for Alembic migrations execution."""

import os
from alembic import command
from alembic.config import Config


def test_alembic_migrations_upgrade_and_downgrade():
    """Verify that migrations can upgrade to head and downgrade to base without errors."""
    ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg = Config(ini_path)
    # Use in-memory SQLite for migration test
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Upgrade again
    command.upgrade(alembic_cfg, "head")
