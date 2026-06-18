#!/usr/bin/env bash
# Retry partial gap months, then resume full NAS BUILD (2020–2025).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/retry_and_resume.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_LOCAL_ROOT="$ROOT"
export KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

mkdir -p "$ROOT/logs/processing" "$ROOT/logs/ingestion"

log() { echo "$1" | tee -a "$LOG"; }

log "=== retry + resume start $(date -u) ==="

if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup"
fi

retry_month() {
  local y="$1" m="$2"
  log "--- retry extract ${y}-${m} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" >>"$LOG" 2>&1 \
    || log "WARN retry ${y}-${m} failed"
}

# Feb months: maxt on D: from gap backfill; wdir on NAS — pull + extract wdir only.
retry_month 2020 07
retry_month 2021 03
retry_month 2022 02
retry_month 2023 02
retry_month 2024 02

# 2025-02 maxt: re-attempt AWS backfill then full month extract.
log "--- backfill maxt 2025-02 ---"
bash "$SCRIPTS/21_backfill_ndfd_yguz_month.sh" maxt 2025 02 "YGUZ*" >>"$LOG" 2>&1 \
  || log "WARN 2025-02 maxt backfill failed"
retry_month 2025 02

log "=== starting full BUILD 2020–2025 (skips complete months) ==="
export KMIA_BUILD_CHARTS=1
bash "$SCRIPTS/36_process_all_from_nas.sh" >>"$LOG" 2>&1

log "=== retry + resume complete $(date -u) ==="
