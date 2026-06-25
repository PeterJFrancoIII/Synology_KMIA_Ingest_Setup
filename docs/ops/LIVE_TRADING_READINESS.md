# Live trading readiness (future gate)

**Status:** Not ready — paper accumulation phase  
**Mode:** Paper only until all gates in [`ACCUMULATION_GATES.md`](ACCUMULATION_GATES.md) clear  
**Red-zone:** Requires explicit human approval before any live order execution

---

## Prerequisites (all required)

### Paper forward gates

- [ ] Real KXHIGHMIA settled n ≥ 20 (post-policy subset reported separately)
- [ ] maker_limit era settled n ≥ 10
- [ ] WS orderbook archive ≥ 14 days
- [ ] Scorecard `avg_edge` populated on real trades
- [ ] Forward win rate within plausible band vs Legion5 backtest (after fair filters)
- [ ] WS maker replay pilot validates fill VWAP assumptions (`pilot_ws_maker_replay.py`)

### Policy and science

- [ ] Human policy tier review per [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md)
- [ ] `prob_model_comparison.json` reviewed — live/backtest P(bin) drift acceptable
- [ ] Plain-English review in `policy_review_for_human.txt`
- [ ] `approve_trading_policy.sh` run with typed `APPROVE` (if tier changes)

### Infrastructure

- [ ] `kmia_paper_ops_watch.sh` green (exit 0) for 7 consecutive days
- [ ] Weather gate ≥ 95% cycles OK over 7 days
- [ ] Legion5 → NAS research sync automated (`55_sync_research_to_nas.ps1` + manifest)
- [ ] No unresolved RED items in [`PAPER_TRADING_READINESS.md`](PAPER_TRADING_READINESS.md)

### Console 3 / execution (not in Console 2 repo)

- [ ] Dedicated Auto Trader module with `no_real_trading` governance
- [ ] Capital limits and max daily loss defined
- [ ] Kalshi API credentials scoped for production (human-managed secrets)
- [ ] Rollback plan documented

---

## Explicit non-goals until this checklist completes

- No `no_real_trading: False` without human sign-off on this document
- No simulated weather backfill
- No policy tier change to “fix” forward win rate without Legion5 sweep
- No MOCK ledger rows in governance metrics

---

## Related

- Accumulation tracking: [`ACCUMULATION_GATES.md`](ACCUMULATION_GATES.md)
- Daily ops: [`DAILY_OPERATOR_CHECKLIST.md`](DAILY_OPERATOR_CHECKLIST.md)
- Architecture: [`../architecture/THREE_CONSOLE_ARCHITECTURE.md`](../architecture/THREE_CONSOLE_ARCHITECTURE.md)
