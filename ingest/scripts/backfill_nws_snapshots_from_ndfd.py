#!/usr/bin/env python3
"""Write aligned NWS snapshot JSON from NDFD point maxT at 25.7906 / -80.3164.

Replaces IEM zone-text backfill for Kalshi historical joins. Requires Legion5
VALID_ONLY maxt CSVs extracted with kmia_station pin (wgrib2 -lon).

NO REAL TRADING — archival ingest only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from kalshi_nws_join import default_kalshi_nws_dir, nws_forecast_high_at_anchor
from kalshi_price_history_loader import anchor_time_utc_for_settlement, discover_price_history_files
from kmia_kalshi_paths import console2_root, kalshi_root, optional_existing
from ndfd_kalshi_forecast import (
    SOURCE,
    build_ndfd_nws_snapshot,
    discover_ndfd_maxt_csvs,
    merge_ndfd_maxt_csvs,
    ndfd_forecast_high_at_anchor,
)
from weather_data_policy import is_usable_nws_snapshot

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 NDFD ARCHIVAL BACKFILL ONLY",
}


def default_ndfd_search_roots() -> list[Path]:
    roots: list[Path] = []
    for env_name, default in (
        ("NDFD_KALSHI_SEARCH_ROOT", None),
        ("KMIA_ROOT", Path("/d/KMIA_Process")),
        ("KMIA_ROOT", Path("/e/KMIA_Ingest")),
    ):
        import os

        raw = os.environ.get(env_name)
        if raw:
            roots.append(Path(raw))
        elif default:
            roots.append(default)
    roots.append(kalshi_root() / "backend" / "data" / "processed" / "ndfd_kalshi")
    roots.append(console2_root() / "Research" / "NDFD_Kalshi_Anchor")
    return roots


def default_merged_ndfd_csv() -> Path:
    import os

    raw = os.environ.get("NDFD_KALSHI_MAXT_CSV")
    if raw:
        return Path(raw)
    for candidate in (
        kalshi_root() / "backend/data/processed/ndfd_kalshi/kalshi_ndfd_maxt_VALID_ONLY.csv",
        console2_root() / "Research/NDFD_Kalshi_Anchor/kalshi_ndfd_maxt_VALID_ONLY.csv",
        Path("/d/KMIA_Process/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv"),
    ):
        if candidate.is_file():
            return candidate
    return console2_root() / "Research/NDFD_Kalshi_Anchor/kalshi_ndfd_maxt_VALID_ONLY.csv"


def quarantine_all_iem_snapshots(nws_dir: Path) -> int:
    """Move legacy IEM zone-text snapshots aside before NDFD gridpoint backfill."""
    import shutil

    nws_dir = Path(nws_dir)
    quarantine = nws_dir / "_quarantine_iem_zone"
    quarantine.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in nws_dir.glob("nws_kmia_snapshot_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("source") != "nws_iem_afos_archive":
            continue
        shutil.move(str(path), str(quarantine / path.name))
        moved += 1
    return moved


def _remove_iem_snapshots_for_day(nws_dir: Path, settlement_date: str) -> int:
    removed = 0
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    for path in list(nws_dir.glob("nws_kmia_snapshot_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("source") != "nws_iem_afos_archive":
            continue
        if data.get("settlement_date_et") == settlement_date:
            path.unlink(missing_ok=True)
            removed += 1
            continue
        ts_raw = data.get("fetched_at_utc")
        if not ts_raw:
            continue
        ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if abs((ts - anchor_utc).total_seconds()) < 86400:
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def _has_live_nws_at_anchor(nws_dir: Path, settlement_date: str) -> bool:
    fc = nws_forecast_high_at_anchor(nws_dir, settlement_date)
    if not fc.get("found"):
        return False
    path = Path(str(fc.get("snapshot_path") or ""))
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return data.get("source") == "api.weather.gov" and is_usable_nws_snapshot(data)


def backfill_day(
    settlement_date: str,
    *,
    ndfd_csv: Path,
    nws_dir: Path,
    dry_run: bool,
    force: bool,
    replace_iem: bool,
) -> dict[str, Any]:
    if not force and _has_live_nws_at_anchor(nws_dir, settlement_date):
        return {"day": settlement_date, "status": "skipped", "reason": "live_api_snapshot_exists"}

    fc = ndfd_forecast_high_at_anchor(ndfd_csv, settlement_date)
    if not fc.get("found"):
        return {"day": settlement_date, "status": "missing", "reason": fc.get("reason")}

    release_utc = datetime.fromisoformat(str(fc["release_time_utc"]).replace("Z", "+00:00"))
    snap = build_ndfd_nws_snapshot(
        settlement_date,
        high_f=float(fc["forecast_temp_f"]),
        release_time_utc=release_utc,
    )
    fname_ts = release_utc.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d_%H%M%S")
    out_path = nws_dir / f"nws_kmia_snapshot_{fname_ts}.json"

    if dry_run:
        return {
            "day": settlement_date,
            "status": "dry_run",
            "high_f": fc["forecast_temp_f"],
            "release_utc": fc["release_time_utc"],
            "path": str(out_path),
        }

    nws_dir.mkdir(parents=True, exist_ok=True)
    if replace_iem:
        _remove_iem_snapshots_for_day(nws_dir, settlement_date)
    out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {
        "day": settlement_date,
        "status": "written",
        "high_f": fc["forecast_temp_f"],
        "release_utc": fc["release_time_utc"],
        "path": str(out_path),
        "source": SOURCE,
    }


def resolve_ndfd_csv(args: argparse.Namespace) -> Path:
    if args.ndfd_csv and args.ndfd_csv.is_file():
        return args.ndfd_csv
    if args.merge_monthly:
        roots = [Path(p) for p in args.search_root] if args.search_root else default_ndfd_search_roots()
        paths = discover_ndfd_maxt_csvs(roots)
        if not paths:
            raise SystemExit(f"No NDFD VALID_ONLY CSVs under {roots}")
        out = default_merged_ndfd_csv()
        merge_ndfd_maxt_csvs(paths, out)
        print(f"Merged {len(paths)} CSVs → {out} ({out.stat().st_size} bytes)")
        return out
    merged = default_merged_ndfd_csv()
    if merged.is_file():
        return merged
    raise SystemExit(
        "NDFD CSV not found. Run on Legion5: legion5/52_kalshi_ndfd_anchor_backfill.sh "
        "or pass --ndfd-csv / --merge-monthly"
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ndfd-csv", type=Path, default=None)
    parser.add_argument("--merge-monthly", action="store_true", help="Merge monthly VALID_ONLY CSVs first")
    parser.add_argument("--search-root", type=Path, action="append", default=None)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite even if live api snapshot exists")
    parser.add_argument("--replace-iem", action="store_true", default=True)
    parser.add_argument("--no-replace-iem", action="store_false", dest="replace_iem")
    args = parser.parse_args(argv)

    nws_dir = args.nws_dir or optional_existing(default_kalshi_nws_dir())
    if nws_dir is None:
        print("ERROR: NWS dir not found", file=sys.stderr)
        return 1
    nws_dir = Path(nws_dir)

    ndfd_csv = resolve_ndfd_csv(args)

    if args.replace_iem and not args.dry_run:
        n_moved = quarantine_all_iem_snapshots(nws_dir)
        if n_moved:
            print(f"Quarantined {n_moved} IEM zone snapshots → {nws_dir / '_quarantine_iem_zone'}")

    if args.price_history_dir:
        days = sorted(discover_price_history_files(args.price_history_dir).keys())
    elif args.start_date and args.end_date:
        from datetime import timedelta

        start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        days = []
        cur = start
        while cur <= end:
            days.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
    else:
        print("ERROR: pass --price-history-dir or --start-date and --end-date", file=sys.stderr)
        return 1

    if args.start_date:
        days = [d for d in days if d >= args.start_date]
    if args.end_date:
        days = [d for d in days if d <= args.end_date]

    stats: dict[str, int] = {}
    for day in days:
        row = backfill_day(
            day,
            ndfd_csv=ndfd_csv,
            nws_dir=nws_dir,
            dry_run=args.dry_run,
            force=args.force,
            replace_iem=args.replace_iem,
        )
        stats[row["status"]] = stats.get(row["status"], 0) + 1
        print(
            f"{row['day']}: {row['status']}"
            + (f" high={row.get('high_f')}F" if row.get("high_f") is not None else "")
            + (f" ({row.get('reason')})" if row.get("reason") else "")
        )

    print(f"\nNDFD CSV: {ndfd_csv}")
    print(f"Stats: {stats}")
    return 0 if stats.get("error", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
