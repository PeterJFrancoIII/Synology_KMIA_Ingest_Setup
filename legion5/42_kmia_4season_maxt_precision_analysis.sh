#!/usr/bin/env bash
# KMIA NDFD 4-Season Max-Temperature Precision Analysis (2021)
#
# Processes one representative month per meteorological season from NAS,
# then runs lead-time, weather-condition, and seasonal precision analysis.
#
# Study ID: KMIA_NDFD_4Season_MaxT_Precision_2021
# Months:   Dec=Winter, Apr=Spring, Jul=Summer, Oct=Fall
set -euo pipefail

STUDY_ID="KMIA_NDFD_4Season_MaxT_Precision_2021"
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/${STUDY_ID}.log"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"

# winter | spring | summer | fall (2021 raw confirmed on NAS)
MONTHS="${TEST_MONTHS:-2021-12 2021-04 2021-07 2021-10}"
ANALYSIS_DIR="$ROOT/analysis/${STUDY_ID}"
POINTS="$ROOT/processed/points/station=KMIA"

mkdir -p "$ROOT/logs/processing" "$ANALYSIS_DIR" "$HOME/.ssh/controlmasters"

log() { echo "$1" | tee -a "$LOG"; }

season_name() {
  case "$1" in
    12|01|02) echo Winter ;;
    03|04|05) echo Spring ;;
    06|07|08) echo Summer ;;
    09|10|11) echo Fall ;;
    *) echo Unknown ;;
  esac
}

log "=== ${STUDY_ID} ==="
log "Started: $(date -u)"
log "Months: $MONTHS"

# Install SSH config if missing
if ! grep -q "KMIA NAS connection" "$HOME/.ssh/config" 2>/dev/null; then
  [ -f "$SCRIPTS/nas_ssh_config" ] && cat "$SCRIPTS/nas_ssh_config" >> "$HOME/.ssh/config"
fi

for ym in $MONTHS; do
  y="${ym%-*}"
  m="${ym#*-}"
  log "--- $(season_name "$m") ${y}-${m} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1
done

# ISD 2021
obs="$POINTS/kmia_ncei_global_hourly_2021.csv"
if [ ! -f "$obs" ]; then
  log "ISD download 2021"
  ISD_YEAR=2021 KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
    bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1 || log "WARN ISD failed"
  cp "$ROOT/raw/observed/isd/2021/72202012839.csv" "$obs" 2>/dev/null || true
fi

maxt=() wdir=()
for ym in $MONTHS; do
  y="${ym%-*}"; m="${ym#*-}"
  maxt+=("$POINTS/monthly/${y}/ndfd_kmia_maxt_${y}${m}_VALID_ONLY.csv")
  wdir+=("$POINTS/monthly/${y}/ndfd_kmia_wdir_${y}${m}_VALID_ONLY.csv")
done

mkdir -p "$POINTS/yearly"
forecast="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${STUDY_ID}.csv"

"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt[@]}" --output "$POINTS/yearly/ndfd_kmia_maxt_${STUDY_ID}.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir[@]}" --output "$POINTS/yearly/ndfd_kmia_wdir_${STUDY_ID}.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$POINTS/yearly/ndfd_kmia_maxt_${STUDY_ID}.csv" "$POINTS/yearly/ndfd_kmia_wdir_${STUDY_ID}.csv" \
  --output "$forecast" >>"$LOG" 2>&1

log "Running precision analysis -> $ANALYSIS_DIR"
"$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$forecast" \
  --obs-glob "$obs" \
  --out "$ANALYSIS_DIR" \
  --study-name "$STUDY_ID" \
  --four-season-sample >>"$LOG" 2>&1

log "=== COMPLETE ${STUDY_ID} $(date -u) ==="
log "Report: $ANALYSIS_DIR/accuracy_report.md"
ls -lh "$ANALYSIS_DIR/" >>"$LOG" 2>&1
