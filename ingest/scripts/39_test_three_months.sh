#!/usr/bin/env bash
# NAS container: process 3 test months (default 2020 Jul–Sep) + accuracy analysis.
set -euo pipefail

PYTHON="/opt/kmia-venv/bin/python3"
export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

ROOT="/data/KMIA_Ingest"
SCRIPTS="$ROOT/scripts"
YEAR="${TEST_YEAR:-2020}"
MONTHS=(${TEST_MONTHS:-07 08 09})
LOG="$ROOT/logs/processing/test_three_months.log"
POINTS="$ROOT/processed/points/station=KMIA"
MONTHLY="$POINTS/monthly/${YEAR}"
YEARLY="$POINTS/yearly"

mkdir -p "$YEARLY" "$MONTHLY" "$(dirname "$LOG")"

log() { echo "$1" | tee -a "$LOG"; }

log "=== NAS 3-month test $(date -u) YEAR=$YEAR MONTHS=${MONTHS[*]} ==="

OBS="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
if [ ! -f "$OBS" ] && [ -f "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" ]; then
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$OBS"
fi
if [ ! -f "$OBS" ]; then
  ISD_YEAR="$YEAR" bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$OBS"
fi

maxt_inputs=() wdir_inputs=()

for MONTH in "${MONTHS[@]}"; do
  MONTH=$(printf '%02d' "$((10#$MONTH))")
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

  log "=== Process ${YEAR}-${MONTH} ==="

  if [ ! -f "$MAXT_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      log "  extract maxt"
      $PYTHON "$SCRIPTS/22_batch_extract_local_gribs.py" \
        --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    fi
    log "  filter maxt"
    $PYTHON "$SCRIPTS/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$MAXT_VALID" >>"$LOG" 2>&1
  else
    log "  maxt VALID_ONLY exists — skip"
  fi
  maxt_inputs+=("$MAXT_VALID")

  if [ ! -f "$WDIR_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      log "  extract wdir"
      $PYTHON "$SCRIPTS/22_batch_extract_local_gribs.py" \
        --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    fi
    log "  filter wdir"
    $PYTHON "$SCRIPTS/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$WDIR_VALID" >>"$LOG" 2>&1
  else
    log "  wdir VALID_ONLY exists — skip"
  fi
  wdir_inputs+=("$WDIR_VALID")
done

log "merge test forecast"
$PYTHON "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt_inputs[@]}" \
  --output "$YEARLY/ndfd_kmia_maxt_test_VALID_ONLY.csv" >>"$LOG" 2>&1
$PYTHON "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir_inputs[@]}" \
  --output "$YEARLY/ndfd_kmia_wdir_test_VALID_ONLY.csv" >>"$LOG" 2>&1
$PYTHON "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$YEARLY/ndfd_kmia_maxt_test_VALID_ONLY.csv" "$YEARLY/ndfd_kmia_wdir_test_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv" >>"$LOG" 2>&1

log "accuracy analysis"
$PYTHON "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv" \
  --obs-glob "$OBS" \
  --out "$ROOT/analysis/test_${YEAR}" >>"$LOG" 2>&1

log "=== TEST COMPLETE $(date -u) ==="
wc -l "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv" | tee -a "$LOG"
head -20 "$ROOT/analysis/test_${YEAR}/accuracy_report.md" | tee -a "$LOG"
