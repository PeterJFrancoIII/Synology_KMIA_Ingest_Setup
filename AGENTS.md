# Agent Operating Rules

## Prime directive

Build the user's current objective with maximum verified progress and minimum drift.

**Before any session:** Read `docs/bootloader/AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md` (Sections 0–8 minimum) and `MISSION.md`.

## Required loop

1. Read `MISSION.md` and `docs/specs/current-objective.md`.
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
- **NAS ingest skill:** `.cursor/skills/kmia-nas-ingest/SKILL.md`

## Risk classes

| Class | Examples |
|-------|----------|
| **Green** | Docs, research markdown, isolated legion5 scripts, chart HTML |
| **Yellow** | Extract/filter pipeline, merge scripts, NAS pull helpers, dependencies |
| **Red** | Secrets, NAS write/backfill to raw GRIB, production infra, credentials |

Red changes require explicit human approval before edits and before merge.

## Communication

Use terse, evidence-first updates. Preserve exact code, paths, commands, and errors. Respond with MISSION / STATE / PLAN / SCOPE / VERIFY when doing multi-step architect work (per bootloader Section 0).
