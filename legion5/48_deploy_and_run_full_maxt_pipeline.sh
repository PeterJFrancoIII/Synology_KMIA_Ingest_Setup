#!/usr/bin/env bash
# Deploy latest scripts to Legion5 and start full 2020–2025 max-t BUILD + analysis.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${LEGION5_HOST:-Legion5}"
REMOTE="${KMIA_REMOTE:-D:/KMIA_Process}"

echo "=== Deploy scripts to ${HOST}:${REMOTE}/scripts ==="
scp -r "${REPO}/ingest/scripts/"* "${HOST}:${REMOTE}/scripts/"
scp "${REPO}/legion5/"{35_process_month_from_nas.sh,36_process_all_from_nas.sh,nas_pull_helpers.sh,kmia_legion5_env.sh,45_kmia_year_maxt_precision_analysis.sh,47_build_kmia_chart_suite.sh,43_setup_nas_smb.ps1} \
  "${HOST}:${REMOTE}/scripts/"
scp "${REPO}/ingest/scripts/11_isd_smoke_kmia.sh" "${HOST}:${REMOTE}/scripts/"

echo "=== Start full pipeline on Legion5 (background) ==="
scp "${REPO}/legion5/48_start_full_maxt_pipeline.bat" "${HOST}:${REMOTE}/scripts/"
ssh "$HOST" "D:\\KMIA_Process\\scripts\\48_start_full_maxt_pipeline.bat"

echo ""
echo "Monitor: ssh ${HOST} \"C:\\\\Progra~1\\\\Git\\\\bin\\\\bash.exe -lc 'tail -f /d/KMIA_Process/logs/processing/process_all.log'\""
