#!/usr/bin/env bash
# Legion5: NDFD merged CSV → NWS backfill → backtest → policy sweep → export drafts.
# Writes to NAS Kalshi tree via Z: (shared with MediaServer2Local container).
# NO REAL TRADING EXECUTION
#
# Usage:
#   bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh
#   bash .../54_kalshi_ndfd_research_pipeline.sh /path/to/kalshi_ndfd_maxt_VALID_ONLY.csv

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

MERGED="${1:-$NDFD_KALSHI_MAXT_CSV}"
WORKERS="${POLICY_SWEEP_WORKERS:-8}"
STATE_FILE="$CONSOLE2_BACKTEST_DIR/.ndfd_research_last_sha256"
LOG_DIR="$ROOT/logs/research"
mkdir -p "$LOG_DIR" "$CONSOLE2_BACKTEST_DIR"
LOG="$LOG_DIR/kalshi_ndfd_research_$(date +%Y%m%dT%H%M%SZ).log"

log() { echo "[54_research] $*" | tee -a "$LOG"; }

if [ ! -f "$MERGED" ]; then
  log "ERROR: merged NDFD CSV missing: $MERGED"
  exit 1
fi

if [ -f "$STATE_FILE" ] && [ "${FORCE_NDFD_RESEARCH:-0}" != "1" ]; then
  cur="$("$PYTHON" -c "import hashlib, pathlib; p=pathlib.Path(r'''$MERGED'''); print(hashlib.sha256(p.read_bytes()).hexdigest())")"
  prev="$(grep '^csv_sha256=' "$STATE_FILE" | cut -d= -f2- || true)"
  if [ -n "$prev" ] && [ "$cur" = "$prev" ]; then
    log "skip — already processed this CSV (sha256 match)"
    exit 0
  fi
fi

log "merged=$MERGED"
log "kalshi=$KMIA_KALSHI_ROOT nws=$KALSHI_NWS_DIR backtest=$CONSOLE2_BACKTEST_DIR"

log "[1/5] NDFD → NWS snapshots (--replace-iem)…"
"$PYTHON" "$SCRIPTS/backfill_nws_snapshots_from_ndfd.py" \
  --ndfd-csv "$MERGED" \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --nws-dir "$KALSHI_NWS_DIR" \
  --replace-iem 2>&1 | tee -a "$LOG"

log "[2/5] taker backtest (matches live paper)…"
"$PYTHON" "$SCRIPTS/historical_checksum_backtest.py" \
  --mode kalshi \
  --order-mode taker \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --output-dir "$CONSOLE2_BACKTEST_DIR" 2>&1 | tee -a "$LOG"

log "[3/5] policy sweep (workers=$WORKERS selection=${KALSHI_POLICY_SELECTION:-max_roi} taker)…"
"$PYTHON" "$SCRIPTS/kalshi_policy_optimizer.py" \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --output-dir "$CONSOLE2_BACKTEST_DIR" \
  --workers "$WORKERS" \
  --selection "${KALSHI_POLICY_SELECTION:-max_roi}" \
  --order-mode taker 2>&1 | tee -a "$LOG"

log "[4/5] export drafts…"
"$PYTHON" "$SCRIPTS/export_trading_policy.py" \
  --backtest-dir "$CONSOLE2_BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH_DIR" \
  --no-copy 2>&1 | tee -a "$LOG"

"$PYTHON" "$SCRIPTS/export_safest_policy_from_sweep.py" \
  --backtest-dir "$CONSOLE2_BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH_DIR" 2>&1 | tee -a "$LOG" || log "WARN: safest export skipped"

log "[5/5] state + sync note"
cur_sha="$("$PYTHON" -c "import hashlib, pathlib; p=pathlib.Path(r'''$MERGED'''); print(hashlib.sha256(p.read_bytes()).hexdigest())")"
{
  echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "csv_sha256=$cur_sha"
  echo "merged=$MERGED"
  echo "log=$LOG"
} > "$STATE_FILE"

log "COMPLETE — Legion5 mirror (sync to NAS via 55_sync_kalshi_mirror_to_nas.ps1):"
log "  $KALSHI_RESEARCH_DIR/trading_policy_draft.json"
log "  $KALSHI_RESEARCH_DIR/trading_policy_safest_draft.json"
log "  $CONSOLE2_BACKTEST_DIR/recommended_policy.json"
log "  $KALSHI_NWS_DIR/ (NDFD snapshots)"
