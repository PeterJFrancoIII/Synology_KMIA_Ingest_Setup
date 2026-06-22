#!/usr/bin/env python3
"""Backfill aligned NWS forecast snapshots from IEM AFOS archives.

api.weather.gov exposes only the current grid forecast — not historical JSON.
IEM archives real NWS zone forecast text products (ZFPMFL) from WFO Miami.
We parse the Coastal Miami-Dade zone (FLZ173) at the Kalshi anchor
(prior-day 10 AM ET) and write snapshot JSON compatible with kalshi_nws_join.

Snapshots use the canonical MapClick pin (25.7906, -80.3164 / MFL/105,51).
Zone text is coarser than a grid cell; prefer live api.weather.gov captures
going forward. This fills historical backtest gaps only.

NO REAL TRADING — archival ingest only (no synthetic/proxy values).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from kalshi_nws_join import default_kalshi_nws_dir, nws_forecast_high_at_anchor
from kalshi_price_history_loader import anchor_time_utc_for_settlement, discover_price_history_files
from kmia_station import KMIA_LAT, KMIA_LON, NWS_GRID_ID, NWS_GRID_X, NWS_GRID_Y
from nws_iem_zone_parser import (
    DEFAULT_ZONE_ID,
    build_daily_period,
    parse_zone_daytime_high,
    pick_product_before_anchor,
    split_iem_products,
)

ET = ZoneInfo("America/New_York")
IEM_AFOS_URL = "https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py"
IEM_PRODUCT = "ZFPMFL"
USER_AGENT = "KMIA-Console2-Backfill/1.0 (research; no-trading)"

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 NWS ARCHIVAL BACKFILL ONLY",
}


def _http_get_text(url: str, timeout: int = 120) -> str:
    proc = subprocess.run(
        ["curl", "-sfL", "-A", USER_AGENT, url],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"HTTP fetch failed ({proc.returncode}): {proc.stderr[:200]}")
    body = proc.stdout
    if body.startswith("ERROR:"):
        raise RuntimeError(body.strip())
    return body


def fetch_iem_zfp_window(anchor_date: datetime) -> str:
    """Fetch ZFPMFL products around anchor_date (ET calendar day)."""
    start = (anchor_date - timedelta(days=2)).strftime("%Y-%m-%d")
    end = anchor_date.strftime("%Y-%m-%d")
    url = (
        f"{IEM_AFOS_URL}?pil={IEM_PRODUCT}&fmt=text&limit=30"
        f"&sdate={start}&edate={end}"
    )
    return _http_get_text(url)


def has_usable_forecast_at_anchor(nws_dir: Path, settlement_date: str) -> bool:
    fc = nws_forecast_high_at_anchor(nws_dir, settlement_date)
    return bool(fc.get("found"))


def build_snapshot(
    *,
    settlement_date: str,
    high_f: int,
    issued_utc: datetime,
    zone_id: str,
    product_wmo: str,
) -> dict[str, Any]:
    issued_et = issued_utc.astimezone(ET)
    daily = build_daily_period(settlement_date, high_f, issued_utc=issued_utc)
    grid_suffix = f"{NWS_GRID_ID}/{NWS_GRID_X},{NWS_GRID_Y}"
    return {
        "fetched_at_utc": issued_utc.isoformat(),
        "generated_at_utc": issued_utc.isoformat(),
        "observation_time_utc": None,
        "station": "KMIA",
        "forecast_pin_lat": KMIA_LAT,
        "forecast_pin_lon": KMIA_LON,
        "source": "nws_iem_afos_archive",
        "archival_method": "iem_afos_zfpmfl",
        "archival_zone_id": zone_id,
        "archival_product_pil": IEM_PRODUCT,
        "archival_wmo_header": product_wmo,
        "timeseries_source_url": "https://www.weather.gov/wrh/timeseries?site=kmia",
        "api_observations_url": "https://api.weather.gov/stations/KMIA/observations",
        "api_daily_forecast_url": f"https://api.weather.gov/gridpoints/{grid_suffix}/forecast",
        "api_hourly_forecast_url": f"https://api.weather.gov/gridpoints/{grid_suffix}/forecast/hourly",
        "settlement_authority_status": "ARCHIVAL_RESEARCH",
        "metar_parse_status": "NOT_APPLICABLE",
        "station_status": "OK",
        "forecast_high_f": high_f,
        "daily_forecast": [daily],
        "daily_forecast_count": 1,
        "hourly_forecast": [],
        "hourly_forecast_count": 0,
        "recent_observations_table": [],
        "recent_observations_count": 0,
        "stale_data": False,
        "endpoint_status": "OK",
        "warnings": [
            "Archival NWS zone forecast via IEM AFOS (ZFPMFL). "
            "Zone FLZ173 is coarser than MapClick grid MFL/105,51; "
            "use live api.weather.gov snapshots when available.",
        ],
        "settlement_date_et": settlement_date,
        "anchor_time_utc": anchor_time_utc_for_settlement(settlement_date).isoformat(),
        "issued_time_et": issued_et.strftime("%Y-%m-%d %I:%M %p %Z"),
        "safety": _SAFETY,
    }


def backfill_day(
    settlement_date: str,
    nws_dir: Path,
    *,
    zone_id: str,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    anchor_et = anchor_utc.astimezone(ET)

    if not force and has_usable_forecast_at_anchor(nws_dir, settlement_date):
        return {"day": settlement_date, "status": "skipped", "reason": "forecast_at_anchor_exists"}

    try:
        raw = fetch_iem_zfp_window(anchor_et)
    except RuntimeError as exc:
        return {"day": settlement_date, "status": "error", "reason": str(exc)}

    products = split_iem_products(raw)
    picked = pick_product_before_anchor(products, anchor_utc)
    if not picked:
        return {"day": settlement_date, "status": "missing", "reason": "no_iem_product_before_anchor"}

    issued_utc, product_text = picked
    zone_candidates = [zone_id]
    if zone_id == DEFAULT_ZONE_ID:
        zone_candidates.append("FLZ074")
    high_f = None
    used_zone = zone_id
    for z in zone_candidates:
        high_f = parse_zone_daytime_high(product_text, settlement_date, zone_id=z)
        if high_f is not None:
            used_zone = z
            break
    if high_f is None:
        return {
            "day": settlement_date,
            "status": "missing",
            "reason": f"no_high_in_zone_{zone_id}",
            "issued_utc": issued_utc.isoformat(),
        }

    wmo = "unknown"
    import re

    m = re.search(r"FPUS52\s+KMFL\s+(\d{6})", product_text)
    if m:
        wmo = m.group(1)

    snap = build_snapshot(
        settlement_date=settlement_date,
        high_f=high_f,
        issued_utc=issued_utc,
        zone_id=used_zone,
        product_wmo=wmo,
    )

    fname = f"nws_kmia_snapshot_{issued_utc.astimezone(ET).strftime('%Y-%m-%d_%H%M%S')}.json"
    out_path = nws_dir / fname

    if dry_run:
        return {
            "day": settlement_date,
            "status": "dry_run",
            "high_f": high_f,
            "issued_utc": issued_utc.isoformat(),
            "path": str(out_path),
        }

    nws_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {
        "day": settlement_date,
        "status": "written",
        "high_f": high_f,
        "issued_utc": issued_utc.isoformat(),
        "path": str(out_path),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--zone-id", default=DEFAULT_ZONE_ID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Write even if aligned snapshot exists")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    nws_dir = args.nws_dir or default_kalshi_nws_dir()
    if nws_dir is None:
        print("ERROR: NWS directory not found", file=sys.stderr)
        return 1
    nws_dir = Path(nws_dir)

    if args.price_history_dir:
        days = sorted(discover_price_history_files(args.price_history_dir).keys())
    else:
        days = []

    if args.start_date or args.end_date or not days:
        if not args.start_date or not args.end_date:
            print("ERROR: provide --price-history-dir or both --start-date and --end-date", file=sys.stderr)
            return 1
        start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        cur = start
        days = []
        while cur <= end:
            days.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)

    if args.start_date:
        days = [d for d in days if d >= args.start_date]
    if args.end_date:
        days = [d for d in days if d <= args.end_date]

    results: list[dict[str, Any]] = []
    stats = {"written": 0, "skipped": 0, "missing": 0, "error": 0, "dry_run": 0}

    for day in days:
        row = backfill_day(
            day,
            nws_dir,
            zone_id=args.zone_id,
            dry_run=args.dry_run,
            force=args.force,
        )
        results.append(row)
        stats[row["status"]] = stats.get(row["status"], 0) + 1
        if not args.json:
            print(
                f"{row['day']}: {row['status']}"
                + (f" high={row['high_f']}F" if row.get("high_f") is not None else "")
                + (f" ({row.get('reason')})" if row.get("reason") else "")
            )

    summary = {
        "n_days": len(days),
        "stats": stats,
        "zone_id": args.zone_id,
        "nws_dir": str(nws_dir),
        "results": results,
        "safety": _SAFETY,
    }
    if args.json:
        print(json.dumps(summary, indent=2))

    return 0 if stats.get("error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
