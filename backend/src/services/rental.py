"""Shared exact rental predicates and explicit cost units."""
from decimal import Decimal
from sqlalchemy import func, cast
from geoalchemy2 import Geography
from src.models.property import Property

RULE_KEYS = ("allow_pets", "curfew", "private_bathroom", "has_mezzanine", "has_washing_machine", "live_with_owner", "has_elevator", "fingerprint_lock")


def deposit_amount(monthly_rent, deposit_months):
    if deposit_months is None:
        return None
    return Decimal(str(monthly_rent)) * Decimal(str(deposit_months))


def apply_rental_filters(stmt, criteria, coordinates=None):
    values = criteria.model_dump() if hasattr(criteria, "model_dump") else criteria
    keys = (*RULE_KEYS, "rental_type", "electricity_billing", "max_deposit")
    if any(values.get(key) is not None for key in keys):
        stmt = stmt.where(Property.listing_type == "rent", Property.status == "active")
    if values.get("rental_type") is not None:
        stmt = stmt.where(Property.rental_type == values["rental_type"])
    for key in RULE_KEYS:
        if values.get(key) is not None:
            stmt = stmt.where(Property.rental_rules[key].as_boolean() == values[key])
    if values.get("electricity_billing") is not None:
        stmt = stmt.where(Property.rental_costs["electricity_billing"].as_string() == values["electricity_billing"])
    if values.get("max_deposit") is not None:
        stmt = stmt.where(Property.rental_costs["deposit_months"].as_integer() <= values["max_deposit"])
    if coordinates:
        lat, lng = coordinates
        point = cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)
        stmt = stmt.where(func.ST_DWithin(cast(Property.geom, Geography), point, values.get("radius_km", 3.0) * 1000))
    return stmt


async def resolve_landmark(criteria):
    landmark = getattr(criteria, "near_landmark", None)
    if not landmark:
        return None
    from src.services.spatial_service import SpatialService, normalize_vietnamese_text
    normalized = normalize_vietnamese_text(landmark).replace(".", "")
    if normalized in ("bach khoa", "dai hoc bach khoa", "dh bach khoa", "truong bach khoa", "truong dai hoc bach khoa"):
        landmark = "Đại học Bách Khoa Hà Nội"
    elif "bach khoa" in normalized and any(city in normalized for city in ("hcm", "ho chi minh", "sai gon")):
        landmark = "dai hoc bach khoa tphcm"
    try:
        location = await SpatialService().geocode_landmark(landmark)
        return (location.latitude, location.longitude) if location else None
    except Exception:
        return None


def rental_text(rental_type=None, rental_costs=None, rental_rules=None):
    labels = {"room": "Phòng trọ", "serviced_apartment": "Căn hộ dịch vụ", "house_share": "Ở ghép", "entire_house": "Nguyên căn"}
    parts = [labels.get(rental_type, rental_type)] if rental_type else []
    costs = rental_costs or {}
    water_unit = "VND/người/tháng" if costs.get("water_unit") == "per_person" else "VND/m³" if costs.get("water_unit") == "per_m3" else "VND (chưa rõ đơn vị)"
    units = {"electricity_per_kwh": "VND/kWh", "water_cost": water_unit, "deposit_months": "tháng", "parking_fee_monthly": "VND/tháng", "service_fee_monthly": "VND/tháng"}
    names = {"electricity_per_kwh": "Giá điện", "water_cost": "Giá nước", "deposit_months": "Đặt cọc", "parking_fee_monthly": "Phí gửi xe", "service_fee_monthly": "Phí dịch vụ", "allow_pets": "Cho nuôi thú cưng", "curfew": "Có giờ đóng cửa", "private_bathroom": "Phòng tắm riêng", "has_mezzanine": "Có gác lửng", "has_washing_machine": "Máy giặt", "live_with_owner": "Chung chủ", "has_elevator": "Thang máy", "fingerprint_lock": "Khóa vân tay", "max_occupants": "Số người tối đa", "curfew_time": "Giờ đóng cửa"}
    for key, value in (rental_costs or {}).items():
        if value is not None:
            label = names.get(key, key)
            display = "điện giá dân, giá nhà nước" if value == "state_rate" else "đơn giá cố định" if value == "fixed" else value
            parts.append(f"{label} ({key}): {display} {units.get(key, '')}")
    for key, value in (rental_rules or {}).items():
        if value is not None:
            display = "Có" if value is True else "Không" if value is False else value
            parts.append(f"{names.get(key, key)} ({key}): {display}")
    return ". ".join(parts)


# Smart Living Cost Calculator — transparent monthly budget estimation.
AC_KWH_PER_MONTH = 120.0
FRIDGE_KWH_PER_MONTH = 30.0
GENERAL_KWH_PER_MONTH = 30.0
DEFAULT_ELECTRICITY_PRICE = 3000.0
ESTIMATED_WATER_M3_PER_PERSON = 2.0


def estimate_monthly_living_cost(
    *,
    unit_number: str,
    unit_price: float,
    shared_costs: dict | None,
    occupants: int = 1,
    has_ac: bool = True,
    has_fridge: bool = True,
    property_id=None,
    unit_id=None,
):
    """Estimate a transparent monthly cost sheet for one rental unit.

    Pure function (no DB) so it stays unit-testable:
    - Electricity: appliance-based kWh estimate × unit price from shared_costs.
    - Water: per-person billing multiplies occupants; per-m³ assumes ~2 m³/person.
    - Fixed costs: room rent + wifi/parking/cleaning from shared_costs.
    """
    from src.schemas.rental_management import (
        CostLineItem,
        ElectricityBreakdown,
        MonthlyCostEstimate,
    )

    costs = shared_costs or {}
    occupants = max(1, occupants)

    ac_kwh = AC_KWH_PER_MONTH if has_ac else 0.0
    fridge_kwh = FRIDGE_KWH_PER_MONTH if has_fridge else 0.0
    general_kwh = GENERAL_KWH_PER_MONTH
    total_kwh = ac_kwh + fridge_kwh + general_kwh
    published_electricity_price = costs.get("electricity_per_kwh")
    unit_price_per_kwh = float(DEFAULT_ELECTRICITY_PRICE if published_electricity_price is None else published_electricity_price)

    electricity_amount = total_kwh * unit_price_per_kwh

    water_unit = costs.get("water_unit")
    water_cost = costs.get("water_cost")
    if water_cost is not None and water_unit == "per_person":
        water_amount = float(water_cost) * occupants
        water_note = f"{water_cost:,.0f} đ × {occupants} người"
    elif water_cost is not None:
        estimated_m3 = ESTIMATED_WATER_M3_PER_PERSON * occupants
        water_amount = float(water_cost) * estimated_m3
        water_note = f"{water_cost:,.0f} đ × ~{estimated_m3:.0f} m³ (ước tính {ESTIMATED_WATER_M3_PER_PERSON:.0f} m³/người)"
    else:
        water_amount = 0.0
        water_note = "Chưa công bố giá nước; chưa tính vào tổng dự kiến"

    fixed_costs = [
        CostLineItem(key="room", label="Tiền phòng", amount=float(unit_price), note=None),
    ]
    wifi_fee = costs.get("wifi_fee")
    if wifi_fee is not None:
        fixed_costs.append(CostLineItem(key="wifi", label="Internet/Wifi", amount=float(wifi_fee), note=None))
    parking_fee = costs.get("parking_fee_monthly")
    if parking_fee is not None:
        fixed_costs.append(CostLineItem(key="parking", label="Phí gửi xe", amount=float(parking_fee), note=None))
    cleaning_fee = costs.get("cleaning_fee")
    if cleaning_fee is not None:
        fixed_costs.append(CostLineItem(key="cleaning", label="Phí vệ sinh", amount=float(cleaning_fee), note=None))
    service_fee = costs.get("service_fee_monthly")
    if service_fee is not None:
        fixed_costs.append(CostLineItem(key="service", label="Phí dịch vụ", amount=float(service_fee), note=None))

    appliance_notes = []
    if has_ac:
        appliance_notes.append(f"Máy lạnh ~{AC_KWH_PER_MONTH:.0f} kWh")
    if has_fridge:
        appliance_notes.append(f"Tủ lạnh ~{FRIDGE_KWH_PER_MONTH:.0f} kWh")
    appliance_notes.append(f"Sinh hoạt chung ~{GENERAL_KWH_PER_MONTH:.0f} kWh")

    variable_costs = [
        CostLineItem(
            key="electricity",
            label="Tiền điện (dự tính)",
            amount=electricity_amount,
            note=f"{' + '.join(appliance_notes)} × {unit_price_per_kwh:,.0f} đ/kWh" + (" (giả định khi chưa công bố giá điện)" if published_electricity_price is None else ""),
        ),
        CostLineItem(key="water", label="Tiền nước (dự tính)", amount=water_amount, note=water_note),
    ]

    estimated_total = sum(item.amount for item in fixed_costs) + sum(item.amount for item in variable_costs)

    return MonthlyCostEstimate(
        property_id=property_id,
        unit_id=unit_id,
        unit_number=unit_number,
        occupants=occupants,
        electricity=ElectricityBreakdown(
            ac_kwh=ac_kwh,
            fridge_kwh=fridge_kwh,
            general_kwh=general_kwh,
            total_kwh=total_kwh,
            unit_price=unit_price_per_kwh,
        ),
        fixed_costs=fixed_costs,
        variable_costs=variable_costs,
        estimated_total_monthly=estimated_total,
        per_person_monthly=estimated_total / occupants,
    )
