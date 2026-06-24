#!/bin/bash
# NAS daily pipeline: MAE priors sync + Kalshi policy refresh (Console 2 → shared Kalshi data)
# NO REAL TRADING EXECUTION

set -euo pipefail

export TZ="${TZ:-America/New_York}"
export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

CONSOLE2="${CONSOLE2_ROOT:-/data/KMIA_Ingest/setup_repo}"
KALSHI="${KMIA_KALSHI_ROOT:-/data/Kalshi}"
LOG_DIR="${NAS_POLICY_LOG_DIR:-/data/logs/paper_research}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/nas_policy_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NAS policy pipeline $STAMP ==="
echo "CONSOLE2=$CONSOLE2"
echo "KALSHI=$KALSHI"

export CONSOLE2_ROOT="$CONSOLE2"
export KMIA_KALSHI_ROOT="$KALSHI"
export KALSHI_PRICE_DIR="${KALSHI_PRICE_DIR:-$KALSHI/Kalshi - Miami Max Temp. Bet History}"
export KALSHI_PROCESSED_DIR="${KALSHI_PROCESSED_DIR:-$KALSHI/backend/data/processed}"
export KALSHI_RESEARCH_DIR="${KALSHI_RESEARCH_DIR:-$KALSHI/backend/data/research}"
export PYTHONPATH="$CONSOLE2/ingest/scripts:$KALSHI/backend/src"
export POLICY_SWEEP_WORKERS="${POLICY_SWEEP_WORKERS:-2}"
export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
# Legion5 weekly task owns backtest/sweep; NAS daily = ingest + NCEI + coverage only.
export SKIP_POLICY_SWEEP="${SKIP_POLICY_SWEEP:-1}"

if [ ! -d "$CONSOLE2/ingest/scripts" ]; then
  echo "ERROR: Console2 scripts missing at $CONSOLE2/ingest/scripts"
  echo "Deploy setup_repo to /volume2/Data/App_Development/KMIA_Ingest/setup_repo"
  exit 1
fi

echo "[A1/2] Build MAE priors from Console 2 enriched CSV..."
CSV="${CONSOLE2_ENRICHED_CSV:-$CONSOLE2/Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv}"
MAE_OUT="${MAE_PRIORS_FILE:-$KALSHI/backend/data/processed/mae/mae_priors.json}"
if [ ! -f "$CSV" ]; then
  echo "WARN: enriched CSV not found ($CSV) — skipping MAE priors"
else
  mkdir -p "$(dirname "$MAE_OUT")"
  if [ -f "$KALSHI/scripts/build_mae_priors.py" ]; then
    python "$KALSHI/scripts/build_mae_priors.py" --csv "$CSV" --out "$MAE_OUT" || {
      echo "WARN: build_mae_priors failed"
    }
  else
    echo "WARN: $KALSHI/scripts/build_mae_priors.py missing"
  fi
fi

echo "[A2/2] Daily policy refresh (backtest + export draft)..."
bash "$CONSOLE2/ingest/scripts/run_daily_policy_refresh.sh"

echo "=== NAS policy pipeline complete ==="
