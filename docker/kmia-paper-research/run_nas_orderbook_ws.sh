#!/bin/bash
# NAS WebSocket orderbook archiver — long-running daemon in kmia-orderbook-ws container.
# NO REAL TRADING EXECUTION

set -euo pipefail

export TZ="${TZ:-America/New_York}"
export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"
export KMIA_PYTHON=/opt/kmia-venv/bin/python3

KALSHI="${KMIA_KALSHI_ROOT:-/data/Kalshi}"
LOG_DIR="${NAS_ORDERBOOK_WS_LOG_DIR:-/data/logs/orderbook_ws}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/orderbook_ws_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NAS orderbook WebSocket daemon $STAMP ==="
echo "KALSHI=$KALSHI"

if [ ! -d "$KALSHI/backend/src" ] || [ ! -f "$KALSHI/scripts/run_orderbook_ws_daemon.sh" ]; then
  echo "ERROR: Kalshi runtime missing — run deploy_kalshi_runtime_to_nas.sh from Mac"
  exit 1
fi

# shellcheck disable=SC1091
source /usr/local/bin/load_kalshi_api_env_nas.sh

export KMIA_KALSHI_ROOT="$KALSHI"
export KALSHI_PROCESSED_DIR="${KALSHI_PROCESSED_DIR:-$KALSHI/backend/data/processed}"
export KALSHI_MARKET_ARCHIVE_DIR="${KALSHI_MARKET_ARCHIVE_DIR:-$KALSHI_PROCESSED_DIR/kalshi_market_archive}"
export KALSHI_WS_ENABLED="${KALSHI_WS_ENABLED:-true}"
export KALSHI_WS_SNAPSHOT_INTERVAL_SEC="${KALSHI_WS_SNAPSHOT_INTERVAL_SEC:-60}"
export KALSHI_WS_ARCHIVE_RAW_DELTAS="${KALSHI_WS_ARCHIVE_RAW_DELTAS:-true}"

cd "$KALSHI"
exec bash scripts/run_orderbook_ws_daemon.sh
