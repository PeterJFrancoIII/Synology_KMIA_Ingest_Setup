# Legion5 as KMIA Processor

**Active scripts:** [`ACTIVE_MANIFEST.md`](ACTIVE_MANIFEST.md) · [`ACTIVE_MANIFEST.json`](ACTIVE_MANIFEST.json)

Legion5 pulls raw GRIB **one month at a time** from the NAS (3 TB archive), extracts KMIA
points with `wgrib2`, keeps VALID_ONLY CSVs on **D:**, and deletes raw after each month.

E: may be full; use D: for all processing.

## One-time setup (on Legion5)

```powershell
# Create processor workspace on D:
New-Item -ItemType Directory -Force D:\KMIA_Process\scripts, D:\KMIA_Process\logs\processing

# SMB mount for fast NAS pulls (enter NAS password once)
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1
```

Copy from Mac (run on Mac):

```bash
scp -r "Synology_KMIA_Ingest_Setup/ingest/scripts/"* Legion5:D:/KMIA_Process/scripts/
scp "Synology_KMIA_Ingest_Setup/legion5/"{35_process_month_from_nas.sh,nas_pull_helpers.sh,kmia_legion5_env.sh,36_process_all_from_nas.sh,42_kmia_4season_maxt_precision_analysis.sh,43_*} Legion5:D:/KMIA_Process/scripts/
```

Ensure SSH key to NAS (port 23921):

```bash
ssh -p 23921 Viper117@192.168.0.193 echo ok
```

## Default env (automatic via `kmia_legion5_env.sh`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `NAS_SMB_DRIVE` | `Z:` | Synology `Data` share mount |
| `NAS_PULL_MODE` | auto (`smb` if Z: mounted) | robocopy vs SSH tar |
| `KMIA_EXTRACT_WORKERS` | `4` | parallel wgrib2 processes |
| `NAS_SSH_HOST` | `nas-local` | SSH fallback / off-LAN |

Override SSH-only: `export NAS_PULL_MODE=ssh`

## Run full pipeline (Git Bash on Legion5)

```bash
# Env loaded automatically from kmia_legion5_env.sh
nohup bash /d/KMIA_Process/scripts/36_process_all_from_nas.sh \
  > /d/KMIA_Process/logs/processing/process_all.nohup.log 2>&1 &
tail -f /d/KMIA_Process/logs/processing/process_all.log
```

## Analysis outputs (`D:\KMIA_Process\analysis\`)

| File | Research question |
|------|-------------------|
| `lead_hour_accuracy.csv` | Q1: accuracy by hours before 4 PM ET |
| `best_lead_hour_per_day.csv` | Q1: optimal lead per target date |
| `conditions_accuracy.csv` | Q2: wind, stability, forecast-range buckets |
| `seasonal_by_month.csv` | Q3: accuracy by calendar month |
| `accuracy_report.md` | Summary narrative |

## Accuracy definition

- **Within 1°F / 2°F / 3°F**: `|forecast − observed daily max|`
- **Verified in range**: observed max inside min–max of that day's releases
- Anchor: **4 PM ET** on target date; window **0–36 hours** before anchor (golden master)

## Monitor

```bash
tail -f /d/KMIA_Process/logs/processing/process_all.log
ls /d/KMIA_Process/processed/points/station=KMIA/monthly/*/
```
