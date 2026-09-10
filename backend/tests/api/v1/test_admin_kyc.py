import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_current_active_user
from src.core.database import get_db_session
from src.main import create_app
from src.models.kyc import UserKycVerification
from src.models.user import User, UserRole


@pytest.fixture
def superadmin() -> User:
    return User(email="admin@space247.vn", hashed_password="x", full_name="Admin", role=UserRole.SUPERADMIN, is_active=True)


@pytest.fixture
def member() -> User:
    return User(email="user@space247.vn", hashed_password="x", full_name="Member", role=UserRole.USER, is_active=True)


@pytest.mark.asyncio
async def test_pending_kyc_forbidden_for_member(member: User):
    app = create_app()
    app.dependency_overrides[get_current_active_user] = lambda: member
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/admin/kyc/pending")).status_code == 403


@pytest.mark.asyncio
async def test_superadmin_reviews_kyc_and_creates_notification(superadmin: User):
    app = create_app()
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    kyc = UserKycVerification(
        user_id=uuid.uuid4(), citizen_id_last4="1234", front_document_key="storage/kyc/front", back_document_key="storage/kyc/back",
        front_content_type="image/jpeg", back_content_type="image/jpeg", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = kyc
    session.execute.return_value = result
    app.dependency_overrides[get_current_active_user] = lambda: superadmin
    app.dependency_overrides[get_db_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/admin/kyc/{kyc.user_id}/review", json={"action": "approve"})
    assert response.status_code == 200
    assert kyc.status == "verified"
    session.add.assert_called_once()
