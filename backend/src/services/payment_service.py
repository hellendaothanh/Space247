import logging
from datetime import datetime, timezone
import urllib.parse
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import UserNotification
from src.models.rental_property import DepositTransaction, RentalInquiry, RentalUnit
from src.schemas.rental_management import PaymentWebhookPayload, RentalUnitStatus

logger = logging.getLogger("space247_backend.payment_service")


class PaymentService:
    DEFAULT_BANK_ID = "970422"  # MB Bank
    DEFAULT_ACCOUNT_NO = "0987654321"
    DEFAULT_ACCOUNT_NAME = "CONG TY SPACE247 VIETNAM"
    DEFAULT_TEMPLATE = "compact2"

    @classmethod
    def generate_reference_code(cls, prefix: str = "SP247") -> str:
        """Mint unique, easily recognizable transaction reference code."""
        timestamp_part = int(datetime.now(timezone.utc).timestamp())
        unique_suffix = uuid.uuid4().hex[:5].upper()
        return f"{prefix}{timestamp_part}{unique_suffix}"

    @classmethod
    def generate_vietqr_url(
        cls,
        reference_code: str,
        amount: float,
        bank_id: str | None = None,
        account_no: str | None = None,
        account_name: str | None = None,
        template: str | None = None,
    ) -> str:
        """
        Generate Napas 247 VietQR QuickLink image URL.
        Specification: https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png?...
        """
        b_id = bank_id or cls.DEFAULT_BANK_ID
        acc_no = account_no or cls.DEFAULT_ACCOUNT_NO
        acc_name = urllib.parse.quote(account_name or cls.DEFAULT_ACCOUNT_NAME)
        tmpl = template or cls.DEFAULT_TEMPLATE
        ref = urllib.parse.quote(reference_code)
        amt = int(amount)

        return f"https://img.vietqr.io/image/{b_id}-{acc_no}-{tmpl}.png?amount={amt}&addInfo={ref}&accountName={acc_name}"

    @classmethod
    async def process_payment_webhook(
        cls,
        db: AsyncSession,
        payload: PaymentWebhookPayload,
    ) -> DepositTransaction:
        """
        Process incoming payment IPN webhook idempotently.
        On match:
        - Updates transaction to success
        - Locks room to reserved
        - Updates inquiry to confirmed
        - Dispatches UserNotification records to tenant & host
        """
        stmt = select(DepositTransaction).where(DepositTransaction.reference_code == payload.reference_code)
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()

        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giao dịch đặt cọc với mã {payload.reference_code}",
            )

        # Idempotent 200 response if already completed
        if tx.status == "success":
            logger.info("Transaction %s already processed successfully. Returning idempotent response.", tx.reference_code)
            return tx

        now = datetime.now(timezone.utc)
        expires_at = tx.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if tx.status == "expired" or now > expires_at:
            if tx.status != "expired":
                tx.status = "expired"
                await db.commit()
                await db.refresh(tx)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giao dịch đặt cọc đã hết hạn hiệu lực (15 phút)",
            )

        if payload.status and payload.status.lower() in ("failed", "cancelled", "canceled", "error"):
            tx.status = "failed"
            tx.provider_response = payload.model_dump()
            await db.commit()
            await db.refresh(tx)
            return tx

        if payload.amount < float(tx.amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số tiền thanh toán ({payload.amount}) không đủ so với yêu cầu đặt cọc ({tx.amount})",
            )

        # Update RentalUnit to reserved
        unit_stmt = select(RentalUnit).where(RentalUnit.id == tx.unit_id)
        unit_res = await db.execute(unit_stmt)
        unit = unit_res.scalar_one_or_none()
        if unit and unit.status in ("occupied", "reserved"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phòng {unit.unit_number} không còn khả dụng (trạng thái: {unit.status})",
            )

        tx.status = "success"
        tx.paid_at = now
        tx.provider_response = payload.model_dump()
        unit_number = ""
        if unit:
            unit.status = RentalUnitStatus.RESERVED.value
            unit_number = unit.unit_number

        # Update RentalInquiry to confirmed if linked
        if tx.inquiry_id:
            inq_stmt = select(RentalInquiry).where(RentalInquiry.id == tx.inquiry_id)
            inq_res = await db.execute(inq_stmt)
            inquiry = inq_res.scalar_one_or_none()
            if inquiry:
                inquiry.status = "confirmed"

        # Atomically create UserNotification for tenant
        tenant_notif = UserNotification(
            user_id=tx.tenant_id,
            title="Đặt cọc giữ chỗ thành công",
            message=(
                f"Bạn đã đặt cọc thành công {float(tx.amount):,.0f} VND cho phòng {unit_number}. "
                "Trạng thái phòng đã được chuyển sang Đã giữ chỗ."
            ),
            notification_type="deposit_success",
        )
        db.add(tenant_notif)

        # Atomically create UserNotification for landlord (host)
        host_notif = UserNotification(
            user_id=tx.host_id,
            title="Nhận tiền đặt cọc giữ chỗ",
            message=(
                f"Khách thuê đã thanh toán đặt cọc thành công {float(tx.amount):,.0f} VND cho phòng {unit_number}. "
                "Hệ thống đã tự động khóa phòng sang trạng thái Đã giữ chỗ."
            ),
            notification_type="deposit_received",
        )
        db.add(host_notif)

        await db.commit()
        await db.refresh(tx)
        return tx

    @classmethod
    async def get_or_expire_transaction(
        cls,
        db: AsyncSession,
        reference_code: str,
    ) -> DepositTransaction:
        """Fetch transaction by reference code, auto-expiring if 15 minutes elapsed while pending."""
        stmt = select(DepositTransaction).where(DepositTransaction.reference_code == reference_code)
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()

        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy giao dịch đặt cọc",
            )

        now = datetime.now(timezone.utc)
        expires_at = tx.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if tx.status == "pending" and expires_at < now:
            tx.status = "expired"
            await db.commit()
            await db.refresh(tx)

        return tx
