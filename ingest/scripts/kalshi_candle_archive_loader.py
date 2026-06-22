#!/usr/bin/env python3
"""Load archived Kalshi candlesticks at the prior-day 10 AM ET anchor.

Complements minute CSV yes-ask columns with bid/ask/volume from full API
candle JSONL. Used for anchor price validation and future slippage simulation.

NO REAL TRADING — reference data only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from kalshi_candle_archive import candle_archive_filename
from kalshi_market_data_client import (
    candlestick_side_dollars,
    candlestick_yes_ask_cents,
)
from kalshi_price_history_loader import (
    anchor_time_utc_for_settlement,
    parse_kalshi_column_header,
)

ANCHOR_CANDLE_MAX_DELTA_MINUTES = 5.0


def default_candle_archive_dir() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_candle_archive_dir, optional_existing

    return optional_existing(kalshi_candle_archive_dir())


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _header_to_bin_label(header: str, column_map: dict[str, str]) -> Optional[str]:
    header = header.strip()
    if header in column_map:
        return column_map[header]
    parsed = parse_kalshi_column_header(header)
    if parsed:
        return parsed
    for col, label in column_map.items():
        if col.strip() == header:
            return label
    return None


def extract_anchor_candle_fields(candle: dict[str, Any]) -> dict[str, Any]:
    """Flatten one archived candle record to anchor-friendly fields."""
    yes_ask_cents = candlestick_yes_ask_cents(candle)
    yes_bid = candlestick_side_dollars(candle, "yes_bid", "close_dollars")
    yes_ask = candlestick_side_dollars(candle, "yes_ask", "close_dollars")
    return {
        "yes_ask_cents": yes_ask_cents,
        "yes_bid_dollars": yes_bid,
        "yes_ask_dollars": yes_ask,
        "volume": candle.get("volume"),
        "end_period_ts": candle.get("end_period_ts"),
    }


@dataclass
class AnchorCandleContext:
    settlement_date: str
    found: bool
    anchor_time_utc: str = ""
    matched_timestamp_utc: Optional[str] = None
    delta_minutes_from_anchor: Optional[float] = None
    archive_path: Optional[str] = None
    by_bin: dict[str, dict[str, Any]] = field(default_factory=dict)
    reason: Optional[str] = None

    def yes_ask_cents(self, bin_label: str) -> Optional[float]:
        row = self.by_bin.get(bin_label) or {}
        val = row.get("yes_ask_cents")
        return float(val) if val is not None else None

    def yes_ask_dollars(self, bin_label: str) -> Optional[float]:
        row = self.by_bin.get(bin_label) or {}
        if row.get("yes_ask_dollars") is not None:
            return float(row["yes_ask_dollars"])
        cents = self.yes_ask_cents(bin_label)
        return round(cents / 100.0, 4) if cents is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement_date": self.settlement_date,
            "found": self.found,
            "anchor_time_utc": self.anchor_time_utc,
            "matched_timestamp_utc": self.matched_timestamp_utc,
            "delta_minutes_from_anchor": self.delta_minutes_from_anchor,
            "archive_path": self.archive_path,
            "bins_with_candles": sorted(self.by_bin.keys()),
            "reason": self.reason,
        }


def _iter_candle_records(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _candle_end_ts(record: dict[str, Any]) -> Optional[datetime]:
    candle = record.get("candle") or {}
    ts = candle.get("end_period_ts")
    if ts is None:
        return None
    return _parse_ts(ts)


def load_anchor_candle_context(
    settlement_date: str,
    column_map: dict[str, str],
    archive_dir: Optional[Path] = None,
    *,
    max_delta_minutes: float = ANCHOR_CANDLE_MAX_DELTA_MINUTES,
) -> AnchorCandleContext:
    """Pick per-bin candlesticks nearest prior-day 10 AM ET anchor."""
    anchor = anchor_time_utc_for_settlement(settlement_date)
    base = AnchorCandleContext(
        settlement_date=settlement_date,
        found=False,
        anchor_time_utc=anchor.isoformat(),
    )
    if archive_dir is None:
        archive_dir = default_candle_archive_dir()
    if archive_dir is None or not Path(archive_dir).is_dir():
        base.reason = "archive_dir_missing"
        return base

    archive_dir = Path(archive_dir)
    path = archive_dir / candle_archive_filename(settlement_date)
    if not path.is_file():
        base.reason = "candle_file_missing"
        return base

    best_by_bin: dict[str, tuple[float, dict[str, Any], datetime]] = {}

    for record in _iter_candle_records(path):
        header = (record.get("column_header") or "").strip()
        if not header:
            continue
        bin_label = _header_to_bin_label(header, column_map)
        if not bin_label:
            continue
        end_ts = _candle_end_ts(record)
        if end_ts is None:
            continue
        delta_min = (end_ts - anchor).total_seconds() / 60.0
        if delta_min < -max_delta_minutes or delta_min > max_delta_minutes:
            continue
        candle = record.get("candle") or {}
        fields = extract_anchor_candle_fields(candle)
        if fields.get("yes_ask_cents") is None and fields.get("yes_ask_dollars") is None:
            continue
        prev = best_by_bin.get(bin_label)
        if prev is None or abs(delta_min) < abs(prev[0]):
            best_by_bin[bin_label] = (delta_min, fields, end_ts)

    if not best_by_bin:
        base.reason = "no_candles_near_anchor"
        base.archive_path = str(path)
        return base

    by_bin: dict[str, dict[str, Any]] = {}
    deltas: list[float] = []
    latest_ts: Optional[datetime] = None
    for bin_label, (delta_min, fields, end_ts) in best_by_bin.items():
        by_bin[bin_label] = {
            **fields,
            "delta_minutes_from_anchor": round(delta_min, 2),
            "matched_timestamp_utc": end_ts.isoformat(),
        }
        deltas.append(delta_min)
        if latest_ts is None or end_ts > latest_ts:
            latest_ts = end_ts

    return AnchorCandleContext(
        settlement_date=settlement_date,
        found=True,
        anchor_time_utc=anchor.isoformat(),
        matched_timestamp_utc=latest_ts.isoformat() if latest_ts else None,
        delta_minutes_from_anchor=round(sum(deltas) / len(deltas), 2) if deltas else None,
        archive_path=str(path),
        by_bin=by_bin,
    )


def anchor_bin_prices_from_candles(
    ctx: AnchorCandleContext,
) -> dict[str, Optional[float]]:
    """Map candle context to bin_prices_cents dict (CSV-compatible)."""
    out: dict[str, Optional[float]] = {}
    for bin_label, row in ctx.by_bin.items():
        cents = row.get("yes_ask_cents")
        if cents is None and row.get("yes_ask_dollars") is not None:
            cents = round(float(row["yes_ask_dollars"]) * 100.0, 2)
        out[bin_label] = float(cents) if cents is not None else None
    return out
