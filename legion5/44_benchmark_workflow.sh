#!/usr/bin/env bash
# Benchmark NAS->Legion5 pull modes and wgrib2 worker scaling.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
BENCH="$ROOT/raw/bench_workflow"
YEAR="${BENCH_YEAR:-2021}"
MONTH="${BENCH_MONTH:-07}"
DAY="${BENCH_DAY:-15}"
REMOTE_DAY="/volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}/${DAY}"
SMB_DAY="Z:/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}/${DAY}"

source "$SCRIPTS/kmia_legion5_env.sh"
source "$SCRIPTS/nas_pull_helpers.sh"
nas_pull_autodetect_mode

mkdir -p "$BENCH"
rm -rf "$BENCH"/*

bytes_in() {
  find "$1" -type f -exec stat -c%s {} + 2>/dev/null | awk '{s+=$1} END {print s+0}'
}

echo "=== KMIA workflow benchmark $(date -u) ==="
echo "Legion5 CPUs: $(nproc 2>/dev/null || echo unknown)"
df -h /d 2>/dev/null | tail -1
echo "NAS_PULL_MODE: ${NAS_PULL_MODE:-ssh}"
echo ""

# SSH tar one day (optional; may fail if shell user lacks path ACL)
dest_ssh="$BENCH/ssh_day"
mkdir -p "$dest_ssh"
start=$(date +%s)
if ssh_nas "${NAS_SSH_HOST:-nas-local}" "tar cf - -C '${REMOTE_DAY}' ." 2>/dev/null | tar xf - -C "$dest_ssh" 2>/dev/null; then
  end=$(date +%s)
  ssh_sec=$((end - start))
  ssh_files=$(find "$dest_ssh" -type f | wc -l | tr -d ' ')
  ssh_mb=$(awk "BEGIN {printf \"%.1f\", $(bytes_in "$dest_ssh") / 1048576}")
  echo "ssh_tar_day: ${ssh_sec}s ${ssh_files} files ${ssh_mb} MB"
else
  echo "ssh_tar_day: SKIP (NAS shell ACL — SMB is LAN default)"
fi

# SMB robocopy one day
dest_smb="$BENCH/smb_day"
mkdir -p "$dest_smb"
win_src=$(to_win_path "$SMB_DAY")
win_dest=$(to_win_path "$dest_smb")
start=$(date +%s)
MSYS2_ARG_CONV_EXCL='*' /c/Windows/System32/robocopy.exe "$win_src" "$win_dest" /E /MT:16 /NP /NFL /NDL /NJH /NJS /nc /ns >/dev/null 2>&1
end=$(date +%s)
smb_sec=$((end - start))
smb_files=$(find "$dest_smb" -type f | wc -l | tr -d ' ')
smb_mb=$(awk "BEGIN {printf \"%.1f\", $(bytes_in "$dest_smb") / 1048576}")
smb_mbps=$(awk "BEGIN {printf \"%.1f\", $smb_mb / ($smb_sec > 0 ? $smb_sec : 1)}")
echo "smb_robocopy_day: ${smb_sec}s ${smb_files} files ${smb_mb} MB = ${smb_mbps} MB/s"

# wgrib2 worker scaling (one day maxt)
extract_root="$BENCH/extract_root"
mkdir -p "$extract_root/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}"
cp -r "$dest_smb"/* "$extract_root/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}/"

for w in 1 4 8; do
  out="$BENCH/extract_w${w}.csv"
  rm -f "$out"
  start=$(date +%s)
  "$PYTHON" "$SCRIPTS/22_batch_extract_local_gribs.py" \
    --root "$extract_root" --subcategory maxt --year "$YEAR" --month "$MONTH" \
    --pattern "YGUZ*" --workers "$w" --output "$out" >/dev/null 2>&1 || true
  end=$(date +%s)
  rows=$(($(wc -l < "$out" 2>/dev/null || echo 1) - 1))
  echo "extract_maxt_day_workers_${w}: $((end - start))s rows=${rows}"
done

valid_proxy="$ROOT/processed/points/station=KMIA/monthly/${YEAR}/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
wdir_proxy="$ROOT/processed/points/station=KMIA/monthly/${YEAR}/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"
for f in "$valid_proxy" "$wdir_proxy"; do
  [ -f "$f" ] && echo "csv $(basename "$f"): $(awk "BEGIN {printf \"%.2f\", $(stat -c%s "$f") / 1048576}") MB"
done

echo ""
echo "=== Observed full-month times (2021 4-season study) ==="
echo "spring_202104: 22:38:20 -> 23:04:26 UTC (~26 min, SMB w=4)"
echo "summer_202107: 23:04:27 -> 23:30:50 UTC (~26 min, SMB w=4)"
echo "fall_202110:   23:30:50 -> 23:56:37 UTC (~26 min, SMB w=4)"
echo "winter_202112: ~50 min (SSH tar, serial wdir — pre-optimization)"
echo ""
echo "=== Extrapolation: 72 months (2020-2025) ==="
echo "path_A_legion5_smb_w4: ~31 hours (72 x 26 min)"
echo "path_B_legion5_smb_w8_parallel_vars: ~18-22 hours (est.)"
echo "path_C_nas_extract_legion5_csv: ~4-8 hours extract on NAS + ~1 hour CSV pull (est.)"
echo "path_D_analysis_only (CSVs exist): ~5 min per study"
echo "=== done ==="
