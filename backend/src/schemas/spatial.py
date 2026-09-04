from typing import Any, Literal
from pydantic import BaseModel, Field
from src.schemas.property import ListingType, PropertyResponse, PropertyType


TransportMode = Literal["motorcycle", "car", "transit", "walking"]
AmenityCategory = Literal["school", "hospital", "metro", "supermarket", "all"]


class TargetLocationInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    formatted_address: str | None = None


class IsochroneSearchRequest(BaseModel):
    target_landmark: str = Field(
        ...,
        description="Name of landmark (e.g. 'Keangnam', 'Chợ Bến Thành') or coordinates 'latitude,longitude'",
        examples=["Keangnam", "Chợ Bến Thành", "21.0169,105.7839"],
    )
    max_duration_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Commuting travel time limit in minutes (5 to 60)",
    )
    transport_mode: TransportMode = Field(
        default="motorcycle",
        description="Mode of transportation",
    )
    property_type: PropertyType | None = None
    listing_type: ListingType | None = None
    min_price: float | None = None
    max_price: float | None = None
    min_bedrooms: int | None = None
    limit: int = Field(default=30, ge=1, le=100)


class IsochronePropertyItem(BaseModel):
    property: PropertyResponse
    estimated_travel_minutes: float
    distance_km: float


class IsochroneSearchResponse(BaseModel):
    target_location: TargetLocationInfo
    max_duration_minutes: int
    transport_mode: str
    isochrone_geojson: dict[str, Any]
    total: int
    properties: list[IsochronePropertyItem]


class AmenityPOI(BaseModel):
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    weight: float = 1.0
    distance_meters: float | None = None
    address: str | None = None


class AmenityHeatmapResponse(BaseModel):
    category: str
    total_points: int
    heatmap_points: list[list[float]] = Field(
        description="Array of [lat, lng, weight] coordinates for Leaflet.heat"
    )
    pois: list[AmenityPOI]
