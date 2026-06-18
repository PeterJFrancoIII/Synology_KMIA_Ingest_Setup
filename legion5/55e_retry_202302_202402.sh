#!/usr/bin/env bash
# Retry 2023-02 and 2024-02 wdir (extract CSV exists; filter failed on bad lines).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
LOG="$ROOT/logs/processing/retry_202302_202402.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing"
log() { echo "$(date -u) $1" | tee -a "$LOG"; }

filter_or_rerun() {
  local year="$1" month="$2"
  local mp monthly point valid
  mp=$(printf '%02d' "$((10#$month))")
  monthly="$ROOT/processed/points/station=KMIA/monthly/${year}"
  point="$monthly/ndfd_kmia_wdir_${year}${mp}_point_forecasts.csv"
  valid="$monthly/ndfd_kmia_wdir_${year}${mp}_VALID_ONLY.csv"

  if [ -f "$valid" ]; then
    log "SKIP ${year}-${mp} — VALID_ONLY exists"
    return 0
  fi

  if [ -f "$point" ]; then
    log "filter wdir ${year}-${mp} from existing point CSV"
    if "$PYTHON" "$SCRIPTS/23_filter_valid_only.py" --input "$point" --output "$valid" >>"$LOG" 2>&1; then
      log "OK filter ${year}-${mp}"
      rm -rf "$ROOT/raw/forecast/ndfd_aws/wdir/${year}/${mp}" 2>/dev/null || true
      return 0
    fi
    log "WARN filter failed ${year}-${mp} — full re-process"
    rm -f "$point"
  fi

  log "full 35_process_month ${year}-${mp}"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$year" "$month" >>"$LOG" 2>&1 \
    && log "OK ${year}-${mp}" || log "WARN failed ${year}-${mp}"
}

log "=== retry 202302 202402 start $(date -u) ==="
if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup"
fi

filter_or_rerun 2023 02
filter_or_rerun 2024 02

log "=== retry 202302 202402 complete $(date -u) ==="
