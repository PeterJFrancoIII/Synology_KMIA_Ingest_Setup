#!/usr/bin/env python3
"""Merge per-year accuracy_points_enriched.csv into AllYears study folder."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

YEAR_STUDY_TMPL = "KMIA_NDFD_Year_MaxT_Precision_{year}"
ALL_STUDY = "KMIA_NDFD_AllYears_MaxT_Precision"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build AllYears enriched CSV from yearly studies")
    ap.add_argument("--analysis-dir", type=Path, required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--study-name", default=ALL_STUDY)
    ap.add_argument("--rebuild-chart", action="store_true")
    ap.add_argument("--python", default="python3")
    args = ap.parse_args()

    analysis_dir = args.analysis_dir.resolve()
    out_dir = analysis_dir / args.study_name
    out_dir.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []
    used_years: list[int] = []
    for year in args.years:
        enriched = analysis_dir / YEAR_STUDY_TMPL.format(year=year) / "accuracy_points_enriched.csv"
        if not enriched.is_file():
            print(f"SKIP missing: {enriched}")
            continue
        df = pd.read_csv(enriched, low_memory=False)
        df["target_dt"] = pd.to_datetime(df["target_date_et"])
        frames.append(df)
        used_years.append(year)
        print(f"  {year}: {df['target_date_et'].nunique()} days, {len(df)} releases")

    if not frames:
        raise SystemExit("No yearly enriched CSVs found — nothing to merge")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["target_date_et", "release_time_et"], keep="last")
    merged = merged.sort_values(["target_date_et", "release_time_et"]).reset_index(drop=True)

    out_csv = out_dir / "accuracy_points_enriched.csv"
    merged.to_csv(out_csv, index=False)

    manifest = {
        "study_name": args.study_name,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_years": used_years,
        "n_days": int(merged["target_date_et"].nunique()),
        "n_releases": int(len(merged)),
        "date_min": str(merged["target_date_et"].min()),
        "date_max": str(merged["target_date_et"].max()),
        "inputs": [str(analysis_dir / YEAR_STUDY_TMPL.format(year=y) / "accuracy_points_enriched.csv") for y in used_years],
        "output": str(out_csv),
    }
    (out_dir / "all_years_merge_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {out_csv} ({manifest['n_days']} days, {manifest['n_releases']} releases)")
    print(f"Range: {manifest['date_min']} -> {manifest['date_max']}")

    if args.rebuild_chart:
        import subprocess
        import sys

        scripts = Path(__file__).resolve().parent
        py = args.python or sys.executable
        suite = out_dir / "kmia_chart_suite.html"
        subprocess.run(
            [
                py,
                str(scripts / "chart_kmia_interactive_accuracy_explorer.py"),
                "--points",
                str(out_csv),
                "--out",
                str(suite),
                "--study-name",
                args.study_name,
            ],
            check=True,
        )
        subprocess.run(
            [py, str(scripts / "build_kmia_chart_portal.py"), "--analysis-dir", str(analysis_dir), "--skip-build"],
            check=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
