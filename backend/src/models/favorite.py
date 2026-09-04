from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class FavoriteProperty(Base):
    __tablename__ = "favorite_properties"
    __table_args__ = (
        UniqueConstraint("user_id", "property_id", name="uq_favorite_user_property"),
        Index("ix_favorite_properties_user_id", "user_id"),
        Index("ix_favorite_properties_property_id", "property_id"),
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
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="favorites")
    property = relationship("Property", backref="favorited_by")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<FavoriteProperty(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"
