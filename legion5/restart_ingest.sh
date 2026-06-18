#!/usr/bin/env bash
set -euo pipefail
export KMIA_ROOT="/e/KMIA_Ingest"
export KMIA_PYTHON="/e/Miniforge3/python.exe"
export KMIA_PATH="/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2"
export PATH="$KMIA_PATH:$PATH"
cd "$KMIA_ROOT"
nohup bash "$KMIA_ROOT/scripts/03_legion5_year_pipeline.sh" 2020 >> "$KMIA_ROOT/logs/ingestion/legion5_year_2020.nohup.log" 2>&1 &
echo "started pid $!"
