#!/usr/bin/env python3
"""Refresh official NCEI GHCN daily TMAX into kmia_daily_history.jsonl.

Fetches USW00012839 daily-summaries from NCEI and merges into the Kalshi
canonical history file. Does not write to NWS observed JSONL.

NO REAL TRADING — official settlement truth only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

NCEI_DAILY_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    "?dataset=daily-summaries"
    "&stations=USW00012839"
    "&dataTypes=TMAX,TMIN,PRCP"
    "&format=json"
    "&units=standard"
)
STATION = "USW00012839"
STATION_NAME = "MIAMI INTERNATIONAL AIRPORT, FL US"


def _default_history_path() -> Path:
    from kmia_kalshi_paths import kmia_daily_history_jsonl

    return kmia_daily_history_jsonl()


def _default_clim_txt() -> Path:
    from kmia_kalshi_paths import ncei_climatology_txt

    return ncei_climatology_txt()


DEFAULT_HISTORY = None  # resolved via _default_history_path()
DEFAULT_CLIM_TXT = None


def _http_get_json(url: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["curl", "-sfL", url],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"NCEI fetch failed: {proc.stderr}")
    data = json.loads(proc.stdout)
    return data if isinstance(data, list) else []


def fetch_ncei_rows(start_date: str, end_date: str) -> list[dict[str, Any]]:
    url = f"{NCEI_DAILY_URL}&startDate={start_date}&endDate={end_date}"
    rows = _http_get_json(url)
    out: list[dict[str, Any]] = []
    for row in rows:
        day = str(row.get("DATE", "")).strip()
        tmax_raw = row.get("TMAX")
        if not day or tmax_raw in (None, "", "M"):
            continue
        try:
            tmax_f = int(float(tmax_raw))
        except (TypeError, ValueError):
            continue
        tmin_f: Optional[int] = None
        if row.get("TMIN") not in (None, "", "M"):
            try:
                tmin_f = int(float(row["TMIN"]))
            except (TypeError, ValueError):
                pass
        prcp_in: Optional[float] = None
        if row.get("PRCP") not in (None, "", "M"):
            try:
                prcp_in = float(row["PRCP"])
            except (TypeError, ValueError):
                pass
        out.append({
            "station": STATION,
            "name": STATION_NAME,
            "date": day,
            "tmax_f": tmax_f,
            "tmin_f": tmin_f,
            "tavg_f": None,
            "prcp_in": prcp_in,
            "source": "ncei_daily_summaries_api",
            "quality_flags": [],
        })
    return out


def load_history_by_date(path: Path) -> dict[str, dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return by_date
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        day = row.get("date")
        if day:
            by_date[str(day)] = row
    return by_date


def merge_history(
    existing: dict[str, dict[str, Any]],
    fresh: list[dict[str, Any]],
    *,
    prefer_api_for_dates: Optional[set[str]] = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    prefer = prefer_api_for_dates or set()
    added = 0
    merged = dict(existing)
    for row in fresh:
        day = row["date"]
        if day not in merged or day in prefer or merged[day].get("tmax_f") is None:
            merged[day] = row
            added += 1
    return merged, added


def write_history(path: Path, records: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(records[d], sort_keys=True) for d in sorted(records)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def refresh_climatology(
    *,
    history_path: Path,
    start_date: str,
    end_date: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    existing = load_history_by_date(history_path)
    fresh = fetch_ncei_rows(start_date, end_date)
    target_dates = {r["date"] for r in fresh}
    merged, updated = merge_history(existing, fresh, prefer_api_for_dates=target_dates)
    if not dry_run:
        write_history(history_path, merged)
    return {
        "history_path": str(history_path),
        "start_date": start_date,
        "end_date": end_date,
        "ncei_rows_fetched": len(fresh),
        "records_updated_or_added": updated,
        "total_records_after": len(merged),
        "dry_run": dry_run,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history-path", type=Path, default=None)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    history_path = args.history_path or _default_history_path()

    result = refresh_climatology(
        history_path=history_path,
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
