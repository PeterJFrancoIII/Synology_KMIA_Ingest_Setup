#!/usr/bin/env python3
"""Extract KMIA point rows from local NDFD GRIB files already on NAS."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TEMP_VARS = {"maxt", "mint", "temp", "td"}
WIND_SPEED_VARS = {"wspd", "wgust"}
PERCENT_VARS = {"sky", "pop12"}
QPF_VARS = {"qpf"}

POINT_FIELDS = [
    "extracted_at_utc",
    "source",
    "source_path",
    "local_path",
    "requested_subcategory",
    "station_id",
    "station_lat",
    "station_lon",
    "interp_method",
    "decoder",
    "message_number",
    "byte_offset",
    "grib_ref_time_utc",
    "valid_time_utc",
    "lead_text",
    "grib_variable",
    "level",
    "lon_returned",
    "lat_returned",
    "value_native",
    "value_f",
    "value_c",
    "value_mph",
    "value_inches",
    "value_percent",
    "raw_wgrib2_line",
]


def iso_utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_grib_time(s: str) -> Optional[str]:
    if not s:
        return None
    fmt = "%Y%m%d%H" if len(s) == 10 else "%Y%m%d%H%M" if len(s) == 12 else None
    if not fmt:
        return None
    try:
        t = dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        return t.isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def add_normalized_values(row: Dict[str, object], subcat: str, val: float) -> None:
    if subcat in TEMP_VARS:
        c = val - 273.15 if val > 150.0 else val
        row["value_c"] = c
        row["value_f"] = c * 9.0 / 5.0 + 32.0
    elif subcat in WIND_SPEED_VARS:
        row["value_mph"] = val * 2.2369362920544
    elif subcat in PERCENT_VARS:
        row["value_percent"] = val
    elif subcat in QPF_VARS:
        row["value_inches"] = val / 25.4


def parse_wgrib2_line(line: str, requested_subcategory: str, source_path: str) -> Dict[str, object]:
    parts = line.strip().split(":")
    row: Dict[str, object] = {
        "source": "ndfd_aws",
        "source_path": source_path,
        "requested_subcategory": requested_subcategory,
        "message_number": parts[0] if parts else None,
        "byte_offset": parts[1] if len(parts) > 1 else None,
        "grib_ref_time_utc": None,
        "valid_time_utc": None,
        "lead_text": None,
        "grib_variable": None,
        "level": None,
        "lon_returned": None,
        "lat_returned": None,
        "value_native": None,
        "value_f": None,
        "value_c": None,
        "value_mph": None,
        "value_inches": None,
        "value_percent": None,
        "raw_wgrib2_line": line.strip(),
    }
    ref_match = re.search(r"(?:^|:)d=(\d{10,12})(?::|$)", line)
    vt_match = re.search(r"(?:^|:)vt=(\d{10,12})(?::|$)", line)
    if ref_match:
        row["grib_ref_time_utc"] = parse_grib_time(ref_match.group(1))
    if vt_match:
        row["valid_time_utc"] = parse_grib_time(vt_match.group(1))
    if len(parts) > 3:
        row["grib_variable"] = parts[3]
    if len(parts) > 4:
        row["level"] = parts[4]
    if len(parts) > 5:
        row["lead_text"] = parts[5]
    lon_match = re.search(r"lon=([-+]?\d+(?:\.\d+)?)", line)
    lat_match = re.search(r"lat=([-+]?\d+(?:\.\d+)?)", line)
    val_match = re.search(r"val=([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", line)
    if lon_match:
        row["lon_returned"] = float(lon_match.group(1))
    if lat_match:
        row["lat_returned"] = float(lat_match.group(1))
    if val_match:
        val = float(val_match.group(1))
        row["value_native"] = val
        add_normalized_values(row, requested_subcategory, val)
    return row


def run_wgrib2(wgrib2: str, grib_path: Path, lon: float, lat: float) -> List[str]:
    cmd = [wgrib2, str(grib_path), "-s", "-vt", "-lon", str(lon), str(lat)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"wgrib2 failed for {grib_path}")
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def source_path_from_local(raw_root: Path, grib_path: Path, subcat: str) -> str:
    rel = grib_path.relative_to(raw_root)
    parts = rel.parts
    if len(parts) >= 4:
        yyyy, mm, dd, filename = parts[0], parts[1], parts[2], parts[3]
        return f"s3://noaa-ndfd-pds/wmo/{subcat}/{yyyy}/{mm}/{dd}/{filename}"
    return str(grib_path)


def append_rows(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=POINT_FIELDS, extrasaction="ignore", quoting=csv.QUOTE_NONNUMERIC
        )
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def _extract_one_file(job: Tuple[str, str, str, str, float, float, str]) -> Tuple[List[Dict[str, object]], Optional[str]]:
    """Worker: extract rows from one GRIB file. Picklable for ProcessPoolExecutor."""
    grib_path_str, raw_root_str, subcategory, wgrib2, lon, lat, station_id = job
    grib_path = Path(grib_path_str)
    raw_root = Path(raw_root_str)
    try:
        source_path = source_path_from_local(raw_root, grib_path, subcategory)
        lines = run_wgrib2(wgrib2, grib_path, lon, lat)
        extracted_at = iso_utc_now()
        rows: List[Dict[str, object]] = []
        for line in lines:
            row = parse_wgrib2_line(line, subcategory, source_path)
            row.update({
                "extracted_at_utc": extracted_at,
                "local_path": str(grib_path),
                "station_id": station_id,
                "station_lat": lat,
                "station_lon": lon,
                "interp_method": "nearest",
                "decoder": wgrib2,
            })
            rows.append(row)
        return rows, None
    except Exception as exc:
        return [], f"FAIL {grib_path.name}: {exc}"


def default_workers() -> int:
    cpus = os.cpu_count() or 4
    return max(1, min(8, cpus - 1))


def main() -> int:
    p = argparse.ArgumentParser(description="Batch extract KMIA points from local NDFD GRIB files.")
    p.add_argument("--root", default="/data/KMIA_Ingest")
    p.add_argument("--subcategory", default="maxt")
    p.add_argument("--year", required=True)
    p.add_argument("--month", required=True)
    p.add_argument("--pattern", default="YGUZ*", help="Filename glob; default KMIA-covering tiles.")
    p.add_argument("--lat", type=float, default=25.7975)
    p.add_argument("--lon", type=float, default=-80.2872)
    p.add_argument("--station-id", default="KMIA")
    p.add_argument("--wgrib2", default="wgrib2")
    p.add_argument("--flush-every", type=int, default=25)
    p.add_argument(
        "--workers",
        type=int,
        default=default_workers(),
        help="Parallel wgrib2 processes (1=serial). Default: min(8, cpu_count-1).",
    )
    p.add_argument("--output", help="Optional output CSV path (default: processed/.../ndfd_kmia_point_forecasts.csv)")
    args = p.parse_args()

    root = Path(args.root)
    raw_root = root / "raw" / "forecast" / "ndfd_aws" / args.subcategory / args.year / args.month
    out_dir = root / "processed" / "points" / f"station={args.station_id}"
    out_csv = Path(args.output) if getattr(args, "output", None) else out_dir / "ndfd_kmia_point_forecasts.csv"
    log_path = root / "logs" / "ingestion" / f"batch_extract_{args.subcategory}_{args.year}{args.month}.log"

    if not raw_root.is_dir():
        print(f"Missing raw directory: {raw_root}", file=sys.stderr)
        return 1

    files = sorted(
        fp for fp in raw_root.rglob("*")
        if fp.is_file() and fnmatch.fnmatch(fp.name, args.pattern)
    )
    if not files:
        print(f"No files matched {args.pattern} under {raw_root}", file=sys.stderr)
        return 1

    if out_csv.exists():
        out_csv.unlink()

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    workers = max(1, args.workers)
    total_rows = 0
    failures = 0

    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"Started: {iso_utc_now()}\n")
        log.write(f"Files: {len(files)}\n")
        log.write(f"Pattern: {args.pattern}\n")
        log.write(f"Workers: {workers}\n")
        log.write(f"Output: {out_csv}\n")

        jobs = [
            (str(grib_path), str(raw_root), args.subcategory, args.wgrib2, args.lon, args.lat, args.station_id)
            for grib_path in files
        ]

        if workers == 1:
            batch: List[Dict[str, object]] = []
            for idx, job in enumerate(jobs, start=1):
                rows, err = _extract_one_file(job)
                if err:
                    failures += 1
                    print(err, file=sys.stderr)
                    log.write(err + "\n")
                else:
                    batch.extend(rows)
                if idx % args.flush_every == 0 or idx == len(files):
                    append_rows(out_csv, batch)
                    total_rows += len(batch)
                    batch.clear()
                    print(f"Processed {idx}/{len(files)} files; rows={total_rows}")
                    log.write(f"Processed {idx}/{len(files)} files; rows={total_rows}\n")
        else:
            done = 0
            batch = []
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_extract_one_file, job): job for job in jobs}
                for fut in as_completed(futures):
                    rows, err = fut.result()
                    done += 1
                    if err:
                        failures += 1
                        print(err, file=sys.stderr)
                        log.write(err + "\n")
                    else:
                        batch.extend(rows)
                    if done % args.flush_every == 0 or done == len(files):
                        append_rows(out_csv, batch)
                        total_rows += len(batch)
                        batch.clear()
                        print(f"Processed {done}/{len(files)} files; rows={total_rows}")
                        log.write(f"Processed {done}/{len(files)} files; rows={total_rows}\n")

        log.write(f"Finished: {iso_utc_now()}\n")
        log.write(f"Total rows: {total_rows}\n")
        log.write(f"Failures: {failures}\n")

    print(f"Wrote {total_rows} rows to {out_csv}")
    print(f"Failures: {failures}")
    if total_rows == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
