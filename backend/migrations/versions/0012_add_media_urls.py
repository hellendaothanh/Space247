"""Add property and project media URLs.

Revision ID: 0012
Revises: 0011
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("properties", "projects"):
        op.add_column(table, sa.Column("video_url", sa.String(length=500), nullable=True))
        op.add_column(table, sa.Column("virtual_tour_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    for table in ("projects", "properties"):
        op.drop_column(table, "virtual_tour_url")
        op.drop_column(table, "video_url")
