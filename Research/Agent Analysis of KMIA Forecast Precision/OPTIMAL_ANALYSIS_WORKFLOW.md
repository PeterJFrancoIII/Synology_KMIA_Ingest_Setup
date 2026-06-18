# Optimal KMIA Forecast-Precision Analysis Workflow

**Canonical research copy:** `Research/Agent Analysis of KMIA Forecast Precision/OPTIMAL_ANALYSIS_WORKFLOW.md`  
**Purpose:** Fastest path to `accuracy_report.md` and companion CSVs, with efficient use of Mac, NAS, and Legion5.  
**Based on:** Live benchmarks and the completed `KMIA_NDFD_4Season_MaxT_Precision_2021` study (2026-06-15/16).  
**Benchmark script:** `legion5/44_benchmark_workflow.sh`, `legion5/44b_worker_bench.sh`

---

## Executive summary

| Goal | Fastest path | Wall-clock |
|------|--------------|------------|
| **Re-run analysis** (CSVs already exist) | Legion5: merge + `analyze_kmia_forecast_accuracy.py` | **~2–5 min** |
| **4-season study** (4 months, first time) | Legion5: SMB + 8 workers + overlapped pull/extract | **~1.0–1.5 hours** |
| **Full archive** (72 months, first time) | Legion5 batch → write VALID_ONLY to NAS `processed/` | **~20–24 hours** (one-time) |
| **Full archive analysis** (after Phase 1) | Legion5: SMB pull CSVs only from NAS | **~15–30 min** |

**Do not** move raw GRIB to Legion5 for repeat analysis. **Do not** use NAS for `wgrib2` bulk extract as primary compute — the DS225+ CPU is much slower than Legion5.

**Do** treat NAS `processed/points/station=KMIA/monthly/` as the durable CSV lake after first processing.

---

## 1. System resource profile (measured)

### Legion5 (primary compute)

| Resource | Measured | Implication |
|----------|----------|-------------|
| CPU | **12 logical cores** | Supports 8 `wgrib2` workers; current default is 4 |
| D: disk | **932 GB total, 185 GB free (81%)** | Enough for 4-month study; **tight for 72-month** if raw GRIB lingers |
| SMB `Z:` | `\\192.168.0.193\Data` mounted | **~95 MB/s** robocopy (82 files / 191 MB in ~2 s, one-day test) |
| SSH tar | Works in production but **ACL-blocked** for some benchmark paths | Fallback off-LAN only |
| wgrib2 + Python | Miniforge on `E:` | Keep `E:` for toolchain; all data on `D:` |

### NAS MediaServer2 (storage + optional orchestration)

| Resource | Measured | Implication |
|----------|----------|-------------|
| CPU | **Intel Celeron J4125** (4 cores @ 2.0 GHz) | **Not** competitive with Legion5 for `wgrib2` |
| RAM | **18 GB** | Docker `kmia-arch-ingest` limited to 3 GB |
| Volume 2 | **4.0 TB free** of 8.8 TB | Ideal home for **processed CSV lake** |
| Raw lake | **~3 TB** NDFD 2020–2025 | Source of truth; immutable |
| Docker | Compose exists; **not reachable via SSH `docker`** in current setup | NAS extract requires DSM UI or docker path fix before automation |

### Mac (orchestration + reference)

| Role | Use | Avoid |
|------|-----|-------|
| Script source of truth | rsync/scp deploy to Legion5/NAS | Bulk GRIB processing |
| Golden master charts | Visual reference only | Production batch extract |
| Study launch | SSH → Legion5 `run_*.sh` | Keeping large datasets locally |

---

## 2. Benchmark evidence

### 2.1 Network pull (one day, ~82 maxt files, ~191 MB)

| Mode | Time | Throughput | Notes |
|------|------|------------|-------|
| **SMB robocopy** (`Z:`, `/MT:16`) | **~2 s** | **~95 MB/s** | Production default |
| SMB `cp` (Git Bash) | ~3 s | ~64 MB/s | Simpler, slightly slower |
| SSH `tar` (benchmark) | SKIP | — | NAS shell ACL on direct path; winter study used `nas-local` successfully |

### 2.2 Full month (observed, optimized path)

| Month | Start (UTC) | End (UTC) | Duration | Pull mode | Workers |
|-------|-------------|-----------|----------|-----------|---------|
| Spring 2021-04 | 22:38:20 | 23:04:26 | **26 min** | SMB | 4 |
| Summer 2021-07 | 23:04:27 | 23:30:50 | **26 min** | SMB | 4 |
| Fall 2021-10 | 23:30:50 | 23:56:37 | **26 min** | SMB | 4 |
| Winter 2021-12 | — | — | **~50 min** | SSH tar (pre-opt) | 1 |

**Per-month time budget (optimized, SMB + 4 workers):**

| Phase | Spring/Fall/Summer |
|-------|-------------------|
| Pull maxt (~2,500 files, ~10 GB) | ~3–5 min |
| Extract maxt (~8k rows) | ~3 min |
| Pull wdir (~2,500 files, ~40 GB) | ~5–7 min |
| **Extract wdir (~85k rows)** | **~15–18 min** ← dominant |
| Filter + delete raw | ~1 min |
| **Total** | **~26 min** |

### 2.3 CSV vs GRIB (why the lake matters)

| Asset | Size per month | Pull time (SMB) |
|-------|----------------|-----------------|
| Raw wdir GRIB | ~40 GB | ~5–7 min |
| wdir VALID_ONLY CSV | **~39 MB** | **<1 s** |
| maxt VALID_ONLY CSV | **~4 MB** | **<1 s** |
| **Both VALID_ONLY** | **~43 MB** | **<2 s** |

Analysis input for 4 months: **~170 MB CSV** vs **~160 GB GRIB** — a **~1000×** reduction.

### 2.4 Analysis layer (observed)

Completed `KMIA_NDFD_4Season_MaxT_Precision_2021`: merge + `analyze_kmia_forecast_accuracy.py` → all outputs in **<1 min** after CSVs exist.

---

## 3. Bottleneck ranking (current optimized stack)

1. **wdir `wgrib2` extract** (~65% of month time) — CPU-bound on Legion5  
2. **Sequential staging** — maxt then wdir pull/extract; no overlap  
3. **Moving ~40 GB/month** that is discarded after extract — bandwidth + D: wear  
4. **D: disk headroom** — 185 GB free; ~40 GB peak raw per month is OK serially, risky if parallel months  
5. **Intermediate `point_forecasts.csv`** — doubles write volume (~38 MB/month, minor)  
6. **NAS CPU** — rules out NAS-primary extract for speed (J4125 ≪ Legion5 Ryzen 12-thread)

---

## 4. Recommended workflow (three phases)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0 — One-time setup (Legion5)                                          │
│   43_setup_nas_smb.ps1  →  Z: mounted  →  kmia_legion5_env.sh sourced       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
┌──────────────────────────────┐                    ┌──────────────────────────────┐
│ PHASE 1 — BUILD (once)       │                    │ PHASE 2 — ANALYZE (repeat)   │
│ Legion5: GRIB → VALID_ONLY   │                    │ Legion5: CSV → tables/charts │
│ Write monthly CSVs to NAS    │                    │ SMB pull from NAS processed/ │
│ processed/points/station=KMIA│                    │ merge + analyze_kmia_*       │
└──────────────────────────────┘                    └──────────────────────────────┘
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3 — CHART SUITE (repeatable)                                          │
│ `47_build_kmia_chart_suite.sh` → kmia_chart_suite.html (2 tabs)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 0 — Environment (once per Legion5 boot)

```powershell
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1
```

```bash
# Automatic via kmia_legion5_env.sh when sourced by launchers:
export NAS_SMB_DRIVE=Z:
export NAS_PULL_MODE=smb          # auto when Z: present
export KMIA_EXTRACT_WORKERS=8     # recommend 8 on 12-core box
export NAS_SMB_THREADS=16
```

### Phase 1 — BUILD monthly VALID_ONLY (first-time processing)

**Where:** Legion5 only  
**Script:** `35_process_month_from_nas.sh` (loop via `36_process_all_from_nas.sh` or custom month list)

**Optimized month pipeline (target: ~18–20 min/month):**

```text
  ┌─ robocopy maxt ─┐     ┌─ extract maxt (workers=4) ─┐
  │  (background)   │     │                           │
  └─ robocopy wdir ─┘ ──► └─ extract wdir (workers=8) ─┘ ──► filter ──► VALID_ONLY
         parallel pull              sequential or parallel extract
         ~5 min total               ~12–15 min wdir + ~3 min maxt
```

**Rules:**

1. **SMB only** on LAN (`Z:`); never SCP/SFTP (broken on Synology).
2. **Delete raw GRIB** immediately after VALID_ONLY (already in `35_process_month_from_nas.sh`).
3. **Copy VALID_ONLY to NAS** after each month:

   ```bash
   # Target (NAS canonical):
   Z:/App_Development/KMIA_Ingest/processed/points/station=KMIA/monthly/YYYY/
   ```

4. **Skip `point_forecasts.csv`** in future script revision (optional; saves ~40 MB/month scratch).
5. **ISD once per year** on Legion5 or NAS; copy to `processed/points/station=KMIA/kmia_ncei_global_hourly_YYYY.csv`.

**Full 2020–2025 extrapolation:**

| Configuration | Est. total | Notes |
|---------------|------------|-------|
| Current (SMB, w=4, serial) | **~31 h** | 72 × 26 min |
| **Recommended (SMB, w=8, parallel pull)** | **~20–24 h** | See §5 |
| NAS-primary extract | **~35–45 h** | Slower CPU; not recommended |
| Analysis-only after BUILD | **~15–30 min** | 72 months × ~43 MB CSV |

### Phase 2 — ANALYZE (fast path — use this for studies)

**Where:** Legion5  
**When:** Monthly VALID_ONLY CSVs exist on NAS or Legion5

**4-season study:**

```bash
bash /d/KMIA_Process/run_KMIA_NDFD_4Season_MaxT_Precision_2021.sh
```

If all four months already have `*_VALID_ONLY.csv`, set env to **skip BUILD**:

```bash
# Future: TEST_SKIP_BUILD=1 — only merge + analyze (today: months skip automatically if VALID_ONLY exists)
```

**Full-span analysis:**

```bash
# Pull only needed monthly CSVs from Z: (no GRIB)
# Merge years → analyze_kmia_forecast_accuracy.py --four-season-sample or full
```

**Outputs:**

```text
D:\KMIA_Process\analysis\<STUDY_ID>\
  accuracy_report.md
  four_season_precision_summary.csv
  lead_hour_accuracy_by_season.csv
  conditions_accuracy.csv
  ...
```

**Mac sync (optional):**

```bash
scp -r Legion5:D:/KMIA_Process/analysis/<STUDY_ID>/ ./analysis/
```

### Phase 3 — CHART SUITE (repeatable after Phase 2)

**Where:** Legion5 (canonical) or Mac (rebuild from synced PNG + enriched CSV)  
**Script:** `build_kmia_chart_suite.py` via `47_build_kmia_chart_suite.sh`  
**Inputs:** `accuracy_points_enriched.csv`, merged `VALID_ONLY_{year}.csv`, ISD `{year}.csv`  
**Outputs:** `kmia_chart_suite.html` (2 tabs), `chart_suite_manifest.json`

```bash
# Legion5 (after year analysis)
bash D:/KMIA_Process/scripts/47_build_kmia_chart_suite.sh KMIA_NDFD_Year_MaxT_Precision_2021 2021

# Mac (pull PNG + rebuild local HTML)
bash legion5/pull_year_2021_analysis_to_mac.sh
```

**Tabs in `kmia_chart_suite.html`:**
1. Forecast timeline (daily summary)
2. Accuracy explorer (day/week/month, ±1/2/3°F, stability toggles)

---

## 5. Optimizations to implement next (ordered by ROI)

### A. Must-have (before full 72-month BUILD)

| # | Change | Est. savings | Effort |
|---|--------|--------------|--------|
| 1 | **`KMIA_EXTRACT_WORKERS=8`** for wdir | ~20–30% extract time | Env var only |
| 2 | **Parallel robocopy** maxt + wdir before extract | ~5–8 min/month | Small `35_process` patch |
| 3 | **Post-month NAS sync** of VALID_ONLY | Enables Phase 2 anywhere | `rsync`/`cp` to `Z:` path |
| 4 | **D: disk watchdog** (pause if free < 50 GB) | Prevents failed months | Small guard script |

### B. High value (next sprint)

| # | Change | Est. savings | Effort |
|---|--------|--------------|--------|
| 5 | **Parallel extract** maxt + wdir (2 Python PIDs) | ~3 min/month | Medium `35_process` patch |
| 6 | **Skip `point_forecasts.csv`** — extract → filter in memory/stream | Minor disk/time | `22_batch` + `23_filter` refactor |
| 7 | **`44_benchmark_workflow.sh`** fix robocopy `set -e` on rc=1 | Ops visibility | Done in repo; deploy |
| 8 | **Analysis-only launcher** `run_analysis_only.sh` | Avoid accidental re-pull | New thin script |

### C. Not recommended (benchmarked out)

| Idea | Why not |
|------|---------|
| SCP / SFTP from NAS | Subsystems disabled on Synology |
| NAS-primary `wgrib2` at scale | J4125 ≪ Legion5; saves network (~7 min) but loses ~20+ min on CPU |
| Mac as processor | No `wgrib2` batch path; orchestration only |
| Keep raw GRIB on D: | 40 GB/month × 72 = disk exhaustion |

### D. Future (NAS Docker path)

When `docker` is CLI-accessible on NAS:

- Use `kmia-arch-ingest` for **overnight BUILD** only if Legion5 is unavailable
- Still copy VALID_ONLY to `processed/` — analysis stays on Legion5
- DS225+ `mem_limit: 3g` caps worker count; expect **slower** than Legion5

---

## 6. Decision matrix

| Situation | Workflow |
|-----------|----------|
| **4-season precision study, CSVs missing** | Phase 1 BUILD (4 months) → Phase 2 ANALYZE |
| **4-season study, CSVs on Legion5/NAS** | Phase 2 only (~5 min) |
| **Full 2020–2025 first processing** | Phase 1 BUILD all months → sync to NAS → Phase 2 |
| **Re-run tables with new filters** | Phase 2 only |
| **Off-LAN (Tailscale)** | `NAS_PULL_MODE=ssh` + `nas-local`; expect ~40 min/month |
| **Charts for Kalshi review** | Phase 3 after Phase 2 |

---

## 7. Standard operating procedure (copy-paste)

### First-time BUILD + 4-season analysis

```bash
# Legion5 Git Bash
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1

export KMIA_EXTRACT_WORKERS=8
export NAS_SMB_THREADS=16

nohup bash /d/KMIA_Process/run_KMIA_NDFD_4Season_MaxT_Precision_2021.sh \
  >> /d/KMIA_Process/logs/processing/KMIA_NDFD_4Season_MaxT_Precision_2021.log 2>&1 &

tail -f /d/KMIA_Process/logs/processing/KMIA_NDFD_4Season_MaxT_Precision_2021.log
```

### Verify completion

```bash
ls /d/KMIA_Process/analysis/KMIA_NDFD_4Season_MaxT_Precision_2021/accuracy_report.md
head -30 /d/KMIA_Process/analysis/KMIA_NDFD_4Season_MaxT_Precision_2021/accuracy_report.md
```

### Benchmark before scaling

```bash
bash /d/KMIA_Process/scripts/44_benchmark_workflow.sh
bash /d/KMIA_Process/scripts/44b_worker_bench.sh
```

---

## 8. Role assignment (final)

| Machine | Responsibility | % of wall-clock (full archive) |
|---------|----------------|--------------------------------|
| **NAS** | Raw GRIB lake (3 TB); durable `processed/` CSV store | Storage only (~0% compute) |
| **Legion5** | BUILD (wgrib2), ANALYZE (pandas), optional charts | **~99%** |
| **Mac** | Deploy scripts, sync results, golden master reference | **~1%** (orchestration) |

---

## 9. Completed study reference

`KMIA_NDFD_4Season_MaxT_Precision_2021` validated the pipeline:

- **126 target days**, **77.3% within 2°F**, **MAE 1.20°F**
- Spring weakest (59.5% within 2°F); Fall strongest (85.6%)
- Outputs at `D:\KMIA_Process\analysis\KMIA_NDFD_4Season_MaxT_Precision_2021\`

---

*Last updated: 2026-06-16. Re-run `44_benchmark_workflow.sh` after hardware or network changes.*
