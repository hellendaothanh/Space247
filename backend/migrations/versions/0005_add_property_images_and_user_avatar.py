"""Add property images and user avatar_url

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-04 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _upgrade_offline() -> None:
    op.add_column(
        "properties",
        sa.Column("images", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(500), nullable=True),
    )


def _upgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    prop_columns = {col["name"] for col in inspector.get_columns("properties")}
    if "images" not in prop_columns:
        op.add_column(
            "properties",
            sa.Column("images", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
        )

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "avatar_url" not in user_columns:
        op.add_column(
            "users",
            sa.Column("avatar_url", sa.String(500), nullable=True),
        )


def upgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _upgrade_offline()
    else:
        _upgrade_online()


def downgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        op.drop_column("properties", "images")
        op.drop_column("users", "avatar_url")
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        prop_columns = {col["name"] for col in inspector.get_columns("properties")}
        if "images" in prop_columns:
            op.drop_column("properties", "images")

        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "avatar_url" in user_columns:
            op.drop_column("users", "avatar_url")
