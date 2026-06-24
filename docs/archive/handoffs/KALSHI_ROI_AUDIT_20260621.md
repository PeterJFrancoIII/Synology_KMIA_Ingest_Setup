# Kalshi ROI data layer audit

**Date:** 2026-06-21  
**Console:** 2 (research only — no order execution)

## Coverage scorecard (2026-06-21)

| Layer | Coverage |
|-------|----------|
| Price-history days | 62 |
| Forecast at 10 AM anchor (NWS / NDFD backfill / rules_v2) | 62/62 (100%) |
| Observed settlement (NCEI CLIMIA TMAX) | 62/62 (100%) |
| Full join (forecast + NCEI) | 62/62 (100%) |
| Policy confidence tier | MEDIUM (≥20 scored days) |

## Station alignment

- Canonical pin: **25.7906, -80.3164 → MFL/105,51**
- `verify_kmia_station_alignment.py`: **OK** — operational paths aligned

## Data source roles

| Stream | Path | Kalshi backtest role |
|--------|------|----------------------|
| 10 AM forecast | `kalshi_nws_join.forecast_high_at_anchor()` | Primary — must match policy sweep |
| NCEI settlement | `history/kmia_daily_history.jsonl` | Primary observed max |
| NWS observed JSONL | `weather_nws/nws_observed_history.jsonl` | Fallback + live intraday series |
| MAE enriched CSV | `accuracy_points_enriched.csv` | **MAE research only** (4 PM anchor) — not for trading backtest |
| Live NWS snapshot | `nws_kmia_snapshot_*.json` | Console 1 capture; grid MFL/105,51 |

## Known gaps

- Orderbook archive at anchor: 0/62 (candle + minute CSV fallback)
- IEM MOS backfill: disabled unless `KALSHI_BACKTEST_ALLOW_IEM_MOS=1`
- Approved policy (26% edge) stale vs latest draft (0% edge)

## Pre-fix vs post-fix backtest divergence (root cause)

Pre-fix default backtest used **4 PM enriched CSV forecast** + **ISD observed** against **10 AM prices**, with IEM MOS enabled → inflated eligibility (72%) and phantom edge.

Post-fix: enriched CSV still defaulted in `--mode kalshi` until this recovery pass; policy sweep always used 10 AM join.

## Post-recovery results (2026-06-21)

| Metric | 18% backtest (10 AM join) | Recommended policy (sweep) |
|--------|---------------------------|----------------------------|
| Forecast join | `kalshi_nws_join_10am` | Same |
| Settlement | NCEI only | NCEI only |
| Traded days | 7 | 45 |
| Win rate | 42.9% | **73.3%** |
| ROI | **168.73%** | **76.99%** |
| Total P&L | $49.60 | **$292.75** |
| Insurance | fraction 25% | fraction, budget **100%**, k=0.6 |
| Insurance covers book | 0% (fraction 25%) | **31.1%** |

**Loss taxonomy (recommended policy):** 33 wins, 12 `both_miss` (forecast + insurance bins missed).

**Human action:** Re-approve draft policy (`min_forecast_edge: 0%`, `insurance_budget_fraction: 1.0`) — stale approved policy still at 26% edge.
