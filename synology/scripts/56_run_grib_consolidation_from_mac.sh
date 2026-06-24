#!/usr/bin/env bash
# Orchestrate Legion5 → NAS GRIB consolidation from Mac.
#
# Transfer uses SMB3 robocopy on Legion5 (Z: mount, ~95–120 MB/s).
# SSH is only used to pre-create destination month dirs on NAS.
#
# Usage:
#   ./56_run_grib_consolidation_from_mac.sh audit
#   ./56_run_grib_consolidation_from_mac.sh transfer
#   ./56_run_grib_consolidation_from_mac.sh cleanup-legion5
#   ./56_run_grib_consolidation_from_mac.sh cleanup-mac

set -euo pipefail

REPO="${REPO:-$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup}"
LEGION_HOST="${LEGION_HOST:-Legion5}"
LEGION_SCRIPTS='D:/KMIA_Process/scripts'
MODE="${1:-audit}"

deploy_scripts() {
  echo "[mac] Deploy consolidation scripts to $LEGION_HOST:$LEGION_SCRIPTS ..."
  ssh "$LEGION_HOST" 'if not exist D:\KMIA_Process\scripts mkdir D:\KMIA_Process\scripts'
  scp "$REPO/legion5/56_consolidate_legion5_grib_to_nas.sh" \
      "$REPO/legion5/57_cleanup_legion5_grib.sh" \
      "$REPO/legion5/kmia_legion5_env.sh" \
      "$LEGION_HOST:D:/KMIA_Process/scripts/"
}

run_legion() {
  local cmd="$1"
  ssh "$LEGION_HOST" "\"C:\\Program Files\\Git\\bin\\bash.exe\" -lc 'cd /d/KMIA_Process/scripts && bash $cmd'"
}

cleanup_mac_test_raw() {
  local base="$HOME/Desktop/App Development/Kalshi/1_Downloads/NCEI_Historical_Ingest"
  echo "[mac] Removing test raw/ GRIB dirs under NCEI_Historical_Ingest (keeping golden master CSVs) ..."
  for d in "$base"/kmia_ndfd_*; do
    [ -d "$d/raw" ] || continue
    size=$(du -sh "$d/raw" 2>/dev/null | cut -f1)
    echo "  rm -rf $d/raw ($size)"
    rm -rf "$d/raw"
  done
  # Also clean experiments raw if present
  [ -d "$base/experiments" ] && find "$base/experiments" -type d -name raw -exec rm -rf {} + 2>/dev/null || true
  echo "[mac] Mac test raw cleanup done"
}

cleanup_nas_kalshi_test_raw() {
  echo "[mac] Removing duplicate test raw/ on NAS Kalshi mirror ..."
  ssh MediaServer2 'sudo -n bash -s' <<'EOF'
set -euo pipefail
BASE="/volume2/Data/App_Development/Kalshi/1_Downloads/NCEI_Historical_Ingest"
for d in "$BASE"/kmia_ndfd_*; do
  [ -d "$d/raw" ] || continue
  echo "  rm -rf $d/raw ($(du -sh "$d/raw" | cut -f1))"
  rm -rf "$d/raw"
done
find "$BASE/experiments" -type d -name raw 2>/dev/null | while read -r r; do
  echo "  rm -rf $r"
  rm -rf "$r"
done
echo "NAS Kalshi test raw cleanup done"
EOF
}

deploy_scripts

case "$MODE" in
  audit)
    run_legion "56_consolidate_legion5_grib_to_nas.sh audit"
    ;;
  transfer)
    run_legion "56_consolidate_legion5_grib_to_nas.sh transfer"
    ;;
  verify)
    run_legion "56_consolidate_legion5_grib_to_nas.sh verify"
    ;;
  cleanup-legion5)
    run_legion "CONFIRM=YES 57_cleanup_legion5_grib.sh delete"
    ;;
  cleanup-mac)
    cleanup_mac_test_raw
    cleanup_nas_kalshi_test_raw
    ;;
  all)
    run_legion "56_consolidate_legion5_grib_to_nas.sh audit"
    run_legion "56_consolidate_legion5_grib_to_nas.sh transfer"
    run_legion "CONFIRM=YES 57_cleanup_legion5_grib.sh delete"
    cleanup_mac_test_raw
    cleanup_nas_kalshi_test_raw
    ;;
  *)
    echo "Usage: $0 {audit|transfer|verify|cleanup-legion5|cleanup-mac|all}" >&2
    exit 1
    ;;
esac
