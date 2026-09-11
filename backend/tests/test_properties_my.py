from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_current_active_user, get_db_session
from src.core.security import create_access_token
from src.main import app
from src.models.property import Property
from src.models.user import User
from src.schemas.property import PropertyStatus


@pytest.mark.asyncio
async def test_get_my_properties_unauthorized():
    """Accessing /properties/my without Bearer token must return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/properties/my")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_my_properties_success_and_filtering():
    """Authenticated user only sees their own listings, with status filtering."""
    user_id_1 = uuid.uuid4()
    user_1 = User(
        id=user_id_1,
        email="owner1@space247.vn",
        hashed_password="hash",
        full_name="Owner One",
        role="agent",
        is_active=True,
    )

    prop1 = Property(
        id=uuid.uuid4(),
        title="Listing of User 1 - Active",
        description="Mô tả căn hộ trung tâm",
        property_type="apartment",
        listing_type="sale",
        price=3500000000.0,
        currency="VND",
        area_sqm=75.0,
        address="123 Nguyễn Trãi",
        city="Hà Nội",
        status="active",
        user_id=user_id_1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    prop2 = Property(
        id=uuid.uuid4(),
        title="Listing of User 1 - Inactive",
        description="Mô tả căn hộ đã bán",
        property_type="apartment",
        listing_type="sale",
        price=4000000000.0,
        currency="VND",
        area_sqm=80.0,
        address="125 Nguyễn Trãi",
        city="Hà Nội",
        status="inactive",
        user_id=user_id_1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_session = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        try:
            params = stmt.compile().params
            bind_vals = [str(v).lower() for v in params.values()]
        except Exception:
            bind_vals = []

        if any("inactive" in v for v in bind_vals):
            res.scalars.return_value.all.return_value = [prop2]
        elif any("active" in v for v in bind_vals):
            res.scalars.return_value.all.return_value = [prop1]
        else:
            res.scalars.return_value.all.return_value = [prop1, prop2]
        return res

    mock_session.execute = mock_execute

    async def override_get_db():
        yield mock_session

    async def override_get_current_user():
        return user_1

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    token = create_access_token(subject=str(user_id_1))
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch all my properties
        resp = await client.get("/api/v1/properties/my", headers=headers)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2
        assert items[0]["title"] == "Listing of User 1 - Active"

        # 2. Filter by status=inactive
        resp_inactive = await client.get("/api/v1/properties/my?status=inactive", headers=headers)
        assert resp_inactive.status_code == 200
        items_inactive = resp_inactive.json()
        assert len(items_inactive) == 1
        assert items_inactive[0]["status"] == "inactive"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_and_delete_property_ownership():
    """Ensure non-owner cannot update or delete property, while owner and admin can."""
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    owner_user = User(
        id=owner_id,
        email="owner@space247.vn",
        hashed_password="hash",
        full_name="Owner User",
        role="user",
        is_active=True,
    )
    other_user = User(
        id=other_user_id,
        email="stranger@space247.vn",
        hashed_password="hash",
        full_name="Stranger User",
        role="user",
        is_active=True,
    )
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@space247.vn",
        hashed_password="hash",
        full_name="Admin User",
        role="admin",
        is_active=True,
    )

    prop = Property(
        id=uuid.uuid4(),
        title="Owner Exclusive Listing",
        description="Chi tiết căn hộ độc quyền của chủ sở hữu",
        property_type="apartment",
        listing_type="sale",
        price=5000000000.0,
        currency="VND",
        area_sqm=90.0,
        address="100 Phố Huế",
        city="Hà Nội",
        status="active",
        user_id=owner_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_session = AsyncMock()

    async def mock_execute(stmt):
        res = MagicMock()
        res.scalar_one_or_none.return_value = prop
        return res

    mock_session.execute = mock_execute
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthenticated update & delete -> 401
        app.dependency_overrides.pop(get_current_active_user, None)
        unauth_put = await client.put(f"/api/v1/properties/{prop.id}", json={"title": "No Auth"})
        assert unauth_put.status_code == 401

        unauth_del = await client.delete(f"/api/v1/properties/{prop.id}")
        assert unauth_del.status_code == 401

        # 2. Other user tries to update -> 403
        app.dependency_overrides[get_current_active_user] = lambda: other_user

        resp = await client.put(f"/api/v1/properties/{prop.id}", json={"title": "Hack Title"})
        assert resp.status_code == 403

        # 3. Other user tries to delete -> 403
        del_resp = await client.delete(f"/api/v1/properties/{prop.id}")
        assert del_resp.status_code == 403

        # 4. Owner updates -> 200
        app.dependency_overrides[get_current_active_user] = lambda: owner_user
        owner_resp = await client.put(f"/api/v1/properties/{prop.id}", json={"title": "Updated Title By Owner"})
        assert owner_resp.status_code == 200

        # 5. Owner deletes -> 204
        owner_del_resp = await client.delete(f"/api/v1/properties/{prop.id}")
        assert owner_del_resp.status_code == 204

        # 6. Admin can delete -> 204
        app.dependency_overrides[get_current_active_user] = lambda: admin_user
        admin_del_resp = await client.delete(f"/api/v1/properties/{prop.id}")
        assert admin_del_resp.status_code == 204

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_my_listings_dashboard_kpis_and_pagination():
    """Verify GET /properties/my-listings computes KPI stats, filters by status, and paginates correctly."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="lister@space247.vn",
        hashed_password="hash",
        full_name="Listing Pro",
        role="agent",
        is_active=True,
    )

    prop_active = Property(
        id=uuid.uuid4(),
        title="Active Apartment Listing",
        description="Mô tả căn hộ trung tâm 1",
        property_type="apartment",
        listing_type="sale",
        price=4500000000.0,
        currency="VND",
        area_sqm=80.0,
        address="12 Hoàn Kiếm",
        city="Hà Nội",
        status="active",
        is_visible=True,
        view_count=120,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        refreshed_at=datetime.now(timezone.utc),
    )

    prop_hidden = Property(
        id=uuid.uuid4(),
        title="Hidden Property",
        description="Mô tả căn hộ tạm ẩn",
        property_type="house",
        listing_type="rent",
        price=15000000.0,
        currency="VND",
        area_sqm=50.0,
        address="34 Cầu Giấy",
        city="Hà Nội",
        status="hidden",
        is_visible=False,
        view_count=50,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        refreshed_at=datetime.now(timezone.utc),
    )

    mock_session = AsyncMock()

    # 1. all_props_res
    all_props_mock = MagicMock()
    all_props_mock.scalars.return_value.all.return_value = [prop_active, prop_hidden]

    # 2. fav_count_res
    fav_mock = MagicMock()
    fav_mock.scalar.return_value = 8

    # 3. count_res (filtered)
    count_mock = MagicMock()
    count_mock.scalar.return_value = 2

    # 4. paged_res
    paged_mock = MagicMock()
    paged_mock.scalars.return_value.all.return_value = [prop_active, prop_hidden]

    # 5. p_fav_res (per property favorites)
    p_fav_mock = MagicMock()
    p_fav_mock.all.return_value = [(prop_active.id, 5), (prop_hidden.id, 3)]

    mock_session.execute.side_effect = [all_props_mock, fav_mock, count_mock, paged_mock, p_fav_mock]

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user

    token = create_access_token(subject=str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/properties/my-listings?page=1&page_size=10", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        stats = data["stats"]
        assert stats["total_listings"] == 2
        assert stats["active_listings"] == 1
        assert stats["hidden_listings"] == 1
        assert stats["total_views"] == 170
        assert stats["total_favorites"] == 8

        # First item has favorites_count 5
        assert data["items"][0]["favorites_count"] == 5

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_my_listings_actions():
    """Verify toggle-visibility, mark-sold, and refresh endpoints."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="owner_actions@space247.vn",
        hashed_password="hash",
        full_name="Action Owner",
        role="agent",
        is_active=True,
    )

    prop = Property(
        id=uuid.uuid4(),
        title="Action Test Property",
        description="Mô tả căn hộ để test action",
        property_type="apartment",
        listing_type="sale",
        price=3000000000.0,
        currency="VND",
        area_sqm=65.0,
        address="99 Phố Huế",
        city="Hà Nội",
        status="active",
        is_visible=True,
        view_count=10,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        refreshed_at=datetime.now(timezone.utc),
    )

    mock_session = AsyncMock()

    def get_scalar():
        m = MagicMock()
        m.scalar_one_or_none.return_value = prop
        return m

    mock_session.execute.side_effect = [get_scalar(), get_scalar(), get_scalar()]
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user

    token = create_access_token(subject=str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Toggle visibility -> switches to False and status='hidden'
        toggle_resp = await client.patch(f"/api/v1/properties/{prop.id}/toggle-visibility", headers=headers)
        assert toggle_resp.status_code == 200
        assert prop.is_visible is False
        assert prop.status == "hidden"

        # 2. Mark sold -> status='sold', is_visible=False
        sold_resp = await client.post(f"/api/v1/properties/{prop.id}/mark-sold", json={"status": "sold"}, headers=headers)
        assert sold_resp.status_code == 200
        assert prop.status == "sold"
        assert prop.is_visible is False

        # 3. Refresh listing -> refreshed_at updated
        refresh_resp = await client.post(f"/api/v1/properties/{prop.id}/refresh", headers=headers)
        assert refresh_resp.status_code == 200
        assert mock_session.commit.called

    app.dependency_overrides.clear()