import logging
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user, get_optional_current_user
from src.core.database import get_db_session
from src.models.rental_property import RentalInquiry, RentalProperty, RentalUnit
from src.models.user import User
from src.schemas.rental_management import (
    RentalInquiryCreate,
    RentalInquiryResponse,
    RentalPropertyModel,
    RentalPropertyResponse,
    RentalSearchFilter,
    RentalUnitFurnishing,
    RentalUnitResponse,
    RentalUnitStatus,
)

logger = logging.getLogger("space247_backend.rentals")
router = APIRouter()


def _populate_property_response(prop: RentalProperty) -> RentalPropertyResponse:
    units_list = prop.units or []
    total_units = len(units_list)
    available_units = [u for u in units_list if u.status == RentalUnitStatus.AVAILABLE.value]
    
    prices = [float(u.price) for u in units_list if u.price is not None]
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None

    host_summary = None
    if prop.host:
        host_summary = {
            "id": prop.host.id,
            "full_name": prop.host.full_name,
            "email": prop.host.email,
            "phone": prop.host.phone,
            "avatar_url": prop.host.avatar_url,
        }

    return RentalPropertyResponse(
        id=prop.id,
        host_id=prop.host_id,
        host=host_summary,
        name=prop.name,
        description=prop.description,
        property_model=prop.property_model,
        address=prop.address,
        ward=prop.ward,
        district=prop.district,
        city=prop.city,
        latitude=prop.latitude,
        longitude=prop.longitude,
        shared_costs=prop.shared_costs or {},
        shared_rules=prop.shared_rules or {},
        images=prop.images or [],
        is_active=prop.is_active,
        total_units_count=total_units,
        available_units_count=len(available_units),
        min_price=min_price,
        max_price=max_price,
        units=[RentalUnitResponse.model_validate(u) for u in units_list],
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


@router.get(
    "",
    response_model=list[RentalPropertyResponse],
    summary="Explore rental buildings and rooms (Tenant discovery)",
)
async def list_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Tìm kiếm tên khu trọ hoặc địa chỉ"),
    property_model: RentalPropertyModel | None = Query(None),
    city: str | None = Query(None),
    district: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    furnishing: RentalUnitFurnishing | None = Query(None),
    has_mezzanine: bool | None = Query(None),
    has_private_bathroom: bool | None = Query(None),
    allow_pets: bool | None = Query(None),
    fingerprint_lock: bool | None = Query(None),
    curfew: bool | None = Query(None),
    only_available: bool = Query(False, description="Chỉ hiện khu có phòng trống"),
    db: AsyncSession = Depends(get_db_session),
) -> list[RentalPropertyResponse]:
    """
    Search and filter rental properties with clean filters.
    """
    stmt = (
        select(RentalProperty)
        .where(RentalProperty.is_active == True)
        .options(selectinload(RentalProperty.units), selectinload(RentalProperty.host))
    )

    if property_model:
        stmt = stmt.where(RentalProperty.property_model == property_model.value)
    if city:
        stmt = stmt.where(RentalProperty.city.ilike(f"%{city.strip()}%"))
    if district:
        stmt = stmt.where(RentalProperty.district.ilike(f"%{district.strip()}%"))
    if query:
        term = f"%{query.strip()}%"
        stmt = stmt.where(or_(RentalProperty.name.ilike(term), RentalProperty.address.ilike(term)))

    # JSON rules filters
    if allow_pets is not None:
        stmt = stmt.where(RentalProperty.shared_rules["allow_pets"].as_boolean() == allow_pets)
    if fingerprint_lock is not None:
        stmt = stmt.where(RentalProperty.shared_rules["fingerprint_lock"].as_boolean() == fingerprint_lock)
    if curfew is not None:
        stmt = stmt.where(RentalProperty.shared_rules["curfew"].as_boolean() == curfew)

    # Unit-level subquery constraints if unit filters applied
    unit_predicates = []
    if only_available:
        unit_predicates.append(RentalUnit.status == RentalUnitStatus.AVAILABLE.value)
    if min_price is not None:
        unit_predicates.append(RentalUnit.price >= min_price)
    if max_price is not None:
        unit_predicates.append(RentalUnit.price <= max_price)
    if furnishing is not None:
        unit_predicates.append(RentalUnit.furnishing == furnishing.value)
    if has_mezzanine is not None:
        unit_predicates.append(RentalUnit.has_mezzanine == has_mezzanine)
    if has_private_bathroom is not None:
        unit_predicates.append(RentalUnit.has_private_bathroom == has_private_bathroom)

    if unit_predicates:
        matching_prop_ids = (
            select(RentalUnit.property_id)
            .where(*unit_predicates)
            .distinct()
        )
        stmt = stmt.where(RentalProperty.id.in_(matching_prop_ids))

    stmt = stmt.order_by(RentalProperty.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    properties = result.scalars().all()

    return [_populate_property_response(p) for p in properties]


@router.get(
    "/my-inquiries",
    response_model=list[RentalInquiryResponse],
    summary="Get current tenant's rental inquiries history",
)
async def get_my_inquiries(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RentalInquiry]:
    stmt = (
        select(RentalInquiry)
        .where(RentalInquiry.tenant_id == current_user.id)
        .options(selectinload(RentalInquiry.unit))
        .order_by(RentalInquiry.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/{property_id}",
    response_model=RentalPropertyResponse,
    summary="Get rental property details with units",
)
async def get_rental_property_details(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> RentalPropertyResponse:
    stmt = (
        select(RentalProperty)
        .where(RentalProperty.id == property_id)
        .options(selectinload(RentalProperty.units), selectinload(RentalProperty.host))
    )
    result = await db.execute(stmt)
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy khu trọ/căn hộ dịch vụ")

    return _populate_property_response(prop)


@router.post(
    "/units/{unit_id}/inquire",
    response_model=RentalInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit viewing appointment or booking request for a room",
)
async def inquire_unit(
    unit_id: uuid.UUID,
    inquiry_in: RentalInquiryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalInquiry:
    # 1. Fetch unit and parent property
    stmt = select(RentalUnit).where(RentalUnit.id == unit_id).options(selectinload(RentalUnit.property))
    result = await db.execute(stmt)
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng tương ứng")

    if unit.status == RentalUnitStatus.OCCUPIED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng này hiện đã có người thuê, vui lòng chọn phòng khác",
        )

    # 2. Create inquiry record
    inquiry = RentalInquiry(
        unit_id=unit.id,
        tenant_id=current_user.id,
        host_id=unit.property.host_id,
        inquiry_type=inquiry_in.inquiry_type.value,
        scheduled_time=inquiry_in.scheduled_time,
        tenant_name=inquiry_in.tenant_name or current_user.full_name,
        tenant_phone=inquiry_in.tenant_phone or current_user.phone,
        message=inquiry_in.message,
        status="pending",
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry
