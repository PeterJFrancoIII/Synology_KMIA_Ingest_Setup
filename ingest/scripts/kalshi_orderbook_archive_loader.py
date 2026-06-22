#!/usr/bin/env python3
"""Load archived Kalshi orderbook snapshots at the prior-day 10 AM ET anchor.

Used by kalshi_price_history_loader for maker-fill simulation and book-based
liquidity caps. Falls back to CSV-only when archive is missing.

NO REAL TRADING — reference data only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from kalshi_price_history_loader import (
    anchor_time_utc_for_settlement,
    event_ticker_for_settlement,
    parse_kalshi_column_header,
)

ANCHOR_BOOK_MAX_DELTA_MINUTES = 45.0
DEFAULT_TOP_OF_BOOK_PARTICIPATION = 0.25


def default_orderbook_archive_dir() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_market_archive_dir, optional_existing

    return optional_existing(kalshi_market_archive_dir())


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def extract_top_of_book(orderbook: dict[str, Any]) -> dict[str, Any]:
    """Normalize archived orderbook entry to top-of-book dollars + size."""
    out: dict[str, Any] = {
        "yes_bid_dollars": orderbook.get("top_yes_bid_dollars"),
        "yes_ask_dollars": orderbook.get("top_yes_ask_dollars"),
        "no_bid_dollars": orderbook.get("top_no_bid_dollars"),
        "no_ask_dollars": orderbook.get("top_no_ask_dollars"),
        "last_price_dollars": orderbook.get("last_price_dollars"),
        "yes_ask_size": orderbook.get("yes_ask_size"),
        "yes_bid_size": orderbook.get("yes_bid_size"),
        "top_of_book_source": orderbook.get("top_of_book_source"),
    }

    yes_bids = orderbook.get("yes_bids") or []
    no_bids = orderbook.get("no_bids") or []
    if yes_bids and isinstance(yes_bids[0], (list, tuple)) and len(yes_bids[0]) >= 2:
        if out["yes_bid_dollars"] is None:
            out["yes_bid_dollars"] = round(float(yes_bids[0][0]) / 100.0, 4)
        if out["yes_bid_size"] is None:
            out["yes_bid_size"] = int(yes_bids[0][1])
    if no_bids and isinstance(no_bids[0], (list, tuple)) and len(no_bids[0]) >= 1:
        if out["yes_ask_dollars"] is None:
            out["yes_ask_dollars"] = round((100.0 - float(no_bids[0][0])) / 100.0, 4)
        if out["yes_ask_size"] is None and len(no_bids[0]) >= 2:
            out["yes_ask_size"] = int(no_bids[0][1])

    for key in ("yes_bid_dollars", "yes_ask_dollars"):
        if out[key] is not None:
            out[key] = round(float(out[key]), 4)
    if out["yes_ask_dollars"] is not None:
        out["yes_ask_cents"] = round(out["yes_ask_dollars"] * 100.0, 2)
    return out


@dataclass
class AnchorOrderbookContext:
    settlement_date: str
    found: bool
    event_ticker: str = ""
    fetched_at_utc: Optional[str] = None
    delta_minutes_from_anchor: Optional[float] = None
    archive_path: Optional[str] = None
    by_bin: dict[str, dict[str, Any]] = field(default_factory=dict)
    reason: Optional[str] = None

    def yes_ask_dollars(self, bin_label: str) -> Optional[float]:
        row = self.by_bin.get(bin_label) or {}
        val = row.get("yes_ask_dollars")
        return float(val) if val is not None else None

    def yes_ask_cents(self, bin_label: str) -> Optional[float]:
        row = self.by_bin.get(bin_label) or {}
        if row.get("yes_ask_cents") is not None:
            return float(row["yes_ask_cents"])
        ask = self.yes_ask_dollars(bin_label)
        return round(ask * 100.0, 2) if ask is not None else None

    def yes_ask_size(self, bin_label: str) -> Optional[int]:
        row = self.by_bin.get(bin_label) or {}
        size = row.get("yes_ask_size")
        if size is None:
            return None
        try:
            return int(size)
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement_date": self.settlement_date,
            "found": self.found,
            "event_ticker": self.event_ticker,
            "fetched_at_utc": self.fetched_at_utc,
            "delta_minutes_from_anchor": self.delta_minutes_from_anchor,
            "archive_path": self.archive_path,
            "bins_with_book": sorted(self.by_bin.keys()),
            "reason": self.reason,
        }


def _iter_archive_records(
    archive_dir: Path,
    utc_dates: list[datetime.date],
) -> Iterator[tuple[dict[str, Any], str]]:
    for day in utc_dates:
        path = archive_dir / "orderbooks" / f"{day.isoformat()}.jsonl"
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line), str(path)
                except json.JSONDecodeError:
                    continue


def _record_matches_event(record: dict[str, Any], event_ticker: str) -> bool:
    event_ticker = event_ticker.upper()
    for m in record.get("markets_compact") or []:
        et = (m.get("event_ticker") or "").upper()
        tick = (m.get("ticker") or "").upper()
        if et == event_ticker or tick.startswith(event_ticker + "-"):
            return True
    for tick in (record.get("orderbooks") or {}):
        if tick.upper().startswith(event_ticker + "-"):
            return True
    return False


def _subtitle_to_bin_label(subtitle: str, column_map: dict[str, str]) -> Optional[str]:
    subtitle = subtitle.strip()
    if subtitle in column_map:
        return column_map[subtitle]
    parsed = parse_kalshi_column_header(subtitle)
    if parsed:
        return parsed
    for col, label in column_map.items():
        if col.strip() == subtitle:
            return label
    return None


def _map_record_to_bins(
    record: dict[str, Any],
    column_map: dict[str, str],
    event_ticker: str,
) -> dict[str, dict[str, Any]]:
    event_ticker = event_ticker.upper()
    ticker_to_subtitle: dict[str, str] = {}
    for m in record.get("markets_compact") or []:
        tick = (m.get("ticker") or "").upper()
        et = (m.get("event_ticker") or "").upper()
        if et != event_ticker and not tick.startswith(event_ticker + "-"):
            continue
        sub = (m.get("subtitle") or m.get("title") or "").strip()
        if sub:
            ticker_to_subtitle[tick] = sub

    by_bin: dict[str, dict[str, Any]] = {}
    for ticker, ob in (record.get("orderbooks") or {}).items():
        tick_u = ticker.upper()
        sub = ticker_to_subtitle.get(tick_u)
        if not sub and tick_u.startswith(event_ticker + "-"):
            sub = ticker_to_subtitle.get(tick_u)
        if not sub:
            continue
        bin_label = _subtitle_to_bin_label(sub, column_map)
        if not bin_label:
            continue
        by_bin[bin_label] = extract_top_of_book(ob if isinstance(ob, dict) else {})
    return by_bin


def load_anchor_orderbook_context(
    settlement_date: str,
    column_map: dict[str, str],
    archive_dir: Optional[Path] = None,
    *,
    max_delta_minutes: float = ANCHOR_BOOK_MAX_DELTA_MINUTES,
) -> AnchorOrderbookContext:
    """Find archived orderbook snapshot closest to prior-day 10 AM ET anchor."""
    event_ticker = event_ticker_for_settlement(settlement_date)
    base = AnchorOrderbookContext(
        settlement_date=settlement_date,
        found=False,
        event_ticker=event_ticker,
    )
    if archive_dir is None:
        archive_dir = default_orderbook_archive_dir()
    if archive_dir is None or not Path(archive_dir).is_dir():
        base.reason = "archive_dir_missing"
        return base

    archive_dir = Path(archive_dir)
    anchor = anchor_time_utc_for_settlement(settlement_date)
    utc_dates = [
        anchor.date(),
        (anchor + timedelta(days=1)).date(),
    ]

    best_record: Optional[dict[str, Any]] = None
    best_path: Optional[str] = None
    best_delta: Optional[float] = None

    for record, path in _iter_archive_records(archive_dir, utc_dates):
        if not _record_matches_event(record, event_ticker):
            continue
        ts = _parse_ts(record.get("fetched_at_utc"))
        if ts is None:
            continue
        delta_min = (ts - anchor).total_seconds() / 60.0
        if delta_min < -5.0 or delta_min > max_delta_minutes:
            continue
        if best_delta is None or abs(delta_min) < abs(best_delta):
            best_record = record
            best_path = path
            best_delta = delta_min

    if best_record is None:
        base.reason = "no_snapshot_near_anchor"
        return base

    by_bin = _map_record_to_bins(best_record, column_map, event_ticker)
    if not by_bin:
        base.reason = "snapshot_unmapped_to_bins"
        base.fetched_at_utc = best_record.get("fetched_at_utc")
        base.archive_path = best_path
        return base

    return AnchorOrderbookContext(
        settlement_date=settlement_date,
        found=True,
        event_ticker=event_ticker,
        fetched_at_utc=best_record.get("fetched_at_utc"),
        delta_minutes_from_anchor=round(best_delta, 2) if best_delta is not None else None,
        archive_path=best_path,
        by_bin=by_bin,
    )
