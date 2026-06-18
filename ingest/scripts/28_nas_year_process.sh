#!/usr/bin/env bash
# Process previously ingested raw GRIBs: extract → VALID_ONLY → merge → chart.
# Run after 27_nas_year_ingest.sh has finished downloading a year.
set -euo pipefail

PYTHON="/opt/kmia-venv/bin/python3"
export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

ROOT="/data/KMIA_Ingest"
YEAR="${1:-2020}"
LOG="$ROOT/logs/ingestion/nas_year_${YEAR}_process.log"
POINTS="$ROOT/processed/points/station=KMIA"
YEARLY="$POINTS/yearly"
MONTHLY="$POINTS/monthly/${YEAR}"

mkdir -p "$YEARLY" "$MONTHLY" "$(dirname "$LOG")"

if [ "$YEAR" = "2020" ]; then
  FIRST_MONTH=4
  LAST_MONTH=12
elif [ "$YEAR" = "2026" ]; then
  FIRST_MONTH=1
  LAST_MONTH=6
else
  FIRST_MONTH=1
  LAST_MONTH=12
fi

{
  echo "=== NAS year PROCESS YEAR=${YEAR} ==="
  echo "Started: $(date -u)"
} | tee "$LOG"

OBS_CSV="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
if [ "$YEAR" != "2026" ] && [ ! -f "$OBS_CSV" ] && [ -f "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" ]; then
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$OBS_CSV"
fi

MAXT_MONTHLY=()
WDIR_MONTHLY=()

for MONTH in $(seq -w "$FIRST_MONTH" "$LAST_MONTH"); do
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

  if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
    echo "=== Month ${YEAR}-${MONTH} (skip — already processed) ===" | tee -a "$LOG"
    MAXT_MONTHLY+=("$MAXT_VALID")
    WDIR_MONTHLY+=("$WDIR_VALID")
    continue
  fi

  echo "=== Process ${YEAR}-${MONTH} ===" | tee -a "$LOG"

  if [ ! -f "$MAXT_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      echo "  extract maxt" | tee -a "$LOG"
      $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
        --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    fi
    echo "  filter maxt VALID_ONLY" | tee -a "$LOG"
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$MAXT_VALID" >>"$LOG" 2>&1
  fi
  MAXT_MONTHLY+=("$MAXT_VALID")

  if [ ! -f "$WDIR_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      echo "  extract wdir" | tee -a "$LOG"
      $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
        --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    fi
    echo "  filter wdir VALID_ONLY" | tee -a "$LOG"
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$WDIR_VALID" >>"$LOG" 2>&1
  fi
  WDIR_MONTHLY+=("$WDIR_VALID")
done

echo "Step: merge yearly maxt" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${MAXT_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1

echo "Step: merge yearly wdir" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${WDIR_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1

echo "Step: merge maxt + wdir" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/24_merge_forecast_csv.py" \
  --inputs "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv" >>"$LOG" 2>&1

if [ "$YEAR" != "2026" ] && [ -f "$OBS_CSV" ]; then
  echo "Step: chart outputs" | tee -a "$LOG"
  export KMIA_ROOT="$ROOT" KMIA_YEAR="$YEAR"
  export KMIA_FORECAST_CSV="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv"
  export KMIA_OBS_CSV="$OBS_CSV"
  $PYTHON "$ROOT/scripts/chart_kmia_year_stability_wind.py" >>"$LOG" 2>&1
fi

echo "Finished process: $(date -u)" | tee -a "$LOG"
