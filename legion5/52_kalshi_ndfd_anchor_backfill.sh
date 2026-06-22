#!/usr/bin/env bash
# Re-extract NDFD maxT at MapClick pin (25.7906 / -80.3164) and backfill Kalshi NWS snapshots.
#
# Parallelism (12-core Legion5 defaults):
#   KMIA_EXTRACT_WORKERS=10     wgrib2 processes per month (one month at a time)
#   KMIA_AWS_DAY_PARALLEL=6     concurrent S3 day downloads per month
#   KMIA_MONTH_DL_PARALLEL=2    months downloading simultaneously (when not pipelined)
# Pipeline: download month N+1 while extracting month N (fastest safe path).
#
# Run on Legion5 after deploy:
#   KMIA_FORCE_REEXTRACT=1 bash D:/KMIA_Process/scripts/52_kalshi_ndfd_anchor_backfill.sh 2026 04 2026 06

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export PYTHONPATH="$SCRIPTS:${PYTHONPATH:-}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
# shellcheck source=kmia_station_env.sh
source "$SCRIPTS/kmia_station_env.sh"

if [ "${SKIP_STORAGE_CHECK:-0}" != "1" ]; then
  bash "$SCRIPTS/53_check_storage_headroom.sh" || {
    echo "[52_ndfd] Storage preflight failed — set SKIP_STORAGE_CHECK=1 to override" >&2
    exit 1
  }
fi

START_YEAR="${1:-2026}"
START_MONTH="${2:-04}"
END_YEAR="${3:-2026}"
END_MONTH="${4:-06}"
FORCE="${KMIA_FORCE_REEXTRACT:-0}"
WORKERS="${KMIA_EXTRACT_WORKERS:-10}"

POINTS="$ROOT/processed/points/station=KMIA"
MERGED="$POINTS/kalshi_ndfd_maxt_VALID_ONLY.csv"
KALSHI_NWS="${KALSHI_NWS_DIR:-/d/KMIA_Process/kalshi_mirror/backend/data/processed/weather_nws}"
PRICE_DIR="${KALSHI_PRICE_DIR:-}"

log() { echo "[52_ndfd] $*"; }

month_in_range() {
  local y=$1 m=$2 ey=$3 em=$4
  local cur=$(( y * 100 + 10#$m ))
  local end_ym=$(( ey * 100 + 10#$em ))
  [ "$cur" -le "$end_ym" ]
}

pin_ok_csv() {
  local valid_out="$1"
  "$PYTHON" - <<PY
import pandas as pd, sys
df = pd.read_csv(r"$valid_out", nrows=5)
if "station_lat" not in df.columns:
    sys.exit(1)
lat = float(df["station_lat"].iloc[0])
lon = float(df["station_lon"].iloc[0])
sys.exit(0 if abs(lat - 25.7906) < 0.001 and abs(lon + 80.3164) < 0.001 else 1)
PY
}

ensure_month_paths() {
  local year=$1 month=$2
  month=$(printf '%02d' "$((10#$month))")
  MONTHLY="$POINTS/monthly/${year}"
  RAW_OUT="$MONTHLY/ndfd_kmia_maxt_${year}${month}_point_forecasts.csv"
  VALID_OUT="$MONTHLY/ndfd_kmia_maxt_${year}${month}_VALID_ONLY.csv"
  mkdir -p "$MONTHLY"
}

download_month() {
  local year=$1 month=$2
  month=$(printf '%02d' "$((10#$month))")
  ensure_month_paths "$year" "$month"
  local raw_dir="$ROOT/raw/forecast/ndfd_aws/maxt/${year}/${month}"

  if [ -d "$raw_dir" ] && [ -n "$(find "$raw_dir" -type f -name 'YGUZ*' 2>/dev/null | head -1)" ]; then
    log "download ${year}-${month}: raw present — top up missing days (parallel=${KMIA_AWS_DAY_PARALLEL:-6})..."
    KMIA_ROOT="$ROOT" bash "$SCRIPTS/21_backfill_ndfd_yguz_month.sh" maxt "$year" "$month" "YGUZ*"
    return 0
  fi

  log "download ${year}-${month}: pull from NAS..."
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$year" "$month" || true

  if [ ! -d "$raw_dir" ] || [ -z "$(find "$raw_dir" -type f -name 'YGUZ*' 2>/dev/null | head -1)" ]; then
    log "download ${year}-${month}: NAS miss — AWS YGUZ (day_parallel=${KMIA_AWS_DAY_PARALLEL:-6})..."
    KMIA_ROOT="$ROOT" bash "$SCRIPTS/21_backfill_ndfd_yguz_month.sh" maxt "$year" "$month" "YGUZ*"
  fi
}

extract_month() {
  local year=$1 month=$2
  month=$(printf '%02d' "$((10#$month))")
  ensure_month_paths "$year" "$month"

  if [ "$FORCE" = "1" ]; then
    log "extract ${year}-${month}: force at lat=$KMIA_LAT lon=$KMIA_LON workers=$WORKERS"
    rm -f "$RAW_OUT" "$VALID_OUT"
  elif [ -f "$VALID_OUT" ] && pin_ok_csv "$VALID_OUT"; then
    log "extract ${year}-${month}: skip — VALID_ONLY already at canonical pin"
    return 0
  elif [ -f "$VALID_OUT" ]; then
    log "extract ${year}-${month}: legacy pin — re-extract workers=$WORKERS"
    rm -f "$RAW_OUT" "$VALID_OUT"
  fi

  log "extract ${year}-${month}: wgrib2 x${WORKERS}..."
  "$PYTHON" "$SCRIPTS/22_batch_extract_local_gribs.py" \
    --subcategory maxt --year "$year" --month "$month" \
    --pattern "YGUZ*" --root "$ROOT" \
    --lat "$KMIA_LAT" --lon "$KMIA_LON" \
    --workers "$WORKERS" \
    --output "$RAW_OUT"

  "$PYTHON" "$SCRIPTS/23_filter_valid_only.py" \
    --input "$RAW_OUT" --output "$VALID_OUT"
  log "extract ${year}-${month}: wrote $VALID_OUT"
}

# Build month list
MONTHS=()
y=$START_YEAR
m=$START_MONTH
while month_in_range "$y" "$m" "$END_YEAR" "$END_MONTH"; do
  MONTHS+=("${y}:$(printf '%02d' "$((10#$m))")")
  m=$((10#$m + 1))
  if [ "$m" -gt 12 ]; then m=1; y=$((y + 1)); fi
done

n=${#MONTHS[@]}
log "months=${n} workers=${WORKERS} aws_day_parallel=${KMIA_AWS_DAY_PARALLEL:-6} pipeline=download[N+1]||extract[N]"

if [ "$n" -eq 0 ]; then
  log "no months in range"
  exit 1
fi

# Pipeline: overlap download of next month with extract of current (CPU-saturated extract, I/O-bound download).
IFS=: read -r y0 m0 <<< "${MONTHS[0]}"
download_month "$y0" "$m0"
extract_month "$y0" "$m0" &
ext_pid=$!

for ((i=1; i<n; i++)); do
  IFS=: read -r y m <<< "${MONTHS[$i]}"
  download_month "$y" "$m" &
  dl_pid=$!
  wait "$ext_pid" 2>/dev/null || wait "$ext_pid"
  wait "$dl_pid" 2>/dev/null || wait "$dl_pid"
  extract_month "$y" "$m" &
  ext_pid=$!
done
wait "$ext_pid" 2>/dev/null || wait "$ext_pid"

log "merge monthly VALID_ONLY → $MERGED"
"$PYTHON" "$SCRIPTS/ndfd_kalshi_forecast.py" merge \
  --roots "$POINTS/monthly/2026" \
  --output "$MERGED"

BACKFILL_ARGS=(--ndfd-csv "$MERGED" --replace-iem --nws-dir "$KALSHI_NWS")
if [ -n "$PRICE_DIR" ] && [ -d "$PRICE_DIR" ]; then
  BACKFILL_ARGS+=(--price-history-dir "$PRICE_DIR")
else
  BACKFILL_ARGS+=(--start-date "${START_YEAR}-$(printf '%02d' "$START_MONTH")-01")
  BACKFILL_ARGS+=(--end-date "${END_YEAR}-$(printf '%02d' "$END_MONTH")-28")
fi

if [ "${SKIP_KALSHI_BACKFILL:-0}" = "1" ]; then
  log "SKIP_KALSHI_BACKFILL=1 — merged CSV only: $MERGED"
else
  log "research pipeline on Legion5 (NAS Kalshi via Z:)…"
  bash "$SCRIPTS/54_kalshi_ndfd_research_pipeline.sh" "$MERGED"
fi

JOB_TAG="${START_YEAR}$(printf '%02d' "$START_MONTH")_${END_YEAR}$(printf '%02d' "$END_MONTH")"
DONE_DIR="$ROOT/logs/jobs"
mkdir -p "$DONE_DIR"
DONE_MARKER="$DONE_DIR/ndfd_kalshi_${JOB_TAG}.done"
{
  echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "job_tag=$JOB_TAG"
  echo "merged=$MERGED"
  echo "months=$n"
  echo "workers=$WORKERS"
} > "$DONE_MARKER"
log "done — merged CSV: $MERGED (marker: $DONE_MARKER)"
