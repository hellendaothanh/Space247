import logging
import uuid
from geoalchemy2 import WKTElement
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_host_user
from src.core.database import get_db_session
from src.models.rental_property import RentalInquiry, RentalProperty, RentalUnit
from src.models.user import User
from src.schemas.rental_management import (
    LandlordDashboardStats,
    RentalInquiryResponse,
    RentalInquiryStatusUpdate,
    RentalPropertyCreate,
    RentalPropertyResponse,
    RentalPropertyUpdate,
    RentalUnitCreate,
    RentalUnitResponse,
    RentalUnitStatus,
    RentalUnitStatusUpdate,
    RentalUnitUpdate,
)

logger = logging.getLogger("space247_backend.host")
router = APIRouter()


def _populate_host_property_response(prop: RentalProperty) -> RentalPropertyResponse:
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
    "/stats",
    response_model=LandlordDashboardStats,
    summary="Landlord dashboard statistics",
)
async def get_landlord_stats(
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> LandlordDashboardStats:
    # 1. Properties count
    prop_count_stmt = select(func.count(RentalProperty.id)).where(RentalProperty.host_id == current_host.id)
    total_props = (await db.execute(prop_count_stmt)).scalar() or 0

    # 2. Units breakdown
    units_stmt = (
        select(RentalUnit)
        .join(RentalProperty, RentalProperty.id == RentalUnit.property_id)
        .where(RentalProperty.host_id == current_host.id)
    )
    units_res = await db.execute(units_stmt)
    all_units = list(units_res.scalars().all())

    total_units = len(all_units)
    available_units = sum(1 for u in all_units if u.status == RentalUnitStatus.AVAILABLE.value)
    occupied_units = sum(1 for u in all_units if u.status == RentalUnitStatus.OCCUPIED.value)
    reserved_units = sum(1 for u in all_units if u.status == RentalUnitStatus.RESERVED.value)

    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0.0

    # Estimated monthly revenue (occupied units)
    est_revenue = sum(float(u.price) for u in all_units if u.status == RentalUnitStatus.OCCUPIED.value)

    # 3. Pending inquiries count
    inq_stmt = (
        select(func.count(RentalInquiry.id))
        .where(RentalInquiry.host_id == current_host.id, RentalInquiry.status == "pending")
    )
    pending_inquiries = (await db.execute(inq_stmt)).scalar() or 0

    return LandlordDashboardStats(
        total_properties=total_props,
        total_units=total_units,
        available_units=available_units,
        occupied_units=occupied_units,
        reserved_units=reserved_units,
        occupancy_rate=occupancy_rate,
        estimated_monthly_revenue=est_revenue,
        pending_inquiries_count=pending_inquiries,
    )


@router.get(
    "/properties",
    response_model=list[RentalPropertyResponse],
    summary="List rental properties managed by current host",
)
async def list_host_properties(
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RentalPropertyResponse]:
    stmt = (
        select(RentalProperty)
        .where(RentalProperty.host_id == current_host.id)
        .options(selectinload(RentalProperty.units), selectinload(RentalProperty.host))
        .order_by(RentalProperty.created_at.desc())
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()
    return [_populate_host_property_response(p) for p in properties]


@router.post(
    "/properties",
    response_model=RentalPropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rental property / building (Multi-step wizard)",
)
async def create_rental_property(
    prop_in: RentalPropertyCreate,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalPropertyResponse:
    geom = None
    if prop_in.latitude is not None and prop_in.longitude is not None:
        geom = WKTElement(f"POINT({prop_in.longitude} {prop_in.latitude})", srid=4326)

    property_obj = RentalProperty(
        host_id=current_host.id,
        name=prop_in.name,
        description=prop_in.description,
        property_model=prop_in.property_model.value,
        address=prop_in.address,
        ward=prop_in.ward,
        district=prop_in.district,
        city=prop_in.city,
        latitude=prop_in.latitude,
        longitude=prop_in.longitude,
        geom=geom,
        shared_costs=prop_in.shared_costs,
        shared_rules=prop_in.shared_rules,
        images=prop_in.images,
        is_active=prop_in.is_active,
    )
    db.add(property_obj)
    await db.flush()

    # Create initial units if provided in wizard
    for u_in in prop_in.initial_units:
        unit = RentalUnit(
            property_id=property_obj.id,
            unit_number=u_in.unit_number,
            floor=u_in.floor,
            area_sqm=u_in.area_sqm,
            price=u_in.price,
            deposit=u_in.deposit,
            status=u_in.status.value,
            furnishing=u_in.furnishing.value,
            has_mezzanine=u_in.has_mezzanine,
            has_private_bathroom=u_in.has_private_bathroom,
            max_occupants=u_in.max_occupants,
            images=u_in.images,
        )
        db.add(unit)

    await db.commit()

    # Re-fetch with units
    stmt = (
        select(RentalProperty)
        .where(RentalProperty.id == property_obj.id)
        .options(selectinload(RentalProperty.units), selectinload(RentalProperty.host))
    )
    res = await db.execute(stmt)
    full_prop = res.scalar_one()
    return _populate_host_property_response(full_prop)


@router.post(
    "/properties/{property_id}/units",
    response_model=RentalUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new room/unit to host's rental property",
)
async def add_unit_to_property(
    property_id: uuid.UUID,
    unit_in: RentalUnitCreate,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalUnit:
    prop_stmt = select(RentalProperty).where(RentalProperty.id == property_id)
    prop_res = await db.execute(prop_stmt)
    prop = prop_res.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy khu trọ")

    if prop.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền quản lý khu trọ này")

    unit = RentalUnit(
        property_id=property_id,
        unit_number=unit_in.unit_number,
        floor=unit_in.floor,
        area_sqm=unit_in.area_sqm,
        price=unit_in.price,
        deposit=unit_in.deposit,
        status=unit_in.status.value,
        furnishing=unit_in.furnishing.value,
        has_mezzanine=unit_in.has_mezzanine,
        has_private_bathroom=unit_in.has_private_bathroom,
        max_occupants=unit_in.max_occupants,
        images=unit_in.images,
    )
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


@router.patch(
    "/units/{unit_id}/status",
    response_model=RentalUnitResponse,
    summary="1-Click toggle room status (available <-> occupied <-> reserved)",
)
async def update_unit_status(
    unit_id: uuid.UUID,
    status_update: RentalUnitStatusUpdate,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalUnit:
    unit_stmt = select(RentalUnit).where(RentalUnit.id == unit_id).options(selectinload(RentalUnit.property))
    res = await db.execute(unit_stmt)
    unit = res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng")

    if unit.property.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền quản lý phòng này")

    unit.status = status_update.status.value
    await db.commit()
    await db.refresh(unit)
    return unit


@router.get(
    "/inquiries",
    response_model=list[RentalInquiryResponse],
    summary="List viewing and booking inquiries received by current host",
)
async def list_host_inquiries(
    status_filter: str | None = Query(None, description="Lọc theo status: pending, confirmed, rejected"),
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RentalInquiry]:
    stmt = (
        select(RentalInquiry)
        .where(RentalInquiry.host_id == current_host.id)
        .options(selectinload(RentalInquiry.unit))
        .order_by(RentalInquiry.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(RentalInquiry.status == status_filter)

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.patch(
    "/inquiries/{inquiry_id}/status",
    response_model=RentalInquiryResponse,
    summary="Confirm or reject an inquiry appointment",
)
async def update_inquiry_status(
    inquiry_id: uuid.UUID,
    status_in: RentalInquiryStatusUpdate,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalInquiry:
    stmt = select(RentalInquiry).where(RentalInquiry.id == inquiry_id).options(selectinload(RentalInquiry.unit))
    res = await db.execute(stmt)
    inquiry = res.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy yêu cầu")

    if inquiry.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền duyệt yêu cầu này")

    inquiry.status = status_in.status.value
    await db.commit()
    await db.refresh(inquiry)
    return inquiry
