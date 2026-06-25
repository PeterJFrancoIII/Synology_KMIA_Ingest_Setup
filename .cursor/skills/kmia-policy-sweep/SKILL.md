---
name: kmia-policy-sweep
description: >-
  Runs Kalshi policy sweep and export on Legion5 only. Use when optimizing
  maker_limit/taker parameters, exporting trading_policy_draft.json, or syncing
  research to NAS — not on Mac or NAS daily ingest.
---

# KMIA policy sweep (Legion5)

## Before starting

1. Read `0_Developer_Source_Files/ROUTING.md` → Kalshi backtest row
2. Read `legion5/ACTIVE_MANIFEST.json` → `kalshi_research`
3. Read `ingest/scripts/ACTIVE_MANIFEST.json` → `kalshi_backtest`, `policy_export`
4. Schema sample: `ingest/scripts/fixtures/sample_policy_sweep.json`

## Runtime

| Host | Role |
|------|------|
| **Legion5** | Sweep, backtest, `55_export_maker_policy.sh` |
| **NAS** | Ingest-only (`SKIP_POLICY_SWEEP=1`) — never sweep here |
| **Mac** | Deploy + human `approve_trading_policy.sh` only |

## Typical flow (Legion5 Git Bash)

```bash
bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh
bash D:/KMIA_Process/scripts/55_export_maker_policy.sh
powershell -File D:/KMIA_Process/scripts/55_sync_research_to_nas.ps1
```

## Key Python (FILE MAP in header — do not read whole file)

- `ingest/scripts/kalshi_policy_optimizer.py` → `run_policy_sweep`
- `ingest/scripts/historical_checksum_backtest.py` → `run_kalshi_price_backtest`
- `ingest/scripts/export_trading_policy.py`

## Outputs (contract files — track in git)

- `recommended_policy.json`, `trading_policy_draft.json`
- Timestamped `policy_sweep_*` — **gitignored**; Legion5 mirror retains history

## Hard rules

- No simulated weather (`no-simulated-weather-data.mdc`)
- Human must approve before NAS applies `trading_policy.json`
- Update `trade_policies.md` via `update_trade_policies_doc.py` after tier change
