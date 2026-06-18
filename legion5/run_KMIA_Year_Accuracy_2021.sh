#!/usr/bin/env bash
# Launch full-year 2021 accuracy analysis in background (Apr–Dec on NAS).
set -euo pipefail
export KMIA_YEAR=2021
export KMIA_FIRST_MONTH=4
export KMIA_LAST_MONTH=12
export KMIA_EXTRACT_WORKERS=8
source /d/KMIA_Process/scripts/kmia_legion5_env.sh
STUDY_ID="KMIA_NDFD_Year_MaxT_Precision_2021"
LOG="/d/KMIA_Process/logs/processing/${STUDY_ID}.nohup.log"
mkdir -p /d/KMIA_Process/logs/processing
nohup bash /d/KMIA_Process/scripts/45_kmia_year_maxt_precision_analysis.sh >>"$LOG" 2>&1 &
echo "started pid $! log=$LOG"
echo "monitor: tail -f $LOG"
echo "done when: /d/KMIA_Process/analysis/${STUDY_ID}/COMPLETE.txt exists"
