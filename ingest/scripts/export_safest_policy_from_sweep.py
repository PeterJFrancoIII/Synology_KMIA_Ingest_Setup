#!/usr/bin/env python3
"""Export trading_policy_safest_draft.json from latest policy sweep Pareto frontier.

Selects highest win_rate (then ROI) among insured configs with min sample size.
NO REAL TRADING — Console 2 research export only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from export_trading_policy import _latest_json
from kmia_kalshi_paths import console2_backtest_dir, kalshi_research_dir
from trading_policy_manifest import build_trading_policy_manifest

MIN_TRADES_DEFAULT = 20


def select_safest_from_sweep(sweep: dict[str, Any], *, min_trades: int = MIN_TRADES_DEFAULT) -> Optional[dict[str, Any]]:
    frontier = sweep.get("pareto_frontier") or []
    pool = [c for c in frontier if c.get("insurance_enabled") and c.get("n_trades", 0) >= min_trades]
    if not pool:
        pool = [c for c in frontier if c.get("n_trades", 0) >= min_trades]
    if not pool:
        pool = list(frontier)
    if not pool:
        return None
    pool.sort(key=lambda c: (c.get("win_rate", 0), c.get("roi_pct", 0), c.get("total_pnl", 0)), reverse=True)
    best = pool[0]
    return {
        **{k: best[k] for k in (
            "min_forecast_edge", "max_entry_yes_ask", "require_cheapest_at_open",
            "insurance_enabled", "insurance_mode", "insurance_budget_fraction",
            "insurance_price_k", "n_trades", "n_wins", "n_losses", "win_rate",
            "win_rate_pct", "total_pnl", "total_deployed", "roi_pct",
            "avg_insurance_legs", "insurance_covers_book_rate_pct",
        ) if k in best},
        "selection_method": "pareto_max_win_rate_then_roi_insured",
        "confidence": "moderate" if best.get("n_trades", 0) >= min_trades else "low",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--backtest-dir", type=Path, default=None)
    p.add_argument("--kalshi-research-dir", type=Path, default=None)
    p.add_argument("--min-trades", type=int, default=MIN_TRADES_DEFAULT)
    args = p.parse_args()

    backtest_dir = args.backtest_dir or console2_backtest_dir()
    research_dir = args.kalshi_research_dir or kalshi_research_dir()
    sweep_path = _latest_json(backtest_dir, "policy_sweep_*.json")
    if sweep_path is None:
        print("No policy_sweep JSON found")
        return 1

    sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    safest = select_safest_from_sweep(sweep, min_trades=args.min_trades)
    if not safest:
        print("No suitable safest config in Pareto frontier")
        return 1

    manifest = build_trading_policy_manifest(
        safest,
        source_sweep=str(sweep_path),
        approved_by_human=False,
    )
    out = research_dir / "trading_policy_safest_draft.json"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sweep": str(sweep_path),
        "recommended_safest_policy": safest,
        "trading_policy_safest_draft": manifest,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Safest draft written: {out}")
    print(
        f"  edge={safest.get('min_forecast_edge')} cap={safest.get('max_entry_yes_ask')} "
        f"win={safest.get('win_rate_pct')}% pnl={safest.get('total_pnl')} n={safest.get('n_trades')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
