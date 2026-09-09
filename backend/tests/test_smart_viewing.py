from datetime import date, time
from urllib.parse import parse_qs, urlparse

import pytest
from pydantic import ValidationError

from src.schemas.rental_management import ViewingScheduleReplaceRequest, ViewingScheduleWindow
from src.services.viewing_calendar import calendar_values


def test_schedule_rejects_overlapping_windows() -> None:
    with pytest.raises(ValidationError):
        ViewingScheduleReplaceRequest(windows=[
            ViewingScheduleWindow(weekday=0, start_time=time(9), end_time=time(12)),
            ViewingScheduleWindow(weekday=0, start_time=time(11), end_time=time(13)),
        ])


def test_schedule_accepts_adjacent_windows_and_monday_zero() -> None:
    payload = ViewingScheduleReplaceRequest(windows=[
        ViewingScheduleWindow(weekday=0, start_time=time(9), end_time=time(10)),
        ViewingScheduleWindow(weekday=0, start_time=time(10), end_time=time(11)),
    ])
    assert [window.weekday for window in payload.windows] == [0, 0]


def test_confirmed_calendar_payload_has_matching_vietnam_civil_time_and_location() -> None:
    google, uid, ical = calendar_values(
        inquiry_id="00000000-0000-0000-0000-000000000001",
        day=date(2026, 9, 14), start=time(9, 30), end=time(10), title="Xem phòng P.101", location="10 Tạ Quang Bửu, Hà Nội",
    )
    params = parse_qs(urlparse(google).query)
    assert params["ctz"] == ["Asia/Ho_Chi_Minh"]
    assert params["dates"] == ["20260914T093000/20260914T100000"]
    assert uid in ical
    assert "DTSTART;TZID=Asia/Ho_Chi_Minh:20260914T093000" in ical
    assert "DTEND;TZID=Asia/Ho_Chi_Minh:20260914T100000" in ical
    assert "LOCATION:10 Tạ Quang Bửu\\, Hà Nội" in ical


def test_calendar_text_escapes_ical_values() -> None:
    _, _, ical = calendar_values(inquiry_id="one", day=date(2026, 9, 14), start=time(9), end=time(10), title="A, B", location="A; B")
    assert "SUMMARY:A\\, B" in ical
    assert "LOCATION:A\\; B" in ical
