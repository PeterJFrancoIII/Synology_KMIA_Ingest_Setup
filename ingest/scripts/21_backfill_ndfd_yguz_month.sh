#!/usr/bin/env bash
# Download only YGUZ*/YBUZ* NDFD tiles for one variable/month (KMIA-covering family).
set -euo pipefail

export PATH="${KMIA_PATH:-/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin}:${PATH}"

ROOT="${KMIA_ROOT:-/data/KMIA_Ingest}"
SUBCATEGORY="${1:-}"
YEAR="${2:-}"
MONTH="${3:-}"
PATTERN="${4:-YGUZ*}"

if [ -z "$SUBCATEGORY" ] || [ -z "$YEAR" ] || [ -z "$MONTH" ]; then
  echo "Usage: $0 <variable> <YYYY> <MM> [pattern]"
  echo "Example: $0 wdir 2020 06 YBUZ*"
  exit 1
fi

MONTH=$(printf '%02d' "$((10#$MONTH))")
DAY_PARALLEL="${KMIA_AWS_DAY_PARALLEL:-6}"

LOCAL_ROOT="${KMIA_LOCAL_ROOT:-}"
if [ -z "$LOCAL_ROOT" ] && { [[ "$ROOT" == [A-Za-z]:* ]] || [[ "$ROOT" == //* ]]; }; then
  LOCAL_ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
  if [[ "$LOCAL_ROOT" == [A-Za-z]:* ]] || [[ "$LOCAL_ROOT" == //* ]]; then
    LOCAL_ROOT="/d/KMIA_Process"
  fi
fi
if [ -n "$LOCAL_ROOT" ]; then
  LOG="$LOCAL_ROOT/logs/ingestion/backfill_${SUBCATEGORY}_${YEAR}${MONTH}.log"
else
  LOG="$ROOT/logs/ingestion/backfill_${SUBCATEGORY}_yguz_${YEAR}${MONTH}.log"
fi
mkdir -p "$(dirname "$LOG")"
mkdir -p "$ROOT/raw/forecast/ndfd_aws/${SUBCATEGORY}/${YEAR}/${MONTH}"

log() { echo "$1" | tee -a "$LOG"; }

log "=== NDFD ${SUBCATEGORY} backfill ${YEAR}-${MONTH} ==="
log "Pattern: ${PATTERN} day_parallel=${DAY_PARALLEL}"
log "ROOT: ${ROOT}"
log "Started: $(date -u)"

PY="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
if [ ! -x "$PY" ] && ! command -v "$PY" >/dev/null 2>&1; then
  PY="${KMIA_PYTHON:-python3}"
fi
days_in_month="$("$PY" -c "import calendar; print(calendar.monthrange(int('${YEAR}'), int('${MONTH}'))[1])")"

downloads=0
failures=0
skips=0

download_one_day() {
  local day="$1"
  local s3_prefix="s3://noaa-ndfd-pds/wmo/${SUBCATEGORY}/${YEAR}/${MONTH}/${day}/"
  local out="$ROOT/raw/forecast/ndfd_aws/${SUBCATEGORY}/${YEAR}/${MONTH}/${day}"
  mkdir -p "$out"
  if [ -n "$(find "$out" -maxdepth 1 -type f -name "$PATTERN" -print -quit 2>/dev/null)" ]; then
    echo "skip"
    return 0
  fi
  log "Download: $s3_prefix (${PATTERN})"
  if (cd "$ROOT" && aws s3 cp --no-sign-request --no-progress --recursive "$s3_prefix" "$out/" \
      --exclude "*" --include "$PATTERN" >>"$LOG" 2>&1); then
    echo "ok"
  else
    log "WARN: download failed ${YEAR}-${MONTH}-${day}"
    echo "fail"
    return 1
  fi
}

if [ "$DAY_PARALLEL" -gt 1 ]; then
  for day in $(seq -w 1 "$days_in_month"); do
    download_one_day "$day" &
    while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$DAY_PARALLEL" ]; do
      wait -n 2>/dev/null || wait || true
    done
  done
  wait
else
  for day in $(seq -w 1 "$days_in_month"); do
    S3_PREFIX="s3://noaa-ndfd-pds/wmo/${SUBCATEGORY}/${YEAR}/${MONTH}/${day}/"
    OUT="$ROOT/raw/forecast/ndfd_aws/${SUBCATEGORY}/${YEAR}/${MONTH}/${day}"
    mkdir -p "$OUT"
    if [ -n "$(find "$OUT" -maxdepth 1 -type f -name "$PATTERN" -print -quit 2>/dev/null)" ]; then
      log "Skip download (exists): ${YEAR}-${MONTH}-${day}"
      skips=$((skips + 1))
      continue
    fi
    log "Download: $S3_PREFIX (${PATTERN})"
    if (cd "$ROOT" && aws s3 cp --no-sign-request --no-progress --recursive "$S3_PREFIX" "$OUT/" \
        --exclude "*" --include "$PATTERN" >>"$LOG" 2>&1); then
      downloads=$((downloads + 1))
    else
      log "WARN: download failed ${YEAR}-${MONTH}-${day}"
      failures=$((failures + 1))
    fi
  done
fi

file_count=$(find "$ROOT/raw/forecast/ndfd_aws/${SUBCATEGORY}/${YEAR}/${MONTH}" -type f 2>/dev/null | wc -l | tr -d ' ')
log "Finished: $(date -u)"
log "Days in month: $days_in_month | downloaded: $downloads | skipped: $skips | failures: $failures | files: $file_count"

if [ "$file_count" -eq 0 ] && [ "$failures" -gt 0 ]; then
  exit 1
fi
