#!/bin/sh
set -eu

ROOT="/volume2/Data/App_Development"
FAIL=0

check_writable() {
  path="$1"
  if [ ! -d "$path" ]; then
    echo "MISSING: $path"
    FAIL=1
    return
  fi
  testfile="$path/.write_test_$$"
  if touch "$testfile" 2>/dev/null; then
    rm -f "$testfile"
    echo "OK (writable): $path"
  else
    echo "NOT WRITABLE: $path"
    FAIL=1
  fi
}

echo "=== PERMISSIONS CHECK ==="
check_writable "$ROOT"
check_writable "$ROOT/KMIA_Ingest"
check_writable "$ROOT/KMIA_Ingest/raw"
check_writable "$ROOT/KMIA_Ingest/processed"
check_writable "$ROOT/KMIA_Ingest/manifest"
check_writable "$ROOT/KMIA_Ingest/logs"
check_writable "$ROOT/Docker/kmia-arch-ingest"
check_writable "$ROOT/Scripts"

if [ "$FAIL" -ne 0 ]; then
  echo "Permissions check FAILED"
  exit 1
fi

echo "Permissions check PASSED"
