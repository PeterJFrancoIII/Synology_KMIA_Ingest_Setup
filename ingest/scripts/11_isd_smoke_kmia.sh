#!/usr/bin/env bash
set -euo pipefail

ROOT="${KMIA_ROOT:-/data/KMIA_Ingest}"
YEAR="${ISD_YEAR:-2025}"
FILE="72202012839.csv"
URL="https://www.ncei.noaa.gov/data/global-hourly/access/${YEAR}/${FILE}"
OUT="$ROOT/raw/observed/isd/${YEAR}/${FILE}"
LOG="$ROOT/logs/smoke_tests/isd_kmia_${YEAR}.log"
MANIFEST_SCRIPT="$ROOT/scripts/40_manifest_append.py"

mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"

{
  echo "=== ISD Smoke: KMIA ${YEAR} ==="
  echo "Started: $(date -u)"
  echo "URL: $URL"
  echo "Output: $OUT"
} | tee "$LOG"

curl -fL "$URL" -o "$OUT"
sha256sum "$OUT" | tee -a "$LOG"
head -5 "$OUT" | tee -a "$LOG"

PY="${KMIA_PYTHON:-python3}"

if [ -f "$MANIFEST_SCRIPT" ]; then
  "$PY" "$MANIFEST_SCRIPT" \
    --file "$OUT" \
    --source "ncei_isd" \
    --source-path "$URL" \
    --format "csv" \
    --decoder "curl" \
    --status "ok"
fi

echo "ISD smoke test PASSED" | tee -a "$LOG"
