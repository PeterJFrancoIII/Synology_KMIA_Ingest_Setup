#!/usr/bin/env bash
# Short test: process 3 months from NAS on Legion5 + run accuracy analysis.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"
export PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}:$PATH"

LOG="$ROOT/logs/processing/test_three_months.log"
mkdir -p "$ROOT/logs/processing"

log() { echo "$1" | tee -a "$LOG"; }

# Default: 2020 Jul–Sep (partial progress existed; good end-to-end test)
YEAR="${TEST_YEAR:-2020}"
MONTHS=(${TEST_MONTHS:-07 08 09})

log "=== 3-month processor test $(date -u) YEAR=$YEAR MONTHS=${MONTHS[*]} ==="

# ISD once
OBS="$ROOT/processed/points/station=KMIA/kmia_ncei_global_hourly_${YEAR}.csv"
if [ ! -f "$OBS" ]; then
  log "ISD download $YEAR"
  ISD_YEAR="$YEAR" KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
    bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$OBS"
fi

for m in "${MONTHS[@]}"; do
  log "--- processing ${YEAR}-${m} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$YEAR" "$m" >>"$LOG" 2>&1
done

POINTS="$ROOT/processed/points/station=KMIA"
MONTHLY="$POINTS/monthly/${YEAR}"
YEARLY="$POINTS/yearly"
mkdir -p "$YEARLY"

maxt_inputs=() wdir_inputs=()
for m in "${MONTHS[@]}"; do
  mm=$(printf '%02d' "$((10#$m))")
  maxt_inputs+=("$MONTHLY/ndfd_kmia_maxt_${YEAR}${mm}_VALID_ONLY.csv")
  wdir_inputs+=("$MONTHLY/ndfd_kmia_wdir_${YEAR}${mm}_VALID_ONLY.csv")
done

log "merge test months"
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt_inputs[@]}" \
  --output "$YEARLY/ndfd_kmia_maxt_test_VALID_ONLY.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir_inputs[@]}" \
  --output "$YEARLY/ndfd_kmia_wdir_test_VALID_ONLY.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$YEARLY/ndfd_kmia_maxt_test_VALID_ONLY.csv" "$YEARLY/ndfd_kmia_wdir_test_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv" >>"$LOG" 2>&1

log "accuracy analysis (test)"
"$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv" \
  --obs-glob "$OBS" \
  --out "$ROOT/analysis/test_${YEAR}" >>"$LOG" 2>&1

log "=== TEST COMPLETE $(date -u) ==="
log "Outputs:"
log "  $POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_TEST.csv"
log "  $ROOT/analysis/test_${YEAR}/accuracy_report.md"
ls -lh "$MONTHLY"/*_VALID_ONLY.csv 2>/dev/null | tee -a "$LOG" || true
