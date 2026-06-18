#!/usr/bin/env python3
"""
Repeatable KMIA interactive chart suite builder.

Runs after analyze_kmia_forecast_accuracy.py (needs accuracy_points_enriched.csv).

Outputs (in study analysis dir):
  - kmia_chart_suite.html                   interactive dashboard (2 tabs)
  - chart_suite_manifest.json               inputs/outputs log
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def run(cmd: list[str], env: dict[str, str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build KMIA interactive chart suite")
    ap.add_argument("--root", type=Path, default=Path(os.environ.get("KMIA_ROOT", ".")))
    ap.add_argument("--study-name", required=True, help="Study ID folder under analysis/")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--python", default=sys.executable, help="Python executable")
    ap.add_argument(
        "--analysis-dir",
        type=Path,
        help="Override analysis output dir (default: root/analysis/{study_name})",
    )
    args = ap.parse_args()

    root = args.root.resolve()
    analysis_dir = (args.analysis_dir or root / "analysis" / args.study_name).resolve()
    analysis_dir.mkdir(parents=True, exist_ok=True)

    enriched = analysis_dir / "accuracy_points_enriched.csv"
    suite_html = analysis_dir / "kmia_chart_suite.html"
    manifest_path = analysis_dir / "chart_suite_manifest.json"

    if not enriched.is_file():
        raise SystemExit(f"Missing required input: {enriched}")

    scripts = script_dir()
    env = os.environ.copy()
    env["KMIA_ROOT"] = str(root)

    interactive_cmd = [
        args.python,
        str(scripts / "chart_kmia_interactive_accuracy_explorer.py"),
        "--points",
        str(enriched),
        "--out",
        str(suite_html),
        "--study-name",
        args.study_name,
    ]
    run(interactive_cmd, env)

    legacy = analysis_dir / "kmia_interactive_accuracy_explorer.html"
    legacy.write_bytes(suite_html.read_bytes())

    manifest = {
        "study_name": args.study_name,
        "year": args.year,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": {
            "accuracy_points_enriched": str(enriched),
        },
        "outputs": {
            "chart_suite_html": str(suite_html),
            "accuracy_report": str(analysis_dir / "accuracy_report.md"),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {suite_html}")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
