#!/usr/bin/env bash
# Short test: process 3 months from NAS (default 2020-08, 09, 10).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/test_3months.log"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" KMIA_PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}"
export PATH="$KMIA_PATH:$PATH"

MONTHS="${TEST_MONTHS:-2020-08 2020-09 2020-10}"

mkdir -p "$ROOT/logs/processing"

log() { echo "$1" | tee -a "$LOG"; }

log "=== 3-month processor test $(date -u) ==="

for ym in $MONTHS; do
  y="${ym%-*}"
  m="${ym#*-}"
  log "month $ym"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1
done

# ISD for 2020
obs="$ROOT/processed/points/station=KMIA/kmia_ncei_global_hourly_2020.csv"
if [ ! -f "$obs" ]; then
  ISD_YEAR=2020 KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
    bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
  cp "$ROOT/raw/observed/isd/2020/72202012839.csv" "$obs"
fi

# Merge test months + run mini analysis
points="$ROOT/processed/points/station=KMIA"
monthly="$points/monthly/2020"
maxt=() wdir=()
for ym in $MONTHS; do
  m="${ym#*-}"
  maxt+=("$monthly/ndfd_kmia_maxt_2020${m}_VALID_ONLY.csv")
  wdir+=("$monthly/ndfd_kmia_wdir_2020${m}_VALID_ONLY.csv")
done

mkdir -p "$points/yearly"
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt[@]}" --output "$points/yearly/ndfd_kmia_maxt_2020_TEST3.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir[@]}" --output "$points/yearly/ndfd_kmia_wdir_2020_TEST3.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$points/yearly/ndfd_kmia_maxt_2020_TEST3.csv" "$points/yearly/ndfd_kmia_wdir_2020_TEST3.csv" \
  --output "$points/ndfd_kmia_point_forecasts_VALID_ONLY_TEST3.csv" >>"$LOG" 2>&1

"$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$points/ndfd_kmia_point_forecasts_VALID_ONLY_TEST3.csv" \
  --obs-glob "$obs" \
  --out "$ROOT/analysis/test_3months" >>"$LOG" 2>&1

log "=== TEST COMPLETE — see $ROOT/analysis/test_3months/accuracy_report.md ==="
ls -lh "$ROOT/analysis/test_3months/" >>"$LOG" 2>&1
