from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_current_active_user, get_db_session
from src.main import app
from src.models.favorite import FavoriteProperty
from src.models.property import Property
from src.models.user import User


@pytest.mark.asyncio
async def test_favorites_endpoints_unauthorized():
    """Accessing /properties/favorites or toggling favorite without Bearer token must return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET favorites
        resp1 = await client.get("/api/v1/properties/favorites")
        assert resp1.status_code == 401

        # POST favorite toggle
        dummy_id = uuid.uuid4()
        resp2 = await client.post(f"/api/v1/properties/{dummy_id}/favorite")
        assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_toggle_favorite_property_not_found():
    """Toggling a non-existent property returns 404."""
    user = User(
        id=uuid.uuid4(),
        email="test_fav@space247.vn",
        hashed_password="hash",
        full_name="Fav User",
        role="user",
        is_active=True,
    )

    mock_db = AsyncMock()
    # Property query returns None
    mock_prop_res = MagicMock()
    mock_prop_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_prop_res

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/api/v1/properties/{uuid.uuid4()}/favorite")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_toggle_favorite_add_and_remove_cycle():
    """Toggling favorite adds when missing, and deletes when existing."""
    user = User(
        id=uuid.uuid4(),
        email="fav_cycle@space247.vn",
        hashed_password="hash",
        full_name="Cycle User",
        role="user",
        is_active=True,
    )
    property_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Step 1: Property exists, existing favorite is None -> Adds favorite
    mock_prop_res = MagicMock()
    mock_prop_res.scalar_one_or_none.return_value = property_id

    mock_fav_empty = MagicMock()
    mock_fav_empty.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_prop_res, mock_fav_empty]

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Add favorite
        resp_add = await client.post(f"/api/v1/properties/{property_id}/favorite")
        assert resp_add.status_code == 200
        data_add = resp_add.json()
        assert data_add["is_favorite"] is True
        assert data_add["property_id"] == str(property_id)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

        # Step 2: Property exists, existing favorite is Present -> Removes favorite
        existing_fav = FavoriteProperty(user_id=user.id, property_id=property_id)
        mock_fav_present = MagicMock()
        mock_fav_present.scalar_one_or_none.return_value = existing_fav

        mock_db.reset_mock()
        mock_db.execute.side_effect = [mock_prop_res, mock_fav_present]

        resp_remove = await client.post(f"/api/v1/properties/{property_id}/favorite")
        assert resp_remove.status_code == 200
        data_remove = resp_remove.json()
        assert data_remove["is_favorite"] is False
        assert data_remove["property_id"] == str(property_id)
        mock_db.delete.assert_called_once_with(existing_fav)
        mock_db.flush.assert_called_once()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_favorite_properties_list():
    """GET /properties/favorites returns list of properties favorited by user."""
    user = User(
        id=uuid.uuid4(),
        email="fav_list@space247.vn",
        hashed_password="hash",
        full_name="List User",
        role="user",
        is_active=True,
    )

    prop = Property(
        id=uuid.uuid4(),
        title="Biệt thự Thảo Điền Quận 2",
        description="Mô tả biệt thự đẳng cấp ven sông",
        property_type="villa",
        listing_type="sale",
        price=45000000000.0,
        currency="VND",
        area_sqm=350.0,
        num_bedrooms=5,
        num_bathrooms=6,
        address="12 Đường số 10",
        ward="Thảo Điền",
        district="Quận 2",
        city="TP. Hồ Chí Minh",
        status="active",
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [prop]
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/properties/favorites")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(prop.id)
        assert data[0]["title"] == "Biệt thự Thảo Điền Quận 2"

    app.dependency_overrides.clear()
