#!/bin/bash
set -euo pipefail

# Python venv for manifest/gap tooling and cfgrib research fallback.
python -m venv /opt/kmia-venv
/opt/kmia-venv/bin/pip install --upgrade pip wheel
/opt/kmia-venv/bin/pip install \
  boto3 botocore pandas pyarrow duckdb xarray cfgrib eccodes \
  requests beautifulsoup4 lxml tqdm

echo 'export PATH="/opt/kmia-venv/bin:${PATH}"' > /etc/profile.d/kmia-venv.sh

# wgrib2 is not in Arch pacman; conda-forge matches the proven VPS install path.
MINIFORGE=/opt/miniforge3
if ! command -v wgrib2 >/dev/null 2>&1; then
  echo "Installing Miniforge + wgrib2 from conda-forge..."
  curl -fsSL -o /tmp/miniforge.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  bash /tmp/miniforge.sh -b -p "$MINIFORGE"
  "$MINIFORGE/bin/mamba" install -y -c conda-forge wgrib2
  ln -sf "$MINIFORGE/bin/wgrib2" /usr/local/bin/wgrib2
  rm -f /tmp/miniforge.sh
fi

echo 'export PATH="/opt/miniforge3/bin:/usr/local/bin:${PATH}"' > /etc/profile.d/kmia-wgrib2.sh

if command -v wgrib2 >/dev/null 2>&1; then
  echo "wgrib2 found: $(wgrib2 -version 2>&1 | head -1)"
else
  echo "wgrib2 install failed"
  exit 1
fi
