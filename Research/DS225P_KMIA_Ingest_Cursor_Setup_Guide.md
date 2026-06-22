# DS225+ KMIA Historical Forecast + Observed Data Ingestion Setup Guide

**Target NAS:** Synology DS225+ / MediaServer2  
**Canonical project root:** `/volume2/Data/App_Development`  
**Target station:** KMIA, Miami International Airport  
**Target data:** historical NDFD forecast data + historical observed/verification data  
**Preferred setup method:** Cursor-driven project files + Synology Container Manager / Docker  
**Preferred container OS:** Arch Linux  
**Operating mode:** research / dry-run / ingestion only. No Kalshi live trading or order execution.

---

## 1. Executive summary

This document prepares the Synology NAS as a storage-first ingestion appliance for KMIA historical weather data. The NAS should store all project development data under:

```text
/volume2/Data/App_Development
```

The NAS should run a Docker/Container Manager ingestion container, preferably Arch Linux, mounted to that shared folder. The container will install the weather-data toolchain and run download, checksum, manifest, GRIB inventory, and KMIA point-extraction jobs.

The ingestion architecture is:

```text
official data sources
-> raw immutable archive
-> checksum/file manifest
-> GRIB/station message inventory
-> KMIA point extracts
-> normalized Parquet/CSV
-> gap reports and retry queues
```

The NAS is not the primary modeling/trading engine. It is the durable data lake and ingestion worker.

---

## 2. Canonical source doctrine

Use these source families:

### Forecast data

| Source | Use |
|---|---|
| AWS Open Data NDFD | Primary historical NDFD forecast archive for 2020-04-16 onward |
| NCEI THREDDS NDFD | Catalog browsing, spot retrieval, OPeNDAP-style workflows, and gap checks |
| NCEI AIRS NDFD by WMO header | Long-history pre-2020 backfill, beginning 2004-06-06 |

### Observed / verification data

| Source | Use |
|---|---|
| NCEI ISD / ISD-Lite / LCD | KMIA station observation truth and station history |
| NOMADS RTMA | Near-real-time gridded analysis companion |
| NOMADS URMA | Final gridded analysis companion |
| Synoptic / MADIS / HF-ASOS, if available | Fast operational observation layer, not final settlement truth |

Critical rules:

1. Do **not** treat NDFD as observed data. NDFD is forecast data.
2. Do **not** infer release time from filenames. Use GRIB ref time (`d=`) for release and valid time (`vt=`) for the forecast element. Do not assume fixed 00/06/12/18 UTC cycles.
3. Use `wgrib2` or `grib2io` first for NDFD GRIB2 work because NDFD scan-pattern decoding can be fragile.
4. Do **not** hard-code a grid cell for KMIA. Derive the nearest point or interpolation weights from each GRIB file.
5. Keep raw files forever when storage allows.
6. Keep manifests immutable.
7. Keep processed data reproducible from raw files + manifest + code version.

---

## 3. Current NAS state from terminal

Already completed:

```text
/volume2/Data/App_Development
/volume2/Data/App_Development/Kalshi
/volume2/Data/App_Development/KMIA_Ingest
/volume2/Data/App_Development/Docker
/volume2/Data/App_Development/Backups
/volume2/Data/App_Development/Logs
/volume2/Data/App_Development/Scripts
/volume2/Data/App_Development/Archives
```

Already verified:

```text
/volume2 total: 8.8T
/volume2 used:  1.7T
/volume2 free:  7.1T
```

The project-data search found only the newly created App_Development paths. The unrelated `weather` matches under Games are not project data.

---

## 4. Final NAS directory layout

Cursor should create and maintain this layout:

```text
/volume2/Data/App_Development/
  Kalshi/
    repo/
    docs/
    exports/

  KMIA_Ingest/
    raw/
      forecast/
        ndfd_aws/
          maxt/
          temp/
          td/
          sky/
          wdir/
          wspd/
          pop12/
          qpf/
        ndfd_thredds/
        ndfd_airs/
      observed/
        isd/
        isd_lite/
        lcd/
        rtma/
        urma/
        synoptic/
        madis/

    processed/
      messages/
      points/
      daily/
      joins/
      parquet/
      csv/

    manifest/
      files.parquet
      messages.parquet
      retries.parquet
      gaps.parquet
      run_log.jsonl

    config/
      docker-compose.yml
      kmia_ingest.env.example
      pointgrid.txt
      variables.txt

    scripts/
      00_create_tree.sh
      01_host_audit.sh
      02_container_smoke.sh
      10_ndfd_aws_smoke_maxt.sh
      11_isd_smoke_kmia.sh
      20_extract_kmia_point.sh
      30_gap_audit.sh
      90_cron_install.sh

    logs/
      host/
      container/
      ingestion/
      smoke_tests/

  Docker/
    kmia-arch-ingest/
      docker-compose.yml
      Dockerfile
      README.md

  Backups/
    kmia_ingest_config/
    manifests/
    scripts/

  Logs/
  Scripts/
  Archives/
```

---

## 5. Cursor project structure

Open Cursor on a local project folder first, for example:

```text
~/Desktop/App Development/Synology_KMIA_Ingest_Setup
```

Cursor should generate this local repository:

```text
Synology_KMIA_Ingest_Setup/
  README.md
  docs/
    DS225P_KMIA_Ingest_Cursor_Setup_Guide.md
    NAS_Runbook.md
    Data_Source_Map.md
    Smoke_Test_Checklist.md
  synology/
    scripts/
      00_create_tree.sh
      01_host_audit.sh
      02_find_project_data.sh
      03_permissions_check.sh
      90_cron_install.sh
  docker/
    kmia-arch-ingest/
      Dockerfile
      docker-compose.yml
      entrypoint.sh
      install_toolchain.sh
      smoke_container.sh
  ingest/
    config/
      variables.txt
      kmia_station.json
      pointgrid.txt
      kmia_ingest.env.example
    scripts/
      10_ndfd_aws_smoke_maxt.sh
      11_isd_smoke_kmia.sh
      20_extract_kmia_point.sh
      30_gap_audit.sh
      40_manifest_append.py
      50_list_ndfd_s3.py
      60_download_isd_year.py
  tests/
    test_paths.sh
    test_no_internal_storage.sh
    test_container_mount.sh
```

Then copy/sync these files to the NAS with `rsync`.

---

## 6. Cursor master prompt

Paste this into Cursor:

```text
TASK:
Create a Synology DS225+ setup repo for KMIA historical forecast and observed weather ingestion.

CONTEXT:
All project development data must live under /volume2/Data/App_Development on the NAS. The NAS is MediaServer2. We will use Synology Container Manager / Docker. Preferred container OS is Arch Linux. Target station is KMIA. This is research/data ingestion only, no live trading.

DATA SOURCES:
Forecasts: AWS NDFD from 2020-04-16 onward, NCEI THREDDS for catalog/spot checks, NCEI AIRS for 2004-06-06 onward long-history recovery.
Observations/verification: NCEI ISD, ISD-Lite, LCD, NOMADS RTMA, NOMADS URMA, and optional Synoptic/MADIS/HF-ASOS.

RULES:
- Do not store project files outside /volume2/Data/App_Development.
- Use GRIB ref time (`d=`) for release time — not filename post times; do not bucket to fixed 00/06/12/18 UTC cycles.
- Preserve source path, file timestamp, run time, valid time, checksum, and station coordinates.
- Use wgrib2 or grib2io first for NDFD GRIB2.
- Do not hard-code a KMIA grid cell.
- Start with nearest-grid extraction for reproducibility.
- Use raw immutable storage + manifest + processed point extracts.
- Keep scripts POSIX-compatible where possible.
- No secrets in repo.
- No Kalshi live-trading or order execution code.

CREATE:
1. README.md
2. docs/NAS_Runbook.md
3. docs/Data_Source_Map.md
4. docs/Smoke_Test_Checklist.md
5. synology/scripts/00_create_tree.sh
6. synology/scripts/01_host_audit.sh
7. synology/scripts/02_find_project_data.sh
8. synology/scripts/03_permissions_check.sh
9. docker/kmia-arch-ingest/docker-compose.yml
10. docker/kmia-arch-ingest/Dockerfile
11. docker/kmia-arch-ingest/install_toolchain.sh
12. docker/kmia-arch-ingest/smoke_container.sh
13. ingest/config/variables.txt
14. ingest/config/kmia_station.json
15. ingest/config/pointgrid.txt
16. ingest/scripts/10_ndfd_aws_smoke_maxt.sh
17. ingest/scripts/11_isd_smoke_kmia.sh
18. ingest/scripts/20_extract_kmia_point.sh
19. ingest/scripts/40_manifest_append.py
20. tests/test_paths.sh
21. tests/test_container_mount.sh

ACCEPTANCE:
- Shell scripts pass sh -n or bash -n.
- Every absolute NAS path begins with /volume2/Data/App_Development.
- docker-compose mounts /volume2/Data/App_Development:/data.
- Smoke test downloads one day of NDFD maxt from AWS S3 and tries wgrib2 point extraction for KMIA.
- ISD smoke test downloads KMIA-like station file 72202012839.csv for one year.
- Manifest writer records source, source_path, retrieved_at_utc, sha256, bytes, format, station_id, station_lat, station_lon, decoder, status, error_text.
- No real trading, no order execution, no API keys.

OUTPUT:
Report files created, exact commands to run on the NAS, and any assumptions.
```

---

## 7. NAS bootstrap scripts Cursor should create

### `synology/scripts/00_create_tree.sh`

```sh
#!/bin/sh
set -eu

ROOT="/volume2/Data/App_Development"

mkdir -p "$ROOT"/{Kalshi,KMIA_Ingest,Docker,Backups,Logs,Scripts,Archives} 2>/dev/null || true

mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws"/{maxt,temp,td,sky,wdir,wspd,pop12,qpf}
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast"/{ndfd_thredds,ndfd_airs}
mkdir -p "$ROOT/KMIA_Ingest/raw/observed"/{isd,isd_lite,lcd,rtma,urma,synoptic,madis}
mkdir -p "$ROOT/KMIA_Ingest/processed"/{messages,points,daily,joins,parquet,csv}
mkdir -p "$ROOT/KMIA_Ingest/manifest"
mkdir -p "$ROOT/KMIA_Ingest/config"
mkdir -p "$ROOT/KMIA_Ingest/scripts"
mkdir -p "$ROOT/KMIA_Ingest/logs"/{host,container,ingestion,smoke_tests}
mkdir -p "$ROOT/Docker/kmia-arch-ingest"
mkdir -p "$ROOT/Backups"/{kmia_ingest_config,manifests,scripts}

find "$ROOT" -maxdepth 4 -type d | sort
```

If brace expansion fails under Synology `/bin/sh`, Cursor should rewrite it using plain repeated `mkdir -p` commands.

### `synology/scripts/01_host_audit.sh`

```sh
#!/bin/sh
set -eu

ROOT="/volume2/Data/App_Development"

echo "=== HOST ==="
hostname
date
uname -a

echo

echo "=== VOLUMES ==="
df -h

echo

echo "=== PROJECT ROOT ==="
du -sh "$ROOT" 2>/dev/null || true
find "$ROOT" -maxdepth 3 -type d 2>/dev/null | sort

echo

echo "=== DOCKER ==="
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true
else
  echo "docker not found in PATH"
fi
```

### `synology/scripts/02_find_project_data.sh`

```sh
#!/bin/sh
set -eu

find /volume2/Data \
  -path /volume2/Data/Games -prune -o \
  -path /volume2/Data/docker -prune -o \
  \( \
    -iname "*kalshi*" -o \
    -iname "*kmia*" -o \
    -iname "*madis*" -o \
    -iname "*ndfd*" -o \
    -iname "*synoptic*" -o \
    -iname "*weather*" \
  \) -print
```

---

## 8. Docker / Container Manager setup

### Compose file

Create this as:

```text
/volume2/Data/App_Development/Docker/kmia-arch-ingest/docker-compose.yml
```

```yaml
services:
  kmia-arch-ingest:
    build: .
    image: kmia-arch-ingest:latest
    container_name: kmia-arch-ingest
    restart: unless-stopped
    command: ["sleep", "infinity"]
    environment:
      TZ: America/New_York
      KMIA_ROOT: /data/KMIA_Ingest
      KMIA_LAT: "25.7906"
      KMIA_LON: "-80.3164"
      PYTHONUNBUFFERED: "1"
    volumes:
      - /volume2/Data/App_Development:/data
    working_dir: /data/KMIA_Ingest
    mem_limit: 3g
    cpus: 2
```

### Dockerfile

```Dockerfile
FROM archlinux:latest

ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
      base-devel git curl wget rsync ca-certificates tzdata \
      python python-pip python-virtualenv \
      aws-cli jq unzip gzip bzip2 xz zstd \
      cdo nco eccodes && \
    pacman -Scc --noconfirm

RUN python -m venv /opt/kmia-venv
RUN /opt/kmia-venv/bin/pip install --upgrade pip wheel && \
    /opt/kmia-venv/bin/pip install \
      boto3 botocore pandas pyarrow duckdb xarray cfgrib eccodes \
      requests beautifulsoup4 lxml tqdm

ENV PATH="/opt/kmia-venv/bin:${PATH}"

WORKDIR /data/KMIA_Ingest
```

### Important wgrib2 note

Arch’s default repositories may not include `wgrib2`. Cursor should implement a check:

```sh
if ! command -v wgrib2 >/dev/null 2>&1; then
  echo "wgrib2 missing. Install via AUR/manual build or use grib2io fallback."
fi
```

Do not start full ingestion until `wgrib2 -version` or an approved `grib2io` fallback works.

---

## 9. Configuration files

### `ingest/config/variables.txt`

```text
maxt
TD
td
sky
wdir
wspd
pop12
qpf
```

Recommended normalized variable set:

```text
maxt
temp
td
sky
wdir
wspd
pop12
qpf
```

### `ingest/config/kmia_station.json`

```json
{
  "station_id": "KMIA",
  "name": "Miami International Airport",
  "lat": 25.7906,
  "lon": -80.3164,
  "lon_360": 279.6836,
  "timezone": "America/New_York",
  "isd_usaf": "722020",
  "isd_wban": "12839",
  "isd_global_hourly_file_example": "72202012839.csv",
  "isd_lite_file_example": "722020-12839-2025.gz"
}
```

### `ingest/config/pointgrid.txt`

```text
gridtype = lonlat
xsize    = 1
ysize    = 1
xfirst   = -80.3164
xinc     = 0
yfirst   = 25.7906
yinc     = 0
```

---

## 10. Smoke tests

### NDFD AWS smoke test

Create:

```text
/volume2/Data/App_Development/KMIA_Ingest/scripts/10_ndfd_aws_smoke_maxt.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/KMIA_Ingest"
SUBCATEGORY="maxt"
YEAR="2020"
MONTH="06"
DAY="01"
KMIA_LON="-80.3164"
KMIA_LAT="25.7906"

OUT="$ROOT/raw/forecast/ndfd_aws/$SUBCATEGORY/$YEAR/$MONTH/$DAY"
LOG="$ROOT/logs/smoke_tests/ndfd_aws_maxt_${YEAR}${MONTH}${DAY}.log"
mkdir -p "$OUT" "$(dirname "$LOG")"

aws s3 ls --no-sign-request "s3://noaa-ndfd-pds/wmo/$SUBCATEGORY/$YEAR/$MONTH/$DAY/" | tee "$LOG"
aws s3 cp --no-sign-request --recursive \
  "s3://noaa-ndfd-pds/wmo/$SUBCATEGORY/$YEAR/$MONTH/$DAY/" \
  "$OUT/" | tee -a "$LOG"

first_file="$(find "$OUT" -type f | head -1)"
if [ -z "$first_file" ]; then
  echo "No NDFD files downloaded" | tee -a "$LOG"
  exit 1
fi

sha256sum "$first_file" | tee -a "$LOG"

if command -v wgrib2 >/dev/null 2>&1; then
  wgrib2 "$first_file" -s -vt -lon "$KMIA_LON" "$KMIA_LAT" | tee -a "$LOG"
else
  echo "wgrib2 missing; download succeeded but point extraction skipped" | tee -a "$LOG"
  exit 2
fi
```

Run inside the container:

```bash
bash /data/KMIA_Ingest/scripts/10_ndfd_aws_smoke_maxt.sh
```

### ISD smoke test

Create:

```text
/volume2/Data/App_Development/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/KMIA_Ingest"
YEAR="2025"
FILE="72202012839.csv"
URL="https://www.ncei.noaa.gov/data/global-hourly/access/$YEAR/$FILE"
OUT="$ROOT/raw/observed/isd/$YEAR/$FILE"
LOG="$ROOT/logs/smoke_tests/isd_kmia_${YEAR}.log"

mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"

curl -fL "$URL" -o "$OUT"
sha256sum "$OUT" | tee "$LOG"
head -5 "$OUT" | tee -a "$LOG"
```

Run inside the container:

```bash
bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh
```

---

## 11. Manifest writer

Create:

```text
/volume2/Data/App_Development/KMIA_Ingest/scripts/40_manifest_append.py
```

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--source-path", required=True)
    p.add_argument("--format", required=True)
    p.add_argument("--decoder", default="unknown")
    p.add_argument("--status", default="ok")
    p.add_argument("--error-text", default="")
    p.add_argument("--manifest", default="/data/KMIA_Ingest/manifest/run_log.jsonl")
    args = p.parse_args()

    path = Path(args.file)
    record = {
        "source": args.source,
        "source_path": args.source_path,
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "local_path": str(path),
        "sha256": sha256_file(path) if path.exists() else None,
        "content_length": path.stat().st_size if path.exists() else None,
        "format": args.format,
        "station_id": "KMIA",
        "station_lat": 25.7906,
        "station_lon": -80.3164,
        "decoder": args.decoder,
        "status": args.status,
        "error_text": args.error_text or None,
    }

    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 12. Copy files from Cursor repo to NAS

From your Mac, after Cursor creates the setup repo:

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
rsync -av --progress \
  synology/ docker/ ingest/ docs/ README.md \
  MediaServer2:/volume2/Data/App_Development/KMIA_Ingest/setup_repo/
```

Then SSH in:

```bash
ssh MediaServer2
cd /volume2/Data/App_Development/KMIA_Ingest/setup_repo
```

Copy scripts into canonical NAS locations:

```bash
cp -R synology/scripts/* /volume2/Data/App_Development/Scripts/
cp -R ingest/scripts/* /volume2/Data/App_Development/KMIA_Ingest/scripts/
cp -R ingest/config/* /volume2/Data/App_Development/KMIA_Ingest/config/
cp -R docker/kmia-arch-ingest/* /volume2/Data/App_Development/Docker/kmia-arch-ingest/
chmod +x /volume2/Data/App_Development/Scripts/*.sh
chmod +x /volume2/Data/App_Development/KMIA_Ingest/scripts/*.sh
```

---

## 13. Build and start container

On NAS:

```bash
cd /volume2/Data/App_Development/Docker/kmia-arch-ingest
sudo docker compose build
sudo docker compose up -d
sudo docker ps
```

Enter container:

```bash
sudo docker exec -it kmia-arch-ingest bash
```

Inside container:

```bash
pwd
ls -la /data
ls -la /data/KMIA_Ingest
python --version
aws --version
cdo -V | head
ncks --version || true
wgrib2 -version || true
```

---

## 14. First acceptance run

Inside the container:

```bash
bash /data/KMIA_Ingest/scripts/10_ndfd_aws_smoke_maxt.sh
bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh
```

Expected outputs:

```text
/data/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2020/06/01/<files>
/data/KMIA_Ingest/raw/observed/isd/2025/72202012839.csv
/data/KMIA_Ingest/logs/smoke_tests/*.log
```

If `wgrib2` is missing, the NDFD smoke test should still prove S3 download and checksum but should exit with a clear `wgrib2 missing` message.

---

## 15. Cron / scheduling plan

Do not schedule full historical backfill until smoke tests pass.

After smoke tests pass, install small incremental jobs only:

```text
# Recent NDFD forecast ingest
*/30 * * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/recent_ndfd.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/recent_ndfd.log 2>&1

# Daily station observation ingest
30 2 * * * docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/isd_daily.log 2>&1

# Weekly gap audit
0 4 * * 0 docker exec kmia-arch-ingest bash /data/KMIA_Ingest/scripts/30_gap_audit.sh >> /volume2/Data/App_Development/KMIA_Ingest/logs/ingestion/gap_audit.log 2>&1
```

For historical backfill, use manual batches:

```text
one source
one variable
one month
one worker
verify manifest
then continue
```

---

## 16. Cursor implementation phases

### Phase 1: NAS prep repo

Create docs, scripts, Dockerfile, compose file, and smoke tests.

Acceptance:

```bash
find . -type f
sh -n synology/scripts/*.sh
bash -n ingest/scripts/*.sh
bash tests/test_paths.sh
```

### Phase 2: NAS copy and container build

Copy repo to NAS. Build Arch container. Verify `/data` mount.

Acceptance:

```bash
docker ps
docker exec kmia-arch-ingest ls -la /data/KMIA_Ingest
```

### Phase 3: Data-source smoke tests

Download one NDFD date and one ISD file.

Acceptance:

```bash
find /volume2/Data/App_Development/KMIA_Ingest/raw -type f | head
find /volume2/Data/App_Development/KMIA_Ingest/logs/smoke_tests -type f
```

### Phase 4: wgrib2 / point extraction

Install/verify `wgrib2` or approved `grib2io` fallback. Extract KMIA point from one NDFD file.

Acceptance:

```bash
wgrib2 -version
wgrib2 <file> -s -vt -lon -80.3164 25.7906
```

### Phase 5: Manifest and gap ledger

Append manifest records for smoke test files.

Acceptance:

```bash
tail -5 /volume2/Data/App_Development/KMIA_Ingest/manifest/run_log.jsonl
```

### Phase 6: Controlled backfill

Backfill by source, variable, and month. Keep concurrency low.

Acceptance:

```bash
raw files present
manifest records present
logs contain no repeated failures
no data outside /volume2/Data/App_Development
```

---

## 17. No-go conditions

Stop if any of these happen:

```text
Files are being written outside /volume2/Data/App_Development
Container writes important data only inside its internal filesystem
wgrib2/grib2io cannot decode NDFD files
NDFD files download but run/valid timestamps are not preserved
ISD station file is not KMIA 722020/12839
Scripts assume fixed NDFD cycles only
Backfill is launched without manifest/checksum logging
The NAS begins swapping heavily or becomes unstable
Any trading/order-execution code appears
```

---

## 18. Operator commands cheat sheet

SSH:

```bash
ssh MediaServer2
```

Audit:

```bash
/volume2/Data/App_Development/Scripts/01_host_audit.sh
/volume2/Data/App_Development/Scripts/02_find_project_data.sh
```

Container:

```bash
cd /volume2/Data/App_Development/Docker/kmia-arch-ingest
sudo docker compose up -d
sudo docker exec -it kmia-arch-ingest bash
```

Smoke tests:

```bash
sudo docker exec -it kmia-arch-ingest bash /data/KMIA_Ingest/scripts/10_ndfd_aws_smoke_maxt.sh
sudo docker exec -it kmia-arch-ingest bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh
```

Storage check:

```bash
df -h /volume2
sudo du -h -d 3 /volume2/Data/App_Development | sort -hr | head -50
```

Find accidental project data outside root:

```bash
find /volume2/Data \
  -path /volume2/Data/Games -prune -o \
  -path /volume2/Data/docker -prune -o \
  \( -iname "*kalshi*" -o -iname "*kmia*" -o -iname "*madis*" -o -iname "*ndfd*" -o -iname "*synoptic*" \) -print
```

---

## 19. Final desired end state

When this setup is complete, the DS225+ will have:

```text
1. A single canonical project root at /volume2/Data/App_Development.
2. A Docker/Arch ingestion container mounted to /data.
3. Official forecast and observed data stored separately.
4. Raw files preserved with checksums.
5. KMIA point extracts generated reproducibly.
6. Manifest and gap ledgers available for backtesting.
7. Smoke-tested download paths for NDFD and ISD.
8. No project data scattered elsewhere on the NAS.
9. No live trading code or credentials.
```

