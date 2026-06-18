#!/usr/bin/env bash
# Retry partial months: wdir from NAS (maxt already on D:), 2025-02 maxt from AWS.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/retry_partial_months.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_LOCAL_ROOT="$ROOT"
export KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing"

log() { echo "$1" | tee -a "$LOG"; }

log "=== partial month retry start $(date -u) ==="

if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup"
fi

retry() {
  local y="$1" m="$2"
  log "--- 35_process_month ${y}-${m} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1 \
    && log "OK ${y}-${m}" || log "WARN failed ${y}-${m}"
}

# maxt on D:; wdir on NAS
retry 2020 07
retry 2021 03
retry 2022 02
retry 2023 02
retry 2024 02

# 2025-02: maxt missing (AWS failed earlier); wdir on NAS
log "--- backfill maxt 2025-02 ---"
bash "$SCRIPTS/21_backfill_ndfd_yguz_month.sh" maxt 2025 02 "YGUZ*" >>"$LOG" 2>&1 \
  && log "OK backfill 2025-02 maxt" || log "WARN backfill 2025-02 maxt failed"
retry 2025 02

log "=== partial month retry complete $(date -u) ==="
