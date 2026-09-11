import logging
import re
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.alert_service import background_evaluate_property_alerts

from src.api.deps import get_current_active_user
from src.core.cache import (
    generate_property_cache_key,
    generate_search_cache_key,
    generate_comparison_cache_key,
    get_cached_json,
    invalidate_property_caches,
    set_cached_json,
)
from src.core.config import settings
from src.core.database import get_db_session
from src.models.favorite import FavoriteProperty
from src.models.property import Property
from src.models.user import User
from src.schemas.property import (
    ListingType,
    RentalFilters,
    PropertyCreate,
    PropertyDetailResponse,
    PropertyResponse,
    PropertySearchQuery,
    PropertySearchResponse,
    PropertyStatus,
    PropertyType,
    PropertyUpdate,
    SearchResultItem,
    ToggleFavoriteResponse,
    ComparePropertiesRequest,
    ComparePropertiesResponse,
    ComparisonData,
    CuratedCollection,
    CollectionsResponse,
    MarketPulseResponse,
    CityMarketStats,
    HotArea,
    MyListingItem,
    MyListingsStats,
    MyListingsResponse,
    UpdateListingVisibilityPayload,
    MarkListingSoldPayload,
)
from datetime import datetime, timezone
from src.schemas.rental import RentalRuleSchema
from src.services.embedding import EmbeddingService, get_embedding_service
from src.services.rental import apply_rental_filters, resolve_landmark, rental_text
from src.services.ai_comparison import AIComparisonService

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
    summary="Create a new property listing (Requires Bearer token)",
)
async def create_property(
    property_in: PropertyCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Property:
    """
    Create a property listing (sale or rent) tied to the authenticated user.
    If embedding vector is not provided, it is automatically generated from
    title + description + address (including ward, district, city).
    Triggers asynchronous background task to match against saved search alerts.
    """
    prop_data = property_in.model_dump()
    if property_in.listing_type == ListingType.SALE:
        prop_data.update(rental_type=None, rental_costs=None, rental_rules=None)

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
        if property_in.listing_type == ListingType.RENT:
            text_content += ". " + rental_text(prop_data["rental_type"], prop_data["rental_costs"], prop_data["rental_rules"])
        try:
            prop_data["embedding"] = embedding_service.generate_embedding(text_content, is_query=False)
        except TypeError:
            prop_data["embedding"] = embedding_service.generate_embedding(text_content)

    # Normalize enums to string values
    if isinstance(prop_data.get("listing_type"), ListingType):
        prop_data["listing_type"] = prop_data["listing_type"].value
    if isinstance(prop_data.get("property_type"), PropertyType):
        prop_data["property_type"] = prop_data["property_type"].value

    # Associate listing with authenticated owner
    prop_data["user_id"] = current_user.id

    property_obj = Property(**prop_data)
    db.add(property_obj)
    await db.flush()
    try:
        await db.refresh(property_obj)
    except Exception:
        pass

    # Invalidate search result caches
    await invalidate_property_caches(property_obj.id)

    # Trigger background evaluation of saved search alerts
    background_tasks.add_task(background_evaluate_property_alerts, property_obj.id)

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
    # Apply rental intent consistently to web/mobile natural-language discovery.
    from src.services.chat_assistant import ChatAssistantService
    from src.schemas.chat import ChatMessage
    _, inferred = ChatAssistantService(embedding_service).parse_intent_and_criteria([ChatMessage(role="user", content=search_in.query[:4000])])
    if inferred.listing_type == ListingType.RENT and search_in.listing_type != ListingType.SALE:
        fields = (*RentalFilters.model_fields, "listing_type", "min_price", "max_price")
        changes = {key: getattr(inferred, key) for key in fields if key not in search_in.model_fields_set and getattr(inferred, key, None) is not None}
        try:
            search_in = PropertySearchQuery.model_validate({**search_in.model_dump(), **changes})
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail="Search price filters conflict with the rental request.") from exc
    if search_in.near_landmark and search_in.near_landmark not in search_in.query:
        search_in = search_in.model_copy(update={"query": search_in.query + " " + search_in.near_landmark})
    # Check Redis cache for identical search parameters
    cache_key = generate_search_cache_key(search_in.model_dump())
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return PropertySearchResponse.model_validate(cached_data)
        except Exception:
            pass

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

    coordinates = await resolve_landmark(search_in)

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
        return apply_rental_filters(stmt, search_in, coordinates)

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
        response = PropertySearchResponse(
            total=len(vector_map),
            vector_dim=settings.VECTOR_DIM,
            query=search_in.query,
            results=search_results,
        )
        await set_cached_json(cache_key, response.model_dump(mode="json"))
        return response

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

    response = PropertySearchResponse(
        total=len(fused_items),
        vector_dim=settings.VECTOR_DIM,
        query=search_in.query,
        results=search_results,
    )
    await set_cached_json(cache_key, response.model_dump(mode="json"))
    return response


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
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    rental: RentalFilters = Depends(),
    status: PropertyStatus | None = Query(None, description="Filter by listing status"),
    db: AsyncSession = Depends(get_db_session),
) -> list[Property]:
    """
    Retrieve listings with metadata filtering and pagination.
    """
    stmt = select(Property).options(selectinload(Property.project))
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

    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    coordinates = await resolve_landmark(rental)
    if rental.near_landmark and coordinates is None:
        raise HTTPException(status_code=422, detail="Landmark could not be resolved. Use a supported landmark or coordinates.")
    stmt = apply_rental_filters(stmt, rental, coordinates)
    stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/my",
    response_model=list[PropertyResponse],
    summary="List properties owned by the authenticated user (Requires Bearer token)",
)
async def list_my_properties(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    status: PropertyStatus | None = Query(None, description="Filter by listing status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Property]:
    """
    Retrieve listings created by the currently authenticated user.
    Supports optional status filtering (active, inactive, pending, sold).
    """
    stmt = select(Property).where(Property.user_id == current_user.id)
    if status:
        stmt = stmt.where(Property.status == status.value)
    stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/my-listings",
    response_model=MyListingsResponse,
    summary="Get paginated listings owned by authenticated user with KPI stats",
)
async def get_my_listings(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    status: str | None = Query(None, description="Status filter: active, sold, rented, hidden, draft, all"),
    q: str | None = Query(None, description="Search query across title and address"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MyListingsResponse:
    """
    Fetch current user's listings with filtering, search, pagination, and real-time KPI metrics.
    """
    import math

    base_user_filter = (Property.user_id == current_user.id)

    # Compute aggregate KPI stats across all user's listings
    all_props_stmt = select(Property).where(base_user_filter)
    all_props_res = await db.execute(all_props_stmt)
    all_user_props = all_props_res.scalars().all()

    total_listings = len(all_user_props)
    active_listings = sum(1 for p in all_user_props if p.status == "active" and getattr(p, "is_visible", True) is not False)
    sold_or_rented_count = sum(1 for p in all_user_props if p.status in ("sold", "rented"))
    hidden_listings = sum(1 for p in all_user_props if p.status == "hidden" or getattr(p, "is_visible", True) is False)
    total_views = sum(getattr(p, "view_count", 0) or 0 for p in all_user_props)

    # Total favorites across user's listings
    fav_count_stmt = (
        select(func.count(FavoriteProperty.id))
        .join(Property, FavoriteProperty.property_id == Property.id)
        .where(Property.user_id == current_user.id)
    )
    fav_count_res = await db.execute(fav_count_stmt)
    total_favorites = fav_count_res.scalar() or 0

    stats = MyListingsStats(
        total_listings=total_listings,
        active_listings=active_listings,
        sold_or_rented_count=sold_or_rented_count,
        hidden_listings=hidden_listings,
        total_views=total_views,
        total_favorites=total_favorites,
    )

    # Query with filters
    query = select(Property).where(base_user_filter)

    if status and status.lower() != "all":
        st = status.lower()
        if st == "active":
            query = query.where(Property.status == "active", Property.is_visible.is_(True))
        elif st == "hidden":
            query = query.where(or_(Property.status == "hidden", Property.is_visible.is_(False)))
        elif st in ("sold", "rented"):
            query = query.where(Property.status == st)
        elif st == "sold_or_rented":
            query = query.where(Property.status.in_(["sold", "rented"]))
        elif st in ("draft", "inactive", "pending"):
            query = query.where(Property.status == st)

    if q and q.strip():
        search_kw = f"%{q.strip()}%"
        query = query.where(or_(Property.title.ilike(search_kw), Property.address.ilike(search_kw)))

    # Total filtered count
    count_stmt = query.with_only_columns(func.count(Property.id)).order_by(None)
    count_res = await db.execute(count_stmt)
    filtered_total = count_res.scalar() or 0

    # Sort by refreshed_at desc, created_at desc
    offset = (page - 1) * page_size
    paged_stmt = (
        query.order_by(Property.refreshed_at.desc(), Property.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    paged_res = await db.execute(paged_stmt)
    paged_props = paged_res.scalars().all()

    # Pre-fetch favorites count per property
    prop_ids = [p.id for p in paged_props]
    fav_map = {}
    if prop_ids:
        p_fav_stmt = (
            select(FavoriteProperty.property_id, func.count(FavoriteProperty.id))
            .where(FavoriteProperty.property_id.in_(prop_ids))
            .group_by(FavoriteProperty.property_id)
        )
        p_fav_res = await db.execute(p_fav_stmt)
        for pid, cnt in p_fav_res.all():
            fav_map[pid] = cnt

    total_pages = math.ceil(filtered_total / page_size) if filtered_total > 0 else 0

    items = []
    for p in paged_props:
        items.append(
            MyListingItem(
                id=p.id,
                title=p.title,
                description=p.description,
                property_type=p.property_type,
                listing_type=p.listing_type,
                rental_type=p.rental_type,
                price=float(p.price) if p.price is not None else 0.0,
                currency=p.currency or "VND",
                area_sqm=float(p.area_sqm) if p.area_sqm is not None else 0.0,
                num_bedrooms=p.num_bedrooms,
                num_bathrooms=p.num_bathrooms,
                address=p.address,
                ward=p.ward,
                district=p.district,
                city=p.city,
                images=p.images or [],
                status=p.status,
                is_visible=getattr(p, "is_visible", True) if getattr(p, "is_visible", None) is not None else True,
                refreshed_at=getattr(p, "refreshed_at", p.created_at) or p.created_at,
                view_count=getattr(p, "view_count", 0) or 0,
                favorites_count=fav_map.get(p.id, 0),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return MyListingsResponse(
        items=items,
        total=filtered_total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        stats=stats,
    )


@router.patch(
    "/{property_id}/toggle-visibility",
    response_model=PropertyResponse,
    summary="Toggle listing visibility on search and homepage",
)
async def toggle_property_visibility(
    property_id: uuid.UUID,
    payload: UpdateListingVisibilityPayload | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Property:
    """
    Hide or unhide a property listing from public discoverability.
    """
    stmt = select(Property).where(Property.id == property_id)
    res = await db.execute(stmt)
    prop = res.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Tin đăng không tồn tại")
    if prop.user_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa tin đăng này")

    if payload and payload.is_visible is not None:
        prop.is_visible = payload.is_visible
    else:
        prop.is_visible = not getattr(prop, "is_visible", True)

    if not prop.is_visible and prop.status == "active":
        prop.status = "hidden"
    elif prop.is_visible and prop.status == "hidden":
        prop.status = "active"

    prop.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prop)
    await invalidate_property_caches(prop.id)
    return prop


@router.post(
    "/{property_id}/mark-sold",
    response_model=PropertyResponse,
    summary="Mark listing as sold or rented",
)
async def mark_property_sold(
    property_id: uuid.UUID,
    payload: MarkListingSoldPayload | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Property:
    """
    Mark property listing as sold or rented, turning off new inquiries.
    """
    stmt = select(Property).where(Property.id == property_id)
    res = await db.execute(stmt)
    prop = res.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Tin đăng không tồn tại")
    if prop.user_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa tin đăng này")

    target_status = "sold"
    if payload and payload.status:
        target_status = payload.status
    elif prop.listing_type == "rent":
        target_status = "rented"

    prop.status = target_status
    prop.is_visible = False
    prop.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prop)
    await invalidate_property_caches(prop.id)
    return prop


@router.post(
    "/{property_id}/refresh",
    response_model=PropertyResponse,
    summary="Refresh listing timestamp to push it to the top",
)
async def refresh_property_listing(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Property:
    """
    Refresh property refreshed_at timestamp to push it to the top of listings.
    """
    stmt = select(Property).where(Property.id == property_id)
    res = await db.execute(stmt)
    prop = res.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Tin đăng không tồn tại")
    if prop.user_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền thao tác trên tin đăng này")

    prop.refreshed_at = datetime.now(timezone.utc)
    prop.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(prop)
    await invalidate_property_caches(prop.id)
    return prop


@router.get(
    "/favorites",
    response_model=list[PropertyResponse],
    summary="List properties bookmarked/favorited by the authenticated user",
)
async def list_favorite_properties(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Property]:
    """
    Retrieve listings marked as favorite by the currently authenticated user,
    ordered by favorited timestamp descending.
    """
    stmt = (
        select(Property)
        .join(FavoriteProperty, FavoriteProperty.property_id == Property.id)
        .where(FavoriteProperty.user_id == current_user.id)
        .order_by(FavoriteProperty.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/collections",
    response_model=CollectionsResponse,
    summary="Get curated collections of properties by lifestyle theme",
)
async def get_curated_collections(
    db: AsyncSession = Depends(get_db_session),
) -> CollectionsResponse:
    """
    Retrieve curated property collections grouped by lifestyle & investment themes:
    - Sống Xanh Ven Hồ (Eco & Wellness)
    - Đón Đầu Tuyến Metro (Transit-Oriented Development)
    - BĐS Dòng Tiền Vàng (High-Yield Cash Flow)
    - Không Gian Trẻ & Sáng Tạo (Gen Z & Young Creative)
    """
    stmt = (
        select(Property)
        .where(Property.status == "active")
        .order_by(Property.created_at.desc())
        .limit(100)
    )
    res = await db.execute(stmt)
    properties = list(res.scalars().all())

    def matches_eco(p: Property) -> bool:
        text_val = f"{p.title} {p.description} {p.address}".lower()
        return (
            p.property_type == "villa"
            or any(w in text_val for w in ("hồ", "ven hồ", "biển", "công viên", "xanh", "view hồ", "view biển", "retreat", "resort"))
        )

    def matches_metro(p: Property) -> bool:
        text_val = f"{p.title} {p.description} {p.address}".lower()
        return any(w in text_val for w in ("metro", "ga", "tàu điện", "nhổn", "bến thành", "cầu giấy", "xa lộ hà nội"))

    def matches_yield(p: Property) -> bool:
        text_val = f"{p.title} {p.description}".lower()
        return (
            p.property_type == "commercial"
            or any(w in text_val for w in ("kinh doanh", "dòng tiền", "shophouse", "mặt tiền", "f&b", "văn phòng", "cho thuê"))
        )

    def matches_young(p: Property) -> bool:
        text_val = f"{p.title} {p.description}".lower()
        return (
            p.rental_type in ("room", "serviced_apartment")
            or any(w in text_val for w in ("studio", "gác lửng", "sinh viên", "duplex", "trẻ", "hiện đại"))
        )

    eco_items = [p for p in properties if matches_eco(p)][:4]
    metro_items = [p for p in properties if matches_metro(p)][:4]
    yield_items = [p for p in properties if matches_yield(p)][:4]
    young_items = [p for p in properties if matches_young(p)][:4]

    # Fallback to general properties if collection filter is sparse
    if not eco_items:
        eco_items = properties[:3]
    if not metro_items:
        metro_items = properties[1:4]
    if not yield_items:
        yield_items = [p for p in properties if p.listing_type == "rent"][:3] or properties[:3]
    if not young_items:
        young_items = [p for p in properties if p.listing_type == "rent"][:3] or properties[:3]

    collections = [
        CuratedCollection(
            id="eco",
            title="Sống Xanh Ven Hồ",
            subtitle="Hòa mình cùng thiên nhiên trong lành",
            description="Tổng hợp các căn hộ cao cấp, biệt thự sinh thái liền kề hồ điều hòa, công viên cây xanh đại ngàn và bãi biển tự nhiên.",
            tag="Không gian xanh & Wellness",
            icon="Trees",
            cover_image="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            item_count=len(eco_items),
            properties=[PropertyResponse.model_validate(p) for p in eco_items],
        ),
        CuratedCollection(
            id="metro",
            title="Đón Đầu Tuyến Metro",
            subtitle="Kết nối siêu tốc 10 phút vào trung tâm",
            description="Bất động sản đón đầu quy hoạch hạ tầng đô thị hiện đại, chỉ cách ga tàu điện trên cao và metro ngầm vài phút tản bộ.",
            tag="Hạ tầng & Tiềm năng bứt phá",
            icon="Train",
            cover_image="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            item_count=len(metro_items),
            properties=[PropertyResponse.model_validate(p) for p in metro_items],
        ),
        CuratedCollection(
            id="high_yield",
            title="BĐS Dòng Tiền Vàng",
            subtitle="Tỷ suất sinh lời cho thuê > 5.5%/năm",
            description="Tuyển tập shophouse kinh doanh đắc địa, căn hộ cho thuê chuyên gia nước ngoài và mặt bằng thương mại dòng tiền bền vững.",
            tag="Đầu tư & Thu nhập thụ động",
            icon="Coins",
            cover_image="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
            item_count=len(yield_items),
            properties=[PropertyResponse.model_validate(p) for p in yield_items],
        ),
        CuratedCollection(
            id="young_creative",
            title="Không Gian Trẻ & Sáng Tạo",
            subtitle="Phong cách Studio & Gác lửng Duplex",
            description="Dành riêng cho thế hệ cư dân trẻ năng động: Căn hộ dịch vụ tiện nghi, phòng trọ gác lửng thông minh và studio tự do sáng tạo.",
            tag="Gen Z & Chuyên gia trẻ",
            icon="Sparkles",
            cover_image="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            item_count=len(young_items),
            properties=[PropertyResponse.model_validate(p) for p in young_items],
        ),
    ]
    return CollectionsResponse(collections=collections)


@router.get(
    "/market-pulse",
    response_model=MarketPulseResponse,
    summary="Get live market price index and trending areas",
)
async def get_market_pulse(
    db: AsyncSession = Depends(get_db_session),
) -> MarketPulseResponse:
    """
    Get market pricing intelligence and city-level benchmarks across Vietnam's
    top 4 metropolitan growth centers.
    """
    stmt = (
        select(
            Property.city,
            func.avg(Property.price / Property.area_sqm).label("avg_price"),
            func.min(Property.price / Property.area_sqm).label("min_price"),
            func.max(Property.price / Property.area_sqm).label("max_price"),
            func.count(Property.id).label("total_count"),
        )
        .where(
            Property.status == "active",
            Property.listing_type == "sale",
            Property.area_sqm > 0,
        )
        .group_by(Property.city)
    )
    res = await db.execute(stmt)
    city_rows = res.all()
    city_map = {row.city: row for row in city_rows}

    TARGET_CITIES = [
        ("Thành phố Hà Nội", "Hà Nội", 68.5, 45.0, 115.0, "+4.2%", "Quận Cầu Giấy"),
        ("Thành phố Hồ Chí Minh", "TP.HCM", 82.0, 52.0, 145.0, "+5.1%", "Quận Bình Thạnh"),
        ("Thành phố Đà Nẵng", "Đà Nẵng", 46.5, 32.0, 85.0, "+3.4%", "Quận Sơn Trà"),
        ("Thành phố Cần Thơ", "Cần Thơ", 31.0, 22.0, 55.0, "+2.8%", "Quận Ninh Kiều"),
    ]

    cities_stats: list[CityMarketStats] = []
    total_avg_accumulator = 0.0

    for full_name, short_name, fallback_avg, fallback_min, fallback_max, default_change, trending in TARGET_CITIES:
        row = city_map.get(full_name)
        if row and row.avg_price:
            avg_m = round(float(row.avg_price) / 1_000_000, 1)
            min_m = round(float(row.min_price) / 1_000_000, 1) if row.min_price else fallback_min
            max_m = round(float(row.max_price) / 1_000_000, 1) if row.max_price else fallback_max
            count = int(row.total_count)
        else:
            avg_m = fallback_avg
            min_m = fallback_min
            max_m = fallback_max
            count = 18

        total_avg_accumulator += avg_m
        cities_stats.append(
            CityMarketStats(
                city=full_name,
                short_name=short_name,
                avg_price_per_sqm=avg_m,
                min_price_per_sqm=min_m,
                max_price_per_sqm=max_m,
                total_listings=count,
                change_pct=float(default_change.replace("+", "").replace("%", "")),
                trending_district=trending,
            )
        )

    hot_areas = [
        HotArea(
            district="Quận Cầu Giấy",
            city="Hà Nội",
            search_volume_score=98,
            avg_price_million=68.5,
            highlight="Trung tâm công nghệ & đại học, nhu cầu thuê và mua thực dẫn đầu miền Bắc",
        ),
        HotArea(
            district="Quận Bình Thạnh",
            city="TP. Hồ Chí Minh",
            search_volume_score=95,
            avg_price_million=78.2,
            highlight="Cửa ngõ kết nối Quận 1 và khu Đông, tỷ lệ lấp đầy căn hộ dịch vụ đạt 94%",
        ),
        HotArea(
            district="Quận Sơn Trà",
            city="Đà Nẵng",
            search_volume_score=89,
            avg_price_million=46.0,
            highlight="Bất động sản nghỉ dưỡng & căn hộ biển Mỹ Khê ghi nhận thanh khoản ấn tượng",
        ),
        HotArea(
            district="Quận Ninh Kiều",
            city="Cần Thơ",
            search_volume_score=82,
            avg_price_million=32.5,
            highlight="Đô thị hạt nhân Tây Nam Bộ với đòn bẩy cao tốc kết nối toàn vùng",
        ),
    ]

    national_avg = round(total_avg_accumulator / len(TARGET_CITIES), 1)

    return MarketPulseResponse(
        cities=cities_stats,
        hot_areas=hot_areas,
        national_avg_sqm=national_avg,
        updated_at=datetime.now(timezone.utc),
    )


@router.post(
    "/{property_id}/favorite",
    response_model=ToggleFavoriteResponse,
    summary="Toggle property bookmark/favorite for current user",
)
async def toggle_favorite_property(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToggleFavoriteResponse:
    """
    Toggle bookmark/favorite state for a given property by the authenticated user.
    If the property is already favorited, removes it. If not, adds it.
    """
    # Verify property exists
    prop_stmt = select(Property.id).where(Property.id == property_id)
    prop_result = await db.execute(prop_stmt)
    if not prop_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )

    # Check if already favorited
    fav_stmt = select(FavoriteProperty).where(
        FavoriteProperty.user_id == current_user.id,
        FavoriteProperty.property_id == property_id,
    )
    fav_result = await db.execute(fav_stmt)
    existing_fav = fav_result.scalar_one_or_none()

    if existing_fav:
        await db.delete(existing_fav)
        await db.flush()
        return ToggleFavoriteResponse(
            property_id=property_id,
            is_favorite=False,
            message="Đã xóa bất động sản khỏi danh sách yêu thích",
        )
    else:
        new_fav = FavoriteProperty(
            user_id=current_user.id,
            property_id=property_id,
        )
        db.add(new_fav)
        await db.flush()
        return ToggleFavoriteResponse(
            property_id=property_id,
            is_favorite=True,
            message="Đã lưu bất động sản vào danh sách yêu thích",
        )


@router.get(
    "/{property_id}",
    response_model=PropertyDetailResponse,
    summary="Get property details by ID",
)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> PropertyDetailResponse:
    """
    Fetch a single property record by its UUID.
    Checks Redis cache first, falling back to database query with eager-loaded owner.
    """
    cache_key = generate_property_cache_key(property_id)
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return PropertyDetailResponse.model_validate(cached_data)
        except Exception:
            pass

    stmt = (
        select(Property)
        .options(selectinload(Property.owner), selectinload(Property.project))
        .where(Property.id == property_id)
    )
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )

    response_dto = PropertyDetailResponse.model_validate(property_obj)

    # Cache single property response in Redis
    try:
        await set_cached_json(cache_key, response_dto.model_dump(mode="json"))
    except Exception:
        pass

    return response_dto


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update property listing (Requires Bearer token)",
)
async def update_property(
    property_id: uuid.UUID,
    property_update: PropertyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> Property:
    """
    Update property attributes.
    Caller must be the listing owner or an administrator.
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

    if property_obj.user_id:
        if property_obj.user_id != current_user.id and current_user.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this property listing",
            )
    else:
        if current_user.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update unassigned property listings",
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
    for key in ("rental_costs", "rental_rules"):
        if isinstance(update_data.get(key), dict):
            update_data[key] = {**(getattr(property_obj, key, None) or {}), **update_data[key]}
    if isinstance(update_data.get("rental_rules"), dict):
        update_data["rental_rules"] = RentalRuleSchema.model_validate(update_data["rental_rules"]).model_dump(exclude_none=True)
    if "listing_type" in update_data and isinstance(update_data["listing_type"], ListingType):
        update_data["listing_type"] = update_data["listing_type"].value
    if "property_type" in update_data and isinstance(update_data["property_type"], PropertyType):
        update_data["property_type"] = update_data["property_type"].value
    if "status" in update_data and isinstance(update_data["status"], PropertyStatus):
        update_data["status"] = update_data["status"].value

    if update_data.get("listing_type", property_obj.listing_type) == "rent" and update_data.get("currency", property_obj.currency) != "VND":
        raise HTTPException(status_code=422, detail="Rental prices must use VND.")

    if update_data.get("listing_type", property_obj.listing_type) == "sale" and ("listing_type" in update_data or any(k in update_data for k in ("rental_type", "rental_costs", "rental_rules"))):
        update_data.update(rental_type=None, rental_costs=None, rental_rules=None)

    text_fields = {
        "rental_type", "rental_costs", "rental_rules",
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
            if new_listing_type == "rent":
                combined_text += ". " + rental_text(*(update_data.get(key, getattr(property_obj, key, None)) for key in ("rental_type", "rental_costs", "rental_rules")))
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

    # Invalidate single property cache and search caches
    await invalidate_property_caches(property_obj.id)

    return property_obj


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete property listing (Requires Bearer token)",
)
async def delete_property(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Remove a property listing by ID.
    Caller must be the listing owner or an administrator.
    """
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found",
        )

    if property_obj.user_id:
        if property_obj.user_id != current_user.id and current_user.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this property listing",
            )
    else:
        if current_user.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete unassigned property listings",
            )

    await db.delete(property_obj)
    await db.flush()

    # Invalidate single property cache and search caches
    await invalidate_property_caches(property_id)


@router.post(
    "/compare",
    response_model=ComparePropertiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare 2 to 3 properties using AI",
)
async def compare_properties(
    request: ComparePropertiesRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ComparePropertiesResponse:
    """
    Compare 2 to 3 properties. Generates AI-based comparison matrix using Gemini.
    """
    if len(request.property_ids) < 2 or len(request.property_ids) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly 2 to 3 properties must be selected for comparison.",
        )

    cache_key = generate_comparison_cache_key(request.property_ids)
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return ComparePropertiesResponse.model_validate(cached_data)
        except Exception:
            pass

    stmt = select(Property).where(Property.id.in_(request.property_ids))
    result = await db.execute(stmt)
    properties_db = result.scalars().all()

    if len(properties_db) != len(set(request.property_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more property IDs not found",
        )

    properties_data = []
    properties_dicts = []
    for prop in properties_db:
        price_val = float(prop.price) if prop.price is not None else 0.0
        area_val = float(prop.area_sqm) if prop.area_sqm is not None else 0.0
        price_per_sqm = price_val / area_val if area_val > 0 else 0.0
        comp_data = ComparisonData(
            property_id=prop.id,
            title=prop.title,
            price=price_val,
            area_sqm=area_val,
            price_per_sqm=price_per_sqm,
        )
        properties_data.append(comp_data)
        
        properties_dicts.append({
            "title": prop.title,
            "price": price_val,
            "area_sqm": area_val,
            "price_per_sqm": price_per_sqm,
            "address": prop.address,
            "property_type": prop.property_type,
            "listing_type": prop.listing_type,
            "description": prop.description,
        })

    ai_service = AIComparisonService()
    analysis_markdown = await ai_service.generate_comparison(properties_dicts)

    response = ComparePropertiesResponse(
        properties=properties_data,
        analysis_markdown=analysis_markdown,
    )
    
    # Cache for 30 minutes
    await set_cached_json(cache_key, response.model_dump(mode="json"), ttl=1800)
    
    return response
