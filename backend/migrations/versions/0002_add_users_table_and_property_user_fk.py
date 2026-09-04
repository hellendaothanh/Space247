"""Add users table and property user foreign key

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-04 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _upgrade_offline() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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

    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Add user_id column with foreign key to properties table
    op.add_column("properties", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_properties_user_id"), "properties", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_properties_user_id_users",
        "properties",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def _upgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    # 1. Create users table if not exists
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=50), nullable=True),
            sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    else:
        existing_indices = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_id" not in existing_indices and op.f("ix_users_id") not in existing_indices:
            op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        if "ix_users_email" not in existing_indices and op.f("ix_users_email") not in existing_indices:
            op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Add user_id column with foreign key to properties table
    if "properties" in tables:
        columns = {c["name"] for c in inspector.get_columns("properties")}
        if "user_id" not in columns:
            op.add_column("properties", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_index(op.f("ix_properties_user_id"), "properties", ["user_id"], unique=False)
            op.create_foreign_key(
                "fk_properties_user_id_users",
                "properties",
                "users",
                ["user_id"],
                ["id"],
                ondelete="SET NULL",
            )
        else:
            prop_indices = {idx["name"] for idx in inspector.get_indexes("properties")}
            if "ix_properties_user_id" not in prop_indices and op.f("ix_properties_user_id") not in prop_indices:
                op.create_index(op.f("ix_properties_user_id"), "properties", ["user_id"], unique=False)

            fks = {fk["name"] for fk in inspector.get_foreign_keys("properties")}
            if "fk_properties_user_id_users" not in fks and "properties_user_id_fkey" not in fks:
                op.create_foreign_key(
                    "fk_properties_user_id_users",
                    "properties",
                    "users",
                    ["user_id"],
                    ["id"],
                    ondelete="SET NULL",
                )


def upgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _upgrade_offline()
    else:
        _upgrade_online()


def _downgrade_offline() -> None:
    op.drop_constraint("fk_properties_user_id_users", "properties", type_="foreignkey")
    op.drop_index(op.f("ix_properties_user_id"), table_name="properties")
    op.drop_column("properties", "user_id")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")


def _downgrade_online() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "properties" in tables:
        fks = {fk["name"] for fk in inspector.get_foreign_keys("properties")}
        if "fk_properties_user_id_users" in fks:
            op.drop_constraint("fk_properties_user_id_users", "properties", type_="foreignkey")
        elif "properties_user_id_fkey" in fks:
            op.drop_constraint("properties_user_id_fkey", "properties", type_="foreignkey")

        prop_indices = {idx["name"] for idx in inspector.get_indexes("properties")}
        if "ix_properties_user_id" in prop_indices or op.f("ix_properties_user_id") in prop_indices:
            op.drop_index(op.f("ix_properties_user_id"), table_name="properties")

        columns = {c["name"] for c in inspector.get_columns("properties")}
        if "user_id" in columns:
            op.drop_column("properties", "user_id")

    if "users" in tables:
        user_indices = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_email" in user_indices or op.f("ix_users_email") in user_indices:
            op.drop_index(op.f("ix_users_email"), table_name="users")
        if "ix_users_id" in user_indices or op.f("ix_users_id") in user_indices:
            op.drop_index(op.f("ix_users_id"), table_name="users")
        op.drop_table("users")


def downgrade() -> None:
    context = op.get_context()
    if getattr(context, "as_sql", False) or context.bind is None:
        _downgrade_offline()
    else:
        _downgrade_online()


