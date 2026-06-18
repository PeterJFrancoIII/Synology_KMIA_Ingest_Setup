#!/usr/bin/env bash
set -euo pipefail
export KMIA_ROOT="/e/KMIA_Ingest"
export KMIA_PYTHON="/e/Miniforge3/python.exe"
export KMIA_PATH="/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2"
export PATH="$KMIA_PATH:$PATH"
ROOT="$KMIA_ROOT"
mkdir -p "$ROOT/logs/ingestion" "$ROOT/logs/smoke_tests" "$ROOT/raw/observed/isd/2020" "$ROOT/processed/points/station=KMIA/monthly/2020"
cd "$ROOT"
echo "=== ISD smoke ==="
ISD_YEAR=2020 KMIA_ROOT="$KMIA_ROOT" KMIA_PYTHON="$KMIA_PYTHON" bash "$ROOT/scripts/11_isd_smoke_kmia.sh"
echo "=== Starting year pipeline ==="
nohup bash "$ROOT/scripts/03_legion5_year_pipeline.sh" 2020 > "$ROOT/logs/ingestion/legion5_year_2020.nohup.log" 2>&1 &
sleep 4
tail -20 "$ROOT/logs/ingestion/legion5_year_2020_pipeline.log" 2>/dev/null || tail -10 "$ROOT/logs/ingestion/legion5_year_2020.nohup.log"
