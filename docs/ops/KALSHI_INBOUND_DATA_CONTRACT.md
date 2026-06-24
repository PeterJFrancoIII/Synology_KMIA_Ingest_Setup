# Kalshi vendor inbound data contract

**Version:** 1.0  
**Updated:** 2026-06-23  
**Mode:** Read-only ingest — no order execution

---

## Purpose

Receive bulk historical Kalshi orderbook dumps (L2 / deltas / snapshots) that the public API does not provide for settled markets. Files land on NAS via SFTP; Console 2 validates and merges into the research archive.

---

## Inbound path (NAS)

| Path | Access |
|------|--------|
| `/volume2/Data/App_Development/Kalshi/inbound_from_vendor/` | Write-only DSM user `kalshi_inbound` (human-provisioned) |
| `.../inbound_from_vendor/quarantine/` | Validator staging (no direct reads by backtest) |
| `.../kalshi_market_archive/orderbook_vendor/` | Promoted JSONL after validation |

Setup (operator, on NAS): [`synology/scripts/setup_kalshi_inbound_drop.sh`](../../synology/scripts/setup_kalshi_inbound_drop.sh)

---

## Requested dataset scope

| Field | Requirement |
|-------|-------------|
| **Series** | `KXHIGHMIA` (all temperature bins) |
| **Period** | Market open → settlement per event day (earliest available → present) |
| **Granularity** | Preferred: `orderbook_delta` or full L2 snapshots; minimum: 1-minute bid/ask/size per level |
| **Closed markets** | Required (WS cannot subscribe after close) |
| **Timezone** | UTC timestamps with millisecond precision preferred |
| **Format** | JSONL (one record per line) or Parquet; gzip optional |
| **Manifest** | `manifest.json` per drop: file list, SHA-256, row counts, date range |

### Record schema (JSONL)

```json
{
  "ticker": "KXHIGHMIA-26APR20-B83.5",
  "event_ticker": "KXHIGHMIA-26APR20",
  "snapshot_at_utc": "2026-04-19T14:02:15.123Z",
  "yes_bids": [[18, 120.0]],
  "no_bids": [[75, 80.0]],
  "source": "kalshi_vendor_bulk",
  "schema_version": "1.0"
}
```

- `yes_bids` / `no_bids`: `[[price_cents, size], ...]` best-first (same as REST archive)
- Optional: `trades` array for tick replay (future)

---

## Validation (automated)

Run after each vendor drop:

```bash
python3 ingest/scripts/ingest_kalshi_vendor_orderbook_drop.py \
  --inbound-dir /volume2/Data/App_Development/Kalshi/inbound_from_vendor \
  --archive-dir /volume2/Data/App_Development/Kalshi/backend/data/processed/kalshi_market_archive
```

Validator:
1. Verifies `manifest.json` checksums
2. Rejects non-KXHIGHMIA tickers
3. Quarantines malformed lines
4. Appends to `orderbook_vendor/YYYY-MM-DD.jsonl`
5. Writes `orderbook_vendor/ingest_report_<stamp>.json`

---

## Security

- Credentials for `kalshi_inbound` **never** in git
- Vendor user: write-only to `inbound_from_vendor/`; no read of secrets or trading keys
- Quarantine retained 30 days before purge (operator policy)

---

## Related docs

- Outreach template: [`KALSHI_VENDOR_DATA_REQUEST.md`](KALSHI_VENDOR_DATA_REQUEST.md)
- API fields we already consume: [`../architecture/KALSHI_API_RESPONSE_FIELDS.md`](../architecture/KALSHI_API_RESPONSE_FIELDS.md)
- Live WS ingest: [`../architecture/KALSHI_WS_ORDERBOOK_INGEST.md`](../architecture/KALSHI_WS_ORDERBOOK_INGEST.md)
