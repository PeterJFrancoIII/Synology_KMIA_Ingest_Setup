# Archived: season-stratified wind regime distribution shifts

**Status:** Archived 2026-06-20 — not used in live paper trading or recommended policy.

## Why archived

A/B backtest on Kalshi price history (Apr–Jun 2026, recommended 26% edge policy):

| Variant | Trades | Sim P&L |
|---------|-------:|--------:|
| Baseline (no wind shift) | 21 | +$70.16 |
| Forecast wind (deployable) | 0 | $0 |
| JJA-only forecast wind | 1 | −$2.70 |

Enriched CSV calibration (1,957 days, 2020–2025): wind-adjusted top-bin hit rate **71.8% → 70.9%** (worse); DJF especially degraded (cold-front confound on NW/N).

## What remains active

- `forecast_wdir_cardinal` / `observed_wdir_cardinal` in `accuracy_points_enriched.csv` — still used by charts and MAE research.
- Optional `wind_shift_f` hook in `kalshi_integer_distribution.py` (default 0) for future experiments.

## Archived artifacts

| Path | Purpose |
|------|---------|
| `ingest/scripts/archive/wind_regime/backtest_wind_regime_ab.py` | A/B backtest runner |
| `ingest/scripts/archive/wind_regime/kalshi_wind_regime_shifts.py` | Console 2 shift table |
| `Research/.../Kalshi_Price_Backtest/archive/wind_regime/wind_regime_ab_*.json` | Backtest reports |

## Re-run archived backtest

```bash
cd ingest/scripts
KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1 python3 archive/wind_regime/backtest_wind_regime_ab.py
```

Kalshi live-loop archive: `../Kalshi/docs/archive/wind_regime_distribution_shifts/README.md`
