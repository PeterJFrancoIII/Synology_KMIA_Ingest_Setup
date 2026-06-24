#!/bin/bash
# Daily policy sweep + export draft trading_policy.json (Console 2 → Console 3)
# NO REAL TRADING EXECUTION
#
# Run on Legion5 (54_kalshi_ndfd_research_pipeline.sh) or NAS (run_nas_policy_pipeline.sh).
# Mac = deploy only — set ALLOW_MAC_POLICY_REFRESH=1 to override (not recommended).
#
# Do NOT call kalshi_policy_optimizer.py or historical_checksum_backtest.py directly on Mac.
# Legion5 canonical entry: bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh
# See docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md § Compute routing.

set -euo pipefail

if [[ "$(uname -s)" == Darwin ]] && [[ "${ALLOW_MAC_POLICY_REFRESH:-0}" != "1" ]]; then
  echo "ERROR: run_daily_policy_refresh.sh must not run on Mac." >&2
  echo "  Legion5: bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh" >&2
  echo "  NAS:     sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh" >&2
  exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
export CONSOLE2_ROOT="${CONSOLE2_ROOT:-$REPO_ROOT}"

source "${SCRIPT_DIR}/kmia_kalshi_env.sh" 2>/dev/null || true

# Optional: Kalshi API (same folder as Kalshi repo API Keys)
_KALSHI_LOAD="${KMIA_KALSHI_ROOT:-$HOME/Desktop/App Development/Kalshi}/scripts/load_kalshi_api_env.sh"
if [ -f "$_KALSHI_LOAD" ]; then
  # shellcheck disable=SC1090
  source "$_KALSHI_LOAD" 2>/dev/null || true
fi

PRICE_DIR="${KALSHI_PRICE_DIR:-$(python3 -c 'from kmia_kalshi_paths import kalshi_price_history_dir; print(kalshi_price_history_dir())')}"
BACKTEST_DIR="${CONSOLE2_BACKTEST_DIR:-$REPO_ROOT/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest}"
KALSHI_RESEARCH="${KALSHI_RESEARCH_DIR:-$(python3 -c 'from kmia_kalshi_paths import kalshi_research_dir; print(kalshi_research_dir())')}"
OB_ARCHIVE="${KALSHI_MARKET_ARCHIVE_DIR:-$(python3 -c 'from kmia_kalshi_paths import kalshi_market_archive_dir; print(kalshi_market_archive_dir())')}"
CANDLE_ARCHIVE="${KALSHI_CANDLE_ARCHIVE_DIR:-$(python3 -c 'from kmia_kalshi_paths import kalshi_candle_archive_dir; print(kalshi_candle_archive_dir())')}"

NCEI_END="${NCEI_REFRESH_END_DATE:-$(date +%Y-%m-%d)}"
NCEI_START="${NCEI_REFRESH_START_DATE:-2026-04-20}"

export PYTHONPATH="${REPO_ROOT}/ingest/scripts:${PYTHONPATH:-}"
POLICY_WORKERS="${POLICY_SWEEP_WORKERS:-$(python3 -c 'from kalshi_policy_optimizer import default_workers; print(default_workers())')}"

echo "[0/8] Ingest new Kalshi price-history CSVs from API..."
python3 ingest/scripts/ingest_kalshi_market_data.py --output-dir "$PRICE_DIR"

echo "[0b/8] Archive full candlestick JSONL (bid/ask/volume)..."
python3 ingest/scripts/kalshi_candle_archive.py --archive-dir "$CANDLE_ARCHIVE" || {
  echo "WARN: candle archive step failed (non-fatal)"
}

echo "[0c/8] Archive coverage status..."
python3 ingest/scripts/kalshi_archive_status.py \
  --price-history-dir "$PRICE_DIR" \
  --orderbook-archive-dir "$OB_ARCHIVE" \
  --candle-archive-dir "$CANDLE_ARCHIVE" || true

echo "[1/8] Refresh official NCEI CLIMIA TMAX ($NCEI_START → $NCEI_END)..."
python3 ingest/scripts/refresh_kmia_ncei_climatology.py \
  --start-date "$NCEI_START" --end-date "$NCEI_END"

echo "[1b/8] Quarantine NWS snapshots not on canonical KMIA grid (MFL/105,51)..."
python3 ingest/scripts/quarantine_mismatched_nws_snapshots.py || true

echo "[1c/8] Backfill aligned NWS history from NDFD point extract (MapClick pin)..."
PYTHONPATH="${REPO_ROOT}/ingest/scripts:${PYTHONPATH:-}" python3 ingest/scripts/backfill_nws_snapshots_from_ndfd.py \
  --merge-monthly \
  --price-history-dir "$PRICE_DIR" \
  --replace-iem || {
  echo "WARN: NDFD NWS backfill skipped or partial (run Legion5 52_kalshi_ndfd_anchor_backfill.sh)"
}

echo "[2/8] Weather coverage scorecard..."
python3 ingest/scripts/kalshi_weather_coverage_scorecard.py

echo "[3b/8] Probability model parity check (gaussian vs integer_dist)..."
python3 ingest/scripts/compare_prob_models.py \
  --price-history-dir "$PRICE_DIR" \
  --output "$BACKTEST_DIR/prob_model_comparison.json" || {
  echo "WARN: prob model comparison failed (non-fatal)"
}

if [ "${SKIP_POLICY_SWEEP:-0}" = "1" ]; then
  echo "[4-8/8] SKIP_POLICY_SWEEP=1 — ingest-only; Legion5 owns backtest/sweep (weekly task)."
  echo "Daily policy refresh (ingest-only) complete."
  exit 0
fi

echo "[4/8] Kalshi price backtest (taker — matches paper execution)..."
python3 ingest/scripts/historical_checksum_backtest.py \
  --mode kalshi \
  --order-mode taker \
  --price-history-dir "$PRICE_DIR" \
  --orderbook-archive-dir "$OB_ARCHIVE" \
  --candle-archive-dir "$CANDLE_ARCHIVE" \
  --output-dir "$BACKTEST_DIR"

echo "[5/8] Policy optimizer sweep (${POLICY_WORKERS} workers, taker)..."
python3 ingest/scripts/kalshi_policy_optimizer.py \
  --price-history-dir "$PRICE_DIR" \
  --orderbook-archive-dir "$OB_ARCHIVE" \
  --candle-archive-dir "$CANDLE_ARCHIVE" \
  --output-dir "$BACKTEST_DIR" \
  --workers "$POLICY_WORKERS" \
  --order-mode taker

echo "[6/8] Export trading_policy draft..."
python3 ingest/scripts/export_trading_policy.py \
  --backtest-dir "$BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH" \
  --order-mode taker \
  --no-copy

echo "[7/8] Dual-mode comparison (taker primary + maker reference)..."
python3 ingest/scripts/historical_checksum_backtest.py \
  --mode kalshi \
  --price-history-dir "$PRICE_DIR" \
  --orderbook-archive-dir "$OB_ARCHIVE" \
  --candle-archive-dir "$CANDLE_ARCHIVE" \
  --output-dir "$BACKTEST_DIR" \
  --dual-report

echo "[8/8] Trading bridge refresh (frontier + pipeline status)..."
bash ingest/scripts/refresh_trading_bridge.sh || echo "WARN: bridge refresh partial failure"

echo "Daily policy refresh complete. Review trading_policy_draft.json before approving."
