from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except ZoneInfoNotFoundError:
    VIETNAM_TZ = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")


def appointment_datetime(day: date, value: time) -> datetime:
    return datetime.combine(day, value, tzinfo=VIETNAM_TZ)


def _escape_ical(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def calendar_values(*, inquiry_id: str, day: date, start: time, end: time, title: str, location: str) -> tuple[str, str, str]:
    starts_at = appointment_datetime(day, start)
    ends_at = appointment_datetime(day, end)
    google_url = "https://calendar.google.com/calendar/render?" + urlencode({
        "action": "TEMPLATE",
        "text": title,
        "location": location,
        "dates": f"{starts_at.strftime('%Y%m%dT%H%M%S')}/{ends_at.strftime('%Y%m%dT%H%M%S')}",
        "ctz": "Asia/Ho_Chi_Minh",
    })
    uid = f"viewing-{inquiry_id}@space247.vn"
    ical = "\r\n".join((
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Space247//Viewing//EN", "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID=Asia/Ho_Chi_Minh:{starts_at.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND;TZID=Asia/Ho_Chi_Minh:{ends_at.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{_escape_ical(title)}", f"LOCATION:{_escape_ical(location)}", "END:VEVENT", "END:VCALENDAR", "",
    ))
    return google_url, uid, ical
