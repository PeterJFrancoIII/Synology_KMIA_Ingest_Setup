#!/usr/bin/env bash
# Opt-in only: remove raw GRIB when monthly VALID_ONLY exists for that variable.
# Run manually with: KMIA_ALLOW_CLEANUP=1 bash 34_cleanup_raw_grib.sh
set -euo pipefail
if [ "${KMIA_ALLOW_CLEANUP:-0}" != "1" ]; then
  echo "Refusing to delete raw GRIB (set KMIA_ALLOW_CLEANUP=1 to run)." >&2
  exit 1
fi
ROOT="${KMIA_ROOT:-/data/KMIA_Ingest}"
RAW="$ROOT/raw/forecast/ndfd_aws"
MONTHLY="$ROOT/processed/points/station=KMIA/monthly"
LOG="$ROOT/logs/ingestion/cleanup_raw.log"

echo "=== cleanup $(date -u) ===" | tee "$LOG"
for YEAR_DIR in "$MONTHLY"/*/; do
  [ -d "$YEAR_DIR" ] || continue
  YEAR=$(basename "$YEAR_DIR")
  for MONTH in $(seq -w 1 12); do
    for VAR in maxt wdir; do
      VALID="$MONTHLY/$YEAR/ndfd_kmia_${VAR}_${YEAR}${MONTH}_VALID_ONLY.csv"
      RAW_D="$RAW/${VAR}/$YEAR/$MONTH"
      if [ -f "$VALID" ] && [ -d "$RAW_D" ]; then
        echo "rm $RAW_D" | tee -a "$LOG"
        rm -rf "$RAW_D"
      fi
    done
  done
done
for F in "$MONTHLY"/*/*_point_forecasts.csv; do
  [ -f "$F" ] || continue
  V="${F/_point_forecasts.csv/_VALID_ONLY.csv}"
  if [ -f "$V" ]; then rm -f "$F" && echo "rm $F" >>"$LOG"; fi
done
df -h /data 2>/dev/null | tee -a "$LOG" || df -h /volume2 | tee -a "$LOG" || true
