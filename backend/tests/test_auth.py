from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_current_active_user
from src.core.database import get_db_session
from src.core.security import create_access_token, hash_password
from src.main import app
from src.models.property import Property
from src.models.user import User


@pytest.mark.asyncio
async def test_register_and_login_flow():
    """Test user registration, JWT generation, and login credential verification."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # User storage simulation
    users_db: dict[str, User] = {}

    async def mock_execute(stmt):
        result = MagicMock()
        # Check email query
        stmt_str = str(stmt).lower()
        if "users.email" in stmt_str or "email" in stmt_str:
            found_user = None
            for u in users_db.values():
                found_user = u
                break
            result.scalar_one_or_none.return_value = found_user
        elif "users.id" in stmt_str or "users" in stmt_str:
            found_user = list(users_db.values())[0] if users_db else None
            result.scalar_one_or_none.return_value = found_user
        else:
            result.scalar_one_or_none.return_value = None
        return result

    mock_session.execute = mock_execute

    def capture_add(instance):
        if isinstance(instance, User):
            users_db[instance.email] = instance

    mock_session.add.side_effect = capture_add

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new user
        reg_payload = {
            "email": "agent.nguyen@space247.vn",
            "password": "SecurePassword123!",
            "full_name": "Nguyễn Văn Chuyên Nghiệp",
            "phone": "0987654321",
            "role": "agent",
        }
        resp = await client.post("/api/v1/auth/register", json=reg_payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "agent.nguyen@space247.vn"
        assert data["user"]["role"] == "agent"
        token = data["access_token"]

        # 2. Reject duplicate registration
        dup_resp = await client.post("/api/v1/auth/register", json=reg_payload)
        assert dup_resp.status_code == 400
        assert "already registered" in dup_resp.json()["detail"].lower()

        # 3. Login with correct password
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "agent.nguyen@space247.vn", "password": "SecurePassword123!"},
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data
        assert login_data["user"]["full_name"] == "Nguyễn Văn Chuyên Nghiệp"

        # 4. Reject login with wrong password
        wrong_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "agent.nguyen@space247.vn", "password": "WrongPassword!"},
        )
        assert wrong_resp.status_code == 401
        assert "incorrect" in wrong_resp.json()["detail"].lower()

        # 5. Access /auth/me with Bearer token
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "agent.nguyen@space247.vn"
        assert me_data["is_active"] is True

        # 6. Reject /auth/me with missing or invalid token
        unauth_resp = await client.get("/api/v1/auth/me")
        assert unauth_resp.status_code == 401

        invalid_token_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert invalid_token_resp.status_code == 401

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_protected_property_creation_with_auth():
    """Verify that creating property requires Bearer token and assigns user_id."""
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        email="landlord@space247.vn",
        hashed_password=hash_password("Pass1234!"),
        full_name="Lê Gia Chủ",
        is_active=True,
    )

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        return result

    mock_session.execute = mock_execute

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db

    token = create_access_token(subject=str(user_id))

    property_payload = {
        "title": "Biệt thự Đảo Kim Cương ven sông Sài Gòn",
        "description": "Biệt thự cao cấp có hồ bơi sân vườn sang trọng, an ninh tuyệt đối.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 45000000000.0,
        "area_sqm": 350.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "10 Đảo Kim Cương",
        "ward": "Bình Trưng Tây",
        "district": "TP Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt creation without token -> 401
        no_auth_resp = await client.post("/api/v1/properties", json=property_payload)
        assert no_auth_resp.status_code == 401

        # Create with valid token -> 201
        auth_prop_resp = await client.post(
            "/api/v1/properties",
            json=property_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert auth_prop_resp.status_code == 201, auth_prop_resp.text
        created_prop = auth_prop_resp.json()
        assert created_prop["title"] == property_payload["title"]
        assert created_prop["user_id"] == str(user_id)

    app.dependency_overrides.clear()
