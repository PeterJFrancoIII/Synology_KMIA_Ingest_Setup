#!/usr/bin/env bash
# Launch raw ingest only — one year at a time (low CPU; downloads for later processing).
set -euo pipefail

ROOT="/data/KMIA_Ingest"
SCRIPTS="$ROOT/scripts"
LOG="$ROOT/logs/ingestion/launch_ingest.log"

mkdir -p "$ROOT/logs/ingestion"

log() { echo "$1" | tee -a "$LOG"; }

log "=== NAS sequential raw ingest $(date -u) ==="

for YEAR in 2020 2021 2022 2023 2024 2025 2026; do
  log "ingest year ${YEAR}"
  bash "$SCRIPTS/27_nas_year_ingest.sh" "$YEAR" >>"$LOG" 2>&1
  log "year ${YEAR} ingest complete"
done

log "all years ingested $(date -u)"
