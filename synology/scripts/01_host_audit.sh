#!/bin/sh
set -eu

ROOT="/volume2/Data/App_Development"

echo "=== HOST ==="
hostname
date
uname -a

echo

echo "=== VOLUMES ==="
df -h

echo

echo "=== PROJECT ROOT ==="
du -sh "$ROOT" 2>/dev/null || true
find "$ROOT" -maxdepth 3 -type d 2>/dev/null | sort

echo

echo "=== DOCKER ==="
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true
else
  echo "docker not found in PATH"
fi
