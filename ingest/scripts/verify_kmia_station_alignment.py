#!/usr/bin/env python3
"""Audit KMIA lat/lon alignment across config, code, and runtime artifacts.

Canonical pin: 25.7906, -80.3164 → NWS MFL/105,51
Observations: USW00012839 / KMIA (station ID, not grid pin)

Exit 0 when all checks pass; exit 1 on any failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from kmia_station import KMIA_LAT, KMIA_LON, NWS_GRID_URL_SUFFIX, load_station_config

# Legacy pins that must not appear in operational code/docs (exclude Research archives).
LEGACY_PATTERNS = [
    r"25\.7975",
    r"-80\.2872",
    r"25\.7959,\s*-80\.2870",
    r"MFL/106,51",
    r"MFL/109,96",
    r"279\.7128",
]

OPERATIONAL_GLOBS = [
    "ingest/scripts/*.py",
    "ingest/scripts/*.sh",
    "ingest/config/*",
    "docker/**/*.yml",
    "legion5/*.{sh,ps1}",
    "docs/*.md",
    ".cursor/skills/**/*.md",
]

KALSHI_OPERATIONAL_GLOBS = [
    "backend/src/**/*.py",
    "scripts/*.sh",
    "docs/NWS_LIVE_DATA.md",
    ".cursor/skills/**/*.md",
]

SKIP_PATH_PARTS = {
    "1_Downloads",
    "Deep Research",
    "node_modules",
    ".git",
    "_quarantine_wrong_grid",
    "agent-transcripts",
}


SKIP_FILENAMES = {
    "verify_kmia_station_alignment.py",
    "quarantine_mismatched_nws_snapshots.py",
}


def _should_scan(path: Path) -> bool:
    if path.name in SKIP_FILENAMES:
        return False
    if path.name.startswith("test_"):
        return False
    parts = set(path.parts)
    if parts & SKIP_PATH_PARTS:
        return False
    return True


def scan_tree(root: Path, globs: list[str]) -> list[tuple[Path, str, int]]:
    hits: list[tuple[Path, str, int]] = []
    for pattern in globs:
        for path in root.glob(pattern):
            if not path.is_file() or not _should_scan(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                for pat in LEGACY_PATTERNS:
                    if re.search(pat, line):
                        hits.append((path, line.strip()[:120], line_no))
                        break
    return hits


def check_config(repo: Path) -> list[str]:
    errors: list[str] = []
    cfg_path = repo / "ingest/config/kmia_station.json"
    if not cfg_path.is_file():
        return ["missing ingest/config/kmia_station.json"]
    cfg = json.loads(cfg_path.read_text())
    if float(cfg.get("lat", 0)) != KMIA_LAT or float(cfg.get("lon", 0)) != KMIA_LON:
        errors.append(f"kmia_station.json lat/lon mismatch: {cfg.get('lat')}, {cfg.get('lon')}")
    if cfg.get("nws_grid_id") != "MFL" or cfg.get("nws_grid_x") != 105 or cfg.get("nws_grid_y") != 51:
        errors.append(f"kmia_station.json grid mismatch: {cfg.get('nws_grid_id')}/{cfg.get('nws_grid_x')},{cfg.get('nws_grid_y')}")
    return errors


def check_kalshi_mirror(kalshi_root: Path) -> list[str]:
    errors: list[str] = []
    mod = kalshi_root / "backend/src/shared/kmia_station.py"
    if not mod.is_file():
        return ["missing Kalshi backend/src/shared/kmia_station.py"]
    text = mod.read_text()
    if "25.7906" not in text or "-80.3164" not in text or "105" not in text:
        errors.append("Kalshi kmia_station.py missing canonical pin")
    return errors


def check_nws_snapshot(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"NWS snapshot missing: {path}"]
    data = json.loads(path.read_text())
    url = str(data.get("api_daily_forecast_url") or "")
    if NWS_GRID_URL_SUFFIX not in url:
        errors.append(f"NWS snapshot wrong grid: {url}")
    lat = data.get("forecast_pin_lat")
    lon = data.get("forecast_pin_lon")
    if lat is not None and abs(float(lat) - KMIA_LAT) > 0.001:
        errors.append(f"NWS snapshot pin lat {lat}")
    if lon is not None and abs(float(lon) - KMIA_LON) > 0.001:
        errors.append(f"NWS snapshot pin lon {lon}")
    return errors


def check_ndfd_csv_station_lat(csv_path: Path, sample_rows: int = 500) -> list[str]:
    """Warn if NDFD extract CSV still carries legacy station_lat."""
    errors: list[str] = []
    if not csv_path.is_file():
        return []
    import csv

    seen: set[str] = set()
    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            if i >= sample_rows:
                break
            lat = row.get("station_lat")
            lon = row.get("station_lon")
            if lat:
                seen.add(str(lat))
            if lon:
                seen.add(str(lon))
    legacy = {s for s in seen if s.startswith("25.797") or s.startswith("-80.287")}
    if legacy:
        errors.append(
            f"NDFD CSV {csv_path.name} still has legacy station coords in sample: {sorted(legacy)} "
            "(re-extract required)"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console2-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--kalshi-root", type=Path, default=None)
    parser.add_argument("--nws-snapshot", type=Path, default=None)
    parser.add_argument("--ndfd-csv", type=Path, default=None)
    args = parser.parse_args(argv)

    c2 = args.console2_root
    kalshi = args.kalshi_root or c2.parent / "Kalshi"
    failures: list[str] = []

    cfg = load_station_config()
    print(f"Canonical: {cfg['lat']}, {cfg['lon']} → {NWS_GRID_URL_SUFFIX}")

    failures.extend(check_config(c2))
    if kalshi.is_dir():
        failures.extend(check_kalshi_mirror(kalshi))

    c2_hits = scan_tree(c2, OPERATIONAL_GLOBS)
    if c2_hits:
        failures.append(f"Console2 legacy coordinate refs: {len(c2_hits)}")
        for path, line, no in c2_hits[:15]:
            failures.append(f"  {path.relative_to(c2)}:{no}: {line}")

    if kalshi.is_dir():
        k_hits = scan_tree(kalshi, KALSHI_OPERATIONAL_GLOBS)
        if k_hits:
            failures.append(f"Kalshi legacy coordinate refs: {len(k_hits)}")
            for path, line, no in k_hits[:15]:
                failures.append(f"  {path.relative_to(kalshi)}:{no}: {line}")

    nws = args.nws_snapshot or kalshi / "backend/data/processed/weather_nws/latest_nws_kmia_snapshot.json"
    failures.extend(check_nws_snapshot(nws))

    ndfd = args.ndfd_csv
    if ndfd is None:
        candidate = c2 / "Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv"
        if candidate.is_file():
            ndfd = candidate
    if ndfd:
        failures.extend(check_ndfd_csv_station_lat(ndfd))

    if failures:
        print("\nFAIL — alignment issues:")
        for f in failures:
            print(f"  • {f}")
        return 1

    print("\nOK — operational paths aligned with 25.7906, -80.3164 (MFL/105,51)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
