#!/bin/bash
# Deploy Console 2 policy research scripts to NAS (same tree as kmia-arch-ingest).
# Uses tar-over-SSH (Synology disables scp subsystem).
#
# Usage:
#   ./synology/scripts/deploy_paper_research_to_nas.sh
#   ./synology/scripts/deploy_paper_research_to_nas.sh --kalshi-src

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2}"
CONSOLE2_LOCAL="$(cd "$(dirname "$0")/../.." && pwd)"
KALSHI_LOCAL="${KALSHI_LOCAL:-$HOME/Desktop/App Development/Kalshi}"

# Canonical NAS paths (match kmia-arch-ingest runbook)
NAS_SETUP="App Development/Synology_KMIA_Ingest_Setup"
NAS_CANONICAL="/volume2/Data/App_Development"

DO_KALSHI_SRC=0
for arg in "$@"; do
  case "$arg" in
    --kalshi-src) DO_KALSHI_SRC=1 ;;
  esac
done

_tar_to_nas() {
  local dest="$1"
  shift
  tar cf - "$@" | ssh "$NAS" "mkdir -p '$dest' && cd '$dest' && tar xf -"
}

echo "=== Deploy kmia-paper-research (Arch) to $NAS ==="
echo "Console2: $CONSOLE2_LOCAL"

if [ ! -d "$KALSHI_LOCAL/backend/src" ]; then
  echo "ERROR: Kalshi repo not found at $KALSHI_LOCAL"
  exit 1
fi

echo "[1/4] Console 2 ingest scripts + docker/kmia-paper-research..."
_tar_to_nas "$NAS_SETUP" \
  -C "$CONSOLE2_LOCAL" ingest/scripts docker/kmia-paper-research

echo "[2/4] Research artifacts (backtest dir + enriched CSV if present)..."
_tar_to_nas "$NAS_SETUP/Research/Agent Analysis of KMIA Forecast Precision" \
  -C "$CONSOLE2_LOCAL/Research/Agent Analysis of KMIA Forecast Precision" \
  Kalshi_Price_Backtest \
  2>/dev/null || true

if [ -f "$CONSOLE2_LOCAL/Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv" ]; then
  _tar_to_nas "$NAS_SETUP/Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_AllYears_MaxT_Precision" \
    -C "$CONSOLE2_LOCAL/Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_AllYears_MaxT_Precision" \
    accuracy_points_enriched.csv
fi

echo "[3/4] Kalshi build_mae_priors.py..."
ssh "$NAS" "mkdir -p 'App Development/Kalshi/scripts'"
_tar_to_nas "App Development/Kalshi/scripts" \
  -C "$KALSHI_LOCAL/scripts" build_mae_priors.py

if [ "$DO_KALSHI_SRC" -eq 1 ]; then
  echo "[3b/4] Kalshi backend/src..."
  _tar_to_nas "App Development/Kalshi/backend" \
    -C "$KALSHI_LOCAL/backend" src
fi

echo "[4/4] Install into canonical NAS locations (if writable)..."
ssh "$NAS" "chmod +x '$NAS_SETUP/ingest/scripts/'*.sh '$NAS_SETUP/docker/kmia-paper-research/'*.sh 2>/dev/null || true; \
  mkdir -p '$NAS_CANONICAL/KMIA_Ingest/setup_repo' \
           '$NAS_CANONICAL/Kalshi/scripts' \
           '$NAS_CANONICAL/Docker/kmia-paper-research' \
           '$NAS_CANONICAL/logs/paper_research' \
           '$NAS_CANONICAL/secrets' 2>/dev/null || \
  mkdir -p 'App Development/logs/paper_research' 'App Development/secrets'"

# Best-effort copy to canonical tree (may fail if SSH user lacks volume2 write — use DSM File Station)
ssh "$NAS" "
  if [ -w '$NAS_CANONICAL/KMIA_Ingest/setup_repo' ] 2>/dev/null; then
    cp -R '$NAS_SETUP'/ingest '$NAS_CANONICAL/KMIA_Ingest/setup_repo/' 2>/dev/null || true
    cp -R '$NAS_SETUP'/docker/kmia-paper-research/* '$NAS_CANONICAL/Docker/kmia-paper-research/' 2>/dev/null || true
    cp -R '$NAS_SETUP'/Research '$NAS_CANONICAL/KMIA_Ingest/setup_repo/' 2>/dev/null || true
    cp 'App Development/Kalshi/scripts/build_mae_priors.py' '$NAS_CANONICAL/Kalshi/scripts/' 2>/dev/null || true
    echo 'Canonical copy OK'
  else
    echo 'WARN: no write to $NAS_CANONICAL — copy setup_repo via DSM to KMIA_Ingest/setup_repo'
  fi
" || true

cat <<EOF

Deploy complete.

Build Arch container (same pattern as kmia-arch-ingest):
  ssh $NAS
  cp -R '$NAS_SETUP'/docker/kmia-paper-research/* $NAS_CANONICAL/Docker/kmia-paper-research/
  cd $NAS_CANONICAL/Docker/kmia-paper-research
  sudo docker compose build && sudo docker compose up -d

Smoke + manual run:
  sudo docker exec kmia-paper-research /usr/local/bin/smoke_container.sh
  sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh

Schedule: synology/scripts/90_cron_install.sh (DSM Task Scheduler)

EOF
