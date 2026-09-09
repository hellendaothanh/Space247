"""Add smart viewing schedules and calendar metadata.

Revision ID: 0014
Revises: 0013
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "host_availability_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_host_availability_schedule_day"),
        sa.CheckConstraint("start_time < end_time", name="ck_host_viewing_schedule_time_range"),
        sa.CheckConstraint("slot_duration_minutes > 0 AND slot_duration_minutes <= 480", name="ck_host_viewing_schedule_duration"),
        sa.UniqueConstraint("host_id", "day_of_week", "start_time", name="uq_host_availability_schedule_window"),
    )
    op.create_index("ix_host_availability_schedules_host_day", "host_availability_schedules", ["host_id", "day_of_week"])
    op.create_table(
        "host_blocked_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("host_id", "date", name="uq_host_blocked_date"),
    )
    op.create_index("ix_host_blocked_dates_host_date", "host_blocked_dates", ["host_id", "date"])
    op.add_column("rental_inquiries", sa.Column("appointment_date", sa.Date(), nullable=True))
    op.add_column("rental_inquiries", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("rental_inquiries", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column("rental_inquiries", sa.Column("calendar_event_uid", sa.String(length=100), nullable=True))
    op.add_column("rental_inquiries", sa.Column("google_calendar_url", sa.Text(), nullable=True))
    op.add_column("rental_inquiries", sa.Column("ical_data", sa.Text(), nullable=True))
    op.add_column("rental_inquiries", sa.Column("reminder_status", sa.String(length=20), nullable=False, server_default="pending"))
    op.create_index("ix_rental_inquiries_host_appointment", "rental_inquiries", ["host_id", "appointment_date", "start_time"])
    op.create_unique_constraint("uq_rental_inquiries_host_appointment_start", "rental_inquiries", ["host_id", "appointment_date", "start_time"])


def downgrade() -> None:
    op.drop_constraint("uq_rental_inquiries_host_appointment_start", "rental_inquiries", type_="unique")
    op.drop_index("ix_rental_inquiries_host_appointment", table_name="rental_inquiries")
    for column in ("reminder_status", "ical_data", "google_calendar_url", "calendar_event_uid", "end_time", "start_time", "appointment_date"):
        op.drop_column("rental_inquiries", column)
    op.drop_index("ix_host_blocked_dates_host_date", table_name="host_blocked_dates")
    op.drop_table("host_blocked_dates")
    op.drop_index("ix_host_availability_schedules_host_day", table_name="host_availability_schedules")
    op.drop_table("host_availability_schedules")
