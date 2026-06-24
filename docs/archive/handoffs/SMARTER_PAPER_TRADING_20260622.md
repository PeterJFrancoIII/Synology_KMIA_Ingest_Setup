# Smarter Paper Trading — implementation handoff

**Date:** 2026-06-22  
**Repo:** Kalshi (Console 3) — code changes  
**Console 2:** docs only (`KALSHI_WS_ORDERBOOK_INGEST.md`, `current-objective.md`)

## What shipped

### Phase 1 — Freshest book wins
- `backend/src/market_data/orderbook_merge.py` — per-ticker merge; skip REST when WS artifact is newer
- `update_kalshi_snapshots.py` — preserves fresher `kalshi_ws` books before writing `latest_kalshi_orderbooks.json`
- `signal_generator.py` — `orderbook_artifact` metadata on paper signal report

### Phase 2 — One edge pipeline
- `backend/src/trading/calibrated_edge.py` — `calibrated_contract_edge()`
- `event_signal_builder.py` — MAE-calibrated edge for actions; `PAPER BUY CANDIDATE` uses `effective_min_edge`
- `money_distribution.py` — Kelly sizing on `calibrated_probability`; costs use ladder VWAP when present
- `bet_decision_engine.py` — reuses signal calibrated fields; taker limit from `fill_vwap`

### Phase 3 — Depth-aware taker fill
- `kalshi/orderbook.py` — `walk_yes_ask_ladder`, `build_yes_ask_levels`
- Pricing + liquidity caps use cumulative ask depth through `max_entry_yes_ask`
- `policy_limits.resolve_limit_price_for_signal` prefers `fill_vwap` for taker mode

## Tests (local)

```bash
cd Kalshi/backend
python3 -m pytest tests/test_orderbook_merge.py tests/test_orderbook_ladder.py \
  tests/test_calibrated_edge.py tests/test_signal_generator_helpers.py \
  tests/test_bet_decision_engine.py -q
# 44 passed
```

## Deploy + verify on NAS

```bash
# From Console 2 repo (Mac on LAN)
NAS_HOST=MediaServer2 ./synology/scripts/deploy_kalshi_runtime_to_nas.sh

# On NAS — confirm WS heartbeat < 120s
cat /volume2/Data/App_Development/Kalshi/kalshi_market_archive/ws_daemon_status.json

# After next paper cron cycle — confirm signal audit fields
jq '.orderbook_artifact, .signals[0] | {orderbook_source, fill_vwap, calibrated_probability, executable_edge}' \
  /volume2/Data/App_Development/Kalshi/latest_paper_signal.json
```

## Operator gate (human)

Re-approve taker policy from latest Console 2 sweep draft:

```bash
cd /path/to/Kalshi
bash scripts/approve_trading_policy.sh   # type APPROVE
# Expect: max_entry_yes_ask 0.25, order_mode taker
```

Policy draft: `Research/.../Kalshi_Price_Backtest/recommended_policy.json` (Console 2).
