"""Add saved_search_alerts and user_notifications tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-04 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _upgrade_offline() -> None:
    op.create_table(
        "saved_search_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("frequency", sa.String(50), server_default="instant", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_saved_search_alerts_user_id"), "saved_search_alerts", ["user_id"], unique=False)
    op.create_index(op.f("ix_saved_search_alerts_is_active"), "saved_search_alerts", ["is_active"], unique=False)

    op.create_table(
        "user_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(50), server_default="saved_search_match", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alert_id"], ["saved_search_alerts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_user_notifications_user_id"), "user_notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_notifications_is_read"), "user_notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_user_notifications_created_at"), "user_notifications", ["created_at"], unique=False)


def _upgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "saved_search_alerts" not in tables:
        op.create_table(
            "saved_search_alerts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("frequency", sa.String(50), server_default="instant", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
            sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_saved_search_alerts_user_id"), "saved_search_alerts", ["user_id"], unique=False)
        op.create_index(op.f("ix_saved_search_alerts_is_active"), "saved_search_alerts", ["is_active"], unique=False)
    else:
        existing_indices = {idx["name"] for idx in inspector.get_indexes("saved_search_alerts")}
        if "ix_saved_search_alerts_user_id" not in existing_indices and op.f("ix_saved_search_alerts_user_id") not in existing_indices:
            op.create_index(op.f("ix_saved_search_alerts_user_id"), "saved_search_alerts", ["user_id"], unique=False)
        if "ix_saved_search_alerts_is_active" not in existing_indices and op.f("ix_saved_search_alerts_is_active") not in existing_indices:
            op.create_index(op.f("ix_saved_search_alerts_is_active"), "saved_search_alerts", ["is_active"], unique=False)

    if "user_notifications" not in tables:
        op.create_table(
            "user_notifications",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("notification_type", sa.String(50), server_default="saved_search_match", nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["alert_id"], ["saved_search_alerts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_user_notifications_user_id"), "user_notifications", ["user_id"], unique=False)
        op.create_index(op.f("ix_user_notifications_is_read"), "user_notifications", ["is_read"], unique=False)
        op.create_index(op.f("ix_user_notifications_created_at"), "user_notifications", ["created_at"], unique=False)
    else:
        existing_indices = {idx["name"] for idx in inspector.get_indexes("user_notifications")}
        if "ix_user_notifications_user_id" not in existing_indices and op.f("ix_user_notifications_user_id") not in existing_indices:
            op.create_index(op.f("ix_user_notifications_user_id"), "user_notifications", ["user_id"], unique=False)
        if "ix_user_notifications_is_read" not in existing_indices and op.f("ix_user_notifications_is_read") not in existing_indices:
            op.create_index(op.f("ix_user_notifications_is_read"), "user_notifications", ["is_read"], unique=False)
        if "ix_user_notifications_created_at" not in existing_indices and op.f("ix_user_notifications_created_at") not in existing_indices:
            op.create_index(op.f("ix_user_notifications_created_at"), "user_notifications", ["created_at"], unique=False)


def upgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _upgrade_offline()
    else:
        _upgrade_online()


def downgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        op.drop_table("user_notifications")
        op.drop_table("saved_search_alerts")
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        tables = set(inspector.get_table_names())
        if "user_notifications" in tables:
            op.drop_table("user_notifications")
        if "saved_search_alerts" in tables:
            op.drop_table("saved_search_alerts")
