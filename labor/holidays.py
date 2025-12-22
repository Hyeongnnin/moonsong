import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
from django.core.cache import cache

HOLIDAY_ICS_URL = "https://calendar.google.com/calendar/ical/ko.south_korea%23holiday%40group.v.calendar.google.com/public/full.ics"
CACHE_TTL = 60 * 60 * 24  # 24 hours
logger = logging.getLogger(__name__)

HOLIDAY_TYPE_LEGAL = "LEGAL"
HOLIDAY_TYPE_OBSERVANCE = "OBSERVANCE"

_LEGAL_KEYWORDS = tuple(
    keyword.lower()
    for keyword in [
        "새해 첫날",
        "신정",
        "new year's day",
        "설날",
        "설날 연휴",
        "추석",
        "추석 연휴",
        "lunar new year",
        "korean thanksgiving",
        "삼일절",
        "부처님 오신 날",
        "부처님오신날",
        "석가탄신일",
        "buddha's birthday",
        "어린이날",
        "children's day",
        "현충일",
        "memorial day",
        "광복절",
        "liberation day",
        "개천절",
        "national foundation day",
        "한글날",
        "hangul day",
        "성탄절",
        "christmas day",
        "근로자의 날",
        "근로자의날",
        "labor day",
        "임시공휴일",
        "임시 공휴일",
        "temporary holiday",
        "대체공휴일",
        "대체 공휴일",
        "대체휴일",
        "대체 휴일",
        "substitute holiday",
        "선거",
        "선거일",
        "election day",
        "투표",
        "국회의원 선거",
        "국회의원 재보궐선거",
        "전국동시지방선거",
        "대통령 선거",
        "국민투표",
    ]
)


def _normalize(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def _classify_event(summary: str) -> str:
    normalized = _normalize(summary)
    if not normalized:
        return HOLIDAY_TYPE_OBSERVANCE

    for keyword in _LEGAL_KEYWORDS:
        if keyword in normalized:
            return HOLIDAY_TYPE_LEGAL

    if "크리스마스" in normalized and "이브" not in normalized:
        return HOLIDAY_TYPE_LEGAL
    if "christmas" in normalized and "eve" not in normalized:
        return HOLIDAY_TYPE_LEGAL

    return HOLIDAY_TYPE_OBSERVANCE


def _fetch_ics_text() -> str:
    response = requests.get(HOLIDAY_ICS_URL, timeout=10)
    response.raise_for_status()
    return response.text


def _parse_holidays(ics_text: str) -> List[Dict]:
    events: List[Dict] = []
    blocks = ics_text.split("BEGIN:VEVENT")
    for block in blocks[1:]:
        lines = block.splitlines()
        date_value = None
        summary_value = None
        for raw_line in lines:
            line = raw_line.strip()
            if line.startswith("DTSTART"):
                try:
                    _, date_part = line.split(":", 1)
                except ValueError:
                    continue
                date_value = date_part.strip()[:8]
            elif line.startswith("SUMMARY"):
                try:
                    _, summary_part = line.split(":", 1)
                except ValueError:
                    continue
                summary_value = summary_part.strip()
        if date_value and summary_value:
            try:
                parsed_date = datetime.strptime(date_value, "%Y%m%d").date()
                events.append(
                    {
                        "date": parsed_date,
                        "name": summary_value,
                        "type": _classify_event(summary_value),
                    }
                )
            except ValueError:
                logger.warning("Failed to parse holiday date: %s", date_value)
    return events


def get_holidays_for_month(year: int, month: int) -> List[Dict[str, str]]:
    cache_key = f"holidays:{year:04d}-{month:02d}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        ics_text = _fetch_ics_text()
        events = _parse_holidays(ics_text)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to fetch/parse holiday ICS: %s", exc)
        return []

    month_events = [
        {
            "date": event["date"].isoformat(),
            "name": event["name"],
            "type": event.get("type", HOLIDAY_TYPE_LEGAL),
        }
        for event in events
        if event["date"].year == year and event["date"].month == month
    ]

    cache.set(cache_key, month_events, CACHE_TTL)
    return month_events
