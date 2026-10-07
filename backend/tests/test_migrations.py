import os
from pathlib import Path
from alembic import command
from alembic.config import Config


def test_alembic_migrations_upgrade_and_downgrade(tmp_path: Path):
    """Verify that migrations can upgrade to head and downgrade to base without errors on an isolated db."""
    ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg = Config(ini_path)

    # Use isolated temp SQLite file for migration test
    test_db_file = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{test_db_file.as_posix()}"
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Upgrade again
    command.upgrade(alembic_cfg, "head")
