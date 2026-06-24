#!/bin/bash
# Deploy Kalshi Console 3 runtime (paper loop) to NAS.
# Mac = deploy only; execution runs on kmia-paper-research container.
#
# Canonical deploy after any Kalshi backend/src or scripts change (replaces piecemeal hot-patches).
#
# Usage:
#   NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
#   NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh --with-data

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2}"
KALSHI_LOCAL="${KALSHI_LOCAL:-$HOME/Desktop/App Development/Kalshi}"
NAS_CANONICAL="/volume2/Data/App_Development/Kalshi"
WITH_DATA=0
for arg in "$@"; do
  case "$arg" in
    --with-data) WITH_DATA=1 ;;
  esac
done

_tar_to_nas_canonical() {
  tar cf - "$@" | ssh "$NAS" "sudo tar xf - -C '$NAS_CANONICAL'"
}

echo "=== Deploy Kalshi runtime to $NAS ==="

echo "[1/4] backend/src + scripts → $NAS_CANONICAL..."
_tar_to_nas_canonical -C "$KALSHI_LOCAL" backend/src scripts

echo "[2/4] Ensure processed data dirs..."
ssh "$NAS" "sudo mkdir -p \
  '$NAS_CANONICAL/backend/data/processed/kalshi_market_snapshots' \
  '$NAS_CANONICAL/backend/data/processed/kalshi_market_archive/orderbooks' \
  '$NAS_CANONICAL/backend/data/processed/kalshi_market_archive/orderbook_ws' \
  '$NAS_CANONICAL/backend/data/processed/kalshi_market_archive/orderbook_ws_snapshots' \
  '$NAS_CANONICAL/backend/data/processed/kalshi_market_archive/markets' \
  '$NAS_CANONICAL/backend/data/processed/kalshi_candle_archive' \
  '$NAS_CANONICAL/backend/data/processed/weather_nws' \
  '$NAS_CANONICAL/backend/data/processed/reports' \
  '$NAS_CANONICAL/backend/data/processed/paper_trading' \
  '$NAS_CANONICAL/backend/data/processed/status' \
  '$NAS_CANONICAL/backend/data/processed/history' \
  '$NAS_CANONICAL/backend/data/processed/mae' \
  '$NAS_CANONICAL/backend/data/research' \
  '/volume2/Data/App_Development/logs/paper_trading' \
  '/volume2/Data/App_Development/logs/orderbook_ws'"

if [ "$WITH_DATA" -eq 1 ]; then
  echo "[2b/4] Sync Mac processed data (ledger, history, snapshots)..."
  tar cf - -C "$KALSHI_LOCAL/backend/data" processed | \
    ssh "$NAS" "sudo tar xf - -C '$NAS_CANONICAL/backend/data'"
fi

echo "[3/4] chmod scripts..."
ssh "$NAS" "sudo chmod +x '$NAS_CANONICAL/scripts/'*.sh 2>/dev/null || true"

echo "[4/4] verify run_orderbook_ws_daemon.sh..."
ssh "$NAS" "sudo test -x '$NAS_CANONICAL/scripts/run_orderbook_ws_daemon.sh' && echo OK || echo MISSING"

cat <<EOF

Kalshi runtime deployed to NAS.

Smoke paper loop:
  ssh $NAS
  sudo docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh

WebSocket orderbook daemon:
  cd /volume2/Data/App_Development/Docker/kmia-paper-research
  sudo /var/packages/ContainerManager/target/usr/bin/docker compose up -d kmia-orderbook-ws
  sudo /var/packages/ContainerManager/target/usr/bin/docker logs -f kmia-orderbook-ws

Schedule (DSM Task Scheduler): synology/scripts/90_cron_install.sh
  */5 * * * * paper loop
  15 18 * * *   policy research

Mac should NOT run launchd paper loop — deploy only.

EOF
