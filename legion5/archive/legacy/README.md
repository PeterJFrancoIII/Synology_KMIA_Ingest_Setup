# Legacy Legion5 bootstrap (one-time WSL / Windows setup)

Scripts moved here from `legion5/` root for clarity. **Active pipelines** use `35_*`–`55_*` (NAS pull, extract, analyze, Kalshi research).

These files supported the original **E:\KMIA_Setup** WSL ingest bootstrap (2020 year pipeline). Legion5 may still have copies at `E:\KMIA_Setup\` from an earlier deploy; this archive is the repo record only.

| Script | Purpose |
|--------|---------|
| `00_optimize_windows.ps1` | Windows tuning |
| `01_install_wsl.ps1` / `01_disable_startup.ps1` | WSL install / startup cleanup |
| `02_bootstrap_kmia.sh` / `02_winget_debloat.ps1` | WSL data tree + debloat |
| `03_ram_audit.ps1` | RAM audit (not `03_legion5_year_pipeline.sh` — still in `legion5/`) |
| `04_*` | Native bootstrap / RAM hogs |
| `05_post_reboot_wsl.ps1` / `06_resume.ps1` | Post-reboot WSL resume |
| `07_install_wgrib2_windows.ps1` | Native wgrib2 |
| `08_install_wsl_docker.ps1` / `09_run_kmia_container.ps1` | WSL Docker path |

**Current workflow:** [`README_PROCESSOR.md`](../../README_PROCESSOR.md), [`OPTIMAL_ANALYSIS_WORKFLOW.md`](../../../docs/OPTIMAL_ANALYSIS_WORKFLOW.md).
