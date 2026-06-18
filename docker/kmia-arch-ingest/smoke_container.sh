#!/usr/bin/env bash
set -euo pipefail

echo "=== KMIA Ingest Container Smoke ==="
echo "Date: $(date -u)"
echo

echo "=== Mount ==="
if [ ! -d /data/KMIA_Ingest ]; then
  echo "FAIL: /data/KMIA_Ingest not mounted"
  exit 1
fi
echo "OK: /data/KMIA_Ingest exists"
ls -la /data | head -20
echo

echo "=== Python ==="
export PATH="/opt/kmia-venv/bin:${PATH}"
python --version
pip --version
echo

echo "=== AWS CLI ==="
aws --version
echo

echo "=== CDO / NCO / eccodes ==="
cdo -V 2>&1 | head -1 || echo "cdo not found"
ncks --version 2>&1 | head -1 || echo "ncks not found"
grib_ls --version 2>&1 | head -1 || echo "grib_ls not found"
echo

echo "=== wgrib2 ==="
if command -v wgrib2 >/dev/null 2>&1; then
  wgrib2 -version 2>&1 | head -1
else
  echo "wgrib2 missing — install before full point extraction"
  python -c "import cfgrib, eccodes; print('cfgrib/eccodes OK')" 2>/dev/null || echo "cfgrib/eccodes import failed"
fi

echo
echo "=== Station Config ==="
if [ -f /data/KMIA_Ingest/config/kmia_station.json ]; then
  cat /data/KMIA_Ingest/config/kmia_station.json
else
  echo "WARN: kmia_station.json not found yet"
fi

echo
echo "Container smoke check complete."
