#!/usr/bin/env bash
# Rebuild KMIA_NDFD_AllYears_MaxT_Precision from completed per-year studies.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
ANALYSIS="$ROOT/analysis"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"

echo "=== Rebuild AllYears from yearly enriched CSVs ==="
"$PYTHON" "$SCRIPTS/merge_all_years_enriched.py" \
  --analysis-dir "$ANALYSIS" \
  --years 2020 2021 2022 2023 2024 2025 \
  --python "$PYTHON" \
  --rebuild-chart

echo "=== Refresh chart portal ==="
"$PYTHON" "$SCRIPTS/build_kmia_chart_portal.py" --root "$ROOT"
echo "Done: $ANALYSIS/KMIA_NDFD_AllYears_MaxT_Precision/kmia_chart_suite.html"
