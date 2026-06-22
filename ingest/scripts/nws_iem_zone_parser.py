"""Parse IEM-archived NWS zone forecast text (ZFPMFL) for KMIA coastal Miami-Dade."""

from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# Coastal Miami-Dade — closest NWS zone text to MapClick pin at KMIA.
DEFAULT_ZONE_ID = "FLZ173"

_WMO_HEADER_RE = re.compile(
    r"FPUS52\s+KMFL\s+(?P<ddhhmm>\d{6})",
    re.MULTILINE,
)
_ZONE_BLOCK_RE = re.compile(
    rf"^{DEFAULT_ZONE_ID}-\d{{6}}-\s*\n(.*?)(?:\n\$\$|\Z)",
    re.MULTILINE | re.DOTALL,
)
_PERIOD_RE = re.compile(
    r"\.(?P<name>[A-Z]+(?:\s+NIGHT)?)\.\.\.(?P<body>.*?)(?=\.[A-Z]|\Z)",
    re.DOTALL,
)
_HIGHS_RE = re.compile(
    r"Highs?(?:\s+in\s+the\s+|\s+)(?P<phrase>[^.\n]+)",
    re.IGNORECASE,
)
_PHRASE_RULES: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"^lower\s+(\d+)s$", re.I), 2),
    (re.compile(r"^mid\s+(\d+)s$", re.I), 5),
    (re.compile(r"^upper\s+(\d+)s$", re.I), 8),
    (re.compile(r"^around\s+(\d+)$", re.I), 0),
    (re.compile(r"^near\s+(\d+)$", re.I), 0),
    (re.compile(r"^(\d+)$", re.I), 0),
)


def settlement_weekday_period(settlement_date: str) -> str:
    dt = datetime.strptime(settlement_date, "%Y-%m-%d")
    return calendar.day_name[dt.weekday()].upper()


def phrase_to_high_f(phrase: str) -> Optional[int]:
    text = phrase.strip().rstrip(".")
    for pattern, offset in _PHRASE_RULES:
        m = pattern.match(text)
        if m:
            base = int(m.group(1))
            return base + offset
    return None


def parse_zone_daytime_high(
    product_text: str,
    settlement_date: str,
    *,
    zone_id: str = DEFAULT_ZONE_ID,
) -> Optional[int]:
    """Return integer °F high for settlement_date from a ZFPMFL zone block."""
    if zone_id != DEFAULT_ZONE_ID:
        block_re = re.compile(
            rf"^{re.escape(zone_id)}-\d{{6}}-\s*\n(.*?)(?:\n\$\$|\Z)",
            re.MULTILINE | re.DOTALL,
        )
    else:
        block_re = _ZONE_BLOCK_RE

    period_name = settlement_weekday_period(settlement_date)
    for block in block_re.findall(product_text):
        for pm in _PERIOD_RE.finditer(block):
            name = pm.group("name").strip()
            if name != period_name:
                continue
            body = pm.group("body")
            hm = _HIGHS_RE.search(body)
            if not hm:
                continue
            return phrase_to_high_f(hm.group("phrase"))
    return None


def parse_wmo_issue_utc(wmo_ddhhmm: str, anchor_utc: datetime) -> datetime:
    """Decode WMO DDHHMM (UTC) relative to anchor (handles month boundaries)."""
    day = int(wmo_ddhhmm[:2])
    hour = int(wmo_ddhhmm[2:4])
    minute = int(wmo_ddhhmm[4:6])
    anchor_et = anchor_utc.astimezone(ET)
    candidates: list[datetime] = []
    for month_delta in (0, -1, 1):
        month = anchor_et.month + month_delta
        year = anchor_et.year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        try:
            candidates.append(datetime(year, month, day, hour, minute, tzinfo=timezone.utc))
        except ValueError:
            continue
    if not candidates:
        raise ValueError(f"invalid WMO time {wmo_ddhhmm}")
    # Pick candidate closest to anchor (must be before anchor + slack)
    slack = anchor_utc + timedelta(minutes=30)
    before = [c for c in candidates if c <= slack]
    if before:
        return max(before, key=lambda c: c.timestamp())
    return min(candidates, key=lambda c: abs(c.timestamp() - anchor_utc.timestamp()))


def split_iem_products(raw: str) -> list[str]:
    """Split IEM AFOS retrieve payload into individual products."""
    text = raw.replace("\x01", "")
    chunks = re.split(r"(?=FPUS52\s+KMFL)", text)
    return [c.strip() for c in chunks if c.strip()]


def pick_product_before_anchor(
    products: list[str],
    anchor_utc: datetime,
) -> Optional[tuple[datetime, str]]:
    """Choose latest ZFPMFL product issued at or before anchor (+30 min slack)."""
    slack = anchor_utc.timestamp() + 30 * 60
    candidates: list[tuple[datetime, str]] = []
    for product in products:
        m = _WMO_HEADER_RE.search(product)
        if not m:
            continue
        issued = parse_wmo_issue_utc(m.group("ddhhmm"), anchor_utc)
        if issued.timestamp() <= slack:
            candidates.append((issued, product))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0]


def build_daily_period(
    settlement_date: str,
    high_f: int,
    *,
    issued_utc: datetime,
) -> dict[str, Any]:
    dt = datetime.strptime(settlement_date, "%Y-%m-%d").replace(tzinfo=ET)
    start = dt.replace(hour=6).isoformat()
    return {
        "valid_time_utc": start,
        "forecast_date_et": settlement_date,
        "display_day": dt.strftime("%a %m/%d"),
        "period_name": calendar.day_name[dt.weekday()],
        "isDaytime": True,
        "temperature_f": high_f,
        "temperature_unit": "F",
        "shortForecast": f"High near {high_f}",
        "detailedForecast": f"High near {high_f} (IEM-archived NWS zone forecast).",
        "raw_message": f"High near {high_f}",
    }
