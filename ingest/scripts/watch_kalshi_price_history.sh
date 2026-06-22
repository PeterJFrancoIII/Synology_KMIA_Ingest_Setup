#!/bin/bash
# Watch Kalshi price-history folder; on new CSV run backtest + policy sweep + export draft.
# NO REAL TRADING EXECUTION

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PRICE_DIR="${KALSHI_PRICE_DIR:-/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History}"
BACKTEST_DIR="$ROOT/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest"
KALSHI_RESEARCH="${KALSHI_RESEARCH_DIR:-/Users/computer/Desktop/App Development/Kalshi/backend/data/research}"
STATE_FILE="${BACKTEST_DIR}/.last_price_history_mtime"

if [[ ! -d "$PRICE_DIR" ]]; then
  echo "Price history dir missing: $PRICE_DIR" >&2
  exit 1
fi

latest_csv="$(find "$PRICE_DIR" -maxdepth 1 -name 'kalshi-price-history-*.csv' -type f 2>/dev/null | sort | tail -1)"
if [[ -z "$latest_csv" ]]; then
  echo "No kalshi-price-history-*.csv in $PRICE_DIR"
  exit 0
fi

mtime="$(stat -f '%m' "$latest_csv" 2>/dev/null || stat -c '%Y' "$latest_csv")"
last_mtime=""
if [[ -f "$STATE_FILE" ]]; then
  last_mtime="$(cat "$STATE_FILE")"
fi

if [[ "$mtime" == "$last_mtime" ]]; then
  echo "No new price-history CSV (latest: $(basename "$latest_csv"))"
  exit 0
fi

echo "New CSV detected: $(basename "$latest_csv") — running policy refresh..."
bash "$ROOT/ingest/scripts/run_daily_policy_refresh.sh"
echo "$mtime" > "$STATE_FILE"
echo "Draft policy exported; human must approve trading_policy.json"
