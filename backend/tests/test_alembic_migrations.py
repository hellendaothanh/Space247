import io
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command

from src.core.database import Base
from src.models import FavoriteProperty, Property, SavedSearchAlert, User, UserNotification  # noqa: F401


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
    """Verify that migration scripts are discoverable and have a single clean head revision '0004'."""
    cfg = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)

    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 head revision, got {heads}"
    assert heads[0] == "0006", f"Expected head revision to be '0006', got {heads[0]}"

    rev1 = script.get_revision("0001")
    assert rev1 is not None
    assert "pgvector" in rev1.doc.lower()
    assert "properties" in rev1.doc.lower()
    assert rev1.down_revision is None

    rev2 = script.get_revision("0002")
    assert rev2 is not None
    assert "users" in rev2.doc.lower()
    assert rev2.down_revision == "0001"

    rev3 = script.get_revision("0003")
    assert rev3 is not None
    assert "favorite" in rev3.doc.lower()
    assert rev3.down_revision == "0002"

    rev4 = script.get_revision("0004")
    assert rev4 is not None
    assert "alerts" in rev4.doc.lower() or "notifications" in rev4.doc.lower()
    assert rev4.down_revision == "0003"

    rev5 = script.get_revision("0005")
    assert rev5 is not None
    assert "images" in rev5.doc.lower() or "avatar" in rev5.doc.lower()
    assert rev5.down_revision == "0004"

    rev6 = script.get_revision("0006")
    assert rev6 is not None
    assert "project" in rev6.doc.lower()
    assert rev6.down_revision == "0005"


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

    # Verify favorite_properties table
    assert "CREATE TABLE favorite_properties" in generated_sql

    # Verify saved_search_alerts and user_notifications tables
    assert "CREATE TABLE saved_search_alerts" in generated_sql
    assert "CREATE TABLE user_notifications" in generated_sql

    # Verify 0005 additions
    assert "ALTER TABLE properties ADD COLUMN images TEXT[]" in generated_sql
    assert "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)" in generated_sql

    # Verify 0006 additions
    assert "CREATE TABLE projects" in generated_sql
    assert "ALTER TABLE properties ADD COLUMN project_id UUID" in generated_sql

    # Verify alembic version stamp
    assert "INSERT INTO alembic_version" in generated_sql
    assert "'0006'" in generated_sql


def test_alembic_downgrade_offline_sql_generation(capsys):
    """Verify that offline SQL generation for downgrade ('downgrade 0006:base --sql') produces clean rollback DDL."""
    cfg = get_alembic_config()

    # Generate downgrade SQL from 0006 to base using range syntax required by --sql mode
    command.downgrade(cfg, "0006:base", sql=True)
    captured = capsys.readouterr()
    generated_sql = captured.out

    assert "ALTER TABLE properties DROP COLUMN project_id;" in generated_sql
    assert "DROP TABLE projects;" in generated_sql
    assert "ALTER TABLE properties DROP COLUMN images;" in generated_sql
    assert "ALTER TABLE users DROP COLUMN avatar_url;" in generated_sql
    assert "DROP TABLE user_notifications;" in generated_sql
    assert "DROP TABLE saved_search_alerts;" in generated_sql
    assert "DROP TABLE favorite_properties;" in generated_sql
    assert "DROP TABLE users;" in generated_sql
    assert "DROP TABLE properties;" in generated_sql


def test_models_metadata_aligned_with_properties():
    """Verify that Base.metadata includes properties, users, favorites, alerts, notifications, and projects tables."""
    assert Base.metadata is not None
    assert "properties" in Base.metadata.tables
    assert "users" in Base.metadata.tables
    assert "favorite_properties" in Base.metadata.tables
    assert "saved_search_alerts" in Base.metadata.tables
    assert "user_notifications" in Base.metadata.tables
    assert "projects" in Base.metadata.tables

    prop_table = Base.metadata.tables["properties"]
    assert "embedding" in prop_table.c
    assert "title" in prop_table.c
    assert "user_id" in prop_table.c
    assert "images" in prop_table.c
    assert "project_id" in prop_table.c

    project_table = Base.metadata.tables["projects"]
    assert "name" in project_table.c
    assert "slug" in project_table.c
    assert "developer" in project_table.c
    assert "embedding" in project_table.c

    user_table = Base.metadata.tables["users"]
    assert "email" in user_table.c
    assert "hashed_password" in user_table.c
    assert "role" in user_table.c
    assert "avatar_url" in user_table.c

    fav_table = Base.metadata.tables["favorite_properties"]
    assert "user_id" in fav_table.c
    assert "property_id" in fav_table.c

    alert_table = Base.metadata.tables["saved_search_alerts"]
    assert "user_id" in alert_table.c
    assert "criteria" in alert_table.c
    assert "frequency" in alert_table.c

    notif_table = Base.metadata.tables["user_notifications"]
    assert "user_id" in notif_table.c
    assert "message" in notif_table.c
    assert "is_read" in notif_table.c
