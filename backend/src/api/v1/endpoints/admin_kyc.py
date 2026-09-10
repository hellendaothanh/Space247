import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_superadmin
from src.core.database import get_db_session
from src.models.alert import UserNotification
from src.models.kyc import KycVerificationStatus, UserKycVerification
from src.models.user import User
from src.schemas.user import KYCReviewPayload, KycPendingUserResponse


router = APIRouter(dependencies=[Depends(get_current_superadmin)])


@router.get("/pending", response_model=list[KycPendingUserResponse])
async def get_pending_kyc_list(
    db: AsyncSession = Depends(get_db_session),
) -> list[KycPendingUserResponse]:
    result = await db.execute(
        select(UserKycVerification, User)
        .join(User, User.id == UserKycVerification.user_id)
        .where(UserKycVerification.status == KycVerificationStatus.PENDING.value)
        .order_by(UserKycVerification.created_at.asc())
    )
    return [
        KycPendingUserResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            status=kyc.status,
            masked_citizen_id=f"****{kyc.citizen_id_last4}",
            created_at=kyc.created_at,
            updated_at=kyc.updated_at,
        )
        for kyc, user in result.all()
    ]


@router.post("/{user_id}/review")
async def review_kyc(
    user_id: uuid.UUID,
    payload: KYCReviewPayload,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    result = await db.execute(select(UserKycVerification).where(UserKycVerification.user_id == user_id))
    kyc = result.scalar_one_or_none()
    if not kyc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ KYC.")

    approved = payload.action == "approve"
    kyc.status = KycVerificationStatus.VERIFIED.value if approved else KycVerificationStatus.REJECTED.value
    message = "Hồ sơ CCCD của bạn đã được xác thực." if approved else f"Hồ sơ CCCD cần bổ sung: {payload.reason or 'Vui lòng kiểm tra và gửi lại.'}"
    db.add(UserNotification(
        user_id=user_id,
        title="Kết quả duyệt hồ sơ KYC",
        message=message,
        notification_type="kyc_review",
    ))
    await db.flush()
    return {"status": kyc.status, "message": message}
