import io
import sys
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile
from httpx import ASGITransport, AsyncClient
from PIL import Image

from src.api.deps import get_current_active_user
from src.core.database import get_db_session
from src.core.config import settings
from src.core.security import decode_access_token
from src.main import app
from src.api.v1.endpoints.kyc import get_documents, stream_document
from src.models.kyc import UserKycVerification
from src.models.user import User
from src.services.storage import kyc_storage


def image_upload() -> UploadFile:
    data = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(data, format="JPEG")
    data.seek(0)
    return UploadFile(filename="front.jpg", file=data, headers={"content-type": "image/jpeg"})


@pytest.mark.asyncio
async def test_local_kyc_storage_uses_private_user_scoped_key_and_short_grant(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "KYC_STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "KYC_LOCAL_STORAGE_PATH", str(tmp_path))
    user_id = uuid.uuid4()
    upload = image_upload()

    key, content_type = await kyc_storage.store(user_id, "front", upload)
    grant = await kyc_storage.grant(key, content_type)

    assert key.startswith(f"{user_id}/front/")
    assert (tmp_path / key).is_file()
    assert str(tmp_path) not in grant
    token = grant.split("grant=", 1)[1]
    payload = decode_access_token(token)
    assert payload and payload["scope"] == "kyc:read" and payload["sub"] == key
    assert payload["exp"] - payload["iat"] == settings.KYC_RETRIEVAL_TTL_SECONDS


@pytest.mark.asyncio
async def test_rejects_unsupported_kyc_media(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "KYC_LOCAL_STORAGE_PATH", str(tmp_path))
    upload = UploadFile(filename="identity.pdf", file=io.BytesIO(b"pdf"), headers={"content-type": "application/pdf"})
    with pytest.raises(Exception) as error:
        await kyc_storage.store(uuid.uuid4(), "front", upload)
    assert getattr(error.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_user_cannot_retrieve_another_users_kyc_documents():
    user_a = User(id=uuid.uuid4(), email="a@example.com", hashed_password="hash", full_name="User A")
    user_b = User(id=uuid.uuid4(), email="b@example.com", hashed_password="hash", full_name="User B")

    async def override_user():
        return user_a

    async def override_db():
        yield object()

    app.dependency_overrides[get_current_active_user] = override_user
    app.dependency_overrides[get_db_session] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/kyc/my-documents?user_id={user_b.id}")
        assert response.status_code == 403
        assert "KYC documents" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_owner_and_superadmin_receive_only_temporary_document_grants(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "KYC_STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "KYC_LOCAL_STORAGE_PATH", str(tmp_path))
    owner = User(id=uuid.uuid4(), email="owner@example.com", hashed_password="hash", full_name="Owner")
    superadmin = User(id=uuid.uuid4(), email="superadmin@example.com", hashed_password="hash", full_name="Superadmin", role="superadmin")
    kyc = UserKycVerification(
        user_id=owner.id,
        status="pending",
        citizen_id_last4="1234",
        front_document_key=f"{owner.id}/front/identity.jpg",
        back_document_key=f"{owner.id}/back/identity.jpg",
        front_content_type="image/jpeg",
        back_content_type="image/jpeg",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = kyc
    db = AsyncMock()
    db.execute.return_value = result
    db.get.return_value = owner

    own_response = await get_documents(None, owner, db)
    review_response = await get_documents(owner.id, superadmin, db)

    for response in (own_response, review_response):
        assert response.masked_citizen_id == "****1234"
        assert response.front.expires_in == 900
        assert response.back.expires_in == 900
        assert response.front.url.startswith("/api/v1/kyc/documents/stream?grant=")
        assert str(tmp_path) not in response.front.url


@pytest.mark.asyncio
async def test_local_stream_grant_returns_private_image_response(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "KYC_STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "KYC_LOCAL_STORAGE_PATH", str(tmp_path))
    key = f"{uuid.uuid4()}/front/identity.jpg"
    path = tmp_path / key
    path.parent.mkdir(parents=True)
    path.write_bytes(b"image-data")

    grant = await kyc_storage.grant(key, "image/jpeg")
    response = await stream_document(grant.split("grant=", 1)[1])

    assert response.media_type == "image/jpeg"
    assert response.headers["cache-control"] == "private, no-store"
    with pytest.raises(Exception) as error:
        await stream_document("invalid")
    assert getattr(error.value, "status_code", None) == 401


@pytest.mark.asyncio
async def test_s3_grant_uses_private_cache_and_configured_ttl(monkeypatch):
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://r2.example.test/grant"
    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=MagicMock(return_value=client)))
    monkeypatch.setattr(settings, "KYC_STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "KYC_S3_BUCKET", "kyc-private")
    monkeypatch.setattr(settings, "KYC_S3_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "KYC_S3_SECRET_ACCESS_KEY", "secret")

    assert await kyc_storage.grant("user/front/id.jpg", "image/jpeg") == "https://r2.example.test/grant"
    _, kwargs = client.generate_presigned_url.call_args
    assert kwargs["ExpiresIn"] == 900
    assert kwargs["Params"]["ResponseCacheControl"] == "private, no-store"
