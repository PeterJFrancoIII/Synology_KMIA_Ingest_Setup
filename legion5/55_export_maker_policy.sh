#!/usr/bin/env bash
# Export maker_limit policy from trading_window_ab dynamic winner → kalshi_mirror.
# NO REAL TRADING EXECUTION
#
# Prerequisite: 55_trading_window_ab.sh (recommended_policy_dynamic.json)
#
# Usage:
#   bash D:/KMIA_Process/scripts/55_export_maker_policy.sh

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

BT="$CONSOLE2_BACKTEST_DIR"
RD="$KALSHI_RESEARCH_DIR"
DYNAMIC="$BT/recommended_policy_dynamic.json"
REC="$BT/recommended_policy.json"

log() { echo "[export_maker] $*"; }

if [ ! -f "$DYNAMIC" ]; then
  log "ERROR: missing $DYNAMIC — run 55_trading_window_ab.sh first" >&2
  exit 2
fi

log "Promote recommended_policy_dynamic.json → recommended_policy.json"
cp -f "$DYNAMIC" "$REC"

log "Export trading_policy_draft.json (maker_limit)…"
"$PYTHON" "$SCRIPTS/export_trading_policy.py" \
  --backtest-dir "$BT" \
  --kalshi-research-dir "$RD" \
  --order-mode maker_limit \
  --no-copy
# Keep backtest dir draft in sync for bridge refresh
cp -f "$RD/trading_policy_draft.json" "$BT/trading_policy_draft.json" 2>/dev/null || true

bash "$SCRIPTS/55_prep_mirror_sync.sh"

log "COMPLETE — draft at $RD/trading_policy_draft.json"
log "Next: powershell -File $SCRIPTS/55_sync_research_to_nas.ps1"
