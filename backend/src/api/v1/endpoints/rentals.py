from datetime import date, datetime, time, timedelta, timezone
import logging
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user, get_current_host_user, get_optional_current_user
from src.core.database import get_db_session
from src.models.rental_property import DepositTransaction, HostViewingBlockedDate, HostViewingSchedule, RentalInquiry, RentalProperty, RentalUnit
from src.models.user import User
from src.schemas.rental_management import (
    DepositApproveRequest,
    DepositTransactionResponse,
    RentalInquiryCreate,
    RentalInquiryResponse,
    RentalPropertyModel,
    RentalPropertyResponse,
    RentalSearchFilter,
    RentalUnitFurnishing,
    RentalUnitResponse,
    RentalUnitStatus,
    ViewingBookingRequest,
    ViewingCalendarResponse,
    ViewingSlot,
)
from src.services.payment_service import PaymentService
from src.services.viewing_calendar import calendar_values

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


async def _available_slot_windows(db: AsyncSession, host_id: uuid.UUID, day: date) -> list[tuple[time, time, int]]:
    blocked = await db.execute(select(HostViewingBlockedDate.id).where(HostViewingBlockedDate.host_id == host_id, HostViewingBlockedDate.date == day))
    if blocked.scalar_one_or_none() is not None:
        return []
    schedules = await db.execute(select(HostViewingSchedule).where(HostViewingSchedule.host_id == host_id, HostViewingSchedule.day_of_week == day.weekday(), HostViewingSchedule.is_active == True).order_by(HostViewingSchedule.start_time))
    return [(window.start_time, window.end_time, window.slot_duration_minutes) for window in schedules.scalars().all()]


@router.get("/{unit_id}/available-slots", response_model=list[ViewingSlot], summary="List available viewing slots for a Vietnam civil date")
async def list_viewing_slots(unit_id: uuid.UUID, day: date = Query(..., alias="date"), db: AsyncSession = Depends(get_db_session)) -> list[ViewingSlot]:
    unit = (await db.execute(select(RentalUnit).where(RentalUnit.id == unit_id).options(selectinload(RentalUnit.property)))).scalar_one_or_none()
    if not unit or not unit.property.is_active or unit.status == RentalUnitStatus.OCCUPIED.value:
        return []
    windows = await _available_slot_windows(db, unit.property.host_id, day)
    if not windows:
        return []
    appointments = await db.execute(select(RentalInquiry).where(RentalInquiry.host_id == unit.property.host_id, RentalInquiry.appointment_date == day, RentalInquiry.status.in_(("pending", "confirmed"))))
    reserved = [(item.start_time, item.end_time) for item in appointments.scalars().all() if item.start_time and item.end_time]
    slots: list[ViewingSlot] = []
    for starts_at, ends_at, duration in windows:
        cursor = datetime.combine(day, starts_at)
        boundary = datetime.combine(day, ends_at)
        while cursor + timedelta(minutes=duration) <= boundary:
            start, end = cursor.time(), (cursor + timedelta(minutes=duration)).time()
            if not any(start < existing_end and end > existing_start for existing_start, existing_end in reserved):
                slots.append(ViewingSlot(date=day, start_time=start, end_time=end))
            cursor += timedelta(minutes=duration)
    return slots


@router.post("/units/{unit_id}/book-appointment", response_model=RentalInquiryResponse, status_code=status.HTTP_201_CREATED, summary="Book an available viewing slot")
async def book_viewing_slot(unit_id: uuid.UUID, booking: ViewingBookingRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_session)) -> RentalInquiry:
    from src.services.viewing_calendar import VIETNAM_TZ
    if booking.date < datetime.now(VIETNAM_TZ).date():
        raise HTTPException(status_code=422, detail="Không thể đặt lịch trong quá khứ")
    unit = (await db.execute(select(RentalUnit).where(RentalUnit.id == unit_id).options(selectinload(RentalUnit.property)))).scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng tương ứng")
    if unit.status == RentalUnitStatus.OCCUPIED.value or not unit.property.is_active:
        raise HTTPException(status_code=409, detail="Phòng không còn khả dụng để đặt lịch xem")
    end_time = None
    for starts_at, ends_at, duration in await _available_slot_windows(db, unit.property.host_id, booking.date):
        start_minutes = starts_at.hour * 60 + starts_at.minute
        requested_minutes = booking.start_time.hour * 60 + booking.start_time.minute
        if (requested_minutes - start_minutes) % duration != 0:
            continue
        candidate_end = (datetime.combine(booking.date, booking.start_time) + timedelta(minutes=duration)).time()
        if starts_at <= booking.start_time and candidate_end <= ends_at:
            end_time = candidate_end
            break
    if end_time is None:
        raise HTTPException(status_code=409, detail="Khung giờ đã chọn không còn khả dụng")
    # Serialize all bookings for a host so overlap checks cannot race between tenants.
    await db.execute(select(User.id).where(User.id == unit.property.host_id).with_for_update())
    overlap = await db.execute(select(RentalInquiry.id).where(RentalInquiry.host_id == unit.property.host_id, RentalInquiry.appointment_date == booking.date, RentalInquiry.status.in_(("pending", "confirmed")), RentalInquiry.start_time < end_time, RentalInquiry.end_time > booking.start_time).with_for_update())
    if overlap.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Khung giờ đã được đặt")
    inquiry = RentalInquiry(unit_id=unit.id, tenant_id=current_user.id, host_id=unit.property.host_id, inquiry_type="view_appointment", appointment_date=booking.date, start_time=booking.start_time, end_time=end_time, scheduled_time=datetime.combine(booking.date, booking.start_time, tzinfo=timezone(timedelta(hours=7))), tenant_name=booking.tenant_name or current_user.full_name, tenant_phone=booking.tenant_phone or current_user.phone, message=booking.message, status="pending")
    db.add(inquiry)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Khung giờ đã được đặt")
    await db.refresh(inquiry)
    return inquiry


@router.get("/appointments/{inquiry_id}/calendar.ics", summary="Download a confirmed viewing as iCalendar")
async def download_viewing_calendar(inquiry_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_session)) -> Response:
    inquiry = (await db.execute(select(RentalInquiry).where(RentalInquiry.id == inquiry_id))).scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
    if current_user.id not in (inquiry.tenant_id, inquiry.host_id):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập lịch hẹn này")
    if inquiry.status != "confirmed" or not inquiry.ical_data:
        raise HTTPException(status_code=409, detail="Lịch hẹn chưa được xác nhận")
    return Response(inquiry.ical_data, media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="space247-viewing-{inquiry.id}.ics"'})


@router.get("/inquiries/{inquiry_id}/calendar", response_model=ViewingCalendarResponse, summary="Get confirmed viewing calendar metadata")
async def get_viewing_calendar(inquiry_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_session)) -> ViewingCalendarResponse:
    inquiry = (await db.execute(select(RentalInquiry).where(RentalInquiry.id == inquiry_id))).scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
    if current_user.id not in (inquiry.tenant_id, inquiry.host_id):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập lịch hẹn này")
    if inquiry.status != "confirmed" or not inquiry.google_calendar_url or not inquiry.calendar_event_uid:
        raise HTTPException(status_code=409, detail="Lịch hẹn chưa được xác nhận")
    return ViewingCalendarResponse(inquiry_id=inquiry.id, google_calendar_url=inquiry.google_calendar_url, ical_uid=inquiry.calendar_event_uid)


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


@router.post(
    "/inquiries/{inquiry_id}/approve-and-deposit",
    response_model=DepositTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Approve booking inquiry and generate 15-minute VietQR deposit checkout link",
)
async def approve_inquiry_and_deposit(
    inquiry_id: uuid.UUID,
    payload: DepositApproveRequest | None = None,
    current_host: User = Depends(get_current_host_user),
    db: AsyncSession = Depends(get_db_session),
) -> DepositTransaction:
    stmt = (
        select(RentalInquiry)
        .where(RentalInquiry.id == inquiry_id)
        .options(selectinload(RentalInquiry.unit).selectinload(RentalUnit.property))
    )
    res = await db.execute(stmt)
    inquiry = res.scalar_one_or_none()

    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy yêu cầu thuê phòng")

    unit = inquiry.unit
    if not unit or not unit.property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin phòng liên quan")

    if unit.property.host_id != current_host.id and current_host.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền quản lý phòng này")

    if unit.status in (RentalUnitStatus.OCCUPIED.value, RentalUnitStatus.RESERVED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng này hiện đã có người thuê hoặc đã được đặt cọc giữ chỗ",
        )

    if payload and payload.deposit_amount and payload.deposit_amount > 0:
        deposit_amount = float(payload.deposit_amount)
    else:
        deposit_amount = float(
            unit.deposit if unit.deposit and unit.deposit > 0 else (unit.price if unit.price and unit.price > 0 else 1_000_000)
        )
    ref_code = PaymentService.generate_reference_code()
    vietqr_url = PaymentService.generate_vietqr_url(reference_code=ref_code, amount=deposit_amount)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)

    tx = DepositTransaction(
        unit_id=unit.id,
        inquiry_id=inquiry.id,
        tenant_id=inquiry.tenant_id,
        host_id=unit.property.host_id,
        amount=deposit_amount,
        reference_code=ref_code,
        payment_method="vietqr",
        vietqr_url=vietqr_url,
        status="pending",
        expires_at=expires_at,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx
