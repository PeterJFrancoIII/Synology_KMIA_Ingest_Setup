# KMIA NDFD Ingest & Forecast-Precision System — State, Objectives, and Charting Tools

**Document purpose:** Handoff summary for onboarding a new chat or contributor.  
**Last updated:** 2026-06-22  
**Canonical repo:** `/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup`  
**Operating mode:** Research / dry-run / ingestion only — **no live trading**

---

## 1. Mission and Ultimate Objective

This system exists to support **Kalshi KMIA daily maximum-temperature market research**. The core question is not merely “what did NDFD forecast?” but:

> **When, and under what weather conditions, are NDFD max-temperature forecasts most accurate relative to the observed daily maximum at KMIA (Miami International Airport)?**

That question drives everything downstream: ingest design, VALID_ONLY filtering, the golden-master chart format, and the quantitative accuracy analysis (`analyze_kmia_forecast_accuracy.py`).

### Three research questions the analysis layer answers


| #                                        | Question                                                                                                                                                                                                 | Primary outputs                                                                                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1 — Lead time & observed max timing** | How many hours before the **observed daily max temperature** on the target date does the forecast best predict that max? And **at what time (ET) did the observed daily max occur** on each target date? | `lead_hour_accuracy.csv`, `best_lead_hour_per_day.csv`, `lead_hour_accuracy_by_season.csv`, `kmia_*_daily_summary.csv` (observed max timestamp per day) |
| **Q2 — Weather conditions**              | How do **wind direction**, **forecast stability**, and **intra-day forecast spread** affect accuracy?                                                                                                    | `conditions_accuracy.csv`                                                                                                                               |
| **Q3 — Seasonality**                     | Which times of year are forecasts most/least accurate, and why (Miami dry season vs convective summer)?                                                                                                  | `seasonal_by_month.csv`, `four_season_precision_summary.csv`, `accuracy_report.md`                                                                      |


### Success criteria

1. **Complete historical archive** of NDFD point forecasts + NCEI ISD observations for KMIA (2020–2026 target span).
2. **Reproducible charts** for any processed period — visually comparing every forecast release to observed max.
3. **Quantified precision tables** (% within 1°F / 2°F / 3°F, MAE, bias) sliced by lead hour, stability class, wind regime, and season.
4. Eventually: inform **when to trust** NDFD for Kalshi max-temp settlement research (still dry-run only).

---

## 2. System Architecture (Three Machines)

Three-machine **topology** is unchanged (Mac → NAS → Legion5). Production data movement and compute use **SMB3 robocopy + parallel `wgrib2`** on Legion5 — not tar-over-SSH serial pulls.

**Canonical speed workflow:** [Research/Agent Analysis of KMIA Forecast Precision/OPTIMAL_ANALYSIS_WORKFLOW.md](../Research/Agent%20Analysis%20of%20KMIA%20Forecast%20Precision/OPTIMAL_ANALYSIS_WORKFLOW.md)  
**Optimization summary:** [2026-06-15_infrastructure_optimization_summary.md](../Research/Agent%20Analysis%20of%20KMIA%20Forecast%20Precision/2026-06-15_infrastructure_optimization_summary.md)  
**Bottleneck analysis:** [2026-06-16_system_bottleneck_analysis.md](../Research/Agent%20Analysis%20of%20KMIA%20Forecast%20Precision/2026-06-16_system_bottleneck_analysis.md)

### Machine roles


| Machine     | Role                                                                | Transport / compute                                                                                                               |
| ----------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Mac**     | Script source of truth, deploy, SSH launch to Legion5               | rsync/scp to NAS; ~1% wall-clock (orchestration only)                                                                             |
| **NAS**     | Immutable raw GRIB lake + durable processed CSV lake; **Kalshi live ingest** (`kmia-arch-ingest`, `kmia-paper-research`, `kmia-orderbook-ws`) | Storage + scheduled policy/paper loop + **WS orderbook archive**; not primary `wgrib2` compute |
| **Legion5** | Primary compute: BUILD + ANALYZE phases                             | **SMB3** robocopy from `Z:` (~95 MB/s LAN); parallel extract (`KMIA_EXTRACT_WORKERS`); SSH tar **fallback only** when `Z:` absent |


### Optimized processing path (2026-06-15+)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  Mac — scripts, docs, deploy (~1% wall-clock)                               │
│  rsync deploy → NAS setup_repo; SSH → Legion5 run_*.sh                      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  NAS — Synology DS225+ (MediaServer2)                                       │
│  /volume2/Data/App_Development/KMIA_Ingest                                  │
│  • raw/ — immutable GRIB lake (~3 TB, 2020–2025)                            │
│  • processed/points/station=KMIA/monthly/ — VALID_ONLY CSV lake (target)    │
│  • Docker kmia-arch-ingest for on-NAS ingest                                │
└───────────────┬─────────────────────────────────────┬───────────────────────┘
                │ SMB3 robocopy (BUILD: pull GRIB)    │ SMB3 (ANALYZE: pull CSVs)
                │ Z: → D:\KMIA_Process                │ ~43 MB/month vs ~50 GB GRIB
                ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Legion5 — primary compute (D:\KMIA_Process; toolchain on E:)               │
│                                                                             │
│  PHASE 1 BUILD (once per month):                                            │
│    SMB pull raw GRIB → parallel wgrib2 (22_batch_extract_local_gribs.py)    │
│    → VALID_ONLY filter → write monthly CSVs back to NAS → delete local raw  │
│                                                                             │
│  PHASE 2 ANALYZE (repeat):                                                  │
│    SMB pull VALID_ONLY CSVs only → merge → analyze + charts                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

**One-time Legion5 setup:** `legion5/43_setup_nas_smb.ps1` (mount `Z:`) + source `legion5/kmia_legion5_env.sh` from all launchers.

### Optimized Network


| Layer              | Optimized (LAN default)                                                      |
| ------------------ | ---------------------------------------------------------------------------- |
| NAS → Legion5 pull | **SMB3 robocopy** via `Z:` (~5–7 min, ~95 MB/s)                              |
| Extract            | **Parallel** `--workers` (4 measured; **8 recommended** for 72-month run)    |
| Per month          | **~26 min** (4 workers); target **~18–20 min** (8 workers + overlapped pull) |
| Repeat analysis    | **SMB pull CSVs only** (~1000× smaller than raw GRIB)                        |


### Wall-clock targets (benchmarks)


| Task                                | Fastest path                | Est. time             |
| ----------------------------------- | --------------------------- | --------------------- |
| Re-run analysis (CSVs exist)        | Legion5 merge + analyze     | **2–5 min**           |
| 4-season study (first BUILD)        | SMB + workers               | **~1.0–1.5 h**        |
| Full 2020–2025 BUILD (72 months)    | SMB + w=8 + CSV lake on NAS | **~20–24 h** one-time |
| Full archive analysis (after BUILD) | SMB pull CSVs from NAS      | **~15–30 min**        |


**Remaining bottleneck:** wdir `wgrib2` extract on Legion5 (~65% of per-month time). Network is no longer the primary limiter after SMB optimization.

### SSH hosts


| Alias                                | Role                                                      |
| ------------------------------------ | --------------------------------------------------------- |
| `MediaServer2` / `MediaServer2Local` | Synology NAS (LAN `192.168.0.193:23921`, user `Viper117`) |
| `Legion5` / `Legion5Local`           | Windows processor (`legion5.taild0730.ts.net` or LAN)     |


### Storage layout (NAS canonical)

```text
/volume2/Data/App_Development/KMIA_Ingest/
  raw/forecast/ndfd_aws/{maxt,wdir,...}/YYYY/MM/   # immutable GRIB
  raw/observed/isd/YYYY/72202012839.csv
  processed/points/station=KMIA/
    monthly/YYYY/ndfd_kmia_{maxt,wdir}_YYYYMM_VALID_ONLY.csv
    yearly/
    ndfd_kmia_point_forecasts_VALID_ONLY_YYYY.csv
    kmia_ncei_global_hourly_YYYY.csv
    kmia_YYYY_PLUS_mean_median_stability_wind_*.csv
    kmia_YYYY_stability_wind.png
  manifest/   # checksums, gaps, retries
  logs/
```

---

## 3. Current State (as of 2026-06-16)

### NAS ingest — COMPLETE

- **~3.0 TB** raw NDFD GRIB on NAS; years **2020–2025** ingested.
- AWS NDFD archive begins **2020-04-16** (no Jan–Mar 2020 on S3).
- **2026 ingest attempted but 0 files** (month path bug: `2026/1/` vs `2026/01/`).
- **2021 gap on NAS:** Jan–Mar missing; only Apr–Dec present. Winter seasonal samples use **December** not January.

### Legion5 processing — COMPLETE (4-season study)

- Workspace: `D:\KMIA_Process` (~185 GB free on D:).
- **Default workflow:** See `**Research/Agent Analysis of KMIA Forecast Precision/OPTIMAL_ANALYSIS_WORKFLOW.md`**
- **Completed study:** `KMIA_NDFD_4Season_MaxT_Precision_2021` — reports archived under `Research/Agent Analysis of KMIA Forecast Precision/`

### Golden master (Mac reference, DO NOT EDIT)

Location:

```text
/Users/computer/Desktop/App Development/Kalshi/1_Downloads/NCEI_Historical_Ingest/
  GOLDEN_MASTER_DO_NOT_TOUCH_kmia_ndfd_forecast_vs_observed_CURRENT_WITH_WIND/
```

This folder is the **visual format reference**. All new chart work must copy from it, not edit in place.

---

## 4. Data Pipeline (Raw → Chart-Ready)

**GRIB extract reference:** [GRIB_CSV_Extraction.md](GRIB_CSV_Extraction.md) — columns, variables, VALID_ONLY rules, and what analysis consumes.

```text
AWS noaa-ndfd-pds (NDFD GRIB2)
    ↓ ingest (NAS container or Legion5 pull)
raw/forecast/ndfd_aws/{maxt,wdir}/YYYY/MM/*.grib2
    ↓ wgrib2 nearest-grid extract (22_batch_extract_local_gribs.py)
point CSV per month (all rows, incl. invalid 999/9.999e+20)
    ↓ VALID_ONLY filter (23_filter_valid_only.py)
monthly *VALID_ONLY.csv
    ↓ merge maxt + wdir (24_merge_forecast_csv.py, 28_merge_yearly_forecast_csv.py)
ndfd_kmia_point_forecasts_VALID_ONLY_{YEAR}.csv
    ↓ parallel path
NCEI ISD 72202012839 → kmia_ncei_global_hourly_{YEAR}.csv
    ↓
CHARTS (matplotlib) + ANALYSIS (pandas tables)
```

### Critical ingest rules

1. **NDFD is forecast data** — never treat as observed truth.
2. **VALID_ONLY filter** removes grid misses (`lon/lat 999`, sentinel values `9.999e+20`).
3. **Do not hard-code grid cell** — derive nearest point per GRIB file.
4. **Use GRIB message ref time for release time** (`grib_ref_time_utc` from wgrib2 `d=`). Do not parse release time from filenames (those are file-post times like `..._202004161732`). Do not round or bucket releases to fixed 00/06/12/18 UTC cycles — NDFD can publish many updates per day; keep each distinct ref time.
5. **Lead-time window (target):** 0–36 hours before the **observed daily max timestamp** on the target date. *Current golden-master pipeline still filters on a fixed **4 PM ET** anchor — see §5.5; redesign should re-anchor lead hours to observed-max time.*

### Variables in active use


| Variable        | NDFD subcategory | Chart role                           |
| --------------- | ---------------- | ------------------------------------ |
| Max temperature | `maxt`           | Primary Y-axis; all accuracy metrics |
| Wind direction  | `wdir`           | Label annotations (arrows/cardinals) |


Planned: `td`, `sky`, `wspd`, `pop12`, `qpf`.

---

## 5. Charting Tools — Detailed Reference

Charting is the **primary human-facing deliverable** of this system. The charts translate raw GRIB + ISD into actionable visual intelligence for Kalshi max-temp research: *how confident was the model, how did forecasts evolve, did observed max fall inside the envelope, and what was the wind regime?*

### 5.1 Golden Master — `chart_kmia_PLUS_mean_median_stability_wind.py`

**Location (protected):**  
`Kalshi/.../GOLDEN_MASTER_DO_NOT_TOUCH_.../chart_kmia_PLUS_mean_median_stability_wind.py`

**Status:** DO NOT TOUCH. Visual format lock as of 2026-06-03.

#### What the chart shows


| Element                           | Meaning                                                       |
| --------------------------------- | ------------------------------------------------------------- |
| **X axis**                        | Target date (ET calendar day for daily max)                   |
| **Y axis**                        | Temperature °F (forecast and observed on same scale)          |
| **Vertical shaded bar**           | Min–max range of all NDFD max-t releases for that target date |
| **Dots**                          | Each individual forecast release (one dot per release time)   |
| **Dot Y position**                | Median max-t for that release (deduped from tile rows)        |
| **Stacked labels (right of bar)** | Release time, lead hours, forecast °F, wind arrow + cardinal  |
| **Diamond**                       | Mean of all releases that day                                 |
| **Horizontal tick**               | Median of all releases                                        |
| **Circle line**                   | Latest release before anchor                                  |
| **X marker**                      | Observed daily max (from ISD hourly, highest valid TMP)       |
| **Observed label (left of X)**    | Obs temp, timestamp, observed wind arrow                      |
| **Top banner per day**            | Stability class + outcome class + forecast range °F           |
| **Bottom-left text box**          | Observed max timing stats (mean/median/range of hour-of-day)  |


#### Classification logic (shared across all chart + analysis scripts)

**Forecast stability** (intra-day spread among releases):


| Class        | Criteria                                                       |
| ------------ | -------------------------------------------------------------- |
| **STABLE**   | range ≤ 1.5°F AND std ≤ 0.75°F AND first→latest change ≤ 1.0°F |
| **MIXED**    | range ≤ 3.0°F AND std ≤ 1.5°F AND first→latest change ≤ 2.0°F  |
| **UNSTABLE** | anything worse                                                 |


**Outcome vs observed** (did the day's forecast envelope capture truth?):


| Class         | Criteria                                    |
| ------------- | ------------------------------------------- |
| **VERIFIED**  | observed max ∈ [min forecast, max forecast] |
| **WARM MISS** | observed > max forecast by < 2°F            |
| **WARM BUST** | observed > max forecast by ≥ 2°F            |
| **COOL MISS** | observed < min forecast by < 2°F            |
| **COOL BUST** | observed < min forecast by ≥ 2°F            |


#### What the golden master aims to achieve

1. **See forecast evolution** — every release before settlement window, not just the latest.
2. **Spot stable vs chaotic days** — STABLE days are higher-confidence trading candidates.
3. **Relate wind to busts** — easterly flow vs sea-breeze / convective patterns visible in labels.
4. **Time the observed max** — record when KMIA actually peaked (ET timestamp) and measure forecast lead relative to that moment, not a fixed clock anchor.
5. **Visual settlement research** — dry-run: “would I have been inside the envelope at my entry lead time?”

#### Golden master outputs

```text
kmia_PLUS_mean_median_stability_wind.png          # chart
kmia_PLUS_mean_median_stability_wind_points.csv   # per-release rows
kmia_PLUS_mean_median_stability_wind_daily_summary.csv  # per-day aggregates
ndfd_kmia_point_forecasts_VALID_ONLY.csv          # merged forecast input
kmia_ncei_global_hourly_2020.csv                  # ISD input
```

---

### 5.2 Year Chart — `ingest/scripts/chart_kmia_year_stability_wind.py`

**Purpose:** Production chart generator for a **full calendar year** after year-finalize pipeline.

**Invoked by:** `legion5/32_finalize_year.sh` (and NAS `28_nas_year_process.sh` equivalent).

**Inputs (env vars):**

```bash
KMIA_ROOT          # data root
KMIA_YEAR          # e.g. 2020
KMIA_FORECAST_CSV  # ndfd_kmia_point_forecasts_VALID_ONLY_{YEAR}.csv
KMIA_OBS_CSV       # kmia_ncei_global_hourly_{YEAR}.csv
```

**Outputs:**

```text
processed/points/station=KMIA/
  kmia_{YEAR}_PLUS_mean_median_stability_wind_points.csv
  kmia_{YEAR}_PLUS_mean_median_stability_wind_daily_summary.csv
  kmia_{YEAR}_stability_wind.png
```

**Behavior:** Implements the **same visual spec as golden master** for an entire year. Figure width scales with day count (`max(24, n_days * 1.1)` inches). Label stacking algorithm prevents overlapping release annotations.

**Aims to achieve:**

- One PNG per year for archival review and year-over-year comparison.
- CSV sidecars for programmatic drill-down without re-parsing GRIB.
- Automated step at end of year pipeline — charts are not manual.

---

### 5.3 Long-Period Chart — `ingest/scripts/chart_kmia_long_period_stability_wind.py`

**Purpose:** Extend golden-master readability to **multi-month or multi-year spans** without unreadable label density.

**Modes (`--mode`):**


| Mode       | Behavior                                                                 |
| ---------- | ------------------------------------------------------------------------ |
| `detail`   | Golden-master full labels, **chunked** (default 7 days/page)             |
| `overview` | Full date span, envelope + markers only — **no per-release label stack** |
| `both`     | Emits overview + all detail chunks                                       |


**CLI example:**

```bash
python chart_kmia_long_period_stability_wind.py \
  --mode both \
  --chunk-days 7 \
  --data-dir /path/to/station=KMIA \
  --out-dir /path/to/charts
```

**Outputs:**

```text
kmia_stability_wind_overview_{start}_to_{end}.png
kmia_stability_wind_detail_{chunk_start}_to_{chunk_end}.png  # one per chunk
kmia_PLUS_mean_median_stability_wind_points.csv               # if not exists
kmia_PLUS_mean_median_stability_wind_daily_summary.csv
```

**Aims to achieve:**

1. **Macro patterns** — overview shows seasonal accuracy drift, systematic warm bias months.
2. **Micro forensics** — detail chunks preserve golden-master label fidelity for case studies.
3. **Bridge ingest → research** — after full 2020–2025 processing, generate readable chart sets without hand-tuning matplotlib.

---

### 5.4 Accuracy Analysis (tabular companion) — `analyze_kmia_forecast_accuracy.py`

**Not a chart**, but implements the **same methodology** as charts and answers the three research questions quantitatively.

**Inputs:**

- Merged `ndfd_kmia_point_forecasts_VALID_ONLY*.csv`
- ISD `kmia_ncei_global_hourly_*.csv`

**Outputs:**


| File                                | Content                                                            |
| ----------------------------------- | ------------------------------------------------------------------ |
| `accuracy_report.md`                | Narrative summary                                                  |
| `lead_hour_accuracy.csv`            | Q1: accuracy by lead-hour bucket (hours before observed daily max) |
| `best_lead_hour_per_day.csv`        | Q1: optimal lead per target date + observed max timestamp          |
| `lead_hour_accuracy_by_season.csv`  | Q1 sliced by four-season sample                                    |
| `conditions_accuracy.csv`           | Q2: stability, wind, range buckets                                 |
| `seasonal_by_month.csv`             | Q3: calendar month patterns                                        |
| `four_season_precision_summary.csv` | Q3: one-month-per-season study                                     |
| `accuracy_points_enriched.csv`      | Full enriched row-level data                                       |


**Accuracy metrics:**

- **Within 1°F / 2°F / 3°F:** `|forecast − observed daily max|`
- **Verified in range:** observed max inside that day's min–max release envelope
- **MAE, bias** per grouping

**Relationship to charts:** Charts show *why* a day busted; analysis tables show *how often* busts occur by lead hour, wind, and season. Together they form the research loop.

---

### 5.5 Chart methodology constants (all tools)

```python
MAX_HOURS_BEFORE_TARGET_ANCHOR = 36.0   # only releases 0–36h before anchor
TARGET_ANCHOR_HOUR_ET = 16              # CURRENT: fixed 4 PM ET (golden-master legacy)
# TARGET: anchor = observed daily max timestamp per target date (see Q1)
```

**Observed daily max derivation:**

- Parse ISD `TMP` (tenths °C), convert to °F.
- Group by ET target date; take **highest valid hourly reading** (first occurrence on ties).
- Parse `WND` for observed wind direction at max hour.

**Wind display:**

- Meteorological wind direction = **from** direction.
- Chart arrows show approximate **flow-to** direction (rotate 180°).
- Eight compass buckets: N, NE, E, SE, S, SW, W, NW.

---

## 6. Active Study: Four-Season Precision Analysis

**Study ID:** `KMIA_NDFD_4Season_MaxT_Precision_2021`


| Season | Month   | Notes                                        |
| ------ | ------- | -------------------------------------------- |
| Winter | 2021-12 | Dec used because Jan–Mar 2021 missing on NAS |
| Spring | 2021-04 |                                              |
| Summer | 2021-07 |                                              |
| Fall   | 2021-10 |                                              |


**Pipeline:**

```bash
# Legion5 launcher
/d/KMIA_Process/run_KMIA_NDFD_4Season_MaxT_Precision_2021.sh
  → 42_kmia_4season_maxt_precision_analysis.sh
    → 35_process_month_from_nas.sh (×4 months)
    → merge CSVs
    → analyze_kmia_forecast_accuracy.py --four-season-sample
```

**Expected analysis output directory:**

```text
D:\KMIA_Process\analysis\KMIA_NDFD_4Season_MaxT_Precision_2021\
```

After this study validates the pipeline, scale to **full 2020–2025** processing + yearly charts.

---

## 7. Key Scripts Map


| Script                                                    | Role                                     |
| --------------------------------------------------------- | ---------------------------------------- |
| `ingest/scripts/22_batch_extract_local_gribs.py`          | wgrib2 batch extract to point CSV        |
| `ingest/scripts/23_filter_valid_only.py`                  | Remove invalid grid/sentinel rows        |
| `ingest/scripts/24_merge_forecast_csv.py`                 | Join maxt + wdir on release keys         |
| `ingest/scripts/28_merge_yearly_forecast_csv.py`          | Concat monthly VALID_ONLY files          |
| `ingest/scripts/11_isd_smoke_kmia.sh`                     | Download ISD for a year                  |
| `ingest/scripts/chart_kmia_year_stability_wind.py`        | **Year golden-master chart**             |
| `ingest/scripts/chart_kmia_long_period_stability_wind.py` | **Multi-month overview + detail chunks** |
| `ingest/scripts/analyze_kmia_forecast_accuracy.py`        | **Quantitative precision analysis**      |
| `legion5/35_process_month_from_nas.sh`                    | Pull one month NAS → VALID_ONLY          |
| `legion5/36_process_all_from_nas.sh`                      | Full year loop                           |
| `legion5/32_finalize_year.sh`                             | Merge year + **run year chart**          |
| `legion5/42_kmia_4season_maxt_precision_analysis.sh`      | Four-season study pipeline               |
| `legion5/nas_pull_helpers.sh`                             | SMB/SSH NAS pull helpers                 |
| `legion5/43_benchmark_pull_modes.sh`                      | tar vs SMB pull benchmark                |
| `legion5/44_benchmark_workflow.sh`                        | Full workflow timing benchmark           |


---

## 8. Known Issues and Caveats


| Issue                               | Impact                                  | Mitigation                                                          |
| ----------------------------------- | --------------------------------------- | ------------------------------------------------------------------- |
| Legion5 E: drive full               | Cannot process on E:                    | Use `D:\KMIA_Process` only                                          |
| Synology scp subsystem broken       | scp fails                               | tar over SSH or **SMB robocopy** (default on LAN)                   |
| SSH ControlMaster hangs Legion5↔NAS | Stalled pulls                           | `NAS_SSH_OPTS="-o ControlMaster=no"`                                |
| 2021 Jan–Mar missing on NAS         | Winter sample uses Dec                  | Document in seasonal studies                                        |
| 2026 zero-file ingest               | Month zero-padding bug                  | Fix path resolver before 2026 ingest                                |
| Duplicate NDFD tile rows            | Same release/target collapsed by median | Golden master caveat; filter canonical product family in production |
| Forecast ≠ observed                 | Settlement research only                | Never use NDFD as truth                                             |


---

## 9. Recommended Next Steps (for new chat)

1. **Follow** `Research/Agent Analysis of KMIA Forecast Precision/OPTIMAL_ANALYSIS_WORKFLOW.md` for full 2020–2025 BUILD + ANALYZE.
2. **Review** completed 4-season results in `Research/Agent Analysis of KMIA Forecast Precision/KMIA_NDFD_4Season_MaxT_Precision_2021/`.
3. **Run year charts** for any completed year via `32_finalize_year.sh` → `chart_kmia_year_stability_wind.py`.
4. **Scale processing** 2020–2025 on Legion5 (`36_process_all_from_nas.sh`) with `KMIA_EXTRACT_WORKERS=8`.
5. **Sync VALID_ONLY CSVs to NAS** `processed/points/station=KMIA/monthly/` after each month.
6. **Close 2026 ingest bug** and backfill 2021 Q1 if raw exists elsewhere.
7. **Kalshi trading bridge:** Run `ingest/scripts/run_daily_policy_refresh.sh`; review `policy_review_for_human.txt` in Kalshi repo; approve policy when satisfied. See `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`.

---

## 10. How Charting Connects to Kalshi Research (Intent)

```text
                    ┌─────────────────────────────┐
                    │  Kalshi KMIA Max-T Market   │
                    │  (daily settlement research)│
                    └──────────────┬──────────────┘
                                   │
                    "At H hours before observed daily max,
                     how accurate is NDFD max-t?
                     When did observed max occur?"
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  Golden-master chart      Accuracy tables           Long-period charts
  (per-day forensics)      (aggregate precision)     (seasonal/regime trends)
         │                         │                         │
         └─────────────────────────┴─────────────────────────┘
                                   │
                    Trading research insights (dry-run):
                    • Best lead hour to enter
                    • Skip UNSTABLE / wide-range days
                    • Seasonal bias correction
                    • Wind-regime conditional accuracy
```

The charts are not decorative output — they are the **design spec** for what “good” forecast-observation comparison looks like, and the analysis layer exists to **measure** what the charts suggest visually.

---

## 11. Reference Paths Quick Copy

```text
# Mac setup repo (this project)
/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup

# Golden master (DO NOT EDIT)
/Users/computer/Desktop/App Development/Kalshi/1_Downloads/NCEI_Historical_Ingest/GOLDEN_MASTER_DO_NOT_TOUCH_kmia_ndfd_forecast_vs_observed_CURRENT_WITH_WIND/

# NAS data lake
/volume2/Data/App_Development/KMIA_Ingest

# Legion5 processor
D:\KMIA_Process
```

---

## 12. Kalshi trading-policy bridge (2026-06-20)

Console 2 now exports **backtested trading policy** for Console 3 (Kalshi repo) — file-only, no shared imports.

| Topic | Detail |
|-------|--------|
| **Anchor** | Prior-day **10 AM ET** (Kalshi bin open), not 4 PM NDFD research anchor |
| **Weather join** | NWS snapshot → rules_v2 → IEM GFS MOS (forecast); NCEI CLIMIA TMAX (observed) |
| **Backtest** | `historical_checksum_backtest.py --mode kalshi`; hedged maker/taker sim |
| **Policy export** | `trading_policy.json` / `trading_policy_draft.json` via `export_trading_policy.py` |
| **Liquidity** | ~$121k/event-day; caps at 25% top-of-book, 0.5% volume, 25 contracts/leg |
| **Human gate** | `approved_by_human: true` required before Console 3 applies policy overrides |
| **State doc** | `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md` |
| **Kalshi doc** | `../Kalshi/docs/TRADING_POLICY_AND_LIQUIDITY.md` |

**Do not conflate:** MAE charts use **4 PM ET** NDFD releases; Kalshi backtest uses **10 AM ET** prior-day prices and forecast-at-anchor join.

---

## 13. Kalshi WebSocket orderbook ingest (2026-06-22)

Finest book granularity for KXHIGHMIA: continuous WebSocket `orderbook_delta` on NAS.

| Topic | Detail |
|-------|--------|
| **Container** | `kmia-orderbook-ws` (same image as `kmia-paper-research`, separate long-running service) |
| **Code home** | Kalshi repo `backend/src/market_data/orderbook_ws_*.py`, `kalshi_ws_client.py` |
| **NAS orchestration** | Console 2 `docker/kmia-paper-research/`, `synology/scripts/deploy_*_to_nas.sh` |
| **Raw archive** | `Kalshi/backend/data/processed/kalshi_market_archive/orderbook_ws/YYYY-MM-DD.jsonl` |
| **Checkpoints** | `.../orderbook_ws_snapshots/` (60s reconstructed full book) |
| **Health** | `.../ws_daemon_status.json` |
| **Fallback** | REST 5-min `orderbooks/` from paper loop |
| **Phase 2** | Backtest loader at 10 AM ET anchor — not yet wired |
| **Design doc** | `docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md` |
| **Handoff** | `docs/handoffs/KALSHI_WS_ORDERBOOK_INGEST_20260622.md` |

**Deploy:** `NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh` then rebuild compose and `docker compose up -d kmia-orderbook-ws`.

---

*End of handoff document.*