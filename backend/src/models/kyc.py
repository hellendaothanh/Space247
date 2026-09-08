from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class KycVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class UserKycVerification(Base):
    __tablename__ = "user_kyc_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=KycVerificationStatus.PENDING.value, server_default="pending")
    citizen_id_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    front_document_key: Mapped[str] = mapped_column(String(512), nullable=False)
    back_document_key: Mapped[str] = mapped_column(String(512), nullable=False)
    front_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    back_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="kyc_verification")
