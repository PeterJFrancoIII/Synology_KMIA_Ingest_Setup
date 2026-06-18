#!/usr/bin/env bash
# Mac/local: build chart suite from synced analysis folder.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STUDY="${1:-KMIA_NDFD_Year_MaxT_Precision_2021}"
YEAR="${2:-2021}"
ANALYSIS="$REPO/Research/Agent Analysis of KMIA Forecast Precision/${STUDY}"

FORECAST="${KMIA_FORECAST_CSV:-}"
OBS="${KMIA_OBS_CSV:-}"
EXTRA=()
if [ -n "$FORECAST" ]; then EXTRA+=(--forecast "$FORECAST"); fi
if [ -n "$OBS" ]; then EXTRA+=(--obs "$OBS"); fi

python3 "$REPO/ingest/scripts/build_kmia_chart_suite.py" \
  --root "$REPO" \
  --study-name "$STUDY" \
  --year "$YEAR" \
  --analysis-dir "$ANALYSIS" \
  "${EXTRA[@]}"

open "$ANALYSIS/kmia_chart_suite.html" 2>/dev/null || true
