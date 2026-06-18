#!/usr/bin/env bash
# Bootstrap KMIA ingest toolchain inside WSL on Legion5.
set -euo pipefail

ROOT="${KMIA_ROOT:-/mnt/e/KMIA_Ingest}"
SETUP="${KMIA_SETUP:-/mnt/e/KMIA_Setup}"

echo "=== Legion5 KMIA bootstrap ==="
echo "ROOT=$ROOT"

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl wget git ca-certificates unzip jq awscli \
  python3 python3-pip python3-venv \
  build-essential

mkdir -p "$ROOT"/{scripts,logs/ingestion,logs/smoke_tests,raw,processed,setup_repo/ingest/scripts}
mkdir -p "$ROOT/raw/forecast/ndfd_aws" "$ROOT/raw/observed/isd" "$ROOT/processed/points/station=KMIA"

# Symlink so NAS scripts work unchanged
if [ ! -e /data/KMIA_Ingest ]; then
  sudo mkdir -p /data
  sudo ln -sfn "$ROOT" /data/KMIA_Ingest
fi

# Python venv
if [ ! -x /opt/kmia-venv/bin/python3 ]; then
  sudo python3 -m venv /opt/kmia-venv
  sudo /opt/kmia-venv/bin/pip install --upgrade pip wheel
  sudo /opt/kmia-venv/bin/pip install \
    boto3 botocore pandas pyarrow matplotlib requests tqdm
fi

# Miniforge + wgrib2
MINIFORGE=/opt/miniforge3
if ! command -v wgrib2 >/dev/null 2>&1; then
  echo "Installing Miniforge + wgrib2..."
  curl -fsSL -o /tmp/miniforge.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  sudo bash /tmp/miniforge.sh -b -p "$MINIFORGE"
  sudo "$MINIFORGE/bin/mamba" install -y -c conda-forge wgrib2
  sudo ln -sf "$MINIFORGE/bin/wgrib2" /usr/local/bin/wgrib2
  rm -f /tmp/miniforge.sh
fi

export PATH="/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:${PATH}"

# Copy scripts from setup bundle
if [ -d "$SETUP/ingest/scripts" ]; then
  cp -f "$SETUP/ingest/scripts/"* "$ROOT/scripts/"
  cp -f "$SETUP/ingest/scripts/"* "$ROOT/setup_repo/ingest/scripts/"
  chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
fi

echo "=== Tool versions ==="
/opt/kmia-venv/bin/python3 --version
/opt/kmia-venv/bin/python3 -c "import pandas; print('pandas', pandas.__version__)"
wgrib2 -version 2>&1 | head -1
aws --version 2>&1 | head -1

echo "=== Smoke: ISD 2020 ==="
ISD_YEAR=2020 bash "$ROOT/scripts/11_isd_smoke_kmia.sh"

echo "LEGION5_BOOTSTRAP_OK"
