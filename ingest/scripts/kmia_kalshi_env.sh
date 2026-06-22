# Source from NAS container or Legion5 before policy refresh — NOT on Mac (deploy only).
# Optional: place overrides at /volume2/Data/App_Development/secrets/kmia_paper_research.env

: "${CONSOLE2_ROOT:=/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup}"
: "${KMIA_KALSHI_ROOT:=/Users/computer/Desktop/App Development/Kalshi}"

export CONSOLE2_ROOT
export KMIA_KALSHI_ROOT
export KALSHI_PRICE_DIR="${KALSHI_PRICE_DIR:-$KMIA_KALSHI_ROOT/Kalshi - Miami Max Temp. Bet History}"
export KALSHI_PROCESSED_DIR="${KALSHI_PROCESSED_DIR:-$KMIA_KALSHI_ROOT/backend/data/processed}"
export KALSHI_RESEARCH_DIR="${KALSHI_RESEARCH_DIR:-$KMIA_KALSHI_ROOT/backend/data/research}"
export KALSHI_MARKET_ARCHIVE_DIR="${KALSHI_MARKET_ARCHIVE_DIR:-$KALSHI_PROCESSED_DIR/kalshi_market_archive}"
export KALSHI_CANDLE_ARCHIVE_DIR="${KALSHI_CANDLE_ARCHIVE_DIR:-$KALSHI_PROCESSED_DIR/kalshi_candle_archive}"
export CONSOLE2_BACKTEST_DIR="${CONSOLE2_BACKTEST_DIR:-$CONSOLE2_ROOT/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest}"
# Align backtest P(bin) with live paper loop (parity verified via compare_prob_models.py)
export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
export PYTHONPATH="${CONSOLE2_ROOT}/ingest/scripts:${PYTHONPATH:-}"
