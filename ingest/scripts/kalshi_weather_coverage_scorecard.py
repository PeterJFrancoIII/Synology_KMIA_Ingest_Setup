#!/usr/bin/env python3
"""Read-only Kalshi weather coverage scorecard for backtest planning.

Reports real NWS/rules_v2 forecast coverage and official NCEI CLIMIA TMAX
observed coverage. Does NOT write, backfill, or synthesize weather data.

NO REAL TRADING — coverage reporting only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    default_kalshi_observed_jsonl,
    default_kmia_daily_history_jsonl,
    forecast_high_at_anchor,
    load_ncei_climatology_tmaxes,
    load_observed_daily_maxes,
    load_settlement_observed_maxes,
)
from iem_mos_forecast_archive import default_iem_mos_archive_path
from kalshi_price_history_loader import discover_price_history_files

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 SCORECARD ONLY",
}


def forecast_available(
    settlement_date: str,
    *,
    nws_dir: Optional[Path],
    reports_dir: Optional[Path],
    iem_mos_archive: Optional[Path],
) -> tuple[bool, str]:
    fc = forecast_high_at_anchor(
        settlement_date,
        nws_dir=nws_dir,
        reports_dir=reports_dir,
        iem_mos_archive=iem_mos_archive,
    )
    if fc.get("found"):
        return True, str(fc.get("source") or "unknown")
    return False, "none"


def coverage_scorecard(
    settlement_days: list[str],
    *,
    nws_dir: Optional[Path],
    reports_dir: Optional[Path],
    observed_jsonl: Optional[Path],
    ncei_history_jsonl: Optional[Path],
    iem_mos_archive: Optional[Path],
) -> dict[str, Any]:
    ncei = (
        load_ncei_climatology_tmaxes(ncei_history_jsonl)
        if ncei_history_jsonl else {}
    )
    live_nws = load_observed_daily_maxes(observed_jsonl) if observed_jsonl else {}
    settlement_obs = load_settlement_observed_maxes(
        ncei_history_jsonl=ncei_history_jsonl,
        nws_observed_jsonl=observed_jsonl,
    )
    fc_days: list[str] = []
    ncei_days: list[str] = []
    live_nws_days: list[str] = []
    both_days: list[str] = []
    fc_sources: dict[str, str] = {}
    for day in settlement_days:
        has_fc, src = forecast_available(
            day, nws_dir=nws_dir, reports_dir=reports_dir, iem_mos_archive=iem_mos_archive
        )
        if has_fc:
            fc_days.append(day)
            fc_sources[day] = src
        if day in ncei:
            ncei_days.append(day)
        if day in live_nws:
            live_nws_days.append(day)
        if has_fc and day in settlement_obs:
            both_days.append(day)
    total = len(settlement_days)
    return {
        "total_price_days": total,
        "forecast_coverage": len(fc_days),
        "ncei_climatology_coverage": len(ncei_days),
        "live_nws_observed_coverage": len(live_nws_days),
        "settlement_observed_coverage": len([d for d in settlement_days if d in settlement_obs]),
        "full_join_coverage": len(both_days),
        "forecast_pct": round(100 * len(fc_days) / total, 1) if total else 0,
        "ncei_observed_pct": round(100 * len(ncei_days) / total, 1) if total else 0,
        "full_join_pct": round(100 * len(both_days) / total, 1) if total else 0,
        "missing_forecast": [d for d in settlement_days if d not in fc_days],
        "missing_ncei_observed": [d for d in settlement_days if d not in ncei],
        "forecast_sources": fc_sources,
        "policy": "real_weather_only_no_simulation",
        "safety": _SAFETY,
    }


def print_scorecard_human(card: dict[str, Any]) -> None:
    total = card.get("total_price_days", 0)
    fc = card.get("forecast_coverage", 0)
    ncei = card.get("ncei_climatology_coverage", 0)
    both = card.get("full_join_coverage", 0)
    print("=" * 56)
    print("  KALSHI BACKTEST DATA SCORECARD (REAL WEATHER ONLY)")
    print("  NO SIMULATED / BACKFILLED FORECAST OR OBSERVED DATA")
    print("=" * 56)
    print(f"  Price-history days:        {total}")
    print(f"  Forecast (NWS/rules_v2):   {fc}/{total}  ({card.get('forecast_pct', 0)}%)")
    print(f"  Observed (NCEI CLIMIA):    {ncei}/{total}  ({card.get('ncei_observed_pct', 0)}%)")
    print(f"  Full join (FC+NCEI obs):   {both}/{total}  ({card.get('full_join_pct', 0)}%)")
    if fc < total:
        miss = card.get("missing_forecast", [])
        print(f"  Missing forecast:          {len(miss)} days")
    if ncei < total:
        miss = card.get("missing_ncei_observed", [])
        print(f"  Missing NCEI observed:     {len(miss)} days")
    if both >= 20:
        print("  Policy confidence tier:     MEDIUM (≥20 scored days)")
    elif both >= 10:
        print("  Policy confidence tier:     LOW-MEDIUM (≥10 scored days)")
    elif both >= 5:
        print("  Policy confidence tier:     LOW (≥5 scored days)")
    else:
        print("  Policy confidence tier:     VERY LOW (<5 scored days)")
    print("=" * 56)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--price-history-dir",
        type=Path,
        default=Path(
            "/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History"
        ),
    )
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--observed-jsonl", type=Path, default=None)
    parser.add_argument("--ncei-history-jsonl", type=Path, default=None)
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    nws_dir = args.nws_dir or default_kalshi_nws_dir()
    observed_jsonl = args.observed_jsonl or default_kalshi_observed_jsonl()
    ncei_history = args.ncei_history_jsonl or default_kmia_daily_history_jsonl()
    iem_archive = default_iem_mos_archive_path()
    reports_dir = args.reports_dir or default_kalshi_forecast_reports_dir()

    days = sorted(discover_price_history_files(args.price_history_dir).keys())
    if args.start_date:
        days = [d for d in days if d >= args.start_date]
    if args.end_date:
        days = [d for d in days if d <= args.end_date]

    card = coverage_scorecard(
        days,
        nws_dir=nws_dir,
        reports_dir=reports_dir,
        observed_jsonl=observed_jsonl,
        ncei_history_jsonl=ncei_history,
        iem_mos_archive=iem_archive,
    )
    if args.json:
        print(json.dumps(card, indent=2))
    else:
        print_scorecard_human(card)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
