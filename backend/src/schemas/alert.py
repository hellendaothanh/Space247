from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from src.schemas.property import PropertyResponse


class CreateAlertRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Alert display title")
    criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Search filter criteria (min_price, max_price, city, district, property_type, etc.)",
    )
    frequency: str = Field(
        default="instant",
        pattern="^(instant|daily|weekly)$",
        description="Notification frequency: instant, daily, or weekly",
    )


class UpdateAlertRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    criteria: dict[str, Any] | None = None
    frequency: str | None = Field(default=None, pattern="^(instant|daily|weekly)$")
    is_active: bool | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    criteria: dict[str, Any]
    frequency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_notified_at: datetime | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    alert_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None
    title: str
    message: str
    notification_type: str = "saved_search_match"
    is_read: bool = False
    created_at: datetime
    property: PropertyResponse | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse] = Field(default_factory=list)
    total: int = Field(default=0)
    unread_count: int = Field(default=0)
