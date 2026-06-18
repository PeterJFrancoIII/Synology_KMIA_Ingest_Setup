#!/usr/bin/env bash
# Full archive BUILD + max-temperature analysis (2020–2025).
# Pull NAS raw GRIB → extract KMIA point → VALID_ONLY → merge → ISD → analyze.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/process_all.log"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
POINTS="$ROOT/processed/points/station=KMIA"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"
export KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing" "$SCRIPTS" "$HOME/.ssh/controlmasters"

log() { echo "$1" | tee -a "$LOG"; }

log "=== Legion5 full max-t pipeline start $(date -u) ROOT=$ROOT workers=$KMIA_EXTRACT_WORKERS ==="

# Ensure SMB (Z:) for fast pulls when credentials exist
if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 \
    || log "WARN SMB setup failed — will try UNC or SSH"
fi
# shellcheck source=nas_pull_helpers.sh
source "$SCRIPTS/nas_pull_helpers.sh"
nas_pull_autodetect_mode
log "NAS_PULL_MODE=${NAS_PULL_MODE:-ssh} host=${NAS_SSH_HOST:-nas-local}"

sync_month_to_nas() {
  local y="$1" m="$2"
  local src="$POINTS/monthly/${y}"
  local rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
  local nas_month=""
  if [ -n "${NAS_SMB_DRIVE:-}" ] && [ -d "${NAS_SMB_DRIVE%/}/${rel}/processed" ]; then
    nas_month="${NAS_SMB_DRIVE%/}/${rel}/processed/points/station=KMIA/monthly/${y}"
  else
    nas_month="//${NAS_SMB_HOST:-192.168.0.193}/${NAS_SMB_SHARE:-Data}/${rel}/processed/points/station=KMIA/monthly/${y}"
  fi
  mkdir -p "$nas_month" 2>/dev/null || return 0
  for f in "ndfd_kmia_maxt_${y}${m}_VALID_ONLY.csv" "ndfd_kmia_wdir_${y}${m}_VALID_ONLY.csv"; do
    [ -f "$src/$f" ] && cp -f "$src/$f" "$nas_month/" 2>/dev/null || true
  done
}

fetch_isd() {
  local y="$1"
  local obs="$POINTS/kmia_ncei_global_hourly_${y}.csv"
  if [ -f "$obs" ]; then
    log "ISD $y exists — skip"
    return
  fi
  log "ISD download $y"
  ISD_YEAR="$y" KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON" \
    bash "$SCRIPTS/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1 || log "WARN ISD $y failed"
  cp "$ROOT/raw/observed/isd/${y}/72202012839.csv" "$obs" 2>/dev/null || true
}

analyze_year() {
  local y="$1"
  local study="KMIA_NDFD_Year_MaxT_Precision_${y}"
  local forecast="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${y}.csv"
  local obs="$POINTS/kmia_ncei_global_hourly_${y}.csv"
  local out="$ROOT/analysis/${study}"
  if [ ! -f "$forecast" ] || [ ! -f "$obs" ]; then
    log "SKIP analysis $y — missing forecast or ISD"
    return
  fi
  log "=== analyze year $y -> $study ==="
  "$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
    --forecast "$forecast" \
    --obs-glob "$obs" \
    --out "$out" \
    --study-name "$study" >>"$LOG" 2>&1 || log "WARN analysis $y failed"
  if [ "${KMIA_BUILD_CHARTS:-1}" = "1" ] && [ -f "$out/accuracy_points_enriched.csv" ]; then
    bash "$SCRIPTS/47_build_kmia_chart_suite.sh" "$study" "$y" >>"$LOG" 2>&1 \
      || log "WARN chart suite $y failed"
  fi
  {
    echo "study_id=${study}"
    echo "completed_utc=$(date -u)"
    echo "year=${y}"
  } >"$out/COMPLETE.txt" 2>/dev/null || true
}

merge_year() {
  local y="$1"
  local monthly="$POINTS/monthly/${y}"
  local yearly="$POINTS/yearly"
  mkdir -p "$yearly"
  local maxt_inputs=() wdir_inputs=()
  for f in "$monthly"/ndfd_kmia_maxt_${y}*_VALID_ONLY.csv; do
    [ -f "$f" ] && maxt_inputs+=("$f")
  done
  for f in "$monthly"/ndfd_kmia_wdir_${y}*_VALID_ONLY.csv; do
    [ -f "$f" ] && wdir_inputs+=("$f")
  done
  [ ${#maxt_inputs[@]} -eq 0 ] && { log "WARN no maxt months for $y"; return; }
  [ ${#wdir_inputs[@]} -eq 0 ] && { log "WARN no wdir months for $y — maxt-only merge skipped"; return; }
  log "merge year $y (${#maxt_inputs[@]} maxt, ${#wdir_inputs[@]} wdir months)"
  "$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
    --inputs "${maxt_inputs[@]}" \
    --output "$yearly/ndfd_kmia_maxt_${y}_VALID_ONLY.csv" >>"$LOG" 2>&1
  "$PYTHON" "$SCRIPTS/28_merge_yearly_forecast_csv.py" \
    --inputs "${wdir_inputs[@]}" \
    --output "$yearly/ndfd_kmia_wdir_${y}_VALID_ONLY.csv" >>"$LOG" 2>&1
  "$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
    --inputs "$yearly/ndfd_kmia_maxt_${y}_VALID_ONLY.csv" "$yearly/ndfd_kmia_wdir_${y}_VALID_ONLY.csv" \
    --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${y}.csv" >>"$LOG" 2>&1
  analyze_year "$y"
}

process_year() {
  local y="$1" first="$2" last="$3"
  fetch_isd "$y"
  for m in $(seq -w "$first" "$last"); do
    log "--- year $y month $m ---"
    bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1 || log "WARN month $y-$m failed"
    sync_month_to_nas "$y" "$m"
    sleep 3
  done
  merge_year "$y"
}

build_chart_portal() {
  log "=== build multi-year chart portal ==="
  "$PYTHON" "$SCRIPTS/build_kmia_chart_portal.py" --root "$ROOT" >>"$LOG" 2>&1 \
    || log "WARN chart portal failed"
}

process_year 2020 4 12
process_year 2021 1 12
process_year 2022 1 12
process_year 2023 1 12
process_year 2024 1 12
process_year 2025 1 12

log "=== merge all years for multi-year analysis ==="
ALL=()
for y in 2020 2021 2022 2023 2024 2025; do
  f="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${y}.csv"
  [ -f "$f" ] && ALL+=("$f")
done
if [ ${#ALL[@]} -gt 0 ]; then
  "$PYTHON" "$SCRIPTS/24_merge_forecast_csv.py" \
    --inputs "${ALL[@]}" \
    --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_ALL.csv" >>"$LOG" 2>&1
  STUDY_ALL="KMIA_NDFD_AllYears_MaxT_Precision"
  OBS_ALL=()
  for y in 2020 2021 2022 2023 2024 2025; do
    o="$POINTS/kmia_ncei_global_hourly_${y}.csv"
    [ -f "$o" ] && OBS_ALL+=("$o")
  done
  if [ ${#OBS_ALL[@]} -gt 0 ]; then
    log "=== multi-year analysis (${#ALL[@]} forecast years, ${#OBS_ALL[@]} ISD files) ==="
    "$PYTHON" "$SCRIPTS/analyze_kmia_forecast_accuracy.py" \
      --forecast "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_ALL.csv" \
      --obs-glob "$(IFS=,; echo "${OBS_ALL[*]}")" \
      --out "$ROOT/analysis/${STUDY_ALL}" \
      --study-name "$STUDY_ALL" >>"$LOG" 2>&1 || log "WARN multi-year analysis failed"
    if [ "${KMIA_BUILD_CHARTS:-1}" = "1" ] && [ -f "$ROOT/analysis/${STUDY_ALL}/accuracy_points_enriched.csv" ]; then
      bash "$SCRIPTS/47_build_kmia_chart_suite.sh" "$STUDY_ALL" "2020" >>"$LOG" 2>&1 \
        || log "WARN all-years chart suite failed"
    fi
  fi
else
  log "WARN no yearly forecast files — skipping multi-year merge"
fi

build_chart_portal

log "=== Legion5 full max-t pipeline complete $(date -u) ==="
