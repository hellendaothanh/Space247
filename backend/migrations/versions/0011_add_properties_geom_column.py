"""Add missing spatial geometry column to properties.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-08 07:40:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_properties_geom ON properties USING gist (geom)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_geom")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS geom")
