#!/usr/bin/env bash
# Repeatable chart suite: golden-master PNG + unified HTML dashboard.
# Usage: 47_build_kmia_chart_suite.sh STUDY_NAME YEAR
set -euo pipefail

STUDY="${1:?STUDY_NAME required}"
YEAR="${2:?YEAR required}"
ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"
export KMIA_ROOT="$ROOT" KMIA_PYTHON="$PYTHON"

"$PYTHON" "$SCRIPTS/build_kmia_chart_suite.py" \
  --root "$ROOT" \
  --study-name "$STUDY" \
  --year "$YEAR" \
  --python "$PYTHON"

ANALYSIS="$ROOT/analysis/${STUDY}"
echo "Open: $ANALYSIS/kmia_chart_suite.html"
