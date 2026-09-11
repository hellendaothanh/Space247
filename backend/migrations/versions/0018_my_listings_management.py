"""Add my listings management fields: is_visible, refreshed_at, view_count.

Revision ID: 0018
Revises: 0017
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "properties",
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        "properties",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_properties_user_status", "properties", ["user_id", "status"])
    op.create_index("ix_properties_refreshed_at", "properties", ["refreshed_at"])


def downgrade() -> None:
    op.drop_index("ix_properties_refreshed_at", table_name="properties")
    op.drop_index("ix_properties_user_status", table_name="properties")
    op.drop_column("properties", "view_count")
    op.drop_column("properties", "refreshed_at")
    op.drop_column("properties", "is_visible")
