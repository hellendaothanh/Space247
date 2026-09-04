import io
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command

from src.core.database import Base
from src.models.property import Property  # noqa: F401


BACKEND_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI_PATH = BACKEND_DIR / "alembic.ini"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"


def get_alembic_config(stdout_buffer: io.StringIO | None = None) -> Config:
    """Helper to load alembic Config pointing to backend/alembic.ini."""
    cfg = Config(str(ALEMBIC_INI_PATH), stdout=stdout_buffer)
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def test_alembic_configuration_and_paths():
    """Verify that alembic.ini and migration directory structure exist and are valid."""
    assert ALEMBIC_INI_PATH.is_file(), f"alembic.ini not found at {ALEMBIC_INI_PATH}"
    assert MIGRATIONS_DIR.is_dir(), f"migrations dir not found at {MIGRATIONS_DIR}"
    assert (MIGRATIONS_DIR / "env.py").is_file(), "env.py missing in migrations/"
    assert (MIGRATIONS_DIR / "script.py.mako").is_file(), "script.py.mako missing in migrations/"
    assert (MIGRATIONS_DIR / "versions").is_dir(), "versions/ dir missing in migrations/"


def test_alembic_script_directory_and_head_revision():
    """Verify that migration scripts are discoverable and have a single clean head revision '0002'."""
    cfg = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)

    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 head revision, got {heads}"
    assert heads[0] == "0002", f"Expected head revision to be '0002', got {heads[0]}"

    rev1 = script.get_revision("0001")
    assert rev1 is not None
    assert "pgvector" in rev1.doc.lower()
    assert "properties" in rev1.doc.lower()
    assert rev1.down_revision is None

    rev2 = script.get_revision("0002")
    assert rev2 is not None
    assert "users" in rev2.doc.lower()
    assert rev2.down_revision == "0001"


def test_alembic_offline_sql_generation(capsys):
    """Verify that offline SQL generation ('upgrade head --sql') produces proper DDL statements."""
    cfg = get_alembic_config()

    # Run offline upgrade to head
    command.upgrade(cfg, "head", sql=True)
    captured = capsys.readouterr()
    generated_sql = captured.out

    # Verify vector extension
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in generated_sql

    # Verify properties table
    assert "CREATE TABLE properties" in generated_sql
    assert "embedding VECTOR(768)" in generated_sql

    # Verify users table and foreign key
    assert "CREATE TABLE users" in generated_sql
    assert "ALTER TABLE properties ADD COLUMN user_id UUID" in generated_sql

    # Verify alembic version stamp
    assert "INSERT INTO alembic_version" in generated_sql
    assert "'0002'" in generated_sql


def test_alembic_downgrade_offline_sql_generation(capsys):
    """Verify that offline SQL generation for downgrade ('downgrade 0002:base --sql') produces clean rollback DDL."""
    cfg = get_alembic_config()

    # Generate downgrade SQL from 0002 to base using range syntax required by --sql mode
    command.downgrade(cfg, "0002:base", sql=True)
    captured = capsys.readouterr()
    generated_sql = captured.out

    assert "DROP TABLE users;" in generated_sql
    assert "DROP TABLE properties;" in generated_sql


def test_models_metadata_aligned_with_properties():
    """Verify that Base.metadata includes properties and users tables."""
    assert Base.metadata is not None
    assert "properties" in Base.metadata.tables
    assert "users" in Base.metadata.tables

    prop_table = Base.metadata.tables["properties"]
    assert "embedding" in prop_table.c
    assert "title" in prop_table.c
    assert "user_id" in prop_table.c

    user_table = Base.metadata.tables["users"]
    assert "email" in user_table.c
    assert "hashed_password" in user_table.c
    assert "role" in user_table.c
