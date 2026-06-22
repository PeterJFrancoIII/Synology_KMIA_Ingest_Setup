#!/usr/bin/env python3
"""Build real IEM GFS MOS forecast archive for Kalshi settlement days missing live NWS.

Writes to iem_gfs_mos_forecast_archive.jsonl — separate from live NWS snapshots.
NO REAL TRADING.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from iem_mos_forecast_archive import (
    build_archive_for_days,
    default_iem_mos_archive_path,
)
from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    forecast_high_at_anchor,
    nws_forecast_high_at_anchor,
    rules_v2_forecast_at_anchor,
)
from kalshi_price_history_loader import discover_price_history_files


def _has_live_forecast(day: str, nws_dir, reports_dir) -> bool:
    if nws_dir and nws_forecast_high_at_anchor(nws_dir, day).get("found"):
        return True
    if reports_dir and rules_v2_forecast_at_anchor(reports_dir, day).get("found"):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--price-history-dir",
        type=Path,
        default=Path(
            "/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History"
        ),
    )
    parser.add_argument("--archive-path", type=Path, default=None)
    parser.add_argument("--only-missing", action="store_true", default=True)
    args = parser.parse_args()

    archive = args.archive_path or default_iem_mos_archive_path()
    if archive is None:
        print("ERROR: IEM MOS archive path not available.", file=sys.stderr)
        return 1

    nws_dir = default_kalshi_nws_dir()
    reports_dir = default_kalshi_forecast_reports_dir()
    days = sorted(discover_price_history_files(args.price_history_dir).keys())
    if args.only_missing:
        days = [d for d in days if not _has_live_forecast(d, nws_dir, reports_dir)]

    result = build_archive_for_days(
        days,
        archive,
        skip_if_live_exists=lambda d: _has_live_forecast(d, nws_dir, reports_dir),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
