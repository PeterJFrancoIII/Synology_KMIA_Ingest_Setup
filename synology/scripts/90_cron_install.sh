#!/bin/bash
# NAS cron: write template + optionally activate paper loop in /etc/crontab.
#
# Usage:
#   NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh
#   NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh --activate-paper-loop
#   NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh --activate-policy-pipeline
#   NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh --activate-all

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2Local}"
CRON_FILE="/volume2/Data/App_Development/KMIA_Ingest/config/cron.example"
LOG_DIRS="/volume2/Data/App_Development/logs/paper_research /volume2/Data/App_Development/logs/paper_trading"
ACTIVATE_PAPER=0
ACTIVATE_POLICY=0
for arg in "$@"; do
  case "$arg" in
    --activate-paper-loop) ACTIVATE_PAPER=1 ;;
    --activate-policy-pipeline) ACTIVATE_POLICY=1 ;;
    --activate-all) ACTIVATE_PAPER=1; ACTIVATE_POLICY=1 ;;
  esac
done

CRON_BODY='# Recent NDFD forecast ingest (placeholder — create recent_ndfd.sh before enabling)
# */30 * * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/recent_ndfd.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/recent_ndfd.log 2>&1

# Daily station observation ingest
30 2 * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/isd_daily.log 2>&1

# Weekly gap audit
0 4 * * 0 docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/30_gap_audit.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/gap_audit.log 2>&1

# Daily Kalshi policy research (~2:30 AM ET — after NCEI CLIMIA TMAX ~2 AM publish)
30 2 * * * docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh >> /volume2/Data/App_Development/logs/paper_research/cron.log 2>&1

# Paper trading loop every 15 minutes (Console 3 — NAS only)
*/15 * * * * docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh >> /volume2/Data/App_Development/logs/paper_trading/cron.log 2>&1'

echo "=== Install NAS cron template on $NAS ==="

ssh "$NAS" "sudo mkdir -p $LOG_DIRS /volume2/Data/App_Development/KMIA_Ingest/config"

printf '%s\n' "$CRON_BODY" | ssh "$NAS" "sudo tee $CRON_FILE > /dev/null"

echo "Cron template written on NAS: $CRON_FILE"

if [ "$ACTIVATE_PAPER" -eq 1 ]; then
  echo "=== Activating 15-min paper loop in /etc/crontab ==="
  ssh "$NAS" "sudo sh -c '
    set -e
    mkdir -p /volume2/Data/App_Development/logs/paper_trading
    if grep -q \"KMIA Paper Loop\" /etc/crontab; then
      echo ALREADY_ACTIVE
    else
      echo \"# KMIA Paper Loop (Console 3)\" >> /etc/crontab
      echo \"*/15 * * * * root /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh >> /volume2/Data/App_Development/logs/paper_trading/cron.log 2>&1\" >> /etc/crontab
      echo INSTALLED
    fi
    tail -3 /etc/crontab
  '"
fi

if [ "$ACTIVATE_POLICY" -eq 1 ]; then
  echo "=== Activating daily policy research in /etc/crontab (2:30 AM local — after NCEI CLIMIA) ==="
  ssh "$NAS" "sudo sh -c '
    set -e
    mkdir -p /volume2/Data/App_Development/logs/paper_research
    sed -i \"/KMIA Policy Research/,+1d\" /etc/crontab
    echo \"# KMIA Policy Research (Console 2 daily — after NCEI CLIMIA ~2 AM EST)\" >> /etc/crontab
    echo \"30 2 * * * root /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh >> /volume2/Data/App_Development/logs/paper_research/cron.log 2>&1\" >> /etc/crontab
    grep KMIA /etc/crontab
  '"
fi

cat <<'EOF'

Active jobs (when flags used): /etc/crontab as root, full docker path.
  Paper loop:   */15 min
  Policy pipe:  02:30 daily (after NCEI CLIMIA TMAX ~2 AM EST publish)

Runtime placement:
  NAS  — ingest, policy research, paper loop (kmia-arch-ingest + kmia-paper-research)
  Legion5 — GRIB extract, MAE charts only
  Mac — deploy scripts + human policy approval only (no launchd paper loop)

EOF
