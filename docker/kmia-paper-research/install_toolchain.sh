#!/bin/bash
set -euo pipefail

# Python venv for Console 2 policy research (backtest, price ingest, MAE export).
python -m venv /opt/kmia-venv
/opt/kmia-venv/bin/pip install --upgrade pip wheel
/opt/kmia-venv/bin/pip install \
  pandas \
  requests \
  python-dateutil \
  pydantic \
  beautifulsoup4 \
  pyyaml \
  websockets

echo 'export PATH="/opt/kmia-venv/bin:${PATH}"' > /etc/profile.d/kmia-venv.sh

/opt/kmia-venv/bin/python -c "import pandas, requests, pydantic; print('kmia venv OK')"
