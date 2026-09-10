"""Rental Experience & Tenant Conversion Suite: per-unit media/amenities and
property surroundings/security features for transparent tenant discovery.

Revision ID: 0015
Revises: 0014
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Per-unit media & amenities (images/max_occupants already exist since 0009)
    op.add_column("rental_units", sa.Column("floor_plan_url", sa.String(length=500), nullable=True))
    op.add_column(
        "rental_units",
        sa.Column("room_amenities", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"),
    )
    # Building-level video review, nearby commute distances and safety commitments
    op.add_column("rental_properties", sa.Column("video_url", sa.String(length=500), nullable=True))
    op.add_column(
        "rental_properties",
        sa.Column("surroundings", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"),
    )
    op.add_column(
        "rental_properties",
        sa.Column("security_features", postgresql.ARRAY(sa.Text()), nullable=True, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("rental_properties", "security_features")
    op.drop_column("rental_properties", "surroundings")
    op.drop_column("rental_properties", "video_url")
    op.drop_column("rental_units", "room_amenities")
    op.drop_column("rental_units", "floor_plan_url")
