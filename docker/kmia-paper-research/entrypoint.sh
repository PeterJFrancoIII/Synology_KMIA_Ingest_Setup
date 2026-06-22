#!/bin/bash
set -euo pipefail

export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

# Lightweight startup guard — verify /data mount exists (same pattern as kmia-arch-ingest).
if [ ! -d /data/KMIA_Ingest ] && [ ! -d /data/Kalshi ]; then
  echo "ERROR: /data not mounted. Ensure /volume2/Data/App_Development is mounted at /data."
  exit 1
fi

# Optional secrets (Kalshi API) — never commit this file.
if [ -f /data/secrets/kmia_paper_research.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /data/secrets/kmia_paper_research.env
  set +a
fi

exec "$@"
