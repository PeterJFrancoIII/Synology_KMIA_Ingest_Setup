# Mission

## User objective

Build and operate a **KMIA NDFD historical ingest + forecast-precision research system** for Kalshi max-temperature market analysis (dry-run / research only — no live trading).

## Current objective

Maintain the three-machine pipeline (Mac → NAS → Legion5), keep extracted VALID_ONLY CSV lakes current through 2025, and produce golden-master forecast-vs-observed charts and accuracy studies for all years.

## Success criteria

- [x] Complete 2020–2025 NDFD maxt + wdir VALID_ONLY extracts on Legion5
- [x] Per-year and all-years analysis + chart portal on Legion5
- [ ] Mac-local chart portal synced when needed (optional; primary view on Legion5)
- [ ] NAS raw lake gaps documented and backfilled where write access allows
- [ ] All agent work follows Zero-Drift Bootloader governance

## Non-goals

- Live Kalshi order execution or trading automation
- Storing multi-GB GRIB or yearly forecast CSVs in git
- NAS-side wgrib2 as primary compute path
- SCP/SFTP for NAS data pulls (SMB + SSH tar fallback only)

## Constraints

- **Stack:** Bash/Python on Legion5 (Miniforge), Docker ingest on Synology DS225+, Mac for deploy/docs
- **Deployment:** Scripts rsync/scp to NAS and Legion5; no cloud runtime
- **Security/privacy:** No secrets in repo; NAS SMB user `kmia_legion5` read-only on Legion5
- **Timeline:** Research archive 2020–2025; 2026 ingest via Docker when enabled

## Source of truth

- **Bootloader (mandatory for all agents):** `docs/bootloader/AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md`
- **Project state:** `docs/PROJECT_STATE_AND_OBJECTIVES.md`
- **Current slice spec:** `docs/specs/current-objective.md`
- **Agent rules:** `AGENTS.md`, `.cursor/rules/`
- **Workflow:** `Research/Agent Analysis of KMIA Forecast Precision/OPTIMAL_ANALYSIS_WORKFLOW.md`

## Red-zone areas

Auth, payments, production infrastructure, customer data, secrets, and destructive NAS writes require explicit human approval.
