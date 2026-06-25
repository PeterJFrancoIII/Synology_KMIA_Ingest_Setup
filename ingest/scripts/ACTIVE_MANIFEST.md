# ingest/scripts active manifest

**Machine-readable:** [`ACTIVE_MANIFEST.json`](ACTIVE_MANIFEST.json)  
**Routing:** [`0_Developer_Source_Files/ROUTING.md`](../../0_Developer_Source_Files/ROUTING.md)

Agents: pick **one group** below; do not list-dir the whole folder (76+ Python files).

| Group | Entry scripts | Run on |
|-------|---------------|--------|
| `nas_docker_ingest` | `10_*`, `20_*`, `21_*`, `22_*`, `30_*`, `40_*` | NAS container |
| `mae_charts` | `analyze_kmia_forecast_accuracy.py`, `build_kmia_chart_*` | Legion5 |
| `kalshi_backtest` | `historical_checksum_backtest.py`, `kalshi_policy_optimizer.py` | Legion5 |
| `policy_export` | `export_trading_policy.py`, `run_daily_policy_refresh.sh` | Legion5 / NAS ingest-only |
| `ops` | `kmia_paper_ops_watch.sh`, `kalshi_archive_status.py` | Mac → SSH / read-only |
| `calibration_nbm` | `fetch_nbm_maxt_kmia.py`, `trading_window_priors.py` | Legion5 |

**Schema samples:** [`fixtures/`](fixtures/) — use instead of opening full sweep/backtest JSON.

**Disabled:** `backfill_kalshi_nws_ncei.py`, `archive/wind_regime/`

**Tests:** `test_*.py` — run via pytest, not for production routing.
