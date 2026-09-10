from enum import Enum
from pydantic import BaseModel, Field, field_validator

from src.schemas.property import ListingType, PropertyResponse, PropertyType


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: str = Field(..., description="Sender role: user, assistant, or system")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower not in {r.value for r in ChatRole}:
            raise ValueError(f"Invalid role '{v}'. Allowed roles: user, assistant, system")
        return v_lower


from src.schemas.rental import RentalFilters


class ExtractedCriteria(RentalFilters):
    listing_type: ListingType | None = Field(default=None, description="Sale or rent")
    property_type: PropertyType | None = Field(default=None, description="Apartment, house, villa, etc.")
    city: str | None = Field(default=None, description="Extracted city")
    district: str | None = Field(default=None, description="Extracted district")
    min_price: float | None = Field(default=None, description="Minimum price filter in VND")
    max_price: float | None = Field(default=None, description="Maximum price filter in VND")
    min_bedrooms: int | None = Field(default=None, description="Minimum bedrooms")
    amenities: list[str] = Field(default_factory=list, description="Extracted amenity keywords")
    project_name: str | None = Field(default=None, description="Extracted project or developer name")
    raw_query: str = Field(default="", description="Search text extracted from user question")


class ChatAssistantRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Conversation history ending with the latest user query",
    )
    limit: int = Field(default=4, ge=1, le=10, description="Maximum number of recommended properties")


class LivingCostItem(BaseModel):
    category: str = Field(..., description="Tên khoản mục (tiền phòng, điện, nước, dịch vụ, v.v.)")
    unit_price: float = Field(..., ge=0, description="Đơn giá")
    quantity: float = Field(..., ge=0, description="Số lượng tiêu thụ / số người")
    unit_label: str = Field(..., description="Đơn vị tính (kWh, m³, người, tháng, xe)")
    subtotal: float = Field(..., ge=0, description="Thành tiền = đơn giá * số lượng")
    note: str | None = Field(default=None, description="Ghi chú chi tiết")


class LivingCostBreakdown(BaseModel):
    room_price: float = Field(..., ge=0, description="Giá thuê phòng gốc")
    occupants: int = Field(default=1, ge=1, description="Số người ở")
    electricity_kwh: float = Field(default=150.0, ge=0, description="Số điện ước tính tiêu thụ")
    water_usage: float = Field(default=2.0, ge=0, description="Số khối nước hoặc người")
    water_unit: str = Field(default="m3", description="'m3' hoặc 'person'")
    items: list[LivingCostItem] = Field(default_factory=list, description="Chi tiết các khoản phí")
    total_monthly_cost: float = Field(..., ge=0, description="Tổng chi phí sinh hoạt hàng tháng")
    cost_per_person: float = Field(..., ge=0, description="Chi phí trung bình mỗi người")
    summary: str = Field(default="", description="Bảng tổng hợp hoặc giải thích thân thiện")


class ChatAssistantResponse(BaseModel):
    message: str = Field(..., description="Assistant response text in Vietnamese")
    properties: list[PropertyResponse] = Field(
        default_factory=list,
        description="List of recommended properties matching extracted criteria",
    )
    criteria: ExtractedCriteria | None = Field(
        default=None,
        description="Extracted search parameters",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested quick follow-up queries for the user",
    )
    living_cost: LivingCostBreakdown | None = Field(
        default=None,
        description="Bảng phân tích chi phí sinh hoạt hàng tháng ước tính",
    )
