#!/usr/bin/env bash
# Legion5: A/B backtest — BACKTEST_TRADING_WINDOW dynamic vs anchor (maker_limit).
# NO REAL TRADING EXECUTION
#
# Usage:
#   bash D:/KMIA_Process/scripts/55_trading_window_ab.sh

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
export POLICY_SWEEP_WORKERS="${POLICY_SWEEP_WORKERS:-8}"

LOG_DIR="$ROOT/logs/research"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/trading_window_ab_$(date +%Y%m%dT%H%M%SZ).log"

log() { echo "[window_ab] $*" | tee -a "$LOG"; }

if [ ! -d "$KMIA_KALSHI_READ_ROOT" ]; then
  if [ -f "$ROOT/secrets/nas_smb_password" ] && [ -f "$SCRIPTS/43_setup_nas_smb.ps1" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || true
  fi
fi
if [ ! -d "$KALSHI_PRICE_DIR" ]; then
  log "ERROR: price history missing: $KALSHI_PRICE_DIR" >&2
  exit 2
fi

OUT_DIR="$CONSOLE2_BACKTEST_DIR"
AB_JSON="$OUT_DIR/trading_window_ab.json"

run_mode() {
  local mode="$1"
  local tag="$2"
  export BACKTEST_TRADING_WINDOW="$mode"
  log "=== mode=$mode tag=$tag ==="

  "$PYTHON" "$SCRIPTS/historical_checksum_backtest.py" \
    --mode kalshi \
    --order-mode maker_limit \
    --price-history-dir "$KALSHI_PRICE_DIR" \
    --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
    --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
    --output-dir "$OUT_DIR" 2>&1 | tee -a "$LOG"

  "$PYTHON" "$SCRIPTS/kalshi_policy_optimizer.py" \
    --price-history-dir "$KALSHI_PRICE_DIR" \
    --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
    --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
    --output-dir "$OUT_DIR" \
    --workers "$POLICY_SWEEP_WORKERS" \
    --order-mode maker_limit \
    --selection "$KALSHI_POLICY_SELECTION" 2>&1 | tee -a "$LOG"

  cp -f "$OUT_DIR/recommended_policy.json" "$OUT_DIR/recommended_policy_${tag}.json" 2>/dev/null || true
}

log "Starting trading window A/B (maker_limit)…"
run_mode dynamic dynamic
run_mode anchor anchor

# Taker dynamic reference (parity with quant_core baseline)
export BACKTEST_TRADING_WINDOW=dynamic
log "=== taker reference (dynamic) ==="
"$PYTHON" "$SCRIPTS/kalshi_policy_optimizer.py" \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
  --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
  --output-dir "$OUT_DIR" \
  --workers "$POLICY_SWEEP_WORKERS" \
  --order-mode taker \
  --selection "$KALSHI_POLICY_SELECTION" 2>&1 | tee -a "$LOG"
cp -f "$OUT_DIR/recommended_policy.json" "$OUT_DIR/recommended_policy_taker_dynamic.json" 2>/dev/null || true

"$PYTHON" -c "
import json
from datetime import datetime, timezone
from pathlib import Path
import os

out = Path(os.environ['CONSOLE2_BACKTEST_DIR'])

def load_rec(name):
    p = out / name
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding='utf-8'))
    return data.get('recommended_policy') or data

def summarize(r):
    if not r:
        return {}
    return {
        'min_forecast_edge': r.get('min_forecast_edge'),
        'max_entry_yes_ask': r.get('max_entry_yes_ask'),
        'n_trades': r.get('n_trades'),
        'win_rate_pct': r.get('win_rate_pct'),
        'roi_pct': r.get('roi_pct'),
        'total_pnl': r.get('total_pnl'),
        'ece': r.get('ece'),
        'calibration_pass': r.get('calibration_pass'),
        'selection_method': r.get('selection_method'),
    }

payload = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'order_mode_primary': 'maker_limit',
    'comparison': {
        'dynamic': summarize(load_rec('recommended_policy_dynamic.json')),
        'anchor': summarize(load_rec('recommended_policy_anchor.json')),
        'taker_dynamic_reference': summarize(load_rec('recommended_policy_taker_dynamic.json')),
    },
    'note': 'maker_limit A/B; taker_dynamic for parity with quant_core baseline',
}
ab = out / 'trading_window_ab.json'
ab.write_text(json.dumps(payload, indent=2), encoding='utf-8')
print('Wrote', ab)
for k, v in payload['comparison'].items():
    print(k, 'n=', v.get('n_trades'), 'win=', v.get('win_rate_pct'), 'roi=', v.get('roi_pct'))
" 2>&1 | tee -a "$LOG"

log "COMPLETE — $AB_JSON log=$LOG"
