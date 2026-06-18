#!/usr/bin/env bash
# Wait for in-flight wdir months, then process remaining partial months.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/retry_remaining_wdir.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing"

log() { echo "$(date -u) $1" | tee -a "$LOG"; }

wait_wdir_valid() {
  local year="$1" month="$2"
  local mp valid
  mp=$(printf '%02d' "$((10#$month))")
  valid="$ROOT/processed/points/station=KMIA/monthly/${year}/ndfd_kmia_wdir_${year}${mp}_VALID_ONLY.csv"
  while [ ! -f "$valid" ]; do
    log "waiting ${year}-${mp} wdir VALID_ONLY..."
    sleep 60
  done
  log "OK ${year}-${mp} wdir VALID_ONLY exists"
}

log "=== retry remaining wdir start $(date -u) ==="

if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup"
fi

# Let parallel in-flight jobs (2020-07 manual, 2025-02 via 55b) finish first.
wait_wdir_valid 2020 07
wait_wdir_valid 2025 02

for ym in "2021 03" "2022 02" "2023 02" "2024 02"; do
  set -- $ym
  log "--- 35_process_month ${1}-${2} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$1" "$2" >>"$LOG" 2>&1 \
    && log "OK ${1}-${2}" || log "WARN failed ${1}-${2}"
done

log "=== retry remaining wdir complete $(date -u) ==="
