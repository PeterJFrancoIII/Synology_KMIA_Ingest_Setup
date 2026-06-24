#!/bin/bash
# NAS weekly forward paper scorecard (read-only).
# NO REAL TRADING EXECUTION

set -euo pipefail

export TZ="${TZ:-America/New_York}"
export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

KALSHI="${KMIA_KALSHI_ROOT:-/data/Kalshi}"
LOG_DIR="${NAS_PAPER_LOG_DIR:-/data/logs/paper_trading}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/paper_scorecard_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NAS paper forward scorecard $STAMP ==="

export PYTHONPATH="$KALSHI/backend/src"
python3 "$KALSHI/scripts/paper_forward_scorecard.py"

echo "=== scorecard complete ==="
