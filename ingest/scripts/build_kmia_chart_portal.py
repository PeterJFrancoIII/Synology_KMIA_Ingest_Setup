#!/usr/bin/env python3
"""
Build KMIA multi-year chart portal — links per-year chart suites + all-years view.

Scans analysis/ for KMIA_NDFD_Year_MaxT_Precision_* and KMIA_NDFD_AllYears_* studies.
Optionally builds missing per-year chart suites when enriched CSV exists.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

YEAR_STUDY_RE = re.compile(r"^KMIA_NDFD_Year_MaxT_Precision_(\d{4})$")


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def discover_studies(analysis_root: Path) -> list[dict]:
    rows: list[dict] = []
    if not analysis_root.is_dir():
        return rows
    for d in sorted(analysis_root.iterdir()):
        if not d.is_dir():
            continue
        enriched = d / "accuracy_points_enriched.csv"
        suite = d / "kmia_chart_suite.html"
        if not enriched.is_file():
            continue
        m = YEAR_STUDY_RE.match(d.name)
        year = int(m.group(1)) if m else None
        report = d / "accuracy_report.md"
        rows.append(
            {
                "study_id": d.name,
                "year": year,
                "enriched": str(enriched),
                "suite": str(suite) if suite.is_file() else "",
                "report": str(report) if report.is_file() else "",
                "is_multiyear": d.name.startswith("KMIA_NDFD_AllYears"),
            }
        )
    rows.sort(key=lambda r: (r["is_multiyear"], r["year"] or 0))
    return rows


def ensure_suite(root: Path, study: dict, python: str) -> str:
    suite = Path(study["suite"]) if study["suite"] else None
    if suite and suite.is_file():
        return str(suite)
    year = study["year"] or 2020
    builder = script_dir() / "build_kmia_chart_suite.py"
    subprocess.run(
        [
            python,
            str(builder),
            "--root",
            str(root),
            "--study-name",
            study["study_id"],
            "--year",
            str(year),
        ],
        check=True,
        env=os.environ.copy(),
    )
    out = root / "analysis" / study["study_id"] / "kmia_chart_suite.html"
    return str(out)


def study_coverage(enriched: Path) -> dict | None:
    try:
        import pandas as pd

        df = pd.read_csv(enriched, usecols=["target_date_et"], low_memory=False)
        df["target_dt"] = pd.to_datetime(df["target_date_et"])
        years = sorted(df["target_dt"].dt.year.unique().astype(int).tolist())
        return {
            "n_days": int(df["target_date_et"].nunique()),
            "date_min": str(df["target_date_et"].min()),
            "date_max": str(df["target_date_et"].max()),
            "years": years,
        }
    except Exception:
        return None


def render_portal(studies: list[dict], out_path: Path) -> None:
    year_cards = []
    multiyear = None
    for s in studies:
        if s["is_multiyear"]:
            multiyear = s
            continue
        if not s["suite"]:
            continue
        rel = Path(s["suite"]).name
        year_cards.append(
            f"""    <a class="card" href="../{s['study_id']}/{rel}">
      <span class="year">{s['year']}</span>
      <span class="label">{s['study_id']}</span>
    </a>"""
        )
    multiyear_block = ""
    if multiyear and multiyear["suite"]:
        rel = Path(multiyear["suite"]).name
        cov = study_coverage(Path(multiyear["enriched"]))
        if cov and len(cov["years"]) > 1:
            year_label = f"{cov['years'][0]}–{cov['years'][-1]}"
            sub = f"{cov['n_days']} days · {cov['date_min']} → {cov['date_max']}"
        elif cov:
            year_label = str(cov["years"][0]) if cov["years"] else "All years"
            sub = f"{cov['n_days']} days · {cov['date_min']} → {cov['date_max']}"
        else:
            year_label = "All years"
            sub = multiyear["study_id"]
        multiyear_block = f"""
  <section>
    <h2>All years combined</h2>
    <a class="card wide" href="../{multiyear['study_id']}/{rel}">
      <span class="year">{year_label}</span>
      <span class="label">{sub}</span>
    </a>
  </section>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>KMIA Max-Temperature Chart Portal</title>
  <style>
    :root {{
      --bg: #0f1419;
      --panel: #1a2332;
      --text: #e8edf4;
      --muted: #8b9cb3;
      --border: #2d3a4f;
      --accent: #4c9aff;
    }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 1.5rem;
      line-height: 1.5;
    }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.35rem; }}
    h2 {{ font-size: 1rem; color: var(--muted); margin: 1.5rem 0 0.75rem; font-weight: 500; }}
    .sub {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 0.75rem;
    }}
    .card {{
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding: 1rem;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      text-decoration: none;
      color: inherit;
      transition: border-color 0.15s;
    }}
    .card:hover {{ border-color: var(--accent); }}
    .card.wide {{ max-width: 320px; }}
    .year {{ font-size: 1.5rem; font-weight: 600; color: var(--accent); }}
    .label {{ font-size: 0.72rem; color: var(--muted); word-break: break-all; }}
  </style>
</head>
<body>
  <h1>KMIA Max-Temperature Chart Portal</h1>
  <div class="sub">Historical NDFD forecast vs ISD observed · per-year interactive suites</div>
  <section>
    <h2>By year</h2>
    <div class="grid">
{chr(10).join(year_cards) if year_cards else '      <p class="sub">No year chart suites yet — processing in progress.</p>'}
    </div>
  </section>
{multiyear_block}
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build KMIA multi-year chart portal")
    ap.add_argument("--root", type=Path, default=Path(os.environ.get("KMIA_ROOT", ".")))
    ap.add_argument("--analysis-dir", type=Path, help="Override analysis directory")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--skip-build", action="store_true", help="Do not build missing suites")
    args = ap.parse_args()

    root = args.root.resolve()
    analysis_root = (args.analysis_dir or root / "analysis").resolve()
    portal_dir = analysis_root / "KMIA_Chart_Portal"
    portal_html = portal_dir / "kmia_chart_portal.html"

    studies = discover_studies(analysis_root)
    if not args.skip_build:
        for s in studies:
            if not s["suite"]:
                try:
                    s["suite"] = ensure_suite(root, s, args.python)
                except subprocess.CalledProcessError as exc:
                    print(f"WARN: chart build failed for {s['study_id']}: {exc}", file=sys.stderr)

    render_portal(studies, portal_html)
    manifest = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "studies": studies,
        "portal_html": str(portal_html),
    }
    (portal_dir / "portal_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {portal_html} ({len(studies)} studies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
