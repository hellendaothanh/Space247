import logging
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.schemas.rental_management import (
    DepositTransactionResponse,
    PaymentWebhookPayload,
)
from src.services.payment_service import PaymentService

logger = logging.getLogger("space247_backend.payments")
router = APIRouter()


@router.post(
    "/webhook/{provider}",
    summary="Payment webhook IPN receiver for VietQR / MoMo / Napas 247",
    status_code=status.HTTP_200_OK,
)
async def receive_payment_webhook(
    provider: str,
    payload: PaymentWebhookPayload,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Handle asynchronous payment webhook from VietQR / Bank IPN.
    Validates payment amount and reference code, atomically reserves room, and notifies users.
    Idempotent: repeating notifications for the same reference code safely return 200.
    """
    payload.provider = provider
    tx = await PaymentService.process_payment_webhook(db=db, payload=payload)
    return {
        "status": "success",
        "message": "Giao dịch thanh toán được xử lý thành công",
        "reference_code": tx.reference_code,
        "transaction_status": tx.status,
    }


@router.get(
    "/deposit-transactions/{reference_code}",
    response_model=DepositTransactionResponse,
    summary="Get deposit transaction status by reference code (real-time polling)",
)
async def get_deposit_transaction(
    reference_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> DepositTransactionResponse:
    """
    Fetch deposit transaction details and real-time status.
    Auto-expires the transaction if the 15-minute reservation window has lapsed.
    """
    tx = await PaymentService.get_or_expire_transaction(db=db, reference_code=reference_code)
    return DepositTransactionResponse.model_validate(tx)
