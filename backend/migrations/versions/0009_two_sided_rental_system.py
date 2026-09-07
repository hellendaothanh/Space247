"""Two-sided rental system: rental_properties, rental_units, and rental_inquiries

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-07 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. rental_properties table
    op.create_table(
        "rental_properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("property_model", sa.String(50), nullable=False, server_default="boarding_house"),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("ward", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geom", Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True),
        sa.Column("shared_costs", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("shared_rules", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("images", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rental_properties_host_id", "rental_properties", ["host_id"], unique=False)
    op.create_index("ix_rental_properties_property_model", "rental_properties", ["property_model"], unique=False)
    op.create_index("ix_rental_properties_city_district", "rental_properties", ["city", "district"], unique=False)

    # 2. rental_units table
    op.create_table(
        "rental_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_number", sa.String(50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("area_sqm", sa.Float(), nullable=False),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("deposit", sa.Numeric(15, 2), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="available"),
        sa.Column("furnishing", sa.String(50), nullable=False, server_default="basic"),
        sa.Column("has_mezzanine", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_private_bathroom", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_occupants", sa.Integer(), nullable=True, server_default="2"),
        sa.Column("images", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rental_units_property_id", "rental_units", ["property_id"], unique=False)
    op.create_index("ix_rental_units_status", "rental_units", ["status"], unique=False)
    op.create_index("ix_rental_units_price", "rental_units", ["price"], unique=False)

    # 3. rental_inquiries table
    op.create_table(
        "rental_inquiries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rental_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inquiry_type", sa.String(50), nullable=False, server_default="view_appointment"),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_name", sa.String(255), nullable=True),
        sa.Column("tenant_phone", sa.String(50), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rental_inquiries_unit_id", "rental_inquiries", ["unit_id"], unique=False)
    op.create_index("ix_rental_inquiries_tenant_id", "rental_inquiries", ["tenant_id"], unique=False)
    op.create_index("ix_rental_inquiries_host_id", "rental_inquiries", ["host_id"], unique=False)
    op.create_index("ix_rental_inquiries_status", "rental_inquiries", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("rental_inquiries")
    op.drop_table("rental_units")
    op.drop_table("rental_properties")
