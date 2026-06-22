# Kalshi trading policy bridge — program state

**Last updated:** 2026-06-21  
**Console:** 2 (research/backtest) → 3 (paper loop) via files only  
**Mode:** Dry-run / paper only — **no live order execution in this repo**

---

## Purpose

Console 2 produces **backtested trading policy** and exports it for Console 3 (Kalshi repo). Console 1 (Streamlit) shows human-readable status. One manifest (`trading_policy.json`) replaces parallel edge configs across consoles (backtest default **18%** as of 2026-06-20).

Full export schema: [CONSOLE_2_EXPORT_CONTRACT.md](./CONSOLE_2_EXPORT_CONTRACT.md)

---

## Design anchors (do not conflate)

| Concept | Anchor | Used for |
|---------|--------|----------|
| MAE / NDFD research | **4 PM ET** NDFD release | `accuracy_points_enriched.csv`, chart portal |
| Kalshi bin open / bet timing | **Prior-day 10 AM ET** | Price history CSV, forecast join, maker/taker sim |
| Forecast °F at bet time | Latest real source **≤ 10:30 AM ET** prior day | NWS snapshot → rules_v2 → IEM GFS MOS |
| P(bin) in backtest | `integer_dist_v1` when `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1` (see `kmia_kalshi_env.sh`) | Edge, insurance sizing |
| P(bin) in live paper loop | Integer dist + MAE shrink | `signal_generator.py` |

---

## Weather data for Kalshi backtest (2026-04-20 → 2026-06-20)

| Source | Role | Path (Kalshi processed data) |
|--------|------|------------------------------|
| Kalshi price history CSV | Bin asks at 10 AM open | `Kalshi - Miami Max Temp. Bet History/` |
| Kalshi orderbook archive | Top-of-book ask/size at anchor (maker fill replay) | `backend/data/processed/kalshi_market_archive/orderbooks/` |
| Kalshi candle archive | Full bid/ask/volume JSONL (future slippage work) | `backend/data/processed/kalshi_candle_archive/` |
| NWS live snapshots | Forecast high when available | `backend/data/processed/weather_nws/nws_kmia_snapshot_*.json` |
| IEM GFS MOS archive | Historical MOS when no live snapshot | `backend/data/processed/weather_nws/iem_gfs_mos_forecast_archive.jsonl` |
| NCEI CLIMIA daily TMAX | Settlement observed max | `backend/data/processed/history/kmia_daily_history.jsonl` |
| NWS observed JSONL | Fallback observed | `backend/data/processed/weather_nws/nws_observed_history.jsonl` |

**Coverage scorecard (run anytime):**

```bash
python ingest/scripts/kalshi_weather_coverage_scorecard.py
```

As of 2026-06-21: **62/62** forecast, observed, and full join; policy confidence **moderate** (≥20 scored trades).

**Policy approval:** Human-approved policy may be **stale** (e.g. 26% edge) vs latest draft from sweep (often 0–5% edge + insurance). Re-run `bash ingest/scripts/refresh_trading_bridge.sh` after sweep and re-approve via Kalshi `scripts/approve_trading_policy.sh`.

**Kalshi backtest default:** `--mode kalshi` uses **10 AM `kalshi_nws_join`** + NCEI settlement (`--no-enriched-csv` default). Do not use 4 PM `accuracy_points_enriched.csv` for trading evaluation unless `--use-enriched-csv`.

---

## Backtest outputs (Console 2)

| Artifact | Producer |
|----------|----------|
| `kalshi_price_backtest_*.json` | `historical_checksum_backtest.py --mode kalshi` |
| `dual_mode_comparison.json` | `--dual-report` (taker vs maker) |
| `policy_sweep_*.json`, `recommended_policy.json` | `kalshi_policy_optimizer.py` |
| `policy_frontier_*.html` | `chart_kalshi_policy_frontier.py` |
| `trading_policy_draft.json` (export) | `export_trading_policy.py` → Kalshi `backend/data/research/` |

**Compute routing (mandatory):**

| Host | Role | Policy sweep command |
|------|------|----------------------|
| **Legion5** | Primary — NDFD extract + backtest + sweep (local to NAS via `Z:`) | `bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh` |
| **NAS** | Scheduled daily refresh (`kmia-paper-research` container) | `sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh` |
| **Mac** | Deploy scripts + human review only — **never** run sweep/backtest | Blocked by `run_daily_policy_refresh.sh` unless `ALLOW_MAC_POLICY_REFRESH=1` |

Legion5 reads Kalshi price history and archives from **`Z:/App_Development/Kalshi`** (NAS SMB, ~95 MB/s LAN). Writes go to **`D:/KMIA_Process/kalshi_mirror`** then sync via `55_sync_kalshi_mirror_to_nas.ps1`. Mac pulls over Tailscale/SSH are slow and stale relative to NAS.

**Legion5 operator (Git Bash):**

```bash
# 0. From Mac — deploy latest scripts (once per session)
scp legion5/{52,54}*.sh legion5/kmia_kalshi_legion5_env.sh legion5/kmia_legion5_env.sh \
  ingest/scripts/{kalshi_policy_optimizer,export_trading_policy,export_safest_policy_from_sweep,historical_checksum_backtest,backfill_nws_snapshots_from_ndfd,write_policy_human_review,chart_kalshi_policy_frontier}.py \
  Legion5:D:/KMIA_Process/scripts/

# 1. On Legion5 — verify Z: mounted, then run full research pipeline
test -d /z/App_Development/Kalshi || echo "Mount Z: first (43_setup_nas_smb.ps1)"
bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh

# 2. Sync drafts to NAS Kalshi tree (writable creds required)
powershell -ExecutionPolicy Bypass -File D:/KMIA_Process/scripts/55_sync_kalshi_mirror_to_nas.ps1

# 3. Human review on Mac (Kalshi repo)
cat ~/Desktop/App\ Development/Kalshi/backend/data/processed/status/policy_review_for_human.txt
bash ~/Desktop/App\ Development/Kalshi/scripts/approve_trading_policy.sh
```

Autorun after NDFD extract: `bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --once 202604_202606`

**NAS scheduled refresh** (no NDFD extract — uses live NWS + API ingest):

```bash
bash ingest/scripts/run_daily_policy_refresh.sh   # inside NAS container only; blocked on Mac
```

---

## Liquidity / thin markets

KXHIGHMIA is thin (~**$121k/event-day** reference volume; median top-of-book ~**376 contracts** in snapshots).

| Layer | Cap logic | Module |
|-------|-----------|--------|
| Console 2 backtest | Max **25 contracts/leg**; **25% of archived top-of-book** when JSONL present; else CSV-only cap | `kalshi_price_history_loader.backtest_max_contracts()` + `kalshi_orderbook_archive_loader.py` |
| Console 3 live | min(25% of `yes_ask_size`, 0.5% of event volume, 25 abs) | Kalshi `trading/liquidity_limits.py` |

Policy manifest fields: `avg_event_volume_usd`, `max_top_of_book_participation`, `max_event_volume_participation`, `abs_max_contracts_per_leg`.

---

## Human approval (no code review required)

1. Plain-English report: Kalshi `backend/data/processed/status/policy_review_for_human.txt`
2. Streamlit → Paper Trading → **Trading Policy Review**
3. Terminal: `bash scripts/approve_trading_policy.sh` (Kalshi repo)

Until `approved_by_human: true` on `trading_policy.json`, Console 3 keeps **legacy taker + MAE edge** (draft does not change execution).

---

## Key scripts (Console 2)

| Script | Role |
|--------|------|
| `historical_checksum_backtest.py` | Kalshi price-primary backtest |
| `kalshi_policy_optimizer.py` | Policy sweep + draft manifest |
| `export_trading_policy.py` | Export to Kalshi research dir |
| `kalshi_weather_coverage_scorecard.py` | Data join scorecard |
| `kalshi_orderbook_archive_loader.py` | 10 AM anchor book load for maker-fill replay |
| `build_iem_mos_forecast_archive.py` | Backfill IEM MOS rows |
| `watch_kalshi_price_history.sh` | CSV-drop hook |
| `run_daily_policy_refresh.sh` | Backtest + sweep + export |

---

## Key modules (Console 3 — Kalshi repo)

| Path | Role |
|------|------|
| `backend/src/research/trading_policy.py` | Load approved/draft policy |
| `backend/src/trading/bet_decision_engine.py` | Policy edge, maker limits, liquidity caps |
| `backend/src/trading/liquidity_limits.py` | Thin-market contract caps |
| `backend/src/trading/policy_limits.py` | Maker bids, insurance legs |
| `scripts/update_trading_pipeline_status.py` | Pipeline health JSON + human review text |
| `scripts/analyze_kalshi_liquidity.py` | Volume / book-size summary |

---

## Non-goals (unchanged)

- No Streamlit UI in Console 2
- No auto-approve policy
- No real Kalshi orders from either repo
- Do not merge NAS Legion5 batch into 15-minute paper loop
