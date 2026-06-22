"""NDFD point maxT at Kalshi anchor (prior-day 10 AM ET) — MapClick pin 25.7906 / -80.3164.

Uses Legion5 VALID_ONLY maxt extracts (wgrib2 -lon at canonical coords).
NO REAL TRADING — archival forecast join only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from kalshi_price_history_loader import anchor_time_utc_for_settlement
from kmia_station import KMIA_LAT, KMIA_LON, NWS_GRID_ID, NWS_GRID_X, NWS_GRID_Y

ET = ZoneInfo("America/New_York")
ANCHOR_SLACK_MINUTES = 30
SOURCE = "noaa_ndfd_point_archive"


def _normalize_lon_360(lon: float) -> float:
    return lon + 360.0 if lon < 0 else lon


def _pin_ok(lat: float, lon: float, *, tol: float = 0.02) -> bool:
    lon360 = _normalize_lon_360(lon)
    return abs(lat - KMIA_LAT) <= tol and abs(lon360 - _normalize_lon_360(KMIA_LON)) <= tol


@lru_cache(maxsize=4)
def _load_maxt_frame(csv_path: str) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.is_file():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        return df
    sub = df.get("requested_subcategory")
    if sub is not None:
        df = df[sub.astype(str).str.lower().eq("maxt")].copy()
    for col in ("station_lat", "station_lon", "lat_returned", "lon_returned", "value_f"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["grib_ref_time_utc"] = pd.to_datetime(df["grib_ref_time_utc"], errors="coerce", utc=True)
    df["valid_time_utc"] = pd.to_datetime(df["valid_time_utc"], errors="coerce", utc=True)
    df = df.dropna(subset=["grib_ref_time_utc", "valid_time_utc", "value_f"])

    if "station_lat" in df.columns and "station_lon" in df.columns:
        mask = df.apply(
            lambda r: _pin_ok(float(r["station_lat"]), float(r["station_lon"]))
            if pd.notna(r.get("station_lat")) and pd.notna(r.get("station_lon"))
            else False,
            axis=1,
        )
        pinned = df[mask]
        if not pinned.empty:
            df = pinned
    return df


def discover_ndfd_maxt_csvs(search_roots: list[Path]) -> list[Path]:
    """Find monthly or merged VALID_ONLY maxt CSVs under Legion5-style layouts."""
    found: list[Path] = []
    seen: set[str] = set()
    patterns = (
        "ndfd_kmia_maxt_*_VALID_ONLY.csv",
        "kalshi_ndfd_maxt_*VALID_ONLY*.csv",
        "ndfd_kmia_point_forecasts_VALID_ONLY*.csv",
    )
    for root in search_roots:
        if not root.is_dir():
            continue
        for pat in patterns:
            for path in sorted(root.rglob(pat)):
                key = str(path.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(path)
    return found


def merge_ndfd_maxt_csvs(csv_paths: list[Path], output: Path) -> Path:
    """Merge multiple VALID_ONLY maxt CSVs into one deduped file."""
    frames: list[pd.DataFrame] = []
    for path in csv_paths:
        df = _load_maxt_frame(str(path))
        if not df.empty:
            frames.append(df)
    if not frames:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("", encoding="utf-8")
        return output
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(
        subset=["grib_ref_time_utc", "valid_time_utc", "value_f", "local_path"],
        keep="last",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output, index=False)
    _load_maxt_frame.cache_clear()
    return output


def _daytime_max_on_date(df: pd.DataFrame, settlement_date: str) -> Optional[float]:
    """Max NDFD maxT (°F) with valid time on settlement_date (ET calendar day)."""
    if df.empty:
        return None
    dates_et = df["valid_time_utc"].dt.tz_convert(ET).dt.strftime("%Y-%m-%d")
    day_rows = df.loc[dates_et == settlement_date, "value_f"]
    if day_rows.empty:
        return None
    return float(day_rows.max())


def ndfd_forecast_high_at_anchor(
    ndfd_csv: Path,
    settlement_date: str,
) -> dict[str, Any]:
    """NDFD point maxT for settlement_date from latest release at or before Kalshi anchor."""
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    slack = anchor_utc + timedelta(minutes=ANCHOR_SLACK_MINUTES)

    df = _load_maxt_frame(str(ndfd_csv.resolve()))
    if df.empty:
        return {"found": False, "reason": "ndfd_csv_empty_or_missing", "csv": str(ndfd_csv)}

    eligible = df[df["grib_ref_time_utc"] <= slack]
    if eligible.empty:
        return {
            "found": False,
            "reason": "no_ndfd_release_before_anchor",
            "anchor_time_utc": anchor_utc.isoformat(),
        }

    release_times = sorted(eligible["grib_ref_time_utc"].unique())
    release_utc = release_times[-1]
    release_rows = eligible[eligible["grib_ref_time_utc"] == release_utc]
    high_f = _daytime_max_on_date(release_rows, settlement_date)
    if high_f is None:
        return {
            "found": False,
            "reason": "no_ndfd_maxt_for_settlement_date",
            "release_time_utc": pd.Timestamp(release_utc).isoformat(),
        }

    return {
        "found": True,
        "forecast_temp_f": round(high_f, 1),
        "release_time_utc": pd.Timestamp(release_utc).isoformat(),
        "anchor_time_utc": anchor_utc.isoformat(),
        "source": SOURCE,
        "ndfd_csv": str(ndfd_csv.resolve()),
        "station_lat": KMIA_LAT,
        "station_lon": KMIA_LON,
    }


def build_ndfd_nws_snapshot(
    settlement_date: str,
    *,
    high_f: float,
    release_time_utc: datetime,
) -> dict[str, Any]:
    """Snapshot JSON compatible with kalshi_nws_join (canonical grid metadata)."""
    grid_suffix = f"{NWS_GRID_ID}/{NWS_GRID_X},{NWS_GRID_Y}"
    release_et = release_time_utc.astimezone(ET)
    day_label = datetime.strptime(settlement_date, "%Y-%m-%d").strftime("%a %m/%d")
    return {
        "fetched_at_utc": release_time_utc.isoformat(),
        "generated_at_utc": release_time_utc.isoformat(),
        "observation_time_utc": None,
        "station": "KMIA",
        "forecast_pin_lat": KMIA_LAT,
        "forecast_pin_lon": KMIA_LON,
        "source": SOURCE,
        "archival_method": "ndfd_wgrib2_point_extract",
        "timeseries_source_url": "https://www.weather.gov/wrh/timeseries?site=kmia",
        "api_observations_url": "https://api.weather.gov/stations/KMIA/observations",
        "api_daily_forecast_url": f"https://api.weather.gov/gridpoints/{grid_suffix}/forecast",
        "api_hourly_forecast_url": f"https://api.weather.gov/gridpoints/{grid_suffix}/forecast/hourly",
        "settlement_authority_status": "ARCHIVAL_RESEARCH",
        "metar_parse_status": "NOT_APPLICABLE",
        "station_status": "OK",
        "forecast_high_f": int(round(high_f)),
        "daily_forecast": [
            {
                "valid_time_utc": f"{settlement_date}T10:00:00-04:00",
                "forecast_date_et": settlement_date,
                "display_day": day_label,
                "period_name": settlement_date,
                "isDaytime": True,
                "temperature_f": int(round(high_f)),
                "temperature_unit": "F",
                "shortForecast": f"High near {int(round(high_f))}",
                "detailedForecast": (
                    f"NDFD maxT point extract at {KMIA_LAT}, {KMIA_LON} "
                    f"(release {release_et.strftime('%Y-%m-%d %H:%M %Z')})."
                ),
                "raw_message": f"NDFD maxT {high_f}F",
            }
        ],
        "daily_forecast_count": 1,
        "hourly_forecast": [],
        "hourly_forecast_count": 0,
        "recent_observations_table": [],
        "recent_observations_count": 0,
        "stale_data": False,
        "endpoint_status": "OK",
        "warnings": [
            "Archival NOAA NDFD point maxT at MapClick pin — not live api.weather.gov JSON.",
        ],
        "settlement_date_et": settlement_date,
        "anchor_time_utc": anchor_time_utc_for_settlement(settlement_date).isoformat(),
        "safety": {"no_real_trading": True},
    }


def _cli_merge(args: argparse.Namespace) -> int:
    roots = [Path(r) for r in args.roots]
    paths = discover_ndfd_maxt_csvs(roots)
    out = Path(args.output)
    merge_ndfd_maxt_csvs(paths, out)
    print(f"merged {len(paths)} files -> {out}")
    return 0 if paths else 1


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="NDFD Kalshi anchor forecast utilities")
    sub = p.add_subparsers(dest="cmd")

    m = sub.add_parser("merge", help="Merge VALID_ONLY maxt CSVs")
    m.add_argument("--roots", nargs="+", required=True, help="Search roots (monthly year dirs)")
    m.add_argument("--output", required=True, help="Merged CSV output path")
    m.set_defaults(func=_cli_merge)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
