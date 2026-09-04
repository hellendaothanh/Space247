import logging
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user, get_db_session
from src.models.user import User
from src.schemas.alert import NotificationListResponse, NotificationResponse
from src.services.alert_service import AlertService, get_alert_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current user's notifications and unread badge count",
)
async def list_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> NotificationListResponse:
    items, total, unread_count = await alert_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> NotificationResponse:
    notification = await alert_service.mark_notification_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )
    return NotificationResponse.model_validate(notification)


@router.post(
    "/read-all",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Mark all user notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> dict[str, Any]:
    count = await alert_service.mark_all_read(db=db, user_id=current_user.id)
    return {"success": True, "updated_count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> None:
    deleted = await alert_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )
