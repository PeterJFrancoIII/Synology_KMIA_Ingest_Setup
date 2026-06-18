#!/usr/bin/env bash
# Benchmark NAS -> Legion5 pull: SSH tar vs SMB robocopy (one day of GRIB).
set -euo pipefail

HOST="${NAS_SSH_HOST:-nas-local}"
YEAR="${BENCH_YEAR:-2021}"
MONTH="${BENCH_MONTH:-04}"
DAY="${BENCH_DAY:-01}"
VAR="${BENCH_VAR:-maxt}"
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
DEST_BASE="$ROOT/raw/bench_pull"
REMOTE="/volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws/${VAR}/${YEAR}/${MONTH}/${DAY}"

SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
# shellcheck source=nas_pull_helpers.sh
source "${SCRIPTS}/nas_pull_helpers.sh"

mkdir -p "$DEST_BASE"

bytes_in_dest() {
  find "$1" -type f -exec stat -c%s {} + 2>/dev/null | awk '{s+=$1} END {print s+0}'
}

bench_ssh() {
  local dest="$DEST_BASE/ssh_${VAR}_${YEAR}${MONTH}${DAY}"
  rm -rf "$dest"
  mkdir -p "$dest"
  local start end secs bytes mb mbps
  start=$(date +%s)
  if [ "${NAS_TAR_COMPRESS:-no}" = "yes" ]; then
    ssh_nas "$HOST" "tar czf - -C '$REMOTE' ." | tar xzf - -C "$dest"
  else
    ssh_nas "$HOST" "tar cf - -C '$REMOTE' ." | tar xf - -C "$dest"
  fi
  end=$(date +%s)
  secs=$((end - start))
  [ "$secs" -lt 1 ] && secs=1
  bytes=$(bytes_in_dest "$dest")
  mb=$(awk "BEGIN {printf \"%.1f\", $bytes / 1048576}")
  mbps=$(awk "BEGIN {printf \"%.1f\", $mb / $secs}")
  echo "ssh_tar: ${mb} MB in ${secs}s = ${mbps} MB/s ($(count_pulled_files "$dest") files)"
}

bench_smb() {
  local dest="$DEST_BASE/smb_${VAR}_${YEAR}${MONTH}${DAY}"
  rm -rf "$dest"
  mkdir -p "$dest"
  local src threads win_src win_dest start end secs bytes mb mbps rc
  src=$(resolve_smb_month_dir "$VAR" "$YEAR" "$MONTH") || {
    echo "smb: SKIP — SMB path not available (run 43_setup_nas_smb.ps1)"
    return 0
  }
  src="${src}/${DAY}"
  if [ ! -d "$src" ]; then
    echo "smb: SKIP — day dir missing: $src"
    return 0
  fi
  threads="${NAS_SMB_THREADS:-16}"
  win_src=$(to_win_path "$src")
  win_dest=$(to_win_path "$dest")
  start=$(date +%s)
  MSYS2_ARG_CONV_EXCL='*' cmd.exe //c "robocopy \"${win_src}\" \"${win_dest}\" /E /MT:${threads} /NP /NFL /NDL /NJH /NJS /nc /ns"
  rc=$?
  end=$(date +%s)
  secs=$((end - start))
  [ "$secs" -lt 1 ] && secs=1
  if [ "$rc" -ge 8 ]; then
    echo "smb: FAIL robocopy rc=$rc"
    return 1
  fi
  bytes=$(bytes_in_dest "$dest")
  mb=$(awk "BEGIN {printf \"%.1f\", $bytes / 1048576}")
  mbps=$(awk "BEGIN {printf \"%.1f\", $mb / $secs}")
  echo "smb_robocopy: ${mb} MB in ${secs}s = ${mbps} MB/s ($(count_pulled_files "$dest") files)"
}

echo "=== Pull mode benchmark $(date -u) ==="
echo "Remote day: $REMOTE"
echo "NAS_PULL_MODE current: ${NAS_PULL_MODE:-ssh}"
echo "NAS_SMB_DRIVE: ${NAS_SMB_DRIVE:-unset}"
ping -n 2 "${NAS_SMB_HOST:-192.168.0.193}" 2>/dev/null | tail -1 || true
bench_ssh
bench_smb
echo "=== done ==="
