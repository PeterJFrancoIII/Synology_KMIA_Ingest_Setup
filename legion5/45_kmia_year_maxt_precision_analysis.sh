#!/usr/bin/env bash
# Full-year KMIA max-temperature precision analysis.
#
# Processes all available months for YEAR (default 2021 Apr–Dec on NAS),
# merges forecast + ISD, runs accuracy tables (+ optional year chart).
#
# Study ID: KMIA_NDFD_Year_MaxT_Precision_${YEAR}
set -euo pipefail

YEAR="${KMIA_YEAR:-2021}"
FIRST_MONTH="${KMIA_FIRST_MONTH:-4}"
LAST_MONTH="${KMIA_LAST_MONTH:-12}"
if [ "$YEAR" = "2020" ]; then FIRST_MONTH="${KMIA_FIRST_MONTH:-4}"; fi

STUDY_ID="KMIA_NDFD_Year_MaxT_Precision_${YEAR}"
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/${STUDY_ID}.log"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
ANALYSIS_DIR="$ROOT/analysis/${STUDY_ID}"
POINTS="$ROOT/processed/points/station=KMIA"
DONE_MARKER="$ANALYSIS_DIR/COMPLETE.txt"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"
export KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing" "$ANALYSIS_DIR" "$HOME/.ssh/controlmasters"

log() { echo "$1" | tee -a "$LOG"; }

log "=== ${STUDY_ID} ==="
log "Started: $(date -u)"
log "Months: ${YEAR} $(printf '%02d' "$FIRST_MONTH")-$(printf '%02d' "$LAST_MONTH")"
log "pull=${NAS_PULL_MODE:-auto} workers=${KMIA_EXTRACT_WORKERS}"

# Ensure SMB mount when credentials exist
if [ -f "$ROOT/secrets/nas_smb_password" ] && ! net use Z: >/dev/null 2>&1; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup failed — may use SSH fallback"
fi

for m in $(seq -w "$FIRST_MONTH" "$LAST_MONTH"); do
  log "--- ${YEAR}-${m} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$YEAR" "$m" >>"$LOG" 2>&1 || log "WARN month ${YEAR}-${m} failed"
  # Sync VALID_ONLY to NAS processed lake (optional, fast)
  nas_month="Z:/App_Development/KMIA_Ingest/processed/points/station=KMIA/monthly/${YEAR}"
  mkdir -p "$nas_month" 2>/dev/null || true
  cp -f "$POINTS/monthly/${YEAR}/ndfd_kmia_maxt_${YEAR}${m}_VALID_ONLY.csv" "$nas_month/" 2>/dev/null || true
  cp -f "$POINTS/monthly/${YEAR}/ndfd_kmia_wdir_${YEAR}${m}_VALID_ONLY.csv" "$nas_month/" 2>/dev/null || true
done

obs="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
if [ ! -f "$obs" ]; then
  log "ISD download ${YEAR}"
  ISD_YEAR="$YEAR" KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
    bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1 || log "WARN ISD failed"
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$obs" 2>/dev/null || true
fi

maxt=() wdir=()
for m in $(seq -w "$FIRST_MONTH" "$LAST_MONTH"); do
  mf="$POINTS/monthly/${YEAR}/ndfd_kmia_maxt_${YEAR}${m}_VALID_ONLY.csv"
  wf="$POINTS/monthly/${YEAR}/ndfd_kmia_wdir_${YEAR}${m}_VALID_ONLY.csv"
  if [ -f "$mf" ] && [ -f "$wf" ]; then
    maxt+=("$mf")
    wdir+=("$wf")
  else
    log "WARN missing VALID_ONLY for ${YEAR}-${m} — excluded from merge"
  fi
done

if [ ${#maxt[@]} -eq 0 ]; then
  log "ERROR no monthly VALID_ONLY files for ${YEAR}"
  exit 1
fi

mkdir -p "$POINTS/yearly"
forecast="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv"

log "Merge ${#maxt[@]} months -> yearly forecast"
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${maxt[@]}" \
  --output "$POINTS/yearly/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
  --inputs "${wdir[@]}" \
  --output "$POINTS/yearly/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1
"$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
  --inputs "$POINTS/yearly/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" \
           "$POINTS/yearly/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" \
  --output "$forecast" >>"$LOG" 2>&1

log "Running precision analysis -> $ANALYSIS_DIR"
"$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
  --forecast "$forecast" \
  --obs-glob "$obs" \
  --out "$ANALYSIS_DIR" \
  --study-name "$STUDY_ID" >>"$LOG" 2>&1

log "Chart suite (golden-master + interactive dashboard)"
bash "$SCRIPTS/47_build_kmia_chart_suite.sh" "$STUDY_ID" "$YEAR" >>"$LOG" 2>&1 || log "WARN chart suite failed"

log "=== COMPLETE ${STUDY_ID} $(date -u) ==="
log "Report: $ANALYSIS_DIR/accuracy_report.md"
ls -lh "$ANALYSIS_DIR/" >>"$LOG" 2>&1
{
  echo "study_id=${STUDY_ID}"
  echo "completed_utc=$(date -u)"
  echo "year=${YEAR}"
  echo "months=${FIRST_MONTH}-${LAST_MONTH}"
  echo "months_merged=${#maxt[@]}"
  echo "report=$ANALYSIS_DIR/accuracy_report.md"
} >"$DONE_MARKER"
