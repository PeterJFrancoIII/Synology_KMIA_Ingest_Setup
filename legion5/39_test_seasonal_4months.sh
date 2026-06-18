#!/usr/bin/env bash
# Seasonal test: 4 months (winter, spring, summer, fall) from NAS.
# Default: 2021-01, 2021-04, 2021-07, 2021-10 (full calendar year on S3).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/test_seasonal_4months.log"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" KMIA_PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}"
export PATH="$KMIA_PATH:$PATH"

# winter=Dec, spring=Apr, summer=Jul, fall=Oct (2021 — full Apr-Dec raw on NAS)
MONTHS="${TEST_MONTHS:-2021-12 2021-04 2021-07 2021-10}"
OUT_TAG="${TEST_OUT_TAG:-SEASONAL4}"
ANALYSIS_DIR="$ROOT/analysis/test_$(echo "$OUT_TAG" | tr '[:upper:]' '[:lower:]')"

mkdir -p "$ROOT/logs/processing" "$ANALYSIS_DIR"

log() { echo "$1" | tee -a "$LOG"; }

log "=== Seasonal 4-month test $(date -u) ==="
log "Months: $MONTHS"

for ym in $MONTHS; do
  y="${ym%-*}"
  m="${ym#*-}"
  log "month $ym ($(
    case "$m" in
      12|01|02) echo winter ;;
      03|04|05) echo spring ;;
      06|07|08) echo summer ;;
      09|10|11) echo fall ;;
      *) echo unknown ;;
    esac
  ))"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1
done

# ISD for each year present
years=$(echo "$MONTHS" | tr ' ' '\n' | cut -d- -f1 | sort -u)
obs_files=()
for y in $years; do
  obs="$ROOT/processed/points/station=KMIA/kmia_ncei_global_hourly_${y}.csv"
  if [ ! -f "$obs" ]; then
    log "ISD download $y"
    ISD_YEAR="$y" KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
      bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1 || log "WARN ISD $y failed"
    cp "$ROOT/raw/observed/isd/${y}/72202012839.csv" "$obs" 2>/dev/null || true
  fi
  [ -f "$obs" ] && obs_files+=("$obs")
done

points="$ROOT/processed/points/station=KMIA"
maxt=() wdir=()
for ym in $MONTHS; do
  y="${ym%-*}"
  m="${ym#*-}"
  maxt+=("$points/monthly/${y}/ndfd_kmia_maxt_${y}${m}_VALID_ONLY.csv")
  wdir+=("$points/monthly/${y}/ndfd_kmia_wdir_${y}${m}_VALID_ONLY.csv")
done

mkdir -p "$points/yearly"
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt[@]}" --output "$points/yearly/ndfd_kmia_maxt_${OUT_TAG}.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir[@]}" --output "$points/yearly/ndfd_kmia_wdir_${OUT_TAG}.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$points/yearly/ndfd_kmia_maxt_${OUT_TAG}.csv" "$points/yearly/ndfd_kmia_wdir_${OUT_TAG}.csv" \
  --output "$points/ndfd_kmia_point_forecasts_VALID_ONLY_${OUT_TAG}.csv" >>"$LOG" 2>&1

obs_arg=$(IFS=,; echo "${obs_files[*]}")
"$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$points/ndfd_kmia_point_forecasts_VALID_ONLY_${OUT_TAG}.csv" \
  --obs-glob "$obs_arg" \
  --out "$ANALYSIS_DIR" >>"$LOG" 2>&1

log "=== SEASONAL TEST COMPLETE — $ANALYSIS_DIR/accuracy_report.md ==="
ls -lh "$ANALYSIS_DIR/" >>"$LOG" 2>&1
