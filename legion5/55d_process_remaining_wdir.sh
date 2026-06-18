#!/usr/bin/env bash
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/retry_remaining_wdir.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

log() { echo "$(date -u) $1" | tee -a "$LOG"; }

if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || log "WARN SMB setup"
fi

# 2025-02 wdir pull was partial/corrupt (robocopy rc=9); re-pull from NAS.
rm -rf "$ROOT/raw/forecast/ndfd_aws/wdir/2025/02"

for ym in "2021 03" "2022 02" "2023 02" "2024 02" "2025 02"; do
  set -- $ym
  log "--- 35_process_month ${1}-${2} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$1" "$2" >>"$LOG" 2>&1 \
    && log "OK ${1}-${2}" || log "WARN failed ${1}-${2}"
done

log "=== remaining wdir batch complete $(date -u) ==="
