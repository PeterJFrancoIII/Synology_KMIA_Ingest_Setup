# Agent Operating Rules

## Console identity (mandatory)

**This repo = Console 2 — Weather Ingestion & MAE Probabilities.**

| Console | Workspace | Scope |
|---------|-----------|--------|
| 1 — Kalshi Main | `../Kalshi` | Human Streamlit overview, live weather/markets |
| 2 — Weather Ingest & MAE | **this repo** | NAS ingest, Legion5 batch, MAE charts |
| 3 — Auto Trader | *future module* | Strategies, paper/active trading |

Read `docs/architecture/THREE_CONSOLE_ARCHITECTURE.md` before cross-cutting work.  
**Never** add Streamlit UI, Kalshi order execution, or paper-ledger code here.

## Prime directive

Build the user's current objective with maximum verified progress and minimum drift.

**Before any session:** Read [AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md](AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md) (Sections 0–8 minimum), [MISSION.md](MISSION.md), and [trade_policies.md](trade_policies.md) when touching Kalshi policy, backtest, or paper-loop exports.

## Trading policy document (mandatory for policy work)

- **Canonical strategy reasoning:** [trade_policies.md](trade_policies.md)
- **Regenerate after any policy change:** `PYTHONPATH=ingest/scripts python3 ingest/scripts/update_trade_policies_doc.py`
- Auto-sync also runs from `export_trading_policy.py`, `kalshi_policy_optimizer.py`, and `write_policy_human_review.py`.
- Agents **must** update this file when altering selection objective, sweep results, or exported draft parameters.

## Required loop

1. Read [MISSION.md](MISSION.md), [current-objective.md](current-objective.md), and [ROUTING.md](ROUTING.md).
2. Read scoped `.cursor/rules/*.mdc` for the area you are editing.
3. State allowed and forbidden files.
4. Plan before editing.
5. Implement one small slice.
6. Run verification (SSH to Legion5, log tail, or local script check as appropriate).
7. Update handoff/memory in docs if work spans sessions.

## Commands

### Deploy

- **Canonical NAS deploy:** `docs/NAS_Runbook.md` § Canonical deploy (ordered checklist)
- **SSH host:** `NAS_HOST=MediaServer2` (not `MediaServer2Local` — often times out)
- **Kalshi runtime:** `NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh`
- **Paper window + maker fix:** `NAS_HOST=MediaServer2 ./synology/scripts/deploy_paper_trading_window_fix.sh`
- **NAS DSM cron:** `NAS_HOST=MediaServer2 ./synology/scripts/90_cron_install.sh --activate-all`
- **Ops watch:** `NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh`

### Legion5 — after any `legion5/*.sh` or `ingest/scripts/*.py` change

Sync scripts to Legion5 before running pipelines there:

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
scp legion5/{52,54,55}*.sh legion5/kmia_kalshi_legion5_env.sh legion5/43b_setup_nas_smb_write.ps1 \
  Legion5:D:/KMIA_Process/scripts/
scp ingest/scripts/{export_trading_policy,trading_policy_manifest,kalshi_policy_optimizer,kalshi_price_history_loader,kmia_kalshi_paths}.py \
  Legion5:D:/KMIA_Process/scripts/
```

Policy export after trading-window A/B:

```bash
# Git Bash on Legion5
bash D:/KMIA_Process/scripts/55_export_maker_policy.sh
powershell -ExecutionPolicy Bypass -File D:/KMIA_Process/scripts/55_sync_research_to_nas.ps1
```

One-time writable SMB: `powershell -File D:\KMIA_Process\scripts\43b_setup_nas_smb_write.ps1`  
(password: `D:\KMIA_Process\secrets\nas_smb_write_password` — never commit)

### Legion5 research

- **Deploy to Legion5:** `scp legion5/* Legion5:D:/KMIA_Process/scripts/`
- **Resume BUILD:** `ssh Legion5 D:\KMIA_Process\scripts\48b_start_resume_build.bat`
- **Build charts on Legion5:** `ssh Legion5 D:\KMIA_Process\scripts\49_build_all_charts.sh` (via Git bash)
- **Pull charts to Mac:** `legion5/pull_all_charts_to_mac.sh`
- **NDFD + Kalshi research:** `bash D:/KMIA_Process/scripts/52_kalshi_ndfd_anchor_backfill.sh …` then `54_kalshi_ndfd_research_pipeline.sh`
- **Legion5 autorun:** `bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --once 202604_202606`
- **Weekly baseline:** `bash D:/KMIA_Process/scripts/55_quant_core_baseline.sh`
- **Trading window A/B:** `bash D:/KMIA_Process/scripts/55_trading_window_ab.sh`

### NAS runtime (no research sweep on NAS)

- **NAS scheduled ingest:** `sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh` (`SKIP_POLICY_SWEEP=1`)
- **NAS WebSocket orderbook:** `docker compose up -d kmia-orderbook-ws` — see `docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md`

### Other

- **Bridge artifacts:** `bash ingest/scripts/refresh_trading_bridge.sh` (Legion5 or NAS only — not Mac)
- **Archive coverage:** `python3 ingest/scripts/kalshi_archive_status.py`
- **Verify KMIA pin:** `PYTHONPATH=ingest/scripts python3 ingest/scripts/verify_kmia_station_alignment.py`
- **Kalshi API fields:** `docs/architecture/KALSHI_API_RESPONSE_FIELDS.md`
- **NAS ingest skill:** `.cursor/skills/kmia-nas-ingest/SKILL.md`

**Runtime placement:** NAS = ingest + paper loop + WS archive (production). Legion5 = NDFD extract + backtest/sweep. **Mac = deploy + human approval only — do not run policy sweeps, NDFD extract, or backtest pipelines on Mac.**

## Risk classes

| Class | Examples |
|-------|----------|
| **Green** | Docs, research markdown, isolated legion5 scripts, chart HTML |
| **Yellow** | Extract/filter pipeline, merge scripts, NAS pull helpers, dependencies |
| **Red** | Secrets, NAS write/backfill to raw GRIB, production infra, credentials |

**Weather data rule (mandatory):** Never simulate, backfill, or proxy forecast or observed weather in Kalshi weather sets. See `.cursor/rules/no-simulated-weather-data.mdc`. Use `kalshi_weather_coverage_scorecard.py` (report only).

Red changes require explicit human approval before edits and before merge.

## Communication

Use terse, evidence-first updates. Preserve exact code, paths, commands, and errors. Respond with MISSION / STATE / PLAN / SCOPE / VERIFY when doing multi-step architect work (per bootloader Section 0).
