#!/usr/bin/env bash
# Merge Legion5 local NDFD GRIB into NAS canonical lake with deduplication.
#
# Transfer path: SMB3 robocopy via Z: (~95–120 MB/s on LAN). SSH is used only to
# pre-create destination month dirs (chmod 777) and for audit fallback counts.
#
# Sources (Legion5):
#   E:/KMIA_Ingest/raw/forecast/ndfd_aws  — legacy full copy (~950 GB)
#   D:/KMIA_Process/raw/forecast/ndfd_aws — gap-backfill staging
#
# Destination (NAS):
#   /volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws
#
# Usage:
#   bash 56_consolidate_legion5_grib_to_nas.sh audit
#   bash 56_consolidate_legion5_grib_to_nas.sh transfer
#   bash 56_consolidate_legion5_grib_to_nas.sh verify
#   DRY_RUN=1 bash 56_consolidate_legion5_grib_to_nas.sh transfer

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
MODE="${1:-audit}"
DRY_RUN="${DRY_RUN:-0}"

NAS_HOST="${NAS_SSH_HOST:-nas-local}"
NAS_RAW="/volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws"
NAS_SSH_OPTS="${NAS_SSH_OPTS:--o ControlMaster=no -o ConnectTimeout=30 -o BatchMode=yes}"

SOURCES=(
  "/e/KMIA_Ingest/raw/forecast/ndfd_aws"
  "/d/KMIA_Process/raw/forecast/ndfd_aws"
)

LOG_DIR="$ROOT/logs/ingestion"
PLAN="$LOG_DIR/grib_consolidation_plan.tsv"
TRANSFER_LOG="$LOG_DIR/grib_consolidation_transfer.log"
MANIFEST="$ROOT/manifest/grib_consolidation_manifest.jsonl"

mkdir -p "$LOG_DIR" "$ROOT/manifest"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
# shellcheck source=nas_push_helpers.sh
source "$SCRIPTS/nas_push_helpers.sh"

log() { echo "[56_grib] $(date -u +%H:%M:%S) $*" | tee -a "$TRANSFER_LOG"; }

nas_month_count() {
  local var="$1" year="$2" month="$3"
  if ensure_smb_read_mount; then
    smb_nas_month_count "$var" "$year" "$month"
    return 0
  fi
  ssh_nas "sudo -n find '${NAS_RAW}/${var}/${year}/$(printf '%02d' "$((10#$month))")' -type f 2>/dev/null | wc -l" 2>/dev/null \
    | tr -d ' \r\n'
}

transfer_month() {
  local src_root="$1" var="$2" year="$3" month="$4"
  local n
  n=$(find "${src_root}/${var}/${year}/$(printf '%02d' "$((10#$month))")" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' ')
  [ "${n:-0}" -gt 0 ] || n=$(find "${src_root}/${var}/${year}/$((10#$month))" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$DRY_RUN" = "1" ]; then
    log "DRY-RUN SMB3 month $var/$year/$month ($n files)"
    return 0
  fi
  if ! ensure_smb_read_mount; then
    log "ERROR: Z: SMB mount missing — run 43_setup_nas_smb.ps1" >&2
    return 1
  fi
  log "TRANSFER SMB3 $var/$year/$month ($n files) ..."
  smb_push_month "$src_root" "$var" "$year" "$month" "$TRANSFER_LOG"
  echo "{\"type\":\"month\",\"mode\":\"smb3\",\"var\":\"$var\",\"year\":\"$year\",\"month\":\"$month\",\"files\":$n,\"at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >>"$MANIFEST"
}

transfer_missing_files() {
  transfer_month "$1" "$2" "$3" "$4"
}

build_plan() {
  : >"$PLAN"
  echo -e "action\tsource\tvar\tyear\tmonth\tlocal_count\tnas_count" >>"$PLAN"
  ensure_smb_read_mount || log "WARN: Z: not mounted — audit counts via SSH (slower)"

  for src_root in "${SOURCES[@]}"; do
    [ -d "$src_root" ] || continue
    for var_dir in "$src_root"/*; do
      [ -d "$var_dir" ] || continue
      var=$(basename "$var_dir")
      for year_dir in "$var_dir"/*; do
        [ -d "$year_dir" ] || continue
        year=$(basename "$year_dir")
        for month_dir in "$year_dir"/*; do
          [ -d "$month_dir" ] || continue
          month=$(basename "$month_dir")
          month=$(printf '%02d' "$((10#$month))")
          local_n=$(find "$month_dir" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' ')
          [ "${local_n:-0}" -gt 0 ] || continue
          nas_n=$(nas_month_count "$var" "$year" "$month")
          nas_n=${nas_n:-0}
          if [ "$nas_n" -eq 0 ]; then
            echo -e "whole_month\t${src_root}\t${var}\t${year}\t${month}\t${local_n}\t0" >>"$PLAN"
          elif [ "$local_n" -gt "$nas_n" ]; then
            echo -e "partial\t${src_root}\t${var}\t${year}\t${month}\t${local_n}\t${nas_n}" >>"$PLAN"
          else
            echo -e "skip\t${src_root}\t${var}\t${year}\t${month}\t${local_n}\t${nas_n}" >>"$PLAN"
          fi
        done
      done
    done
  done

  log "PLAN written: $PLAN"
  echo "--- Summary ---"
  awk -F'\t' 'NR>1 {print $1}' "$PLAN" | sort | uniq -c
  echo "--- Transfer candidates ---"
  awk -F'\t' 'NR>1 && $1!="skip" {print}' "$PLAN"
}

execute_plan() {
  log "=== EXECUTE $(date -u) dry_run=$DRY_RUN mode=SMB3 ==="
  ensure_smb_read_mount || { log "ERROR: mount Z: before transfer"; exit 1; }

  while IFS=$'\t' read -r action source var year month local_n nas_n || [ -n "${action:-}" ]; do
    action="${action//$'\r'/}"
    source="${source//$'\r'/}"
    var="${var//$'\r'/}"
    year="${year//$'\r'/}"
    month="${month//$'\r'/}"
    local_n="${local_n//$'\r'/}"
    nas_n="${nas_n//$'\r'/}"
    case "$action" in
      whole_month) transfer_month "$source" "$var" "$year" "$month" || log "WARN failed $var/$year/$month" ;;
      partial) transfer_missing_files "$source" "$var" "$year" "$month" || log "WARN failed $var/$year/$month" ;;
      skip) log "SKIP $var/$year/$month (local=$local_n nas=$nas_n — already on NAS)" ;;
    esac
  done < <(tail -n +2 "$PLAN" | tr -d '\r')

  log "EXECUTE DONE"
}

verify_plan() {
  local fail=0 line action var year month local_n
  while IFS=$'\t' read -r action source var year month local_n nas_n || [ -n "${action:-}" ]; do
    action="${action//$'\r'/}"
    var="${var//$'\r'/}"
    year="${year//$'\r'/}"
    month="${month//$'\r'/}"
    local_n="${local_n//$'\r'/}"
    [ "$action" = "skip" ] && continue
    new_n=$(nas_month_count "$var" "$year" "$month")
    if [ "${new_n:-0}" -lt "${local_n:-1}" ]; then
      log "VERIFY FAIL: $var/$year/$month expected >=$local_n got ${new_n:-0}"
      fail=$((fail + 1))
    fi
  done < <(tail -n +2 "$PLAN" | tr -d '\r')

  if [ "$fail" -eq 0 ]; then
    log "VERIFY OK"
  else
    log "VERIFY FAILED ($fail months)"
    exit 1
  fi
}

case "$MODE" in
  audit) build_plan ;;
  transfer)
    [ -f "$PLAN" ] || build_plan
    execute_plan
    verify_plan
    ;;
  verify)
    [ -f "$PLAN" ] || build_plan
    verify_plan
    ;;
  *)
    echo "Usage: $0 {audit|transfer|verify}" >&2
    exit 1
    ;;
esac
