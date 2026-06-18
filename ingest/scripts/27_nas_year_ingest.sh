#!/usr/bin/env bash
# Raw ingest only: ISD observed CSV + NDFD maxt/wdir GRIB downloads.
# No wgrib2 extract, VALID_ONLY filter, merge, or charting — run 28_nas_year_process.sh later.
set -euo pipefail

ROOT="/data/KMIA_Ingest"
YEAR="${1:-2020}"
LOG="$ROOT/logs/ingestion/nas_year_${YEAR}_ingest.log"
RAW="$ROOT/raw/forecast/ndfd_aws"
POINTS="$ROOT/processed/points/station=KMIA"
MONTHLY="$POINTS/monthly/${YEAR}"

mkdir -p "$(dirname "$LOG")" "$MONTHLY"

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
  echo "=== NAS year INGEST (raw only) YEAR=${YEAR} ==="
  echo "Started: $(date -u)"
  echo "Months: $(printf '%02d' $FIRST_MONTH)-$(printf '%02d' $LAST_MONTH)"
} | tee "$LOG"

OBS_CSV="$POINTS/kmia_ncei_global_hourly_${YEAR}.csv"
if [ "$YEAR" = "2026" ]; then
  echo "Step 1: ISD ${YEAR} (skip — NCEI 2026 not published yet)" | tee -a "$LOG"
elif [ -f "$OBS_CSV" ] || [ -f "$ROOT/raw/observed/isd/${YEAR}/72202012839.csv" ]; then
  echo "Step 1: ISD ${YEAR} (skip — already downloaded)" | tee -a "$LOG"
else
  echo "Step 1: ISD ${YEAR}" | tee -a "$LOG"
  ISD_YEAR="$YEAR" bash "$ROOT/scripts/11_isd_smoke_kmia.sh" >>"$LOG" 2>&1
fi

for MONTH in $(seq -w "$FIRST_MONTH" "$LAST_MONTH"); do
  MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
  WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

  if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
    echo "=== Ingest ${YEAR}-${MONTH} (skip — Legion5/NAS VALID_ONLY complete) ===" | tee -a "$LOG"
    continue
  fi

  echo "=== Ingest ${YEAR}-${MONTH} ===" | tee -a "$LOG"

  if [ -f "$MAXT_VALID" ]; then
    echo "  maxt skip — VALID_ONLY already exists (Legion5)" | tee -a "$LOG"
  else
    echo "  download maxt YGUZ (skips existing days)" | tee -a "$LOG"
    bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" maxt "$YEAR" "$MONTH" "YGUZ*" >>"$LOG" 2>&1
  fi

  if [ -f "$WDIR_VALID" ]; then
    echo "  wdir skip — VALID_ONLY already exists (Legion5)" | tee -a "$LOG"
  else
    echo "  download wdir YBUZ (skips existing days)" | tee -a "$LOG"
    bash "$ROOT/scripts/21_backfill_ndfd_yguz_month.sh" wdir "$YEAR" "$MONTH" "YBUZ*" >>"$LOG" 2>&1
  fi

  echo "  ingest ${YEAR}-${MONTH} done" | tee -a "$LOG"
done

{
  echo "Finished ingest: $(date -u)"
  echo "maxt files: $(find "$RAW/maxt/${YEAR}" -type f 2>/dev/null | wc -l)"
  echo "wdir files: $(find "$RAW/wdir/${YEAR}" -type f 2>/dev/null | wc -l)"
} | tee -a "$LOG"
