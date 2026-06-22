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

## 7. Policy Research Container (`kmia-paper-research`)

**Arch Linux** container — same basis as `kmia-arch-ingest`. Daily Kalshi price-history ingest, backtest, and `trading_policy_draft.json` export. **No order execution.**

Scripts live in the same setup repo tree as ingest:

```text
/volume2/Data/App_Development/KMIA_Ingest/setup_repo/ingest/scripts/
/volume2/Data/App_Development/Docker/kmia-paper-research/
/volume2/Data/App_Development/Kalshi/
```

### Deploy from Mac

Synology disables the scp subsystem; use tar-over-SSH:

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
chmod +x synology/scripts/deploy_paper_research_to_nas.sh
./synology/scripts/deploy_paper_research_to_nas.sh --kalshi-src
```

Then copy into canonical locations (if deploy script could not write `/volume2`):

```bash
ssh MediaServer2
cp -R "App Development/Synology_KMIA_Ingest_Setup/ingest" \
  /volume2/Data/App_Development/KMIA_Ingest/setup_repo/
cp -R "App Development/Synology_KMIA_Ingest_Setup/docker/kmia-paper-research/"* \
  /volume2/Data/App_Development/Docker/kmia-paper-research/
```

### Secrets (red zone — not in git)

```text
/volume2/Data/App_Development/secrets/kmia_paper_research.env
```

Template: `docker/kmia-paper-research/kmia_paper_research.env.example`

### Build and start

Same flow as §3 ingest container:

```bash
cd /volume2/Data/App_Development/Docker/kmia-paper-research
sudo docker compose build
sudo docker compose up -d
sudo docker exec kmia-paper-research /usr/local/bin/smoke_container.sh
```

Manual pipeline run (expect ~5–10 min on DS225+):

```bash
sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh
```

Container stays alive with `sleep infinity` (like ingest). Schedule via DSM Task Scheduler — see `synology/scripts/90_cron_install.sh` (**2:30 AM ET** daily, after NCEI CLIMIA publish).

Logs:

```text
/volume2/Data/App_Development/logs/paper_research/cron.log
/volume2/Data/App_Development/logs/paper_research/nas_policy_*.log
```

### Pull draft policy to Mac

```bash
rsync -av MediaServer2:/volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy_draft.json \
  "$HOME/Desktop/App Development/Kalshi/backend/data/research/"
```

Human approval still happens on Mac via `approve_trading_policy.sh` in the Kalshi repo.

### Paper trading loop (Console 3 — NAS only)

**Runtime:** `kmia-paper-research` container every 15 minutes. Mac is **deploy-only** — do not run `run_paper_trading_loop.sh` or Mac launchd schedules.

Deploy Kalshi runtime (backend + scripts):

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
NAS_HOST=MediaServer2Local ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
# Optional: sync Mac ledger/snapshots
NAS_HOST=MediaServer2Local ./synology/scripts/deploy_kalshi_runtime_to_nas.sh --with-data
```

After Dockerfile changes (new wrapper scripts), rebuild container (§ Build and start).

Manual smoke:

```bash
sudo docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh
```

DSM cron (install from Mac):

```bash
NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh
```

| Schedule | Job |
|----------|-----|
| `*/15 * * * *` | Paper loop (`run_nas_paper_loop.sh`) |
| `30 2 * * *` | Policy research (`run_nas_policy_pipeline.sh`) — after NCEI CLIMIA ~2 AM |

Logs:

```text
/volume2/Data/App_Development/logs/paper_trading/cron.log
/volume2/Data/App_Development/logs/paper_trading/paper_loop_*.log
```

**Legion5** remains batch-only (GRIB extract, MAE charts, `accuracy_points_enriched.csv`). No paper loop or live Kalshi API calls on Legion5.

## No-Go Conditions

Stop if:

- Files are written outside `/volume2/Data/App_Development`
- Container stores important data only inside its internal filesystem
- `wgrib2`/`grib2io` cannot decode NDFD files
- NDFD run/valid timestamps are not preserved
- ISD station file is not KMIA `722020/12839`
- Backfill starts without manifest/checksum logging
- Any live trading or order-execution code appears
