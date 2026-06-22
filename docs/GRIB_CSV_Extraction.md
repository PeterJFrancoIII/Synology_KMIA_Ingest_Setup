# GRIB-to-CSV Extraction — What Data We Pull

**Document purpose:** Reference for what the KMIA pipeline extracts from NDFD GRIB2 files into point CSVs.  
**Last updated:** 2026-06-16

---

## Pipeline at a glance

```text
NDFD GRIB2 tiles (NAS raw lake)
    → wgrib2 -lon lat per file (22_batch_extract_local_gribs.py)
    → point_forecasts.csv (all rows)
    → VALID_ONLY.csv (filtered)
    → maxt + wdir merged yearly
    → charts and accuracy tables
```

**Script:** [../ingest/scripts/22_batch_extract_local_gribs.py](../ingest/scripts/22_batch_extract_local_gribs.py)  
**Filter:** [../ingest/scripts/23_filter_valid_only.py](../ingest/scripts/23_filter_valid_only.py)  
**Monthly orchestration:** [../legion5/35_process_month_from_nas.sh](../legion5/35_process_month_from_nas.sh)

---

## Source GRIBs

| Item | Value |
|------|-------|
| Archive | AWS `s3://noaa-ndfd-pds/wmo/{subcategory}/{YYYY}/{MM}/{DD}/` |
| Station | KMIA — lat **25.7906**, lon **-80.3164** (MapClick / MFL/105,51) |
| Method | **Nearest grid point** per file (`wgrib2 ... -lon -80.3164 25.7906`) |
| Tile filter | `maxt`: `YGUZ*` (KMIA-covering tiles); `wdir`: `YBUZ*` |

**Important:** We do **not** extract the full grid. Each GRIB file can contain **multiple GRIB messages** (forecast lead times); `wgrib2 -s -vt -lon` returns **one line per message**, each becoming one CSV row.

### Release time vs filename time

NDFD archives many tile files per day. Three timestamps matter — do not confuse them:

| Concept | Source | Example |
|---------|--------|---------|
| **File post time** | Filename suffix | `YGUZ87_KWBN_202004161732` → file posted **17:32 UTC** |
| **GRIB ref time** | wgrib2 `d=` → `grib_ref_time_utc` | `d=2020041618` → model ref **18:00 UTC** |
| **Valid time** | wgrib2 `vt=` → `valid_time_utc` | `vt=2020042000` → valid **00:00 UTC** Apr 20 |

**Release time for lead-hour math is always `grib_ref_time_utc`**, not the filename. Ref times are often on the hour (16:00, 18:00, 22:00 UTC) but NDFD publishes many updates per day — do not bucket to fixed 00/06/12/18 UTC cycles.

Example from golden master: file `..._KWBN_202004161732` → `grib_ref_time_utc=2020-04-16T18:00:00Z`.

---

## Variables extracted today vs planned

| NDFD subcategory | GRIB field | In production? | Primary value column | Unit in CSV |
|------------------|------------|----------------|----------------------|-------------|
| **maxt** | TMAX, 2 m above ground | **Yes** | `value_f` (also `value_c`, `value_native`) | °F (native often Kelvin) |
| **wdir** | WDIR, 10 m above ground | **Yes** | `value_native` | degrees meteorological (wind **from**) |
| temp, td, sky, wspd, pop12, qpf | various | Planned ([Data_Source_Map.md](Data_Source_Map.md)) | `value_f`, `value_percent`, `value_mph`, etc. | per subcategory |

Example **maxt** row (from golden master):

```text
grib_ref_time_utc=2020-04-16T18:00:00Z
valid_time_utc=2020-04-20T00:00:00Z
lead_text=66-78 hour max fcst
grib_variable=TMAX
value_native=307 → value_f=92.93°F
```

Example **wdir** row:

```text
grib_ref_time_utc=2020-04-16T18:00:00Z
valid_time_utc=2020-04-19T06:00:00Z
lead_text=60 hour fcst
grib_variable=WDIR
value_native=250 (degrees)
```

---

## CSV schema (26 columns per row)

Defined in `POINT_FIELDS` in [22_batch_extract_local_gribs.py](../ingest/scripts/22_batch_extract_local_gribs.py):

| Column | Meaning |
|--------|---------|
| `extracted_at_utc` | When extract ran |
| `source` | Always `ndfd_aws` |
| `source_path` | Canonical S3 path reconstructed from local path |
| `local_path` | Path to GRIB file on Legion5/NAS |
| `requested_subcategory` | `maxt` or `wdir` |
| `station_id` | `KMIA` |
| `station_lat`, `station_lon` | Requested coordinates (25.7906, -80.3164) |
| `interp_method` | `nearest` |
| `decoder` | `wgrib2` |
| `message_number`, `byte_offset` | GRIB message index inside file |
| **`grib_ref_time_utc`** | **Forecast release / reference time** (when NDFD issued this message) |
| **`valid_time_utc`** | **Valid time** of the forecast element |
| `lead_text` | Human lead descriptor from GRIB (e.g. `66-78 hour max fcst`) |
| `grib_variable` | `TMAX`, `WDIR`, etc. |
| `level` | e.g. `2 m above ground`, `10 m above ground` |
| `lon_returned`, `lat_returned` | Actual grid point wgrib2 used |
| **`value_native`** | Raw numeric value from GRIB |
| `value_f`, `value_c` | Populated for temperature vars |
| `value_mph`, `value_inches`, `value_percent` | Populated for wind/precip/sky vars when used |
| `raw_wgrib2_line` | Full wgrib2 output line for audit |

**Semantically, each row is:** one forecast message at KMIA's nearest grid point, keyed by **release time + valid time + variable**.

---

## VALID_ONLY filter

[23_filter_valid_only.py](../ingest/scripts/23_filter_valid_only.py) drops rows where:

- `lon_returned` or `lat_returned` is missing or **≥ 900** (wgrib2 grid-miss sentinel)
- `value_native` is missing or **≥ 1e19** (GRIB fill value `9.999e+20`)

**Output files per month:**

```text
processed/points/station=KMIA/monthly/YYYY/
  ndfd_kmia_maxt_YYYYMM_VALID_ONLY.csv
  ndfd_kmia_wdir_YYYYMM_VALID_ONLY.csv
```

Intermediate `*_point_forecasts.csv` (unfiltered) is optional scratch; production uses `*_VALID_ONLY.csv`.

---

## Merge and what analysis actually uses

[24_merge_forecast_csv.py](../ingest/scripts/24_merge_forecast_csv.py) concatenates monthly VALID_ONLY files into yearly files, then merges maxt + wdir into `ndfd_kmia_point_forecasts_VALID_ONLY_{YEAR}.csv`.

[analyze_kmia_forecast_accuracy.py](../ingest/scripts/analyze_kmia_forecast_accuracy.py) then derives:

| Derived field | Source |
|---------------|--------|
| `target_date_et` | ET calendar date from `valid_time_utc` |
| `release_time_et` | From `grib_ref_time_utc` |
| `forecast_temp_f` | Median of `value_f` per (target_date, release_time) for maxt rows |
| `forecast_wdir_deg` | Median of `value_native` per (target_date, release_time) for wdir rows |
| `hours_before_target_anchor` | Release time vs anchor (currently 4 PM ET; mission doc targets observed-max time) |

Duplicate tile rows for the same release+target are **collapsed by median** (golden master caveat).

---

## Observations are NOT from GRIB

ISD hourly truth is a **separate path** — not extracted from GRIB:

- Source: NCEI Global Hourly `72202012839.csv` via [11_isd_smoke_kmia.sh](../ingest/scripts/11_isd_smoke_kmia.sh)
- Stored as: `kmia_ncei_global_hourly_{YEAR}.csv` (full ISD schema; analysis uses `DATE`, `TMP`, `WND`)
- Daily max derived in analysis: highest valid hourly `TMP` per ET calendar day + timestamp of that max + wind at max hour

---

## What we are NOT extracting from GRIB

- Full 2D grids or tiles (only one point)
- All NDFD variables (only maxt + wdir in production)
- Non-KMIA tiles (filtered by `YGUZ*` / `YBUZ*` filename patterns)
- Post-window releases (analysis filters to 0–36h before anchor after merge)
- Observed/settlement truth (comes from ISD, not NDFD)

---

## File size context

Per month (typical):

- Raw GRIB: ~50 GB (maxt ~10 GB + wdir ~40 GB)
- VALID_ONLY CSV: ~43 MB total
- Rows: ~8k maxt + ~85k wdir messages (many lead times per release file)

This is why the **CSV lake on NAS** matters: repeat analysis pulls megabytes, not terabytes of GRIB.

---

## Related docs

- [PROJECT_STATE_AND_OBJECTIVES.md](../0_Developer_Source_Files/PROJECT_STATE_AND_OBJECTIVES.md) — mission, architecture, pipeline overview
- [Data_Source_Map.md](Data_Source_Map.md) — upstream sources and NDFD variable list
- [OPTIMAL_ANALYSIS_WORKFLOW.md](OPTIMAL_ANALYSIS_WORKFLOW.md) — BUILD/ANALYZE performance workflow
