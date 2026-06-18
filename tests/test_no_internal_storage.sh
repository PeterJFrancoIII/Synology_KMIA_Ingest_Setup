#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$REPO_ROOT/docker/kmia-arch-ingest/docker-compose.yml"
FAIL=0

echo "=== test_no_internal_storage ==="

# Fail if compose uses anonymous or named volumes for persistent data instead of /data mount
if grep -qE '^\s+- [a-zA-Z_][a-zA-Z0-9_]*:/' "$COMPOSE" 2>/dev/null; then
  if ! grep -q '/volume2/Data/App_Development:/data' "$COMPOSE"; then
    echo "FAIL: compose may use internal/named volumes without /data NAS mount"
    FAIL=1
  fi
fi

# Fail if scripts write to container-only paths without /data prefix
for script in "$REPO_ROOT"/ingest/scripts/*.sh; do
  if grep -qE '(^|[^/])/tmp/KMIA_Ingest|/var/lib/kmia' "$script" 2>/dev/null; then
    echo "FAIL: $script uses container-internal persistent path"
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo "test_no_internal_storage FAILED"
  exit 1
fi

echo "test_no_internal_storage PASSED"
