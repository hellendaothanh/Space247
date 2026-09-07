import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.core.database import get_db_session
from src.api.deps import get_current_host_user, get_current_active_user
from src.models.user import User, UserRole
from src.models.alert import UserNotification
from src.models.rental_property import (
    DepositTransaction,
    MonthlyInvoice,
    RentalContract,
    RentalInquiry,
    RentalProperty,
    RentalUnit,
)
from src.schemas.rental_management import RentalUnitStatus
from src.services.chat_assistant import ChatAssistantService
from src.schemas.chat import ChatMessage


@pytest.fixture
def host_user() -> User:
    return User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        email="host_lead@space247.vn",
        hashed_password="fakehashpassword",
        full_name="Chủ Nhà Lê Hoàng Long",
        phone="0911223344",
        role=UserRole.HOST.value,
        is_active=True,
    )


@pytest.fixture
def other_host_user() -> User:
    return User(
        id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        email="other_host@space247.vn",
        hashed_password="fakehashpassword",
        full_name="Chủ Nhà Người Khác",
        phone="0933445566",
        role=UserRole.HOST.value,
        is_active=True,
    )


@pytest.fixture
def tenant_user() -> User:
    return User(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        email="tenant_bob@space247.vn",
        hashed_password="fakehashpassword",
        full_name="Khách Thuê Nguyễn Văn An",
        phone="0988776655",
        role=UserRole.USER.value,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_host_dashboard_stats_and_contract_lifecycle(host_user: User, tenant_user: User):
    properties_db: dict[uuid.UUID, RentalProperty] = {}
    units_db: dict[uuid.UUID, RentalUnit] = {}
    contracts_db: dict[uuid.UUID, RentalContract] = {}
    invoices_db: dict[uuid.UUID, MonthlyInvoice] = {}
    inquiries_db: dict[uuid.UUID, RentalInquiry] = {}

    prop_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    prop = RentalProperty(
        id=prop_id,
        host_id=host_user.id,
        name="Nhà Trọ Hoàng Long",
        description="Phòng trọ cao cấp trung tâm",
        address="123 Đinh Tiên Hoàng",
        city="Hồ Chí Minh",
        district="Quận 1",
        is_active=True,
    )
    prop.units = []
    properties_db[prop.id] = prop

    unit_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    unit = RentalUnit(
        id=unit_id,
        property_id=prop.id,
        unit_number="P.101",
        floor=1,
        area_sqm=25.0,
        price=4_000_000.0,
        deposit=4_000_000.0,
        status="available",
    )
    unit.property = prop
    prop.units.append(unit)
    units_db[unit.id] = unit

    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, RentalContract):
            contracts_db[obj.id] = obj
            if obj.unit_id in units_db:
                obj.unit = units_db[obj.unit_id]
        elif isinstance(obj, MonthlyInvoice):
            invoices_db[obj.id] = obj
            if obj.unit_id in units_db:
                obj.unit = units_db[obj.unit_id]
            if obj.contract_id in contracts_db:
                obj.contract = contracts_db[obj.contract_id]
        elif isinstance(obj, UserNotification):
            pass

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()

        if "count(rental_properties.id)" in text_stmt:
            res.scalar.return_value = len(properties_db)
            return res
        if "count(rental_inquiries.id)" in text_stmt:
            res.scalar.return_value = 1
            return res
        if "count(monthly_invoices.id)" in text_stmt:
            res.scalar.return_value = len([i for i in invoices_db.values() if i.status in ("pending", "overdue")])
            return res

        if "from rental_units" in text_stmt:
            params = getattr(stmt.compile(), "params", {})
            for val in params.values():
                if isinstance(val, uuid.UUID) and val in units_db:
                    u = units_db[val]
                    u.property = properties_db.get(u.property_id)
                    res.scalar_one_or_none.return_value = u
                    return res
            res.scalars.return_value.all.return_value = list(units_db.values())
            return res

        if "from rental_contracts" in text_stmt:
            params = getattr(stmt.compile(), "params", {})
            for val in params.values():
                if isinstance(val, uuid.UUID) and val in contracts_db:
                    c = contracts_db[val]
                    c.unit = units_db.get(c.unit_id)
                    res.scalar_one.return_value = c
                    res.scalar_one_or_none.return_value = c
                    return res
            res.scalars.return_value.all.return_value = list(contracts_db.values())
            return res

        res.scalars.return_value.all.return_value = []
        res.scalar_one_or_none.return_value = None
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test GET /api/v1/host/dashboard/stats
        stats_resp = await client.get("/api/v1/host/dashboard/stats")
        assert stats_resp.status_code == 200
        stats_data = stats_resp.json()
        assert stats_data["total_properties"] == 1
        assert stats_data["total_units"] == 1
        assert stats_data["available_units"] == 1
        assert "unpaid_invoices_count" in stats_data
        assert "occupancy_rate" in stats_data
        assert "estimated_monthly_revenue" in stats_data

        # 2. Test POST /api/v1/host/contracts
        contract_payload = {
            "unit_id": str(unit.id),
            "tenant_id": str(tenant_user.id),
            "tenant_name": tenant_user.full_name,
            "tenant_phone": tenant_user.phone,
            "start_date": datetime.now(timezone.utc).isoformat(),
            "rental_price": 4_000_000.0,
            "deposit_amount": 4_000_000.0,
            "electricity_rate": 3500.0,
            "water_rate": 20000.0,
            "water_billing_type": "per_m3",
            "service_fee": 150000.0,
        }
        create_c_resp = await client.post("/api/v1/host/contracts", json=contract_payload)
        assert create_c_resp.status_code == 201
        c_data = create_c_resp.json()
        assert c_data["rental_price"] == 4_000_000.0
        assert unit.status == RentalUnitStatus.OCCUPIED.value

        # 3. Test GET /api/v1/host/contracts
        list_c_resp = await client.get("/api/v1/host/contracts")
        assert list_c_resp.status_code == 200
        assert len(list_c_resp.json()) == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invoice_generation_math_and_validation(host_user: User, tenant_user: User):
    contract_id = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    unit_id = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

    unit = RentalUnit(
        id=unit_id,
        property_id=uuid.uuid4(),
        unit_number="P.202",
        area_sqm=30.0,
        price=5_000_000.0,
        status="occupied",
        max_occupants=2,
    )
    contract = RentalContract(
        id=contract_id,
        unit_id=unit.id,
        property_id=unit.property_id,
        host_id=host_user.id,
        tenant_id=tenant_user.id,
        tenant_name=tenant_user.full_name,
        tenant_phone=tenant_user.phone,
        start_date=datetime.now(timezone.utc),
        rental_price=5_000_000.0,
        electricity_rate=4000.0,
        water_rate=25000.0,
        water_billing_type="per_m3",
        service_fee=200000.0,
        status="active",
    )
    contract.unit = unit

    invoices_db: dict[uuid.UUID, MonthlyInvoice] = {}
    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, MonthlyInvoice):
            invoices_db[obj.id] = obj
            obj.contract = contract
            obj.unit = unit

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()
        if "from rental_contracts" in text_stmt:
            res.scalar_one_or_none.return_value = contract
            return res
        if "from monthly_invoices" in text_stmt:
            res.scalar_one_or_none.return_value = None
            res.scalars.return_value.all.return_value = list(invoices_db.values())
            return res
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Case 1: Negative electricity meter diff -> 400 Bad Request
        bad_reading = {
            "billing_month": "2026-09",
            "readings": [
                {
                    "contract_id": str(contract_id),
                    "electricity_previous": 200.0,
                    "electricity_current": 180.0,  # Invalid: current < previous
                    "water_previous": 10.0,
                    "water_current": 15.0,
                }
            ],
            "due_days": 5,
        }
        bad_resp = await client.post("/api/v1/host/invoices/generate-monthly", json=bad_reading)
        assert bad_resp.status_code == 400
        assert "không được nhỏ hơn" in bad_resp.json()["detail"]

        # Case 2: Valid readings:
        # Electricity = (250 - 200) * 4000 = 50 * 4000 = 200,000
        # Water = (15 - 10) * 25000 = 5 * 25000 = 125,000
        # Room = 5,000,000
        # Service = 200,000
        # Total = 5,000,000 + 200,000 + 125,000 + 200,000 = 5,525,000
        valid_reading = {
            "billing_month": "2026-09",
            "readings": [
                {
                    "contract_id": str(contract_id),
                    "electricity_previous": 200.0,
                    "electricity_current": 250.0,
                    "water_previous": 10.0,
                    "water_current": 15.0,
                }
            ],
            "due_days": 5,
        }
        good_resp = await client.post("/api/v1/host/invoices/generate-monthly", json=valid_reading)
        assert good_resp.status_code == 201
        invoices = good_resp.json()
        assert len(invoices) == 1
        inv = invoices[0]
        assert inv["room_amount"] == 5_000_000.0
        assert inv["electricity_amount"] == 200_000.0
        assert inv["water_amount"] == 125_000.0
        assert inv["service_amount"] == 200_000.0
        assert inv["total_amount"] == 5_525_000.0
        assert inv["status"] == "pending"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_debt_reminder_notification(host_user: User, tenant_user: User):
    invoice_id = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
    invoice = MonthlyInvoice(
        id=invoice_id,
        contract_id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
        host_id=host_user.id,
        tenant_id=tenant_user.id,
        billing_month="2026-09",
        room_amount=4_000_000.0,
        total_amount=4_500_000.0,
        status="pending",
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
    )
    invoice.contract = None
    invoice.unit = None

    notifications_dispatched = []
    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, UserNotification):
            notifications_dispatched.append(obj)

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = invoice
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        remind_resp = await client.post(f"/api/v1/host/invoices/{invoice_id}/remind")
        assert remind_resp.status_code == 200
        remind_data = remind_resp.json()
        assert remind_data["notification_sent"] is True
        assert remind_data["amount_due"] == 4_500_000.0
        assert len(notifications_dispatched) == 1
        assert notifications_dispatched[0].notification_type == "invoice_reminder"
        assert invoice.last_reminded_at is not None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rentals_approve_and_deposit_workflow(host_user: User, tenant_user: User):
    prop_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    prop = RentalProperty(id=prop_id, host_id=host_user.id, name="Khu Trọ An Bình", address="789 Xô Viết Nghệ Tĩnh", city="Hồ Chí Minh")

    unit_id = uuid.UUID("12121212-1212-1212-1212-121212121212")
    unit = RentalUnit(
        id=unit_id,
        property_id=prop_id,
        unit_number="P.303",
        price=3_500_000.0,
        deposit=3_500_000.0,
        status="available",
        area_sqm=20.0,
    )
    unit.property = prop

    inquiry_id = uuid.UUID("34343434-3434-3434-3434-343434343434")
    inquiry = RentalInquiry(
        id=inquiry_id,
        unit_id=unit_id,
        tenant_id=tenant_user.id,
        host_id=host_user.id,
        inquiry_type="booking_request",
        status="pending",
    )
    inquiry.unit = unit

    created_txs: dict[str, DepositTransaction] = {}
    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, DepositTransaction):
            created_txs[obj.reference_code] = obj

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()
        if "from rental_inquiries" in text_stmt:
            res.scalar_one_or_none.return_value = inquiry
            return res
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Approve inquiry and mint deposit
        resp = await client.post(f"/api/v1/rentals/inquiries/{inquiry_id}/approve-and-deposit")
        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == 3_500_000.0
        assert data["status"] == "pending"
        assert "img.vietqr.io" in data["vietqr_url"]
        assert "reference_code" in data
        assert len(created_txs) == 1

        # 2. Re-attempting when unit occupied/reserved gives 400 Bad Request
        unit.status = "reserved"
        resp_occupied = await client.post(f"/api/v1/rentals/inquiries/{inquiry_id}/approve-and-deposit")
        assert resp_occupied.status_code == 400

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_payment_webhook_and_auto_reserve(host_user: User, tenant_user: User):
    unit_id = uuid.UUID("56565656-5656-5656-5656-565656565656")
    unit = RentalUnit(
        id=unit_id,
        property_id=uuid.uuid4(),
        unit_number="P.404",
        price=4_200_000.0,
        status="available",
        area_sqm=28.0,
    )

    inquiry_id = uuid.UUID("78787878-7878-7878-7878-787878787878")
    inquiry = RentalInquiry(
        id=inquiry_id,
        unit_id=unit_id,
        tenant_id=tenant_user.id,
        host_id=host_user.id,
        status="pending",
    )

    ref_code = "SP247_TEST_WEBHOOK_123"
    tx = DepositTransaction(
        id=uuid.uuid4(),
        unit_id=unit_id,
        inquiry_id=inquiry_id,
        tenant_id=tenant_user.id,
        host_id=host_user.id,
        amount=4_200_000.0,
        reference_code=ref_code,
        payment_method="vietqr",
        vietqr_url=f"https://img.vietqr.io/image/970422-0987654321-compact2.png?amount=4200000&addInfo={ref_code}",
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    notifications_dispatched = []
    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, UserNotification):
            notifications_dispatched.append(obj)

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()
        if "from deposit_transactions" in text_stmt:
            res.scalar_one_or_none.return_value = tx
            return res
        if "from rental_units" in text_stmt:
            res.scalar_one_or_none.return_value = unit
            return res
        if "from rental_inquiries" in text_stmt:
            res.scalar_one_or_none.return_value = inquiry
            return res
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Successful Webhook IPN
        webhook_body = {
            "provider": "vietqr",
            "reference_code": ref_code,
            "amount": 4_200_000.0,
            "status": "success",
        }
        wh_resp = await client.post("/api/v1/payments/webhook/vietqr", json=webhook_body)
        assert wh_resp.status_code == 200
        wh_data = wh_resp.json()
        assert wh_data["status"] == "success"
        assert wh_data["transaction_status"] == "success"

        # Assert atomic mutations:
        assert tx.status == "success"
        assert unit.status == RentalUnitStatus.RESERVED.value
        assert inquiry.status == "confirmed"
        # Assert notifications sent to both tenant and host
        assert len(notifications_dispatched) == 2
        types = {n.notification_type for n in notifications_dispatched}
        assert "deposit_success" in types
        assert "deposit_received" in types

        # 2. Idempotent check: repeating webhook returns 200 with no errors
        wh_repeat_resp = await client.post("/api/v1/payments/webhook/vietqr", json=webhook_body)
        assert wh_repeat_resp.status_code == 200

        # 3. Polling endpoint
        poll_resp = await client.get(f"/api/v1/payments/deposit-transactions/{ref_code}")
        assert poll_resp.status_code == 200
        assert poll_resp.json()["status"] == "success"

    app.dependency_overrides.clear()


def test_ai_living_cost_calculation_tool():
    # Unit test for calculate_total_living_cost tool
    breakdown = ChatAssistantService.calculate_total_living_cost(
        occupants=2,
        room_price=4_000_000.0,
        electricity_kwh=150.0,
        water_usage=4.0,
        property_costs={
            "electricity_per_kwh": 3800.0,
            "water_cost": 25000.0,
            "water_unit": "m3",
            "service_fee_monthly": 150000.0,
            "parking_fee_monthly": 100000.0,
        },
    )

    # Math verification:
    # Room: 4,000,000
    # Electricity: 150 * 3800 = 570,000
    # Water: 4.0 * 25000 = 100,000
    # Service: 150,000
    # Parking: 2 * 100000 = 200,000
    # Total: 4,000,000 + 570,000 + 100,000 + 150,000 + 200,000 = 5,020,000
    # Cost per person: 5,020,000 / 2 = 2,510,000
    assert breakdown.room_price == 4_000_000.0
    assert breakdown.occupants == 2
    assert breakdown.total_monthly_cost == 5_020_000.0
    assert breakdown.cost_per_person == 2_510_000.0
    assert "| 🏠 Tiền phòng |" in breakdown.summary
    assert "| ⚡ Tiền điện |" in breakdown.summary
    assert len(breakdown.items) == 5


@pytest.mark.asyncio
async def test_ai_living_cost_conversational_response():
    service = ChatAssistantService()
    user_query = "Căn này 2 người ở với 150 kwh điện thì mỗi tháng hết bao nhiêu tiền sinh hoạt?"
    messages = [ChatMessage(role="user", content=user_query)]

    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is True

    msg, suggestions = service.generate_natural_response(criteria=criteria, properties=[], is_search=True)
    assert "chi phí sinh hoạt hàng tháng" in msg.lower()
    assert "tiền phòng" in msg.lower()
    assert len(suggestions) > 0

    detected_lc = service.detect_and_calculate_living_cost(messages)
    assert detected_lc is not None
    assert detected_lc.occupants == 2
    assert detected_lc.electricity_kwh == 150.0


@pytest.mark.asyncio
async def test_list_host_invoices_filtering_and_status_alias(host_user: User):
    invoices_db: dict[uuid.UUID, MonthlyInvoice] = {}

    inv1 = MonthlyInvoice(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
        host_id=host_user.id,
        tenant_id=uuid.uuid4(),
        billing_month="2026-09",
        room_amount=4_000_000.0,
        electricity_previous_index=100.0,
        electricity_current_index=150.0,
        electricity_rate=3500.0,
        electricity_amount=175_000.0,
        water_rate=20000.0,
        water_amount=80_000.0,
        service_amount=100_000.0,
        total_amount=4_355_000.0,
        status="pending",
        due_date=datetime.now(timezone.utc) + timedelta(days=5),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    inv2 = MonthlyInvoice(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
        host_id=host_user.id,
        tenant_id=uuid.uuid4(),
        billing_month="2026-08",
        room_amount=4_000_000.0,
        electricity_previous_index=50.0,
        electricity_current_index=100.0,
        electricity_rate=3500.0,
        electricity_amount=175_000.0,
        water_rate=20000.0,
        water_amount=80_000.0,
        service_amount=100_000.0,
        total_amount=4_355_000.0,
        status="paid",
        due_date=datetime.now(timezone.utc) - timedelta(days=20),
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        updated_at=datetime.now(timezone.utc) - timedelta(days=25),
    )
    invoices_db[inv1.id] = inv1
    invoices_db[inv2.id] = inv2

    mock_db = AsyncMock()

    async def mock_execute(stmt, *args, **kwargs):
        res = MagicMock()
        items = list(invoices_db.values())
        params = getattr(stmt.compile(), "params", {})
        status_val = next((v for k, v in params.items() if "status" in k), None)
        month_val = next((v for k, v in params.items() if "month" in k), None)
        if status_val:
            items = [i for i in items if i.status == status_val]
        if month_val:
            items = [i for i in items if i.billing_month == month_val]
        res.scalars.return_value.all.return_value = items
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test listing with status alias query parameter
        resp = await client.get("/api/v1/host/invoices?status=pending")
        assert resp.status_code == 200
        invoices = resp.json()
        assert len(invoices) == 1
        assert invoices[0]["status"] == "pending"

        # Test listing with billing_month
        resp_month = await client.get("/api/v1/host/invoices?billing_month=2026-09")
        assert resp_month.status_code == 200
        invoices_month = resp_month.json()
        assert len(invoices_month) == 1
        assert invoices_month[0]["billing_month"] == "2026-09"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_assistant_living_cost_endpoint_payload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Phòng trọ này 2 người ở với 120 kwh điện thì mỗi tháng tổng chi phí sinh hoạt hết khoảng bao nhiêu tiền?",
                }
            ],
            "limit": 3,
        }
        resp = await client.post("/api/v1/chat/assistant", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "living_cost" in data
        assert data["living_cost"] is not None
        lc = data["living_cost"]
        assert lc["occupants"] == 2
        assert lc["electricity_kwh"] == 120.0
        assert lc["total_monthly_cost"] > 0
        assert lc["cost_per_person"] > 0
        assert len(lc["items"]) > 0


@pytest.mark.asyncio
async def test_deposit_transaction_auto_expiration():
    ref_code = "DEPEXPIRED12345"
    expired_tx = DepositTransaction(
        id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        host_id=uuid.uuid4(),
        amount=2_000_000.0,
        reference_code=ref_code,
        vietqr_url="https://img.vietqr.io/image/970422-0987654321-compact2.png",
        status="pending",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),  # in the past
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )

    mock_db = AsyncMock()

    async def mock_execute(stmt, *args, **kwargs):
        res = MagicMock()
        res.scalar_one_or_none.return_value = expired_tx
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(f"/api/v1/payments/deposit-transactions/{ref_code}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "expired"
        assert expired_tx.status == "expired"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invoice_generation_per_person_water_billing(host_user: User):
    contract_id = uuid.uuid4()
    unit_id = uuid.uuid4()

    unit = RentalUnit(
        id=unit_id,
        property_id=uuid.uuid4(),
        unit_number="P.303",
        area_sqm=35.0,
        price=6_000_000.0,
        status="occupied",
        max_occupants=3,
    )
    contract = RentalContract(
        id=contract_id,
        unit_id=unit.id,
        property_id=unit.property_id,
        host_id=host_user.id,
        tenant_id=uuid.uuid4(),
        tenant_name="Khách Hàng C",
        tenant_phone="0911333444",
        start_date=datetime.now(timezone.utc),
        rental_price=6_000_000.0,
        deposit_amount=6_000_000.0,
        electricity_rate=3500.0,
        water_rate=60000.0,  # 60,000 đ/person
        water_billing_type="per_person",
        service_fee=200000.0,
        status="active",
    )
    contract.unit = unit

    invoices_created: list[MonthlyInvoice] = []
    mock_db = AsyncMock()

    def mock_add(obj):
        print("MOCK_ADD_CALLED:", type(obj), obj)
        if isinstance(obj, MonthlyInvoice):
            invoices_created.append(obj)
            obj.unit = unit
            obj.contract = contract

    mock_db.add = mock_add

    async def mock_execute(stmt, *args, **kwargs):
        res = MagicMock()
        stmt_str = str(stmt).lower()
        if "from monthly_invoices" in stmt_str:
            if "where monthly_invoices.contract_id" in stmt_str or "contract_id = :" in stmt_str:
                res.scalar_one_or_none.return_value = None
                return res
            res.scalars.return_value.all.return_value = list(invoices_created)
            return res
        if "rental_contracts" in stmt_str:
            res.scalar_one_or_none.return_value = contract
            return res
        res.scalar_one_or_none.return_value = None
        return res

    mock_db.execute = mock_execute

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_host_user] = lambda: host_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req_payload = {
            "billing_month": "2026-09",
            "due_days": 5,
            "readings": [
                {
                    "contract_id": str(contract_id),
                    "electricity_previous": 0.0,
                    "electricity_current": 100.0,
                    "water_previous": 0.0,
                    "water_current": 0.0,
                }
            ],
        }
        gen_resp = await client.post("/api/v1/host/invoices/generate-monthly", json=req_payload)
        assert gen_resp.status_code == 201
        invoices = gen_resp.json()
        assert len(invoices) == 1
        # Water calculation: 60,000 * 3 occupants = 180,000
        assert invoices[0]["water_amount"] == 180_000.0
        # Total: 6,000,000 + 350,000 + 180,000 + 200,000 = 6,730,000
        assert invoices[0]["total_amount"] == 6_730_000.0

    app.dependency_overrides.clear()
