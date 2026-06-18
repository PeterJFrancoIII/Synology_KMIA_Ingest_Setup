#!/usr/bin/env bash
set -euo pipefail

ROOT="/volume2/Data/App_Development"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

echo "=== test_paths: all NAS absolute paths must start with $ROOT ==="

while IFS= read -r -d '' file; do
  while IFS= read -r line; do
    case "$line" in
      *"$ROOT"*) ;;
      *) continue ;;
    esac
    # Extract path-like tokens starting with /volume2
    for token in $(echo "$line" | grep -oE '/volume2[^ "'\''`]*' || true); do
      case "$token" in
        "$ROOT"*) ;;
        *)
          echo "BAD PATH in $file: $token"
          FAIL=1
          ;;
      esac
    done
  done < "$file"
done < <(find "$REPO_ROOT" -type f \( -name '*.sh' -o -name '*.yml' -o -name '*.yaml' -o -name '*.py' -o -name '*.md' -o -name '*.json' -o -name '*.example' -o -name '*.txt' \) -print0)

if [ "$FAIL" -ne 0 ]; then
  echo "test_paths FAILED"
  exit 1
fi

echo "test_paths PASSED"
