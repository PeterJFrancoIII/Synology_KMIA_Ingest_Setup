#!/bin/bash
# Deploy Kalshi Console 3 runtime (paper loop) to NAS.
# Mac = deploy only; execution runs on kmia-paper-research container.
#
# Usage:
#   NAS_HOST=MediaServer2Local ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
#   NAS_HOST=MediaServer2Local ./synology/scripts/deploy_kalshi_runtime_to_nas.sh --with-data

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2Local}"
KALSHI_LOCAL="${KALSHI_LOCAL:-$HOME/Desktop/App Development/Kalshi}"
NAS_KALSHI="App Development/Kalshi"
WITH_DATA=0
for arg in "$@"; do
  case "$arg" in
    --with-data) WITH_DATA=1 ;;
  esac
done

_tar_to_nas() {
  local dest="$1"
  shift
  tar cf - "$@" | ssh "$NAS" "mkdir -p '$dest' && cd '$dest' && tar xf -"
}

echo "=== Deploy Kalshi runtime to $NAS ==="

echo "[1/4] backend/src + scripts..."
_tar_to_nas "$NAS_KALSHI" \
  -C "$KALSHI_LOCAL" backend/src scripts

echo "[2/4] Ensure processed data dirs..."
ssh "$NAS" "mkdir -p \
  '$NAS_KALSHI/backend/data/processed/kalshi_market_snapshots' \
  '$NAS_KALSHI/backend/data/processed/kalshi_market_archive' \
  '$NAS_KALSHI/backend/data/processed/kalshi_candle_archive' \
  '$NAS_KALSHI/backend/data/processed/weather_nws' \
  '$NAS_KALSHI/backend/data/processed/reports' \
  '$NAS_KALSHI/backend/data/processed/paper_trading' \
  '$NAS_KALSHI/backend/data/processed/status' \
  '$NAS_KALSHI/backend/data/processed/history' \
  '$NAS_KALSHI/backend/data/processed/mae' \
  '$NAS_KALSHI/backend/data/research' \
  'App Development/logs/paper_trading'"

if [ "$WITH_DATA" -eq 1 ]; then
  echo "[2b/4] Sync Mac processed data (ledger, history, snapshots)..."
  _tar_to_nas "$NAS_KALSHI/backend/data" \
    -C "$KALSHI_LOCAL/backend/data" processed
fi

echo "[3/4] Copy to canonical volume2 (sudo)..."
ssh "$NAS" "sudo cp -R '$NAS_KALSHI/backend' /volume2/Data/App_Development/Kalshi/ 2>/dev/null && \
  sudo cp -R '$NAS_KALSHI/scripts' /volume2/Data/App_Development/Kalshi/ 2>/dev/null && \
  echo CANONICAL_OK || echo WARN: canonical copy skipped"

echo "[4/4] chmod scripts..."
ssh "$NAS" "chmod +x '$NAS_KALSHI/scripts/'*.sh 2>/dev/null || true"

cat <<EOF

Kalshi runtime deployed to NAS.

Smoke paper loop:
  ssh $NAS
  sudo docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh

Schedule (DSM Task Scheduler): synology/scripts/90_cron_install.sh
  */15 * * * * paper loop
  15 18 * * *   policy research

Mac should NOT run launchd paper loop — deploy only.

EOF
