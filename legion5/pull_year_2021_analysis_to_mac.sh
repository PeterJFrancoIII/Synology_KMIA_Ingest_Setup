#!/usr/bin/env bash
# Pull analysis + rebuild local interactive chart suite.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STUDY="${1:-KMIA_NDFD_Year_MaxT_Precision_2021}"
YEAR="${2:-2021}"
DEST="$REPO/Research/Agent Analysis of KMIA Forecast Precision/${STUDY}"
mkdir -p "$DEST"

scp "Legion5:D:/KMIA_Process/analysis/${STUDY}/accuracy_points_enriched.csv" "$DEST/" 2>/dev/null || true
scp "Legion5:D:/KMIA_Process/analysis/${STUDY}/accuracy_report.md" "$DEST/" 2>/dev/null || true

python3 "$REPO/ingest/scripts/build_kmia_chart_suite.py" \
  --root "$REPO" \
  --study-name "$STUDY" \
  --year "$YEAR" \
  --analysis-dir "$DEST"

echo "Local suite: $DEST/kmia_chart_suite.html"
