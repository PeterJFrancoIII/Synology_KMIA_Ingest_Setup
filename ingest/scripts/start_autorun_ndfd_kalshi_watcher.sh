#!/usr/bin/env bash
# DEPRECATED — use Legion5 54b_autorun_ndfd_kalshi.sh (Mac = deploy only).
set -euo pipefail
echo "ERROR: start_autorun_ndfd_kalshi_watcher.sh must not run on Mac." >&2
echo "  ssh Legion5 \"C:\\Program Files\\Git\\bin\\bash.exe\" -lc \"nohup bash /d/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --watch 202604_202606 > /d/KMIA_Process/logs/autorun/watcher.nohup.log 2>&1 &\"" >&2
exit 1
