# Handoff — Kalshi WebSocket orderbook ingest (2026-06-22)

## MISSION

Deploy finest-granularity Kalshi orderbook archival on NAS for KXHIGHMIA research (read-only).

## STATE

- **Done:** WebSocket daemon implemented (Kalshi repo), NAS container `kmia-orderbook-ws` deployed and running on MediaServer2.
- **Verified:** 12 tickers subscribed; `orderbook_ws/2026-06-22.jsonl` growing; heartbeat `connected: true`.
- **Fallback:** REST 5-min orderbook archive in paper loop unchanged.

## DESIGN (summary)

See full spec: `docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md`

| Layer | Resolution | Path |
|-------|------------|------|
| WS raw events | Sub-second deltas | `kalshi_market_archive/orderbook_ws/` |
| WS checkpoints | 60s full book | `kalshi_market_archive/orderbook_ws_snapshots/` |
| REST fallback | 5 min | `kalshi_market_archive/orderbooks/` |

Code: Kalshi `backend/src/market_data/orderbook_ws_*.py` + `kalshi_ws_client.py`.

## OPERATOR COMMANDS

```bash
NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
# rebuild compose on NAS, then:
sudo docker compose up -d kmia-orderbook-ws
python3 ingest/scripts/kalshi_archive_status.py
```

## NEXT

1. Let archive accumulate 7–14 days.
2. Extend `kalshi_orderbook_archive_loader.py` to prefer WS snapshots at 10 AM ET anchor.
3. Human re-approval of taker policy draft (separate track).
