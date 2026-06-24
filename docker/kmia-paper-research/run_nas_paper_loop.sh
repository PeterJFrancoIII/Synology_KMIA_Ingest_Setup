#!/bin/bash
# NAS paper trading loop (Console 3) — every 5 min via DSM cron.
# NO REAL TRADING EXECUTION

set -euo pipefail

export TZ="${TZ:-America/New_York}"
export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"
export KMIA_PYTHON=/opt/kmia-venv/bin/python3

KALSHI="${KMIA_KALSHI_ROOT:-/data/Kalshi}"
LOG_DIR="${NAS_PAPER_LOG_DIR:-/data/logs/paper_trading}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/paper_loop_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NAS paper loop $STAMP ==="
echo "KALSHI=$KALSHI"

if [ ! -d "$KALSHI/backend/src" ] || [ ! -d "$KALSHI/scripts" ]; then
  echo "ERROR: Kalshi runtime missing — run deploy_kalshi_runtime_to_nas.sh from Mac"
  exit 1
fi

# shellcheck disable=SC1091
source /usr/local/bin/load_kalshi_api_env_nas.sh

export KMIA_KALSHI_ROOT="$KALSHI"
export PYTHONPATH="$KALSHI/backend/src"

# Dynamic window is default; anchor-only only if explicitly requested (after secrets load).
export PAPER_TRADING_WINDOW="${PAPER_TRADING_WINDOW:-dynamic}"
if [ "${PAPER_TRADING_WINDOW}" = "anchor_only" ]; then
  export PAPER_LOOP_ANCHOR_ONLY=1
else
  export PAPER_TRADING_WINDOW=dynamic
  export PAPER_LOOP_ANCHOR_ONLY=0
fi
echo "PAPER_TRADING_WINDOW=$PAPER_TRADING_WINDOW PAPER_LOOP_ANCHOR_ONLY=$PAPER_LOOP_ANCHOR_ONLY"

# Paper execution mode: maker_limit aligns forward paper with Legion5 maker backtest.
export PAPER_ORDER_MODE="${PAPER_ORDER_MODE:-maker_limit}"
export KALSHI_BACKTEST_ORDER_MODE="${KALSHI_BACKTEST_ORDER_MODE:-maker_limit}"
export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
echo "PAPER_ORDER_MODE=$PAPER_ORDER_MODE KALSHI_BACKTEST_ORDER_MODE=$KALSHI_BACKTEST_ORDER_MODE"

cd "$KALSHI"

bash scripts/run_paper_trading_loop.sh

echo "=== NAS paper loop complete ==="
