from datetime import datetime, timezone
import logging
import re
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import AsyncSessionLocal
from src.models.alert import SavedSearchAlert, UserNotification
from src.models.property import Property
from src.schemas.alert import CreateAlertRequest, UpdateAlertRequest

logger = logging.getLogger(__name__)


class AlertService:
    @staticmethod
    def match_property_to_alert(property_obj: Property, alert: SavedSearchAlert) -> bool:
        """
        Evaluate whether a given property matches the criteria of a saved search alert.
        """
        # Don't notify the listing owner about their own property
        if property_obj.user_id and alert.user_id == property_obj.user_id:
            return False

        criteria = alert.criteria or {}
        if not criteria:
            return True

        # 1. Price filters
        min_price = criteria.get("min_price")
        if min_price is not None:
            try:
                if property_obj.price < float(min_price):
                    return False
            except (ValueError, TypeError):
                pass

        max_price = criteria.get("max_price")
        if max_price is not None:
            try:
                if property_obj.price > float(max_price):
                    return False
            except (ValueError, TypeError):
                pass

        # 2. Listing type filter (sale vs rent)
        listing_type = criteria.get("listing_type")
        if listing_type:
            lt_val = str(listing_type).lower().strip()
            prop_lt = (property_obj.listing_type.value if hasattr(property_obj.listing_type, "value") else str(property_obj.listing_type)).lower()
            if lt_val != prop_lt:
                return False

        # 3. Property type filter
        property_type = criteria.get("property_type")
        if property_type:
            pt_val = str(property_type).lower().strip()
            prop_pt = (property_obj.property_type.value if hasattr(property_obj.property_type, "value") else str(property_obj.property_type)).lower()
            if pt_val != prop_pt:
                return False

        # 4. Location: City
        city = criteria.get("city")
        if city:
            c_val = str(city).lower().strip()
            prop_city = (property_obj.city or "").lower().strip()
            if c_val not in prop_city and prop_city not in c_val:
                return False

        # 5. Location: District
        district = criteria.get("district")
        if district:
            d_val = str(district).lower().strip()
            prop_district = (property_obj.district or "").lower().strip()
            if d_val not in prop_district and prop_district not in d_val:
                return False

        # 6. Bedrooms filter
        min_bedrooms = criteria.get("min_bedrooms")
        if min_bedrooms is not None:
            try:
                min_beds_int = int(min_bedrooms)
                if (property_obj.num_bedrooms or 0) < min_beds_int:
                    return False
            except (ValueError, TypeError):
                pass

        # 7. Keywords / search text
        keywords = criteria.get("keywords") or criteria.get("raw_query")
        if keywords:
            search_str = ""
            if isinstance(keywords, list):
                search_str = " ".join(str(k) for k in keywords)
            elif isinstance(keywords, str):
                search_str = keywords

            tokens = [t.lower() for t in re.split(r"\s+", search_str.strip()) if len(t) >= 2]
            prop_full_text = f"{property_obj.title} {property_obj.description} {property_obj.address}".lower()
            # If any meaningful token is found, consider it matched
            if tokens and not any(t in prop_full_text for t in tokens):
                return False

        return True

    async def evaluate_property_and_notify(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
    ) -> list[UserNotification]:
        """
        Evaluate a newly created/published property against all active alerts,
        generate UserNotification records and log simulated email dispatches.
        """
        stmt_prop = select(Property).where(Property.id == property_id)
        res_prop = await db.execute(stmt_prop)
        property_obj = res_prop.scalar_one_or_none()
        if not property_obj:
            logger.warning("Property %s not found for alert matching", property_id)
            return []

        # Find all active alerts
        stmt_alerts = select(SavedSearchAlert).where(SavedSearchAlert.is_active == True)
        res_alerts = await db.execute(stmt_alerts)
        active_alerts = list(res_alerts.scalars().all())

        created_notifications: list[UserNotification] = []
        now = datetime.now(timezone.utc)

        for alert in active_alerts:
            if self.match_property_to_alert(property_obj, alert):
                notification = UserNotification(
                    user_id=alert.user_id,
                    alert_id=alert.id,
                    property_id=property_obj.id,
                    title=f"Bất động sản mới phù hợp: {property_obj.title}",
                    message=(
                        f"Bất động sản '{property_obj.title}' tại {property_obj.district or ''}, {property_obj.city} "
                        f"với mức giá {property_obj.price:,.0f} VND phù hợp với tiêu chí tìm kiếm '{alert.title}' của bạn."
                    ),
                    notification_type="saved_search_match",
                    is_read=False,
                    created_at=now,
                )
                db.add(notification)
                created_notifications.append(notification)
                alert.last_notified_at = now

                # Log notification & simulated email dispatch
                logger.info(
                    "Matched alert '%s' (user %s) with property '%s'. Created notification and queued email alert.",
                    alert.title,
                    alert.user_id,
                    property_obj.id,
                )

        if created_notifications:
            await db.flush()

        return created_notifications

    async def create_alert(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: CreateAlertRequest,
    ) -> SavedSearchAlert:
        alert = SavedSearchAlert(
            user_id=user_id,
            title=request.title.strip(),
            criteria=request.criteria,
            frequency=request.frequency,
            is_active=True,
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert

    async def get_user_alerts(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[SavedSearchAlert]:
        stmt = (
            select(SavedSearchAlert)
            .where(SavedSearchAlert.user_id == user_id)
            .order_by(SavedSearchAlert.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_alert_by_id(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> SavedSearchAlert | None:
        stmt = select(SavedSearchAlert).where(
            SavedSearchAlert.id == alert_id,
            SavedSearchAlert.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_alert(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
        user_id: uuid.UUID,
        request: UpdateAlertRequest,
    ) -> SavedSearchAlert | None:
        alert = await self.get_alert_by_id(db, alert_id, user_id)
        if not alert:
            return None

        if request.title is not None:
            alert.title = request.title.strip()
        if request.criteria is not None:
            alert.criteria = request.criteria
        if request.frequency is not None:
            alert.frequency = request.frequency
        if request.is_active is not None:
            alert.is_active = request.is_active

        alert.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(alert)
        return alert

    async def delete_alert(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        alert = await self.get_alert_by_id(db, alert_id, user_id)
        if not alert:
            return False
        await db.delete(alert)
        await db.flush()
        return True

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> tuple[list[UserNotification], int, int]:
        # Base condition
        conditions = [UserNotification.user_id == user_id]
        if unread_only:
            conditions.append(UserNotification.is_read == False)

        # Unread count
        unread_stmt = select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False,
        )
        unread_count_res = await db.execute(unread_stmt)
        unread_count = unread_count_res.scalar_one() or 0

        # Total matching
        total_stmt = select(func.count(UserNotification.id)).where(*conditions)
        total_res = await db.execute(total_stmt)
        total = total_res.scalar_one() or 0

        # Items
        items_stmt = (
            select(UserNotification)
            .options(selectinload(UserNotification.property))
            .where(*conditions)
            .order_by(UserNotification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await db.execute(items_stmt)
        items = list(items_res.scalars().all())

        return items, total, unread_count

    async def mark_notification_read(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> UserNotification | None:
        stmt = (
            select(UserNotification)
            .options(selectinload(UserNotification.property))
            .where(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            return None

        notification.is_read = True
        await db.flush()
        await db.refresh(notification)
        return notification

    async def mark_all_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        stmt = (
            update(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False,
            )
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount or 0

    async def delete_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            return False
        await db.delete(notification)
        await db.flush()
        return True


_alert_service: AlertService | None = None


def get_alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service


async def background_evaluate_property_alerts(property_id: uuid.UUID) -> None:
    """
    Background task wrapper for FastAPI BackgroundTasks.
    Creates an independent database session to match alerts and generate notifications.
    """
    service = get_alert_service()
    try:
        async with AsyncSessionLocal() as session:
            try:
                await service.evaluate_property_and_notify(session, property_id)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(
                    "Error executing background alert matching for property %s: %s",
                    property_id,
                    e,
                    exc_info=True,
                )
    except Exception as outer_e:
        logger.error(
            "Failed to obtain session for background alert matching: %s",
            outer_e,
            exc_info=True,
        )
