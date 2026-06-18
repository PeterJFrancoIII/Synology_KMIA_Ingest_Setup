#!/usr/bin/env bash
# Process a single month: maxt + wdir download, extract, VALID_ONLY.
set -euo pipefail

PYTHON="${KMIA_PYTHON:-/opt/kmia-venv/bin/python3}"
export PATH="${KMIA_PATH:-/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin}:${PATH}"
ROOT="${KMIA_ROOT:-/e/KMIA_Ingest}"

YEAR="${1:?YEAR}"
MONTH="${2:?MONTH}"
MONTHLY="$ROOT/processed/points/station=KMIA/monthly/${YEAR}"
LOG="$ROOT/logs/ingestion/month_${YEAR}${MONTH}.log"

mkdir -p "$MONTHLY" "$(dirname "$LOG")"

MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
  echo "skip complete ${YEAR}-${MONTH}" | tee "$LOG"
  exit 0
fi

{
  echo "=== month worker ${YEAR}-${MONTH} ==="
  echo "Started: $(date -u)"
} | tee "$LOG"

if [ ! -f "$MAXT_VALID" ]; then
  if [ ! -f "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" ]; then
    bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" maxt "$YEAR" "$MONTH" "YGUZ*" >>"$LOG" 2>&1
    $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
      --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
      --root "$ROOT" \
      --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
  fi
  $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
    --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
    --output "$MAXT_VALID" >>"$LOG" 2>&1
fi

if [ ! -f "$WDIR_VALID" ]; then
  if [ ! -f "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" ]; then
    bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" wdir "$YEAR" "$MONTH" "YBUZ*" >>"$LOG" 2>&1
    $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
      --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
      --root "$ROOT" \
      --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
  fi
  $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
    --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
    --output "$WDIR_VALID" >>"$LOG" 2>&1
fi

echo "Finished: $(date -u)" | tee -a "$LOG"
