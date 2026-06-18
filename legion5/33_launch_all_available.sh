#!/usr/bin/env bash
# Launch 2021-2026 year pipelines (3 at a time, batched).
set -euo pipefail

export KMIA_ROOT="${KMIA_ROOT:-/e/KMIA_Ingest}"
export KMIA_PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}"
export PATH="$KMIA_PATH:$PATH"

ROOT="$KMIA_ROOT"
SCRIPTS="$ROOT/scripts"
LOG="$ROOT/logs/ingestion/launch_all.log"

mkdir -p "$ROOT/logs/ingestion"

log() { echo "$1" | tee -a "$LOG"; }

log "=== launch parallel years $(date -u) ==="

start_year() {
  local y="$1"
  nohup bash "$SCRIPTS/03_legion5_year_pipeline.sh" "$y" \
    > "$ROOT/logs/ingestion/legion5_year_${y}.nohup.log" 2>&1 &
  log "started year ${y} pid $!"
}

# Batch 1: 2021-2023
for YEAR in 2021 2022 2023; do
  start_year "$YEAR"
  sleep 45
done

log "batch 1 launched; waiting before batch 2..."
sleep 10

# Batch 2: 2024-2026 (2026 partial through Jun in pipeline)
for YEAR in 2024 2025 2026; do
  start_year "$YEAR"
  sleep 45
done

log "all years launched $(date -u)"
