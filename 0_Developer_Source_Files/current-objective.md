# Current objective

**Updated:** 2026-06-20  
**Status:** Legion5 chart portal live; **Kalshi trading-policy bridge active** (Console 2 → 3)

## Active slice

1. **Legion5 / MAE research** — chart portal, all-years merge, NAS gap documentation
2. **Kalshi policy bridge** — price-history backtest, policy sweep, `trading_policy.json` export, thin-market liquidity caps, human review artifacts

See: `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`

## Success for this slice

### MAE / ingest
- [x] 2020–2025 maxt + wdir VALID_ONLY on Legion5
- [x] Per-year + all-years analysis and chart suites
- [x] Chart portal with 8 studies
- [ ] Document any remaining NAS raw gaps (see `docs/ARCHIVE_INTEGRITY_AUDIT_2026-06-16.md`)

### Kalshi trading bridge (Console 2 → 3)
- [x] Kalshi price backtest at prior-day 10 AM ET anchor (maker + taker)
- [x] Weather join: IEM GFS MOS + NCEI TMAX + NWS snapshots (~95% day coverage)
- [x] `trading_policy.json` export + pipeline status + plain-English review
- [x] Console 3 policy loader, maker limits, insurance, liquidity caps
- [x] Candle archive loader + maker fill fallback (orderbook → candle → CSV)
- [x] P(bin) aligned via `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1` (default in kmia_kalshi_env.sh)
- [ ] Human approval of current draft policy (operator action — see `policy_review_for_human.txt`)

## Non-goals (this slice)

- Console 1 / Console 3 **order execution** code in this repo
- Git-storing multi-GB forecast CSVs
- Live Kalshi order placement
- Auto-approve trading policy

## Architecture reference

- **Three consoles:** `docs/architecture/THREE_CONSOLE_ARCHITECTURE.md`
- **Console 2 exports:** `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md`
- **Kalshi bridge state:** `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md`
- **Topology:** [PROJECT_STATE_AND_OBJECTIVES.md](PROJECT_STATE_AND_OBJECTIVES.md)
