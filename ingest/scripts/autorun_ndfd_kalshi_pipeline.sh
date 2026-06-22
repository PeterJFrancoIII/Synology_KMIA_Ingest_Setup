#!/usr/bin/env bash
# DEPRECATED — research runs on Legion5 or MediaServer2Local only. Mac = deploy only.
set -euo pipefail
echo "ERROR: autorun_ndfd_kalshi_pipeline.sh must not run on Mac." >&2
echo "  Legion5: bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --watch JOB_TAG" >&2
echo "  NAS:     sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh" >&2
exit 1
