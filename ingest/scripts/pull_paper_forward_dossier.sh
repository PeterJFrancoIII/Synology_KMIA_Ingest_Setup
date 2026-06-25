#!/bin/bash
# Pull NAS paper-forward artifacts and generate weekly dossier (read-only).
#
# Usage:
#   NAS_HOST=MediaServer2 ./ingest/scripts/pull_paper_forward_dossier.sh
#   NAS_HOST=MediaServer2 ./ingest/scripts/pull_paper_forward_dossier.sh --no-markdown

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2}"
STAMP="$(date -u +%Y%m%d)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_DIR="$REPO_ROOT/docs/ops/paper_forward_analysis"
WRITE_MD=1

for arg in "$@"; do
  case "$arg" in
    --no-markdown) WRITE_MD=0 ;;
  esac
done

mkdir -p "$OUT_DIR"

NAS_KALSHI="/volume2/Data/App_Development/Kalshi"
pull() {
  local remote="$1"
  local local_name="$2"
  ssh "$NAS" "sudo cat '$remote' 2>/dev/null" > "$OUT_DIR/$local_name" || {
    echo "WARN: could not pull $remote"
    return 1
  }
}

echo "=== pull paper forward dossier $STAMP ==="

pull "$NAS_KALSHI/backend/data/processed/paper_trading/ledger.json" "ledger_nas_${STAMP}.json" || true
pull "$NAS_KALSHI/backend/data/processed/status/paper_forward_scorecard.json" "paper_forward_scorecard_nas_${STAMP}.json" || true
pull "$NAS_KALSHI/backend/data/processed/paper_trading/latest_paper_signal.json" "latest_paper_signal_nas_${STAMP}.json" || true
pull "$NAS_KALSHI/backend/data/research/trading_policy.json" "trading_policy_nas_${STAMP}.json" || true
pull "$NAS_KALSHI/backend/data/processed/kalshi_market_archive/ws_daemon_status.json" "ws_daemon_status_nas_${STAMP}.json" || true

LEDGER="$OUT_DIR/ledger_nas_${STAMP}.json"
if [ -f "$LEDGER" ]; then
  PYTHONPATH="$SCRIPT_DIR" python3 "$SCRIPT_DIR/classify_paper_ledger.py" \
    "$LEDGER" \
    --output "$OUT_DIR/ledger_classification_${STAMP}.json"
else
  echo "WARN: no ledger pulled; skipping classification"
fi

if [ "$WRITE_MD" -eq 1 ]; then
  REPORT="$OUT_DIR/PAPER_FORWARD_ANALYSIS_${STAMP}.md"
  export OUT_DIR STAMP REPORT
  python3 - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["OUT_DIR"])
stamp = os.environ["STAMP"]
report = Path(os.environ["REPORT"])
ledger_path = out_dir / f"ledger_classification_{stamp}.json"
score_path = out_dir / f"paper_forward_scorecard_nas_{stamp}.json"
signal_path = out_dir / f"latest_paper_signal_nas_{stamp}.json"
policy_path = out_dir / f"trading_policy_nas_{stamp}.json"

def load(p):
    return json.loads(p.read_text()) if p.is_file() else {}

cls = load(ledger_path)
score = load(score_path)
signal = load(signal_path)
policy = load(policy_path)
wg = signal.get("weather_gate") or {}
mp = score.get("mission_progress") or cls.get("gates") or {}
real_stats = score.get("trade_stats_real_kxhighmia") or {}

lines = [
    f"# Paper forward analysis — {stamp}",
    "",
    "**Generated:** pull_paper_forward_dossier.sh",
    "",
    "## Gates",
    "",
    "| Gate | Current | Target |",
    "|------|--------:|-------:|",
    f"| Real settled | {mp.get('real_settled_current', cls.get('real_settled', '—'))} | {mp.get('real_settled_target', 20)} |",
    f"| maker_limit settled | {mp.get('maker_limit_settled_current', cls.get('maker_limit_settled', '—'))} | {mp.get('maker_limit_settled_target', 10)} |",
    f"| Policy re-approval | {'ALLOWED' if mp.get('policy_reapproval_allowed') else 'HOLD'} | all gates |",
    "",
    "## Weather / signal",
    "",
    f"- weather_gate: {wg.get('status')} allow={wg.get('allow_paper_recommendations')}",
    f"- global_action: {(signal.get('bet_recommendations') or {}).get('global_action')}",
    f"- policy: {policy.get('order_mode')} edge={policy.get('min_forecast_edge')}",
    "",
    "## Real KXHIGHMIA stats",
    "",
    f"- settled: {real_stats.get('settled_trades', cls.get('real_settled'))}",
    f"- win_rate: {real_stats.get('win_rate_pct', cls.get('win_rate_pct'))}%",
    f"- pnl: {real_stats.get('total_pnl', cls.get('total_pnl_settled_real'))}",
    f"- mock_contamination: {score.get('mock_contamination')}",
    "",
    "## Artifacts",
    "",
]
for name in [
    f"ledger_nas_{stamp}.json",
    f"paper_forward_scorecard_nas_{stamp}.json",
    f"latest_paper_signal_nas_{stamp}.json",
    f"trading_policy_nas_{stamp}.json",
    f"ledger_classification_{stamp}.json",
]:
    lines.append(f"- {name}")

report.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {report}")
PY
fi

echo "=== dossier pull complete ==="
echo "OUT_DIR=$OUT_DIR"
