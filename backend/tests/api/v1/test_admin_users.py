from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.main import create_app
from src.core.database import get_db_session
from src.api.deps import get_current_active_user, get_current_user
from src.core.security import hash_password
from src.models.user import User, UserRole


@pytest.fixture
def superadmin_user():
    return User(
        id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        email="superadmin@space247.vn",
        hashed_password=hash_password("Password123@"),
        full_name="Super Admin Space247",
        phone="0900000001",
        role=UserRole.SUPERADMIN.value,
        is_active=True,
        phone_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def regular_user():
    return User(
        id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
        email="regular@space247.vn",
        hashed_password=hash_password("Password123@"),
        full_name="Regular User",
        phone="0912345678",
        role=UserRole.USER.value,
        is_active=True,
        phone_verified=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def agent_user():
    return User(
        id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
        email="agent@space247.vn",
        hashed_password=hash_password("Password123@"),
        full_name="Agent User",
        phone="0988889999",
        role=UserRole.AGENT.value,
        is_active=True,
        phone_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_admin_users_unauthenticated():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/users")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_users_forbidden_for_regular_user(regular_user):
    app = create_app()
    mock_session = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: regular_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/users")
        assert res.status_code == 403
        assert "quyền truy cập cấp cao" in res.json()["detail"]


@pytest.mark.asyncio
async def test_admin_users_forbidden_for_agent(agent_user):
    app = create_app()
    mock_session = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: agent_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/users")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_list_users(superadmin_user, regular_user):
    app = create_app()
    mock_session = AsyncMock()

    count_result = MagicMock()
    count_result.scalar.return_value = 2

    scalars_result = MagicMock()
    scalars_result.all.return_value = [superadmin_user, regular_user]

    list_result = MagicMock()
    list_result.scalars.return_value = scalars_result

    mock_session.execute.side_effect = [count_result, list_result]

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/users?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["email"] == "superadmin@space247.vn"
        assert data["items"][1]["email"] == "regular@space247.vn"


@pytest.mark.asyncio
async def test_superadmin_create_user(superadmin_user):
    app = create_app()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Existing check returns None
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = existing_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "email": "new.agent@space247.vn",
            "password": "InitialPassword123@",
            "full_name": "New Agent",
            "phone": "0933334444",
            "role": "agent",
            "is_active": True,
            "phone_verified": True,
        }
        res = await client.post("/api/v1/admin/users", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "new.agent@space247.vn"
        assert data["role"] == "agent"
        assert data["phone_verified"] is True


@pytest.mark.asyncio
async def test_superadmin_update_user(superadmin_user, regular_user):
    app = create_app()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Query for target user returns regular_user
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = regular_user
    mock_session.execute.return_value = user_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "role": "agent",
            "phone_verified": True,
            "reset_password": "NewAgentPassword123@",
        }
        res = await client.put(f"/api/v1/admin/users/{regular_user.id}", json=payload)
        assert res.status_code == 200
        assert regular_user.role == "agent"
        assert regular_user.phone_verified is True


@pytest.mark.asyncio
async def test_superadmin_soft_delete_user(superadmin_user, regular_user):
    app = create_app()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = regular_user
    mock_session.execute.return_value = user_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.delete(f"/api/v1/admin/users/{regular_user.id}")
        assert res.status_code == 200
        assert "vô hiệu hóa" in res.json()["message"]
        # Soft-deleted: is_active set to False
        assert regular_user.is_active is False


@pytest.mark.asyncio
async def test_superadmin_cannot_self_delete(superadmin_user):
    app = create_app()
    mock_session = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.delete(f"/api/v1/admin/users/{superadmin_user.id}")
        assert res.status_code == 400
        assert "Không thể xóa tài khoản Superadmin đang thao tác" in res.json()["detail"]


@pytest.mark.asyncio
async def test_superadmin_cannot_self_deactivate(superadmin_user):
    app = create_app()
    mock_session = AsyncMock()

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = superadmin_user
    mock_session.execute.return_value = user_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.put(
            f"/api/v1/admin/users/{superadmin_user.id}",
            json={"is_active": False},
        )
        assert res.status_code == 400
        assert "Không thể tự vô hiệu hóa" in res.json()["detail"]


@pytest.mark.asyncio
async def test_superadmin_cannot_self_demote(superadmin_user):
    app = create_app()
    mock_session = AsyncMock()

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = superadmin_user
    mock_session.execute.return_value = user_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.put(
            f"/api/v1/admin/users/{superadmin_user.id}",
            json={"role": "admin"},
        )
        assert res.status_code == 400
        assert "Không thể tự giáng quyền" in res.json()["detail"]


@pytest.mark.asyncio
async def test_superadmin_get_user_detail(superadmin_user, regular_user):
    app = create_app()
    mock_session = AsyncMock()

    # User lookup
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = regular_user

    # Counts lookup: properties, favorites, alerts
    count_prop = MagicMock()
    count_prop.scalar.return_value = 5
    count_fav = MagicMock()
    count_fav.scalar.return_value = 3
    count_alert = MagicMock()
    count_alert.scalar.return_value = 1

    mock_session.execute.side_effect = [user_result, count_prop, count_fav, count_alert]

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/admin/users/{regular_user.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == regular_user.email
        assert data["total_properties"] == 5
        assert data["total_favorites"] == 3
        assert data["total_alerts"] == 1


@pytest.mark.asyncio
async def test_superadmin_get_user_detail_not_found(superadmin_user):
    app = create_app()
    mock_session = AsyncMock()

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = user_result

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: superadmin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/admin/users/{uuid.uuid4()}")
        assert res.status_code == 404
        assert "Không tìm thấy người dùng" in res.json()["detail"]

