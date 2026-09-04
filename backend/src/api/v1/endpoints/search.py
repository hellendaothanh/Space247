from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import (
    generate_search_cache_key,
    get_cached_json,
    set_cached_json,
)
from src.core.config import settings
from src.core.database import get_db_session
from src.models.property import Property
from src.schemas.property import (
    PropertyResponse,
    PropertyStatus,
    SearchResultItem,
    SemanticSearchQuery,
    SemanticSearchResponse,
)

router = APIRouter()


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic vector search for real estate listings",
)
async def semantic_search(
    query: SemanticSearchQuery,
    db: AsyncSession = Depends(get_db_session),
) -> SemanticSearchResponse:
    """
    Perform semantic similarity search over property embeddings using pgvector cosine distance.
    Validates that query vector matches configured embedding dimension (768).
    Supports multi-criteria filtering for sale/rent listings, location, and price ranges.
    """
    # Check Redis cache for identical semantic search query
    cache_key = generate_search_cache_key(query.model_dump())
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return SemanticSearchResponse.model_validate(cached_data)
        except Exception:
            pass

    # Explicit dimension mismatch check before database query execution
    if len(query.query_vector) != settings.VECTOR_DIM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Query vector dimension mismatch: expected {settings.VECTOR_DIM}, "
                f"got {len(query.query_vector)}"
            ),
        )

    # Calculate cosine distance via pgvector expression
    cosine_dist = Property.embedding.cosine_distance(query.query_vector)

    # Base query: only properties with active status and valid embedding
    stmt = (
        select(Property, cosine_dist.label("distance"))
        .where(Property.status == PropertyStatus.ACTIVE.value)
        .where(Property.embedding.is_not(None))
    )

    # Apply structured filters
    if query.listing_type:
        stmt = stmt.where(Property.listing_type == query.listing_type.value)
    if query.property_type:
        stmt = stmt.where(Property.property_type == query.property_type.value)
    if query.address:
        stmt = stmt.where(Property.address.ilike(f"%{query.address}%"))
    if query.city:
        stmt = stmt.where(Property.city.ilike(f"%{query.city}%"))
    if query.district:
        stmt = stmt.where(Property.district.ilike(f"%{query.district}%"))
    if query.num_bedrooms is not None:
        stmt = stmt.where(Property.num_bedrooms == query.num_bedrooms)
    if query.min_bedrooms is not None:
        stmt = stmt.where(Property.num_bedrooms >= query.min_bedrooms)
    if query.min_price is not None:
        stmt = stmt.where(Property.price >= query.min_price)
    if query.max_price is not None:
        stmt = stmt.where(Property.price <= query.max_price)
    if query.min_area_sqm is not None:
        stmt = stmt.where(Property.area_sqm >= query.min_area_sqm)
    if query.max_area_sqm is not None:
        stmt = stmt.where(Property.area_sqm <= query.max_area_sqm)

    # Order by cosine distance ascending (closest match first)
    stmt = stmt.order_by(cosine_dist.asc()).limit(query.limit)

    result = await db.execute(stmt)
    rows = result.all()

    search_results: list[SearchResultItem] = []
    for prop_record, dist in rows:
        # Convert cosine distance (0 to 2) to cosine similarity (1 - dist)
        dist_float = float(dist) if dist is not None else 1.0
        similarity = round(1.0 - dist_float, 4)

        if query.threshold is not None and similarity < query.threshold:
            continue

        search_results.append(
            SearchResultItem(
                property=PropertyResponse.model_validate(prop_record),
                similarity_score=similarity,
            )
        )

    response = SemanticSearchResponse(
        total=len(search_results),
        vector_dim=settings.VECTOR_DIM,
        results=search_results,
    )
    await set_cached_json(cache_key, response.model_dump())
    return response
