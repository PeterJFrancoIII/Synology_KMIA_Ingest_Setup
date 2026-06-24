#!/usr/bin/env bash
# Legion5 daily: NBM archive, Kalshi price ingest, NCEI refresh, mirror → NAS sync.
# NO REAL TRADING EXECUTION
#
# Usage:
#   bash D:/KMIA_Process/scripts/55_daily_kalshi_research.sh
#   SKIP_NAS_SYNC=1 bash ...   # local only

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_kalshi_legion5_env.sh
source "$SCRIPTS/kmia_kalshi_legion5_env.sh"

LOG_DIR="$ROOT/logs/research"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/kalshi_daily_$(date +%Y%m%dT%H%M%SZ).log"

log() { echo "[kalshi_daily] $*" | tee -a "$LOG"; }

mount_z_read() {
  if [ -d "$KMIA_KALSHI_READ_ROOT" ]; then
    return 0
  fi
  log "Mounting Z: (read) via 43_setup_nas_smb.ps1…"
  if [ -f "$ROOT/secrets/nas_smb_password" ] && [ -f "$SCRIPTS/43_setup_nas_smb.ps1" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || true
  fi
}

# Writable mirror paths (Z: kmia_legion5 is read-only)
WRITABLE_PRICE="${KALSHI_PRICE_WRITE_DIR:-$KMIA_KALSHI_WRITE_ROOT/Kalshi - Miami Max Temp. Bet History}"
WRITABLE_CANDLE="${KALSHI_CANDLE_WRITE_DIR:-$KMIA_KALSHI_WRITE_ROOT/backend/data/processed/kalshi_candle_archive}"
mkdir -p "$WRITABLE_PRICE" "$WRITABLE_CANDLE" "$KALSHI_PROCESSED_DIR/history"
export KMIA_DAILY_HISTORY_JSONL="$KALSHI_PROCESSED_DIR/history/kmia_daily_history.jsonl"

mount_y_write() {
  if [ "${SKIP_NAS_SYNC:-0}" = "1" ]; then
    return 0
  fi
  log "Mounting Y: (write) via 43b_setup_nas_smb_write.ps1…"
  if [ -f "$SCRIPTS/43b_setup_nas_smb_write.ps1" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43b_setup_nas_smb_write.ps1" >>"$LOG" 2>&1 || true
  fi
}

sync_mirror_to_nas() {
  if [ "${SKIP_NAS_SYNC:-0}" = "1" ]; then
    log "SKIP_NAS_SYNC=1 — skipping robocopy"
    return 0
  fi
  if [ -f "$SCRIPTS/55_sync_research_to_nas.ps1" ]; then
    log "Syncing research artifacts → NAS…"
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/55_sync_research_to_nas.ps1" >>"$LOG" 2>&1 \
      || log "WARN: research NAS sync failed (non-fatal)"
  elif [ -f "$SCRIPTS/55_sync_kalshi_mirror_to_nas.ps1" ]; then
    log "Syncing kalshi_mirror → NAS…"
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/55_sync_kalshi_mirror_to_nas.ps1" >>"$LOG" 2>&1 \
      || log "WARN: NAS sync failed (non-fatal)"
  fi
}

copy_research_artifacts() {
  local bt="$CONSOLE2_BACKTEST_DIR"
  local rd="$KALSHI_RESEARCH_DIR"
  mkdir -p "$rd/calibration"
  for f in \
    expected_max_hour_priors.json \
    bin_isotonic_v1.json \
    nbm_maxt_archive.jsonl \
    nbm_validation_report.json; do
    if [ -f "$bt/$f" ]; then
      if [ "$f" = "bin_isotonic_v1.json" ]; then
        cp -f "$bt/$f" "$rd/calibration/$f" 2>/dev/null || true
      else
        cp -f "$bt/$f" "$rd/$f" 2>/dev/null || true
      fi
    fi
  done
}

mount_z_read
if [ ! -d "$KALSHI_PRICE_DIR" ]; then
  log "ERROR: price history dir missing: $KALSHI_PRICE_DIR" >&2
  exit 2
fi

ENRICHED="$CONSOLE2_ROOT/analysis/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv"
NCEI_END="${NCEI_REFRESH_END_DATE:-$(date +%Y-%m-%d)}"
NCEI_START="${NCEI_REFRESH_START_DATE:-2026-04-20}"

log "price_dir=$KALSHI_PRICE_DIR mirror=$KMIA_KALSHI_WRITE_ROOT"

log "[1/6] Ingest Kalshi price-history CSVs from API…"
"$PYTHON" "$SCRIPTS/ingest_kalshi_market_data.py" --output-dir "$WRITABLE_PRICE" 2>&1 | tee -a "$LOG" \
  || log "WARN: price ingest failed (non-fatal)"

log "[2/6] Archive candlestick JSONL…"
"$PYTHON" "$SCRIPTS/kalshi_candle_archive.py" \
  --archive-dir "$WRITABLE_CANDLE" \
  --output-dir "$WRITABLE_PRICE" 2>&1 | tee -a "$LOG" \
  || log "WARN: candle archive failed (non-fatal)"

log "[3/6] Refresh NCEI CLIMIA TMAX ($NCEI_START → $NCEI_END)…"
"$PYTHON" "$SCRIPTS/refresh_kmia_ncei_climatology.py" \
  --start-date "$NCEI_START" --end-date "$NCEI_END" \
  --history-path "$KMIA_DAILY_HISTORY_JSONL" 2>&1 | tee -a "$LOG" \
  || log "WARN: NCEI refresh failed (non-fatal)"

log "[4/6] NBM fetch + validation…"
"$PYTHON" "$SCRIPTS/fetch_nbm_maxt_kmia.py" \
  --out "$CONSOLE2_BACKTEST_DIR/nbm_maxt_archive.jsonl" 2>&1 | tee -a "$LOG" \
  || log "WARN: NBM fetch failed (non-fatal)"
if [ -f "$ENRICHED" ]; then
  "$PYTHON" "$SCRIPTS/validate_nbm_vs_historical_stability.py" \
    --enriched-csv "$ENRICHED" \
    --nbm-jsonl "$CONSOLE2_BACKTEST_DIR/nbm_maxt_archive.jsonl" \
    --out "$CONSOLE2_BACKTEST_DIR/nbm_validation_report.json" 2>&1 | tee -a "$LOG" \
    || log "WARN: NBM validation failed (non-fatal)"
else
  log "WARN: enriched CSV missing — skip NBM validation"
fi

log "[5/6] Copy research artifacts to kalshi_mirror…"
copy_research_artifacts

mount_y_write
log "[6/6] Sync mirror to NAS…"
sync_mirror_to_nas

log "COMPLETE — log=$LOG"
