# Current objective

**Updated:** 2026-06-24  
**Status:** NAS paper loop live (`maker_limit` + dynamic window); Legion5 owns policy sweep; NAS ingest-only daily pipeline

## Active slice

1. **Legion5 / MAE research** — chart portal, all-years merge, NAS gap documentation, weekly quant-core baseline
2. **Kalshi policy bridge** — maker_limit policy approved; Legion5 export → NAS research sync; forward paper validation
3. **Kalshi WS orderbook ingest** — `kmia-orderbook-ws` on NAS; WS archive growing for maker backtest replay

See: `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`, `docs/ops/PAPER_TRADING_READINESS.md`, `docs/NAS_Runbook.md`

## Success for this slice

### MAE / ingest
- [x] 2020–2025 maxt + wdir VALID_ONLY on Legion5
- [x] Per-year + all-years analysis and chart suites
- [x] Chart portal with 8 studies
- [ ] Document any remaining NAS raw gaps (see `docs/ARCHIVE_INTEGRITY_AUDIT_2026-06-16.md`)

### Kalshi trading bridge (Console 2 → NAS runtime)
- [x] Kalshi price backtest — maker + taker; dynamic trading window A/B on Legion5
- [x] Weather join: NCEI TMAX + NWS snapshots (NDFD backfill for gaps; no simulated weather)
- [x] `trading_policy.json` export + pipeline status + plain-English review
- [x] P(bin) aligned via `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1`
- [x] **Human-approved policy:** `maker_limit`, 18% edge, $0.35 cap, n=22 backtest (2026-06-24)
- [x] NAS daily pipeline ingest-only (`SKIP_POLICY_SWEEP=1`); Legion5 weekly sweep owns science
- [ ] Legion5→NAS research robocopy via `nas_smb_write_password` (Mac SSH fallback works; automate)
- [ ] Forward paper n≥20 before next policy tier review (`paper_forward_scorecard.json` weekly)

### Kalshi WS orderbook ingest (NAS)
- [x] WebSocket `orderbook_delta` daemon (`kmia-orderbook-ws` container)
- [x] Raw event archive + 60s checkpoint snapshots on NAS
- [x] Paper loop: WS books, maker_limit via `PAPER_ORDER_MODE`, dynamic window
- [x] Backtest loader for WS snapshots (`kalshi_orderbook_archive_loader.py`)
- [ ] WS archive ≥14 days for full maker replay window (accumulating since ~2026-06-22)

## Runtime placement (canonical)

| Host | Role |
|------|------|
| **NAS** | Ingest, 5-min paper loop, WS archive, daily price/NCEI ingest — **only production runtime** |
| **Legion5** | NDFD extract, backtest, policy sweep, `55_export_maker_policy.sh`, mirror → NAS |
| **Mac** | Deploy scripts, human policy approval, docs — **never run research pipelines** |

## Non-goals (this slice)

- Console 1 / Console 3 **order execution** code in this repo
- Live Kalshi order placement
- NAS policy sweep (conflicts with Legion5 maker science)
- Auto-approve trading policy

## Architecture reference

- **Three consoles:** `docs/architecture/THREE_CONSOLE_ARCHITECTURE.md`
- **Console 2 exports:** `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md`
- **Kalshi bridge state:** `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`
- **NAS deploy checklist:** `docs/NAS_Runbook.md` § Canonical deploy
- **Paper readiness:** `docs/ops/PAPER_TRADING_READINESS.md`
