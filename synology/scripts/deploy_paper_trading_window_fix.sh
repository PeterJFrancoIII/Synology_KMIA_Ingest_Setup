#!/bin/bash
# Deploy dynamic paper trading window + maker_limit parity to NAS (run from Mac on LAN).
# Updates launcher in container, secrets env, and Kalshi runtime modules.
#
# Usage:
#   NAS_HOST=MediaServer2 ./synology/scripts/deploy_paper_trading_window_fix.sh

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
KALSHI="${KALSHI_LOCAL:-$HOME/Desktop/App Development/Kalshi}"
DOCKER="/var/packages/ContainerManager/target/usr/bin/docker"
LAUNCHER_SRC="$REPO/docker/kmia-paper-research/run_nas_paper_loop.sh"
PRIORS_SRC="$REPO/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest/expected_max_hour_priors.json"
NAS_KALSHI="/volume2/Data/App_Development/Kalshi"

_tee_to_nas() {
  local dest="$1"
  shift
  cat "$@" | ssh "$NAS" "sudo tee '$dest' > /dev/null"
}

echo "=== Deploy paper trading window + maker fix → $NAS ==="

if [ ! -f "$LAUNCHER_SRC" ]; then
  echo "ERROR: missing $LAUNCHER_SRC" >&2
  exit 1
fi

echo "[1/7] Patch NAS secrets (dynamic window + maker_limit)..."
ssh "$NAS" "sudo bash -s" <<'REMOTE'
set -euo pipefail
ENV="/volume2/Data/App_Development/secrets/kmia_paper_research.env"
_patch_kv() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV" 2>/dev/null; then
    sed -i "s/^${key}=.*/${key}=${val}/" "$ENV"
  else
    echo "${key}=${val}" >> "$ENV"
  fi
}
if [ ! -f "$ENV" ]; then
  echo "WARN: $ENV missing — create from kmia_paper_research.env.example"
else
  _patch_kv PAPER_LOOP_ANCHOR_ONLY 0
  _patch_kv PAPER_TRADING_WINDOW dynamic
  _patch_kv PAPER_ORDER_MODE maker_limit
  _patch_kv KALSHI_BACKTEST_ORDER_MODE maker_limit
  _patch_kv KALSHI_BACKTEST_PROB_MODEL integer_dist_v1
  echo "secrets ok:"
  grep -E '^(PAPER_|KALSHI_BACKTEST_)' "$ENV" || true
fi
REMOTE

echo "[2/7] Copy run_nas_paper_loop.sh into kmia-paper-research container (tee, not scp)..."
_tee_to_nas /tmp/run_nas_paper_loop.sh "$LAUNCHER_SRC"
ssh "$NAS" "sudo $DOCKER cp /tmp/run_nas_paper_loop.sh kmia-paper-research:/usr/local/bin/run_nas_paper_loop.sh && \
  sudo $DOCKER exec kmia-paper-research chmod +x /usr/local/bin/run_nas_paper_loop.sh"

echo "[3/7] Deploy Kalshi paper_trading modules..."
for rel in \
  paper_trading/trading_window.py \
  paper_trading/paper_resilience_gates.py \
  paper_trading/settlement_labels.py; do
  if [ -f "$KALSHI/backend/src/$rel" ]; then
    _tee_to_nas "$NAS_KALSHI/backend/src/$rel" "$KALSHI/backend/src/$rel"
    echo "  deployed $rel"
  else
    echo "  WARN: missing $KALSHI/backend/src/$rel" >&2
  fi
done

echo "[4/7] Deploy expected_max_hour_priors.json..."
if [ -f "$PRIORS_SRC" ]; then
  _tee_to_nas "$NAS_KALSHI/backend/data/research/expected_max_hour_priors.json" "$PRIORS_SRC"
else
  echo "  WARN: priors missing at $PRIORS_SRC" >&2
fi

echo "[5/7] Smoke-run paper loop once..."
ssh "$NAS" "sudo $DOCKER exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh" | tail -20

echo "[6/7] Health watch..."
NAS_HOST="$NAS" "$REPO/ingest/scripts/kmia_paper_ops_watch.sh" | tail -25

echo "[7/7] Reminder: rebuild image to persist launcher across container recreate:"
echo "  ssh $NAS 'cd /volume2/Data/App_Development/Docker/kmia-paper-research && sudo docker compose build kmia-paper-research && sudo docker compose up -d kmia-paper-research'"

echo "=== Deploy complete ==="
