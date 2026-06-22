#!/usr/bin/env python3
"""Build Kalshi KXHIGHMIA price-history CSVs from the public API.

Output matches manual export nomenclature:
  kalshi-price-history-kxhighmia-26apr20-minute.csv
  timestamp,<subtitle bin columns from Kalshi>

NO REAL TRADING — reference data ingest only.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from kalshi_market_data_client import (
    candlestick_yes_ask_cents,
    forward_fill_on_grid,
    get_event_markets,
    get_market_candlesticks,
    list_kxhighmia_events,
    market_window_unix,
    minute_end_timestamps,
    candles_to_price_series,
    timestamp_iso_from_unix,
)
from kalshi_price_history_loader import (
    discover_price_history_files,
    event_ticker_for_settlement,
    export_filename_for_settlement,
    load_price_history_csv,
    settlement_date_from_event_ticker,
)

DEFAULT_OUTPUT_DIR = None  # resolved in default_output_dir()
MANIFEST_NAME = ".kalshi_price_history_ingest_manifest.json"

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - PRICE HISTORY INGEST ONLY",
}


def default_output_dir() -> Path:
    from kmia_kalshi_paths import kalshi_price_history_dir

    return kalshi_price_history_dir()


def manifest_path(output_dir: Path) -> Path:
    return Path(output_dir) / MANIFEST_NAME


def load_manifest(output_dir: Path) -> dict[str, Any]:
    path = manifest_path(output_dir)
    if not path.is_file():
        return {"records": {}, "safety": _SAFETY}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"records": {}, "safety": _SAFETY}
    data.setdefault("records", {})
    data.setdefault("safety", _SAFETY)
    return data


def save_manifest(output_dir: Path, manifest: dict[str, Any]) -> None:
    path = manifest_path(output_dir)
    manifest["safety"] = _SAFETY
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def column_header_for_market(market: dict[str, Any]) -> str:
    subtitle = (market.get("subtitle") or market.get("title") or "").strip()
    if subtitle:
        return subtitle
    return market.get("ticker", "unknown")


def build_price_history_table(
    markets: list[dict[str, Any]],
    *,
    start_ts: int,
    end_ts: int,
    period_interval: int = 1,
    minute_grid: bool = True,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Fetch candlesticks for all event bins; return (headers, rows).

    When period_interval=1 and minute_grid=True (default), emit one row per
    minute from market open→close with last yes-ask forward-filled per bin.
    """
    if period_interval != 1:
        minute_grid = False

    columns: list[tuple[str, str]] = []
    series_by_header: dict[str, dict[int, float]] = {}

    for market in markets:
        ticker = market.get("ticker")
        if not ticker:
            continue
        header = column_header_for_market(market)
        columns.append((header, ticker))
        candles = get_market_candlesticks(
            ticker,
            start_ts=start_ts,
            end_ts=end_ts,
            period_interval=period_interval,
        )
        series_by_header[header] = candles_to_price_series(candles)
        time.sleep(0.15)

    headers = [h for h, _ in columns]

    if minute_grid:
        grid = minute_end_timestamps(start_ts, end_ts)
        filled_by_header = {
            h: forward_fill_on_grid(grid, series_by_header.get(h, {}))
            for h in headers
        }
        rows: list[dict[str, Any]] = []
        for ts in grid:
            row: dict[str, Any] = {"timestamp": timestamp_iso_from_unix(ts)}
            for h in headers:
                row[h] = filled_by_header[h].get(ts)
            rows.append(row)
        return headers, rows

    # Sparse: only minutes where at least one bin had an API candlestick update.
    all_ts: set[int] = set()
    for series in series_by_header.values():
        all_ts.update(series.keys())
    rows = []
    for ts in sorted(all_ts):
        row = {"timestamp": timestamp_iso_from_unix(ts)}
        for h in headers:
            row[h] = series_by_header.get(h, {}).get(ts)
        rows.append(row)
    return headers, rows


def write_price_history_csv(
    path: Path,
    headers: list[str],
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fieldnames = ["timestamp", *headers]
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {"timestamp": row["timestamp"]}
            for h in headers:
                val = row.get(h)
                out[h] = "" if val is None else f"{float(val):.2f}"
            writer.writerow(out)
    tmp.replace(path)


def ingest_settlement_day(
    settlement_date: str,
    output_dir: Path,
    *,
    force: bool = False,
    period_interval: int = 1,
    granularity: str = "minute",
    minute_grid: bool = True,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    filename = export_filename_for_settlement(settlement_date, granularity=granularity)
    out_path = output_dir / filename
    if out_path.is_file() and not force:
        return {
            "settlement_date": settlement_date,
            "status": "skipped_existing",
            "output_path": str(out_path),
        }

    event_ticker = event_ticker_for_settlement(settlement_date)
    markets = get_event_markets(event_ticker)
    if len(markets) < 4:
        return {
            "settlement_date": settlement_date,
            "status": "failed",
            "reason": "insufficient_markets",
            "event_ticker": event_ticker,
            "market_count": len(markets),
        }

    start_ts, end_ts = market_window_unix(markets)
    expected_minutes = len(minute_end_timestamps(start_ts, end_ts))
    headers, rows = build_price_history_table(
        markets,
        start_ts=start_ts,
        end_ts=end_ts,
        period_interval=period_interval,
        minute_grid=minute_grid and period_interval == 1,
    )
    if not rows:
        return {
            "settlement_date": settlement_date,
            "status": "failed",
            "reason": "no_candlesticks",
            "event_ticker": event_ticker,
        }

    write_price_history_csv(out_path, headers, rows)

    # Validate loader compatibility
    df, column_map = load_price_history_csv(out_path)
    manifest = load_manifest(output_dir)
    manifest["records"][settlement_date] = {
        "settlement_date": settlement_date,
        "event_ticker": event_ticker,
        "output_path": str(out_path.resolve()),
        "row_count": len(rows),
        "column_count": len(headers),
        "market_count": len(markets),
        "start_ts": start_ts,
        "end_ts": end_ts,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source": "kalshi_api_candlesticks_yes_ask",
        "period_interval": period_interval,
        "minute_grid_forward_fill": minute_grid and period_interval == 1,
        "expected_minute_rows": expected_minutes,
        "loader_columns_mapped": len(column_map),
        "loader_rows": len(df),
    }
    save_manifest(output_dir, manifest)

    return {
        "settlement_date": settlement_date,
        "status": "written",
        "output_path": str(out_path.resolve()),
        "event_ticker": event_ticker,
        "row_count": len(rows),
        "column_count": len(headers),
        "market_count": len(markets),
    }


def discover_ingest_candidates(
    output_dir: Path,
    *,
    include_open: bool = True,
    include_settled: bool = True,
    missing_only: bool = True,
    lookback_days: int = 14,
    lookahead_days: int = 7,
) -> list[str]:
    """Settlement dates to ingest from Kalshi API (recent window by default)."""
    output_dir = Path(output_dir)
    existing = set(discover_price_history_files(output_dir).keys())
    found: set[str] = set()

    statuses: list[Optional[str]] = []
    if include_open:
        statuses.append("open")
    if include_settled:
        statuses.append("settled")

    for status in statuses:
        for event in list_kxhighmia_events(status=status):
            et = event.get("event_ticker") or ""
            day = settlement_date_from_event_ticker(et)
            if day:
                found.add(day)

    today = datetime.now(timezone.utc).date()
    window_start = today - timedelta(days=lookback_days)
    window_end = today + timedelta(days=lookahead_days)

    candidates: list[str] = []
    for day in sorted(found):
        try:
            d = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < window_start or d > window_end:
            continue
        if missing_only and day in existing:
            continue
        candidates.append(day)
    return candidates


def run_ingest(
    output_dir: Path,
    *,
    settlement_dates: Optional[list[str]] = None,
    missing_only: bool = True,
    discover_from_api: bool = True,
    force: bool = False,
    period_interval: int = 1,
    minute_grid: bool = True,
    lookback_days: int = 14,
    lookahead_days: int = 7,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    days = list(settlement_dates or [])
    if discover_from_api and not settlement_dates:
        days = discover_ingest_candidates(
            output_dir,
            missing_only=missing_only,
            lookback_days=lookback_days,
            lookahead_days=lookahead_days,
        )
    elif missing_only and settlement_dates:
        existing = discover_price_history_files(output_dir)
        days = [d for d in days if force or d not in existing]

    results: list[dict[str, Any]] = []
    for day in sorted(set(days)):
        try:
            results.append(
                ingest_settlement_day(
                    day,
                    output_dir,
                    force=force,
                    period_interval=period_interval,
                    minute_grid=minute_grid,
                )
            )
        except Exception as exc:  # noqa: BLE001 — collect per-day API failures
            results.append(
                {
                    "settlement_date": day,
                    "status": "failed",
                    "reason": "api_error",
                    "error": str(exc),
                }
            )

    written = [r for r in results if r.get("status") == "written"]
    skipped = [r for r in results if r.get("status") == "skipped_existing"]
    failed = [r for r in results if r.get("status") == "failed"]

    return {
        "output_dir": str(output_dir.resolve()),
        "candidates": len(days),
        "written": len(written),
        "skipped": len(skipped),
        "failed": len(failed),
        "results": results,
        "safety": _SAFETY,
    }
