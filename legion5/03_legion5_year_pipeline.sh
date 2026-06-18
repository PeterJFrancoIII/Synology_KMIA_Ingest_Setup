#!/usr/bin/env bash
# Legion5 full-year KMIA ingest — same logic as NAS 27_, tuned for local WSL paths.
set -euo pipefail

PYTHON="${KMIA_PYTHON:-/opt/kmia-venv/bin/python3}"
export PATH="${KMIA_PATH:-/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin}:${PATH}"

ROOT="${KMIA_ROOT:-/e/KMIA_Ingest}"
YEAR="${1:-2020}"
LOG="$ROOT/logs/ingestion/legion5_year_${YEAR}_pipeline.log"
POINTS="$ROOT/processed/points/station=KMIA"
YEARLY="$POINTS/yearly"
MONTHLY="$POINTS/monthly/${YEAR}"

mkdir -p "$YEARLY" "$MONTHLY" "$(dirname "$LOG")"

if [ "$YEAR" = "2020" ]; then
  FIRST_MONTH=4
  LAST_MONTH=12
  echo "Note: AWS NDFD wmo data begins 2020-04-16; skipping months 01-03" | tee -a "$LOG"
elif [ "$YEAR" = "2026" ]; then
  FIRST_MONTH=1
  LAST_MONTH=6
  echo "Note: 2026 partial on S3 through month 06" | tee -a "$LOG"
else
  FIRST_MONTH=1
  LAST_MONTH=12
fi

{
  echo "=== Legion5 year pipeline YEAR=${YEAR} ==="
  echo "Host: $(hostname)"
  echo "Started: $(date -u)"
  echo "ROOT: $ROOT"
} | tee "$LOG"

echo "Step 1: ISD ${YEAR}" | tee -a "$LOG"
ISD_YEAR="$YEAR" bash "$ROOT/scripts/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
cp "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" \
  "$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"

MAXT_MONTHLY=()
WDIR_MONTHLY=()

for MONTH in $(seq -w "$FIRST_MONTH" "$LAST_MONTH"); do
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

  if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
    echo "=== Month ${YEAR}-${MONTH} (skip — complete) ===" | tee -a "$LOG"
    MAXT_MONTHLY+=("$MAXT_VALID")
    WDIR_MONTHLY+=("$WDIR_VALID")
    continue
  fi

  echo "=== Month ${YEAR}-${MONTH} ===" | tee -a "$LOG"

  if [ ! -f "$MAXT_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      echo "  download maxt YGUZ" | tee -a "$LOG"
      bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" maxt "$YEAR" "$MONTH" "YGUZ*" >>"$LOG" 2>&1
      echo "  extract maxt" | tee -a "$LOG"
      $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
        --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    else
      echo "  maxt point forecast exists — skip download/extract" | tee -a "$LOG"
    fi
    echo "  filter maxt VALID_ONLY" | tee -a "$LOG"
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$MAXT_VALID" >>"$LOG" 2>&1
  fi
  MAXT_MONTHLY+=("$MAXT_VALID")

  if [ ! -f "$WDIR_VALID" ]; then
    if [ ! -f "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" ]; then
      echo "  download wdir YBUZ" | tee -a "$LOG"
      bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" wdir "$YEAR" "$MONTH" "YBUZ*" >>"$LOG" 2>&1
      echo "  extract wdir" | tee -a "$LOG"
      $PYTHON "$ROOT/scripts/22_batch_extract_local_gribs.py" \
        --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
        --root "$ROOT" \
        --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
    else
      echo "  wdir point forecast exists — skip download/extract" | tee -a "$LOG"
    fi
    echo "  filter wdir VALID_ONLY" | tee -a "$LOG"
    $PYTHON "$ROOT/scripts/23_filter_valid_only.py" \
      --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
      --output "$WDIR_VALID" >>"$LOG" 2>&1
  fi
  WDIR_MONTHLY+=("$WDIR_VALID")

  echo "  month ${YEAR}-${MONTH} done" | tee -a "$LOG"
done

echo "Step 3: merge yearly" | tee -a "$LOG"
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${MAXT_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1
$PYTHON "$ROOT/scripts/28_merge_yearly_forecast_csv.py" \
  --inputs "${WDIR_MONTHLY[@]}" \
  --output "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" >>"$LOG" 2>&1

$PYTHON "$ROOT/scripts/24_merge_forecast_csv.py" \
  --inputs "$YEARLY/ndfd_kmia_maxt_${YEAR}_VALID_ONLY.csv" "$YEARLY/ndfd_kmia_wdir_${YEAR}_VALID_ONLY.csv" \
  --output "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv" >>"$LOG" 2>&1

echo "Step 6: chart" | tee -a "$LOG"
export KMIA_ROOT="$ROOT" KMIA_YEAR="$YEAR"
export KMIA_FORECAST_CSV="$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv"
export KMIA_OBS_CSV="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
$PYTHON "$ROOT/scripts/chart_kmia_year_stability_wind.py" >>"$LOG" 2>&1

echo "Finished: $(date -u)" | tee -a "$LOG"
ls -lh "$POINTS/ndfd_kmia_point_forecasts_VALID_ONLY_${YEAR}.csv" "$POINTS"/kmia_${YEAR}_* 2>/dev/null | tee -a "$LOG"
