from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ListingType(str, Enum):
    SALE = "sale"
    RENT = "rent"


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    LAND = "land"
    COMMERCIAL = "commercial"


class PropertyStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    RENTED = "rented"
    INACTIVE = "inactive"


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Listing title")
    description: str = Field(..., min_length=10, description="Detailed property description")
    property_type: PropertyType = Field(..., description="Type of property")
    listing_type: ListingType = Field(..., description="Sale or rent")
    price: float = Field(..., gt=0, description="Price in currency units")
    currency: str = Field(default="VND", max_length=10, description="Currency code")
    area_sqm: float = Field(..., gt=0, description="Area in square meters")
    num_bedrooms: int | None = Field(default=None, ge=0, description="Number of bedrooms")
    num_bathrooms: int | None = Field(default=None, ge=0, description="Number of bathrooms")
    address: str = Field(..., min_length=3, max_length=500, description="Street address")
    ward: str | None = Field(default=None, max_length=100, description="Ward or commune")
    district: str | None = Field(default=None, max_length=100, description="District")
    city: str = Field(..., min_length=2, max_length=100, description="City or province")
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0, description="Latitude")
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0, description="Longitude")


class PropertyCreate(PropertyBase):
    embedding: list[float] | None = Field(
        default=None,
        description="Optional 768-dimensional vector embedding of property description",
    )


class PropertyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    property_type: PropertyType | None = None
    listing_type: ListingType | None = None
    price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, max_length=10)
    area_sqm: float | None = Field(default=None, gt=0)
    num_bedrooms: int | None = Field(default=None, ge=0)
    num_bathrooms: int | None = Field(default=None, ge=0)
    address: str | None = Field(default=None, min_length=3, max_length=500)
    ward: str | None = None
    district: str | None = None
    city: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    status: PropertyStatus | None = None
    embedding: list[float] | None = None


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    status: PropertyStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchQuery(BaseModel):
    query_vector: list[float] = Field(..., description="768-dimensional embedding vector")
    listing_type: ListingType | None = Field(default=None, description="Filter by listing type (sale/rent)")
    property_type: PropertyType | None = Field(default=None, description="Filter by property type")
    address: str | None = Field(default=None, description="Filter by address substring")
    city: str | None = Field(default=None, description="Filter by city/province")
    district: str | None = Field(default=None, description="Filter by district")
    num_bedrooms: int | None = Field(
        default=None, ge=0, description="Filter by exact number of bedrooms"
    )
    min_bedrooms: int | None = Field(
        default=None, ge=0, description="Filter by minimum number of bedrooms"
    )
    min_price: float | None = Field(default=None, ge=0, description="Minimum price filter")
    max_price: float | None = Field(default=None, ge=0, description="Maximum price filter")
    min_area_sqm: float | None = Field(default=None, ge=0, description="Minimum area filter")
    max_area_sqm: float | None = Field(default=None, ge=0, description="Maximum area filter")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    threshold: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")

    @model_validator(mode="after")
    def validate_ranges(self) -> "SemanticSearchQuery":
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot exceed max_price")
        if self.min_area_sqm is not None and self.max_area_sqm is not None:
            if self.min_area_sqm > self.max_area_sqm:
                raise ValueError("min_area_sqm cannot exceed max_area_sqm")
        return self


class SearchResultItem(BaseModel):
    property: PropertyResponse
    similarity_score: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score (0 to 1)")
    rrf_score: float | None = Field(default=None, description="Reciprocal Rank Fusion hybrid score")
    vector_rank: int | None = Field(default=None, description="Rank in vector search results (1-indexed)")
    fts_rank: int | None = Field(default=None, description="Rank in full-text search results (1-indexed)")


class SemanticSearchResponse(BaseModel):
    total: int
    vector_dim: int = 768
    results: list[SearchResultItem]


class PropertySearchQuery(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural language search query in Vietnamese or English",
    )
    listing_type: ListingType | None = Field(
        default=None, description="Filter by listing type (sale/rent)"
    )
    property_type: PropertyType | None = Field(
        default=None, description="Filter by property type"
    )
    address: str | None = Field(
        default=None, description="Filter by address substring"
    )
    city: str | None = Field(default=None, description="Filter by city/province")
    district: str | None = Field(default=None, description="Filter by district")
    num_bedrooms: int | None = Field(
        default=None, ge=0, description="Filter by exact number of bedrooms"
    )
    min_bedrooms: int | None = Field(
        default=None, ge=0, description="Filter by minimum number of bedrooms"
    )
    min_price: float | None = Field(
        default=None, ge=0, description="Minimum price filter"
    )
    max_price: float | None = Field(
        default=None, ge=0, description="Maximum price filter"
    )
    min_area_sqm: float | None = Field(
        default=None, ge=0, description="Minimum area filter"
    )
    max_area_sqm: float | None = Field(
        default=None, ge=0, description="Maximum area filter"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results to return"
    )
    threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Minimum cosine similarity threshold"
    )
    enable_hybrid: bool = Field(
        default=True,
        description="Whether to run hybrid search (Reciprocal Rank Fusion of Vector + FTS)",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Reciprocal Rank Fusion smoothing constant k (default 60)",
    )


    @model_validator(mode="after")
    def validate_ranges(self) -> "PropertySearchQuery":
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot exceed max_price")
        if self.min_area_sqm is not None and self.max_area_sqm is not None:
            if self.min_area_sqm > self.max_area_sqm:
                raise ValueError("min_area_sqm cannot exceed max_area_sqm")
        return self


class PropertySearchResponse(BaseModel):
    total: int
    vector_dim: int = 768
    query: str | None = None
    results: list[SearchResultItem]
