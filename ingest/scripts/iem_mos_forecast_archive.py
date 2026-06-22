"""IEM GFS MOS historical forecast archive — real NOAA/NWS MOS via IEM.

Stored separately from live NWS API snapshots. Used only when no live snapshot
or rules_v2 report exists at the Kalshi anchor.

NO REAL TRADING — archival forecast source only.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import quote
from zoneinfo import ZoneInfo

from kalshi_price_history_loader import anchor_time_utc_for_settlement

IEM_MOS_URL = "https://mesonet.agron.iastate.edu/api/1/mos.json"
STATION = "KMIA"
ET = ZoneInfo("America/New_York")
ARCHIVE_FILENAME = "iem_gfs_mos_forecast_archive.jsonl"


def default_iem_mos_archive_path() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_nws_dir

    parent = kalshi_nws_dir()
    return (parent / ARCHIVE_FILENAME) if parent.is_dir() else None


def _http_get_json(url: str) -> Any:
    proc = subprocess.run(
        ["curl", "-sfL", url],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"IEM fetch failed: {proc.stderr}")
    return json.loads(proc.stdout)


def _mos_runtime_for_anchor(anchor_utc: datetime) -> str:
    anchor_et = anchor_utc.astimezone(ET)
    prior = anchor_et.date()
    candidates = [
        datetime(prior.year, prior.month, prior.day, 12, 0, tzinfo=timezone.utc),
        datetime(prior.year, prior.month, prior.day, 6, 0, tzinfo=timezone.utc),
        datetime(prior.year, prior.month, prior.day, 0, 0, tzinfo=timezone.utc),
    ]
    for run in candidates:
        if run <= anchor_utc + timedelta(minutes=30):
            return run.strftime("%Y-%m-%d %H:%M")
    return candidates[0].strftime("%Y-%m-%d %H:%M")


def fetch_iem_gfs_mos_daytime_max(settlement_date: str, anchor_utc: datetime) -> Optional[dict[str, Any]]:
    """Fetch real IEM-archived GFS MOS daytime max for settlement_date."""
    runtime = _mos_runtime_for_anchor(anchor_utc)
    url = f"{IEM_MOS_URL}?station={STATION}&model=GFS&runtime={quote(runtime)}"
    try:
        payload = _http_get_json(url)
    except (RuntimeError, json.JSONDecodeError):
        return None
    daytime_temps: list[float] = []
    for row in payload.get("data") or []:
        ftime = str(row.get("ftime") or "")
        if not ftime.startswith(settlement_date):
            continue
        try:
            ft = datetime.strptime(ftime, "%Y-%m-%d %H:%M").replace(tzinfo=ET)
        except ValueError:
            continue
        if 9 <= ft.hour <= 20:
            tmp = row.get("tmp")
            if tmp is not None:
                daytime_temps.append(float(tmp))
    if not daytime_temps:
        return None
    return {
        "settlement_date_et": settlement_date,
        "forecast_temp_f": max(daytime_temps),
        "mos_runtime": runtime,
        "mos_model": "GFS",
        "station": STATION,
        "source": "iem_gfs_mos_archive",
        "provider": "noaa_nws_mos_via_iem",
        "anchor_time_utc": anchor_utc.isoformat(),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def load_iem_mos_archive(archive_path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    path = Path(archive_path)
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        day = row.get("settlement_date_et")
        if day:
            out[str(day)] = row
    return out


def iem_mos_forecast_at_anchor(
    archive_path: Path,
    settlement_date: str,
) -> dict[str, Any]:
    """MOS archive row for settlement_date (pre-built at anchor)."""
    row = load_iem_mos_archive(archive_path).get(settlement_date)
    if not row:
        return {"found": False, "reason": "no_iem_mos_archive_row"}
    temp = row.get("forecast_temp_f")
    if temp is None:
        return {"found": False, "reason": "no_forecast_temp_in_archive"}
    return {
        "found": True,
        "forecast_temp_f": float(temp),
        "snapshot_path": str(archive_path),
        "snapshot_time_utc": row.get("mos_runtime"),
        "source": "iem_gfs_mos_archive",
        "mos_runtime": row.get("mos_runtime"),
    }


def append_archive_rows(archive_path: Path, rows: list[dict[str, Any]]) -> int:
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_iem_mos_archive(archive_path)
    added = 0
    with archive_path.open("a", encoding="utf-8") as fh:
        for row in rows:
            day = row["settlement_date_et"]
            if day in existing:
                continue
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            existing[day] = row
            added += 1
    return added


def build_archive_for_days(
    settlement_days: list[str],
    archive_path: Path,
    *,
    skip_if_live_exists: Optional[Callable[[str], bool]] = None,
) -> dict[str, Any]:
    """Fetch and append real IEM MOS rows for days missing live forecast."""
    written: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    for day in sorted(settlement_days):
        if skip_if_live_exists and skip_if_live_exists(day):
            skipped.append(day)
            continue
        anchor = anchor_time_utc_for_settlement(day)
        row = fetch_iem_gfs_mos_daytime_max(day, anchor)
        if row is None:
            failed.append(day)
            continue
        if append_archive_rows(archive_path, [row]):
            written.append(day)
    return {
        "archive_path": str(archive_path),
        "written": len(written),
        "failed": failed,
        "skipped_existing_live": len(skipped),
        "written_days": written[:15],
    }
