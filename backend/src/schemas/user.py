from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    role: UserRole = Field(default=UserRole.USER, description="User role (user or agent)")
    password: str = Field(..., min_length=6, max_length=72, description="Raw plaintext password (max 72 chars for bcrypt)")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=72, description="Account password")


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    phone_number: str | None = Field(default=None, max_length=50, description="Contact phone number")
    avatar_url: str | None = Field(default=None, max_length=500, description="Avatar image URL")


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    avatar_url: str | None = Field(default=None, max_length=500, description="Avatar image URL")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=72, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password (minimum 8 characters)")


class UserResponse(UserBase):
    id: uuid.UUID
    phone: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None
    is_active: bool
    phone_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileDetailResponse(UserResponse):
    total_properties: int = 0
    total_favorites: int = 0
    total_alerts: int = 0


class UserCreateByAdminRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=72, description="Initial account password")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    avatar_url: str | None = Field(default=None, max_length=500, description="Avatar image URL")
    role: UserRole = Field(default=UserRole.USER, description="Assigned role")
    is_active: bool = Field(default=True, description="Account active status")
    phone_verified: bool = Field(default=False, description="Phone verified status")


class UserUpdateByAdminRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255, description="Full name of user")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    avatar_url: str | None = Field(default=None, max_length=500, description="Avatar image URL")
    role: UserRole | None = Field(default=None, description="Updated role")
    is_active: bool | None = Field(default=None, description="Account active status")
    phone_verified: bool | None = Field(default=None, description="Phone verified status")
    reset_password: str | None = Field(default=None, min_length=6, max_length=72, description="Optional new password to set")


class UserAdminDetailResponse(UserResponse):
    total_properties: int = 0
    total_favorites: int = 0
    total_alerts: int = 0


class UserPaginationResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
