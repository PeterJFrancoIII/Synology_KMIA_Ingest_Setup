#!/usr/bin/env bash
# Retry months that failed in process_all.log (SMB blips, missing wdir on first pass).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
LOG="$ROOT/logs/processing/process_all.log"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-8}"

grep 'WARN month' "$LOG" 2>/dev/null | sed -n 's/.*WARN month \([0-9]*\)-\([0-9]*\) failed.*/\1 \2/p' | sort -u | while read -r y m; do
  [ -z "$y" ] && continue
  echo "=== retry ${y}-${m} ==="
  bash "$SCRIPTS/35_process_month_from_nas.sh" "$y" "$m" || echo "WARN retry ${y}-${m} failed"
done

bash "$SCRIPTS/49_build_all_charts.sh"
