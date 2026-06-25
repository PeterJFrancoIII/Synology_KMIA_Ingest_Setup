#!/usr/bin/env bash
# ONE-TIME: purge regenerable large blobs from git history (policy sweeps, backtests, wind PNG).
# Requires: git-filter-repo (`brew install git-filter-repo`)
# WARNING: Rewrites history — coordinate before `git push --force origin main`.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "Install git-filter-repo first (e.g. brew install git-filter-repo)"
  exit 1
fi

echo "This will rewrite ALL commits. Press Ctrl+C to abort."
sleep 3

git filter-repo --force \
  --path-glob 'Research/**/Kalshi_Price_Backtest/policy_sweep_*.json' \
  --path-glob 'Research/**/Kalshi_Price_Backtest/kalshi_price_backtest_*.json' \
  --path-glob 'Research/**/Kalshi_Price_Backtest/policy_frontier_*.html' \
  --path-glob 'Research/**/Kalshi_Price_Backtest/policy_pattern_analysis_*.json' \
  --path-glob 'Research/**/Kalshi_Price_Backtest/legion5_run_*/' \
  --path-glob 'Research/**/KMIA_NDFD_Year_MaxT_Precision_2021/kmia_2021_stability_wind.png' \
  --path-glob 'Research/**/KMIA_NDFD_Year_MaxT_Precision_2021/kmia_2021_PLUS_mean_median_stability_wind_points.csv' \
  --invert-paths

git remote add origin git@github.com:PeterJFrancoIII/Synology_KMIA_Ingest_Setup.git 2>/dev/null || true
git reflog expire --expire=now --all
git gc --prune=now --aggressive

du -sh .git
echo "Done. Verify with: bash ingest/scripts/ci/check_research_git_contract.sh"
echo "Then: git push --force origin main  (only if you intend to rewrite remote)"
