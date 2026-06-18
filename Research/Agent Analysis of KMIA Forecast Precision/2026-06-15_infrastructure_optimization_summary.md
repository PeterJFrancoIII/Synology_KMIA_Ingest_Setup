# Infrastructure Optimization Summary

**Date:** 2026-06-15  
**Goal:** Remove Legion5 processing bottlenecks for 4-season and full-archive work

## Changes implemented

### 1. Parallel `wgrib2` extract

- `22_batch_extract_local_gribs.py --workers N` (default via `KMIA_EXTRACT_WORKERS`)
- Wired in `35_process_month_from_nas.sh` (default: 4)

### 2. SMB3 pull mode

- `nas_pull_helpers.sh`: `NAS_PULL_MODE=smb` via robocopy from `Z:`
- Auto-fallback to SSH tar when `Z:` not mounted
- Dedicated read-only NAS user `kmia_legion5` + secrets file on Legion5

### 3. Canonical environment

- `legion5/kmia_legion5_env.sh` sourced by all launchers
- `.cursor/rules/legion5-processor-defaults.mdc` for persistent agent memory

### 4. Setup scripts

- `43_setup_nas_smb.ps1` — mount `Z:` at login
- `43_benchmark_pull_modes.sh`, `44_benchmark_workflow.sh` — benchmarks

## Measured improvement

| Metric | Before | After |
|--------|--------|-------|
| Pull mode | SSH tar (~12 min/wdir month) | SMB robocopy (~5–7 min) |
| Extract | Serial `wgrib2` | 4 parallel workers |
| Per month (optimized months) | ~35–40 min | **~26 min** |
| 4-season study (3 opt + 1 legacy) | ~2+ hours est. | **~1.5 hours** |

## Default workflow (2026-06-15+)

```text
Legion5: Z: SMB pull → parallel wgrib2 → VALID_ONLY → merge → analyze
NAS:     raw GRIB lake (immutable) + target processed/ CSV lake
Mac:     scripts, deploy, research archive
```

## One-time Legion5 setup

```powershell
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1
```

See [OPTIMAL_ANALYSIS_WORKFLOW.md](./OPTIMAL_ANALYSIS_WORKFLOW.md).
