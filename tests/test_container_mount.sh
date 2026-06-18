#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$REPO_ROOT/docker/kmia-arch-ingest/docker-compose.yml"

echo "=== test_container_mount ==="

if [ ! -f "$COMPOSE" ]; then
  echo "FAIL: docker-compose.yml not found at $COMPOSE"
  exit 1
fi

if grep -q '/volume2/Data/App_Development:/data' "$COMPOSE"; then
  echo "test_container_mount PASSED"
  exit 0
fi

echo "FAIL: compose must mount /volume2/Data/App_Development:/data"
exit 1
