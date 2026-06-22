#!/usr/bin/env bash
# Merge Kalshi NDFD VALID_ONLY monthly CSVs on Legion5 (Git Bash).
set -euo pipefail
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export PYTHONPATH="$SCRIPTS:${PYTHONPATH:-}"

YEAR="${1:-2026}"
MERGED="${2:-$ROOT/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv}"
ROOTS="$ROOT/processed/points/station=KMIA/monthly/${YEAR}"

echo "[52c] merge ${ROOTS} -> ${MERGED}"
"$PYTHON" "$SCRIPTS/ndfd_kalshi_forecast.py" merge --roots "$ROOTS" --output "$MERGED"
