#!/usr/bin/env bash
# Fast month-level GRIB audit via SSH to NAS (no per-file SMB walk).
set -euo pipefail

HOST="${NAS_SSH_HOST:-nas-local}"
BASE="${NAS_ROOT:-/volume2/Data/App_Development/KMIA_Ingest}/raw/forecast/ndfd_aws"
YEARS="${1:-2020 2021 2022 2023 2024 2025}"

# shellcheck source=nas_pull_helpers.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/nas_pull_helpers.sh"

count_remote_month() {
  local var="$1" year="$2" month="$3"
  local m_pad m_unpad remote
  m_pad=$(printf '%02d' "$((10#$month))")
  m_unpad=$((10#$month))
  for m in "$m_pad" "$m_unpad"; do
    remote="${BASE}/${var}/${year}/${m}"
    if ssh_nas "$HOST" "test -d '${remote}'" 2>/dev/null; then
      ssh_nas "$HOST" "find '${remote}' -type f 2>/dev/null | wc -l" 2>/dev/null | tr -d ' \r'
      return 0
    fi
  done
  echo "0"
}

echo "=== Fast GRIB archive audit via ${HOST} ==="
echo "base=${BASE}"
printf "%-10s %10s %10s %s\n" "MONTH" "MAXT" "WDIR" "STATUS"
gaps=0
for year in $YEARS; do
  first=1
  [ "$year" = "2020" ] && first=4
  for month in $(seq -w "$first" 12); do
    maxt=$(count_remote_month maxt "$year" "$month")
    wdir=$(count_remote_month wdir "$year" "$month")
    status="OK"
    if [ "$maxt" = "0" ] && [ "$wdir" = "0" ]; then
      status="MISSING_BOTH"
      gaps=$((gaps + 1))
    elif [ "$maxt" = "0" ]; then
      status="MISSING_MAXT"
      gaps=$((gaps + 1))
    elif [ "$wdir" = "0" ]; then
      status="MISSING_WDIR"
      gaps=$((gaps + 1))
    fi
    printf "%s-%s %10s %10s %s\n" "$year" "$month" "$maxt" "$wdir" "$status"
  done
done
echo "=== gaps: ${gaps} months ==="
