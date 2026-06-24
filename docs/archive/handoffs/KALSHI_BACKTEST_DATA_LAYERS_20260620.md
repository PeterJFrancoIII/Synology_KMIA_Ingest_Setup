# Handoff: Kalshi backtest data layers

**Date:** 2026-06-20  
**Console:** 2 (Weather Ingest & MAE Probabilities)  
**Scope:** Read-only backtest / policy research — no order execution

---

## Purpose

Console 2 replays KMIA max-temperature Kalshi markets at the **prior-day 10 AM ET** anchor (when bins open). Multiple data layers stack from coarse to fine; each layer is optional except minute CSV for v1.

---

## Data layer stack (priority order)

| Layer | Path | Anchor use | Backtest module |
|-------|------|------------|-----------------|
| **1. Minute CSV** | `Kalshi - Miami Max Temp. Bet History/*.csv` | Yes-ask cents at/open after 10 AM | `kalshi_price_history_loader.prices_at_anchor()` |
| **2. Orderbook JSONL** | `processed/kalshi_market_archive/orderbooks/YYYY-MM-DD.jsonl` | Top-of-book ask + size at anchor | `kalshi_orderbook_archive_loader.load_anchor_orderbook_context()` |
| **3. Candle JSONL** | `processed/kalshi_candle_archive/*-candles.jsonl` | Bid/ask/volume per minute (validation + future slippage) | `kalshi_candle_archive_loader.load_anchor_candle_context()` |
| **4. Weather join** | NWS / IEM MOS / NCEI | Forecast °F + observed max | `kalshi_nws_join.py` |
| **5. NDFD enriched CSV** | `accuracy_points_enriched.csv` | Optional MAE anchor (4 PM research) | `historical_checksum_backtest.py` |

### Maker fill replay (current logic)

```
limit bid posted at anchor
  → try archived orderbook (ask ≤ bid)     fill_source: archived_orderbook_at_anchor
  → try archived candle (ask ≤ bid)        fill_source: archived_candle_at_anchor
  → else scan minute CSV in posting window fill_source: minute_csv
```

Liquidity caps: `backtest_max_contracts()` uses **25% of archived yes_ask_size** when book present; else 25-contract default.

---

## Key scripts

```bash
export PYTHONPATH=ingest/scripts

# Full backtest (maker default)
python3 ingest/scripts/historical_checksum_backtest.py --mode kalshi \
  --price-history-dir "../Kalshi/Kalshi - Miami Max Temp. Bet History" \
  --orderbook-archive-dir "../Kalshi/backend/data/processed/kalshi_market_archive" \
  --output-dir "Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest"

# Policy sweep + recommended_policy.json
python3 ingest/scripts/kalshi_policy_optimizer.py \
  --price-history-dir "../Kalshi/Kalshi - Miami Max Temp. Bet History" \
  --orderbook-archive-dir "../Kalshi/backend/data/processed/kalshi_market_archive"

# Daily NAS pipeline (CSV + candle archive + sweep)
bash ingest/scripts/run_daily_policy_refresh.sh

# After sweep: human review + frontier + pipeline status
bash ingest/scripts/refresh_trading_bridge.sh
```

---

## Report fields (new / important)

| Field | Meaning |
|-------|---------|
| `n_days_with_anchor_orderbook` | Days with JSONL snapshot within −5…+45 min of anchor |
| `hit_rates.maker_fill_sources` | Count of `archived_orderbook_at_anchor` vs `minute_csv` |
| `daily_results[].market.fill_source` | Per-day maker fill path |
| `daily_results[].market.anchor_orderbook` | Book metadata when found |
| `anchor_candle` on price snapshot | Candle archive at anchor; drives `archived_candle_at_anchor` fills when book absent |

---

## Known gaps

1. **Orderbook archive sparse on Mac/NAS** — live JSONL from paper loop; backtest falls back to CSV/candles until populated.
2. **Candle archive** — backfilled for all 62 price-history days on Mac (100% coverage); enables `archived_candle_at_anchor` fills where book absent.
3. **P(bin) parity** — `kalshi_integer_distribution.py` + `compare_prob_models.py`; opt in with `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1`
4. **Default edge 18%** — `MIN_FORECAST_EXECUTABLE_EDGE = 0.18`; old Research JSON artifacts may still show 14%.
5. **Canonical KMIA pin (2026-06-21+)** — lat **25.7906**, lon **-80.3164** → NWS **MFL/105,51**. Legacy snapshots on MFL/106,51 or MFL/109,96 are quarantined via `quarantine_mismatched_nws_snapshots.py`. IEM MOS backfill disabled unless `KALSHI_BACKTEST_ALLOW_IEM_MOS=1`. **Re-extract NDFD** at new coords before trusting historical MAE CSV for policy.

---

## Tests

```bash
export PYTHONPATH=ingest/scripts
python3 ingest/scripts/test_kalshi_orderbook_archive_loader.py
python3 ingest/scripts/test_kalshi_candle_archive_loader.py
python3 ingest/scripts/test_historical_checksum_backtest.py
python3 ingest/scripts/test_kalshi_policy_optimizer.py
```

All should pass before merging policy changes.

---

## Next agent actions (safe)

1. ~~Wire candle archive into fill fallback~~ (done: orderbook → candle → CSV)
2. Re-run policy sweep after 30+ days of orderbook JSONL.
3. ~~Port `integer_dist_v1` into backtest~~ (done: `kalshi_integer_distribution.py`, max |ΔP|=0 vs gaussian on 310 comparisons)
4. Human: approve `trading_policy.json` in Kalshi repo when satisfied with sweep.
   - Read: `Research/.../Kalshi_Price_Backtest/policy_review_for_human.txt`
   - Run: `bash ingest/scripts/refresh_trading_bridge.sh` after each sweep
   - Approve: `bash scripts/approve_trading_policy.sh` (Kalshi repo)
5. Backfill candle/orderbook archives on NAS; re-sweep when coverage >30 days.

---

## References

- `docs/architecture/KALSHI_DATA_COLLECTION.md`
- `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md`
- `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`
