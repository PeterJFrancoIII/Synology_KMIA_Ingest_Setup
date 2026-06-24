"""Join NWS forecast/observed data from Kalshi backend artifacts for Kalshi-primary backtests."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from kalshi_price_history_loader import anchor_time_utc_for_settlement
from weather_data_policy import (
    is_simulated_nws_snapshot,
    is_simulated_observed_row,
    is_usable_nws_snapshot,
)

_EMBEDDED_TS_FIELDS = (
    "fetched_at_utc",
    "generated_at_utc",
    "observation_time_utc",
    "timestamp_utc",
    "created_at_utc",
)


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _embedded_ts_from_json(path: Path) -> Optional[datetime]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    for field in _EMBEDDED_TS_FIELDS:
        ts = _parse_ts(data.get(field))
        if ts is not None:
            return ts
    return None


def load_observed_daily_maxes(jsonl_path: Path) -> dict[str, float]:
    """Daily max °F by date_et from NWS observed history JSONL."""
    out: dict[str, float] = {}
    path = Path(jsonl_path)
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_simulated_observed_row(row):
                continue
            day = row.get("date_et")
            temp = row.get("temperature_f")
            if day is None or temp is None:
                continue
            day = str(day)
            out[day] = max(out.get(day, float("-inf")), float(temp))
    return {d: v for d, v in out.items() if v != float("-inf")}


def _hourly_daytime_max(data: dict[str, Any], settlement_date: str) -> Optional[float]:
    """Max hourly NWS forecast °F on settlement_date (9 AM–8 PM ET) from a real snapshot."""
    temps: list[float] = []
    for period in data.get("hourly_forecast") or []:
        if str(period.get("date_et")) != settlement_date:
            continue
        temp = period.get("temperature_f")
        if temp is None:
            continue
        time_et = str(period.get("time_et") or "")
        hour: Optional[int] = None
        upper = time_et.upper()
        if " AM ET" in upper or " PM ET" in upper:
            try:
                parts = upper.replace(" ET", "").strip().split(":")
                h = int(parts[0])
                if "PM" in upper and h != 12:
                    h += 12
                if "AM" in upper and h == 12:
                    h = 0
                hour = h
            except (ValueError, IndexError):
                hour = None
        if hour is None or 9 <= hour <= 20:
            temps.append(float(temp))
    return max(temps) if temps else None


def nws_forecast_high_at_anchor(
    nws_dir: Path,
    settlement_date: str,
) -> dict[str, Any]:
    """NWS daytime high for settlement_date from snapshot at or before prior-day 10 AM ET bin open."""
    nws_dir = Path(nws_dir)
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    if not nws_dir.is_dir():
        return {"found": False, "reason": "nws_dir_missing"}

    candidates: list[tuple[datetime, Path]] = []
    for path in nws_dir.glob("nws_kmia_snapshot_*.json"):
        try:
            snap = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if is_simulated_nws_snapshot(snap):
            continue
        if not is_usable_nws_snapshot(snap):
            continue
        ts = _embedded_ts_from_json(path)
        if ts is not None and ts <= anchor_utc + timedelta(minutes=30):
            candidates.append((ts, path))

    if not candidates:
        return {
            "found": False,
            "reason": "no_nws_snapshot_before_anchor",
            "anchor_time_utc": anchor_utc.isoformat(),
        }

    def _source_rank(path: Path) -> int:
        try:
            snap = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 9
        src = str(snap.get("source") or "")
        if src == "api.weather.gov":
            return 0
        if src == "noaa_ndfd_point_archive":
            return 1
        if src == "nws_iem_afos_archive":
            return 3
        return 2

    candidates.sort(key=lambda x: (x[0], -_source_rank(x[1])), reverse=True)
    snap_ts, snap_path = candidates[0]
    data = json.loads(snap_path.read_text(encoding="utf-8"))

    forecast_high: Optional[float] = None
    for period in data.get("daily_forecast") or []:
        if (
            str(period.get("forecast_date_et")) == settlement_date
            and period.get("isDaytime")
            and period.get("temperature_f") is not None
        ):
            forecast_high = float(period["temperature_f"])
            break

    if forecast_high is None and data.get("forecast_high_f") is not None:
        # Root field may reflect current day only — use only when snapshot day matches.
        snap_day = snap_ts.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        prior = (
            datetime.strptime(settlement_date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        if snap_day in (prior, settlement_date):
            forecast_high = float(data["forecast_high_f"])

    if forecast_high is None:
        forecast_high = _hourly_daytime_max(data, settlement_date)

    if forecast_high is None:
        return {
            "found": False,
            "reason": "no_forecast_period_for_settlement_date",
            "snapshot_path": str(snap_path),
            "snapshot_time_utc": snap_ts.isoformat(),
        }

    return {
        "found": True,
        "forecast_temp_f": forecast_high,
        "snapshot_path": str(snap_path),
        "snapshot_time_utc": snap_ts.isoformat(),
        "anchor_time_utc": anchor_utc.isoformat(),
        "source": str(data.get("source") or "nws_snapshot"),
        "wind_direction_compass": data.get("wind_direction_compass"),
    }


def nws_wind_compass_at_anchor(
    nws_dir: Path,
    settlement_date: str,
) -> dict[str, Any]:
    """Surface wind compass from NWS snapshot at or before prior-day 10 AM ET anchor."""
    fc = nws_forecast_high_at_anchor(nws_dir, settlement_date)
    if not fc.get("found"):
        return {"found": False, "reason": fc.get("reason", "no_snapshot")}
    snap_path = Path(str(fc["snapshot_path"]))
    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"found": False, "reason": "snapshot_read_failed"}
    compass = data.get("wind_direction_compass")
    if compass:
        return {
            "found": True,
            "wind_direction_compass": str(compass).strip().upper(),
            "snapshot_path": str(snap_path),
            "source": "nws_snapshot_root",
        }
    return {"found": False, "reason": "no_wind_in_snapshot", "snapshot_path": str(snap_path)}


def observed_wind_compass_at_daily_max(
    jsonl_path: Path,
    settlement_date: str,
    observed_max_f: float,
) -> dict[str, Any]:
    """Wind compass at the observation closest to the settlement daily max °F."""
    path = Path(jsonl_path)
    if not path.is_file():
        return {"found": False, "reason": "jsonl_missing"}

    best: Optional[tuple[float, str]] = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_simulated_observed_row(row):
                continue
            if str(row.get("date_et")) != settlement_date:
                continue
            temp = row.get("temperature_f")
            compass = row.get("wind_direction_compass")
            if temp is None or not compass:
                continue
            delta = abs(float(temp) - float(observed_max_f))
            if best is None or delta < best[0]:
                best = (delta, str(compass).strip().upper())

    if best is None:
        return {"found": False, "reason": "no_wind_obs_on_settlement_day"}
    return {
        "found": True,
        "wind_direction_compass": best[1],
        "delta_from_observed_max_f": round(best[0], 2),
        "source": "nws_observed_history",
    }


def default_kalshi_nws_dir() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_nws_dir, optional_existing

    return optional_existing(kalshi_nws_dir())


def default_kalshi_observed_jsonl() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_observed_jsonl, optional_existing

    return optional_existing(kalshi_observed_jsonl())


def default_kalshi_forecast_reports_dir() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_forecast_reports_dir, optional_existing

    return optional_existing(kalshi_forecast_reports_dir())


def default_kmia_daily_history_jsonl() -> Optional[Path]:
    from kmia_kalshi_paths import kmia_daily_history_jsonl, optional_existing

    return optional_existing(kmia_daily_history_jsonl())


def load_ncei_climatology_tmaxes(history_jsonl: Path) -> dict[str, float]:
    """Official USW00012839 daily TMAX (°F) from kmia_daily_history.jsonl."""
    out: dict[str, float] = {}
    path = Path(history_jsonl)
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = row.get("date")
            tmax = row.get("tmax_f")
            if day is None or tmax is None:
                continue
            out[str(day)] = float(tmax)
    return out


def _settlement_source_label(row_source: Optional[str]) -> str:
    """Map kmia_daily_history.jsonl row source to audit label."""
    src = (row_source or "").strip().lower()
    if src == "nws_cli":
        return "nws_cli"
    return "ncei_climatology"


def load_settlement_observed_maxes_with_sources(
    *,
    ncei_history_jsonl: Optional[Path] = None,
) -> tuple[dict[str, float], dict[str, str]]:
    """Settlement daily max from kmia_daily_history.jsonl only (NCEI finalized / NWS CLI).

    Live NWS hourly obs (nws_observed_history.jsonl) is for intraday gates only — never settlement.
    """
    temps: dict[str, float] = {}
    sources: dict[str, str] = {}
    path = Path(ncei_history_jsonl) if ncei_history_jsonl else None
    if not path or not path.is_file():
        return temps, sources
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = row.get("date")
            tmax = row.get("tmax_f")
            if day is None or tmax is None:
                continue
            day_s = str(day)
            temps[day_s] = float(tmax)
            sources[day_s] = _settlement_source_label(row.get("source"))
    return temps, sources


def load_settlement_observed_maxes(
    *,
    ncei_history_jsonl: Optional[Path] = None,
    nws_observed_jsonl: Optional[Path] = None,
) -> dict[str, float]:
    """Settlement daily max: NCEI/CLI from kmia_daily_history.jsonl only."""
    if nws_observed_jsonl is not None:
        import warnings

        warnings.warn(
            "nws_observed_jsonl is ignored for settlement labels; use gates only",
            DeprecationWarning,
            stacklevel=2,
        )
    temps, _ = load_settlement_observed_maxes_with_sources(
        ncei_history_jsonl=ncei_history_jsonl
    )
    return temps


def rules_v2_forecast_at_anchor(
    reports_dir: Path,
    settlement_date: str,
) -> dict[str, Any]:
    """Rules v2 deterministic anchor from forecast JSON at or before prior-day 10 AM ET bin open."""
    reports_dir = Path(reports_dir)
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    if not reports_dir.is_dir():
        return {"found": False, "reason": "reports_dir_missing"}

    pat = re.compile(
        rf"kmia_forecast_{re.escape(settlement_date)}_rules_v2_climatology_(\d{{6}})\.json$"
    )
    candidates: list[tuple[datetime, Path]] = []
    for path in reports_dir.glob(f"kmia_forecast_{settlement_date}_rules_v2_*.json"):
        m = pat.match(path.name)
        if not m:
            continue
        ts = datetime.strptime(
            f"{settlement_date} {m.group(1)}", "%Y-%m-%d %H%M%S"
        ).replace(tzinfo=timezone.utc)
        if ts <= anchor_utc + timedelta(minutes=30):
            candidates.append((ts, path))

    if not candidates:
        return {"found": False, "reason": "no_rules_v2_report_for_date"}

    candidates.sort(key=lambda x: x[0], reverse=True)
    snap_ts, snap_path = candidates[0]
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    anchor_f = data.get("deterministic_anchor_f") or data.get("best_single_number_f")
    if anchor_f is None:
        return {"found": False, "reason": "no_anchor_in_report", "snapshot_path": str(snap_path)}

    return {
        "found": True,
        "forecast_temp_f": float(anchor_f),
        "snapshot_path": str(snap_path),
        "snapshot_time_utc": snap_ts.isoformat(),
        "source": "rules_v2_climatology",
    }


def forecast_high_at_anchor(
    settlement_date: str,
    *,
    nws_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
    ndfd_csv: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    allow_iem_mos: bool = False,
) -> dict[str, Any]:
    """Best real forecast at Kalshi anchor: NWS snapshot → NDFD point CSV → rules_v2 → optional IEM MOS."""
    if nws_dir is None:
        nws_dir = default_kalshi_nws_dir()
    if nws_dir:
        nws = nws_forecast_high_at_anchor(nws_dir, settlement_date)
        if nws.get("found"):
            return nws
    if ndfd_csv is None:
        from kmia_kalshi_paths import default_ndfd_kalshi_maxt_csv

        ndfd_csv = default_ndfd_kalshi_maxt_csv()
    if ndfd_csv and Path(ndfd_csv).is_file():
        from ndfd_kalshi_forecast import ndfd_forecast_high_at_anchor

        ndfd = ndfd_forecast_high_at_anchor(Path(ndfd_csv), settlement_date)
        if ndfd.get("found"):
            return ndfd
    if reports_dir is None:
        reports_dir = default_kalshi_forecast_reports_dir()
    if reports_dir:
        rv2 = rules_v2_forecast_at_anchor(reports_dir, settlement_date)
        if rv2.get("found"):
            return rv2
    if allow_iem_mos and iem_mos_archive:
        from iem_mos_forecast_archive import iem_mos_forecast_at_anchor

        mos = iem_mos_forecast_at_anchor(iem_mos_archive, settlement_date)
        if mos.get("found"):
            return mos
    return {"found": False, "reason": "no_real_forecast_source"}
