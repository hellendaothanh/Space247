from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    properties = relationship("Property", back_populates="owner")

    @property
    def phone_number(self) -> str | None:
        return self.phone

    @phone_number.setter
    def phone_number(self, value: str | None) -> None:
        self.phone = value

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "role" not in kwargs or kwargs["role"] is None:
            kwargs["role"] = UserRole.USER.value
        elif hasattr(kwargs["role"], "value"):
            kwargs["role"] = kwargs["role"].value
        else:
            kwargs["role"] = str(kwargs["role"]).lower()
            if kwargs["role"].startswith("userrole."):
                kwargs["role"] = kwargs["role"].split(".", 1)[1].lower()
        if "is_active" not in kwargs or kwargs["is_active"] is None:
            kwargs["is_active"] = True
        if "phone_verified" not in kwargs or kwargs["phone_verified"] is None:
            kwargs["phone_verified"] = False
        if "last_login_at" not in kwargs:
            kwargs["last_login_at"] = None
        if "avatar_url" not in kwargs:
            kwargs["avatar_url"] = None
        if "phone_number" in kwargs and "phone" not in kwargs:
            kwargs["phone"] = kwargs.pop("phone_number")
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}', role='{self.role}')>"
