import logging
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db_session
from src.models.property import Property
from src.schemas.property import (
    ListingType,
    PropertyCreate,
    PropertyResponse,
    PropertySearchQuery,
    PropertySearchResponse,
    PropertyStatus,
    PropertyType,
    PropertyUpdate,
    SearchResultItem,
)
from src.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger("space247_backend.properties")
router = APIRouter()


def _sanitize_tsquery(query_text: str) -> str:
    """
    Sanitize natural language string into a PostgreSQL tsquery matching format.
    Splits into alphanumeric/accented tokens and joins with '|' (OR) for broad matching,
    or returns empty string if no valid tokens.
    """
    clean_tokens = [w for w in re.split(r"[\s,.;:!?()\'\"\\/+\-_]+", query_text) if len(w) >= 2]
    if not clean_tokens:
        return ""
    return " | ".join(clean_tokens)


@router.post(
    "",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property listing",
)
async def create_property(
    property_in: PropertyCreate,
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Property:
    """
    Create a property listing (sale or rent).
    If embedding vector is not provided, it is automatically generated from
    title + description + address (including ward, district, city).
    """
    prop_data = property_in.model_dump()

    if property_in.embedding is not None:
        if len(property_in.embedding) != settings.VECTOR_DIM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Property embedding dimension mismatch: expected {settings.VECTOR_DIM}, "
                    f"got {len(property_in.embedding)}"
                ),
            )
    else:
        # Automatically generate 768-dimensional embedding from property content
        text_content = embedding_service.build_property_text(
            title=property_in.title,
            description=property_in.description,
            address=property_in.address,
            ward=property_in.ward,
            district=property_in.district,
            city=property_in.city,
            property_type=property_in.property_type.value if hasattr(property_in.property_type, "value") else str(property_in.property_type),
            listing_type=property_in.listing_type.value if hasattr(property_in.listing_type, "value") else str(property_in.listing_type),
            num_bedrooms=property_in.num_bedrooms,
        )
        try:
            prop_data["embedding"] = embedding_service.generate_embedding(text_content, is_query=False)
        except TypeError:
            prop_data["embedding"] = embedding_service.generate_embedding(text_content)

    # Normalize enums to string values
    if isinstance(prop_data.get("listing_type"), ListingType):
        prop_data["listing_type"] = prop_data["listing_type"].value
    if isinstance(prop_data.get("property_type"), PropertyType):
        prop_data["property_type"] = prop_data["property_type"].value

    property_obj = Property(**prop_data)
    db.add(property_obj)
    await db.flush()
    try:
        await db.refresh(property_obj)
    except Exception:
        pass
    return property_obj


@router.post(
    "/search",
    response_model=PropertySearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Natural language semantic search for properties",
)
async def search_properties(
    search_in: PropertySearchQuery,
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> PropertySearchResponse:
    """
    Search property listings using natural language query.
    Converts query text into 768-dimensional embedding and matches via pgvector cosine distance (<=>),
    combined with filters for listing type (bán/cho thuê), price range, bedrooms, and location.
    When enable_hybrid=True, executes both vector search and Full-Text Search (FTS), fusing
    rankings using Reciprocal Rank Fusion (RRF) with smoothing constant k (default 60).
    """
    # Generate 768-dimensional embedding from the natural language query
    try:
        query_vector = embedding_service.generate_embedding(search_in.query, is_query=True)
    except TypeError:
        query_vector = embedding_service.generate_embedding(search_in.query)

    if len(query_vector) != settings.VECTOR_DIM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Generated query vector dimension mismatch: expected {settings.VECTOR_DIM}, "
                f"got {len(query_vector)}"
            ),
        )

    # Common filter builder for structured metadata
    def apply_filters(base_stmt):
        stmt = base_stmt
        if search_in.listing_type:
            stmt = stmt.where(Property.listing_type == search_in.listing_type.value)
        if search_in.property_type:
            stmt = stmt.where(Property.property_type == search_in.property_type.value)
        if search_in.address:
            stmt = stmt.where(Property.address.ilike(f"%{search_in.address.strip()}%"))
        if search_in.city:
            stmt = stmt.where(Property.city.ilike(f"%{search_in.city.strip()}%"))
        if search_in.district:
            stmt = stmt.where(Property.district.ilike(f"%{search_in.district.strip()}%"))
        if search_in.num_bedrooms is not None:
            stmt = stmt.where(Property.num_bedrooms == search_in.num_bedrooms)
        elif search_in.min_bedrooms is not None:
            stmt = stmt.where(Property.num_bedrooms >= search_in.min_bedrooms)
        if search_in.min_price is not None:
            stmt = stmt.where(Property.price >= search_in.min_price)
        if search_in.max_price is not None:
            stmt = stmt.where(Property.price <= search_in.max_price)
        if search_in.min_area_sqm is not None:
            stmt = stmt.where(Property.area_sqm >= search_in.min_area_sqm)
        if search_in.max_area_sqm is not None:
            stmt = stmt.where(Property.area_sqm <= search_in.max_area_sqm)
        return stmt

    # 1. Vector Search Query
    cosine_dist = Property.embedding.cosine_distance(query_vector)
    vector_stmt = (
        select(Property, cosine_dist.label("distance"))
        .where(Property.status == PropertyStatus.ACTIVE.value)
        .where(Property.embedding.is_not(None))
    )
    vector_stmt = apply_filters(vector_stmt)
    candidate_limit = max(search_in.limit * 3, 50) if search_in.enable_hybrid else search_in.limit
    vector_stmt = vector_stmt.order_by(cosine_dist.asc()).limit(candidate_limit)

    vector_res = await db.execute(vector_stmt)
    vector_rows = vector_res.all()

    # Map candidate properties: id -> (Property, similarity, vector_rank)
    vector_map: dict[uuid.UUID, tuple[Property, float, int]] = {}
    for idx, (prop_rec, dist) in enumerate(vector_rows, start=1):
        dist_float = float(dist) if dist is not None else 1.0
        similarity = round(1.0 - dist_float, 4)
        if search_in.threshold is not None and similarity < search_in.threshold:
            continue
        vector_map[prop_rec.id] = (prop_rec, similarity, idx)

    # If hybrid search is disabled or not enough candidates, return vector results directly
    if not search_in.enable_hybrid:
        search_results: list[SearchResultItem] = []
        for prop_rec, sim, rank in list(vector_map.values())[: search_in.limit]:
            search_results.append(
                SearchResultItem(
                    property=PropertyResponse.model_validate(prop_rec),
                    similarity_score=sim,
                    rrf_score=None,
                    vector_rank=rank,
                    fts_rank=None,
                )
            )
        return PropertySearchResponse(
            total=len(vector_map),
            vector_dim=settings.VECTOR_DIM,
            query=search_in.query,
            results=search_results,
        )

    # 2. Full-Text Search (FTS) Query using PostgreSQL to_tsvector & to_tsquery
    # Concatenate title, address, ward, district, city, description
    search_tsquery_str = _sanitize_tsquery(search_in.query)
    fts_map: dict[uuid.UUID, tuple[Property, float, int]] = {}

    if search_tsquery_str:
        ts_vector_expr = func.to_tsvector(
            "simple",
            func.coalesce(Property.title, "")
            + " "
            + func.coalesce(Property.address, "")
            + " "
            + func.coalesce(Property.ward, "")
            + " "
            + func.coalesce(Property.district, "")
            + " "
            + func.coalesce(Property.city, "")
            + " "
            + func.coalesce(Property.description, ""),
        )
        ts_query_expr = func.to_tsquery("simple", search_tsquery_str)
        fts_rank_expr = func.ts_rank_cd(ts_vector_expr, ts_query_expr)

        fts_stmt = (
            select(Property, fts_rank_expr.label("fts_rank_score"))
            .where(Property.status == PropertyStatus.ACTIVE.value)
            .where(ts_vector_expr.op("@@")(ts_query_expr))
        )
        fts_stmt = apply_filters(fts_stmt)
        fts_stmt = fts_stmt.order_by(fts_rank_expr.desc()).limit(candidate_limit)

        try:
            fts_res = await db.execute(fts_stmt)
            fts_rows = fts_res.all()
            for idx, (prop_rec, fts_score) in enumerate(fts_rows, start=1):
                fts_map[prop_rec.id] = (prop_rec, float(fts_score or 0.0), idx)
        except Exception as fts_exc:
            # Log diagnostic info when FTS cannot execute (e.g. SQLite test runs without to_tsvector)
            logger.debug("FTS search execution skipped or failed: %s", fts_exc)
            fts_map = {}

    # 3. Reciprocal Rank Fusion (RRF)
    # RRF Score(d) = sum_{m in {vector, fts}} 1 / (k + rank_m(d))
    k = search_in.rrf_k
    all_prop_ids = sorted(list(set(vector_map.keys()).union(fts_map.keys())), key=lambda uid: str(uid))
    fused_items: list[tuple[float, Property, float, int | None, int | None]] = []

    for pid in all_prop_ids:
        prop_obj: Property | None = None
        sim_score: float = 0.0
        v_rank: int | None = None
        f_rank: int | None = None
        rrf_score: float = 0.0

        if pid in vector_map:
            prop_obj, sim_score, v_rank = vector_map[pid]
            rrf_score += 1.0 / (k + v_rank)

        if pid in fts_map:
            p_fts, _, f_rank = fts_map[pid]
            if prop_obj is None:
                prop_obj = p_fts
            rrf_score += 1.0 / (k + f_rank)

        if prop_obj is not None:
            # If threshold is specified, only return items meeting the minimum similarity score
            if search_in.threshold is not None and sim_score < search_in.threshold:
                continue
            fused_items.append((rrf_score, prop_obj, sim_score, v_rank, f_rank))

    # Sort descending by RRF score, with deterministic tie-break on similarity_score and property ID
    fused_items.sort(key=lambda x: (x[0], x[2], str(x[1].id)), reverse=True)

    search_results: list[SearchResultItem] = []
    for rrf_val, prop_rec, sim, v_rk, f_rk in fused_items[: search_in.limit]:
        search_results.append(
            SearchResultItem(
                property=PropertyResponse.model_validate(prop_rec),
                similarity_score=sim,
                rrf_score=round(rrf_val, 6),
                vector_rank=v_rk,
                fts_rank=f_rk,
            )
        )

    return PropertySearchResponse(
        total=len(fused_items),
        vector_dim=settings.VECTOR_DIM,
        query=search_in.query,
        results=search_results,
    )


@router.get(
    "",
    response_model=list[PropertyResponse],
    summary="List properties with optional filtering and pagination",
)
async def list_properties(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    listing_type: ListingType | None = Query(None, description="Filter by listing type"),
    property_type: PropertyType | None = Query(None, description="Filter by property type"),
    city: str | None = Query(None, description="Filter by city"),
    status: PropertyStatus | None = Query(None, description="Filter by listing status"),
    db: AsyncSession = Depends(get_db_session),
) -> list[Property]:
    """
    Retrieve listings with metadata filtering and pagination.
    """
    stmt = select(Property)
    if listing_type:
        stmt = stmt.where(Property.listing_type == listing_type.value)
    if property_type:
        stmt = stmt.where(Property.property_type == property_type.value)
    if city:
        stmt = stmt.where(Property.city.ilike(f"%{city}%"))
    if status:
        stmt = stmt.where(Property.status == status.value)
    else:
        stmt = stmt.where(Property.status == PropertyStatus.ACTIVE.value)

    stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property details by ID",
)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Property:
    """
    Fetch a single property record by its UUID.
    """
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )
    return property_obj


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update property listing",
)
async def update_property(
    property_id: uuid.UUID,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Property:
    """
    Update property attributes.
    If embedding is not explicitly provided, re-generates embedding whenever
    title, description, or address fields are modified.
    """
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )

    if property_update.embedding is not None:
        if len(property_update.embedding) != settings.VECTOR_DIM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Property embedding dimension mismatch: expected {settings.VECTOR_DIM}, "
                    f"got {len(property_update.embedding)}"
                ),
            )

    update_data = property_update.model_dump(exclude_unset=True)
    if "listing_type" in update_data and isinstance(update_data["listing_type"], ListingType):
        update_data["listing_type"] = update_data["listing_type"].value
    if "property_type" in update_data and isinstance(update_data["property_type"], PropertyType):
        update_data["property_type"] = update_data["property_type"].value
    if "status" in update_data and isinstance(update_data["status"], PropertyStatus):
        update_data["status"] = update_data["status"].value

    text_fields = {
        "title",
        "description",
        "address",
        "ward",
        "district",
        "city",
        "property_type",
        "listing_type",
        "num_bedrooms",
    }
    has_text_change = any(f in update_data for f in text_fields)

    # Auto-generate embedding if not explicitly given and text fields changed or embedding missing
    if "embedding" not in update_data:
        if has_text_change or property_obj.embedding is None:
            new_title = update_data.get("title", property_obj.title)
            new_description = update_data.get("description", property_obj.description)
            new_address = update_data.get("address", property_obj.address)
            new_ward = update_data.get("ward", property_obj.ward)
            new_district = update_data.get("district", property_obj.district)
            new_city = update_data.get("city", property_obj.city)
            new_property_type = update_data.get("property_type", property_obj.property_type)
            new_listing_type = update_data.get("listing_type", property_obj.listing_type)
            new_num_bedrooms = update_data.get("num_bedrooms", property_obj.num_bedrooms)

            combined_text = embedding_service.build_property_text(
                title=new_title,
                description=new_description,
                address=new_address,
                ward=new_ward,
                district=new_district,
                city=new_city,
                property_type=new_property_type,
                listing_type=new_listing_type,
                num_bedrooms=new_num_bedrooms,
            )
            try:
                update_data["embedding"] = embedding_service.generate_embedding(combined_text, is_query=False)
            except TypeError:
                update_data["embedding"] = embedding_service.generate_embedding(combined_text)

    for field, value in update_data.items():
        setattr(property_obj, field, value)

    await db.flush()
    try:
        await db.refresh(property_obj)
    except Exception:
        pass
    return property_obj


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete property listing",
)
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Remove a property listing by ID.
    """
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )

    await db.delete(property_obj)
