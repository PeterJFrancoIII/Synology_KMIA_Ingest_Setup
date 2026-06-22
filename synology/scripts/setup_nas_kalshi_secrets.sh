#!/bin/bash
# Copy Kalshi read-only credentials from Mac to NAS (red zone — secrets only).
#
# Prereq: Developer_API_Keys.env + PEM in Kalshi API Keys folder
#   bash "/path/to/Kalshi/scripts/setup_kalshi_api_credentials.sh"
#
# Usage:
#   NAS_HOST=MediaServer2Local ./synology/scripts/setup_nas_kalshi_secrets.sh

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2Local}"
KALSHI_ROOT="${KALSHI_ROOT:-$HOME/Desktop/App Development/Kalshi}"
API_DIR="$KALSHI_ROOT/1_Downloads/API Keys & Dcoumentation"
DEV_ENV="$API_DIR/Developer_API_Keys.env"
NAS_SECRETS="App Development/secrets"

if [ ! -f "$DEV_ENV" ]; then
  echo "ERROR: Run Kalshi/scripts/setup_kalshi_api_credentials.sh first"
  exit 1
fi

# shellcheck disable=SC1090
source "$DEV_ENV"

if [ -z "${KALSHI_READ_ONLY_RSA_KEY_PATH:-}" ] || [ ! -f "${KALSHI_READ_ONLY_RSA_KEY_PATH}" ]; then
  echo "ERROR: RSA key file missing: ${KALSHI_READ_ONLY_RSA_KEY_PATH:-unset}"
  exit 1
fi

ssh "$NAS" "mkdir -p '$NAS_SECRETS'"
KEY_FILE="${KALSHI_READ_ONLY_RSA_KEY_PATH}"
# Synology disables scp subsystem — use ssh + cat
ssh "$NAS" "cat > '$NAS_SECRETS/kalshi_private_key.pem'" < "${KEY_FILE}"
ssh "$NAS" "chmod 600 '$NAS_SECRETS/kalshi_private_key.pem'"

ssh "$NAS" "cat > '$NAS_SECRETS/kmia_paper_research.env'" <<EOF
KALSHI_API_KEY_ID=${KALSHI_API_KEY_ID}
KALSHI_PRIVATE_KEY_PATH=/data/secrets/kalshi_private_key.pem
KALSHI_USE_AUTH=true
KALSHI_API_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
EOF

ssh "$NAS" "chmod 600 '$NAS_SECRETS/kmia_paper_research.env' '$NAS_SECRETS/kalshi_private_key.pem'"

echo "NAS secrets installed at ~/$NAS_SECRETS/"
echo "Restart pipeline: sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh"
