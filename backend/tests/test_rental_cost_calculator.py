import uuid

from src.services.rental import estimate_monthly_living_cost


def test_cost_calculator_discloses_estimates_and_preserves_zero_charges():
    estimate = estimate_monthly_living_cost(
        unit_number="P.101",
        unit_price=2_200_000,
        occupants=2,
        has_ac=True,
        has_fridge=True,
        shared_costs={"electricity_per_kwh": 3_000, "water_cost": 20_000, "water_unit": "per_person", "parking_fee_monthly": 0, "wifi_fee": 0, "service_fee_monthly": 10_000},
        property_id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
    )
    assert estimate.electricity.total_kwh == 180
    assert estimate.electricity.unit_price == 3_000
    assert estimate.variable_costs[0].amount == 540_000
    assert estimate.variable_costs[1].amount == 40_000
    assert {line.key for line in estimate.fixed_costs} >= {"room", "parking", "wifi"}
    assert estimate.estimated_total_monthly == 2_790_000
    assert estimate.per_person_monthly == 1_395_000


def test_cost_calculator_marks_missing_rates_and_uses_disclosed_default():
    estimate = estimate_monthly_living_cost(unit_number="P.102", unit_price=2_000_000, occupants=1, has_ac=False, has_fridge=False, shared_costs={})
    assert estimate.electricity.total_kwh == 30
    assert estimate.variable_costs[0].amount == 90_000
    assert "giả định" in (estimate.variable_costs[0].note or "")
    assert estimate.variable_costs[1].amount == 0
    assert "chưa tính" in (estimate.variable_costs[1].note or "")
