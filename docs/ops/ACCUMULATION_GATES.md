# Forward validation accumulation gates

**Status:** HOLD policy re-approval until all gates clear  
**Updated:** 2026-06-25

## Active gates

| Gate | Current (2026-06-25) | Target | ETA / owner |
|------|---------------------:|--------|-------------|
| Real KXHIGHMIA settled | 16 | **≥ 20** | Time + healthy paper loop |
| maker_limit post-approval settled | 2 | **≥ 10** | Time + healthy loop |
| WS orderbook archive depth | ~3 days | **≥ 14 days** | ~**2026-07-06** (`kmia-orderbook-ws` uptime) |
| Weather gate uptime | RED (fixed in code) | **≥ 95%** cycles OK | Deploy `nws_live_client.py` fix to NAS |
| Scorecard `avg_edge` on real trades | sparse | populated | After more post-policy trades |

## Explicit holds

- **No** `approve_trading_policy.sh` tier change
- **No** `no_real_trading: False`
- **No** simulated weather backfill
- **No** policy changes to “fix” 0% real win rate without Legion5 sweep

## Weekly review

1. `NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh` (exit 0 required for green ops)
2. `NAS_HOST=MediaServer2 ./ingest/scripts/pull_paper_forward_dossier.sh`
3. Read [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md) and latest [`paper_forward_analysis/PAPER_FORWARD_ANALYSIS_*.md`](paper_forward_analysis/)
4. Compare `trade_stats_real_kxhighmia` to Legion5 `policy_pattern_analysis_*.json` (maker_limit, comparable edge)

## When gates clear

Human checklist in [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md) → `bash scripts/approve_trading_policy.sh` (Kalshi repo) only after all rows above are green.

## WS replay pilot (after ~2026-07-06)

```bash
# Legion5 or NAS container
KALSHI_ROOT=/path/to/Kalshi python3 ingest/scripts/pilot_ws_maker_replay.py 2026-06-22 2026-06-23
```

Report: `docs/ops/paper_forward_analysis/ws_replay_pilot/`
