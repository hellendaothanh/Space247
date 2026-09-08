"""Add private user KYC verification metadata.

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("user_kyc_verifications", sa.Column("id", sa.UUID(), nullable=False), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("status", sa.String(length=20), server_default="pending", nullable=False), sa.Column("citizen_id_last4", sa.String(length=4), nullable=False), sa.Column("front_document_key", sa.String(length=512), nullable=False), sa.Column("back_document_key", sa.String(length=512), nullable=False), sa.Column("front_content_type", sa.String(length=100), nullable=False), sa.Column("back_content_type", sa.String(length=100), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id"))
    op.create_index("ix_user_kyc_verifications_user_id", "user_kyc_verifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_kyc_verifications_user_id", table_name="user_kyc_verifications")
    op.drop_table("user_kyc_verifications")
