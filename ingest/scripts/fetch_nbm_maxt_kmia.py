#!/usr/bin/env python3
"""Archive NBM/NWS max-temperature guidance at KMIA for spread priors.

Fetches NWS grid forecast (MFL/105,51) and derives percentile band from
available high-temperature guidance. Archives JSONL for validation gate.

NO REAL TRADING EXECUTION — Console 2 ingest only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

_STATION = Path(__file__).resolve().parents[1] / "config" / "kmia_station.json"
_DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/nbm_maxt_archive.jsonl"
)
_HEADERS = {"User-Agent": "KMIA-Console2-NBM-Ingest/1.0 (research)"}


def _load_station() -> dict[str, Any]:
    return json.loads(_STATION.read_text(encoding="utf-8"))


def fetch_grid_forecast() -> dict[str, Any]:
    st = _load_station()
    grid = st["nws_grid_id"]
    x, y = st["nws_grid_x"], st["nws_grid_y"]
    url = f"https://api.weather.gov/gridpoints/{grid}/{x},{y}/forecast"
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _f_to_c_val(v: dict) -> Optional[float]:
    if not v:
        return None
    try:
        return float(v.get("value"))
    except (TypeError, ValueError):
        return None


def extract_daily_max_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period in payload.get("properties", {}).get("periods", []):
        if not period.get("isDaytime", True):
            continue
        temp = period.get("temperature")
        if temp is None:
            continue
        start = period.get("startTime", "")
        date_et = start[:10] if start else None
        if not date_et:
            continue
        rows.append({
            "date_et": date_et,
            "p50_f": float(temp),
            "source_period": period.get("name"),
            "short_forecast": period.get("shortForecast"),
        })
    return rows


def derive_percentile_band(p50: float, *, width_f: float = 4.0) -> dict[str, float]:
    """Derive p10/p90 from center when explicit NBM quantiles unavailable."""
    half = width_f / 2.0
    return {
        "p10_f": round(p50 - half * 1.28, 1),
        "p25_f": round(p50 - half * 0.67, 1),
        "p50_f": round(p50, 1),
        "p75_f": round(p50 + half * 0.67, 1),
        "p90_f": round(p50 + half * 1.28, 1),
        "band_width_f": round(width_f, 2),
    }


def append_archive_row(out_path: Path, row: dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def run_fetch(*, out_path: Path) -> int:
    payload = fetch_grid_forecast()
    fetched_at = datetime.now(timezone.utc).isoformat()
    n = 0
    for base in extract_daily_max_rows(payload):
        band = derive_percentile_band(float(base["p50_f"]))
        row = {
            "fetched_at_utc": fetched_at,
            "date_et": base["date_et"],
            "nbm_version": "nws_grid_forecast_v1",
            "pin": "25.7906,-80.3164",
            "grid": "MFL/105,51",
            **band,
            "meta": {
                "short_forecast": base.get("short_forecast"),
                "source_period": base.get("source_period"),
            },
        }
        append_archive_row(out_path, row)
        n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NWS/NBM max-T guidance for KMIA")
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()
    try:
        n = run_fetch(out_path=args.out)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Appended {n} row(s) to {args.out}")


if __name__ == "__main__":
    main()
