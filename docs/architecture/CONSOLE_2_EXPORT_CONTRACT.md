# Console 2 export contract

**Last updated:** 2026-06-20  
**Publisher:** Weather Ingestion & MAE Probabilities Console (`Synology_KMIA_Ingest_Setup`)  
**Consumers:** Console 1 (human overview links), Console 3 (strategy priors)  
**Transport:** Files only — no shared Python imports, no live API from Console 2 to Kalshi

**Bridge state (summary):** [KALSHI_TRADING_BRIDGE_STATE.md](./KALSHI_TRADING_BRIDGE_STATE.md)

---

## Canonical artifact locations (Legion5)

```
D:\KMIA_Process\
  analysis\
    KMIA_Chart_Portal\kmia_chart_portal.html
    KMIA_NDFD_AllYears_MaxT_Precision\
      accuracy_points_enriched.csv
      accuracy_report.md
      kmia_chart_suite.html
      all_years_merge_manifest.json
    KMIA_NDFD_Year_MaxT_Precision_{YEAR}\
      accuracy_points_enriched.csv
      kmia_chart_suite.html
  processed\points\station=KMIA\
    ndfd_kmia_point_forecasts_VALID_ONLY_{YEAR}.csv
```

Mac Research sync (optional): `Research/Agent Analysis of KMIA Forecast Precision/`

---

## `accuracy_points_enriched.csv` (primary MAE feed)

Key columns for downstream consoles:

| Column | Meaning |
|--------|---------|
| `target_date_et` | Settlement day (ET) |
| `release_time_et` | NDFD release timestamp |
| `forecast_temp_f` | Point max-t forecast (°F) |
| `observed_max_f` | ISD daily max (°F) |
| `abs_error_f` / `signed_error_f` | Error metrics |
| `within_0f` … `within_3f` | Hit flags (±0 = integer match) |
| `forecast_stability` | STABLE / MIXED / UNSTABLE |
| `forecast_wdir_cardinal` | NDFD forecast wind |
| `observed_wdir_cardinal` | ISD wind at daily max |
| `lead_hour_bucket` | Hours before 4 PM ET anchor |

**Console 3 use:** Aggregate to bracket/condition/lead-time hit-rates from MAE columns. Wind direction columns remain for charts and research.

**Archived (2026-06-20):** Season-stratified **`wind_regime_shifts`** distribution correction did not improve Kalshi backtest P&L or enriched CSV top-bin accuracy. See `docs/archive/wind_regime_distribution_shifts/README.md`. Do not rebuild or apply `wind_regime_shifts` in the live paper loop.

**Console 1 use:** Link to chart portal; optional summary stats in system health — read-only.

---

## `all_years_merge_manifest.json`

```json
{
  "n_days": 1957,
  "n_releases": 72084,
  "date_min": "2020-04-16",
  "date_max": "2025-08-26",
  "source_years": [2020, 2021, 2022, 2023, 2024, 2025]
}
```

Consumers **must** display `date_min` → `date_max` — never assume full calendar years without checking this file.

---

## Chart portal (human research)

- **URL pattern:** `.../KMIA_Chart_Portal/kmia_chart_portal.html`
- **Not** a substitute for Console 1 live dashboard
- Console 1 may embed an iframe or link: “Historical MAE research”

---

## Rebuild commands (Console 2 only)

```bash
# All-years from completed per-year studies
bash legion5/50_rebuild_all_years_study.sh

# Full chart portal
bash legion5/49_build_all_charts.sh
```

---

## Explicit non-exports

Console 2 does **not** publish:

- Live Kalshi market prices or orderbooks (minute CSVs + archived JSONL are ingested locally for backtest; not a live feed to downstream consoles)
- Live NWS/TWC snapshots
- Paper trade ledger entries
- Real-time bet recommendations

Those belong to Console 1 and Console 3. Console 2 **does** publish backtested policy manifests and human-readable review text paths (see below).

---

## `historical_checksum_*.json` (checksum backtest export)

**Producer:** `ingest/scripts/historical_checksum_backtest.py`  
**Consumer:** Console 3 `historical_checksum_engine.py` (regression guard)

Validates forecast-vs-observed math from `accuracy_points_enriched.csv` and, when Kalshi price-history CSVs are available, replays **actual bin costs** at the prior-day **10 AM ET** anchor (when Kalshi bins open for betting).

Key fields:

| Field | Meaning |
|-------|---------|
| `daily_results[].forecast_bin` | NDFD anchor mapped to fixed bin (`<=78` … `>=87`) |
| `daily_results[].observed_bin` | ISD settlement truth bin |
| `daily_results[].checksum_failures` | Bin/tolerance/market mismatches |
| `daily_results[].market.bin_prices_cents` | Kalshi yes prices per bin (cents) at bin open |
| `daily_results[].market.forecast_bin_cheapest_at_open` | Forecast-favored bin has lowest yes ask at 10 AM ET open |
| `daily_results[].market.entry_within_cap` | Forecast bin yes ask ≤ $0.35 at open |
| `daily_results[].market.open_purchase_eligible` | Forecast leg passes cheapest + cap + 18% edge |
| `daily_results[].market.fill_source` | Maker fill path: `archived_orderbook_at_anchor` or `minute_csv` |
| `daily_results[].market.anchor_orderbook` | Metadata when archived book found at 10 AM anchor |
| `daily_results[].market.insurance_legs[]` | Prob-weighted insurance bins (relational price cap) |
| `daily_results[].market.insurance_total_cost` | Sum of insurance leg costs (≤ 25% of forecast cost) |
| `daily_results[].trade` | Hedged settlement: forecast + insurance legs, total P&L |
| `hit_rates.open_purchase_eligible_rate` | % validated days passing forecast leg policy |
| `hit_rates.hedged_win_rate` | % traded days with net positive P&L |
| `hit_rates.total_simulated_pnl` | Sum of hedged simulated P&L across traded days |
| `hit_rates.total_deployed` | Sum of capital deployed across settled trades |
| `hit_rates.roi_pct` | `100 × total_simulated_pnl / total_deployed` |
| `hit_rates.insurance_covers_book_rate` | % trades where a winning insurance leg would cover book |
| `hit_rates.forecast_bin_hit_rate` | % days research forecast bin == observed (not settlement) |

**Kalshi price-history inputs:** `kalshi-price-history-kxhighmia-*.csv` (minute or hour). Kalshi uses **sliding 6-bin windows** per settlement day (e.g. Apr 21: `<=74` … `>=83`; Apr 20: `<=78` … `>=87`). The loader parses column headers dynamically and maps the forecast °F to the matching market bin.

**Weather join for Kalshi mode (not NDFD enriched CSV by default):** Forecast at anchor uses `kalshi_nws_join.py` priority: NWS snapshot → NDFD backfill → rules_v2 → (opt-in) IEM GFS MOS. Observed settlement uses **NCEI/CLI daily TMAX only** (`kmia_daily_history.jsonl`). `nws_observed_history.jsonl` is **intraday gates only** — never settlement labels. The 4 PM MAE file `accuracy_points_enriched.csv` is for `--mode enriched` or `--use-enriched-csv` (forecast-only override); default `--mode kalshi` uses **10 AM join** via `--no-enriched-csv` (default).

**Opt-in live-aligned P(bin):** set `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1` before backtest/sweep (default remains gaussian; models match within floating noise for σ=2.2).

**Archive paths on backtest CLI:** `--orderbook-archive-dir`, `--candle-archive-dir`

**Liquidity caps in backtest:** `backtest_max_contracts()` limits each leg to min(25 contracts, 25% of archived top-of-book size when known, else CSV-only cap).

**Orderbook archive (maker fill replay):** When `kalshi_market_archive/orderbooks/YYYY-MM-DD.jsonl` exists, backtest loads the snapshot nearest prior-day **10 AM ET** and uses top-of-book ask/size before falling back to minute CSV. Pass `--orderbook-archive-dir` or set via `kmia_kalshi_paths.kalshi_market_archive_dir()`. See `docs/architecture/KALSHI_DATA_COLLECTION.md`.

**Automatic ingest (Console 2):** `ingest/scripts/ingest_kalshi_market_data.py` pulls **1-minute** candlesticks from the Kalshi public API and writes CSVs into the Bet History folder using the same filename and subtitle column headers as manual exports. Default output is a **complete minute grid** from market open→close with yes-ask **forward-filled** per bin (for intraday pattern analysis). Tracked in `.kalshi_price_history_ingest_manifest.json`. Wired into `run_daily_policy_refresh.sh` step 0 and `run_kalshi_price_history_ingest.sh` for cron.

**Hedged bin-open policy:** At prior-day **10 AM ET** (first tick within 5 minutes for taker mode):

1. **Order mode:** `maker_limit` (default) posts YES limit bids at `P(bin) − edge` with **zero maker fee**; fill when any later ask ≤ bid. `taker` hits the open yes ask with standard fees.
2. **Forecast leg:** Buy forecast market bin when limit bid ≤ $0.35 and **P(bin) − price − fee ≥ 18%**.
3. **Insurance legs:** Two modes via `insurance_mode`:
   - `fraction` (default): bins outside forecast with **P > 10%** and **P < P(forecast)**; bid **≤ k × P(bin)**; spend **≤ budget_fraction × forecast leg cost**; prob-weighted split.
   - `cover_book`: bilateral candidates (both sides); size each leg so a win covers running book cost, up to `budget_fraction × forecast cost` (default 1.0 in cover mode).
4. **Settlement:** Win/loss on each **filled purchased market bin**; net P&L sums all legs.

**Rebuild command:**

```bash
# Kalshi backtest — 10 AM join, 18% edge (default)
python ingest/scripts/historical_checksum_backtest.py --mode kalshi --no-enriched-csv

# MAE checksum only (4 PM enriched CSV)
python ingest/scripts/historical_checksum_backtest.py --mode enriched \
  --csv Research/.../accuracy_points_enriched.csv

# Policy optimizer + frontier chart (probability-first parameter sweep)
python ingest/scripts/kalshi_policy_optimizer.py \
  --price-history-dir "/path/to/Kalshi - Miami Max Temp. Bet History" \
  --output-dir Research/.../Kalshi_Price_Backtest

python ingest/scripts/chart_kalshi_policy_frontier.py \
  --sweep-json Research/.../Kalshi_Price_Backtest/policy_sweep_*.json
```

---

## `policy_sweep_*.json` and `recommended_policy.json`

**Producer:** `ingest/scripts/kalshi_policy_optimizer.py`  
**Consumer:** `ingest/scripts/chart_kalshi_policy_frontier.py`, Console 3 policy review (file-only)

| Field | Meaning |
|-------|---------|
| `configs[]` | Each swept policy: edge, cap, cheapest, insurance, n_trades, win_rate_pct, total_pnl |
| `pareto_frontier[]` | Non-dominated configs in win_rate × total_pnl space |
| `recommended_policy` | Lexicographic winner: max win_rate, then total_pnl, then n_trades, then nearest default cap ($0.35) |
| `recommended_policy.confidence` | `low` if n_trades < 5, else `moderate` |

## `policy_frontier_*.html`

Interactive Plotly chart: win rate vs total P&L scatter, Pareto frontier, recommended star, edge sensitivity curves, top-config table.

---

## `trading_policy.json` (canonical Console 3 input)

**Producer:** `ingest/scripts/kalshi_policy_optimizer.py` + `ingest/scripts/export_trading_policy.py`  
**Consumer:** `Kalshi/backend/src/research/trading_policy.py`, Console 3 paper loop

| Field | Meaning |
|-------|---------|
| `order_mode` | `maker_limit` (default) or `taker` |
| `min_forecast_edge` | Minimum P(bin) − price − fee (e.g. 0.14) |
| `max_entry_yes_ask` | Price cap ($0.35 default) |
| `require_cheapest_at_open` | Forecast bin must be cheapest yes ask at open |
| `insurance_enabled` | Whether to post insurance limit bids |
| `insurance_mode` | `fraction` or `cover_book` |
| `insurance_budget_fraction` | Max insurance spend as fraction of forecast leg (0.25 default; up to 1.0 for cover_book) |
| `insurance_price_k` | Relational cap k × P(bin) for insurance bids (0.60) |
| `min_insurance_bin_prob` | Minimum P(bin) for insurance candidate (0.10) |
| `anchor_hour_et` | Kalshi bin-open anchor (10) |
| `model_version` | Backtest P(bin) engine version (Gaussian σ=2.2) |
| `live_model_version` | Live paper loop engine (`integer_dist_v1`) — may differ until aligned |
| `confidence` | `low` if backtest n_trades < 5, else `moderate` |
| `low_confidence_max_forecast_dollars` | Cap forecast leg at $5 when confidence is low |
| `avg_event_volume_usd` | Reference daily event volume (~121000) for liquidity math |
| `max_top_of_book_participation` | Max fraction of yes_ask_size (0.25) |
| `max_event_volume_participation` | Max fraction of event volume (0.005) |
| `abs_max_contracts_per_leg` | Hard cap per leg (25) |
| `approved_by_human` | **Must be true** before Console 3 applies policy overrides |
| `backtest_metrics` | n_trades, win_rate_pct, total_pnl, etc. from optimizer |
| `trading_policy_draft.json` | Same schema, always `approved_by_human: false` |

**Export command:**

```bash
python ingest/scripts/export_trading_policy.py \
  --backtest-dir Research/.../Kalshi_Price_Backtest \
  --kalshi-research-dir ../Kalshi/backend/data/research
```

Human approval: `bash scripts/approve_trading_policy.sh` in Kalshi repo (sets `approved_by_human: true` on `trading_policy.json`). Until then, Console 3 uses legacy taker + dynamic MAE edge.

**Pipeline status (Kalshi repo, written by Console 3):**

| File | Meaning |
|------|---------|
| `backend/data/processed/status/trading_pipeline_status.json` | Automation health, warnings, backtest summary |
| `backend/data/processed/status/policy_review_for_human.txt` | Plain-English policy review |
| `backend/data/processed/status/backtest_trades_for_human.txt` | Scored backtest trade list |

**Daily refresh:**

```bash
bash ingest/scripts/run_daily_policy_refresh.sh
```
