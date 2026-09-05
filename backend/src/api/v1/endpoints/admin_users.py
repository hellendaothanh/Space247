import logging
import math
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_superadmin_user
from src.core.database import get_db_session
from src.core.security import hash_password
from src.models.alert import SavedSearchAlert
from src.models.favorite import FavoriteProperty
from src.models.property import Property
from src.models.user import User, UserRole
from src.schemas.user import (
    UserAdminDetailResponse,
    UserCreateByAdminRequest,
    UserPaginationResponse,
    UserResponse,
    UserUpdateByAdminRequest,
)

logger = logging.getLogger("space247_backend.admin_users")
router = APIRouter(dependencies=[Depends(get_current_superadmin_user)])


@router.get(
    "",
    response_model=UserPaginationResponse,
    status_code=status.HTTP_200_OK,
    summary="List users with filtering, search, and pagination (Superadmin only)",
)
async def list_users(
    q: str | None = Query(None, description="Search term for name or email"),
    role: str | None = Query(None, description="Filter by user role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db_session),
) -> UserPaginationResponse:
    """List and filter users for superadmin management."""
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    filters = []
    if q:
        search_term = f"%{q.strip().lower()}%"
        filters.append(
            or_(
                func.lower(User.email).ilike(search_term),
                func.lower(User.full_name).ilike(search_term),
            )
        )
    if role:
        filters.append(User.role == role.strip().lower())
    if is_active is not None:
        filters.append(User.is_active == is_active)

    if filters:
        for f in filters:
            stmt = stmt.where(f)
            count_stmt = count_stmt.where(f)

    # Get total count
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    # Apply pagination and sorting (newest first, deterministic)
    offset = (page - 1) * page_size
    stmt = stmt.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(page_size)
    res = await db.execute(stmt)
    users = res.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return UserPaginationResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user with specific role (Superadmin only)",
)
async def create_user_by_admin(
    user_in: UserCreateByAdminRequest,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Create a new user with assigned role and status."""
    existing_stmt = select(User).where(User.email == user_in.email.lower().strip())
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký trong hệ thống.",
        )

    new_user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name.strip(),
        phone=user_in.phone.strip() if user_in.phone else None,
        avatar_url=user_in.avatar_url.strip() if user_in.avatar_url else None,
        role=user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role),
        is_active=user_in.is_active,
        phone_verified=user_in.phone_verified,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.get(
    "/{user_id}",
    response_model=UserAdminDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details and activity metrics (Superadmin only)",
)
async def get_user_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> UserAdminDetailResponse:
    """Get single user profile and their associated properties/alerts metrics."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    # Count properties owned by user
    prop_stmt = select(func.count(Property.id)).where(Property.user_id == user.id)
    prop_res = await db.execute(prop_stmt)
    total_properties = prop_res.scalar() or 0

    # Count favorites
    fav_stmt = select(func.count(FavoriteProperty.id)).where(FavoriteProperty.user_id == user.id)
    fav_res = await db.execute(fav_stmt)
    total_favorites = fav_res.scalar() or 0

    # Count alerts
    alert_stmt = select(func.count(SavedSearchAlert.id)).where(SavedSearchAlert.user_id == user.id)
    alert_res = await db.execute(alert_stmt)
    total_alerts = alert_res.scalar() or 0

    return UserAdminDetailResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        phone_number=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        is_active=user.is_active,
        phone_verified=user.phone_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        total_properties=total_properties,
        total_favorites=total_favorites,
        total_alerts=total_alerts,
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user details, role, status, or reset password (Superadmin only)",
)
async def update_user_by_admin(
    user_id: uuid.UUID,
    update_in: UserUpdateByAdminRequest,
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Update user metadata, assign new role, toggle status, or reset password."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    # Protect against self-deactivation or self-demotion
    if user.id == current_superadmin.id:
        if update_in.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tự vô hiệu hóa tài khoản Superadmin đang đăng nhập.",
            )
        if update_in.role and update_in.role != UserRole.SUPERADMIN and update_in.role != UserRole.SUPERADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tự giáng quyền tài khoản Superadmin đang đăng nhập.",
            )

    if update_in.full_name is not None:
        user.full_name = update_in.full_name.strip()
    if update_in.phone is not None:
        user.phone = update_in.phone.strip() if update_in.phone else None
    if update_in.avatar_url is not None:
        user.avatar_url = update_in.avatar_url.strip() if update_in.avatar_url else None
    if update_in.role is not None:
        user.role = update_in.role.value if hasattr(update_in.role, "value") else str(update_in.role)
    if update_in.is_active is not None:
        user.is_active = update_in.is_active
    if update_in.phone_verified is not None:
        user.phone_verified = update_in.phone_verified
    if update_in.reset_password is not None:
        user.hashed_password = hash_password(update_in.reset_password)

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete (deactivate) a user account (Superadmin only)",
)
async def delete_user_by_admin(
    user_id: uuid.UUID,
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Soft delete by setting is_active = False."""
    if user_id == current_superadmin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa tài khoản Superadmin đang thao tác.",
        )

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    user.is_active = False
    db.add(user)
    await db.flush()

    return {"message": "Đã vô hiệu hóa tài khoản người dùng thành công."}
