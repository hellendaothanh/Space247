from typing import Any, Literal
from pydantic import BaseModel, Field


class ExtractedSpecs(BaseModel):
    area_sqm: float | None = Field(default=None, description="Diện tích sử dụng (m²)")
    num_bedrooms: int | None = Field(default=None, description="Số phòng ngủ")
    num_bathrooms: int | None = Field(default=None, description="Số phòng tắm/WC")
    orientation: str | None = Field(default=None, description="Hướng ban công / cửa chính")
    legal_status: str | None = Field(default=None, description="Tình trạng pháp lý (Sổ đỏ/Sổ hồng/HĐMB)")
    frontage_meters: float | None = Field(default=None, description="Mặt tiền (m)")
    suggested_price: float | None = Field(default=None, description="Giá bán gợi ý nếu có trong note")
    amenities: list[str] = Field(default_factory=list, description="Tiện ích trích xuất được")


class GenerateListingRequest(BaseModel):
    text_prompts: list[str] | str = Field(
        ...,
        description="Ghi chú nhanh hoặc danh sách các gạch đầu dòng về BĐS",
        examples=[["Căn góc 3PN D'Capitale 95m2", "Tầng trung view hồ điều hòa", "Nội thất cao cấp", "Sổ hồng chính chủ"]],
    )
    image_base64: str | None = Field(
        default=None,
        description="Ảnh chụp sổ đỏ, mặt bằng phân lô, hoặc ảnh BĐS dạng base64 (tùy chọn)",
    )
    property_type: str = Field(
        default="apartment",
        description="Loại hình: apartment, house, land, commercial, villa",
    )
    target_audience: str | None = Field(
        default=None,
        description="Đối tượng khách hàng mục tiêu: Gia đình trẻ, Chuyên gia nước ngoài, Nhà đầu tư dòng tiền",
    )


class GenerateListingResponse(BaseModel):
    title_seo: str = Field(description="Tiêu đề chuẩn SEO BĐS hấp dẫn")
    description_markdown: str = Field(description="Bài viết mô tả chi tiết định dạng Markdown")
    extracted_specs: ExtractedSpecs


class ValuationRequest(BaseModel):
    property_type: str = Field(default="apartment", description="Loại hình BĐS")
    area_sqm: float = Field(..., gt=0, description="Diện tích (m²)")
    num_bedrooms: int | None = Field(default=None, ge=0)
    num_bathrooms: int | None = Field(default=None, ge=0)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=2.5, ge=0.5, le=15.0, description="Bán kính tìm kiếm căn tương đồng")
    user_proposed_price: float | None = Field(
        default=None,
        description="Mức giá dự kiến người dùng nhập để so sánh với định giá thị trường",
    )


class ComparableProperty(BaseModel):
    id: str
    title: str
    price: float
    area_sqm: float
    price_per_sqm: float
    distance_km: float
    address: str
    property_type: str


class ValuationResponse(BaseModel):
    estimated_price_per_sqm: float = Field(description="Đơn giá khuyến nghị / m² (VNĐ)")
    estimated_total_price: float = Field(description="Tổng giá đề xuất (VNĐ)")
    price_range_low: float = Field(description="Mức giá tối thiểu gợi ý (VNĐ)")
    price_range_high: float = Field(description="Mức giá tối đa gợi ý (VNĐ)")
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Độ tin cậy của thuật toán định giá (0.0 - 1.0)",
    )
    market_trend: Literal["up", "stable", "down"] = Field(
        default="stable",
        description="Xu hướng thị trường khu vực",
    )
    radius_used_km: float = Field(description="Bán kính thực tế đã sử dụng để tìm căn tương đồng")
    comparable_properties: list[ComparableProperty] = Field(
        description="Danh sách các BĐS tham chiếu lân cận",
    )
    deviation_percentage: float | None = Field(
        default=None,
        description="Độ lệch % so với giá đề xuất của người dùng (+ là cao hơn, - là thấp hơn)",
    )
    pricing_advice: str | None = Field(
        default=None,
        description="Nhận định và lời khuyên định giá từ hệ thống",
    )
