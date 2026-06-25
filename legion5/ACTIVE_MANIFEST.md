# Legion5 active script manifest

**Machine-readable:** [`ACTIVE_MANIFEST.json`](ACTIVE_MANIFEST.json)  
**Do not grep all of `legion5/`** — use the JSON group for your task.

## Env (source in every pipeline)

- `kmia_legion5_env.sh` — SMB, workers, NAS paths
- `kmia_kalshi_legion5_env.sh` — Kalshi mirror paths
- `nas_pull_helpers.sh` / `nas_push_helpers.sh`

## Active paths by task

### Extract (BUILD)

`35_process_month_from_nas.sh` → `36_process_all_from_nas.sh` → `36b_resume_build.sh`  
SMB: `43_setup_nas_smb.ps1` (read), `43b_setup_nas_smb_write.ps1` (write)  
GRIB hygiene: `56_consolidate_legion5_grib_to_nas.sh`, `57_cleanup_legion5_grib.sh`

### Analyze (MAE + charts)

`45_kmia_year_maxt_precision_analysis.sh` → `47_build_kmia_chart_suite.sh`  
All years: `50_rebuild_all_years_study.sh` → `49_build_all_charts.sh`

### Kalshi research (sweep on Legion5 only)

`52_kalshi_ndfd_anchor_backfill.sh` → `54_kalshi_ndfd_research_pipeline.sh`  
Daily: `55_daily_kalshi_research.sh`, `55_daily_nbm_fetch.sh`  
Export: `55_export_maker_policy.sh` → `55_sync_research_to_nas.ps1`

### Mac (mirror only)

`pull_all_charts_to_mac.sh` — **use this**  
`pull_charts_and_data_to_mac.sh` — deprecated (~GB)

## Legacy (do not use for new work)

- `archive/legacy/` — WSL bootstrap
- `03_legion5_year_pipeline.sh` — 2020 WSL year pipeline
- `38_*`, `39_*`, `44_*` — one-off benchmarks/tests
