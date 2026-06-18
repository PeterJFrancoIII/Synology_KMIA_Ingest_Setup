#!/usr/bin/env bash
# Controlled backfill: one source (ndfd_aws), one variable (maxt), one calendar month.
# Requires wgrib2 in PATH. Run inside kmia-arch-ingest after smoke tests pass.
set -euo pipefail

export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

ROOT="/data/KMIA_Ingest"
SUBCATEGORY="maxt"
YEAR="${1:-}"
MONTH="${2:-}"
KMIA_LON="-80.2872"
KMIA_LAT="25.7975"
MANIFEST_SCRIPT="$ROOT/scripts/40_manifest_append.py"
EXTRACT_SCRIPT="$ROOT/scripts/20_extract_kmia_point.sh"
LOG="$ROOT/logs/ingestion/backfill_maxt_${YEAR}${MONTH}.log"

if [ -z "$YEAR" ] || [ -z "$MONTH" ]; then
  echo "Usage: $0 <YYYY> <MM>"
  echo "Example: $0 2020 06"
  exit 1
fi

if ! command -v wgrib2 >/dev/null 2>&1; then
  echo "wgrib2 required before backfill"
  exit 1
fi

mkdir -p "$(dirname "$LOG")"

{
  echo "=== NDFD maxt backfill ${YEAR}-${MONTH} ==="
  echo "Started: $(date -u)"
} | tee "$LOG"

days_in_month="$(date -d "${YEAR}-${MONTH}-01 +1 month -1 day" +%d 2>/dev/null || python3 -c "import calendar; print(calendar.monthrange(int('${YEAR}'), int('${MONTH}'))[1])")"
failures=0
downloads=0
extracts=0

for day in $(seq -w 1 "$days_in_month"); do
  S3_PREFIX="s3://noaa-ndfd-pds/wmo/${SUBCATEGORY}/${YEAR}/${MONTH}/${day}/"
  OUT="$ROOT/raw/forecast/ndfd_aws/$SUBCATEGORY/$YEAR/$MONTH/$day"

  if [ -d "$OUT" ] && [ -n "$(find "$OUT" -type f -print -quit 2>/dev/null)" ]; then
    echo "Skip download (exists): ${YEAR}-${MONTH}-${day}" | tee -a "$LOG"
  else
    mkdir -p "$OUT"
    echo "Download: $S3_PREFIX" | tee -a "$LOG"
    if ! aws s3 cp --no-sign-request --no-progress --recursive "$S3_PREFIX" "$OUT/" >>"$LOG" 2>&1; then
      echo "WARN: download failed for ${YEAR}-${MONTH}-${day}" | tee -a "$LOG"
      failures=$((failures + 1))
      continue
    fi
    downloads=$((downloads + 1))
  fi

  first_file="$(find "$OUT" -type f -name 'YGUZ*' -print -quit)"
  if [ -z "$first_file" ]; then
    first_file="$(find "$OUT" -type f -print -quit)"
  fi
  if [ -z "$first_file" ]; then
    echo "WARN: no files for ${YEAR}-${MONTH}-${day}" | tee -a "$LOG"
    failures=$((failures + 1))
    continue
  fi

  if [ -f "$MANIFEST_SCRIPT" ]; then
    python3 "$MANIFEST_SCRIPT" \
      --file "$first_file" \
      --source "ndfd_aws" \
      --source-path "${S3_PREFIX}$(basename "$first_file")" \
      --format "grib2" \
      --decoder "wgrib2" \
      --status "ok" >>"$LOG" 2>&1 || true
  fi

  if bash "$EXTRACT_SCRIPT" "$first_file" >>"$LOG" 2>&1; then
    extracts=$((extracts + 1))
  else
    echo "WARN: extract failed for $first_file" | tee -a "$LOG"
    failures=$((failures + 1))
  fi
done

{
  echo "Finished: $(date -u)"
  echo "Days in month: $days_in_month"
  echo "New downloads: $downloads"
  echo "Point extracts ok: $extracts"
  echo "Failures/warnings: $failures"
} | tee -a "$LOG"

[ "$failures" -eq 0 ]
