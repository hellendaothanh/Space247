from datetime import date, datetime, time, timezone
import uuid
from typing import Any
from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class RentalProperty(Base):
    """
    Building / Complex level entity (Khu trọ / Tòa nhà căn hộ dịch vụ / Homestay).
    Managed by a host (User). Contains shared rules, fees, address, and units.
    """
    __tablename__ = "rental_properties"
    __table_args__ = (
        Index("ix_rental_properties_host_id", "host_id"),
        Index("ix_rental_properties_property_model", "property_model"),
        Index("ix_rental_properties_city_district", "city", "district"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    property_model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="boarding_house",
        index=True,
    )  # "boarding_house" | "serviced_apartment" | "homestay"

    # Location & Spatial
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Shared Costs & Rules (JSONB)
    # shared_costs: { electricity_per_kwh, electricity_billing, water_cost, water_unit, wifi_fee, parking_fee_monthly, cleaning_fee }
    shared_costs: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    # shared_rules: { curfew, curfew_time, allow_pets, fingerprint_lock, elevator, live_with_owner, washing_machine }
    shared_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    images: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    host = relationship("User", backref="rental_properties")
    units = relationship("RentalUnit", back_populates="property", cascade="all, delete-orphan", lazy="selectin")
    contracts = relationship("RentalContract", back_populates="property", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "images" not in kwargs or kwargs["images"] is None:
            kwargs["images"] = []
        if "shared_costs" not in kwargs or kwargs["shared_costs"] is None:
            kwargs["shared_costs"] = {}
        if "shared_rules" not in kwargs or kwargs["shared_rules"] is None:
            kwargs["shared_rules"] = {}
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)


class RentalUnit(Base):
    """
    Individual Room / Apartment Unit inside a RentalProperty.
    """
    __tablename__ = "rental_units"
    __table_args__ = (
        Index("ix_rental_units_property_id", "property_id"),
        Index("ix_rental_units_status", "status"),
        Index("ix_rental_units_price", "price"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)  # Mã / Số phòng (ví dụ: "P.201")
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, index=True)  # VND/tháng (hoặc VND/đêm nếu homestay)
    deposit: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)  # Tiền đặt cọc
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="available",
        index=True,
    )  # "available" | "occupied" | "reserved"
    furnishing: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="basic",
    )  # "empty" (trống) | "basic" (cơ bản) | "full" (đầy đủ nội thất)
    has_mezzanine: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Có gác lửng/xép
    has_private_bathroom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # Vệ sinh khép kín
    max_occupants: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2)

    images: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    property = relationship("RentalProperty", back_populates="units")
    inquiries = relationship("RentalInquiry", back_populates="unit", cascade="all, delete-orphan")
    contracts = relationship("RentalContract", back_populates="unit", cascade="all, delete-orphan")
    invoices = relationship("MonthlyInvoice", back_populates="unit", cascade="all, delete-orphan")
    deposit_transactions = relationship("DepositTransaction", back_populates="unit", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "images" not in kwargs or kwargs["images"] is None:
            kwargs["images"] = []
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "available"
        if "furnishing" not in kwargs or kwargs["furnishing"] is None:
            kwargs["furnishing"] = "basic"
        if "has_mezzanine" not in kwargs or kwargs["has_mezzanine"] is None:
            kwargs["has_mezzanine"] = False
        if "has_private_bathroom" not in kwargs or kwargs["has_private_bathroom"] is None:
            kwargs["has_private_bathroom"] = True
        if "max_occupants" not in kwargs or kwargs["max_occupants"] is None:
            kwargs["max_occupants"] = 2
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)


class RentalInquiry(Base):
    """
    Viewing appointments and booking inquiries between tenants and hosts.
    """
    __tablename__ = "rental_inquiries"
    __table_args__ = (
        Index("ix_rental_inquiries_unit_id", "unit_id"),
        Index("ix_rental_inquiries_tenant_id", "tenant_id"),
        Index("ix_rental_inquiries_host_id", "host_id"),
        Index("ix_rental_inquiries_status", "status"),
        Index("ix_rental_inquiries_host_appointment", "host_id", "appointment_date", "start_time"),
        UniqueConstraint("host_id", "appointment_date", "start_time", name="uq_rental_inquiries_host_appointment_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inquiry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="view_appointment",
    )  # "view_appointment" | "booking_request"
    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    appointment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    calendar_event_uid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    google_calendar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ical_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    tenant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )  # "pending" | "confirmed" | "rejected" | "completed"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    unit = relationship("RentalUnit", back_populates="inquiries")
    tenant = relationship("User", foreign_keys=[tenant_id], backref="tenant_inquiries")
    host = relationship("User", foreign_keys=[host_id], backref="host_inquiries")
    deposit_transactions = relationship("DepositTransaction", back_populates="inquiry")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)


class HostViewingSchedule(Base):
    __tablename__ = "host_availability_schedules"
    __table_args__ = (
        UniqueConstraint("host_id", "day_of_week", "start_time", name="uq_host_availability_schedule_window"),
        Index("ix_host_availability_schedules_host_day", "host_id", "day_of_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class HostViewingBlockedDate(Base):
    __tablename__ = "host_blocked_dates"
    __table_args__ = (
        UniqueConstraint("host_id", "date", name="uq_host_blocked_date"),
        Index("ix_host_blocked_dates_host_date", "host_id", "date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RentalContract(Base):
    """
    Lease contract between host and tenant for a rental unit.
    """
    __tablename__ = "rental_contracts"
    __table_args__ = (
        Index("ix_rental_contracts_unit_id", "unit_id"),
        Index("ix_rental_contracts_property_id", "property_id"),
        Index("ix_rental_contracts_host_id", "host_id"),
        Index("ix_rental_contracts_tenant_id", "tenant_id"),
        Index("ix_rental_contracts_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rental_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    payment_cycle_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    electricity_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=3500)
    water_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=20000)
    water_billing_type: Mapped[str] = mapped_column(String(20), nullable=False, default="per_m3")  # "per_m3" | "per_person"
    service_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True,
    )  # "active" | "expired" | "terminated"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    unit = relationship("RentalUnit", back_populates="contracts")
    property = relationship("RentalProperty", back_populates="contracts")
    host = relationship("User", foreign_keys=[host_id], backref="host_contracts")
    tenant = relationship("User", foreign_keys=[tenant_id], backref="tenant_contracts")
    invoices = relationship("MonthlyInvoice", back_populates="contract", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "deposit_amount" not in kwargs or kwargs["deposit_amount"] is None:
            kwargs["deposit_amount"] = 0.0
        if "payment_cycle_months" not in kwargs or kwargs["payment_cycle_months"] is None:
            kwargs["payment_cycle_months"] = 1
        if "electricity_rate" not in kwargs or kwargs["electricity_rate"] is None:
            kwargs["electricity_rate"] = 3500.0
        if "water_rate" not in kwargs or kwargs["water_rate"] is None:
            kwargs["water_rate"] = 20000.0
        if "water_billing_type" not in kwargs or kwargs["water_billing_type"] is None:
            kwargs["water_billing_type"] = "per_m3"
        if "service_fee" not in kwargs or kwargs["service_fee"] is None:
            kwargs["service_fee"] = 0.0
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "active"
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)


class MonthlyInvoice(Base):
    """
    Monthly utility and rental invoice generated by landlord.
    """
    __tablename__ = "monthly_invoices"
    __table_args__ = (
        Index("ix_monthly_invoices_contract_id", "contract_id"),
        Index("ix_monthly_invoices_unit_id", "unit_id"),
        Index("ix_monthly_invoices_host_id", "host_id"),
        Index("ix_monthly_invoices_tenant_id", "tenant_id"),
        Index("ix_monthly_invoices_billing_month", "billing_month"),
        Index("ix_monthly_invoices_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    billing_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    room_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    electricity_previous_index: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    electricity_current_index: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    electricity_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=3500)
    electricity_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    water_previous_index: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    water_current_index: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    water_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=20000)
    water_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    service_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    other_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )  # "pending" | "paid" | "overdue" | "cancelled"
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    contract = relationship("RentalContract", back_populates="invoices")
    unit = relationship("RentalUnit", back_populates="invoices")
    host = relationship("User", foreign_keys=[host_id], backref="host_invoices")
    tenant = relationship("User", foreign_keys=[tenant_id], backref="tenant_invoices")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "pending"
        if "electricity_previous_index" not in kwargs:
            kwargs["electricity_previous_index"] = 0.0
        if "electricity_current_index" not in kwargs:
            kwargs["electricity_current_index"] = 0.0
        if "electricity_rate" not in kwargs:
            kwargs["electricity_rate"] = 3500.0
        if "electricity_amount" not in kwargs:
            kwargs["electricity_amount"] = 0.0
        if "water_previous_index" not in kwargs:
            kwargs["water_previous_index"] = 0.0
        if "water_current_index" not in kwargs:
            kwargs["water_current_index"] = 0.0
        if "water_rate" not in kwargs:
            kwargs["water_rate"] = 20000.0
        if "water_amount" not in kwargs:
            kwargs["water_amount"] = 0.0
        if "service_amount" not in kwargs:
            kwargs["service_amount"] = 0.0
        if "other_amount" not in kwargs:
            kwargs["other_amount"] = 0.0
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)


class DepositTransaction(Base):
    """
    Room reservation deposit transaction paid via VietQR Napas 247 or MoMo.
    """
    __tablename__ = "deposit_transactions"
    __table_args__ = (
        Index("ix_deposit_transactions_unit_id", "unit_id"),
        Index("ix_deposit_transactions_tenant_id", "tenant_id"),
        Index("ix_deposit_transactions_host_id", "host_id"),
        Index("ix_deposit_transactions_reference_code", "reference_code", unique=True),
        Index("ix_deposit_transactions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_inquiries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    reference_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="vietqr")
    vietqr_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )  # "pending" | "success" | "expired" | "failed"
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    unit = relationship("RentalUnit", back_populates="deposit_transactions")
    inquiry = relationship("RentalInquiry", back_populates="deposit_transactions")
    tenant = relationship("User", foreign_keys=[tenant_id], backref="tenant_deposits")
    host = relationship("User", foreign_keys=[host_id], backref="host_deposits")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "payment_method" not in kwargs or kwargs["payment_method"] is None:
            kwargs["payment_method"] = "vietqr"
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "pending"
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)

