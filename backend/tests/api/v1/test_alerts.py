from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_current_active_user, get_db_session
from src.main import app
from src.models.alert import SavedSearchAlert, UserNotification
from src.models.property import Property
from src.models.user import User
from src.schemas.alert import CreateAlertRequest
from src.services.alert_service import AlertService


@pytest.mark.asyncio
async def test_alerts_endpoints_unauthorized():
    """Endpoints for alerts and notifications require Bearer authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/v1/alerts without auth
        resp1 = await client.get("/api/v1/alerts")
        assert resp1.status_code == 401

        # POST /api/v1/alerts without auth
        resp2 = await client.post("/api/v1/alerts", json={"title": "Test", "criteria": {}})
        assert resp2.status_code == 401

        # GET /api/v1/notifications without auth
        resp3 = await client.get("/api/v1/notifications")
        assert resp3.status_code == 401


@pytest.mark.asyncio
async def test_alert_crud_lifecycle():
    """Verify full CRUD lifecycle for saved search alerts."""
    user = User(
        id=uuid.uuid4(),
        email="alert_user@space247.vn",
        hashed_password="hash",
        full_name="Alert Tester",
        role="user",
        is_active=True,
    )

    alert_id = uuid.uuid4()
    alert_record = SavedSearchAlert(
        id=alert_id,
        user_id=user.id,
        title="Chung cư Cầu Giấy 3-5 tỷ",
        criteria={"min_price": 3_000_000_000, "max_price": 5_000_000_000, "district": "Cầu Giấy"},
        frequency="instant",
        is_active=True,
    )

    mock_db = AsyncMock()

    # Setup mock returns
    def mock_execute(stmt):
        m = MagicMock()
        stmt_str = str(stmt).lower()
        if "select" in stmt_str:
            m.scalars.return_value.all.return_value = [alert_record]
            m.scalar_one_or_none.return_value = alert_record
        return m

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.delete = AsyncMock()

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Alert
        create_payload = {
            "title": "Chung cư Cầu Giấy 3-5 tỷ",
            "criteria": {
                "min_price": 3_000_000_000,
                "max_price": 5_000_000_000,
                "district": "Cầu Giấy",
            },
            "frequency": "instant",
        }
        resp_create = await client.post("/api/v1/alerts", json=create_payload)
        assert resp_create.status_code == 201
        data_create = resp_create.json()
        assert data_create["title"] == "Chung cư Cầu Giấy 3-5 tỷ"
        assert data_create["is_active"] is True

        # 2. List Alerts
        resp_list = await client.get("/api/v1/alerts")
        assert resp_list.status_code == 200
        data_list = resp_list.json()
        assert len(data_list) == 1
        assert data_list[0]["title"] == "Chung cư Cầu Giấy 3-5 tỷ"

        # 3. Get Alert by ID
        resp_get = await client.get(f"/api/v1/alerts/{alert_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["id"] == str(alert_id)

        # 4. Update Alert
        resp_update = await client.put(
            f"/api/v1/alerts/{alert_id}",
            json={"title": "Updated Title", "is_active": False},
        )
        assert resp_update.status_code == 200

        # 5. Delete Alert
        resp_del = await client.delete(f"/api/v1/alerts/{alert_id}")
        assert resp_del.status_code == 204

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_notifications_endpoints():
    """Verify listing and marking notifications as read."""
    user = User(
        id=uuid.uuid4(),
        email="notif_user@space247.vn",
        hashed_password="hash",
        full_name="Notif Tester",
        role="user",
        is_active=True,
    )

    notif_id = uuid.uuid4()
    notif = UserNotification(
        id=notif_id,
        user_id=user.id,
        title="Bất động sản mới phù hợp",
        message="Căn hộ Cầu Giấy 3.5 tỷ",
        notification_type="saved_search_match",
        is_read=False,
    )

    mock_db = AsyncMock()

    # Mock count queries and select queries
    call_count = 0

    def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        m = MagicMock()
        stmt_str = str(stmt).lower()
        if "count" in stmt_str:
            m.scalar_one.return_value = 1
        elif "update" in stmt_str:
            m.rowcount = 1
        else:
            m.scalars.return_value.all.return_value = [notif]
            m.scalar_one_or_none.return_value = notif
        return m

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List notifications
        resp_list = await client.get("/api/v1/notifications")
        assert resp_list.status_code == 200
        data = resp_list.json()
        assert data["total"] >= 1
        assert data["unread_count"] >= 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Bất động sản mới phù hợp"

        # 2. Mark specific notification as read
        resp_read = await client.patch(f"/api/v1/notifications/{notif_id}/read")
        assert resp_read.status_code == 200
        assert resp_read.json()["is_read"] is True

        # 3. Mark all read
        resp_all = await client.post("/api/v1/notifications/read-all")
        assert resp_all.status_code == 200
        assert resp_all.json()["success"] is True

        # 4. Delete notification
        resp_del = await client.delete(f"/api/v1/notifications/{notif_id}")
        assert resp_del.status_code == 204

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_alert_matching_engine_unit():
    """Verify criteria matching engine accurately evaluates properties against saved alerts."""
    user_owner = uuid.uuid4()
    user_searcher_1 = uuid.uuid4()
    user_searcher_2 = uuid.uuid4()
    user_searcher_mismatch = uuid.uuid4()

    prop = Property(
        id=uuid.uuid4(),
        user_id=user_owner,
        title="Bán căn hộ The Matrix One Mễ Trì",
        description="Căn hộ cao cấp view thoáng, 2 phòng ngủ đẹp",
        price=4_200_000_000,
        currency="VND",
        property_type="apartment",
        listing_type="sale",
        city="Hà Nội",
        district="Nam Từ Liêm",
        address="Mễ Trì, Nam Từ Liêm",
        num_bedrooms=2,
        area_sqm=78.5,
    )

    alert_service = AlertService()

    # Alert 1: Matching criteria (price 3-5B, Nam Từ Liêm, apartment) -> True
    alert_1 = SavedSearchAlert(
        id=uuid.uuid4(),
        user_id=user_searcher_1,
        title="Tìm chung cư Nam Từ Liêm 3-5 tỷ",
        criteria={
            "min_price": 3_000_000_000,
            "max_price": 5_000_000_000,
            "district": "Nam Từ Liêm",
            "property_type": "apartment",
            "listing_type": "sale",
            "min_bedrooms": 2,
        },
        is_active=True,
    )
    assert alert_service.match_property_to_alert(prop, alert_1) is True

    # Alert 2: Matching broad criteria (Hà Nội, price < 6B) -> True
    alert_2 = SavedSearchAlert(
        id=uuid.uuid4(),
        user_id=user_searcher_2,
        title="Nhà Hà Nội dưới 6 tỷ",
        criteria={"max_price": 6_000_000_000, "city": "Hà Nội"},
        is_active=True,
    )
    assert alert_service.match_property_to_alert(prop, alert_2) is True

    # Alert 3: Mismatched price (min_price 5B > 4.2B) -> False
    alert_mismatch_price = SavedSearchAlert(
        id=uuid.uuid4(),
        user_id=user_searcher_mismatch,
        title="Căn hộ cao cấp trên 5 tỷ",
        criteria={"min_price": 5_000_000_000},
        is_active=True,
    )
    assert alert_service.match_property_to_alert(prop, alert_mismatch_price) is False

    # Alert 4: Mismatched location (Quận 1, TP.HCM) -> False
    alert_mismatch_loc = SavedSearchAlert(
        id=uuid.uuid4(),
        user_id=user_searcher_mismatch,
        title="Căn hộ Quận 1",
        criteria={"district": "Quận 1"},
        is_active=True,
    )
    assert alert_service.match_property_to_alert(prop, alert_mismatch_loc) is False

    # Alert 5: Owner's own alert should NOT be notified -> False
    alert_owner = SavedSearchAlert(
        id=uuid.uuid4(),
        user_id=user_owner,
        title="Owner's personal alert",
        criteria={"min_price": 1_000_000_000},
        is_active=True,
    )
    assert alert_service.match_property_to_alert(prop, alert_owner) is False
