#!/usr/bin/env bash
# Smoke test for kmia-paper-research (Arch Linux — same basis as kmia-arch-ingest)
set -euo pipefail

export PATH="/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

echo "=== KMIA Paper Research Container Smoke ==="
echo "Date: $(date -u)"
echo

echo "=== Mount ==="
if [ ! -d /data/KMIA_Ingest ] && [ ! -d /data/Kalshi ]; then
  echo "FAIL: /data not mounted"
  exit 1
fi
echo "OK: /data mount present"
ls -la /data | head -20
echo

echo "=== Python venv ==="
python --version
python -c "import pandas, requests; print('OK: pandas + requests')"
echo

CONSOLE2="${CONSOLE2_ROOT:-/data/KMIA_Ingest/setup_repo}"
KALSHI="${KMIA_KALSHI_ROOT:-/data/Kalshi}"

echo "=== Console 2 scripts ==="
if [ -d "$CONSOLE2/ingest/scripts" ]; then
  echo "OK: $CONSOLE2/ingest/scripts"
else
  echo "WARN: $CONSOLE2/ingest/scripts missing — deploy setup_repo to NAS"
fi

echo "=== Kalshi layout ==="
for d in "$KALSHI/backend/src" "$KALSHI/scripts" "$KALSHI/backend/data/research"; do
  if [ -d "$d" ]; then
    echo "OK: $d"
  else
    echo "WARN: missing $d"
  fi
done

if [ -x /usr/local/bin/run_nas_paper_loop.sh ]; then
  echo "OK: run_nas_paper_loop.sh"
else
  echo "WARN: run_nas_paper_loop.sh missing — rebuild container"
fi

if [ -x "$KALSHI/scripts/kmia_resolve_python.sh" ]; then
  # shellcheck disable=SC1091
  source "$KALSHI/scripts/kmia_resolve_python.sh"
  echo "OK: kmia_resolve_python -> $(kmia_resolve_python "$KALSHI")"
fi

export PYTHONPATH="$CONSOLE2/ingest/scripts:$KALSHI/backend/src"
if [ -f "$CONSOLE2/ingest/scripts/kmia_kalshi_paths.py" ]; then
  python -c "from kmia_kalshi_paths import kalshi_research_dir; print('OK: paths', kalshi_research_dir())"
fi

echo
echo "Container smoke check complete."
