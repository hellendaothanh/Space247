from datetime import datetime
from enum import Enum
from typing import Any, Literal
import uuid
from pydantic import BaseModel, ConfigDict, Field


class RentalPropertyModel(str, Enum):
    BOARDING_HOUSE = "boarding_house"
    SERVICED_APARTMENT = "serviced_apartment"
    HOMESTAY = "homestay"


class RentalUnitStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"


class RentalUnitFurnishing(str, Enum):
    EMPTY = "empty"
    BASIC = "basic"
    FULL = "full"


class RentalInquiryType(str, Enum):
    VIEW_APPOINTMENT = "view_appointment"
    BOOKING_REQUEST = "booking_request"


class RentalInquiryStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COMPLETED = "completed"


# Unit schemas
class RentalUnitBase(BaseModel):
    unit_number: str = Field(..., min_length=1, max_length=50, description="Mã hoặc số phòng (VD: P.201)")
    floor: int | None = Field(default=None, description="Tầng")
    area_sqm: float = Field(..., gt=0, description="Diện tích (m²)")
    price: float = Field(..., gt=0, description="Giá thuê (VND/tháng hoặc VND/đêm đối với Homestay)")
    deposit: float | None = Field(default=None, ge=0, description="Tiền đặt cọc")
    status: RentalUnitStatus = Field(default=RentalUnitStatus.AVAILABLE)
    furnishing: RentalUnitFurnishing = Field(default=RentalUnitFurnishing.BASIC)
    has_mezzanine: bool = Field(default=False, description="Có gác lửng / gác xép")
    has_private_bathroom: bool = Field(default=True, description="Vệ sinh khép kín")
    max_occupants: int | None = Field(default=2, ge=1, description="Số người ở tối đa")
    images: list[str] = Field(default_factory=list, description="Hình ảnh riêng của phòng")


class RentalUnitCreate(RentalUnitBase):
    pass


class RentalUnitUpdate(BaseModel):
    unit_number: str | None = Field(default=None, min_length=1, max_length=50)
    floor: int | None = None
    area_sqm: float | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)
    deposit: float | None = Field(default=None, ge=0)
    status: RentalUnitStatus | None = None
    furnishing: RentalUnitFurnishing | None = None
    has_mezzanine: bool | None = None
    has_private_bathroom: bool | None = None
    max_occupants: int | None = Field(default=None, ge=1)
    images: list[str] | None = None


class RentalUnitStatusUpdate(BaseModel):
    status: RentalUnitStatus = Field(..., description="Trạng thái phòng mới")


class RentalUnitResponse(RentalUnitBase):
    id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Property (Building/Complex) schemas
class RentalPropertyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Tên tòa nhà / khu trọ / homestay")
    description: str = Field(default="", description="Mô tả thông tin chung")
    property_model: RentalPropertyModel = Field(default=RentalPropertyModel.BOARDING_HOUSE)
    address: str = Field(..., min_length=3, max_length=500, description="Địa chỉ")
    ward: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    shared_costs: dict[str, Any] = Field(
        default_factory=dict,
        description="Biểu phí chung: {electricity_per_kwh, electricity_billing, water_cost, water_unit, wifi_fee, parking_fee_monthly, cleaning_fee}",
    )
    shared_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Nội quy chung: {curfew, curfew_time, allow_pets, fingerprint_lock, elevator, live_with_owner, washing_machine}",
    )
    images: list[str] = Field(default_factory=list, description="Hình ảnh tổng thể khu nhà")
    is_active: bool = Field(default=True)


class RentalPropertyCreate(RentalPropertyBase):
    initial_units: list[RentalUnitCreate] = Field(
        default_factory=list,
        description="Danh sách các phòng/căn hộ khởi tạo ban đầu",
    )


class RentalPropertyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    property_model: RentalPropertyModel | None = None
    address: str | None = Field(default=None, min_length=3, max_length=500)
    ward: str | None = None
    district: str | None = None
    city: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    shared_costs: dict[str, Any] | None = None
    shared_rules: dict[str, Any] | None = None
    images: list[str] | None = None
    is_active: bool | None = None


class RentalPropertyHostSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RentalPropertyResponse(RentalPropertyBase):
    id: uuid.UUID
    host_id: uuid.UUID
    host: RentalPropertyHostSummary | None = None
    total_units_count: int = 0
    available_units_count: int = 0
    min_price: float | None = None
    max_price: float | None = None
    units: list[RentalUnitResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Inquiries & Booking
class RentalInquiryCreate(BaseModel):
    inquiry_type: RentalInquiryType = Field(default=RentalInquiryType.VIEW_APPOINTMENT)
    scheduled_time: datetime | None = Field(default=None, description="Thời gian hẹn xem phòng hoặc ngày nhận phòng")
    tenant_name: str | None = Field(default=None, max_length=255)
    tenant_phone: str | None = Field(default=None, max_length=50)
    message: str | None = Field(default=None, description="Lời nhắn gửi chủ nhà")


class RentalInquiryStatusUpdate(BaseModel):
    status: RentalInquiryStatus = Field(..., description="Cập nhật trạng thái yêu cầu")


class RentalInquiryResponse(BaseModel):
    id: uuid.UUID
    unit_id: uuid.UUID
    tenant_id: uuid.UUID
    host_id: uuid.UUID
    inquiry_type: str
    scheduled_time: datetime | None = None
    tenant_name: str | None = None
    tenant_phone: str | None = None
    message: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    unit: RentalUnitResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# Host Dashboard KPIs
class LandlordDashboardStats(BaseModel):
    total_properties: int = 0
    total_units: int = 0
    available_units: int = 0
    occupied_units: int = 0
    reserved_units: int = 0
    occupancy_rate: float = 0.0
    estimated_monthly_revenue: float = 0.0
    pending_inquiries_count: int = 0


# Filter Query for Tenant Search
class RentalSearchFilter(BaseModel):
    query: str | None = None
    property_model: RentalPropertyModel | None = None
    city: str | None = None
    district: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    furnishing: RentalUnitFurnishing | None = None
    has_mezzanine: bool | None = None
    has_private_bathroom: bool | None = None
    allow_pets: bool | None = None
    fingerprint_lock: bool | None = None
    curfew: bool | None = None
    only_available: bool = True
