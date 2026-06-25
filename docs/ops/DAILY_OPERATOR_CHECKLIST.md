# Daily operator checklist — paper trading (NAS)

**Mode:** Paper simulation only — no live Kalshi orders  
**Runtime:** NAS only (`kmia-paper-research`, `kmia-orderbook-ws`)  
**Time budget:** ~10 minutes on LAN

## 1. Automated health watch (start here)

```bash
cd "$HOME/Desktop/App Development/Synology_KMIA_Ingest_Setup"
NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
echo "exit=$?"
```

| Exit | Meaning | Action |
|------|---------|--------|
| **0** | Green | Log archived; continue |
| **1** | Yellow | Review warnings in log; no policy changes |
| **2** | Red | Fix before trusting forward metrics |

Log: [`watch_logs/latest_watch.log`](watch_logs/latest_watch.log)

### Red alerts (stop and fix)

- `weather_gate ERROR` or `current_temp_f` missing
- NAS containers down or SSH failed
- WS heartbeat &gt; 120 min or disconnected
- Paper cron silent &gt; 30 min
- `trading_policy.json` or `latest_paper_signal.json` missing
- Policy vs signal `order_mode` mismatch

### Yellow alerts (monitor)

- MOCK trades are only wins in ledger — use **real_kxhighmia** scorecard stats
- Open legs blocking new entries (expected during accumulation)
- NWS `stale_data` flag
- Mac bot console `:8502` down (optional Streamlit)

---

## 2. In-container verify (NAS)

```bash
ssh MediaServer2 'sudo /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research python3 /data/Kalshi/scripts/verify_smarter_paper.py'
```

**Targets:** `orderbook_artifact.source: kalshi_ws` · 12 KXHIGHMIA tickers · policy `maker_limit` approved

---

## 3. Cron and loop logs

```bash
ssh MediaServer2 'sudo tail -20 /volume2/Data/App_Development/logs/paper_trading/cron.log'
ssh MediaServer2 'sudo ls -lt /volume2/Data/App_Development/logs/paper_trading/paper_loop_*.log | head -3'
```

Confirm a loop completed within the last 30 minutes.

---

## 4. NWS snapshot spot-check

```bash
ssh MediaServer2 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/weather_nws/latest_nws_kmia_snapshot.json' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('endpoint_status', d.get('endpoint_status'))
print('current_temp_f', d.get('current_temp_f'))
print('observed_max', d.get('observed_max_so_far_f'))
print('forecast_high', d.get('forecast_high_f'))
print('latest_obs', d.get('latest_observation_time'))
"
```

Must have `current_temp_f`, `forecast_high_f`, `endpoint_status != ERROR`.

---

## 5. Forward scorecard (honest stats)

```bash
ssh MediaServer2 'sudo /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research bash -c "cd /data/Kalshi && PYTHONPATH=backend/src python3 scripts/paper_forward_scorecard.py"'
ssh MediaServer2 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/status/paper_forward_scorecard.json' | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('trade_stats_real_kxhighmia',{})
m=d.get('mission_progress',{})
print('real settled', r.get('settled_trades'), 'win_rate', r.get('win_rate_pct'), 'pnl', r.get('total_pnl'))
print('gates', m)
print('mock_contamination', d.get('mock_contamination'))
"
```

Use **`trade_stats_real_kxhighmia`**, not aggregate `trade_stats`, for governance decisions.

---

## 6. Open legs vs NO_BET

```bash
ssh MediaServer2 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/paper_trading/latest_paper_signal.json' | python3 -c "
import json,sys
s=json.load(sys.stdin)
b=s.get('bet_recommendations') or {}
print('global_action', b.get('global_action'))
print('block', b.get('global_block_reason'))
wg=s.get('weather_gate') or {}
print('weather_gate', wg.get('status'), wg.get('no_trade_reason'))
"
```

---

## Open-position hygiene

Open KXHIGHMIA legs **block new forecast entries** for the same event date (`NO_BET: Forecast position already open`). This is expected during accumulation.

| Check | Expected |
|-------|----------|
| `settle_paper_trades.sh` runs each loop | Yes — step 5/6 in `run_paper_trading_loop.sh` |
| Settlement source | NCEI CLIMIA TMAX via `kmia_daily_history.jsonl` (NAS daily pipeline) |
| Settlement availability | 06:00 UTC on event_date + 1 day |
| Open legs after settlement window | Human review — check NCEI row exists for `target_date` |

```bash
# Open legs on NAS
ssh MediaServer2 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/paper_trading/ledger.json' | python3 -c "
import json,sys
for t in json.load(sys.stdin).get('trades',[]):
    if str(t.get('status','')).lower()=='open':
        print(t.get('market_ticker'), t.get('target_date'))
"
```

If legs remain open **>48h after settlement window**, check `paper_loop_*.log` for settlement errors and NCEI gap for that date.

---

## 7. Policy re-approval gate (do not skip)

**Hold** `approve_trading_policy.sh` until all gates pass:

| Gate | Target |
|------|--------|
| Real KXHIGHMIA settled | ≥ 20 |
| maker_limit era settled | ≥ 10 |
| WS orderbook archive | ≥ 14 days (~2026-07-06) |

See: [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md), [`PAPER_TRADING_READINESS.md`](PAPER_TRADING_READINESS.md)

---

## 8. Weekly (Sunday after scorecard cron)

```bash
NAS_HOST=MediaServer2 ./ingest/scripts/pull_paper_forward_dossier.sh
```

Review: [`paper_forward_analysis/`](paper_forward_analysis/)

---

## Escalation

| Issue | Allowed without approval | Needs human approval |
|-------|--------------------------|----------------------|
| Container exited | Restart `kmia-paper-research` once | Rebuild image |
| NWS fetch fail | Re-run loop once after API recovery | Code deploy |
| Policy change | — | `approve_trading_policy.sh` |
| Ledger MOCK cleanup | — | NAS ledger edit |
| Live trading | — | Red-zone; not in scope |

Watch protocol: [`PAPER_LOOP_WATCH_PROTOCOL.md`](PAPER_LOOP_WATCH_PROTOCOL.md)
