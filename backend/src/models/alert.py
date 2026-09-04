from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SavedSearchAlert(Base):
    __tablename__ = "saved_search_alerts"
    __table_args__ = (
        Index("ix_saved_search_alerts_user_id", "user_id"),
        Index("ix_saved_search_alerts_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="instant")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", backref="saved_alerts")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        if "is_active" not in kwargs or kwargs["is_active"] is None:
            kwargs["is_active"] = True
        if "frequency" not in kwargs or kwargs["frequency"] is None:
            kwargs["frequency"] = "instant"
        if "criteria" not in kwargs or kwargs["criteria"] is None:
            kwargs["criteria"] = {}
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<SavedSearchAlert(id={self.id}, user_id={self.user_id}, title='{self.title}', active={self.is_active})>"


class UserNotification(Base):
    __tablename__ = "user_notifications"
    __table_args__ = (
        Index("ix_user_notifications_user_id", "user_id"),
        Index("ix_user_notifications_is_read", "is_read"),
        Index("ix_user_notifications_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_search_alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="saved_search_match",
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="notifications")
    alert = relationship("SavedSearchAlert", backref="notifications")
    property = relationship("Property", backref="notifications")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "is_read" not in kwargs or kwargs["is_read"] is None:
            kwargs["is_read"] = False
        if "notification_type" not in kwargs or kwargs["notification_type"] is None:
            kwargs["notification_type"] = "saved_search_match"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<UserNotification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', read={self.is_read})>"
