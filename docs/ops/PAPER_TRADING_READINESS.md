# Paper trading readiness — status matrix

**Updated:** 2026-06-24  
**Mode:** Paper simulation only — no live Kalshi orders  
**Runtime:** NAS `kmia-paper-research` only (Mac = deploy + approve)

## Short answer

| Question | Answer |
|----------|--------|
| Is paper trading live on NAS? | **Yes** — 5-min cron, maker_limit, dynamic window |
| Is orderbook ingest live? | **Yes** — WS daemon + REST archive |
| Is backtest/policy at full capacity? | **Partial** — Legion5 owns sweep; WS archive still young |
| Ready to optimize win rate? | **Collecting** — forward scorecard weekly; re-review at n≥20 |

---

## System status

| Component | Status | Host | Schedule | Health signal |
|-----------|--------|------|----------|---------------|
| Paper loop | **Live** | NAS `kmia-paper-research` | `*/5 * * * *` | `kmia_paper_ops_watch.sh`, `latest_paper_signal.json` |
| WS orderbook | **Live** | NAS `kmia-orderbook-ws` | Continuous | `ws_daemon_status.json`, heartbeat &lt; 120s |
| REST orderbook archive | **Live** | Paper loop | Every 5 min | `orderbooks/YYYY-MM-DD.jsonl` |
| WS snapshots | **Growing** | WS daemon | 60s | `orderbook_ws_snapshots/` (since ~2026-06-22) |
| Daily policy pipeline | **Ingest-only** | NAS | `30 2 * * *` | `SKIP_POLICY_SWEEP=1` in pipeline |
| Legion5 policy sweep | **Primary** | Legion5 | Weekly Task Scheduler | `55_quant_core_baseline.sh`, `55_trading_window_ab.sh` |
| Approved policy | **Live** | NAS `trading_policy.json` | Human approved 2026-06-24 | maker_limit 18% / $0.35, n=22 |
| Forward scorecard | **Scheduled** | NAS | `0 7 * * 0` | `paper_forward_scorecard.json` |

---

## Green (operational)

- Containers: `kmia-paper-research`, `kmia-orderbook-ws`, `kmia-arch-ingest`
- Approved policy: **maker_limit**, 18% min edge, dynamic window, `PAPER_ORDER_MODE=maker_limit`
- `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1` in secrets + [`kmia_kalshi_env.sh`](../../ingest/scripts/kmia_kalshi_env.sh)
- Legion5 export: [`55_export_maker_policy.sh`](../../legion5/55_export_maker_policy.sh)
- Human governance: [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md)
- Deploy runbook: [`../NAS_Runbook.md`](../NAS_Runbook.md) § Canonical deploy

---

## Yellow (partial / needs attention)

| Gap | Impact | Action |
|-----|--------|--------|
| **Legion5→NAS robocopy** | Manual Mac SSH fallback | `43b_setup_nas_smb_write.ps1` + `55_sync_research_to_nas.ps1` |
| **WS archive &lt; 14 days** | Thin maker book replay | Wait; optional vendor L2 |
| **Forward paper sample thin** | Low confidence in live maker fills | Weekly scorecard; re-review at n≥20 |
| **NAS raw / NWS gaps** | MAE priors under-scored on NAS | Legion5 `52_*` or NAS NDFD NWS backfill |
| **NBM / isotonic gates** | Off until archive grows | Daily NBM fetch; re-fit isotonic when multi-year CSV ready |

---

## Red (not done)

| Gap | Action |
|-----|--------|
| DSM `kalshi_inbound` SFTP user | [`setup_kalshi_inbound_drop.sh`](../../synology/scripts/setup_kalshi_inbound_drop.sh) |
| Kalshi vendor historical L2 | [`KALSHI_VENDOR_DATA_REQUEST.md`](KALSHI_VENDOR_DATA_REQUEST.md) |
| Console 1 bot health endpoint | Fix or remove from ops watch (`bot_console: DOWN`) |

---

## Daily verification (LAN)

```bash
NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
```

**Targets:** WS heartbeat &lt; 120s · 12 tickers · `orderbook_artifact.source: kalshi_ws` · `policy_approved: maker_limit`

```bash
ssh MediaServer2 'sudo grep KMIA /etc/crontab'
ssh MediaServer2 'sudo docker ps | grep kmia'
```

---

## Canonical deploy

See **[`docs/NAS_Runbook.md`](../NAS_Runbook.md)** § Canonical deploy — single ordered checklist (do not piecemeal hot-patch).

Quick reference:

```bash
cd "/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup"
NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh
NAS_HOST=MediaServer2 ./synology/scripts/deploy_paper_trading_window_fix.sh
```

---

## Legion5 policy export (after sweep)

```bash
bash D:/KMIA_Process/scripts/55_export_maker_policy.sh
powershell -ExecutionPolicy Bypass -File D:/KMIA_Process/scripts/55_sync_research_to_nas.ps1
```

Then push approved policy to NAS only (not Mac ledger):

```bash
cat Kalshi/backend/data/research/trading_policy.json | ssh MediaServer2 \
  "sudo tee /volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy.json > /dev/null"
```

---

## Accumulation (wait — not code blockers)

| Item | Action |
|------|--------|
| NBM validation gate | ≥4 weeks archive before enabling gate |
| Isotonic calibration | Re-fit after multi-year enriched CSV |
| WS archive depth | Grows daily on NAS |
| Forward paper n | Weekly scorecard; policy review at n≥20 |

---

## Related

- Watch protocol: [`PAPER_LOOP_WATCH_PROTOCOL.md`](PAPER_LOOP_WATCH_PROTOCOL.md)
- Bridge state: [`../architecture/KALSHI_TRADING_BRIDGE_STATE.md`](../architecture/KALSHI_TRADING_BRIDGE_STATE.md)
- Current objective: [`../../0_Developer_Source_Files/current-objective.md`](../../0_Developer_Source_Files/current-objective.md)
