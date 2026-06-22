#!/usr/bin/env python3
"""CLI: ingest Kalshi KXHIGHMIA price-history CSVs from the public API.

Writes files into the Bet History folder using the same naming convention as
manual Kalshi exports (kalshi-price-history-kxhighmia-*.csv).

NO REAL TRADING — reference data ingest only.

Examples:
  python3 ingest/scripts/ingest_kalshi_market_data.py
  python3 ingest/scripts/ingest_kalshi_market_data.py --date 2026-06-19 --force
  python3 ingest/scripts/ingest_kalshi_market_data.py --list-candidates
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from kalshi_price_history_ingest import (
    default_output_dir,
    discover_ingest_candidates,
    run_ingest,
)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Bet History folder (default: Kalshi - Miami Max Temp. Bet History)",
    )
    parser.add_argument(
        "--date",
        action="append",
        dest="dates",
        metavar="YYYY-MM-DD",
        help="Specific settlement date(s) to ingest",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing CSV for requested dates",
    )
    parser.add_argument(
        "--all-api-events",
        action="store_true",
        help="Ingest all open+settled API events, not only missing files",
    )
    parser.add_argument(
        "--list-candidates",
        action="store_true",
        help="Print missing settlement dates discoverable from API and exit",
    )
    parser.add_argument(
        "--period-interval",
        type=int,
        default=1,
        choices=[1],
        help="Candlestick period in minutes (only 1 supported for intraday ingest)",
    )
    parser.add_argument(
        "--sparse",
        action="store_true",
        help="Sparse rows only (API update minutes). Default is full minute grid with forward-fill.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=14,
        help="When auto-discovering, include settled events this many days back (default 14)",
    )
    parser.add_argument(
        "--lookahead-days",
        type=int,
        default=7,
        help="When auto-discovering, include open events this many days ahead (default 7)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    out_dir = args.output_dir or default_output_dir()
    if not out_dir.is_dir() and not args.list_candidates:
        raise SystemExit(f"Output dir not found: {out_dir}")

    if args.list_candidates:
        days = discover_ingest_candidates(
            out_dir,
            missing_only=True,
            lookback_days=args.lookback_days,
            lookahead_days=args.lookahead_days,
        )
        if args.json:
            print(json.dumps({"missing_candidates": days}, indent=2))
        else:
            print(f"Missing ingest candidates ({len(days)}):")
            for d in days:
                print(f"  {d}")
        return 0

    report = run_ingest(
        out_dir,
        settlement_dates=args.dates,
        missing_only=not args.all_api_events and not args.dates,
        discover_from_api=not args.dates,
        force=args.force,
        period_interval=args.period_interval,
        minute_grid=not args.sparse,
        lookback_days=args.lookback_days,
        lookahead_days=args.lookahead_days,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"Kalshi price-history ingest: {report['written']} written, "
            f"{report['skipped']} skipped, {report['failed']} failed "
            f"({report['candidates']} candidates)"
        )
        for row in report.get("results", []):
            if row.get("status") == "written":
                print(f"  + {row['settlement_date']} → {row['output_path']} ({row['row_count']} rows)")
            elif row.get("status") == "failed":
                print(f"  ! {row['settlement_date']}: {row.get('reason')}")

    return 1 if report.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
