#!/usr/bin/env bash
# Legion5: Quant Core baseline — priors, backtest, sweep, isotonic, NBM validate.
# NO REAL TRADING EXECUTION
#
# Usage:
#   bash D:/KMIA_Process/scripts/55_quant_core_baseline.sh

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

export BACKTEST_TRADING_WINDOW=dynamic
export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
export KALSHI_POLICY_SELECTION="${KALSHI_POLICY_SELECTION:-max_roi}"
export POLICY_SWEEP_WORKERS="${POLICY_SWEEP_WORKERS:-8}"

LOG_DIR="$ROOT/logs/research"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/quant_core_baseline_$(date +%Y%m%dT%H%M%SZ).log"

log() { echo "[quant_core] $*" | tee -a "$LOG"; }

if [ ! -d "$KMIA_KALSHI_READ_ROOT" ]; then
  log "Mounting Z: via 43_setup_nas_smb.ps1…"
  if [ -f "$ROOT/secrets/nas_smb_password" ] && [ -f "$SCRIPTS/43_setup_nas_smb.ps1" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || true
  else
    log "WARN: cannot auto-mount Z: (missing password or ps1)"
  fi
fi

if [ ! -d "$KMIA_KALSHI_READ_ROOT" ]; then
  log "ERROR: NAS Kalshi read root missing — mount Z: (43_setup_nas_smb.ps1)" >&2
  exit 2
fi
if [ ! -d "$KALSHI_PRICE_DIR" ]; then
  log "ERROR: Kalshi price history dir missing: $KALSHI_PRICE_DIR" >&2
  exit 2
fi

ENRICHED="$CONSOLE2_ROOT/analysis/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv"
if [ ! -f "$ENRICHED" ]; then
  log "ERROR: enriched CSV missing: $ENRICHED" >&2
  exit 2
fi

log "kalshi_read=$KMIA_KALSHI_READ_ROOT"
log "price_dir=$KALSHI_PRICE_DIR backtest=$CONSOLE2_BACKTEST_DIR"
log "BACKTEST_TRADING_WINDOW=$BACKTEST_TRADING_WINDOW"

log "[1/7] Build expected max-hour priors…"
"$PYTHON" "$SCRIPTS/build_expected_max_hour_priors.py" \
  --csv "$ENRICHED" \
  --out "$CONSOLE2_BACKTEST_DIR/expected_max_hour_priors.json" 2>&1 | tee -a "$LOG"
mkdir -p "$KALSHI_RESEARCH_DIR"
cp -f "$CONSOLE2_BACKTEST_DIR/expected_max_hour_priors.json" \
  "$KALSHI_RESEARCH_DIR/expected_max_hour_priors.json" 2>/dev/null || true

log "[2/7] Taker backtest (dynamic trading window)…"
"$PYTHON" "$SCRIPTS/historical_checksum_backtest.py" \
  --mode kalshi \
  --order-mode taker \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
  --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
  --output-dir "$CONSOLE2_BACKTEST_DIR" 2>&1 | tee -a "$LOG"

log "[3/7] Policy sweep (workers=$POLICY_SWEEP_WORKERS)…"
"$PYTHON" "$SCRIPTS/kalshi_policy_optimizer.py" \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
  --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
  --output-dir "$CONSOLE2_BACKTEST_DIR" \
  --workers "$POLICY_SWEEP_WORKERS" \
  --selection "$KALSHI_POLICY_SELECTION" \
  --order-mode taker 2>&1 | tee -a "$LOG"

log "[4/7] Maker vs taker dual report…"
"$PYTHON" "$SCRIPTS/historical_checksum_backtest.py" \
  --mode kalshi \
  --price-history-dir "$KALSHI_PRICE_DIR" \
  --orderbook-archive-dir "$KALSHI_MARKET_ARCHIVE_DIR" \
  --candle-archive-dir "$KALSHI_CANDLE_ARCHIVE_DIR" \
  --output-dir "$CONSOLE2_BACKTEST_DIR" \
  --dual-report 2>&1 | tee -a "$LOG"

log "[5/7] Fit isotonic calibration (needs scikit-learn)…"
"$PYTHON" "$SCRIPTS/fit_bin_isotonic_calibration.py" \
  --out "$CONSOLE2_BACKTEST_DIR/bin_isotonic_v1.json" 2>&1 | tee -a "$LOG" \
  || log "WARN: isotonic fit skipped/failed"
mkdir -p "$KALSHI_RESEARCH_DIR/calibration"
cp -f "$CONSOLE2_BACKTEST_DIR/bin_isotonic_v1.json" \
  "$KALSHI_RESEARCH_DIR/calibration/bin_isotonic_v1.json" 2>/dev/null || true

log "[6/7] NBM fetch + validation gate…"
"$PYTHON" "$SCRIPTS/fetch_nbm_maxt_kmia.py" \
  --out "$CONSOLE2_BACKTEST_DIR/nbm_maxt_archive.jsonl" 2>&1 | tee -a "$LOG" \
  || log "WARN: NBM fetch failed"
"$PYTHON" "$SCRIPTS/validate_nbm_vs_historical_stability.py" \
  --enriched-csv "$ENRICHED" \
  --nbm-jsonl "$CONSOLE2_BACKTEST_DIR/nbm_maxt_archive.jsonl" \
  --out "$CONSOLE2_BACKTEST_DIR/nbm_validation_report.json" 2>&1 | tee -a "$LOG" \
  || log "WARN: NBM validation failed"

log "[7/7] Export policy drafts…"
"$PYTHON" "$SCRIPTS/export_trading_policy.py" \
  --backtest-dir "$CONSOLE2_BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH_DIR" \
  --order-mode taker \
  --no-copy 2>&1 | tee -a "$LOG"

"$PYTHON" -c "
import json
from pathlib import Path
import os
bt = Path(os.environ['CONSOLE2_BACKTEST_DIR'])
rec = bt / 'recommended_policy.json'
if rec.is_file():
    p = json.loads(rec.read_text())
    r = p.get('recommended_policy') or p
    print('recommended:', 'edge=', r.get('min_forecast_edge'), 'cap=', r.get('max_entry_yes_ask'),
          'ROI=', r.get('roi_pct'), 'win=', r.get('win_rate_pct'), 'n=', r.get('n_trades'),
          'ece=', r.get('ece'), 'calibration_pass=', r.get('calibration_pass'))
nbm = bt / 'nbm_validation_report.json'
if nbm.is_file():
    print('nbm_pass=', json.loads(nbm.read_text()).get('pass'))
print('log=', '$LOG')
" 2>&1 | tee -a "$LOG"

log "COMPLETE — review $CONSOLE2_BACKTEST_DIR/recommended_policy.json"
log "Sync mirror to NAS: powershell D:\\KMIA_Process\\scripts\\55_sync_kalshi_mirror_to_nas.ps1"
