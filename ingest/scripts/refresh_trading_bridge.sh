#!/bin/bash
# Post-sweep artifacts: frontier chart, human review, Kalshi pipeline status.
# NO REAL TRADING EXECUTION

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

source "${SCRIPT_DIR}/kmia_kalshi_env.sh" 2>/dev/null || true
export PYTHONPATH="${REPO_ROOT}/ingest/scripts:${PYTHONPATH:-}"

BACKTEST_DIR="${CONSOLE2_BACKTEST_DIR:-$REPO_ROOT/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest}"
KALSHI_RESEARCH="${KALSHI_RESEARCH_DIR:-$(python3 -c 'from kmia_kalshi_paths import kalshi_research_dir; print(kalshi_research_dir())')}"
KALSHI_ROOT="${KMIA_KALSHI_ROOT:-$HOME/Desktop/App Development/Kalshi}"

SWEEP="$(ls -t "$BACKTEST_DIR"/policy_sweep_*.json 2>/dev/null | head -1 || true)"
if [ -n "$SWEEP" ]; then
  echo "[bridge 1/3] Policy frontier chart..."
  python3 ingest/scripts/chart_kalshi_policy_frontier.py \
    --sweep-json "$SWEEP" \
    --output-dir "$BACKTEST_DIR" || echo "WARN: frontier chart skipped"
else
  echo "[bridge 1/3] Skip frontier (no policy_sweep JSON)"
fi

echo "[bridge 2/3] Human review + bridge status..."
python3 ingest/scripts/write_policy_human_review.py \
  --backtest-dir "$BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH" \
  --skip-export

if [ -f "$KALSHI_ROOT/scripts/update_trading_pipeline_status.py" ]; then
  echo "[bridge 3/3] Kalshi pipeline status..."
  (cd "$KALSHI_ROOT" && PYTHONPATH=backend/src python3 scripts/update_trading_pipeline_status.py \
    --console2-backtest-dir "$BACKTEST_DIR") || echo "WARN: pipeline status update failed"
else
  echo "[bridge 3/3] Skip Kalshi pipeline status (Kalshi repo not found)"
fi

echo "Bridge artifacts ready:"
echo "  $BACKTEST_DIR/policy_review_for_human.txt"
echo "  $REPO_ROOT/0_Developer_Source_Files/trade_policies.md"
echo "  $KALSHI_RESEARCH/trading_policy_draft.json"
