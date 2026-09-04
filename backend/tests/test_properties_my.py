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