#!/usr/bin/env bash
# One-shot Legion5 max-ROI policy pass. NO REAL TRADING.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
export FORCE_NDFD_RESEARCH=1
export KALSHI_POLICY_SELECTION=max_roi
export POLICY_SWEEP_WORKERS="${POLICY_SWEEP_WORKERS:-8}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

echo "=== Legion5 max-ROI policy pass ==="
echo "time=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Z read root: $KMIA_KALSHI_READ_ROOT"
echo "price dir:   $KALSHI_PRICE_DIR"
echo "backtest:    $CONSOLE2_BACKTEST_DIR"
echo "selection:   $KALSHI_POLICY_SELECTION"

if [ ! -d "$KMIA_KALSHI_READ_ROOT" ]; then
  echo "ERROR: NAS Kalshi read root missing — mount Z: (43_setup_nas_smb.ps1)" >&2
  exit 2
fi
if [ ! -d "$KALSHI_PRICE_DIR" ]; then
  echo "ERROR: Kalshi price history dir missing: $KALSHI_PRICE_DIR" >&2
  exit 2
fi

bash "$SCRIPTS/54_kalshi_ndfd_research_pipeline.sh"

echo "=== DONE — max ROI draft ==="
"$PYTHON" -c "
import json, os
from pathlib import Path
p = Path(os.environ['CONSOLE2_BACKTEST_DIR']) / 'recommended_policy.json'
if p.is_file():
    r = json.loads(p.read_text()).get('recommended_policy') or json.loads(p.read_text())
    print(f\"edge={r.get('min_forecast_edge')} cap={r.get('max_entry_yes_ask')} mode={r.get('insurance_mode')} k={r.get('insurance_price_k')} budget={r.get('insurance_budget_fraction')}\")
    print(f\"ROI={r.get('roi_pct')}% win={r.get('win_rate_pct')}% P&L=\${r.get('total_pnl')} n={r.get('n_trades')}\")
    print(f\"method={r.get('selection_method')}\")
"
