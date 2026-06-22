#!/bin/bash
# NAS container: Kalshi read-only API from /data/secrets (no Mac paths).
set -euo pipefail

if [ -f /data/secrets/kmia_paper_research.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /data/secrets/kmia_paper_research.env
  set +a
fi

export KALSHI_READ_ONLY_RSA_KEY_PATH="${KALSHI_READ_ONLY_RSA_KEY_PATH:-${KALSHI_PRIVATE_KEY_PATH:-/data/secrets/kalshi_private_key.pem}}"
export KALSHI_PRIVATE_KEY_PATH="${KALSHI_PRIVATE_KEY_PATH:-$KALSHI_READ_ONLY_RSA_KEY_PATH}"

if [ -n "${KALSHI_API_KEY_ID:-}" ] && [ -f "${KALSHI_READ_ONLY_RSA_KEY_PATH}" ]; then
  export KALSHI_USE_AUTH="${KALSHI_USE_AUTH:-true}"
else
  export KALSHI_USE_AUTH="${KALSHI_USE_AUTH:-false}"
fi

export KALSHI_API_BASE_URL="${KALSHI_API_BASE_URL:-https://api.elections.kalshi.com/trade-api/v2}"
