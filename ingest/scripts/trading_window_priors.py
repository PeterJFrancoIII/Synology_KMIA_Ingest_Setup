"""Expected max-hour priors for Console 2 backtest trading window."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
DEFAULT_BIN_OPEN_HOUR_ET = 10
DEFAULT_CUTOFF_BUFFER_HOURS = 1.0

_DEFAULT_PRIORS = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/expected_max_hour_priors.json"
)


def load_expected_max_hour_priors(path: Optional[Path] = None) -> dict[str, Any]:
    p = Path(path) if path else _DEFAULT_PRIORS
    if not p.is_file():
        return {"weeks": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def week_key_for_date(target_date: str) -> str:
    d = date.fromisoformat(target_date)
    return f"week:{d.isocalendar().week:02d}"


def expected_max_hour_et(target_date: str, *, priors: Optional[dict[str, Any]] = None) -> float:
    data = priors if priors is not None else load_expected_max_hour_priors()
    entry = (data.get("weeks") or {}).get(week_key_for_date(target_date))
    if entry and entry.get("median_hour_et") is not None:
        return float(entry["median_hour_et"])
    return 14.0


def trading_window_end_hour_et(target_date: str) -> float:
    return max(
        float(DEFAULT_BIN_OPEN_HOUR_ET),
        expected_max_hour_et(target_date) - DEFAULT_CUTOFF_BUFFER_HOURS,
    )


def maker_fill_deadline_utc(settlement_date: str) -> datetime:
    """UTC deadline for maker fill scan: target-day (expected_max - 1h) ET."""
    td = date.fromisoformat(settlement_date)
    end_hour = trading_window_end_hour_et(settlement_date)
    h = int(end_hour)
    m = int(round((end_hour - h) * 60))
    end_local = datetime.combine(td, time(h, m), tzinfo=EASTERN)
    return end_local.astimezone(timezone.utc)
