#!/usr/bin/env bash
# CI guard: Research git contract + file size limits.
# Whitelist large canonical research files; block regenerable sweeps/backtests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

FAIL=0

# 1) Regenerable artifacts must not be tracked
FORBIDDEN_PATTERNS=(
  'Research/**/Kalshi_Price_Backtest/policy_sweep_*.json'
  'Research/**/Kalshi_Price_Backtest/kalshi_price_backtest_*.json'
  'Research/**/Kalshi_Price_Backtest/policy_frontier_*.html'
  'Research/**/Kalshi_Price_Backtest/policy_pattern_analysis_*.json'
  'Research/**/Kalshi_Price_Backtest/legion5_run_*'
  'Research/**/Legion5_Extract/**'
  'Research/**/*_stability_wind.png'
)

for pat in "${FORBIDDEN_PATTERNS[@]}"; do
  # shellcheck disable=SC2086
  hits=$(git ls-files $pat 2>/dev/null || true)
  if [ -n "$hits" ]; then
    echo "FAIL: tracked forbidden Research artifact(s) matching $pat:"
    echo "$hits"
    FAIL=1
  fi
done

# 2) Tracked files over 1 MiB need whitelist
MAX_BYTES=$((1024 * 1024))
while IFS= read -r f; do
  [ -z "$f" ] && continue
  size=$(wc -c <"$f" | tr -d ' ')
  if [ "$size" -gt "$MAX_BYTES" ]; then
    case "$f" in
      */accuracy_points_enriched.csv|*/kmia_chart_suite.html|*/kmia_interactive_accuracy_explorer.html)
        continue
        ;;
      *)
        echo "FAIL: tracked file >1MiB not whitelisted: $f ($size bytes)"
        FAIL=1
        ;;
    esac
  fi
done < <(git ls-files 'Research/**')

# 3) Required contract files present
REQUIRED=(
  "Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest/recommended_policy.json"
  "Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest/trading_policy_draft.json"
  "ingest/scripts/fixtures/sample_policy_sweep.json"
  "legion5/ACTIVE_MANIFEST.json"
  "ingest/scripts/ACTIVE_MANIFEST.json"
  "0_Developer_Source_Files/ROUTING.md"
)
for f in "${REQUIRED[@]}"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: missing required agent navigation file: $f"
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi

echo "OK: Research git contract checks passed."
