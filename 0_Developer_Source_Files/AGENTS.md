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

1. Read [MISSION.md](MISSION.md) and [current-objective.md](current-objective.md).
2. Read scoped `.cursor/rules/*.mdc` for the area you are editing.
3. State allowed and forbidden files.
4. Plan before editing.
5. Implement one small slice.
6. Run verification (SSH to Legion5, log tail, or local script check as appropriate).
7. Update handoff/memory in docs if work spans sessions.

## Commands

- **Deploy to Legion5:** `scp legion5/* Legion5:D:/KMIA_Process/scripts/`
- **Resume BUILD:** `ssh Legion5 D:\KMIA_Process\scripts\48b_start_resume_build.bat`
- **Build charts on Legion5:** `ssh Legion5 D:\KMIA_Process\scripts\49_build_all_charts.sh` (via Git bash)
- **Pull charts to Mac:** `legion5/pull_all_charts_to_mac.sh`
- **NAS policy research:** `NAS_HOST=MediaServer2Local ./synology/scripts/deploy_paper_research_to_nas.sh --kalshi-src`
- **NAS paper loop runtime:** `NAS_HOST=MediaServer2Local ./synology/scripts/deploy_kalshi_runtime_to_nas.sh`
- **NAS DSM cron:** `NAS_HOST=MediaServer2Local ./synology/scripts/90_cron_install.sh`
- **Verify KMIA pin alignment:** `PYTHONPATH=ingest/scripts python3 ingest/scripts/verify_kmia_station_alignment.py`
- **Quarantine wrong-grid NWS snapshots:** `PYTHONPATH=ingest/scripts python3 ingest/scripts/quarantine_mismatched_nws_snapshots.py`
- **Legion5 NDFD + Kalshi research (MapClick pin):** `scp legion5/{52,54}*.sh legion5/kmia_kalshi_legion5_env.sh ingest/scripts/{ndfd_kalshi_forecast,backfill_nws_snapshots_from_ndfd,historical_checksum_backtest,kalshi_policy_optimizer,export_trading_policy,export_safest_policy_from_sweep,...}.py Legion5:D:/KMIA_Process/scripts/` then Git Bash: `bash D:/KMIA_Process/scripts/52_kalshi_ndfd_anchor_backfill.sh 2026 04 2026 06` (extract + merge + backfill/backtest on Z:)
- **Legion5 autorun:** `bash D:/KMIA_Process/scripts/54b_autorun_ndfd_kalshi.sh --once 202604_202606`
- **NAS scheduled policy:** `sudo docker exec kmia-paper-research /usr/local/bin/run_nas_policy_pipeline.sh`
- **Bridge artifacts (review + frontier):** `bash ingest/scripts/refresh_trading_bridge.sh`
- **Archive coverage:** `python3 ingest/scripts/kalshi_archive_status.py`
- **NAS ingest skill:** `.cursor/skills/kmia-nas-ingest/SKILL.md`

**Runtime placement:** NAS = ingest + scheduled policy/paper loop (`kmia-paper-research`). Legion5 = NDFD extract + Kalshi backtest/sweep (writes to `Z:/App_Development/Kalshi`). **Mac = deploy + human review only — never run research pipelines on Mac.**

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
