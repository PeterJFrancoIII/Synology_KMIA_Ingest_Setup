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

## 7. Policy Research & Paper Loop (`kmia-paper-research`)

**Arch Linux** container. **NAS is the only production runtime** for paper loop, WS archive companion, and daily ingest. Legion5 owns backtest/sweep; Mac is deploy + human approval only.

Scripts:

```text
/volume2/Data/App_Development/KMIA_Ingest/setup_repo/ingest/scripts/
/volume2/Data/App_Development/Docker/kmia-paper-research/
/volume2/Data/App_Development/Kalshi/
```

### Canonical deploy (single checklist — run from Mac on LAN)

Use this ordered flow after Console 2 or Kalshi `backend/src` changes. **Do not piecemeal hot-patch** unless debugging one file.

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
export NAS_HOST=MediaServer2   # not MediaServer2Local (often times out off-LAN)

# 1) Console 2 ingest scripts + docker launchers → setup_repo
tar cf - ingest/scripts docker/kmia-paper-research docs/ops synology/scripts | \
  ssh "$NAS_HOST" "sudo tar xf - -C /volume2/Data/App_Development/KMIA_Ingest/setup_repo"

# 2) Docker compose tree → canonical Docker path (capital D)
tar cf - -C docker kmia-paper-research | \
  ssh "$NAS_HOST" "sudo tar xf - -C /volume2/Data/App_Development/Docker"

# 3) Kalshi runtime (backend/src + scripts) — canonical deploy
./synology/scripts/deploy_kalshi_runtime_to_nas.sh

# 4) Paper window + maker_limit secrets + hot modules (tee, not scp)
./synology/scripts/deploy_paper_trading_window_fix.sh

# 5) Rebuild container so launchers survive recreate
ssh "$NAS_HOST" 'sudo sh -c "cd /volume2/Data/App_Development/Docker/kmia-paper-research && \
  /var/packages/ContainerManager/target/usr/bin/docker compose build kmia-paper-research && \
  /var/packages/ContainerManager/target/usr/bin/docker compose up -d kmia-paper-research"'

# 6) Cron (first time or after template change)
./synology/scripts/90_cron_install.sh --activate-all

# 7) Verify
NAS_HOST="$NAS_HOST" ./ingest/scripts/kmia_paper_ops_watch.sh
```

**After Legion5 policy export** — push research JSON only (do not `--with-data` Mac ledger):

```bash
# Preferred: Legion5 robocopy (needs nas_smb_write_password)
# powershell -File D:\KMIA_Process\scripts\55_sync_research_to_nas.ps1

# Fallback from Mac after approve_trading_policy.sh:
cat "$HOME/Desktop/App Development/Kalshi/backend/data/research/trading_policy.json" | \
  ssh MediaServer2 "sudo tee /volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy.json > /dev/null"
```

**Policy pipeline roles:**

| Host | `run_daily_policy_refresh.sh` | Notes |
|------|------------------------------|--------|
| Legion5 | Full backtest + sweep | Weekly `55_quant_core_baseline.sh`, `55_trading_window_ab.sh` |
| NAS | `SKIP_POLICY_SWEEP=1` (ingest-only) | Price ingest, NCEI, coverage — no taker/maker conflict |

### Deploy from Mac (legacy / partial)

Synology disables the scp subsystem; use tar-over-SSH or `deploy_*` scripts (not raw scp to NAS):

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

Manual pipeline run (ingest-only — expect ~2–5 min):

```bash
sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh
# Log should show SKIP_POLICY_SWEEP=1 — not full [4/8] backtest on NAS
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

Human approval on Mac; push **policy JSON only** to NAS (see § Canonical deploy). Do not sync Mac paper ledger to NAS unless intentionally resetting state.

### Paper trading loop (Console 3 — NAS only)

**Runtime:** `kmia-paper-research` every 5 minutes. **Approved policy (2026-06-24):** `maker_limit`, 18% edge, dynamic window.

Use § Canonical deploy above — not the legacy commands below.

Legacy reference:

```bash
NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
```

Manual smoke:

```bash
sudo docker exec kmia-paper-research /usr/local/bin/run_nas_paper_loop.sh
```

DSM cron (install from Mac):

```bash
NAS_HOST=MediaServer2 ./synology/scripts/90_cron_install.sh --activate-all
```

| Schedule | Job |
|----------|-----|
| `*/5 * * * *` | Paper loop (`run_nas_paper_loop.sh`) |
| `30 2 * * *` | Policy ingest (`run_nas_policy_pipeline.sh`) — ingest-only |
| `0 7 * * 0` | Forward scorecard (`run_nas_paper_scorecard.sh`) |

Logs:

```text
/volume2/Data/App_Development/logs/paper_trading/cron.log
/volume2/Data/App_Development/logs/paper_trading/paper_loop_*.log
```

**Legion5** remains batch-only (GRIB extract, MAE charts, `accuracy_points_enriched.csv`). No paper loop or live Kalshi API calls on Legion5.

### WebSocket orderbook archiver (finest book granularity)

**Runtime:** `kmia-orderbook-ws` container — long-running daemon (not cron). Archives `orderbook_snapshot` + `orderbook_delta` to `kalshi_market_archive/orderbook_ws/` and 60s checkpoints to `orderbook_ws_snapshots/`.

Prerequisites: Kalshi API secrets (`setup_nas_kalshi_secrets.sh`).

```bash
cd /volume2/Data/App_Development/Docker/kmia-paper-research
sudo docker compose build
sudo docker compose up -d kmia-orderbook-ws
sudo docker logs -f kmia-orderbook-ws
```

Health:

```bash
cat /volume2/Data/App_Development/Kalshi/backend/data/processed/kalshi_market_archive/ws_daemon_status.json
ls -la /volume2/Data/App_Development/Kalshi/backend/data/processed/kalshi_market_archive/orderbook_ws/
```

Logs: `/volume2/Data/App_Development/logs/orderbook_ws/`

Disable: `KALSHI_WS_ENABLED=false` in secrets or `sudo docker compose stop kmia-orderbook-ws`.

## No-Go Conditions

Stop if:

- Files are written outside `/volume2/Data/App_Development`
- Container stores important data only inside its internal filesystem
- `wgrib2`/`grib2io` cannot decode NDFD files
- NDFD run/valid timestamps are not preserved
- ISD station file is not KMIA `722020/12839`
- Backfill starts without manifest/checksum logging
- Any live trading or order-execution code appears
