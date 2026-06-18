#!/usr/bin/env bash
# Merge + chart one year after monthly VALID_ONLY files exist.
set -euo pipefail

PYTHON="${KMIA_PYTHON:-/opt/kmia-venv/bin/python3}"
export PATH="${KMIA_PATH:-/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin}:${PATH}"
ROOT="${KMIA_ROOT:-/e/KMIA_Ingest}"
YEAR="${1:?YEAR}"
FIRST_MONTH="${2:-1}"
if [ "$YEAR" = "2020" ]; then FIRST_MONTH=4; fi

POINTS="$ROOT/processed/points/station=KMIA"
YEARLY="$POINTS/yearly"
MONTHLY="$POINTS/monthly/${YEAR}"
LOG="$ROOT/logs/ingestion/finalize_${YEAR}.log"

mkdir -p "$YEARLY" "$(dirname "$LOG")"

MAXT_MONTHLY=()
WDIR_MONTHLY=()
for MONTH in $(seq -w "$FIRST_MONTH" 12); do
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"
  if [ ! -f "$MAXT_VALID" ] || [ ! -f "$WDIR_VALID" ]; then
    echo "missing month ${YEAR}-${MONTH}" | tee -a "$LOG"
    exit 1
  fi
  MAXT_MONTHLY+=("$MAXT_VALID")
  WDIR_MONTHLY+=("$WDIR_VALID")
done

if [ ! -f "$POINTS/kmia_ncei_global_hourly_${YEAR}.csv" ]; then
  ISD_YEAR="$YEAR" bash "$ROOT/scripts/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
  cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" "$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
fi

$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${MAXT_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${WDIR_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1
$PYTHON "$ROOT/scripts/24_merge_forecast_csv.py" \
  --inputs "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv" >>"$LOG" 2>&1

export KMIA_ROOT="$ROOT" KMIA_YEAR="$YEAR"
export KMIA_FORECAST_CSV="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv"
export KMIA_OBS_CSV="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
$PYTHON "$ROOT/scripts/chart_kmia_year_stability_wind.py" >>"$LOG" 2>&1
echo "finalized ${YEAR}: $(date -u)" | tee -a "$LOG"
