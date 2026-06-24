# Kalshi data collection — what we pull and when to stop

**Updated:** 2026-06-22  
**Scope:** Console 2 + Kalshi read-only ingest. No order execution.

**API field reference:** [KALSHI_API_RESPONSE_FIELDS.md](KALSHI_API_RESPONSE_FIELDS.md) — every documented REST response field from Kalshi OpenAPI v3.22.0 (regenerate via `ingest/scripts/generate_kalshi_api_fields_doc.py`).

## What runs automatically

| Layer | Source | Frequency | Storage |
|-------|--------|-----------|---------|
| **WebSocket orderbooks (finest)** | `orderbook_delta` channel | Continuous (sub-second deltas) | **`kalshi_market_archive/orderbook_ws/YYYY-MM-DD.jsonl`** + **`orderbook_ws_snapshots/`** (60s checkpoints) |
| **Live orderbooks (REST fallback)** | `GET /markets/{ticker}/orderbook` | Every paper loop (~5 min, NAS) | `latest_kalshi_orderbooks.json` + **`kalshi_market_archive/orderbooks/YYYY-MM-DD.jsonl`** |
| **Live market metadata** | Discovery + selected KXHIGHMIA markets | Same | Timestamped JSON + **`kalshi_market_archive/markets/YYYY-MM-DD.jsonl`** |
| **Minute yes-ask CSV** | Candlesticks API | Daily policy refresh (2:30 AM ET, NAS) | `Kalshi - Miami Max Temp. Bet History/*.csv` |
| **Full candle JSONL** | Same candlesticks (bid/ask/volume/raw) | Daily policy refresh step 0b | `backend/data/processed/kalshi_candle_archive/*-candles.jsonl` |

Disable live archival: `KALSHI_ARCHIVE_ENABLED=false`.  
Disable WebSocket daemon: `KALSHI_WS_ENABLED=false` or stop `kmia-orderbook-ws` container.

### WebSocket orderbook daemon (NAS)

Long-running container `kmia-orderbook-ws` subscribes to Kalshi `orderbook_delta` for all open KXHIGHMIA bins.

| Env | Default | Purpose |
|-----|---------|---------|
| `KALSHI_WS_ENABLED` | `true` | Kill switch |
| `KALSHI_WS_SNAPSHOT_INTERVAL_SEC` | `60` | Full-book checkpoint interval |
| `KALSHI_WS_ARCHIVE_RAW_DELTAS` | `true` | Store every snapshot/delta event |

**Deploy:** `sudo docker compose up -d kmia-orderbook-ws` in `Docker/kmia-paper-research/`.  
**Health:** `kalshi_market_archive/ws_daemon_status.json`  
**WebSocket spec:** `docs/specs/kalshi_asyncapi.yaml`

Requires authenticated Kalshi API (`setup_nas_kalshi_secrets.sh`).

## Where files live

**Kalshi repo (live + archive):**

- `backend/data/processed/kalshi_market_snapshots/` — latest + timestamped snapshots
- `backend/data/processed/kalshi_market_archive/` — append-only JSONL (REST orderbooks, markets, **WS orderbook_ws/**)
- `backend/data/processed/kalshi_candle_archive/` — per-settlement full candle JSONL

**Console 2 backtest inputs:**

- Minute CSVs in Bet History folder (unchanged contract for policy optimizer)
- **`kalshi_market_archive/orderbooks/`** — REST maker-fill replay at prior-day **10 AM ET** anchor; **WS/vendor snapshots preferred** when closer (`kalshi_orderbook_archive_loader.py` → `scan_limit_fill`); falls back to minute CSV when archive missing or ask above limit
- **`kalshi_candle_archive/*-candles.jsonl`** — bid/ask/volume at anchor; maker fill fallback after orderbook (`kalshi_candle_archive_loader.py`)

Backtest CLI:

```bash
python3 ingest/scripts/historical_checksum_backtest.py --mode kalshi \
  --orderbook-archive-dir "../Kalshi/backend/data/processed/kalshi_market_archive"
```

## Manual backfill

```bash
# Full candle JSONL for missing settlement days
python3 ingest/scripts/kalshi_candle_archive.py --all-api-events

# Force re-archive one day
python3 ingest/scripts/kalshi_candle_archive.py --date 2026-06-19 --force

# Minute CSV + candle archive (NAS daily pipeline)
bash ingest/scripts/run_daily_policy_refresh.sh
```

Live orderbook archive runs inside `bash scripts/update_kalshi_market_data.sh` (paper loop).

---

## When to stop adding detail (profit-focused)

Goal: improve **P(profitable trade)** and **realistic maker fills**, not archive everything Kalshi exposes.

### Tier 1 — **Do now** (highest ROI)

1. **1-minute yes-ask path** (already have) — anchor pricing at 10 AM ET  
2. **Top-of-book + size** on live loop (already have) — liquidity caps  
3. **Orderbook snapshot archive** (new) — replay whether maker bids would fill  
4. **Full candle JSONL** (new) — bid/ask/volume for spread and slippage backtests  

**Stop here for v1 depth-aware backtest.** This is enough to replace fixed 25-contract caps with historical top-of-book when known.

### Tier 2 — **Add after ~60–90 days of archive** (if win rate still mis-predicted)

5. **Multi-level book ladders** when API returns them (not snapshot fallback)  
6. **Align live `integer_dist_v1` with backtest** (probability model parity)  
7. **Event volume / open interest time series** from market metadata archive  

### Tier 3 — **Optional / specialized**

8. ~~WebSocket delta books (sub-second)~~ **Active on NAS** (`kmia-orderbook-ws`); **10 AM backtest loader wired** (`kalshi_orderbook_archive_loader.py` reads `orderbook_ws_snapshots/` + `orderbook_vendor/`)  
9. Tick-level trade prints  
10. Cross-market arb / full exchange crawl  

Tiers 8–10 help HFT-style execution, not a once-per-day 10 AM ET weather bin strategy.

### Rule of thumb

| If this is wrong… | Add data… | Don't bother with… |
|-------------------|-----------|---------------------|
| Wrong bin / weather | NWS, NCEI, NDFD MAE | Order book |
| Wrong edge / P(bin) | Model parity, calibration | WebSocket |
| Wrong entry price | Minute ask + book archive | Tick data |
| Wrong size / fill | Top-of-book size + ladder archive | Full exchange LOB |
| Wrong day to trade | Policy gates, insurance sim | Latency microstructure |

---

## Trim later

- Compress JSONL older than 90 days to `.jsonl.gz` (include `orderbook_ws/`)  
- Drop `raw` candle payloads after validating flattened fields  
- Sample orderbook archive to 5-min if 15-min is sufficient for fill replay  

See also: `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md` (Kalshi price-history section).
