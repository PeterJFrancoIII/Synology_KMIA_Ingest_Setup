#!/usr/bin/env bash
# Process June 2020 NAS maxt ingest into chart-ready CSVs.
set -euo pipefail

export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

ROOT="/data/KMIA_Ingest"
YEAR="2020"
MONTH="06"
LOG="$ROOT/logs/ingestion/nas_june2020_pipeline.log"

mkdir -p "$(dirname "$LOG")"

{
  echo "=== NAS June 2020 chart pipeline ==="
  echo "Started: $(date -u)"
} | tee "$LOG"

echo "Step 1: ISD 2020" | tee -a "$LOG"
ISD_YEAR=2020 bash "$ROOT/scripts/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1

echo "Step 2: batch extract maxt YGUZ tiles" | tee -a "$LOG"
python3 "$ROOT/scripts/22_batch_extract_local_gribs.py" \
  --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" >>"$LOG" 2>&1

echo "Step 3: VALID_ONLY filter" | tee -a "$LOG"
python3 "$ROOT/scripts/23_filter_valid_only.py" \
  --input "$ROOT/processed/points/station=KMIA/ndfd_kmia_point_forecasts.csv" \
  --output "$ROOT/processed/points/station=KMIA/ndfd_kmia_point_forecasts_VALID_ONLY.csv" >>"$LOG" 2>&1

echo "Step 4: copy ISD for charting" | tee -a "$LOG"
cp "$ROOT/raw/observed/isd/2020/72202012839.csv" \
  "$ROOT/processed/points/station=KMIA/kmia_ncei_global_hourly_2020.csv"

{
  echo "Finished: $(date -u)"
  wc -l "$ROOT/processed/points/station=KMIA/ndfd_kmia_point_forecasts_VALID_ONLY.csv"
  ls -lh "$ROOT/processed/points/station=KMIA/"
} | tee -a "$LOG"
