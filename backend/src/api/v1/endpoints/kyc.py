import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user
from src.core.config import settings
from src.core.database import get_db_session
from src.core.security import decode_access_token
from src.models.kyc import UserKycVerification
from src.models.user import User
from src.schemas.kyc import KycDocumentGrant, KycDocumentsResponse
from src.services.storage import kyc_storage

router = APIRouter()


async def _response(kyc: UserKycVerification) -> KycDocumentsResponse:
    ttl = settings.KYC_RETRIEVAL_TTL_SECONDS
    return KycDocumentsResponse(status=kyc.status, masked_citizen_id=f"****{kyc.citizen_id_last4}", front=KycDocumentGrant(url=await kyc_storage.grant(kyc.front_document_key, kyc.front_content_type), expires_in=ttl), back=KycDocumentGrant(url=await kyc_storage.grant(kyc.back_document_key, kyc.back_content_type), expires_in=ttl), updated_at=kyc.updated_at)


@router.post("/verification", response_model=KycDocumentsResponse, status_code=status.HTTP_201_CREATED)
async def upload_verification(citizen_id: str = Form(..., min_length=4, max_length=32), front: UploadFile = File(...), back: UploadFile = File(...), current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_session)):
    created: list[str] = []
    old_keys: tuple[str, str] = ()
    try:
        front_key, front_type = await kyc_storage.store(current_user.id, "front", front); created.append(front_key)
        back_key, back_type = await kyc_storage.store(current_user.id, "back", back); created.append(back_key)
        result = await db.execute(select(UserKycVerification).where(UserKycVerification.user_id == current_user.id))
        existing = result.scalar_one_or_none()
        if existing:
            old_keys = (existing.front_document_key, existing.back_document_key)
            existing.citizen_id_last4, existing.front_document_key, existing.back_document_key = citizen_id[-4:], front_key, back_key
            existing.front_content_type, existing.back_content_type, existing.status = front_type, back_type, "pending"
            kyc = existing
        else:
            kyc = UserKycVerification(user_id=current_user.id, citizen_id_last4=citizen_id[-4:], front_document_key=front_key, back_document_key=back_key, front_content_type=front_type, back_content_type=back_type)
            db.add(kyc)
        await db.flush()
        await db.commit()
        await db.refresh(kyc)
    except Exception:
        await db.rollback()
        for key in created:
            try:
                await kyc_storage.delete(key)
            except Exception:
                pass
        raise
    for key in old_keys:
        try:
            await kyc_storage.delete(key)
        except Exception:
            pass
    return await _response(kyc)


@router.get("/my-documents", response_model=KycDocumentsResponse)
async def get_documents(user_id: uuid.UUID | None = Query(None), current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_session)):
    target_id = user_id or current_user.id
    if target_id != current_user.id:
        if current_user.role != "superadmin": raise HTTPException(status_code=403, detail="KYC documents can only be retrieved by their owner")
        target = await db.get(User, target_id)
        if not target: raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(UserKycVerification).where(UserKycVerification.user_id == target_id))
    kyc = result.scalar_one_or_none()
    if not kyc: raise HTTPException(status_code=404, detail="KYC verification not found")
    return await _response(kyc)


@router.get("/documents/stream", include_in_schema=False)
async def stream_document(grant: str = Query(...)):
    payload = decode_access_token(grant)
    if not payload or payload.get("scope") != "kyc:read" or not isinstance(payload.get("sub"), str):
        raise HTTPException(status_code=401, detail="Invalid or expired document grant")
    path = kyc_storage.local_path(payload["sub"])
    if not path.is_file(): raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path, media_type=payload.get("content_type", "application/octet-stream"), headers={"Cache-Control": "private, no-store"})
