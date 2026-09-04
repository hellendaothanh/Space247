import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.schemas.mortgage import CalculationMethod, MortgageCalcRequest
from src.services.mortgage_service import MortgageService


@pytest.mark.asyncio
async def test_mortgage_calc_declining_balance_endpoint():
    """Verify declining balance calculation through the public HTTP endpoint."""
    payload = {
        "property_price": 5_000_000_000,
        "down_payment_percent": 30.0,
        "loan_term_years": 20,
        "annual_interest_rate": 7.5,
        "preferential_period_months": 12,
        "post_preferential_rate": 10.5,
        "calculation_method": "declining_balance",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/financial/mortgage-calc", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["property_price"] == 5_000_000_000
        assert data["down_payment_amount"] == 1_500_000_000
        assert data["loan_amount"] == 3_500_000_000
        assert data["loan_term_years"] == 20
        assert data["loan_term_months"] == 240
        assert data["calculation_method"] == "declining_balance"

        # Month 1 monthly payment: principal (3.5B / 240 = 14,583,333) + interest (3.5B * 7.5% / 12 = 21,875,000)
        # Expected first month payment ~ 36,458,333 VND
        assert data["monthly_payment_first_month"] > 35_000_000
        assert data["monthly_payment_first_month"] < 38_000_000
        assert data["total_interest"] > 0

        # Verify schedule length and final balance
        schedule = data["schedule"]
        assert len(schedule) == 240
        assert schedule[0]["month"] == 1
        assert schedule[0]["interest_rate"] == 7.5
        assert schedule[11]["interest_rate"] == 7.5
        assert schedule[12]["interest_rate"] == 10.5
        assert schedule[-1]["month"] == 240
        assert schedule[-1]["remaining_balance"] == 0.0


@pytest.mark.asyncio
async def test_mortgage_calc_fixed_payment_endpoint():
    """Verify fixed payment (annuity) calculation through the public HTTP endpoint."""
    payload = {
        "property_price": 3_000_000_000,
        "down_payment_percent": 20.0,
        "loan_term_years": 15,
        "annual_interest_rate": 8.0,
        "preferential_period_months": 24,
        "post_preferential_rate": 11.0,
        "calculation_method": "fixed_payment",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/financial/mortgage-calc", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["loan_amount"] == 2_400_000_000
        assert data["loan_term_months"] == 180
        assert data["calculation_method"] == "fixed_payment"

        schedule = data["schedule"]
        assert len(schedule) == 180

        # Payments during preferential period should be virtually constant
        pmt_month_1 = schedule[0]["total_payment"]
        pmt_month_2 = schedule[1]["total_payment"]
        assert abs(pmt_month_1 - pmt_month_2) <= 1.0  # round rounding diff

        # Remaining balance at end must be 0
        assert schedule[-1]["remaining_balance"] == 0.0


@pytest.mark.asyncio
async def test_mortgage_calc_edge_cases():
    """Test 0% down payment, 100% down payment, and zero interest rate without crash."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Case 1: 100% down payment (0 loan)
        resp1 = await client.post(
            "/api/v1/financial/mortgage-calc",
            json={
                "property_price": 2_000_000_000,
                "down_payment_percent": 100.0,
                "loan_term_years": 10,
            },
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["loan_amount"] == 0.0
        assert data1["monthly_payment_first_month"] == 0.0
        assert data1["total_interest"] == 0.0

        # Case 2: 0% down payment (100% loan)
        resp2 = await client.post(
            "/api/v1/financial/mortgage-calc",
            json={
                "property_price": 1_000_000_000,
                "down_payment_percent": 0.0,
                "loan_term_years": 10,
            },
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["loan_amount"] == 1_000_000_000
        assert data2["down_payment_amount"] == 0.0

        # Case 3: 0% interest rate
        resp3 = await client.post(
            "/api/v1/financial/mortgage-calc",
            json={
                "property_price": 1_200_000_000,
                "down_payment_percent": 20.0,
                "loan_term_years": 10,
                "annual_interest_rate": 0.0,
                "post_preferential_rate": 0.0,
                "calculation_method": "fixed_payment",
            },
        )
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["total_interest"] == 0.0
        assert len(data3["schedule"]) == 120
        assert data3["schedule"][-1]["remaining_balance"] == 0.0


@pytest.mark.asyncio
async def test_mortgage_calc_invalid_terms():
    """Verify validation: loan_term_years not in 1-35 returns 400 or 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 0 years
        resp1 = await client.post(
            "/api/v1/financial/mortgage-calc",
            json={
                "property_price": 2_000_000_000,
                "loan_term_years": 0,
            },
        )
        assert resp1.status_code in [400, 422]

        # 40 years (> 35)
        resp2 = await client.post(
            "/api/v1/financial/mortgage-calc",
            json={
                "property_price": 2_000_000_000,
                "loan_term_years": 40,
            },
        )
        assert resp2.status_code in [400, 422]
