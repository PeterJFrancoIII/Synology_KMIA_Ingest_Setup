#!/bin/sh
# Cron install template — run manually after smoke tests pass.
# Do not schedule full historical backfill until smoke tests pass.

set -eu

CRON_FILE="/volume2/Data/App_Development/KMIA_Ingest/config/cron.example"

cat > "$CRON_FILE" << 'EOF'
# Recent NDFD forecast ingest (placeholder — create recent_ndfd.sh before enabling)
# */30 * * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/recent_ndfd.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/recent_ndfd.log 2>&1

# Daily station observation ingest
30 2 * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/isd_daily.log 2>&1

# Weekly gap audit
0 4 * * 0 docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/30_gap_audit.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/gap_audit.log 2>&1
EOF

echo "Cron template written to: $CRON_FILE"
echo "Install manually via DSM Task Scheduler or crontab after smoke tests pass."
