# Policy tier review — human decision gate

**Purpose:** Choose which backtest tier to approve before running `approve_trading_policy.sh` in the Kalshi repo.

**Active approved tier (2026-06-24):** `maker_limit`, 18% edge, $0.35 cap, dynamic window — n=22 backtest, `calibration_pass=true`. NAS paper loop only.

**Do not auto-approve.** Read [`policy_review_for_human.txt`](file:///Users/computer/Desktop/App%20Development/Kalshi/backend/data/processed/status/policy_review_for_human.txt) on NAS/Mac after each Legion5 sweep.

---

## Trade-off law

You cannot simultaneously maximize **ROI**, **win rate**, and **total P&L** on the same historical sample. See [`0_Developer_Source_Files/trade_policies.md`](../../0_Developer_Source_Files/trade_policies.md).

---

## Tier comparison (2026-06-22 sweep)

| Tier | `min_forecast_edge` | `max_entry_yes_ask` | Backtest trades | Win % | ROI | Total P&L | Live effect |
|------|---------------------|---------------------|-----------------|-------|-----|-----------|-------------|
| **Active (max-PnL)** | 0% | $0.25 | 4 | 75% | 215% | $42.33 | More entries; intraday noise; current approved policy |
| **Balanced / max-win-rate** | 14% | $0.35 | 1 | 100% | 398% | $19.18 | Fewer entries; higher selectivity |
| **Max ROI guarded** | 14% | $0.35 | 1 | 100% | 398% | $19.18 | Same as balanced on current grid |

**Confidence:** All tiers are **low** until backtest `n_trades ≥ 20` (moderate confidence threshold).

**Calibration gate (2026-06+):** Policy sweep prefers configs with `calibration_pass: true` — `ece ≤ 0.12`, `mean_brier ≤ 0.35`. Baseline Brier/CRPS/reliability emitted in `policy_sweep_*.json`. Human approval also requires forward paper scorecard when available.

---

## Loss taxonomy (Legion5 9% edge tier, 24 trades)

**Source:** `policy_pattern_analysis_20260623T074519Z.json` (sweep `legion5_run_20260622/policy_sweep_20260622T005444Z.json`; Legion5 `20260623T025134Z` equivalent tier on NAS)

| Outcome | Count | % of trades |
|---------|------:|------------:|
| Win | 14 | 58.3% |
| `both_miss` (forecast + insurance missed) | 10 | 41.7% |

**Implication for hybrid path:** Bad-forecast days dominate losses — resilience gates (10 AM anchor, market-agreement, obs staleness) target `both_miss` without raising `min_forecast_edge` in approved policy yet.

**Edge sensitivity:** See `policy_pattern_analysis_20260623T074519Z.json` → `edge_sensitivity_cap_035` (0–30% grid; 9% retains 24 trades @ 58.3% win in draft tier).

---

## Recommendation matrix

| Your priority | Export tier | Env / action |
|---------------|-------------|--------------|
| **Collect forward paper data now** | Keep active max-PnL | No re-approval until sample grows |
| **Tighten win ratio soon** | `balanced` or `max_roi_guarded` | `KALSHI_POLICY_SELECTION=balanced` then re-export + approve |
| **Max dollars on history** | `max_pnl` | Current active tier |
| **Uncertain** | **Hybrid** | Keep current policy; re-sweep after ≥20 trades with `integer_dist_v1` |

---

## Approval checklist

1. Sweep used `KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1` (see [`kmia_kalshi_env.sh`](../../ingest/scripts/kmia_kalshi_env.sh))
2. `prob_model_comparison.json` reviewed — live/backtest P(bin) drift acceptable
3. `policy_frontier_*.html` opened — frontier shape sensible
4. `backtest_metrics.n_trades` noted in draft JSON
5. If `n_trades < 20`: approve only if accepting **low confidence** + `$5` forecast cap
6. Run: `bash scripts/approve_trading_policy.sh` (Kalshi repo) — type `APPROVE`

---

## Export alternate tier (Console 2)

```bash
# On Legion5 or NAS container only — NOT Mac
export KALSHI_POLICY_SELECTION=balanced   # or max_roi, max_pnl
bash ingest/scripts/export_trading_policy.py \
  --backtest-dir "$CONSOLE2_BACKTEST_DIR" \
  --kalshi-research-dir "$KALSHI_RESEARCH_DIR" \
  --order-mode taker
```

Then human review + approve in Kalshi repo.
