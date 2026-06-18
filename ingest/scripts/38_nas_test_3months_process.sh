#!/usr/bin/env bash
# NAS fallback: process 3 test months in-container (when Legion5 offline).
# Same extract/filter as Legion5; raw already on NAS.
set -euo pipefail

PYTHON="/opt/kmia-venv/bin/python3"
export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"
ROOT="/data/KMIA_Ingest"
YEAR=2020
MONTHS="${TEST_MONTHS:-08 09 10}"
LOG="$ROOT/logs/processing/nas_test_3months.log"
POINTS="$ROOT/processed/points/station=KMIA"
MONTHLY="$POINTS/monthly/${YEAR}"

mkdir -p "$(dirname "$LOG")"

log() { echo "$1" | tee -a "$LOG"; }
log "=== NAS 3-month process test $(date -u) ==="

OBS="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
if [ ! -f "$OBS" ] && [ -f "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" ]; then
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$OBS"
fi

for MONTH in $MONTHS; do
  MONTH=$(printf '%02d' "$((10#$MONTH))")
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

  if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
    log "SKIP ${YEAR}-${MONTH} — already processed"
    continue
  fi

  log "=== Process ${YEAR}-${MONTH} ==="
  if [ ! -f "$MAXT_VALID" ]; then
    log "  extract maxt"
    $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
      --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
      --root "$ROOT" \
      --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$MAXT_VALID" >>"$LOG" 2>&1
  fi
  if [ ! -f "$WDIR_VALID" ]; then
    log "  extract wdir"
    $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
      --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
      --root "$ROOT" \
      --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$WDIR_VALID" >>"$LOG" 2>&1
  fi
  log "  done ${YEAR}-${MONTH}"
done

maxt=() wdir=()
for MONTH in $MONTHS; do
  MONTH=$(printf '%02d' "$((10#$MONTH))")
  maxt+=("$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv")
  wdir+=("$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv")
done

$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt[@]}" --output "$POINTS/yearly/ndfd_kmia_maxt_${YEAR}_TEST3.csv" >>"$LOG" 2>&1
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir[@]}" --output "$POINTS/yearly/ndfd_kmia_wdir_${YEAR}_TEST3.csv" >>"$LOG" 2>&1
$PYTHON "$ROOT/scripts/24_merge_forecast_csv.py" \
  --inputs "$POINTS/yearly/ndfd_kmia_maxt_${YEAR}_TEST3.csv" "$POINTS/yearly/ndfd_kmia_wdir_${YEAR}_TEST3.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST3.csv" >>"$LOG" 2>&1

$PYTHON "$ROOT/scripts/analyze_kmia_forecast_accuracy.py" \
  --forecast "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST3.csv" \
  --obs-glob "$OBS" \
  --out "$ROOT/analysis/test_3months" >>"$LOG" 2>&1

log "=== NAS test complete $(date -u) ==="
