#!/bin/bash
# Wrapper for pilot_ws_maker_replay.py — see script for usage.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/pilot_ws_maker_replay.py" "$@"
