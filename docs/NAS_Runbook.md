# NAS Runbook — DS225+ KMIA Ingest

**Target NAS:** Synology DS225+ / MediaServer2  
**Canonical root:** `/volume2/Data/App_Development`  
**Container:** `kmia-arch-ingest` (Arch Linux)

## 1. Host Audit

```bash
ssh MediaServer2
/volume2/Data/App_Development/Scripts/00_create_tree.sh
/volume2/Data/App_Development/Scripts/01_host_audit.sh
/volume2/Data/App_Development/Scripts/02_find_project_data.sh
/volume2/Data/App_Development/Scripts/03_permissions_check.sh
```

## 2. Copy Setup Repo From Mac

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
rsync -av --progress \
  synology/ docker/ ingest/ docs/ README.md \
  MediaServer2:/volume2/Data/App_Development/KMIA_Ingest/setup_repo/
```

Install into canonical locations:

```bash
ssh MediaServer2
cd /volume2/Data/App_Development/KMIA_Ingest/setup_repo
cp -R synology/scripts/* /volume2/Data/App_Development/Scripts/
cp -R ingest/scripts/* /volume2/Data/App_Development/KMIA_Ingest/scripts/
cp -R ingest/config/* /volume2/Data/App_Development/KMIA_Ingest/config/
cp -R docker/kmia-arch-ingest/* /volume2/Data/App_Development/Docker/kmia-arch-ingest/
chmod +x /volume2/Data/App_Development/Scripts/*.sh
chmod +x /volume2/Data/App_Development/KMIA_Ingest/scripts/*.sh
```

## 3. Build And Start Container

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

Inside container verify mount and tools:

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

## 4. Smoke Tests

```bash
sudo docker exec -it kmia-arch-ingest bash /data/KMIA_Ingest/setup_repo/docker/kmia-arch-ingest/smoke_container.sh
sudo docker exec -it kmia-arch-ingest bash /data/KMIA_Ingest/scripts/10_ndfd_aws_smoke_maxt.sh
sudo docker exec -it kmia-arch-ingest bash /data/KMIA_Ingest/scripts/11_isd_smoke_kmia.sh
```

Expected outputs:

```text
/data/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2020/06/01/<files>
/data/KMIA_Ingest/raw/observed/isd/2025/72202012839.csv
/data/KMIA_Ingest/logs/smoke_tests/*.log
/data/KMIA_Ingest/manifest/run_log.jsonl
```

## 5. Storage Check

```bash
df -h /volume2
sudo du -h -d 3 /volume2/Data/App_Development | sort -hr | head -50
```

## 6. Cron (After Smoke Tests Pass)

Do not schedule full historical backfill until smoke tests pass. See `synology/scripts/90_cron_install.sh` for incremental job templates.

## No-Go Conditions

Stop if:

- Files are written outside `/volume2/Data/App_Development`
- Container stores important data only inside its internal filesystem
- `wgrib2`/`grib2io` cannot decode NDFD files
- NDFD run/valid timestamps are not preserved
- ISD station file is not KMIA `722020/12839`
- Backfill starts without manifest/checksum logging
- Any live trading or order-execution code appears
