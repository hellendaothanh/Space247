from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user
from src.core.config import settings
from src.core.database import get_db_session
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User, UserRole
from src.schemas.user import Token, UserLogin, UserRegister, UserResponse, UserUpdate

logger = logging.getLogger("space247_backend.auth")
router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    """Register a new user account with email, password, and optional role."""
    # Check if email is already taken
    existing_stmt = select(User).where(User.email == user_in.email.lower().strip())
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered",
        )

    # Prevent privilege escalation: only allow user or agent on public self-registration
    assigned_role = UserRole.USER.value
    if user_in.role in (UserRole.AGENT, "agent"):
        assigned_role = UserRole.AGENT.value

    # Hash password & create user
    user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name.strip(),
        phone=user_in.phone.strip() if user_in.phone else None,
        role=assigned_role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    try:
        await db.refresh(user)
    except Exception:
        pass

    # Generate JWT access token
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"email": user.email, "role": user.role},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return JWT access token",
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    """Authenticate with email and password to receive a JWT Bearer token."""
    stmt = select(User).where(User.email == login_data.email.lower().strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"email": user.email, "role": user.role},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the profile of the authenticated user requesting the token."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current authenticated user profile",
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Update current user's profile (full_name, phone/phone_number, avatar_url)."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name.strip()
    if user_update.phone_number is not None:
        current_user.phone = user_update.phone_number.strip()
    elif user_update.phone is not None:
        current_user.phone = user_update.phone.strip()
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url.strip()

    db.add(current_user)
    await db.flush()
    try:
        await db.refresh(current_user)
    except Exception:
        pass
    return current_user
