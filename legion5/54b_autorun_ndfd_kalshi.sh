#!/usr/bin/env bash
# Legion5 autorun: wait for NDFD extract job → research pipeline (no Mac).
#
# Usage:
#   bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --watch 202604_202606
#   bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --once 202604_202606

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
MODE="${1:-watch}"
JOB_TAG="${2:-202604_202606}"
POLL_SEC="${AUTORUN_POLL_SEC:-45}"
DONE_MARKER="$ROOT/logs/jobs/ndfd_kalshi_${JOB_TAG}.done"
MERGED="$ROOT/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv"
LOG_DIR="$ROOT/logs/autorun"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/autorun_${JOB_TAG}_$(date +%Y%m%dT%H%M%SZ).log"

log() { echo "[autorun $(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

job_complete() {
  [ -f "$DONE_MARKER" ] && return 0
  local procs
  procs="$(powershell.exe -NoProfile -Command "(Get-Process python -ErrorAction SilentlyContinue).Count" 2>/dev/null | tr -d '\r' || echo 0)"
  [ "${procs:-0}" -eq 0 ] && [ -f "$MERGED" ] && [ -s "$MERGED" ]
}

wait_job() {
  log "watch JOB_TAG=$JOB_TAG poll=${POLL_SEC}s marker=$DONE_MARKER"
  while ! job_complete; do
    procs="$(powershell.exe -NoProfile -Command "(Get-Process python -ErrorAction SilentlyContinue).Count" 2>/dev/null | tr -d '\r' || echo 0)"
    log "waiting… python=$procs"
    sleep "$POLL_SEC"
  done
  log "extract/merge complete"
}

run_pipeline() {
  if [ ! -f "$MERGED" ] || [ ! -s "$MERGED" ]; then
    log "merge missing — running 52c…"
    bash "$SCRIPTS/52c_merge_kalshi_ndfd.sh" 2026 >>"$LOG" 2>&1
  fi
  bash "$SCRIPTS/54_kalshi_ndfd_research_pipeline.sh" "$MERGED" >>"$LOG" 2>&1
}

case "$MODE" in
  --watch) wait_job; run_pipeline ;;
  --once)  run_pipeline ;;
  *) echo "Usage: $0 [--watch|--once] [JOB_TAG]" >&2; exit 1 ;;
esac

log "autorun done — see $LOG"
