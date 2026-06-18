#!/usr/bin/env python3
"""
Audit NDFD GRIB archive integrity on NAS (or local mirror).

Scans raw/forecast/ndfd_aws/{maxt,wdir}/YYYY/MM for:
  - missing months
  - empty months
  - maxt/wdir asymmetry
  - day-level gaps (days with zero GRIB files)

Outputs JSON + markdown under manifest/ or --out-dir.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def month_range(year: int, first: int = 1, last: int = 12) -> list[str]:
    return [f"{m:02d}" for m in range(first, last + 1)]


def count_month(var_root: Path, year: int, month: str) -> dict:
    """Inspect one variable/year/month folder."""
    for m in (month, str(int(month))):
        month_dir = var_root / str(year) / m
        if not month_dir.is_dir():
            continue
        day_dirs = sorted([d for d in month_dir.iterdir() if d.is_dir()])
        if not day_dirs:
            files = list(month_dir.glob("*"))
            n_files = sum(1 for f in files if f.is_file())
            return {
                "path": str(month_dir),
                "exists": True,
                "n_days": 0,
                "n_files": n_files,
                "empty_days": [],
                "status": "EMPTY" if n_files == 0 else "FLAT_FILES",
            }
        empty_days: list[str] = []
        n_files = 0
        for d in day_dirs:
            fc = sum(1 for f in d.iterdir() if f.is_file())
            n_files += fc
            if fc == 0:
                empty_days.append(d.name)
        return {
            "path": str(month_dir),
            "exists": True,
            "n_days": len(day_dirs),
            "n_files": n_files,
            "empty_days": empty_days[:20],
            "n_empty_days": len(empty_days),
            "status": "OK" if n_files > 0 and not empty_days else ("EMPTY" if n_files == 0 else "PARTIAL_DAYS"),
        }
    return {"path": "", "exists": False, "n_days": 0, "n_files": 0, "empty_days": [], "status": "MISSING"}


def combine_status(maxt: dict, wdir: dict) -> str:
    ms, ws = maxt["status"], wdir["status"]
    if ms == "MISSING" and ws == "MISSING":
        return "MISSING_BOTH"
    if ms == "MISSING":
        return "MISSING_MAXT"
    if ws == "MISSING":
        return "MISSING_WDIR"
    if ms == "OK" and ws == "OK":
        if maxt.get("n_empty_days", 0) or wdir.get("n_empty_days", 0):
            return "OK_WITH_EMPTY_DAYS"
        return "OK"
    if ms in ("EMPTY", "MISSING") or ws in ("EMPTY", "MISSING"):
        return "INCOMPLETE"
    return f"CHECK_{ms}_{ws}"


def audit_archive(nas_root: Path, years: list[int], year_first_month: dict[int, int]) -> dict:
    raw = nas_root / "raw" / "forecast" / "ndfd_aws"
    maxt_root = raw / "maxt"
    wdir_root = raw / "wdir"
    months_out: list[dict] = []
    summary = defaultdict(int)

    for year in years:
        first = year_first_month.get(year, 1)
        for month in month_range(year, first, 12):
            maxt = count_month(maxt_root, year, month)
            wdir = count_month(wdir_root, year, month)
            status = combine_status(maxt, wdir)
            summary[status] += 1
            months_out.append(
                {
                    "year": year,
                    "month": month,
                    "status": status,
                    "maxt": maxt,
                    "wdir": wdir,
                }
            )

    ok = summary.get("OK", 0) + summary.get("OK_WITH_EMPTY_DAYS", 0)
    total = len(months_out)
    return {
        "audited_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nas_root": str(nas_root),
        "years": years,
        "total_months_checked": total,
        "months_ok": ok,
        "months_incomplete": total - ok,
        "status_counts": dict(summary),
        "months": months_out,
        "gaps": [m for m in months_out if m["status"] not in ("OK", "OK_WITH_EMPTY_DAYS")],
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# NDFD GRIB Archive Integrity Audit",
        "",
        f"**Audited:** {report['audited_utc']}",
        f"**Root:** `{report['nas_root']}`",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Months checked | {report['total_months_checked']} |",
        f"| Months OK | {report['months_ok']} |",
        f"| Months with gaps | {report['months_incomplete']} |",
        "",
        "### Status counts",
        "",
    ]
    for k, v in sorted(report["status_counts"].items()):
        lines.append(f"- **{k}:** {v}")
    lines.extend(["", "## Gaps (non-OK months)", ""])
    if not report["gaps"]:
        lines.append("_No gaps detected._")
    else:
        lines.append("| Year-Month | Status | maxt files | wdir files | maxt days | wdir days |")
        lines.append("|------------|--------|------------|------------|-----------|-----------|")
        for g in report["gaps"]:
            mx, wd = g["maxt"], g["wdir"]
            lines.append(
                f"| {g['year']}-{g['month']} | {g['status']} | {mx.get('n_files', 0)} | "
                f"{wd.get('n_files', 0)} | {mx.get('n_days', 0)} | {wd.get('n_days', 0)} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit NDFD GRIB archive on NAS")
    ap.add_argument(
        "--nas-root",
        type=Path,
        default=Path("/volume2/Data/App_Development/KMIA_Ingest"),
        help="KMIA_Ingest root (NAS path or Z: mount)",
    )
    ap.add_argument("--years", default="2020,2021,2022,2023,2024,2025")
    ap.add_argument("--out-dir", type=Path, help="Output directory (default: nas_root/manifest)")
    args = ap.parse_args()

    years = [int(y.strip()) for y in args.years.split(",")]
    year_first = {2020: 4}  # AWS NDFD archive starts 2020-04

    nas_root = args.nas_root.resolve() if args.nas_root.exists() else args.nas_root
    if not nas_root.exists():
        raise SystemExit(f"NAS root not found: {nas_root}")

    report = audit_archive(nas_root, years, year_first)
    out_dir = args.out_dir
    if out_dir is None:
        local_root = Path(os.environ.get("KMIA_ROOT", ""))
        out_dir = (local_root / "manifest") if local_root.is_dir() else (nas_root / "manifest")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"archive_integrity_{ts}.json"
    md_path = out_dir / f"archive_integrity_{ts}.md"
    latest_json = out_dir / "archive_integrity_latest.json"
    latest_md = out_dir / "archive_integrity_latest.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    latest_md.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"OK: {report['months_ok']}/{report['total_months_checked']} months")
    print(f"Gaps: {report['months_incomplete']}")
    for g in report["gaps"][:15]:
        print(f"  {g['year']}-{g['month']}: {g['status']}")
    if len(report["gaps"]) > 15:
        print(f"  ... and {len(report['gaps']) - 15} more")
    return 0 if report["months_incomplete"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
