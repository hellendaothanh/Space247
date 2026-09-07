from datetime import datetime, timezone
import uuid
from typing import Any
from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
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

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "images" not in kwargs or kwargs["images"] is None:
            kwargs["images"] = []
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

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)
