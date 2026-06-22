# KMIA Kalshi — Algorithmic Trading Policies

**Last synced:** 2026-06-22T01:12:37.550046+00:00  
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

User requested max probability of profit — max win-rate tier (max_pnl)

**Optimizer method:** `max_win_rate_insured_min_trades_20`  
**Evidence sweep:** `D:\KMIA_Process\analysis\Kalshi_Price_Backtest\policy_sweep_20260622T005444Z.json`  
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
| `max_entry_yes_ask` | $0.35 |
| `order_mode` | maker_limit |
| `anchor_hour_et` | 10 |
| `require_cheapest_at_open` | True |
| `insurance_enabled` | True |
| `insurance_mode` | fraction |
| `insurance_budget_fraction` | 100% |
| `insurance_price_k` | 0.6 |
| `live_model_version` | integer_dist_v1 |

### Backtest metrics (historical — not a guarantee)

| Metric | Value |
|--------|-------|
| Trades | 46 |
| Wins / losses | 33 / 13 |
| Win rate | 71.7% |
| Total P&L | $287.12 |
| Total deployed | $385.88 |
| ROI | 74.41% |
| Avg insurance legs | 2.17 |

### Approval status

**STALE** — `trading_policy.json` is approved but differs from draft. Re-approve via `bash scripts/approve_trading_policy.sh` in Kalshi repo.

---

## Tier comparison (same sweep)

| Tier | Edge | Ins mode | Ins budget | k | Win % | ROI | P&L | Deployed | Trades |
|------|------|----------|------------|---|-------|-----|-----|----------|--------|
| **Active (draft export)** | 0% | fraction | 100% | 0.6 | 71.7% | 74.41% | $287.12 | $385.88 | 46 |
| Max P&L / max win-rate | 0% | fraction | 100% | 0.6 | 71.7% | 74.41% | $287.12 | $385.88 | 46 |
| Balanced (ROI×win≥68%) | 0% | fraction | 50% | 0.6 | 69.6% | 77.64% | $244.31 | $314.69 | 46 |
| Max ROI guarded (win≥65%) | 6% | cover_book | 25% | 0.6 | 66.7% | 93.3% | $173.76 | $186.24 | 33 |
| Max ROI | 9% | cover_book | 25% | 0.5 | 58.3% | 102.42% | $125.99 | $123.01 | 24 |

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
| 2026-06-22 | Auto-sync from `D:\KMIA_Process\analysis\Kalshi_Price_Backtest\policy_sweep_20260622T005444Z.json` — active tier `max_win_rate_insured_min_trades_20`. |

