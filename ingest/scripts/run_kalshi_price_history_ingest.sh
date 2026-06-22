#!/bin/bash
# Fetch missing Kalshi KXHIGHMIA price-history CSVs from the public API.
# NO REAL TRADING EXECUTION

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PRICE_DIR="${KALSHI_PRICE_DIR:-/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History}"

python3 ingest/scripts/ingest_kalshi_market_data.py \
  --output-dir "$PRICE_DIR" \
  "$@"
