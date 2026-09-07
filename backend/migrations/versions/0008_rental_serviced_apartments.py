"""Optional rental metadata, preserving existing sale/rent listings."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("properties", "listing_type", server_default="sale")
    op.add_column("properties", sa.Column("rental_type", sa.String(50), nullable=True))
    op.add_column("properties", sa.Column("rental_costs", postgresql.JSONB(), nullable=True))
    op.add_column("properties", sa.Column("rental_rules", postgresql.JSONB(), nullable=True))
    op.create_index("ix_properties_rental_price", "properties", ["listing_type", "rental_type", "price"])


def downgrade():
    op.drop_index("ix_properties_rental_price", table_name="properties")
    for name in ("rental_rules", "rental_costs", "rental_type"):
        op.drop_column("properties", name)
    op.alter_column("properties", "listing_type", server_default=None)
