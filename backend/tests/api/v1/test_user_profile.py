from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.main import create_app
from src.core.database import get_db_session
from src.api.deps import get_current_active_user, get_current_user
from src.core.security import hash_password, verify_password
from src.models.user import User, UserRole


@pytest.fixture
def current_test_user():
    return User(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        email="test.user@space247.vn",
        hashed_password=hash_password("OldPassword123@"),
        full_name="Nguyễn Văn Test",
        phone="0911223344",
        role=UserRole.USER.value,
        is_active=True,
        phone_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_my_profile(current_test_user):
    app = create_app()
    mock_session = AsyncMock()

    # Mock count queries for properties, favorites, and alerts
    count_result = MagicMock()
    count_result.scalar.return_value = 5
    mock_session.execute.return_value = count_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: current_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/users/me")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "test.user@space247.vn"
        assert data["full_name"] == "Nguyễn Văn Test"
        assert data["role"] == "user"
        assert data["phone_verified"] is True
        assert data["total_properties"] == 5
        assert data["total_favorites"] == 5
        assert data["total_alerts"] == 5


@pytest.mark.asyncio
async def test_update_my_profile(current_test_user):
    app = create_app()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: current_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "full_name": "Nguyễn Văn Đã Đổi Tên",
            "phone": "0999888777",
            "avatar_url": "https://example.com/new-avatar.jpg",
        }
        res = await client.put("/api/v1/users/me", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["full_name"] == "Nguyễn Văn Đã Đổi Tên"
        assert data["phone"] == "0999888777"
        assert current_test_user.full_name == "Nguyễn Văn Đã Đổi Tên"
        assert current_test_user.phone == "0999888777"


@pytest.mark.asyncio
async def test_change_password_success(current_test_user):
    app = create_app()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: current_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "old_password": "OldPassword123@",
            "new_password": "NewSuperSecretPassword456@",
        }
        res = await client.post("/api/v1/users/me/change-password", json=payload)
        assert res.status_code == 200
        assert "thành công" in res.json()["message"]
        # Verify password hash updated
        assert verify_password("NewSuperSecretPassword456@", current_test_user.hashed_password)


@pytest.mark.asyncio
async def test_change_password_invalid_old_password(current_test_user):
    app = create_app()
    mock_session = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: current_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "old_password": "WrongPassword!",
            "new_password": "NewSuperSecretPassword456@",
        }
        res = await client.post("/api/v1/users/me/change-password", json=payload)
        assert res.status_code == 400
        assert "không chính xác" in res.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_too_short(current_test_user):
    app = create_app()
    mock_session = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: current_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "old_password": "OldPassword123@",
            "new_password": "short",
        }
        res = await client.post("/api/v1/users/me/change-password", json=payload)
        assert res.status_code == 422
