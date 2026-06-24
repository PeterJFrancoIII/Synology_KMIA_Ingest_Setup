#!/usr/bin/env bash
# Remove Legion5 local NDFD GRIB after successful NAS consolidation.
# Requires prior successful: 56_consolidate_legion5_grib_to_nas.sh verify
#
# Usage:
#   bash 57_cleanup_legion5_grib.sh dry-run
#   CONFIRM=YES bash 57_cleanup_legion5_grib.sh delete

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
MODE="${1:-dry-run}"
CONFIRM="${CONFIRM:-}"

LOG="$ROOT/logs/ingestion/grib_cleanup.log"
PLAN="$ROOT/logs/ingestion/grib_consolidation_plan.tsv"
TRANSFER_LOG="$ROOT/logs/ingestion/grib_consolidation_transfer.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"

SOURCES=(
  "/e/KMIA_Ingest/raw/forecast/ndfd_aws"
  "/d/KMIA_Process/raw/forecast/ndfd_aws"
)

log() { echo "[57_cleanup] $*" | tee -a "$LOG"; }

if [ ! -f "$PLAN" ] || ! grep -q "VERIFY OK" "$TRANSFER_LOG" 2>/dev/null; then
  log "ERROR: run 56_consolidate transfer+verify first (need plan + VERIFY OK in transfer log)"
  exit 1
fi

for src_root in "${SOURCES[@]}"; do
  [ -d "$src_root" ] || continue
  file_count=$(find "$src_root" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' ')
  size_bytes=$(find "$src_root" -type f ! -name 'Icon*' -exec stat -c '%s' {} + 2>/dev/null \
    | awk '{s+=$1} END {print s+0}')
  size_gb=$(awk -v b="${size_bytes:-0}" 'BEGIN { printf "%.1f", b/1073741824 }')
  log "$src_root — $file_count files (~${size_gb} GB)"
  if [ "$MODE" = "delete" ]; then
    if [ "$CONFIRM" != "YES" ]; then
      log "Set CONFIRM=YES to delete"
      exit 1
    fi
    log "DELETING $src_root ..."
    rm -rf "$src_root"/* 2>/dev/null \
      || powershell.exe -Command "Remove-Item -Recurse -Force '${src_root//\//\\}\*'" 2>/dev/null \
      || true
    log "Deleted contents of $src_root"
  fi
done

# Mac-side Kalshi test raw dirs (informational — run from Mac orchestrator)
log "After Legion5 cleanup, run Mac orchestrator to remove Kalshi NCEI_Historical_Ingest test raw/ dirs"

if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -Command "Get-PSDrive E,D | Format-Table Name,Used,Free" | tee -a "$LOG"
fi

log "DONE mode=$MODE"
