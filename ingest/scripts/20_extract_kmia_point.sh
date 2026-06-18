#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/KMIA_Ingest"
KMIA_LON="${KMIA_LON:--80.2872}"
KMIA_LAT="${KMIA_LAT:-25.7975}"
GRIB_FILE="${1:-}"

if [ -z "$GRIB_FILE" ]; then
  echo "Usage: $0 <path-to-grib2-file>"
  echo "Example: $0 /data/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2020/06/01/<file>"
  exit 1
fi

if [ ! -f "$GRIB_FILE" ]; then
  echo "File not found: $GRIB_FILE"
  exit 1
fi

OUT_DIR="$ROOT/processed/points"
LOG="$ROOT/logs/smoke_tests/extract_kmia_$(basename "$GRIB_FILE").log"
mkdir -p "$OUT_DIR" "$(dirname "$LOG")"

{
  echo "=== KMIA Point Extract ==="
  echo "File: $GRIB_FILE"
  echo "Lon/Lat: $KMIA_LON $KMIA_LAT"
  echo "Started: $(date -u)"
} | tee "$LOG"

if command -v wgrib2 >/dev/null 2>&1; then
  wgrib2 "$GRIB_FILE" -s -vt -lon "$KMIA_LON" "$KMIA_LAT" | tee -a "$LOG"
  echo "Point extraction complete (wgrib2)" | tee -a "$LOG"
  exit 0
fi

export PATH="/opt/kmia-venv/bin:${PATH}"
if python3 -c "import cfgrib, eccodes" 2>/dev/null; then
  python3 - << PY | tee -a "$LOG"
import sys
try:
    import cfgrib
    import eccodes
    print("cfgrib/eccodes fallback available for", "${GRIB_FILE}")
    # Minimal smoke — full decode pipeline added in backfill phase
    print("Install wgrib2 before full point extraction; implement cfgrib fallback in backfill phase if approved")
except Exception as e:
    print("cfgrib/eccodes fallback failed:", e)
    sys.exit(1)
PY
  echo "Point extraction partial (cfgrib/eccodes fallback only)" | tee -a "$LOG"
  exit 2
fi

echo "Neither wgrib2 nor cfgrib/eccodes available" | tee -a "$LOG"
exit 2
