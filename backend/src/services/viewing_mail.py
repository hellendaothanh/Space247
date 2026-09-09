"""Best-effort background delivery for confirmed viewing calendars."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from src.core.config import settings

logger = logging.getLogger("space247_backend.viewing_mail")


def _send(to_email: str, subject: str, body: str, ical_data: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL or not to_email:
        logger.info("SMTP is not configured; skipped viewing calendar email")
        return
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(ical_data.encode("utf-8"), maintype="text", subtype="calendar", filename="space247-viewing.ics", params={"method": "REQUEST"})
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
            if settings.SMTP_USE_TLS:
                client.starttls()
            if settings.SMTP_USERNAME:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            client.send_message(message)
    except Exception:
        logger.exception("Failed to dispatch viewing calendar email to %s", to_email)


async def dispatch_viewing_calendar_email(*, to_email: str, subject: str, body: str, ical_data: str) -> None:
    await asyncio.to_thread(_send, to_email, subject, body, ical_data)
