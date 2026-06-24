#!/usr/bin/env bash
# Copy backtest research artifacts into kalshi_mirror before NAS robocopy.
set -euo pipefail
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"
BT="$CONSOLE2_BACKTEST_DIR"
RD="$KALSHI_RESEARCH_DIR"
mkdir -p "$RD/calibration"
for f in expected_max_hour_priors.json bin_isotonic_v1.json nbm_maxt_archive.jsonl nbm_validation_report.json recommended_policy.json; do
  if [ -f "$BT/$f" ]; then
  case "$f" in
    bin_isotonic_v1.json) cp -f "$BT/$f" "$RD/calibration/$f" ;;
    *) cp -f "$BT/$f" "$RD/$f" ;;
  esac
  echo "copied $f"
  fi
done
# Export draft if missing
if [ ! -f "$RD/trading_policy_draft.json" ] && [ -f "$BT/recommended_policy.json" ]; then
  "${KMIA_PYTHON:-/e/Miniforge3/python.exe}" "$SCRIPTS/export_trading_policy.py" \
    --backtest-dir "$BT" --kalshi-research-dir "$RD" --order-mode maker_limit --no-copy 2>/dev/null || true
fi
echo "mirror prep ok: $RD"
