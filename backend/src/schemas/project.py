from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectStatus(str, Enum):
    UPCOMING = "upcoming"
    UNDER_CONSTRUCTION = "under_construction"
    HANDING_OVER = "handing_over"
    COMPLETED = "completed"


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Project commercial name")
    slug: str = Field(..., min_length=2, max_length=255, description="Unique URL-friendly slug")
    developer: str | None = Field(default=None, max_length=255, description="Real estate developer/builder name")
    description: str | None = Field(default=None, description="Detailed project description in Markdown")
    status: ProjectStatus = Field(default=ProjectStatus.UNDER_CONSTRUCTION, description="Project construction/handover status")
    total_units: int | None = Field(default=None, ge=0, description="Total planned units in project")
    launch_year: int | None = Field(default=None, ge=1900, le=2100, description="Project launch year")
    handover_year: int | None = Field(default=None, ge=1900, le=2100, description="Project estimated/actual handover year")
    address: str = Field(..., min_length=3, max_length=500, description="Project physical street address")
    ward: str | None = Field(default=None, max_length=100, description="Ward or commune")
    district: str | None = Field(default=None, max_length=100, description="District")
    city: str = Field(..., min_length=2, max_length=100, description="City or province")
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0, description="Longitude coordinate")
    images: list[str] = Field(default_factory=list, description="List of project render/actual image URLs")
    master_plan_url: str | None = Field(default=None, max_length=500, description="Master plan / floor plan image URL")
    legal_status: str | None = Field(default=None, max_length=255, description="Legal certification (e.g. Sổ hồng lâu dài, 1/500)")
    price_range_min: float | None = Field(default=None, ge=0, description="Minimum estimated unit price")
    price_range_max: float | None = Field(default=None, ge=0, description="Maximum estimated unit price")
    amenities: list[str] = Field(default_factory=list, description="List of project amenities (hồ bơi, công viên, gym, ...)")

    @model_validator(mode="after")
    def validate_price_range(self) -> "ProjectBase":
        if self.price_range_min is not None and self.price_range_max is not None:
            if self.price_range_min > self.price_range_max:
                raise ValueError("price_range_min cannot exceed price_range_max")
        return self


class ProjectCreate(ProjectBase):
    slug: str | None = Field(default=None, max_length=255, description="Optional custom slug, auto-generated if omitted")
    embedding: list[float] | None = Field(default=None, description="Optional 768-dim semantic search vector")


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    developer: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    total_units: int | None = Field(default=None, ge=0)
    launch_year: int | None = Field(default=None, ge=1900, le=2100)
    handover_year: int | None = Field(default=None, ge=1900, le=2100)
    address: str | None = Field(default=None, min_length=3, max_length=500)
    ward: str | None = None
    district: str | None = None
    city: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    images: list[str] | None = None
    master_plan_url: str | None = None
    legal_status: str | None = None
    price_range_min: float | None = Field(default=None, ge=0)
    price_range_max: float | None = Field(default=None, ge=0)
    amenities: list[str] | None = None
    embedding: list[float] | None = None


class ProjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    developer: str | None = None
    status: ProjectStatus
    city: str
    district: str | None = None
    images: list[str] = Field(default_factory=list)
    price_range_min: float | None = None
    price_range_max: float | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    active_properties_count: int = Field(default=0, description="Number of active listings in this project")
    for_sale_count: int = Field(default=0, description="Number of active units for sale")
    for_rent_count: int = Field(default=0, description="Number of active units for rent")
    average_price_per_sqm: float | None = Field(default=None, description="Average price per sqm of active listings")

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    pass


class PaginatedProjectResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int
