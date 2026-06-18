#!/usr/bin/env bash
# Pull chart portal + all year chart suites from Legion5 to Mac Research folder.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${LEGION5_HOST:-Legion5}"
REMOTE="${KMIA_REMOTE:-D:/KMIA_Process}"
DEST="$REPO/Research/Agent Analysis of KMIA Forecast Precision"

mkdir -p "$DEST"

echo "=== Pull chart portal ==="
scp -r "${HOST}:${REMOTE}/analysis/KMIA_Chart_Portal" "$DEST/" 2>/dev/null || true

for y in 2020 2021 2022 2023 2024 2025; do
  study="KMIA_NDFD_Year_MaxT_Precision_${y}"
  remote="${HOST}:${REMOTE}/analysis/${study}"
  local="$DEST/${study}"
  if ssh "$HOST" "test -f ${REMOTE}/analysis/${study}/accuracy_points_enriched.csv" 2>/dev/null; then
    echo "=== Pull $study ==="
    mkdir -p "$local"
    scp "${remote}/accuracy_points_enriched.csv" "${remote}/accuracy_report.md" \
      "${remote}/kmia_chart_suite.html" "${remote}/chart_suite_manifest.json" \
      "$local/" 2>/dev/null || true
    # Rebuild locally if HTML missing
    if [ ! -f "$local/kmia_chart_suite.html" ] && [ -f "$local/accuracy_points_enriched.csv" ]; then
      python3 "$REPO/ingest/scripts/build_kmia_chart_suite.py" \
        --root "$REPO" --study-name "$study" --year "$y" --analysis-dir "$local"
    fi
  fi
done

all_study="KMIA_NDFD_AllYears_MaxT_Precision"
if ssh "$HOST" "test -f ${REMOTE}/analysis/${all_study}/accuracy_points_enriched.csv" 2>/dev/null; then
  mkdir -p "$DEST/${all_study}"
  scp "${HOST}:${REMOTE}/analysis/${all_study}/"* "$DEST/${all_study}/" 2>/dev/null || true
fi

# Refresh local portal from pulled studies
python3 "$REPO/ingest/scripts/build_kmia_chart_portal.py" \
  --root "$DEST" --analysis-dir "$DEST" --skip-build

echo ""
echo "Open portal: $DEST/KMIA_Chart_Portal/kmia_chart_portal.html"
echo "Or per-year: $DEST/KMIA_NDFD_Year_MaxT_Precision_2021/kmia_chart_suite.html"
