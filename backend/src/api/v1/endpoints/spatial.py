import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_GeomFromGeoJSON, ST_SetSRID, ST_Within
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.models.property import Property
from src.schemas.property import PropertyResponse, PropertyStatus
from src.schemas.spatial import (
    AmenityCategory,
    AmenityHeatmapResponse,
    IsochronePropertyItem,
    IsochroneSearchRequest,
    IsochroneSearchResponse,
)
from src.services.spatial_service import (
    SpatialService,
    get_spatial_service,
    haversine_distance_km,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/isochrone-search",
    response_model=IsochroneSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search properties within commuting travel time polygon (Isochrone)",
)
async def isochrone_search(
    request: IsochroneSearchRequest,
    db: AsyncSession = Depends(get_db_session),
    spatial_service: SpatialService = Depends(get_spatial_service),
) -> IsochroneSearchResponse:
    """
    Search active properties located within an Isochrone polygon based on transport mode and travel time:
    1. Geocodes target landmark or parses coordinate string.
    2. Generates isochrone GeoJSON polygon.
    3. Executes PostGIS spatial query with ST_Within.
    4. Computes estimated travel times and distances to the target landmark.
    """
    # 1. Geocode landmark
    loc_info = await spatial_service.geocode_landmark(request.target_landmark)
    if not loc_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể định vị địa danh '{request.target_landmark}'. Vui lòng thử mốc khác hoặc nhập tọa độ 'vĩ_độ,kinh_độ'.",
        )

    # 2. Compute Isochrone Polygon
    geojson_data = await spatial_service.compute_isochrone_polygon(
        center_lat=loc_info.latitude,
        center_lng=loc_info.longitude,
        duration_minutes=request.max_duration_minutes,
        transport_mode=request.transport_mode,
    )

    feature = geojson_data["features"][0]
    polygon_geometry = feature["geometry"]
    polygon_geojson_str = json.dumps(polygon_geometry)

    # 3. Query properties within polygon using PostGIS ST_Within
    # Fallback to ST_MakePoint if geom is null but latitude/longitude are present
    geom_expr = func.coalesce(
        Property.geom,
        ST_SetSRID(func.ST_MakePoint(Property.longitude, Property.latitude), 4326),
    )

    stmt = (
        select(Property)
        .where(Property.status == PropertyStatus.ACTIVE.value)
        .where(Property.latitude.is_not(None))
        .where(Property.longitude.is_not(None))
        .where(ST_Within(geom_expr, ST_SetSRID(ST_GeomFromGeoJSON(polygon_geojson_str), 4326)))
    )

    # Apply structured filters
    if request.property_type:
        val = request.property_type.value if hasattr(request.property_type, "value") else str(request.property_type)
        stmt = stmt.where(Property.property_type == val)
    if request.listing_type:
        val = request.listing_type.value if hasattr(request.listing_type, "value") else str(request.listing_type)
        stmt = stmt.where(Property.listing_type == val)
    if request.min_price is not None:
        stmt = stmt.where(Property.price >= request.min_price)
    if request.max_price is not None:
        stmt = stmt.where(Property.price <= request.max_price)
    if request.min_bedrooms is not None:
        stmt = stmt.where(Property.num_bedrooms >= request.min_bedrooms)

    stmt = stmt.limit(request.limit)

    result = await db.execute(stmt)
    properties_db = result.scalars().all()

    # 4. Calculate estimated travel time for each property
    speed_kmh = {
        "walking": 4.5,
        "transit": 20.0,
        "motorcycle": 28.0,
        "car": 32.0,
    }.get(request.transport_mode, 28.0)
    detour_factor = 0.75

    property_items: list[IsochronePropertyItem] = []
    for prop in properties_db:
        if prop.latitude is not None and prop.longitude is not None:
            dist_km = haversine_distance_km(
                loc_info.latitude, loc_info.longitude, prop.latitude, prop.longitude
            )
            # Estimated travel time factoring urban detour
            est_minutes = round((dist_km / speed_kmh) * 60.0 / detour_factor, 1)
            # Cap at max_duration for UI realism
            est_minutes = min(float(request.max_duration_minutes), max(2.0, est_minutes))

            prop_resp = PropertyResponse.model_validate(prop)
            property_items.append(
                IsochronePropertyItem(
                    property=prop_resp,
                    estimated_travel_minutes=est_minutes,
                    distance_km=round(dist_km, 2),
                )
            )

    # Sort by closest estimated travel time
    property_items.sort(key=lambda x: x.estimated_travel_minutes)

    return IsochroneSearchResponse(
        target_location=loc_info,
        max_duration_minutes=request.max_duration_minutes,
        transport_mode=request.transport_mode,
        isochrone_geojson=geojson_data,
        total=len(property_items),
        properties=property_items,
    )


@router.get(
    "/amenities/heatmap",
    response_model=AmenityHeatmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get amenity points and density coordinates for heatmap visualization",
)
async def get_amenity_heatmap(
    category: str = Query("all", description="Amenity category: school, hospital, metro, supermarket, or all"),
    min_lat: float | None = Query(None, description="Bounding box min latitude"),
    min_lng: float | None = Query(None, description="Bounding box min longitude"),
    max_lat: float | None = Query(None, description="Bounding box max latitude"),
    max_lng: float | None = Query(None, description="Bounding box max longitude"),
    center_lat: float | None = Query(None, description="Center coordinate latitude"),
    center_lng: float | None = Query(None, description="Center coordinate longitude"),
    radius_km: float = Query(6.0, ge=0.5, le=50.0, description="Search radius in kilometers"),
    spatial_service: SpatialService = Depends(get_spatial_service),
) -> AmenityHeatmapResponse:
    """
    Returns nearby amenities (schools, hospitals, transit, supermarkets) with intensity weights
    formatted for Leaflet Heatmap rendering.
    """
    bounds = None
    if (
        min_lat is not None
        and min_lng is not None
        and max_lat is not None
        and max_lng is not None
    ):
        bounds = [min_lat, min_lng, max_lat, max_lng]

    return await spatial_service.get_amenity_heatmap(
        category=category,
        bounds=bounds,
        center_lat=center_lat,
        center_lng=center_lng,
        radius_km=radius_km,
    )
