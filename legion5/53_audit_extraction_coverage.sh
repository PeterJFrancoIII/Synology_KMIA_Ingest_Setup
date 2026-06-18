#!/usr/bin/env bash
# Audit processed VALID_ONLY coverage vs raw archive gaps.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
POINTS="$ROOT/processed/points/station=KMIA/monthly"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"

manifest="$ROOT/manifest/extraction_coverage.json"
mkdir -p "$ROOT/manifest"

"$PYTHON" - <<'PY' "$POINTS" "$manifest"
import json, sys
from datetime import datetime, timezone
from pathlib import Path

points = Path(sys.argv[1])
manifest = Path(sys.argv[2])
rows = []
if points.is_dir():
    for year_dir in sorted(p for p in points.iterdir() if p.is_dir() and p.name.isdigit()):
        y = year_dir.name
        for m in range(1, 13):
            mm = f"{m:02d}"
            maxt = year_dir / f"ndfd_kmia_maxt_{y}{mm}_VALID_ONLY.csv"
            wdir = year_dir / f"ndfd_kmia_wdir_{y}{mm}_VALID_ONLY.csv"
            if not maxt.exists() and not wdir.exists():
                continue
            status = "OK" if maxt.exists() and wdir.exists() else "PARTIAL"
            rows.append({
                "year": int(y), "month": mm, "status": status,
                "maxt": maxt.exists(), "wdir": wdir.exists(),
                "maxt_bytes": maxt.stat().st_size if maxt.exists() else 0,
                "wdir_bytes": wdir.stat().st_size if wdir.exists() else 0,
            })
out = {
    "audited_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "months_extracted": len([r for r in rows if r["status"] == "OK"]),
    "months_partial": len([r for r in rows if r["status"] == "PARTIAL"]),
    "months": rows,
}
manifest.write_text(json.dumps(out, indent=2) + "\n")
print(f"Extracted OK: {out['months_extracted']} months, partial: {out['months_partial']}")
for r in rows:
    if r["status"] != "OK":
        print(f"  PARTIAL {r['year']}-{r['month']}: maxt={r['maxt']} wdir={r['wdir']}")
PY
