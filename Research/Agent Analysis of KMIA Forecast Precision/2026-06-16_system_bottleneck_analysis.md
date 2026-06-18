# System Bottleneck Analysis

**Date:** 2026-06-16  
**Context:** Post-optimization 4-season study; preparing for full 2020–2025 processing

## Current bottleneck (optimized stack)

**#1: wdir `wgrib2` extract on Legion5** — ~65% of per-month time (~15–18 min of ~26 min).

Network is no longer the primary limiter after SMB robocopy (~95 MB/s measured).

## Per-month time budget (SMB + 4 workers)

| Phase | Time |
|-------|------|
| Pull maxt (~10 GB) | 3–5 min |
| Extract maxt | ~3 min |
| Pull wdir (~40 GB) | 5–7 min |
| Extract wdir | **15–18 min** |
| Filter + cleanup | ~1 min |
| **Total** | **~26 min** |

## Bottleneck ranking

1. wdir CPU extract (Legion5)
2. Serial staging (maxt then wdir; no parallel pull/extract)
3. Moving ~40 GB/month GRIB that is deleted after extract
4. D: disk headroom (185 GB free — OK serially, tight at scale)
5. Intermediate `point_forecasts.csv` (minor)
6. NAS CPU (J4125) — not viable for primary extract vs Legion5 12-core

## Ruled out

| Approach | Why |
|----------|-----|
| NAS-primary `wgrib2` | J4125 ≪ Legion5; saves ~7 min transfer, loses ~20+ min CPU |
| SCP/SFTP | Disabled on Synology |
| Mac as processor | Orchestration only |

## Recommended before 72-month scale

1. `KMIA_EXTRACT_WORKERS=8` (12 cores available)
2. Parallel robocopy maxt + wdir
3. Sync VALID_ONLY CSVs to NAS `processed/` after each month
4. D: disk watchdog (< 50 GB free → pause)

## Extrapolation: 72 months (2020–2025)

| Path | Est. time |
|------|-----------|
| Current (SMB, w=4, serial) | ~31 hours |
| Optimized (SMB, w=8, parallel pull) | ~20–24 hours |
| Analysis-only (CSVs on NAS) | ~15–30 min |

## Data size insight

Per month: ~43 MB VALID_ONLY CSV vs ~50 GB raw GRIB → **~1000×** reduction.  
Store CSVs on NAS; re-run analysis without re-processing GRIB.

See [OPTIMAL_ANALYSIS_WORKFLOW.md](./OPTIMAL_ANALYSIS_WORKFLOW.md) for full workflow.
