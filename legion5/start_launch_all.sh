#!/usr/bin/env bash
set -euo pipefail
export KMIA_ROOT="/e/KMIA_Ingest"
export KMIA_PYTHON="/e/Miniforge3/python.exe"
export KMIA_PATH="/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2"
export PATH="$KMIA_PATH:$PATH"
nohup bash "$KMIA_ROOT/scripts/33_launch_all_available.sh" > "$KMIA_ROOT/logs/ingestion/launch_all_master.nohup.log" 2>&1 &
echo "launch_all pid $!"
