# KMIA Historical Ingest Program — Current State and How We Achieved It

**Date:** 2026-06-08  
**Project:** Kalshi / KMIA Historical Forecast + Observation Research Pipeline  
**Scope:** Current state only, plus how we reached this state.

---

## 1. Current Program State

We now have a working prototype pipeline for KMIA historical weather forecast and observation analysis.

The current purpose of the program is:

```text
For KMIA:
1. Ingest historical NDFD forecast data.
2. Extract point forecasts at or near KMIA.
3. Pull observed KMIA historical station data.
4. Compare forecasted max temperature vs observed max temperature.
5. Visualize forecast range, individual forecast releases, observed max timing, forecast stability, and wind direction.
```

The target station is:

```text
KMIA — Miami International Airport
```

The current historical forecast source is:

```text
NOAA / NWS NDFD archive from AWS Open Data:
s3://noaa-ndfd-pds/wmo/<variable>/<YYYY>/<MM>/<DD>/
```

The current observed-data source is:

```text
NCEI Global Hourly / ISD
KMIA station file: 72202012839.csv
```

The current forecast variables actively tested are:

```text
maxt = forecasted maximum temperature
wdir = forecasted wind direction
```

The desired future variables remain:

```text
maxt
td
sky
wdir
wspd
pop12 / pop
qpf
```

---

## 2. Local Mac Pipeline State

On the local Mac, we created and tested an NDFD ingestion workflow using:

```text
/Users/computer/Desktop/App Development/Kalshi/1_Downloads/NCEI_Historical_Ingest/ingest_kmia_ndfd_forecasts.py
```

The script downloads NDFD WMO GRIB files, extracts KMIA point values using `wgrib2`, and writes processed point data.

We confirmed that the NDFD data being downloaded is forecast data, not observed data.

We also discovered that the NDFD archive contains many regional or product files that do not cover KMIA. Those invalid files return values like:

```text
lon_returned = 999
lat_returned = 999
value_native = 9.999e+20
```

Therefore, we created valid-only CSV files by filtering out invalid rows.

Important local processed files include:

```text
ndfd_kmia_point_forecasts.csv
ndfd_kmia_point_forecasts_VALID_ONLY.csv
kmia_ncei_global_hourly_2020.csv
```

---

## 3. Golden-Master Chart State

We developed a protected golden-master visualization for comparing NDFD forecasted max temperatures against observed KMIA max temperatures.

The latest golden master includes:

```text
X axis = target date
Y axis = forecasted / observed max temperature in °F
Vertical range line = forecasted max-temp range for that target date
Dots = individual historical NDFD forecast releases
Dot Y-position = predicted max temperature
Forecast labels = stacked cleanly to the right of each target-date vertical line
Observed max = X marker
Observed label = placed to the left of the observed max marker
Observed label includes observed max temperature and observed timestamp
Mean forecast marker = diamond
Median forecast marker = horizontal tick
Forecast stability label = STABLE / MIXED / UNSTABLE
Outcome label = VERIFIED / WARM MISS / WARM BUST / COOL MISS / COOL BUST
Observed max timing summary = mean, median, earliest, latest observed max time
Forecast wind direction = shown only inside forecast labels
Observed wind direction = shown only inside the observed max label
```

The newest protected golden-master folder is:

```text
GOLDEN_MASTER_DO_NOT_TOUCH_kmia_ndfd_forecast_vs_observed_CURRENT_WITH_WIND
```

A timestamped backup exists under:

```text
backups/GOLDEN_MASTER_DO_NOT_TOUCH_kmia_ndfd_forecast_vs_observed_WITH_WIND_<timestamp>
```

Important rule:

```text
Do not edit the protected golden master directly.
Future experiments must copy it first and work from the copy.
```

---

## 4. Current Chart Script

The latest wind-enhanced chart script is:

```text
chart_kmia_PLUS_mean_median_stability_wind.py
```

It reads from the current valid-only NDFD data and NCEI observed data, then outputs:

```text
kmia_PLUS_mean_median_stability_wind.png
kmia_PLUS_mean_median_stability_wind_points.csv
kmia_PLUS_mean_median_stability_wind_daily_summary.csv
```

The chart currently uses a high-temperature trading anchor of:

```text
4 PM ET on the target date
```

Forecasts are filtered to:

```text
0 to 36 hours before the 4 PM ET target-date anchor
```

This removed bad negative-lead forecasts that were released after the relevant high-temperature window.

---

## 5. Key Logic Decisions

### 5.1 Forecast Target-Date Interpretation

We originally mapped target date from:

```text
valid_time_utc converted to Eastern date
```

Then we realized NDFD `maxt` can describe a forecast window, not always a perfect calendar-day high.

To reduce invalid comparisons, we anchored the verification window around:

```text
4 PM ET target-date high-temperature anchor
```

and filtered forecasts to:

```text
0 <= hours_before_target_anchor <= 36
```

### 5.2 Observed Max Timing

We added the timestamp when the observed max temperature occurred.

This helped identify cases where a later forecast appeared lower than an already-observed high, which usually means the later NDFD forecast was not forecasting the full day’s already-achieved maximum.

### 5.3 Forecast Stability Classification

We added simple stability rules:

```text
STABLE:
forecast range <= 1.5°F
forecast std <= 0.75°F
first-to-latest forecast change <= 1.0°F

MIXED:
forecast range <= 3.0°F
forecast std <= 1.5°F
first-to-latest forecast change <= 2.0°F

UNSTABLE:
anything wider or more volatile
```

### 5.4 Outcome Classification

We added outcome verification classes:

```text
VERIFIED  = observed max inside forecast range
WARM MISS = observed max slightly above forecast range
WARM BUST = observed max >= 2°F above forecast range
COOL MISS = observed max slightly below forecast range
COOL BUST = observed max >= 2°F below forecast range
```

### 5.5 Wind Direction

We added wind direction using approximate arrows.

Important interpretation:

```text
NCEI observed wind direction and NDFD wdir are meteorological wind directions.
They indicate where wind is FROM.

The chart arrows show approximate wind-flow direction, so the script rotates by 180°.
```

We decided wind arrows should appear only in:

```text
forecasted-data labels
observed max label
```

and not as extra standalone arrows around the chart.

---

## 6. MADIS / NCEI Historical Ingest Server State

The MADIS server is:

```text
104.248.119.62
```

It is a protected MADIS LDM ingest/relay server. We decided not to mix historical-data storage with the live LDM queue/service.

Historical KMIA workspace on the server:

```text
/data/historical_kmia
```

Key server folders:

```text
/data/historical_kmia/bin
/data/historical_kmia/raw
/data/historical_kmia/processed
/data/historical_kmia/logs
/data/historical_kmia/manifests
/data/historical_kmia/tmp
/data/historical_kmia/backups
```

We installed `wgrib2` successfully on the server using Miniforge/Mamba because Ubuntu `apt` did not provide it.

Current working `wgrib2` version:

```text
wgrib2 3.8.0
```

We had to add temporary swap because the server is very small:

```text
RAM: about 458 MiB
CPU: 1 core
Disk: about 8.7 GB root volume
```

The server successfully ran a one-day NDFD smoke test for:

```text
2020-04-16
variables: maxt,wdir
```

Smoke test result:

```text
Keys seen: 189
Files downloaded: 189
Point rows extracted: 2567
Valid KMIA point rows after filtering: 1138
```

---

## 7. Server Storage State

We found the VPS is not large enough to retain raw NDFD GRIB files.

One test day used roughly:

```text
maxt raw files: ~88 MB
wdir raw files: ~598 MB
raw total: ~686 MB
```

The disk filled to 100%, leaving about:

```text
25 MB free
```

We cleaned it up and recovered space to about:

```text
1.8 GB free
```

The important conclusion:

```text
The VPS is adequate for processed KMIA point extracts.
The VPS is not adequate for long-term raw NDFD retention.
```

The correct future server ingest workflow is:

```text
download raw GRIB for one day
extract KMIA point rows
append processed CSV
regenerate valid-only CSV
sync to Synology NAS
delete raw GRIBs
continue
```

We created a cleanup script:

```text
/data/historical_kmia/bin/cleanup_historical_kmia_raw.sh
```

Its job is to preserve processed data but remove raw GRIBs and caches.

---

## 8. Synology NAS State

A Synology NAS is available and should become the durable archive target.

The Synology host used during testing was:

```text
peterjfrancoiii2.synology.me
```

The Synology user shown in the terminal was:

```text
Viper117
```

A Synology audit archive was successfully generated and downloaded to the Mac at:

```text
/Users/computer/Desktop/synology_audit_20260608_162415.tar.gz
```

The tarball was verified locally with:

```bash
tar -tzf ~/Desktop/synology_audit_20260608_162415.tar.gz | head
```

It contains:

```text
system.txt
dsm_version.txt
model.txt
disk_free.txt
mounts.txt
mdstat.txt
shares.txt
packages.txt
network_interfaces.txt
...
```

The audit was originally created on the NAS at:

```text
/volume2/Data/_system_audits/synology_audit_20260608_162415.tar.gz
```

We attempted `scp`, but Synology’s SCP subsystem failed. The successful workaround was:

```bash
ssh MediaServer2 'cat /volume2/Data/_system_audits/synology_audit_20260608_162415.tar.gz' > ~/Desktop/synology_audit_20260608_162415.tar.gz
```

That worked.

---

## 9. Current NAS Integration Plan

The intended NAS path for durable historical data is likely:

```text
/volume2/Data/Kalshi/historical_kmia
```

or similar, depending on the shared-folder structure from the audit.

The desired sync architecture is:

```text
MADIS VPS /data/historical_kmia
        ↓ rsync or ssh/cat fallback
Synology NAS /volume2/Data/Kalshi/historical_kmia
```

Because SCP had issues, we may use:

```text
rsync over SSH if available
or tar/cat streaming over SSH if rsync/SCP is problematic
```

The NAS should hold:

```text
processed point CSVs
valid-only CSVs
daily summaries
chart outputs
golden masters
logs
manifests
possibly raw GRIBs later if NAS capacity allows
```

The VPS should only hold:

```text
scripts
small processed working files
temporary raw GRIBs
logs
```

---

## 10. How We Achieved This State

1. We researched NDFD and confirmed AWS Open Data is the practical automated source for NDFD from 2020-04-16 onward.

2. We created a local NDFD ingestion script for KMIA using `wgrib2`.

3. We installed `wgrib2`, `pandas`, and `matplotlib` locally.

4. We ran small smoke tests on local data and confirmed NDFD forecast-data extraction works.

5. We discovered invalid regional tiles and filtered out rows returning `999 / 9.999e+20`.

6. We downloaded NCEI Global Hourly observed data for KMIA station `72202012839`.

7. We created progressively better charts comparing NDFD forecasted max temperatures vs observed KMIA max temperatures.

8. We iterated chart design until we reached a protected golden master.

9. We added observed max timestamp, mean forecast marker, median forecast marker, forecast stability classification, outcome classification, observed max timing summary, forecast wind direction, and observed wind direction.

10. We protected and backed up the golden master.

11. We began setting up the MADIS ingest server for historical archive work.

12. We installed `wgrib2` on the server via Miniforge/Mamba after adding swap.

13. We ran a successful server-side NDFD smoke test.

14. We discovered the VPS disk is too small for raw retention.

15. We cleaned up raw GRIBs and established that future ingestion must be extract-and-delete.

16. We began configuring the Synology NAS as the durable storage/archive destination.

17. We generated a Synology system audit and successfully downloaded it to the Mac.

---

## 11. Immediate Next Steps

1. Inspect the Synology audit archive:

```text
/Users/computer/Desktop/synology_audit_20260608_162415.tar.gz
```

to determine:

```text
available volumes
free space
shared-folder names
whether rsync is available
Docker/package status
best destination path
```

2. Create a durable NAS folder, likely:

```text
/volume2/Data/Kalshi/historical_kmia
```

3. Set up VPS-to-NAS key-based SSH or a safe authenticated sync method.

4. Patch the NDFD ingest workflow so each day does:

```text
ingest
extract
validate
sync to NAS
delete raw
continue
```

5. Only after NAS sync is working, scale the historical ingest beyond short smoke tests.

---

## 12. Current Safety Rules

```text
Do not retain raw NDFD GRIBs on the VPS.
Do not write historical archive data into live LDM/MADIS directories.
Do not edit the protected golden master directly.
Do not start large historical ingest until NAS sync is working.
Keep real trading disabled / NO-GO.
```
