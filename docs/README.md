# Documentation map

This repo uses **two documentation layers**. Do not merge them — agents load the boot bundle; operators load reference docs.

## Layer 1 — Agent boot bundle (read every session)

**Location:** [`0_Developer_Source_Files/`](../0_Developer_Source_Files/README.md)

Small, stable files that define mission, law, and current slice. Loaded by Cursor rules and the Zero-Drift bootloader.

| Document | Purpose |
|----------|---------|
| Bootloader | Agent operating law (Sections 0–8) |
| `MISSION.md` | Console 2 mission, success criteria, non-goals |
| `current-objective.md` | **Live truth** — active work slice |
| `AGENTS.md` | Commands, risk classes, deploy paths |
| `trade_policies.md` | Kalshi strategy narrative (auto-synced on policy export) |

Root-level `MISSION.md`, `AGENTS.md`, `CLAUDE.md`, and `trade_policies.md` are **stubs only** — edit the `0_Developer_Source_Files/` copies.

## Layer 2 — Reference docs (load when needed)

**Location:** `docs/` (this directory)

Larger, evolving material for operators and deep work.

| When | Where | Examples |
|------|-------|----------|
| Deploy / operate NAS | [`NAS_Runbook.md`](NAS_Runbook.md), [`ops/`](ops/) | Canonical deploy checklist, paper watch |
| System design | [`architecture/`](architecture/) | Three-console model, export contract, WS ingest |
| Data pipelines | Top-level guides | [`GRIB_CSV_Extraction.md`](GRIB_CSV_Extraction.md), [`Data_Source_Map.md`](Data_Source_Map.md) |
| API specs | [`specs/`](specs/) | OpenAPI / AsyncAPI YAML |
| Session snapshots | [`handoffs/`](handoffs/) (active runbooks) · [`archive/handoffs/`](archive/handoffs/) (dated) | **Not** source of truth |
| Moved paths | [`REDIRECTS.md`](REDIRECTS.md) | Historical path changes |

## Rules

1. **`current-objective.md` beats handoffs** — handoff files are point-in-time; the objective file is canonical state.
2. **Do not duplicate governance into `docs/`** — keeps agent context small (bootloader §7.1).
3. **Do not move runbooks into `0_Developer_Source_Files/`** — bloats always-loaded context.

## Quick links

- Paper trading status: [`ops/PAPER_TRADING_READINESS.md`](ops/PAPER_TRADING_READINESS.md)
- Policy tier review: [`ops/POLICY_TIER_REVIEW.md`](ops/POLICY_TIER_REVIEW.md)
- Console boundaries: [`architecture/THREE_CONSOLE_ARCHITECTURE.md`](architecture/THREE_CONSOLE_ARCHITECTURE.md)
- Console 2 exports: [`architecture/CONSOLE_2_EXPORT_CONTRACT.md`](architecture/CONSOLE_2_EXPORT_CONTRACT.md)
