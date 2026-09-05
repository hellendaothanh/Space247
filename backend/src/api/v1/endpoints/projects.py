import logging
import re
import unicodedata
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user
from src.core.cache import (
    generate_project_cache_key,
    generate_project_list_cache_key,
    get_cached_json,
    invalidate_project_caches,
    set_cached_json,
)
from src.core.database import get_db_session
from src.models.project import Project
from src.models.property import Property
from src.models.user import User
from src.schemas.project import (
    PaginatedProjectResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdate,
)
from src.schemas.property import ListingType, PropertyResponse, PropertyStatus, PropertyType
from src.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger("space247_backend.projects")
router = APIRouter()


def slugify(text: str) -> str:
    """
    Generate URL-friendly slug from Vietnamese or English text.
    """
    text = text.replace("đ", "d").replace("Đ", "d")
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", normalized.lower())
    return re.sub(r"[-\s]+", "-", cleaned).strip("-")


def parse_uuid_or_none(val: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError):
        return None


async def get_project_stats_map(db: AsyncSession, project_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, Any]]:
    """
    Compute aggregate listing counts and average price per sqm for the specified projects.
    """
    if not project_ids:
        return {}

    stmt = (
        select(
            Property.project_id,
            func.count(Property.id).label("active_count"),
            func.sum(case((Property.listing_type == ListingType.SALE.value, 1), else_=0)).label("sale_count"),
            func.sum(case((Property.listing_type == ListingType.RENT.value, 1), else_=0)).label("rent_count"),
            func.avg(Property.price / func.nullif(Property.area_sqm, 0)).label("avg_price_sqm"),
        )
        .where(
            Property.project_id.in_(project_ids),
            Property.status == PropertyStatus.ACTIVE.value,
        )
        .group_by(Property.project_id)
    )
    result = await db.execute(stmt)
    stats: dict[uuid.UUID, dict[str, Any]] = {}
    for row in result.all():
        pid, active_count, sale_count, rent_count, avg_price_sqm = row
        stats[pid] = {
            "active_properties_count": int(active_count or 0),
            "for_sale_count": int(sale_count or 0),
            "for_rent_count": int(rent_count or 0),
            "average_price_per_sqm": round(float(avg_price_sqm), 2) if avg_price_sqm else None,
        }
    return stats


@router.get(
    "",
    response_model=PaginatedProjectResponse,
    summary="List real estate projects with filtering and pagination",
)
async def list_projects(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    city: str | None = Query(None, description="Filter by city/province"),
    district: str | None = Query(None, description="Filter by district"),
    status: ProjectStatus | None = Query(None, description="Filter by project construction status"),
    developer: str | None = Query(None, description="Filter by developer name"),
    min_price: float | None = Query(None, ge=0, description="Filter projects with max price >= min_price"),
    max_price: float | None = Query(None, ge=0, description="Filter projects with min price <= max_price"),
    q: str | None = Query(None, description="Search keyword in name or developer"),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedProjectResponse:
    """
    Retrieve a paginated list of real estate projects with optional location, status,
    developer, price range, and keyword filters. Results are cached in Redis with a 30m TTL.
    """
    cache_params = {
        "skip": skip,
        "limit": limit,
        "city": city,
        "district": district,
        "status": status.value if status else None,
        "developer": developer,
        "min_price": min_price,
        "max_price": max_price,
        "q": q,
    }
    cache_key = generate_project_list_cache_key(cache_params)
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return PaginatedProjectResponse.model_validate(cached_data)
        except Exception:
            pass

    stmt = select(Project)
    count_stmt = select(func.count(Project.id))

    if city:
        stmt = stmt.where(Project.city.ilike(f"%{city.strip()}%"))
        count_stmt = count_stmt.where(Project.city.ilike(f"%{city.strip()}%"))
    if district:
        stmt = stmt.where(Project.district.ilike(f"%{district.strip()}%"))
        count_stmt = count_stmt.where(Project.district.ilike(f"%{district.strip()}%"))
    if status:
        stmt = stmt.where(Project.status == status.value)
        count_stmt = count_stmt.where(Project.status == status.value)
    if developer:
        stmt = stmt.where(Project.developer.ilike(f"%{developer.strip()}%"))
        count_stmt = count_stmt.where(Project.developer.ilike(f"%{developer.strip()}%"))
    if min_price is not None:
        stmt = stmt.where(or_(Project.price_range_max >= min_price, Project.price_range_max.is_(None)))
        count_stmt = count_stmt.where(or_(Project.price_range_max >= min_price, Project.price_range_max.is_(None)))
    if max_price is not None:
        stmt = stmt.where(or_(Project.price_range_min <= max_price, Project.price_range_min.is_(None)))
        count_stmt = count_stmt.where(or_(Project.price_range_min <= max_price, Project.price_range_min.is_(None)))
    if q:
        kw = f"%{q.strip()}%"
        kw_filter = or_(Project.name.ilike(kw), Project.developer.ilike(kw))
        stmt = stmt.where(kw_filter)
        count_stmt = count_stmt.where(kw_filter)

    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.order_by(Project.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    projects = list(res.scalars().all())

    # Calculate statistics
    project_ids = [p.id for p in projects]
    stats_map = await get_project_stats_map(db, project_ids)

    items: list[ProjectResponse] = []
    for p in projects:
        st = stats_map.get(p.id, {})
        p_dto = ProjectResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            developer=p.developer,
            description=p.description,
            status=ProjectStatus(p.status) if p.status else ProjectStatus.UNDER_CONSTRUCTION,
            total_units=p.total_units,
            launch_year=p.launch_year,
            handover_year=p.handover_year,
            address=p.address,
            ward=p.ward,
            district=p.district,
            city=p.city,
            latitude=p.latitude,
            longitude=p.longitude,
            images=p.images or [],
            master_plan_url=p.master_plan_url,
            legal_status=p.legal_status,
            price_range_min=float(p.price_range_min) if p.price_range_min is not None else None,
            price_range_max=float(p.price_range_max) if p.price_range_max is not None else None,
            amenities=p.amenities or [],
            created_at=p.created_at,
            updated_at=p.updated_at,
            active_properties_count=st.get("active_properties_count", 0),
            for_sale_count=st.get("for_sale_count", 0),
            for_rent_count=st.get("for_rent_count", 0),
            average_price_per_sqm=st.get("average_price_per_sqm"),
        )
        items.append(p_dto)

    page = (skip // limit) + 1
    pages = (total + limit - 1) // limit if total > 0 else 0

    response_payload = PaginatedProjectResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages,
    )

    # Cache response with 30m TTL
    await set_cached_json(cache_key, response_payload.model_dump(mode="json"), ttl=1800)
    return response_payload


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new real estate project (Requires Bearer token)",
)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> ProjectResponse:
    """
    Create a new project master record. Slug is auto-generated from name if not provided.
    Generates 768-dim semantic embedding vector for project search.
    Invalidates cached project listings.
    """
    # Auto-generate or sanitize slug
    target_slug = project_in.slug.strip() if project_in.slug else slugify(project_in.name)
    if not target_slug:
        target_slug = f"project-{uuid.uuid4().hex[:8]}"

    # Check for existing slug and append suffix if collision
    stmt = select(Project).where(Project.slug == target_slug)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        target_slug = f"{target_slug}-{uuid.uuid4().hex[:6]}"

    proj_dict = project_in.model_dump()
    proj_dict["slug"] = target_slug

    # Compute embedding if not provided
    if not proj_dict.get("embedding"):
        text_content = (
            f"Dự án {project_in.name}. "
            f"Chủ đầu tư: {project_in.developer or 'Đang cập nhật'}. "
            f"Địa chỉ: {project_in.address}, {project_in.district or ''}, {project_in.city}. "
            f"Tiện ích: {', '.join(project_in.amenities) if project_in.amenities else 'Đầy đủ'}. "
            f"{project_in.description or ''}"
        )
        try:
            proj_dict["embedding"] = embedding_service.generate_embedding(text_content, is_query=False)
        except TypeError:
            proj_dict["embedding"] = embedding_service.generate_embedding(text_content)

    # PostGIS geometry
    if project_in.latitude is not None and project_in.longitude is not None:
        proj_dict["geom"] = f"SRID=4326;POINT({project_in.longitude} {project_in.latitude})"

    if isinstance(proj_dict.get("status"), ProjectStatus):
        proj_dict["status"] = proj_dict["status"].value

    project_obj = Project(**proj_dict)
    db.add(project_obj)
    await db.flush()
    await db.refresh(project_obj)

    # Invalidate caches
    await invalidate_project_caches()

    return ProjectResponse(
        id=project_obj.id,
        name=project_obj.name,
        slug=project_obj.slug,
        developer=project_obj.developer,
        description=project_obj.description,
        status=ProjectStatus(project_obj.status) if project_obj.status else ProjectStatus.UNDER_CONSTRUCTION,
        total_units=project_obj.total_units,
        launch_year=project_obj.launch_year,
        handover_year=project_obj.handover_year,
        address=project_obj.address,
        ward=project_obj.ward,
        district=project_obj.district,
        city=project_obj.city,
        latitude=project_obj.latitude,
        longitude=project_obj.longitude,
        images=project_obj.images or [],
        master_plan_url=project_obj.master_plan_url,
        legal_status=project_obj.legal_status,
        price_range_min=float(project_obj.price_range_min) if project_obj.price_range_min is not None else None,
        price_range_max=float(project_obj.price_range_max) if project_obj.price_range_max is not None else None,
        amenities=project_obj.amenities or [],
        created_at=project_obj.created_at,
        updated_at=project_obj.updated_at,
        active_properties_count=0,
        for_sale_count=0,
        for_rent_count=0,
        average_price_per_sqm=None,
    )


@router.get(
    "/{id_or_slug}",
    response_model=ProjectDetailResponse,
    summary="Get project detail by UUID or slug",
)
async def get_project(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectDetailResponse:
    """
    Fetch comprehensive project details by ID or unique URL slug.
    Returns calculated sub-property counts and average price per sqm.
    Cached in Redis with 30m TTL.
    """
    cache_key = generate_project_cache_key(id_or_slug)
    cached_data = await get_cached_json(cache_key)
    if cached_data is not None:
        try:
            return ProjectDetailResponse.model_validate(cached_data)
        except Exception:
            pass

    parsed_uuid = parse_uuid_or_none(id_or_slug)
    if parsed_uuid:
        stmt = select(Project).where(or_(Project.id == parsed_uuid, Project.slug == id_or_slug))
    else:
        stmt = select(Project).where(Project.slug == id_or_slug)

    res = await db.execute(stmt)
    project_obj = res.scalar_one_or_none()
    if not project_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{id_or_slug}' not found",
        )

    # Compute statistics
    stats_map = await get_project_stats_map(db, [project_obj.id])
    st = stats_map.get(project_obj.id, {})

    response_dto = ProjectDetailResponse(
        id=project_obj.id,
        name=project_obj.name,
        slug=project_obj.slug,
        developer=project_obj.developer,
        description=project_obj.description,
        status=ProjectStatus(project_obj.status) if project_obj.status else ProjectStatus.UNDER_CONSTRUCTION,
        total_units=project_obj.total_units,
        launch_year=project_obj.launch_year,
        handover_year=project_obj.handover_year,
        address=project_obj.address,
        ward=project_obj.ward,
        district=project_obj.district,
        city=project_obj.city,
        latitude=project_obj.latitude,
        longitude=project_obj.longitude,
        images=project_obj.images or [],
        master_plan_url=project_obj.master_plan_url,
        legal_status=project_obj.legal_status,
        price_range_min=float(project_obj.price_range_min) if project_obj.price_range_min is not None else None,
        price_range_max=float(project_obj.price_range_max) if project_obj.price_range_max is not None else None,
        amenities=project_obj.amenities or [],
        created_at=project_obj.created_at,
        updated_at=project_obj.updated_at,
        active_properties_count=st.get("active_properties_count", 0),
        for_sale_count=st.get("for_sale_count", 0),
        for_rent_count=st.get("for_rent_count", 0),
        average_price_per_sqm=st.get("average_price_per_sqm"),
    )

    # Cache with 30m TTL
    await set_cached_json(cache_key, response_dto.model_dump(mode="json"), ttl=1800)
    return response_dto


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update real estate project (Requires Bearer token)",
)
async def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> ProjectResponse:
    """
    Update project attributes. Regenerates semantic embedding if core textual attributes change.
    Invalidates associated project caches.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project_obj = res.scalar_one_or_none()
    if not project_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    old_slug = project_obj.slug
    update_data = project_update.model_dump(exclude_unset=True)

    # Check slug conflict if slug is being updated
    if "slug" in update_data and update_data["slug"]:
        new_slug = slugify(update_data["slug"])
        if new_slug != project_obj.slug:
            slug_check_stmt = select(Project).where(Project.slug == new_slug, Project.id != project_id)
            slug_exists = (await db.execute(slug_check_stmt)).scalar_one_or_none()
            if slug_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project slug '{new_slug}' is already in use",
                )
            update_data["slug"] = new_slug

    # Recalculate geom if coordinates updated
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", project_obj.latitude)
        lon = update_data.get("longitude", project_obj.longitude)
        if lat is not None and lon is not None:
            update_data["geom"] = f"SRID=4326;POINT({lon} {lat})"

    # Handle status enum
    if "status" in update_data and isinstance(update_data["status"], ProjectStatus):
        update_data["status"] = update_data["status"].value

    # Check if textual content changed to regenerate embedding
    text_changed = any(k in update_data for k in ("name", "developer", "description", "address", "amenities"))
    if text_changed and "embedding" not in update_data:
        name = update_data.get("name", project_obj.name)
        developer = update_data.get("developer", project_obj.developer)
        description = update_data.get("description", project_obj.description)
        address = update_data.get("address", project_obj.address)
        district = update_data.get("district", project_obj.district)
        city = update_data.get("city", project_obj.city)
        amenities = update_data.get("amenities", project_obj.amenities)
        text_content = (
            f"Dự án {name}. "
            f"Chủ đầu tư: {developer or 'Đang cập nhật'}. "
            f"Địa chỉ: {address}, {district or ''}, {city}. "
            f"Tiện ích: {', '.join(amenities) if amenities else 'Đầy đủ'}. "
            f"{description or ''}"
        )
        try:
            update_data["embedding"] = embedding_service.generate_embedding(text_content, is_query=False)
        except TypeError:
            update_data["embedding"] = embedding_service.generate_embedding(text_content)

    for field, val in update_data.items():
        setattr(project_obj, field, val)

    await db.flush()
    await db.refresh(project_obj)

    # Invalidate old and new caches
    await invalidate_project_caches(project_id=project_id, slug=old_slug)
    if project_obj.slug != old_slug:
        await invalidate_project_caches(slug=project_obj.slug)

    # Re-fetch stats
    stats_map = await get_project_stats_map(db, [project_obj.id])
    st = stats_map.get(project_obj.id, {})

    return ProjectResponse(
        id=project_obj.id,
        name=project_obj.name,
        slug=project_obj.slug,
        developer=project_obj.developer,
        description=project_obj.description,
        status=ProjectStatus(project_obj.status) if project_obj.status else ProjectStatus.UNDER_CONSTRUCTION,
        total_units=project_obj.total_units,
        launch_year=project_obj.launch_year,
        handover_year=project_obj.handover_year,
        address=project_obj.address,
        ward=project_obj.ward,
        district=project_obj.district,
        city=project_obj.city,
        latitude=project_obj.latitude,
        longitude=project_obj.longitude,
        images=project_obj.images or [],
        master_plan_url=project_obj.master_plan_url,
        legal_status=project_obj.legal_status,
        price_range_min=float(project_obj.price_range_min) if project_obj.price_range_min is not None else None,
        price_range_max=float(project_obj.price_range_max) if project_obj.price_range_max is not None else None,
        amenities=project_obj.amenities or [],
        created_at=project_obj.created_at,
        updated_at=project_obj.updated_at,
        active_properties_count=st.get("active_properties_count", 0),
        for_sale_count=st.get("for_sale_count", 0),
        for_rent_count=st.get("for_rent_count", 0),
        average_price_per_sqm=st.get("average_price_per_sqm"),
    )


@router.get(
    "/{id_or_slug}/properties",
    response_model=list[PropertyResponse],
    summary="List properties belonging to a specific real estate project",
)
async def list_project_properties(
    id_or_slug: str,
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    listing_type: ListingType | None = Query(None, description="Filter by listing type"),
    property_type: PropertyType | None = Query(None, description="Filter by property type"),
    min_price: float | None = Query(None, ge=0, description="Filter minimum price"),
    max_price: float | None = Query(None, ge=0, description="Filter maximum price"),
    num_bedrooms: int | None = Query(None, ge=0, description="Filter number of bedrooms"),
    db: AsyncSession = Depends(get_db_session),
) -> list[Property]:
    """
    Retrieve active listings attached to a project with optional filters and pagination.
    """
    parsed_uuid = parse_uuid_or_none(id_or_slug)
    if parsed_uuid:
        proj_stmt = select(Project.id).where(or_(Project.id == parsed_uuid, Project.slug == id_or_slug))
    else:
        proj_stmt = select(Project.id).where(Project.slug == id_or_slug)

    proj_res = await db.execute(proj_stmt)
    project_id = proj_res.scalar_one_or_none()
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{id_or_slug}' not found",
        )

    stmt = (
        select(Property)
        .options(selectinload(Property.project))
        .where(
            Property.project_id == project_id,
            Property.status == PropertyStatus.ACTIVE.value,
        )
    )

    if listing_type:
        stmt = stmt.where(Property.listing_type == listing_type.value)
    if property_type:
        stmt = stmt.where(Property.property_type == property_type.value)
    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    if num_bedrooms is not None:
        stmt = stmt.where(Property.num_bedrooms == num_bedrooms)

    stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())
