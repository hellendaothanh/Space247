import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user
from src.core.database import get_db_session
from src.core.security import hash_password, verify_password
from src.models.alert import SavedSearchAlert
from src.models.favorite import FavoriteProperty
from src.models.property import Property
from src.models.user import User
from src.schemas.user import (
    ChangePasswordRequest,
    UserProfileDetailResponse,
    UserProfileUpdateRequest,
    UserResponse,
)

logger = logging.getLogger("space247_backend.users")
router = APIRouter()


@router.get(
    "/me",
    response_model=UserProfileDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user detailed profile with counts",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileDetailResponse:
    """Retrieve the current authenticated user's profile along with favorite, listing, and alert metrics."""
    # Count properties owned by user
    prop_stmt = select(func.count(Property.id)).where(Property.user_id == current_user.id)
    prop_res = await db.execute(prop_stmt)
    total_properties = prop_res.scalar() or 0

    # Count favorites
    fav_stmt = select(func.count(FavoriteProperty.id)).where(FavoriteProperty.user_id == current_user.id)
    fav_res = await db.execute(fav_stmt)
    total_favorites = fav_res.scalar() or 0

    # Count alerts
    alert_stmt = select(func.count(SavedSearchAlert.id)).where(SavedSearchAlert.user_id == current_user.id)
    alert_res = await db.execute(alert_stmt)
    total_alerts = alert_res.scalar() or 0

    return UserProfileDetailResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        phone_number=current_user.phone,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        is_active=current_user.is_active,
        phone_verified=current_user.phone_verified,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        total_properties=total_properties,
        total_favorites=total_favorites,
        total_alerts=total_alerts,
    )


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user personal profile",
)
async def update_my_profile(
    update_in: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Update personal details (full_name, phone, avatar_url) for the current user."""
    if update_in.full_name is not None:
        current_user.full_name = update_in.full_name.strip()
    if update_in.phone is not None:
        new_phone = update_in.phone.strip() if update_in.phone else None
        if new_phone != current_user.phone:
            current_user.phone_verified = False
        current_user.phone = new_phone
    if update_in.avatar_url is not None:
        current_user.avatar_url = update_in.avatar_url.strip() if update_in.avatar_url else None

    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change current user account password",
)
async def change_my_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Verify old password and set a new password of at least 8 characters."""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác.",
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mật khẩu mới phải có ít nhất 8 ký tự.",
        )

    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    await db.flush()

    return {"message": "Đổi mật khẩu thành công."}
