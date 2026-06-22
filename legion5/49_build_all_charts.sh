#!/usr/bin/env bash
# Build chart suites for all completed studies + multi-year portal.
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"

for y in 2020 2021 2022 2023 2024 2025; do
  study="KMIA_NDFD_Year_MaxT_Precision_${y}"
  enriched="$ROOT/analysis/${study}/accuracy_points_enriched.csv"
  if [ -f "$enriched" ]; then
    echo "=== chart suite $study ==="
    bash "$SCRIPTS/47_build_kmia_chart_suite.sh" "$study" "$y" || echo "WARN $study"
  fi
done

all_study="KMIA_NDFD_AllYears_MaxT_Precision"
if ls "$ROOT/analysis"/KMIA_NDFD_Year_MaxT_Precision_*/accuracy_points_enriched.csv >/dev/null 2>&1; then
  echo "=== rebuild AllYears from yearly studies ==="
  bash "$SCRIPTS/50_rebuild_all_years_study.sh" || echo "WARN AllYears rebuild"
elif [ -f "$ROOT/analysis/${all_study}/accuracy_points_enriched.csv" ]; then
  bash "$SCRIPTS/47_build_kmia_chart_suite.sh" "$all_study" "2020" || echo "WARN $all_study"
fi

"$PYTHON" "$SCRIPTS/build_kmia_chart_portal.py" --root "$ROOT"
echo "Portal: $ROOT/analysis/KMIA_Chart_Portal/kmia_chart_portal.html"
