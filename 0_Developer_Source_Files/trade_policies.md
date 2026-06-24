# KMIA Kalshi — Algorithmic Trading Policies

**Last synced:** 2026-06-22T22:30:02.506529+00:00  
**Maintainers:** AI agents + human operator  
**Scope:** Console 2 research → Console 3 paper loop (file-only bridge)  
**Safety:** `no_real_trading: true` — research and paper simulation only until explicitly approved.

---

## Agent contract (mandatory)

1. **Read this file** before changing policy selection, sweep grids, insurance logic, or Console 3 policy loaders.
2. **Update this file** whenever `trading_policy_draft.json`, `recommended_policy.json`, or human selection objective changes:
   ```bash
   PYTHONPATH=ingest/scripts python3 ingest/scripts/update_trade_policies_doc.py
   ```
3. Pipelines that alter policy **must** call the updater (already wired in `export_trading_policy.py`, `kalshi_policy_optimizer.py`, `write_policy_human_review.py`).
4. Cite section headings in code reviews and handoffs (e.g. "per trade_policies.md § Active Policy").

---

## Strategy summary

Daily **KXHIGHMIA** markets: bet on which temperature bin contains NWS CLIMIA TMAX at KMIA (MFL/105,51 pin).

| Layer | Behavior |
|-------|----------|
| **Timing** | Prior-day **10 AM ET** anchor; maker limit bids |
| **Forecast** | NWS high at anchor + `integer_dist_v1` bin probabilities |
| **Forecast leg** | YES on model-favored bin; edge gate via `min_forecast_edge` |
| **Insurance** | Neighbor bins (`fraction` or `cover_book` mode) |
| **Settlement truth** | NCEI CLIMIA TMAX (`kmia_daily_history.jsonl`) — never simulated weather |

**Three-console split:** This repo (Console 2) owns backtest + policy export. Kalshi repo runs paper loop. No order execution in Console 2.

---

## Selection objective (human intent)

Maximize probability of profit over recurring daily sessions (highest win-rate insured tier).

**Optimizer method:** `max_total_pnl_insured_min_sample_then_roi`  
**Evidence sweep:** `/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest/policy_sweep_20260622T223002Z.json`  
**Minimum sample:** ≥20 insured trades for tier eligibility.

### Trade-off law

You **cannot** simultaneously maximize ROI, win-rate, and total P&L on the same historical sample. Pick one primary objective:

| Goal | Tier to export | Env / flag |
|------|----------------|------------|
| Highest **ROI** | `max_roi` | `KALSHI_POLICY_SELECTION=max_roi` |
| Highest **win rate** / 3-month safety | `max_pnl` | `KALSHI_POLICY_SELECTION=max_pnl` or manual export |
| Balance ROI × win | `balanced` | `KALSHI_POLICY_SELECTION=balanced` |
| Max dollars | `max_pnl` | same as win-rate tier on current grid |

---

## Active policy (draft export)

Parameters below mirror `Kalshi/backend/data/research/trading_policy_draft.json`.

| Parameter | Value |
|-----------|-------|
| `min_forecast_edge` | 0% |
| `max_entry_yes_ask` | $0.25 |
| `order_mode` | maker_limit |
| `anchor_hour_et` | 10 |
| `require_cheapest_at_open` | True |
| `insurance_enabled` | True |
| `insurance_mode` | fraction |
| `insurance_budget_fraction` | 25% |
| `insurance_price_k` | 0.6 |
| `live_model_version` | integer_dist_v1 |

### Backtest metrics (historical — not a guarantee)

| Metric | Value |
|--------|-------|
| Trades | 4 |
| Wins / losses | 3 / 1 |
| Win rate | 75.0% |
| Total P&L | $42.33 |
| Total deployed | $19.67 |
| ROI | 215.13% |
| Avg insurance legs | 0.0 |

### Approval status

**APPROVED** — paper loop uses `trading_policy.json`.

---

## Tier comparison (same sweep)

| Tier | Edge | Ins mode | Ins budget | k | Win % | ROI | P&L | Deployed | Trades |
|------|------|----------|------------|---|-------|-----|-----|----------|--------|
| **Active (draft export)** | 0% | fraction | 25% | 0.6 | 75.0% | 215.13% | $42.33 | $19.67 | 4 |
| Max P&L / max win-rate | 0% | fraction | 25% | 0.6 | 75.0% | 215.13% | $42.33 | $19.67 | 4 |
| Balanced (ROI×win≥68%) | 14% | fraction | 25% | 0.5 | 100.0% | 398.01% | $19.18 | $4.82 | 1 |
| Max ROI guarded (win≥65%) | 14% | fraction | 25% | 0.5 | 100.0% | 398.01% | $19.18 | $4.82 | 1 |
| Max ROI | 14% | fraction | 25% | 0.5 | 100.0% | 398.01% | $19.18 | $4.82 | 1 |

---

## Compute routing

| Host | Role |
|------|------|
| **Legion5** | Canonical backtest + sweep (`54_kalshi_ndfd_research_pipeline.sh`, `Z:` SMB) |
| **NAS** | Scheduled refresh (`kmia-paper-research`) — no NDFD extract |
| **Mac** | Deploy scripts + human review only — **never** run sweep/backtest |

See `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md` for operator commands.

---

## Code map

| Component | Path |
|-----------|------|
| Policy sweep | `ingest/scripts/kalshi_policy_optimizer.py` |
| Backtest | `ingest/scripts/historical_checksum_backtest.py` |
| Manifest export | `ingest/scripts/trading_policy_manifest.py` |
| Draft export | `ingest/scripts/export_trading_policy.py` |
| Human review | `ingest/scripts/write_policy_human_review.py` |
| **This doc sync** | `ingest/scripts/update_trade_policies_doc.py` |
| Console 3 loader | `Kalshi/backend/data/research/trading_policy.json` |

---

## Constraints (non-negotiable)

- No simulated weather in forecasts or settlement (see `.cursor/rules/no-simulated-weather-data.mdc`).
- No live Kalshi orders from Console 2.
- Settlement: NCEI CLIMIA TMAX only for backtest join.
- Station pin: 25.7906, -80.3164 (NWS MFL/105,51).

---

## Change log

| Date (UTC) | Change |
|------------|--------|
| 2026-06-22 | Auto-sync from `policy_sweep_20260622T223002Z.json` — active tier `max_total_pnl_insured_min_sample_then_roi`. |

