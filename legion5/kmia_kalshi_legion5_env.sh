#!/usr/bin/env bash
# Kalshi + Console 2 research paths on Legion5 — all data via NAS SMB (Z:).
# Source after kmia_legion5_env.sh. Mac must NOT run research pipelines.
#
# Requires: Z: mounted (43_setup_nas_smb.ps1)

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/kmia_legion5_env.sh"

_drive="${NAS_SMB_DRIVE:-Z:}"
# Read-only NAS share (kmia_legion5 user)
export KMIA_KALSHI_READ_ROOT="${KMIA_KALSHI_READ_ROOT:-${_drive}/App_Development/Kalshi}"
# Writable Legion5 mirror — sync to NAS via 55_sync_kalshi_mirror_to_nas.ps1 or NAS docker pipeline
export KMIA_KALSHI_WRITE_ROOT="${KMIA_KALSHI_WRITE_ROOT:-${KMIA_ROOT:-/d/KMIA_Process}/kalshi_mirror}"
export KMIA_KALSHI_ROOT="${KMIA_KALSHI_ROOT:-$KMIA_KALSHI_WRITE_ROOT}"
export CONSOLE2_ROOT="${CONSOLE2_ROOT:-${KMIA_ROOT:-/d/KMIA_Process}}"
export KALSHI_PRICE_DIR="${KALSHI_PRICE_DIR:-$KMIA_KALSHI_READ_ROOT/Kalshi - Miami Max Temp. Bet History}"
export KALSHI_PROCESSED_DIR="${KALSHI_PROCESSED_DIR:-$KMIA_KALSHI_WRITE_ROOT/backend/data/processed}"
export KALSHI_RESEARCH_DIR="${KALSHI_RESEARCH_DIR:-$KMIA_KALSHI_WRITE_ROOT/backend/data/research}"
export KALSHI_MARKET_ARCHIVE_DIR="${KALSHI_MARKET_ARCHIVE_DIR:-$KMIA_KALSHI_READ_ROOT/backend/data/processed/kalshi_market_archive}"
export KALSHI_CANDLE_ARCHIVE_DIR="${KALSHI_CANDLE_ARCHIVE_DIR:-$KMIA_KALSHI_READ_ROOT/backend/data/processed/kalshi_candle_archive}"
export KALSHI_NWS_DIR="${KALSHI_NWS_DIR:-$KALSHI_PROCESSED_DIR/weather_nws}"
export KALSHI_OBSERVED_JSONL="${KALSHI_OBSERVED_JSONL:-$KMIA_KALSHI_READ_ROOT/backend/data/processed/weather_nws/nws_observed_history.jsonl}"
export KMIA_DAILY_HISTORY_JSONL="${KMIA_DAILY_HISTORY_JSONL:-$KMIA_KALSHI_READ_ROOT/backend/data/processed/history/kmia_daily_history.jsonl}"
export NCEI_CLIMATOLOGY_TXT="${NCEI_CLIMATOLOGY_TXT:-$KMIA_KALSHI_READ_ROOT/1948-2026_Climatological_Report_USW00012839_MIAMI_INTERNATIONAL_AIRPORT_.txt}"
export CONSOLE2_BACKTEST_DIR="${CONSOLE2_BACKTEST_DIR:-$CONSOLE2_ROOT/analysis/Kalshi_Price_Backtest}"
export NDFD_KALSHI_MAXT_CSV="${NDFD_KALSHI_MAXT_CSV:-$CONSOLE2_ROOT/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv}"
export POLICY_SWEEP_WORKERS="${POLICY_SWEEP_WORKERS:-8}"
export KALSHI_BACKTEST_PROB_MODEL="${KALSHI_BACKTEST_PROB_MODEL:-integer_dist_v1}"
export KALSHI_POLICY_SELECTION="${KALSHI_POLICY_SELECTION:-max_roi}"
export PYTHONPATH="${SCRIPTS:-$CONSOLE2_ROOT/scripts}:${PYTHONPATH:-}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

if [ ! -d "$KMIA_KALSHI_READ_ROOT" ]; then
  echo "[kmia_kalshi_legion5] WARN: Kalshi read root missing ($KMIA_KALSHI_READ_ROOT) — mount Z:" >&2
fi
mkdir -p "$KALSHI_PROCESSED_DIR/weather_nws" "$KALSHI_RESEARCH_DIR" "$CONSOLE2_BACKTEST_DIR"
