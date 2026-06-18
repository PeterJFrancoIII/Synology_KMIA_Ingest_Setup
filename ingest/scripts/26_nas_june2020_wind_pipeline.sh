#!/usr/bin/env bash
# Add NDFD wdir for June 2020, merge with maxt, regenerate wind-aware chart outputs.
set -euo pipefail

PYTHON="/opt/kmia-venv/bin/python3"
export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

ROOT="/data/KMIA_Ingest"
YEAR="2020"
MONTH="06"
POINTS="$ROOT/processed/points/station=KMIA"
LOG="$ROOT/logs/ingestion/nas_june2020_wind_pipeline.log"

mkdir -p "$(dirname "$LOG")"
{
  echo "=== NAS June 2020 wind pipeline ==="
  echo "Started: $(date -u)"
} | tee "$LOG"

echo "Step 1: download wdir YBUZ tiles" | tee -a "$LOG"
bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" wdir "$YEAR" "$MONTH" "YBUZ*" >>"$LOG" 2>&1

echo "Step 2: extract wdir points" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
  --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
  --root "$ROOT" >>"$LOG" 2>&1
mv "$POINTS/ndfd_kmia_point_forecasts.csv" "$POINTS/ndfd_kmia_wdir_point_forecasts.csv"

echo "Step 3: filter wdir VALID_ONLY" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
  --input "$POINTS/ndfd_kmia_wdir_point_forecasts.csv" \
  --output "$POINTS/ndfd_kmia_wdir_point_forecasts_VALID_ONLY.csv" >>"$LOG" 2>&1

echo "Step 4: merge maxt + wdir" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/24_merge_forecast_csv.py" \
  --inputs "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY.csv" "$POINTS/ndfd_kmia_wdir_point_forecasts_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY.csv" >>"$LOG" 2>&1

echo "Step 5: regenerate chart outputs" | tee -a "$LOG"
export KMIA_ROOT=/data/KMIA_Ingest
$PYTHON "$ROOT/scripts/chart_kmia_nas_june2020.py" >>"$LOG" 2>&1

{
  echo "Finished: $(date -u)"
  ls -lh "$POINTS"/*.csv "$POINTS"/*.png 2>/dev/null
} | tee -a "$LOG"
