#!/bin/bash
set -euo pipefail

export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

# Lightweight startup guard — verify /data mount exists.
if [ ! -d /data/KMIA_Ingest ]; then
  echo "ERROR: /data/KMIA_Ingest not found. Ensure /volume2/Data/App_Development is mounted at /data."
  exit 1
fi

exec "$@"
