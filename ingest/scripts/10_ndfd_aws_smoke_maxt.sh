#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/KMIA_Ingest"
SUBCATEGORY="maxt"
YEAR="2020"
MONTH="06"
DAY="01"
KMIA_LON="-80.2872"
KMIA_LAT="25.7975"
S3_PREFIX="s3://noaa-ndfd-pds/wmo/${SUBCATEGORY}/${YEAR}/${MONTH}/${DAY}/"

OUT="$ROOT/raw/forecast/ndfd_aws/$SUBCATEGORY/$YEAR/$MONTH/$DAY"
LOG="$ROOT/logs/smoke_tests/ndfd_aws_maxt_${YEAR}${MONTH}${DAY}.log"
MANIFEST_SCRIPT="$ROOT/scripts/40_manifest_append.py"

mkdir -p "$OUT" "$(dirname "$LOG")"

{
  echo "=== NDFD AWS Smoke: maxt ${YEAR}-${MONTH}-${DAY} ==="
  echo "Started: $(date -u)"
  echo "S3 prefix: $S3_PREFIX"
  echo "Output: $OUT"
} | tee "$LOG"

aws s3 ls --no-sign-request "$S3_PREFIX" | tee -a "$LOG"
aws s3 cp --no-sign-request --no-progress --recursive "$S3_PREFIX" "$OUT/" >> "$LOG" 2>&1

# YGUZ = CONUS grid; subgrid YGAZ/YGRZ files may not cover KMIA.
first_file="$(find "$OUT" -type f -name 'YGUZ*' -print -quit)"
if [ -z "$first_file" ]; then
  first_file="$(find "$OUT" -type f -print -quit)"
fi
if [ -z "$first_file" ]; then
  echo "No NDFD files downloaded" | tee -a "$LOG"
  if [ -f "$MANIFEST_SCRIPT" ]; then
    python3 "$MANIFEST_SCRIPT" \
      --file "$OUT" \
      --source "ndfd_aws" \
      --source-path "$S3_PREFIX" \
      --format "grib2" \
      --decoder "none" \
      --status "error" \
      --error-text "No NDFD files downloaded" || true
  fi
  exit 1
fi

sha256sum "$first_file" | tee -a "$LOG"

if [ -f "$MANIFEST_SCRIPT" ]; then
  python3 "$MANIFEST_SCRIPT" \
    --file "$first_file" \
    --source "ndfd_aws" \
    --source-path "$S3_PREFIX$(basename "$first_file")" \
    --format "grib2" \
    --decoder "aws-cli" \
    --status "ok"
fi

if command -v wgrib2 >/dev/null 2>&1; then
  wgrib2 "$first_file" -s -vt -lon "$KMIA_LON" "$KMIA_LAT" | tee -a "$LOG"
  echo "NDFD smoke test PASSED (download + wgrib2 point extraction)" | tee -a "$LOG"
  exit 0
else
  echo "wgrib2 missing; download succeeded but point extraction skipped" | tee -a "$LOG"
  if [ -f "$MANIFEST_SCRIPT" ]; then
    python3 "$MANIFEST_SCRIPT" \
      --file "$first_file" \
      --source "ndfd_aws" \
      --source-path "$S3_PREFIX$(basename "$first_file")" \
      --format "grib2" \
      --decoder "wgrib2-missing" \
      --status "partial" \
      --error-text "wgrib2 missing; download succeeded but point extraction skipped"
  fi
  exit 2
fi
