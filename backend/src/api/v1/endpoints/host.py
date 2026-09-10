from datetime import date, datetime, timedelta, timezone
import logging
import uuid
from geoalchemy2 import WKTElement
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_host_user
from src.core.database import get_db_session
from src.models.alert import UserNotification
from src.models.rental_property import (
    HostViewingBlockedDate,
    HostViewingSchedule,
    MonthlyInvoice,
    RentalContract,
    RentalInquiry,
    RentalProperty,
    RentalUnit,
)
from src.models.user import User
from src.schemas.rental_management import (
    DebtReminderResponse,
    GenerateInvoicesRequest,
    LandlordDashboardStats,
    MonthlyInvoiceResponse,
    RentalContractCreate,
    RentalContractResponse,
    RentalInquiryResponse,
    RentalInquiryStatusUpdate,
    RentalPropertyCreate,
    RentalPropertyResponse,
    RentalUnitCreate,
    RentalUnitResponse,
    RentalUnitStatus,
    RentalUnitStatusUpdate,
    ViewingBlockedDateRequest,
    ViewingScheduleReplaceRequest,
    ViewingScheduleWindow,
)
from src.services.viewing_calendar import calendar_values
from src.services.viewing_mail import dispatch_viewing_calendar_email

logger = logging.getLogger("space247_backend.host")
router = APIRouter()


@router.get("/schedule", response_model=list[ViewingScheduleWindow], summary="Get the current host viewing schedule")
async def get_viewing_schedule(current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> list[HostViewingSchedule]:
    result = await db.execute(select(HostViewingSchedule).where(HostViewingSchedule.host_id == current_host.id).order_by(HostViewingSchedule.day_of_week, HostViewingSchedule.start_time))
    return list(result.scalars().all())


@router.put("/schedule", response_model=list[ViewingScheduleWindow], summary="Replace the current host weekly viewing schedule")
async def replace_viewing_schedule(payload: ViewingScheduleReplaceRequest, current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> list[HostViewingSchedule]:
    existing = await db.execute(select(HostViewingSchedule).where(HostViewingSchedule.host_id == current_host.id))
    for window in existing.scalars().all():
        await db.delete(window)
    schedules = [HostViewingSchedule(host_id=current_host.id, day_of_week=window.weekday, start_time=window.start_time, end_time=window.end_time, slot_duration_minutes=window.slot_duration_minutes, is_active=window.is_active) for window in payload.windows]
    db.add_all(schedules)
    await db.commit()
    return schedules


@router.get("/schedule/blocked-dates", response_model=list[date], summary="List blocked viewing dates")
async def get_viewing_blocked_dates(current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> list[date]:
    result = await db.execute(select(HostViewingBlockedDate.date).where(HostViewingBlockedDate.host_id == current_host.id).order_by(HostViewingBlockedDate.date))
    return list(result.scalars().all())


@router.post("/schedule/block-date", status_code=status.HTTP_201_CREATED, summary="Block a viewing date")
async def block_viewing_date(payload: ViewingBlockedDateRequest, current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> ViewingBlockedDateRequest:
    exists = await db.execute(select(HostViewingBlockedDate.id).where(HostViewingBlockedDate.host_id == current_host.id, HostViewingBlockedDate.date == payload.blocked_date))
    if exists.scalar_one_or_none() is None:
        db.add(HostViewingBlockedDate(host_id=current_host.id, date=payload.blocked_date))
        await db.commit()
    return payload


@router.delete("/schedule/blocked-dates/{blocked_date}", status_code=status.HTTP_204_NO_CONTENT, summary="Unblock a viewing date")
async def unblock_viewing_date(blocked_date: date, current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> None:
    row = (await db.execute(select(HostViewingBlockedDate).where(HostViewingBlockedDate.host_id == current_host.id, HostViewingBlockedDate.date == blocked_date))).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


@router.post("/appointments/{inquiry_id}/confirm", response_model=RentalInquiryResponse, summary="Confirm a pending viewing and create calendar metadata")
async def confirm_viewing(inquiry_id: uuid.UUID, background_tasks: BackgroundTasks, current_host: User = Depends(get_current_host_user), db: AsyncSession = Depends(get_db_session)) -> RentalInquiry:
    inquiry = (await db.execute(select(RentalInquiry).where(RentalInquiry.id == inquiry_id).options(selectinload(RentalInquiry.unit).selectinload(RentalUnit.property), selectinload(RentalInquiry.tenant), selectinload(RentalInquiry.host)).with_for_update())).scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    if inquiry.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền duyệt yêu cầu này")
    if inquiry.status != "pending":
        raise HTTPException(status_code=409, detail="Chỉ có thể xác nhận lịch hẹn đang chờ")
    if not inquiry.appointment_date or not inquiry.start_time or not inquiry.end_time:
        raise HTTPException(status_code=409, detail="Lịch hẹn không có khung giờ hợp lệ")
    await db.execute(select(User.id).where(User.id == inquiry.host_id).with_for_update())
    overlap = await db.execute(select(RentalInquiry.id).where(RentalInquiry.id != inquiry.id, RentalInquiry.host_id == inquiry.host_id, RentalInquiry.appointment_date == inquiry.appointment_date, RentalInquiry.status == "confirmed", RentalInquiry.start_time < inquiry.end_time, RentalInquiry.end_time > inquiry.start_time).limit(1))
    if overlap.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Khung giờ đã có lịch xác nhận khác")
    title = f"Xem phòng {inquiry.unit.unit_number}"
    location = inquiry.unit.property.address
    inquiry.google_calendar_url, inquiry.calendar_event_uid, inquiry.ical_data = calendar_values(inquiry_id=str(inquiry.id), day=inquiry.appointment_date, start=inquiry.start_time, end=inquiry.end_time, title=title, location=location)
    inquiry.status = "confirmed"
    db.add(UserNotification(user_id=inquiry.tenant_id, title="Lịch xem phòng đã được xác nhận", message=f"{title} vào {inquiry.start_time.strftime('%H:%M')} ngày {inquiry.appointment_date.strftime('%d/%m/%Y')}.", notification_type="viewing_confirmed"))
    db.add(UserNotification(user_id=inquiry.host_id, title="Đã xác nhận lịch xem phòng", message=f"{title} vào {inquiry.start_time.strftime('%H:%M')} ngày {inquiry.appointment_date.strftime('%d/%m/%Y')}.", notification_type="viewing_confirmed"))
    await db.commit()
    await db.refresh(inquiry)
    body = f"Lịch xem phòng đã được xác nhận: {title}, {inquiry.appointment_date:%d/%m/%Y} {inquiry.start_time:%H:%M}-{inquiry.end_time:%H:%M}.\nĐịa điểm: {location}"
    for recipient in {inquiry.tenant.email, inquiry.host.email}:
        if recipient:
            background_tasks.add_task(dispatch_viewing_calendar_email, to_email=recipient, subject="Space247 - Lịch xem phòng đã được xác nhận", body=body, ical_data=inquiry.ical_data)
    return inquiry


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
        video_url=prop.video_url,
        surroundings=prop.surroundings or [],
        security_features=prop.security_features or [],
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
@router.get(
    "/dashboard/stats",
    response_model=LandlordDashboardStats,
    summary="Landlord dashboard statistics (v2)",
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

    # 4. Unpaid invoices count
    unpaid_inv_stmt = (
        select(func.count(MonthlyInvoice.id))
        .where(MonthlyInvoice.host_id == current_host.id, MonthlyInvoice.status.in_(["pending", "overdue"]))
    )
    unpaid_invoices = (await db.execute(unpaid_inv_stmt)).scalar() or 0

    return LandlordDashboardStats(
        total_properties=total_props,
        total_units=total_units,
        available_units=available_units,
        occupied_units=occupied_units,
        reserved_units=reserved_units,
        occupancy_rate=occupancy_rate,
        estimated_monthly_revenue=est_revenue,
        pending_inquiries_count=pending_inquiries,
        unpaid_invoices_count=unpaid_invoices,
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
        video_url=prop_in.video_url,
        surroundings=prop_in.surroundings,
        security_features=prop_in.security_features,
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
            floor_plan_url=u_in.floor_plan_url,
            room_amenities=u_in.room_amenities,
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

    if status_in.status.value == "confirmed" and inquiry.status == "pending" and inquiry.appointment_date and inquiry.start_time and inquiry.end_time:
        title = f"Xem phòng {inquiry.unit.unit_number}" if inquiry.unit else "Xem phòng"
        location = inquiry.unit.property.address if inquiry.unit and inquiry.unit.property else ""
        inquiry.google_calendar_url, inquiry.calendar_event_uid, inquiry.ical_data = calendar_values(
            inquiry_id=str(inquiry.id), day=inquiry.appointment_date, start=inquiry.start_time, end=inquiry.end_time, title=title, location=location,
        )
        db.add(UserNotification(user_id=inquiry.tenant_id, title="Lịch xem phòng đã được xác nhận", message=title, notification_type="viewing_confirmed"))
        db.add(UserNotification(user_id=inquiry.host_id, title="Đã xác nhận lịch xem phòng", message=title, notification_type="viewing_confirmed"))
    inquiry.status = status_in.status.value
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


# ---------------------------------------------------------------------------
# Rental Contracts Management
# ---------------------------------------------------------------------------
@router.get(
    "/contracts",
    response_model=list[RentalContractResponse],
    summary="List rental contracts managed by current host",
)
async def list_host_contracts(
    unit_id: uuid.UUID | None = Query(None, description="Lọc theo phòng"),
    status_filter: str | None = Query(None, description="Lọc theo trạng thái hợp đồng (active, expired, terminated)"),
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RentalContract]:
    stmt = (
        select(RentalContract)
        .where(RentalContract.host_id == current_host.id)
        .options(selectinload(RentalContract.unit))
        .order_by(RentalContract.created_at.desc())
    )
    if unit_id:
        stmt = stmt.where(RentalContract.unit_id == unit_id)
    if status_filter:
        stmt = stmt.where(RentalContract.status == status_filter)

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post(
    "/contracts",
    response_model=RentalContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rental contract for a unit",
)
async def create_rental_contract(
    contract_in: RentalContractCreate,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalContract:
    unit_stmt = (
        select(RentalUnit)
        .where(RentalUnit.id == contract_in.unit_id)
        .options(selectinload(RentalUnit.property))
    )
    unit_res = await db.execute(unit_stmt)
    unit = unit_res.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng")

    if unit.property.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền quản lý phòng này")

    if unit.status != RentalUnitStatus.AVAILABLE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phòng {unit.unit_number} hiện không ở trạng thái sẵn sàng để tạo hợp đồng mới (trạng thái: {unit.status})",
        )

    contract = RentalContract(
        unit_id=unit.id,
        property_id=unit.property_id,
        host_id=unit.property.host_id,
        tenant_id=contract_in.tenant_id,
        tenant_name=contract_in.tenant_name,
        tenant_phone=contract_in.tenant_phone,
        start_date=contract_in.start_date,
        end_date=contract_in.end_date,
        rental_price=contract_in.rental_price,
        deposit_amount=contract_in.deposit_amount,
        payment_cycle_months=contract_in.payment_cycle_months,
        electricity_rate=contract_in.electricity_rate,
        water_rate=contract_in.water_rate,
        water_billing_type=contract_in.water_billing_type,
        service_fee=contract_in.service_fee,
        status="active",
    )
    # Automatically mark unit as occupied
    unit.status = RentalUnitStatus.OCCUPIED.value

    db.add(contract)
    await db.commit()

    stmt = (
        select(RentalContract)
        .where(RentalContract.id == contract.id)
        .options(selectinload(RentalContract.unit))
    )
    res = await db.execute(stmt)
    return res.scalar_one()


# ---------------------------------------------------------------------------
# Invoices & Meter Readings
# ---------------------------------------------------------------------------
@router.get(
    "/invoices",
    response_model=list[MonthlyInvoiceResponse],
    summary="List monthly utility and rental invoices",
)
async def list_host_invoices(
    billing_month: str | None = Query(None, description="Lọc theo tháng (YYYY-MM)"),
    status_filter: str | None = Query(None, alias="status", description="Lọc theo status: pending, paid, overdue, cancelled"),
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[MonthlyInvoice]:
    stmt = (
        select(MonthlyInvoice)
        .where(MonthlyInvoice.host_id == current_host.id)
        .options(selectinload(MonthlyInvoice.unit), selectinload(MonthlyInvoice.contract))
        .order_by(MonthlyInvoice.created_at.desc())
    )
    if billing_month:
        stmt = stmt.where(MonthlyInvoice.billing_month == billing_month)
    if status_filter:
        stmt = stmt.where(MonthlyInvoice.status == status_filter)

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post(
    "/invoices/generate-monthly",
    response_model=list[MonthlyInvoiceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Batch generate monthly utility and rental invoices from meter readings",
)
async def generate_monthly_invoices(
    payload: GenerateInvoicesRequest,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[MonthlyInvoice]:
    created_invoices: list[MonthlyInvoice] = []

    for reading in payload.readings:
        # Duplicate check: same contract & billing_month
        dup_stmt = select(MonthlyInvoice).where(
            MonthlyInvoice.contract_id == reading.contract_id,
            MonthlyInvoice.billing_month == payload.billing_month,
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hóa đơn tháng {payload.billing_month} của hợp đồng này đã tồn tại",
            )

        stmt = (
            select(RentalContract)
            .where(RentalContract.id == reading.contract_id)
            .options(selectinload(RentalContract.unit))
        )
        res = await db.execute(stmt)
        contract = res.scalar_one_or_none()

        if not contract or (contract.host_id != current_host.id and current_host.role not in ("admin", "superadmin")):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy hợp đồng {reading.contract_id} hoặc bạn không có quyền thao tác",
            )

        if contract.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hợp đồng thuê phòng {contract.unit.unit_number if contract.unit else ''} hiện không còn hiệu lực ({contract.status})",
            )

        # Validation: current index >= previous index
        if reading.electricity_current < reading.electricity_previous:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Chỉ số điện mới ({reading.electricity_current}) không được nhỏ hơn chỉ số cũ ({reading.electricity_previous}) "
                    f"của phòng {contract.unit.unit_number if contract.unit else ''}"
                ),
            )

        water_prev = reading.water_previous or 0.0
        water_curr = reading.water_current or 0.0
        if water_curr < water_prev:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Chỉ số nước mới ({water_curr}) không được nhỏ hơn chỉ số cũ ({water_prev}) "
                    f"của phòng {contract.unit.unit_number if contract.unit else ''}"
                ),
            )

        # Calculations
        electricity_usage = reading.electricity_current - reading.electricity_previous
        electricity_amount = electricity_usage * float(contract.electricity_rate)

        if contract.water_billing_type == "per_person":
            occupants = (contract.unit.max_occupants if contract.unit and contract.unit.max_occupants else 1)
            water_amount = float(contract.water_rate) * occupants
        else:
            water_usage = max(0.0, water_curr - water_prev)
            water_amount = water_usage * float(contract.water_rate)

        room_amount = float(contract.rental_price)
        service_amount = float(contract.service_fee or 0.0)
        other_amount = 0.0
        total_amount = room_amount + electricity_amount + water_amount + service_amount + other_amount

        due_date = datetime.now(timezone.utc) + timedelta(days=payload.due_days)

        invoice = MonthlyInvoice(
            contract_id=contract.id,
            unit_id=contract.unit_id,
            host_id=contract.host_id,
            tenant_id=contract.tenant_id,
            billing_month=payload.billing_month,
            room_amount=room_amount,
            electricity_previous_index=reading.electricity_previous,
            electricity_current_index=reading.electricity_current,
            electricity_rate=float(contract.electricity_rate),
            electricity_amount=electricity_amount,
            water_previous_index=water_prev,
            water_current_index=water_curr,
            water_rate=float(contract.water_rate),
            water_amount=water_amount,
            service_amount=service_amount,
            other_amount=other_amount,
            total_amount=total_amount,
            status="pending",
            due_date=due_date,
            notes=reading.notes,
        )
        db.add(invoice)
        created_invoices.append(invoice)

    await db.commit()

    created_ids = [inv.id for inv in created_invoices]
    fetch_stmt = (
        select(MonthlyInvoice)
        .where(MonthlyInvoice.id.in_(created_ids))
        .options(selectinload(MonthlyInvoice.unit), selectinload(MonthlyInvoice.contract))
        .order_by(MonthlyInvoice.created_at.asc())
    )
    result = await db.execute(fetch_stmt)
    return list(result.scalars().all())


@router.post(
    "/invoices/{invoice_id}/remind",
    response_model=DebtReminderResponse,
    summary="Send in-app notification reminder for unpaid rent/utilities invoice",
)
async def send_invoice_reminder(
    invoice_id: uuid.UUID,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> DebtReminderResponse:
    stmt = (
        select(MonthlyInvoice)
        .where(MonthlyInvoice.id == invoice_id)
        .options(selectinload(MonthlyInvoice.contract), selectinload(MonthlyInvoice.unit))
    )
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hóa đơn")

    if invoice.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền quản lý hóa đơn này")

    if invoice.status not in ("pending", "overdue"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chỉ có thể nhắc nợ hóa đơn chưa thanh toán hoặc quá hạn (trạng thái: {invoice.status})",
        )

    due_str = invoice.due_date.strftime("%d/%m/%Y")
    unit_str = f"phòng {invoice.unit.unit_number}" if invoice.unit else "phòng của bạn"
    reminder_title = f"Nhắc nợ tiền phòng tháng {invoice.billing_month}"
    reminder_msg = (
        f"Hóa đơn {unit_str} tháng {invoice.billing_month} với tổng số tiền {float(invoice.total_amount):,.0f} VND "
        f"cần thanh toán trước ngày {due_str}. Vui lòng thanh toán sớm cho chủ nhà."
    )

    notif = UserNotification(
        user_id=invoice.tenant_id,
        title=reminder_title,
        message=reminder_msg,
        notification_type="invoice_reminder",
    )
    db.add(notif)
    invoice.last_reminded_at = datetime.now(timezone.utc)
    await db.commit()

    tenant_name = invoice.contract.tenant_name if invoice.contract else None
    tenant_phone = invoice.contract.tenant_phone if invoice.contract else None

    return DebtReminderResponse(
        invoice_id=invoice.id,
        tenant_id=invoice.tenant_id,
        tenant_name=tenant_name,
        tenant_phone=tenant_phone,
        amount_due=float(invoice.total_amount),
        notification_sent=True,
        message=f"Đã gửi nhắc nợ thành công tới khách thuê qua thông báo ứng dụng.",
    )
