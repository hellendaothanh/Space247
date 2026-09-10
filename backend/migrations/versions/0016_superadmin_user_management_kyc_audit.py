"""Add superadmin account moderation fields.

Revision ID: 0016
Revises: 0015
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("ban_reason", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "is_banned")
