#!/usr/bin/env python3
"""Archive full Kalshi candlestick API payloads per settlement day (JSONL).

Complements minute CSV ingest (yes-ask only). One JSONL per event with all bins;
each line is one candlestick. Safe to re-run with --force.

NO REAL TRADING — reference data ingest only.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from kalshi_market_data_client import (
    get_event_markets,
    get_market_candlesticks,
    market_window_unix,
    normalize_candlestick,
)
from kalshi_price_history_ingest import (
    column_header_for_market,
    default_output_dir,
    discover_ingest_candidates,
    event_ticker_for_settlement,
    export_filename_for_settlement,
    load_manifest,
    save_manifest,
)

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CANDLE ARCHIVE ONLY",
}


def default_candle_archive_dir() -> Path:
    from kmia_kalshi_paths import kalshi_candle_archive_dir

    return kalshi_candle_archive_dir()


def candle_archive_filename(settlement_date: str) -> str:
    base = export_filename_for_settlement(settlement_date, granularity="minute")
    return base.replace("-minute.csv", "-candles.jsonl")


def archive_settlement_candles(
    settlement_date: str,
    archive_dir: Path,
    *,
    force: bool = False,
    period_interval: int = 1,
) -> dict[str, Any]:
    archive_dir = Path(archive_dir)
    out_path = archive_dir / candle_archive_filename(settlement_date)
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
        }

    start_ts, end_ts = market_window_unix(markets)
    archive_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    candle_count = 0

    with tmp.open("w", encoding="utf-8") as fh:
        for market in markets:
            ticker = market.get("ticker")
            if not ticker:
                continue
            header = column_header_for_market(market)
            candles = get_market_candlesticks(
                ticker,
                start_ts=start_ts,
                end_ts=end_ts,
                period_interval=period_interval,
            )
            for candle in candles:
                record = {
                    "settlement_date": settlement_date,
                    "event_ticker": event_ticker,
                    "market_ticker": ticker,
                    "column_header": header,
                    "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
                    "candle": normalize_candlestick(candle),
                    "safety": _SAFETY,
                }
                fh.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
                candle_count += 1
            time.sleep(0.15)

    tmp.replace(out_path)
    return {
        "settlement_date": settlement_date,
        "status": "ok",
        "event_ticker": event_ticker,
        "output_path": str(out_path),
        "market_count": len(markets),
        "candle_count": candle_count,
        "start_ts": start_ts,
        "end_ts": end_ts,
    }


def run_archive(
    *,
    archive_dir: Path,
    price_history_dir: Path,
    dates: Optional[list[str]] = None,
    force: bool = False,
    all_api_events: bool = False,
) -> dict[str, Any]:
    archive_dir = Path(archive_dir)
    price_history_dir = Path(price_history_dir)
    if dates:
        candidates = sorted(set(dates))
    elif all_api_events:
        from kalshi_market_data_client import list_kxhighmia_events
        from kalshi_price_history_ingest import settlement_date_from_event_ticker

        found: set[str] = set()
        for status in ("open", "settled"):
            for event in list_kxhighmia_events(status=status):
                day = settlement_date_from_event_ticker(event.get("event_ticker") or "")
                if day:
                    found.add(day)
        candidates = sorted(found)
    else:
        from kalshi_price_history_loader import discover_price_history_files

        candidates = sorted(discover_price_history_files(price_history_dir).keys())

    results: list[dict[str, Any]] = []
    for day in candidates:
        results.append(
            archive_settlement_candles(day, archive_dir, force=force)
        )

    manifest = load_manifest(price_history_dir)
    manifest.setdefault("candle_archive", {})
    for r in results:
        if r.get("status") == "ok":
            manifest["candle_archive"][r["settlement_date"]] = {
                "path": r["output_path"],
                "candle_count": r.get("candle_count"),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
    save_manifest(price_history_dir, manifest)

    ok = sum(1 for r in results if r.get("status") == "ok")
    skipped = sum(1 for r in results if r.get("status") == "skipped_existing")
    failed = [r for r in results if r.get("status") == "failed"]
    return {
        "archive_dir": str(archive_dir.resolve()),
        "candidates": len(candidates),
        "ok": ok,
        "skipped": skipped,
        "failed": len(failed),
        "results": results,
        "safety": _SAFETY,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None, help="Price history dir (manifest)")
    parser.add_argument("--date", action="append", dest="dates", metavar="YYYY-MM-DD")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--all-api-events", action="store_true")
    args = parser.parse_args(argv)

    price_dir = args.output_dir or default_output_dir()
    archive_dir = args.archive_dir or default_candle_archive_dir()
    summary = run_archive(
        archive_dir=archive_dir,
        price_history_dir=price_dir,
        dates=args.dates,
        force=args.force,
        all_api_events=args.all_api_events,
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
