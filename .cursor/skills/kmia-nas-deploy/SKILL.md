---
name: kmia-nas-deploy
description: >-
  Deploys and operates Console 2 on MediaServer2 (NAS): paper loop, WS
  orderbook archive, cron, secrets. Use when deploying from Mac, installing
  cron, or debugging kmia-paper-research — not for policy sweeps.
---

# KMIA NAS deploy (MediaServer2)

## Before starting

1. Read `docs/NAS_Runbook.md` § **Canonical deploy**
2. Read `0_Developer_Source_Files/ROUTING.md` → NAS deploy row
3. For ingest container only: `.cursor/skills/kmia-nas-ingest/SKILL.md`

## SSH

```bash
export NAS_HOST=MediaServer2   # not MediaServer2Local
```

## Deploy sequence (Mac)

```bash
NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
NAS_HOST=MediaServer2 ./synology/scripts/deploy_paper_trading_window_fix.sh
NAS_HOST=MediaServer2 ./synology/scripts/90_cron_install.sh --activate-all
```

## Verify

```bash
NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
```

## Runtime boundaries

| Container | Purpose |
|-----------|---------|
| `kmia-paper-research` | Paper loop; `SKIP_POLICY_SWEEP=1` on daily pipeline |
| `kmia-orderbook-ws` | WS orderbook archive |
| `kmia-arch-ingest` | NDFD/ISD historical ingest |

## Ops docs

- `docs/ops/PAPER_TRADING_READINESS.md`
- `docs/ops/PAPER_LOOP_WATCH_PROTOCOL.md`
- `docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md`

## Mac must not

- Run `kalshi_policy_optimizer.py` or full backtest sweeps
- Write paper ledger as source of truth (NAS canonical)
