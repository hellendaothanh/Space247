"""Initial pgvector extension, properties table, HNSW index and FTS GIN index

Revision ID: 0001
Revises: 
Create Date: 2026-09-04 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Register PostgreSQL vector extension if not present
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Create properties table
    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("property_type", sa.String(length=50), nullable=False),
        sa.Column("listing_type", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="VND", nullable=False),
        sa.Column("area_sqm", sa.Float(), nullable=False),
        sa.Column("num_bedrooms", sa.Integer(), nullable=True),
        sa.Column("num_bathrooms", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("ward", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
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

    # 3. Create regular B-tree indexes
    op.create_index(op.f("ix_properties_id"), "properties", ["id"], unique=False)
    op.create_index(op.f("ix_properties_title"), "properties", ["title"], unique=False)
    op.create_index(op.f("ix_properties_property_type"), "properties", ["property_type"], unique=False)
    op.create_index(op.f("ix_properties_listing_type"), "properties", ["listing_type"], unique=False)
    op.create_index(op.f("ix_properties_price"), "properties", ["price"], unique=False)
    op.create_index(op.f("ix_properties_area_sqm"), "properties", ["area_sqm"], unique=False)
    op.create_index(op.f("ix_properties_district"), "properties", ["district"], unique=False)
    op.create_index(op.f("ix_properties_city"), "properties", ["city"], unique=False)
    op.create_index(op.f("ix_properties_status"), "properties", ["status"], unique=False)

    # 4. Create HNSW Vector Index on embedding column
    op.create_index(
        "ix_properties_embedding_hnsw",
        "properties",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # 5. Create GIN Full-Text Search Index over concatenated metadata
    op.create_index(
        "ix_properties_fts",
        "properties",
        [
            sa.text(
                "to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(address, '') || ' ' || coalesce(ward, '') || ' ' || coalesce(district, '') || ' ' || coalesce(city, '') || ' ' || coalesce(description, ''))"
            )
        ],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    # Drop custom indexes first
    op.drop_index("ix_properties_fts", table_name="properties")
    op.drop_index("ix_properties_embedding_hnsw", table_name="properties")

    # Drop standard indexes
    op.drop_index(op.f("ix_properties_status"), table_name="properties")
    op.drop_index(op.f("ix_properties_city"), table_name="properties")
    op.drop_index(op.f("ix_properties_district"), table_name="properties")
    op.drop_index(op.f("ix_properties_area_sqm"), table_name="properties")
    op.drop_index(op.f("ix_properties_price"), table_name="properties")
    op.drop_index(op.f("ix_properties_listing_type"), table_name="properties")
    op.drop_index(op.f("ix_properties_property_type"), table_name="properties")
    op.drop_index(op.f("ix_properties_title"), table_name="properties")
    op.drop_index(op.f("ix_properties_id"), table_name="properties")

    # Drop properties table
    op.drop_table("properties")
