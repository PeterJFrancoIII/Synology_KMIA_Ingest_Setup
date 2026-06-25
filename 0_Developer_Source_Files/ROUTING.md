# Agent routing (read before grepping scripts)

**Live state:** [`current-objective.md`](current-objective.md)  
**Commands:** [`AGENTS.md`](AGENTS.md)  
**Runtime:** Legion5 + MediaServer2 only — Mac deploy/approve only.

## Task → entry point

| Task | Read first | Run on | Active manifest |
|------|------------|--------|-----------------|
| NAS deploy / paper loop | `docs/NAS_Runbook.md` § Canonical deploy | Mac → SSH | — |
| NAS ingest / GRIB smoke | `.cursor/skills/kmia-nas-ingest/SKILL.md` | MediaServer2 | `ingest/scripts/ACTIVE_MANIFEST.json` |
| NDFD extract + monthly BUILD | `legion5/README_PROCESSOR.md` | Legion5 | `legion5/ACTIVE_MANIFEST.json` → `extract` |
| Year MAE analyze + charts | `docs/OPTIMAL_ANALYSIS_WORKFLOW.md` | Legion5 | `legion5/ACTIVE_MANIFEST.json` → `analyze` |
| Kalshi backtest + policy sweep | `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md` | Legion5 | `ingest/scripts/ACTIVE_MANIFEST.json` → `kalshi_backtest` |
| Export approved policy | `legion5/55_export_maker_policy.sh` | Legion5 | `legion5/ACTIVE_MANIFEST.json` → `kalshi_research` |
| Human policy approval | Kalshi repo `scripts/approve_trading_policy.sh` | Mac | — |
| Pull charts to Mac (light) | `legion5/pull_all_charts_to_mac.sh` | Mac | — |
| Ops watch (NAS health) | `ingest/scripts/kmia_paper_ops_watch.sh` | Mac → SSH | `ingest/scripts/ACTIVE_MANIFEST.json` → `ops` |

## Mac Research folder (do not wander)

| Safe to open | Do not open (gitignored / Legion5 mirror) |
|--------------|-------------------------------------------|
| `*/accuracy_points_enriched.csv` | `policy_sweep_*.json`, `kalshi_price_backtest_*.json` |
| `*/kmia_chart_suite.html`, chart portal | `Legion5_Extract/`, raw point CSVs |
| `Kalshi_Price_Backtest/recommended_policy.json` | `*_stability_wind.png` (regenerable) |
| `Kalshi_Price_Backtest/trading_policy_draft.json` | Full sweep JSON — use `ingest/scripts/fixtures/` |

Schema samples: `ingest/scripts/fixtures/`

## Mega-modules (grep by section, do not read whole file)

| File | Section map |
|------|-------------|
| `ingest/scripts/historical_checksum_backtest.py` | FILE MAP in module header |
| `ingest/scripts/kalshi_policy_optimizer.py` | FILE MAP in module header |

## Legacy / archive

- Legion5 WSL bootstrap: `legion5/archive/legacy/`
- Dated handoffs: `docs/archive/handoffs/`
- Wind-regime experiment: `ingest/scripts/archive/wind_regime/`
