#!/usr/bin/env python3
"""Regenerate 0_Developer_Source_Files/trade_policies.md from latest policy exports.

Agents MUST run this (or any pipeline that calls it) whenever trading policy
parameters, selection objective, or backtest evidence changes.

NO REAL TRADING — documentation sync only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from kmia_kalshi_paths import console2_backtest_dir, kalshi_research_dir

DOC_REL = Path("0_Developer_Source_Files/trade_policies.md")
MIN_TRADES_NOTE = 20


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_recommended_payload(backtest_dir: Path) -> dict[str, Any]:
    rec_path = backtest_dir / "recommended_policy.json"
    if rec_path.is_file():
        return json.loads(rec_path.read_text(encoding="utf-8"))
    sweeps = sorted(backtest_dir.glob("policy_sweep_*.json"))
    if not sweeps:
        raise FileNotFoundError(f"No recommended_policy or policy_sweep in {backtest_dir}")
    sweep = json.loads(sweeps[-1].read_text(encoding="utf-8"))
    return {
        "recommended_policy": sweep.get("recommended_policy"),
        "policy_tiers": sweep.get("policy_tiers"),
        "source_sweep": str(sweeps[-1]),
        "generated_at_utc": sweep.get("generated_at_utc"),
    }


def _pct(v: Any) -> str:
    try:
        return f"{float(v):.0%}"
    except (TypeError, ValueError):
        return "?"


def _money(v: Any) -> str:
    try:
        return f"${float(v):.2f}"
    except (TypeError, ValueError):
        return "?"


def _tier_row(label: str, t: dict[str, Any]) -> str:
    return (
        f"| {label} | {_pct(t.get('min_forecast_edge'))} | {t.get('insurance_mode', '?')} | "
        f"{_pct(t.get('insurance_budget_fraction'))} | {t.get('insurance_price_k', '?')} | "
        f"{t.get('win_rate_pct', '?')}% | {t.get('roi_pct', '?')}% | {_money(t.get('total_pnl'))} | "
        f"{_money(t.get('total_deployed'))} | {t.get('n_trades', '?')} |"
    )


def build_trade_policies_markdown(
    *,
    payload: dict[str, Any],
    approved: Optional[dict[str, Any]] = None,
    draft: Optional[dict[str, Any]] = None,
) -> str:
    active = payload.get("recommended_policy") or {}
    tiers = payload.get("policy_tiers") or {}
    now = datetime.now(timezone.utc).isoformat()
    source = payload.get("source_sweep") or "unknown"
    selection = active.get("selection_method") or "see recommended_policy.json"
    objective = payload.get("selection_note") or payload.get("policy_objective") or (
        "Maximize probability of profit over recurring daily sessions (highest win-rate insured tier)."
    )

    approved_edge = approved.get("min_forecast_edge") if approved else None
    draft_edge = draft.get("min_forecast_edge") if draft else active.get("min_forecast_edge")
    stale = (
        approved
        and approved.get("approved_by_human")
        and draft
        and (
            approved.get("min_forecast_edge") != draft.get("min_forecast_edge")
            or approved.get("insurance_mode") != draft.get("insurance_mode")
        )
    )

    tier_lines = []
    tier_map = [
        ("**Active (draft export)**", active),
        ("Max P&L / max win-rate", tiers.get("max_pnl")),
        ("Balanced (ROI×win≥68%)", tiers.get("recommended_balanced")),
        ("Max ROI guarded (win≥65%)", tiers.get("max_roi_guarded")),
        ("Max ROI", tiers.get("max_roi")),
    ]
    for label, t in tier_map:
        if t:
            tier_lines.append(_tier_row(label, t))

    lines = [
        "# KMIA Kalshi — Algorithmic Trading Policies",
        "",
        f"**Last synced:** {now}  ",
        "**Maintainers:** AI agents + human operator  ",
        "**Scope:** Console 2 research → Console 3 paper loop (file-only bridge)  ",
        "**Safety:** `no_real_trading: true` — research and paper simulation only until explicitly approved.",
        "",
        "---",
        "",
        "## Agent contract (mandatory)",
        "",
        "1. **Read this file** before changing policy selection, sweep grids, insurance logic, or Console 3 policy loaders.",
        "2. **Update this file** whenever `trading_policy_draft.json`, `recommended_policy.json`, or human selection objective changes:",
        "   ```bash",
        "   PYTHONPATH=ingest/scripts python3 ingest/scripts/update_trade_policies_doc.py",
        "   ```",
        "3. Pipelines that alter policy **must** call the updater (already wired in `export_trading_policy.py`, `kalshi_policy_optimizer.py`, `write_policy_human_review.py`).",
        "4. Cite section headings in code reviews and handoffs (e.g. \"per trade_policies.md § Active Policy\").",
        "",
        "---",
        "",
        "## Strategy summary",
        "",
        "Daily **KXHIGHMIA** markets: bet on which temperature bin contains NWS CLIMIA TMAX at KMIA (MFL/105,51 pin).",
        "",
        "| Layer | Behavior |",
        "|-------|----------|",
        "| **Timing** | Prior-day **10 AM ET** anchor; maker limit bids |",
        "| **Forecast** | NWS high at anchor + `integer_dist_v1` bin probabilities |",
        "| **Forecast leg** | YES on model-favored bin; edge gate via `min_forecast_edge` |",
        "| **Insurance** | Neighbor bins (`fraction` or `cover_book` mode) |",
        "| **Settlement truth** | NCEI CLIMIA TMAX (`kmia_daily_history.jsonl`) — never simulated weather |",
        "",
        "**Three-console split:** This repo (Console 2) owns backtest + policy export. Kalshi repo runs paper loop. No order execution in Console 2.",
        "",
        "---",
        "",
        "## Selection objective (human intent)",
        "",
        objective,
        "",
        f"**Optimizer method:** `{selection}`  ",
        f"**Evidence sweep:** `{source}`  ",
        f"**Minimum sample:** ≥{MIN_TRADES_NOTE} insured trades for tier eligibility.",
        "",
        "### Trade-off law",
        "",
        "You **cannot** simultaneously maximize ROI, win-rate, and total P&L on the same historical sample. Pick one primary objective:",
        "",
        "| Goal | Tier to export | Env / flag |",
        "|------|----------------|------------|",
        "| Highest **ROI** | `max_roi` | `KALSHI_POLICY_SELECTION=max_roi` |",
        "| Highest **win rate** / 3-month safety | `max_pnl` | `KALSHI_POLICY_SELECTION=max_pnl` or manual export |",
        "| Balance ROI × win | `balanced` | `KALSHI_POLICY_SELECTION=balanced` |",
        "| Max dollars | `max_pnl` | same as win-rate tier on current grid |",
        "",
        "---",
        "",
        "## Active policy (draft export)",
        "",
        "Parameters below mirror `Kalshi/backend/data/research/trading_policy_draft.json`.",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| `min_forecast_edge` | {_pct(active.get('min_forecast_edge'))} |",
        f"| `max_entry_yes_ask` | {_money(active.get('max_entry_yes_ask'))} |",
        f"| `order_mode` | maker_limit |",
        f"| `anchor_hour_et` | 10 |",
        f"| `require_cheapest_at_open` | {active.get('require_cheapest_at_open', True)} |",
        f"| `insurance_enabled` | {active.get('insurance_enabled', True)} |",
        f"| `insurance_mode` | {active.get('insurance_mode', 'fraction')} |",
        f"| `insurance_budget_fraction` | {_pct(active.get('insurance_budget_fraction'))} |",
        f"| `insurance_price_k` | {active.get('insurance_price_k', 0.6)} |",
        f"| `live_model_version` | integer_dist_v1 |",
        "",
        "### Backtest metrics (historical — not a guarantee)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Trades | {active.get('n_trades', '?')} |",
        f"| Wins / losses | {active.get('n_wins', '?')} / {active.get('n_losses', '?')} |",
        f"| Win rate | {active.get('win_rate_pct', '?')}% |",
        f"| Total P&L | {_money(active.get('total_pnl'))} |",
        f"| Total deployed | {_money(active.get('total_deployed'))} |",
        f"| ROI | {active.get('roi_pct', '?')}% |",
        f"| Avg insurance legs | {active.get('avg_insurance_legs', '?')} |",
        "",
        "### Approval status",
        "",
    ]
    if stale:
        lines.append(
            "**STALE** — `trading_policy.json` is approved but differs from draft. "
            "Re-approve via `bash scripts/approve_trading_policy.sh` in Kalshi repo."
        )
    elif approved and approved.get("approved_by_human"):
        lines.append("**APPROVED** — paper loop uses `trading_policy.json`.")
    else:
        lines.append("**NOT APPROVED** — paper loop may use legacy policy until human approval.")

    lines.extend([
        "",
        "---",
        "",
        "## Tier comparison (same sweep)",
        "",
        "| Tier | Edge | Ins mode | Ins budget | k | Win % | ROI | P&L | Deployed | Trades |",
        "|------|------|----------|------------|---|-------|-----|-----|----------|--------|",
        *tier_lines,
        "",
        "---",
        "",
        "## Compute routing",
        "",
        "| Host | Role |",
        "|------|------|",
        "| **Legion5** | Canonical backtest + sweep (`54_kalshi_ndfd_research_pipeline.sh`, `Z:` SMB) |",
        "| **NAS** | Scheduled refresh (`kmia-paper-research`) — no NDFD extract |",
        "| **Mac** | Deploy scripts + human review only — **never** run sweep/backtest |",
        "",
        "See `docs/architecture/KALSHI_TRADING_BRIDGE_STATE.md` for operator commands.",
        "",
        "---",
        "",
        "## Code map",
        "",
        "| Component | Path |",
        "|-----------|------|",
        "| Policy sweep | `ingest/scripts/kalshi_policy_optimizer.py` |",
        "| Backtest | `ingest/scripts/historical_checksum_backtest.py` |",
        "| Manifest export | `ingest/scripts/trading_policy_manifest.py` |",
        "| Draft export | `ingest/scripts/export_trading_policy.py` |",
        "| Human review | `ingest/scripts/write_policy_human_review.py` |",
        "| **This doc sync** | `ingest/scripts/update_trade_policies_doc.py` |",
        "| Console 3 loader | `Kalshi/backend/data/research/trading_policy.json` |",
        "",
        "---",
        "",
        "## Constraints (non-negotiable)",
        "",
        "- No simulated weather in forecasts or settlement (see `.cursor/rules/no-simulated-weather-data.mdc`).",
        "- No live Kalshi orders from Console 2.",
        "- Settlement: NCEI CLIMIA TMAX only for backtest join.",
        "- Station pin: 25.7906, -80.3164 (NWS MFL/105,51).",
        "",
        "---",
        "",
        "## Change log",
        "",
        f"| Date (UTC) | Change |",
        "|------------|--------|",
        f"| {now[:10]} | Auto-sync from `{Path(source).name}` — active tier `{selection}`. |",
        "",
    ])
    return "\n".join(lines) + "\n"


def update_trade_policies_doc(
    *,
    repo_root: Optional[Path] = None,
    backtest_dir: Optional[Path] = None,
    kalshi_research: Optional[Path] = None,
) -> Path:
    repo_root = repo_root or _repo_root()
    backtest_dir = backtest_dir or console2_backtest_dir()
    kalshi_research = kalshi_research or kalshi_research_dir()
    payload = _load_recommended_payload(backtest_dir)

    approved_path = kalshi_research / "trading_policy.json"
    draft_path = kalshi_research / "trading_policy_draft.json"
    approved = (
        json.loads(approved_path.read_text(encoding="utf-8"))
        if approved_path.is_file()
        else None
    )
    draft = (
        json.loads(draft_path.read_text(encoding="utf-8"))
        if draft_path.is_file()
        else None
    )

    doc_path = repo_root / DOC_REL
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(
        build_trade_policies_markdown(payload=payload, approved=approved, draft=draft),
        encoding="utf-8",
    )
    return doc_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sync trade_policies.md from latest policy export.")
    parser.add_argument("--backtest-dir", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        path = update_trade_policies_doc(
            repo_root=args.repo_root,
            backtest_dir=args.backtest_dir,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Updated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
