"""Add projects table and property project_id foreign key

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-05 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from geoalchemy2 import Geometry
import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _upgrade_offline() -> None:
    # 1. Create projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("developer", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="completed", nullable=False),
        sa.Column("total_units", sa.Integer(), nullable=True),
        sa.Column("launch_year", sa.Integer(), nullable=True),
        sa.Column("handover_year", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("ward", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geom", Geometry(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("images", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("master_plan_url", sa.String(length=500), nullable=True),
        sa.Column("legal_status", sa.String(length=255), nullable=True),
        sa.Column("price_range_min", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("price_range_max", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("amenities", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 2. Indexes for projects
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)
    op.create_index(op.f("ix_projects_slug"), "projects", ["slug"], unique=True)
    op.create_index(op.f("ix_projects_city"), "projects", ["city"], unique=False)
    op.create_index(op.f("ix_projects_developer"), "projects", ["developer"], unique=False)
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)

    op.create_index(
        "ix_projects_embedding_hnsw",
        "projects",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_index(
        "ix_projects_geom",
        "projects",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )

    # 3. Add project_id FK to properties table
    op.add_column(
        "properties",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_properties_project_id"), "properties", ["project_id"], unique=False)


def _upgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "projects" not in tables:
        _upgrade_offline()
    else:
        # Check projects.geom column
        proj_cols = {c["name"] for c in inspector.get_columns("projects")}
        if "geom" not in proj_cols:
            op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);")
            op.execute("CREATE INDEX IF NOT EXISTS ix_projects_geom ON projects USING gist (geom);")

        # Check properties.geom column
        prop_cols = {c["name"] for c in inspector.get_columns("properties")}
        if "geom" not in prop_cols:
            op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);")
            op.execute("CREATE INDEX IF NOT EXISTS ix_properties_geom ON properties USING gist (geom);")

        # Check properties.project_id column
        if "project_id" not in prop_cols:
            op.add_column(
                "properties",
                sa.Column(
                    "project_id",
                    postgresql.UUID(as_uuid=True),
                    sa.ForeignKey("projects.id", ondelete="SET NULL"),
                    nullable=True,
                ),
            )
            op.create_index(op.f("ix_properties_project_id"), "properties", ["project_id"], unique=False)


def upgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _upgrade_offline()
    else:
        _upgrade_online()


def downgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        op.drop_index(op.f("ix_properties_project_id"), table_name="properties")
        op.drop_column("properties", "project_id")
        op.drop_index("ix_projects_geom", table_name="projects")
        op.drop_index("ix_projects_embedding_hnsw", table_name="projects")
        op.drop_index(op.f("ix_projects_status"), table_name="projects")
        op.drop_index(op.f("ix_projects_developer"), table_name="projects")
        op.drop_index(op.f("ix_projects_city"), table_name="projects")
        op.drop_index(op.f("ix_projects_slug"), table_name="projects")
        op.drop_index(op.f("ix_projects_name"), table_name="projects")
        op.drop_index(op.f("ix_projects_id"), table_name="projects")
        op.drop_table("projects")
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        tables = set(inspector.get_table_names())
        if "properties" in tables:
            prop_cols = {c["name"] for c in inspector.get_columns("properties")}
            if "project_id" in prop_cols:
                op.drop_index(op.f("ix_properties_project_id"), table_name="properties")
                op.drop_column("properties", "project_id")
        if "projects" in tables:
            op.drop_table("projects")
