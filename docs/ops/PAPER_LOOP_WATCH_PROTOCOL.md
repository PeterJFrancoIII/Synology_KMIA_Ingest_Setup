# Paper loop watch protocol (9h agent loop)

**Created:** 2026-06-20  
**Mode:** Read-only diagnostics unless explicit failure

## Restore from backup

Backups live under:

`~/Desktop/App Development/KMIA_System_Backups/pre_watch_20260620/`

```bash
# Example restore Console 2 (destructive — extract elsewhere first)
cd "/Users/computer/Desktop/App Development"
tar xzf KMIA_System_Backups/pre_watch_20260620/Synology_KMIA_Ingest_Setup.tar.gz
```

See `MANIFEST.txt` in that folder for checksums.

## Agent rules during watch

**Allowed (green):**
- Read NAS logs via SSH
- Run `ingest/scripts/kmia_paper_ops_watch.sh`
- Restart `kmia-paper-research` container if exited (no rebuild)
- Re-run `run_nas_paper_loop.sh` once if cron silent >30 min

**Forbidden without human approval:**
- Git force push, mass deletes, policy re-approval
- NAS secrets, trading_policy.json edits
- Code changes in Kalshi/Console2 unless single-line cron fix

## Watch log

`docs/ops/watch_logs/latest_watch.log` (in this repo)

## Loop

30-minute ticks for 9 hours via background shell sentinel `AGENT_LOOP_TICK_paper_watch`.

## Daily health (LAN)

```bash
./ingest/scripts/kmia_paper_ops_watch.sh
# or: NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
```

Checks: containers, WS heartbeat age, `verify_smarter_paper.py`, cron tail, policy/signal JSON, **real_kxhighmia ledger stats**, NWS snapshot.

**Exit codes:** `kmia_paper_ops_watch.sh` returns `0` green · `1` yellow · `2` red.

**Escalation:** RED → fix weather gate / containers / cron before trusting forward metrics. Do not re-approve policy on MOCK-inflated win rates.

**Targets:** WS heartbeat &lt; 120s; 12 KXHIGHMIA tickers; `orderbook_artifact.source: kalshi_ws`; `candidate_to_buy_overlap` ≥ 90% when markets tradable.

**Policy tier review:** [`POLICY_TIER_REVIEW.md`](POLICY_TIER_REVIEW.md) before next `approve_trading_policy.sh`.

**Vendor inbound:** [`KALSHI_INBOUND_DATA_CONTRACT.md`](KALSHI_INBOUND_DATA_CONTRACT.md)

**Readiness matrix:** [`PAPER_TRADING_READINESS.md`](PAPER_TRADING_READINESS.md)

**Forward analysis dossier:** [`paper_forward_analysis/PAPER_FORWARD_ANALYSIS_20260625.md`](paper_forward_analysis/PAPER_FORWARD_ANALYSIS_20260625.md)

**Deep research prompt:** [`DEEP_RESEARCH_PAPER_TRADING_PROMPT.md`](DEEP_RESEARCH_PAPER_TRADING_PROMPT.md) — copy into Claude/Gemini for system review

**Forward scorecard (weekly):** Kalshi `scripts/paper_forward_scorecard.py` — win rate, blocks, avg edge

**Resilience env (NAS `kmia_paper_research.env`):** `PAPER_TRADING_WINDOW=dynamic` (default); `PAPER_LOOP_ANCHOR_ONLY=0`; `PAPER_ORDER_MODE=maker_limit` (aligns paper with maker backtest). Optional: `PAPER_TRADING_WINDOW=anchor_only` for debug; `PAPER_STRICT_MARKET_AGREEMENT`, `MAX_OBS_AGE_MINUTES`, `PAPER_MIN_CALIBRATED_EDGE_FLOOR`
