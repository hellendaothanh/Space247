import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.core.database import get_db_session
from src.api.deps import get_current_host_user, get_current_active_user
from src.models.user import User, UserRole
from src.models.rental_property import RentalProperty, RentalUnit, RentalInquiry


@pytest.fixture
def host_user() -> User:
    return User(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        email="host@space247.vn",
        hashed_password="fakehashpassword",
        full_name="Chủ Nhà Nguyễn Văn An",
        phone="0912345678",
        role=UserRole.HOST.value,
        is_active=True,
    )


@pytest.fixture
def tenant_user() -> User:
    return User(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        email="tenant@space247.vn",
        hashed_password="fakehashpassword",
        full_name="Khách Thuê Trần Thị Bình",
        phone="0987654321",
        role=UserRole.USER.value,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_host_property_and_unit_lifecycle(host_user: User, tenant_user: User):
    # In-memory storage for test objects
    properties_db: dict[uuid.UUID, RentalProperty] = {}
    units_db: dict[uuid.UUID, RentalUnit] = {}
    inquiries_db: dict[uuid.UUID, RentalInquiry] = {}

    current_user_holder = [host_user]

    mock_db = AsyncMock()

    def mock_add(obj):
        if isinstance(obj, RentalProperty):
            properties_db[obj.id] = obj
        elif isinstance(obj, RentalUnit):
            units_db[obj.id] = obj
            if obj.property_id in properties_db:
                prop = properties_db[obj.property_id]
                if obj not in prop.units:
                    prop.units.append(obj)
        elif isinstance(obj, RentalInquiry):
            inquiries_db[obj.id] = obj

    mock_db.add = mock_add
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        text_stmt = str(stmt).lower()

        # Count queries
        if "count(rental_properties.id)" in text_stmt:
            res.scalar.return_value = len(properties_db)
            return res
        if "count(rental_inquiries.id)" in text_stmt:
            res.scalar.return_value = len([i for i in inquiries_db.values() if i.status == "pending"])
            return res

        # Units queries
        if "from rental_units" in text_stmt:
            # Check if filtering by specific unit ID
            params = getattr(stmt.compile(), "params", {})
            for val in params.values():
                if isinstance(val, uuid.UUID) and val in units_db:
                    u = units_db[val]
                    u.property = properties_db.get(u.property_id)
                    res.scalar_one_or_none.return_value = u
                    return res
            # Return all units
            res.scalars.return_value.all.return_value = list(units_db.values())
            return res

        # Inquiries queries
        if "from rental_inquiries" in text_stmt:
            params = getattr(stmt.compile(), "params", {})
            for val in params.values():
                if isinstance(val, uuid.UUID) and val in inquiries_db:
                    inq = inquiries_db[val]
                    inq.unit = units_db.get(inq.unit_id)
                    res.scalar_one_or_none.return_value = inq
                    return res
            res.scalars.return_value.all.return_value = list(inquiries_db.values())
            return res

        # Properties queries
        if "from rental_properties" in text_stmt:
            params = getattr(stmt.compile(), "params", {})
            for val in params.values():
                if isinstance(val, uuid.UUID) and val in properties_db:
                    p = properties_db[val]
                    p.units = [u for u in units_db.values() if u.property_id == p.id]
                    p.host = host_user
                    res.scalar_one_or_none.return_value = p
                    res.scalar_one.return_value = p
                    return res
            all_props = list(properties_db.values())
            for p in all_props:
                p.units = [u for u in units_db.values() if u.property_id == p.id]
                p.host = host_user
            res.scalars.return_value.all.return_value = all_props
            return res

        res.scalars.return_value.all.return_value = []
        res.scalar_one_or_none.return_value = None
        return res

    mock_db.execute = mock_execute

    async def override_get_db():
        yield mock_db

    async def override_get_host_user():
        return current_user_holder[0]

    async def override_get_active_user():
        return current_user_holder[0]

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_host_user] = override_get_host_user
    app.dependency_overrides[get_current_active_user] = override_get_active_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Host creates rental property
        current_user_holder[0] = host_user
        create_payload = {
            "name": "Nhà Trọ Xanh Bách Khoa",
            "description": "Khu trọ an ninh sinh viên",
            "property_model": "boarding_house",
            "address": "Số 10 Tạ Quang Bửu",
            "district": "Hai Bà Trưng",
            "city": "Hà Nội",
            "latitude": 21.0056,
            "longitude": 105.8433,
            "shared_costs": {"electricity_per_kwh": 3500, "water_cost": 30000},
            "shared_rules": {"curfew": False, "allow_pets": True},
            "images": ["https://example.com/prop.jpg"],
            "initial_units": [
                {
                    "unit_number": "P.101",
                    "floor": 1,
                    "area_sqm": 25.0,
                    "price": 3500000.0,
                    "deposit": 3500000.0,
                    "status": "available",
                    "furnishing": "full",
                    "has_mezzanine": True,
                    "has_private_bathroom": True,
                    "max_occupants": 2,
                }
            ],
        }
        res = await client.post("/api/v1/host/properties", json=create_payload)
        assert res.status_code == 201, res.text
        prop_data = res.json()
        prop_id = uuid.UUID(prop_data["id"])
        unit1_id = uuid.UUID(prop_data["units"][0]["id"])
        assert prop_data["name"] == "Nhà Trọ Xanh Bách Khoa"
        assert prop_data["total_units_count"] == 1

        # 2. Host adds a second unit
        unit2_payload = {
            "unit_number": "P.102",
            "floor": 1,
            "area_sqm": 20.0,
            "price": 2800000.0,
            "deposit": 2800000.0,
            "status": "available",
            "furnishing": "basic",
            "has_mezzanine": False,
            "has_private_bathroom": True,
            "max_occupants": 1,
        }
        unit2_res = await client.post(f"/api/v1/host/properties/{prop_id}/units", json=unit2_payload)
        assert unit2_res.status_code == 201
        unit2_id = uuid.UUID(unit2_res.json()["id"])

        # 3. Host dashboard stats
        stats_res = await client.get("/api/v1/host/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_properties"] == 1
        assert stats["total_units"] == 2
        assert stats["available_units"] == 2

        # 4. Host 1-click toggles status of unit 2 to occupied
        patch_res = await client.patch(
            f"/api/v1/host/units/{unit2_id}/status",
            json={"status": "occupied"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "occupied"

        # Re-check stats: 1 occupied, 1 available, monthly revenue calculated
        stats_res2 = await client.get("/api/v1/host/stats")
        stats2 = stats_res2.json()
        assert stats2["available_units"] == 1
        assert stats2["occupied_units"] == 1
        assert stats2["estimated_monthly_revenue"] == 2800000.0

        # 5. Tenant discovers rentals via /api/v1/rentals
        current_user_holder[0] = tenant_user
        rentals_res = await client.get("/api/v1/rentals")
        assert rentals_res.status_code == 200
        items = rentals_res.json()
        assert len(items) == 1
        assert items[0]["name"] == "Nhà Trọ Xanh Bách Khoa"
        assert items[0]["available_units_count"] == 1

        # 6. Tenant books viewing appointment on unit 1
        inq_payload = {
            "inquiry_type": "view_appointment",
            "scheduled_time": "2026-09-10T14:00:00Z",
            "tenant_name": "Trần Thị Bình",
            "tenant_phone": "0987654321",
            "message": "Em muốn qua xem phòng vào chiều mai lúc 14h ạ",
        }
        inq_res = await client.post(f"/api/v1/rentals/units/{unit1_id}/inquire", json=inq_payload)
        assert inq_res.status_code == 201
        inq_data = inq_res.json()
        assert inq_data["status"] == "pending"
        inq_id = inq_data["id"]

        # 7. Tenant views my inquiries
        my_inq_res = await client.get("/api/v1/rentals/my-inquiries")
        assert my_inq_res.status_code == 200
        assert len(my_inq_res.json()) == 1

        # 8. Host confirms viewing appointment
        current_user_holder[0] = host_user
        host_inq_res = await client.get("/api/v1/host/inquiries")
        assert host_inq_res.status_code == 200
        assert len(host_inq_res.json()) == 1

        confirm_res = await client.patch(
            f"/api/v1/host/inquiries/{inq_id}/status",
            json={"status": "confirmed"},
        )
        assert confirm_res.status_code == 200
        assert confirm_res.json()["status"] == "confirmed"

        # 9. Tenant cannot book on already occupied unit
        current_user_holder[0] = tenant_user
        bad_inquire = await client.post(f"/api/v1/rentals/units/{unit2_id}/inquire", json=inq_payload)
        assert bad_inquire.status_code == 400
        assert "đã có người thuê" in bad_inquire.json()["detail"]

    app.dependency_overrides.clear()
