from datetime import datetime, timezone
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.config import settings
from src.core.database import Base


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        Index(
            "ix_properties_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_properties_fts",
            text(
                "to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(address, '') || ' ' || coalesce(ward, '') || ' ' || coalesce(district, '') || ' ' || coalesce(city, '') || ' ' || coalesce(description, ''))"
            ),
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    listing_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # sale / rent
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="VND")
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    num_bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Location
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active", index=True
    )

    # 768-dimensional vector embedding for semantic search
    embedding = mapped_column(Vector(settings.VECTOR_DIM), nullable=True)

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

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "active"
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title='{self.title[:30]}', listing_type='{self.listing_type}', price={self.price})>"
