#!/bin/bash
# Provision Kalshi vendor SFTP drop zone on Synology NAS (operator-run on MediaServer2).
# Does NOT create passwords — prints DSM steps only. No secrets in git.
#
# Usage (on NAS as admin):
#   sudo bash synology/scripts/setup_kalshi_inbound_drop.sh
#
# Or from Mac:
#   ssh MediaServer2 'sudo bash -s' < synology/scripts/setup_kalshi_inbound_drop.sh

set -euo pipefail

KALSHI_ROOT="${KALSHI_ROOT:-/volume2/Data/App_Development/Kalshi}"
INBOUND="${KALSHI_ROOT}/inbound_from_vendor"
QUARANTINE="${INBOUND}/quarantine"
ARCHIVE_VENDOR="${KALSHI_ROOT}/backend/data/processed/kalshi_market_archive/orderbook_vendor"
DSM_USER="${KALSHI_INBOUND_USER:-kalshi_inbound}"

echo "=== Kalshi inbound drop zone setup ==="
echo "KALSHI_ROOT=$KALSHI_ROOT"

mkdir -p "$INBOUND" "$QUARANTINE" "$ARCHIVE_VENDOR"
chmod 750 "$INBOUND" "$QUARANTINE"
chmod 755 "$ARCHIVE_VENDOR"

echo "Created:"
echo "  $INBOUND          (vendor write-only target)"
echo "  $QUARANTINE       (validator quarantine)"
echo "  $ARCHIVE_VENDOR   (promoted checkpoints)"

cat <<EOF

--- DSM operator steps (manual) ---

1. Control Panel → User & Group → Create user: ${DSM_USER}
   - Strong password via secure channel (NOT stored in git)
   - Disable all applications except SFTP if available

2. Control Panel → File Services → SFTP
   - Enable SFTP service
   - Restrict ${DSM_USER} home if using chroot; preferred: shared folder ACL only

3. Shared Folder permissions (File Station or ACL):
   - ${DSM_USER}: WRITE to ${INBOUND} only
   - NO read access to Kalshi secrets, trading keys, or trading_policy.json
   - NO write outside inbound + quarantine

4. Optional: mount inbound as WebDAV instead of SFTP (less preferred for bulk)

5. After first vendor test file lands:
   python3 ingest/scripts/ingest_kalshi_vendor_orderbook_drop.py \\
     --inbound-dir ${INBOUND} \\
     --archive-dir ${KALSHI_ROOT}/backend/data/processed/kalshi_market_archive

6. Contract doc: docs/ops/KALSHI_INBOUND_DATA_CONTRACT.md
   Outreach template: docs/ops/KALSHI_VENDOR_DATA_REQUEST.md

=== setup complete (directories only) ===
EOF
