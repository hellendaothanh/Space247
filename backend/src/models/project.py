from datetime import datetime, timezone
from typing import Any
import uuid
from geoalchemy2 import Geometry
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
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.config import settings
from src.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index(
            "ix_projects_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    developer: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="completed",
        server_default="completed",
        index=True,
    )  # upcoming, under_construction, handing_over, completed
    total_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    launch_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handover_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Location
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    images: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
    )
    master_plan_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    legal_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price_range_min: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    price_range_max: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    amenities: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
    )

    # Vector embedding for project semantic search
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

    # 1:N Relationship to Property
    properties = relationship("Property", back_populates="project", lazy="selectin")

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs or kwargs["status"] is None:
            kwargs["status"] = "completed"
        if "images" not in kwargs or kwargs["images"] is None:
            kwargs["images"] = []
        if "amenities" not in kwargs or kwargs["amenities"] is None:
            kwargs["amenities"] = []
        now = datetime.now(timezone.utc)
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = now
        if "updated_at" not in kwargs or kwargs["updated_at"] is None:
            kwargs["updated_at"] = now
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', slug='{self.slug}', developer='{self.developer}')>"
