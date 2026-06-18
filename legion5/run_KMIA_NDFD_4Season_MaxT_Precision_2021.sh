#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=kmia_legion5_env.sh
source "$(dirname "${BASH_SOURCE[0]}")/scripts/kmia_legion5_env.sh" 2>/dev/null || \
  source /d/KMIA_Process/scripts/kmia_legion5_env.sh
exec bash /d/KMIA_Process/scripts/42_kmia_4season_maxt_precision_analysis.sh
