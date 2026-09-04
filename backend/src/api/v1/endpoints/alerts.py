import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user, get_db_session
from src.models.user import User
from src.schemas.alert import AlertResponse, CreateAlertRequest, UpdateAlertRequest
from src.services.alert_service import AlertService, get_alert_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved search alert (Requires Bearer token)",
)
async def create_alert(
    request: CreateAlertRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    """
    Save search criteria (price, location, property type, bedrooms, keywords)
    and register notification frequency (instant, daily, weekly).
    """
    if not request.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Alert title cannot be empty",
        )

    alert = await alert_service.create_alert(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return AlertResponse.model_validate(alert)


@router.get(
    "",
    response_model=list[AlertResponse],
    status_code=status.HTTP_200_OK,
    summary="List current user's saved search alerts",
)
async def list_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> list[AlertResponse]:
    alerts = await alert_service.get_user_alerts(db=db, user_id=current_user.id)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved search alert by ID",
)
async def get_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await alert_service.get_alert_by_id(db=db, alert_id=alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found",
        )
    return AlertResponse.model_validate(alert)


@router.put(
    "/{alert_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Update saved search alert",
)
async def update_alert(
    alert_id: uuid.UUID,
    request: UpdateAlertRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await alert_service.update_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user.id,
        request=request,
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found",
        )
    return AlertResponse.model_validate(alert)


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved search alert",
)
async def delete_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    alert_service: AlertService = Depends(get_alert_service),
) -> None:
    deleted = await alert_service.delete_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found",
        )
