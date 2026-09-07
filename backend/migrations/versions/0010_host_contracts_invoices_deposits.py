"""Host contracts, monthly invoices, and deposit transactions

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-07 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. rental_contracts table
    op.create_table(
        "rental_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_name", sa.String(255), nullable=False),
        sa.Column("tenant_phone", sa.String(50), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rental_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("payment_cycle_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("electricity_rate", sa.Numeric(10, 2), nullable=False, server_default="3500"),
        sa.Column("water_rate", sa.Numeric(10, 2), nullable=False, server_default="20000"),
        sa.Column("water_billing_type", sa.String(20), nullable=False, server_default="per_m3"),
        sa.Column("service_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rental_contracts_unit_id", "rental_contracts", ["unit_id"], unique=False)
    op.create_index("ix_rental_contracts_property_id", "rental_contracts", ["property_id"], unique=False)
    op.create_index("ix_rental_contracts_host_id", "rental_contracts", ["host_id"], unique=False)
    op.create_index("ix_rental_contracts_tenant_id", "rental_contracts", ["tenant_id"], unique=False)
    op.create_index("ix_rental_contracts_status", "rental_contracts", ["status"], unique=False)

    # 2. monthly_invoices table
    op.create_table(
        "monthly_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_month", sa.String(7), nullable=False),
        sa.Column("room_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("electricity_previous_index", sa.Float(), nullable=False, server_default="0"),
        sa.Column("electricity_current_index", sa.Float(), nullable=False, server_default="0"),
        sa.Column("electricity_rate", sa.Numeric(10, 2), nullable=False, server_default="3500"),
        sa.Column("electricity_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("water_previous_index", sa.Float(), nullable=True, server_default="0"),
        sa.Column("water_current_index", sa.Float(), nullable=True, server_default="0"),
        sa.Column("water_rate", sa.Numeric(10, 2), nullable=False, server_default="20000"),
        sa.Column("water_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("service_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("other_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_reminded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_monthly_invoices_contract_id", "monthly_invoices", ["contract_id"], unique=False)
    op.create_index("ix_monthly_invoices_unit_id", "monthly_invoices", ["unit_id"], unique=False)
    op.create_index("ix_monthly_invoices_host_id", "monthly_invoices", ["host_id"], unique=False)
    op.create_index("ix_monthly_invoices_tenant_id", "monthly_invoices", ["tenant_id"], unique=False)
    op.create_index("ix_monthly_invoices_billing_month", "monthly_invoices", ["billing_month"], unique=False)
    op.create_index("ix_monthly_invoices_status", "monthly_invoices", ["status"], unique=False)

    # 3. deposit_transactions table
    op.create_table(
        "deposit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inquiry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_inquiries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("reference_code", sa.String(50), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False, server_default="vietqr"),
        sa.Column("vietqr_url", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deposit_transactions_unit_id", "deposit_transactions", ["unit_id"], unique=False)
    op.create_index("ix_deposit_transactions_tenant_id", "deposit_transactions", ["tenant_id"], unique=False)
    op.create_index("ix_deposit_transactions_host_id", "deposit_transactions", ["host_id"], unique=False)
    op.create_index("ix_deposit_transactions_reference_code", "deposit_transactions", ["reference_code"], unique=True)
    op.create_index("ix_deposit_transactions_status", "deposit_transactions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("deposit_transactions")
    op.drop_table("monthly_invoices")
    op.drop_table("rental_contracts")
