#!/usr/bin/env bash
# Benchmark Legion5 <-> NAS transfer (one day of GRIB).
set -euo pipefail
HOST="${NAS_SSH_HOST:-nas-local}"
REMOTE="/volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2021/04/01"
DEST="/d/KMIA_Process/raw/bench_test"
mkdir -p "$DEST"
rm -rf "$DEST"/* 2>/dev/null || true

bench() {
  local label="$1" compress="$2"
  rm -rf "$DEST"/* 2>/dev/null || true
  local start end secs bytes
  start=$(date +%s)
  if [ "$compress" = "yes" ]; then
    ssh "$HOST" "tar czf - -C '$REMOTE' ." | tar xzf - -C "$DEST"
  else
    ssh "$HOST" "tar cf - -C '$REMOTE' ." | tar xf - -C "$DEST"
  fi
  end=$(date +%s)
  secs=$((end - start))
  bytes=$(find "$DEST" -type f -exec stat -c%s {} + 2>/dev/null | awk '{s+=$1} END{print s+0}')
  if [ "$secs" -lt 1 ]; then secs=1; fi
  mb=$(echo "scale=1; $bytes / 1048576" | bc)
  mbps=$(echo "scale=1; $mb / $secs" | bc)
  echo "$label: ${mb} MB in ${secs}s = ${mbps} MB/s"
}

echo "=== NAS connection benchmark $(date -u) ==="
echo "Host: $HOST"
ping -n 2 192.168.0.193 | tail -1
bench "tar.gz (compressed)" yes
bench "tar (uncompressed LAN)" no
echo "=== done ==="
