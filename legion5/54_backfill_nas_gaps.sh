#!/usr/bin/env bash
# Backfill GRIB gaps from AWS S3 to Legion5 D: (NAS SMB user is read-only).
# After backfill, run 35_process_month_from_nas.sh — it uses local raw when present.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/ingestion/backfill_gaps.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export PATH="$KMIA_PATH:$PATH"
export KMIA_ROOT="$ROOT"
export KMIA_LOCAL_ROOT="$ROOT"
export KMIA_PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

mkdir -p "$ROOT/logs/ingestion" "$ROOT/raw/forecast/ndfd_aws"

log() { echo "$1" | tee -a "$LOG"; }

log "=== Legion5 gap backfill (AWS → D:) start $(date -u) ==="
log "NOTE: NAS SMB is read-only; GRIB staged locally then extracted to VALID_ONLY."

backfill() {
  local var="$1" year="$2" month="$3" pattern="$4"
  log "--- backfill ${var} ${year}-${month} (${pattern}) ---"
  if bash "$SCRIPTS/21_backfill_ndfd_yguz_month.sh" "$var" "$year" "$month" "$pattern" >>"$LOG" 2>&1; then
    log "OK ${var} ${year}-${month}"
    return 0
  fi
  log "WARN backfill failed ${var} ${year}-${month}"
  return 1
}

process_month() {
  local year="$1" month="$2"
  log "--- extract ${year}-${month} ---"
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$year" "$month" >>"$LOG" 2>&1 \
    || log "WARN extract failed ${year}-${month}"
}

GAP_ROWS=(
  "2020 04 0 1"
  "2020 05 1 1"
  "2020 07 1 0"
  "2021 01 1 1"
  "2021 02 1 1"
  "2021 03 1 0"
  "2022 01 1 1"
  "2022 02 1 0"
  "2023 01 1 1"
  "2023 02 1 0"
  "2024 01 1 1"
  "2024 02 1 0"
  "2025 01 1 1"
  "2025 02 1 0"
)

for row in "${GAP_ROWS[@]}"; do
  read -r year month need_maxt need_wdir <<<"$row"
  month=$(printf '%02d' "$((10#$month))")
  [ "$need_maxt" = "1" ] && backfill maxt "$year" "$month" "YGUZ*"
  [ "$need_wdir" = "1" ] && backfill wdir "$year" "$month" "YBUZ*"
  process_month "$year" "$month"
done

log "=== Legion5 gap backfill + extract complete $(date -u) ==="
