# Kalshi historical orderbook data request (draft)

**Use:** Email or support ticket to Kalshi data/partnerships team. Customize contact and dates before sending.

---

## Subject

Historical L2 orderbook data request — KXHIGHMIA temperature markets (research / liquidity study)

---

## Body

Hello Kalshi team,

We operate a **read-only research pipeline** for the **KXHIGHMIA** (Miami daily high temperature) market series. We use your public API for live orderbooks, candlesticks, and historical fills, and we maintain an internal archive aligned with your OpenAPI v3 schema.

**Gap:** The public API provides **current** orderbooks (`GET /markets/{ticker}/orderbook`) and **historical candlesticks/fills**, but not **full depth orderbook history** for settled markets prior to our WebSocket capture (started 2026-06-22). We cannot reconstruct maker-fill realism or liquidity caps for backtests before that date without vendor bulk data.

**Request:** Would Kalshi provide a bulk historical export for **KXHIGHMIA** with:

- All open bins per event day, from market open through settlement
- Timestamps in **UTC** (millisecond precision preferred)
- Full **yes/no bid ladders** (or orderbook_delta replayable format)
- **Closed/settled** markets included
- Delivery as **JSONL or Parquet** with a checksum manifest

**Our ingest endpoint:** We can receive large files via **SFTP** to our NAS (Synology). We will provide host, port, username, and SSH public key on request. Typical drop location:

`/inbound_from_vendor/` (write-only account, no access to trading credentials)

**Use case:** Academic-style market microstructure research and paper-trading simulation — **no live order placement**. We document our API consumption here: [internal field catalog from Kalshi OpenAPI v3.22.0].

**Volume estimate:** KXHIGHMIA ~12 bins/day; we expect sub-GB per month at 1-minute snapshot granularity.

If bulk L2 is not available, please advise the best supported alternative (e.g., historical tick/trade feed, increased candlestick resolution, or partner data program).

Thank you for considering this request.

[Your name]  
[Organization / project]  
[Contact email]

---

## Internal checklist before sending

- [ ] Provision SFTP user via `setup_kalshi_inbound_drop.sh` on MediaServer2
- [ ] Share credentials through secure channel (not email plaintext if avoidable)
- [ ] Confirm `KALSHI_INBOUND_DATA_CONTRACT.md` schema with vendor if they propose a different format
- [ ] Run `ingest_kalshi_vendor_orderbook_drop.py` on first test file before promoting to backtest
