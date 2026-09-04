from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"


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


class UserResponse(UserBase):
    id: uuid.UUID
    phone_number: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
