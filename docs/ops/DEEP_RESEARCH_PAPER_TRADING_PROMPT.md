# Deep research prompt — KMIA Kalshi paper trading system

**Use:** Copy everything below the horizontal rule into Claude, Gemini, o1, or similar. Attach the artifacts listed in §7.

---

## Prompt (copy from here)

You are advising a **read-only research program** for Kalshi **KXHIGHMIA** (Miami daily high temperature) markets. There is **no live order placement** — only paper simulation on a $100 ledger using real weather and real Kalshi prices.

### Mission

Help us improve **calibrated win probability** and policy design. We cannot simultaneously maximize ROI, win rate, and total P&L on the same sample — state trade-offs explicitly.

### Architecture (three consoles)

| Console | Role | Host |
|---------|------|------|
| **Console 1** | Human Kalshi dashboard (Streamlit) | Mac / Kalshi repo |
| **Console 2** | Weather ingest, MAE research, backtest, policy sweep, export `trading_policy.json` | NAS + Legion5 |
| **Console 3** | Paper loop, signal engine, simulated ledger | NAS (`kmia-paper-research` container) |

Integration is **files only** — no cross-repo imports at runtime.

### What runs on NAS today (2026-06-23)

1. **Paper loop** — DSM cron every **5 minutes** → signal → simulated fills → settlement. Bankroll **$100**. Approved policy: **taker**, `min_forecast_edge: 0.0`, `max_entry_yes_ask: 0.25`, low confidence (n≈4 backtest trades at approval time).
2. **WebSocket orderbook daemon** (`kmia-orderbook-ws`) — continuous `orderbook_delta` for 12 KXHIGHMIA bins; 60s full-book checkpoints; heartbeat `ws_daemon_status.json`.
3. **Smarter paper stack** — WS-fresh books win over stale REST; MAE-calibrated edge (`integer_dist_v1` + shrink); ladder VWAP taker fills through policy cap; audit fields on `latest_paper_signal.json`.
4. **Daily policy pipeline** — cron **2:30 AM ET** → ingest minute CSVs, NCEI settlement, backtest, policy sweep, export `trading_policy_draft.json` (human must approve).

### Backtest design anchors

| Concept | Anchor |
|---------|--------|
| Bet / bin-open timing | **Prior-day 10 AM ET** |
| Forecast at bet time | Latest real NWS / rules_v2 / IEM GFS MOS **≤ 10:30 AM ET** prior day |
| Settlement | Official NCEI CLIMIA TMAX (`USW00012839`) |
| P(bin) model | `integer_dist_v1` (aligned with live paper when env set) |
| Execution modes | **Taker** (matches live paper) vs **maker_limit** (historical grid) |

**Known divergence:** Backtest anchors **10 AM ET once per day**; live paper runs **every 5 min intraday** (defunct penny bins, obs alignment, concentration gates).

### Hard rules (non-negotiable)

- **No simulated, synthetic, or proxy weather** for forecasts or observations.
- **No live Kalshi orders** in this research path.
- Do not recommend “maximize everything” — cite the trade-off law.
- NDFD is forecast research only — never treated as observed settlement.

### Data inventory

| Data | Coverage | Gap |
|------|----------|-----|
| Kalshi minute price-history CSV | Apr 2026 → present | Top-of-book from candles, not full L2 history |
| REST orderbook archive | 5-min snapshots from paper loop | Sparse vs WS |
| WS orderbook archive | **Since ~2026-06-22** | No pre-cutoff full depth |
| WS 60s checkpoints | Growing daily | Backtest loader wired; thin history |
| NWS snapshots + IEM GFS MOS | ~95% join on scored days | NAS scorecard sometimes shows path bugs |
| NCEI daily TMAX | Full settlement research | — |
| NDFD point extract at MapClick pin | Legion5 + NAS backfill | 64/65 days missing forecast validation on one NAS taker run |
| Vendor bulk L2 | Inbound drop zone dirs only | DSM SFTP user not provisioned; Kalshi outreach draft ready |

### Policy tiers (recent sweeps)

| Tier | min_edge | max_ask | Trades | Win % | Notes |
|------|----------|---------|--------|-------|-------|
| **Approved (live)** | 0% | $0.25 | ~4 | ~75% (backtest) | Data-collection mode |
| **Draft (moderate)** | 26% | $0.35 | 22 | ~27% | Not approved; maker_limit sweep on NAS |
| **Balanced / max-win-rate** | 14% | $0.35 | 1 | 100% | Very small n |

Forward paper: ~14 settled trades, ~14% win rate (small sample, includes pre-policy era).

### Open questions (answer these directly)

1. Given **n≈22** insured backtest trades and **~14** forward paper trades, what **`min_forecast_edge`** and **`max_entry_yes_ask`** tier best targets **win probability** vs sample size? Should we stay on 0% edge for data collection or move to 14–26%?
2. How much does **intraday 5-min paper** vs **10 AM-only** decision timing distort forward win rate vs backtest? Is a `10 AM paper tick only` mode worth implementing before trusting live win stats?
3. **Next data ROI:** Legion5 NDFD anchor backfill + full sweep, more WS archive days, or Kalshi vendor historical L2 — which unblocks win-rate research fastest?
4. Are we underusing signal features: **wind regime**, **observed-hour alignment**, **defunct penny-bin filters**, **insurance leg coverage**, **concentration gate** (one forecast leg per settlement date)?
5. **Red flags:** NAS daily cron once ran **maker_limit** backtest while live paper uses **taker** — how dangerous is approving a maker-derived draft for taker execution?
6. What monitoring metrics should we watch daily besides `candidate_to_buy_overlap` and WS heartbeat age?
7. Propose a **90-day research roadmap** with ordered milestones and explicit stop rules (when to stop adding data tiers).

### Response format

1. **Executive summary** (≤5 bullets)
2. **Top 3 recommendations** (actionable, with expected win-rate vs trade-count trade-off)
3. **Risks / false confidence** (where our sample or parity gaps mislead us)
4. **Data investments ranked** (effort vs win-rate insight)
5. **Policy recommendation** (approve, hold, or hybrid — with parameters)
6. **Optional:** pseudocode or env flags for 10 AM parity mode if you recommend it

---

## Artifacts to attach

Pull from NAS or local Kalshi/Console 2 trees:

| File | Purpose |
|------|---------|
| `Kalshi_Price_Backtest/policy_sweep_*.json` (latest) | Sweep grid + Pareto frontier |
| `Kalshi_Price_Backtest/recommended_policy.json` | Optimizer pick |
| `Kalshi_Price_Backtest/prob_model_comparison.json` | gaussian vs integer_dist parity |
| `Kalshi_Price_Backtest/policy_frontier_*.html` | Visual frontier |
| `Kalshi/backend/data/research/trading_policy.json` | Approved policy |
| `Kalshi/backend/data/research/trading_policy_draft.json` | Pending draft |
| `Kalshi/backend/data/processed/paper_trading/latest_paper_signal.json` | Live signal audit |
| `Kalshi/backend/data/processed/paper_trading/ledger.json` | Forward paper history |
| `docs/ops/POLICY_TIER_REVIEW.md` | Human tier comparison |
| `0_Developer_Source_Files/trade_policies.md` | Trade-off law |

## Related ops docs

- Readiness matrix: [`PAPER_TRADING_READINESS.md`](PAPER_TRADING_READINESS.md)
- Daily health: [`PAPER_LOOP_WATCH_PROTOCOL.md`](PAPER_LOOP_WATCH_PROTOCOL.md)
- WS ingest: [`../architecture/KALSHI_WS_ORDERBOOK_INGEST.md`](../architecture/KALSHI_WS_ORDERBOOK_INGEST.md)
- Bridge state: [`../architecture/KALSHI_TRADING_BRIDGE_STATE.md`](../architecture/KALSHI_TRADING_BRIDGE_STATE.md)
