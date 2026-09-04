"""Add favorite_properties table

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-04 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _upgrade_offline() -> None:
    op.create_table(
        "favorite_properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "property_id", name="uq_favorite_user_property"),
    )
    op.create_index(op.f("ix_favorite_properties_user_id"), "favorite_properties", ["user_id"], unique=False)
    op.create_index(op.f("ix_favorite_properties_property_id"), "favorite_properties", ["property_id"], unique=False)


def _upgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "favorite_properties" not in tables:
        op.create_table(
            "favorite_properties",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "property_id", name="uq_favorite_user_property"),
        )
        op.create_index(op.f("ix_favorite_properties_user_id"), "favorite_properties", ["user_id"], unique=False)
        op.create_index(op.f("ix_favorite_properties_property_id"), "favorite_properties", ["property_id"], unique=False)
    else:
        existing_indices = {idx["name"] for idx in inspector.get_indexes("favorite_properties")}
        if "ix_favorite_properties_user_id" not in existing_indices and op.f("ix_favorite_properties_user_id") not in existing_indices:
            op.create_index(op.f("ix_favorite_properties_user_id"), "favorite_properties", ["user_id"], unique=False)
        if "ix_favorite_properties_property_id" not in existing_indices and op.f("ix_favorite_properties_property_id") not in existing_indices:
            op.create_index(op.f("ix_favorite_properties_property_id"), "favorite_properties", ["property_id"], unique=False)


def upgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _upgrade_offline()
    else:
        _upgrade_online()


def downgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        op.drop_table("favorite_properties")
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        if "favorite_properties" in set(inspector.get_table_names()):
            op.drop_table("favorite_properties")
