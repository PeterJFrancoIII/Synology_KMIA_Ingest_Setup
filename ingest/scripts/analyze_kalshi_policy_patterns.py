#!/usr/bin/env python3
"""Loss taxonomy and edge sensitivity from policy sweep artifacts.

NO REAL TRADING — Console 2 research analysis only.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from historical_checksum_backtest import _settle_hedged_trade
from kalshi_policy_optimizer import (
    evaluate_policy_config,
    load_forecast_validated_days,
)
from kalshi_price_history_loader import default_price_history_dir

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 ANALYSIS ONLY",
}


def _latest_sweep(backtest_dir: Path) -> Optional[Path]:
    files = sorted(backtest_dir.glob("policy_sweep_*.json"), reverse=True)
    return files[0] if files else None


def classify_loss(trade_detail: dict[str, Any], observed_max_f: float) -> str:
    """Classify a losing trade day."""
    if trade_detail.get("won"):
        return "win"
    obs_int = int(round(observed_max_f))
    forecast_bin = trade_detail.get("market_bin")
    legs = trade_detail.get("legs") or []
    forecast_hit = any(
        l.get("market_bin_hit") for l in legs if l.get("market_bin") == forecast_bin
    )
    insurance_hit = any(
        l.get("market_bin_hit")
        for l in legs
        if l.get("market_bin") != forecast_bin
    )
    if forecast_hit:
        return "forecast_hit_insurance_miss"
    if insurance_hit:
        return "insurance_hit_forecast_miss"
    return "both_miss"


def edge_sensitivity_curve(
    days: list[dict[str, Any]],
    *,
    cap: float = 0.35,
    insurance_enabled: bool = True,
    insurance_mode: str = "fraction",
    insurance_budget_fraction: float = 0.25,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge_pct in range(0, 31):
        edge = round(edge_pct / 100, 2)
        cfg = evaluate_policy_config(
            days,
            min_forecast_edge=edge,
            max_entry_yes_ask=cap,
            require_cheapest=True,
            insurance_enabled=insurance_enabled,
            insurance_mode=insurance_mode,
            insurance_budget_fraction=insurance_budget_fraction,
        )
        rows.append({
            "edge_pct": edge_pct,
            "n_trades": cfg["n_trades"],
            "win_rate_pct": cfg["win_rate_pct"],
            "total_pnl": cfg["total_pnl"],
            "roi_pct": cfg["roi_pct"],
            "insurance_covers_book_rate_pct": cfg.get(
                "insurance_covers_book_rate_pct", 0.0
            ),
        })
    return rows


def run_analysis(
    *,
    sweep_path: Optional[Path] = None,
    backtest_dir: Optional[Path] = None,
    price_history_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
) -> dict[str, Any]:
    from kmia_kalshi_paths import console2_backtest_dir

    bt_dir = backtest_dir or console2_backtest_dir()
    sweep_file = sweep_path or _latest_sweep(bt_dir)
    if sweep_file is None or not sweep_file.is_file():
        raise FileNotFoundError(f"No policy sweep JSON in {bt_dir}")

    sweep = json.loads(sweep_file.read_text(encoding="utf-8"))
    rec = sweep.get("recommended_policy") or {}
    price_dir = price_history_dir or default_price_history_dir()
    if price_dir is None:
        raise FileNotFoundError("Kalshi price history dir not found")

    from kalshi_candle_archive_loader import default_candle_archive_dir
    from kalshi_orderbook_archive_loader import default_orderbook_archive_dir

    days = load_forecast_validated_days(
        price_dir,
        orderbook_archive_dir=orderbook_archive_dir or default_orderbook_archive_dir(),
        candle_archive_dir=candle_archive_dir or default_candle_archive_dir(),
    )
    cfg = evaluate_policy_config(
        days,
        min_forecast_edge=rec.get("min_forecast_edge", 0.0),
        max_entry_yes_ask=rec.get("max_entry_yes_ask", 0.35),
        require_cheapest=rec.get("require_cheapest_at_open", True),
        insurance_enabled=rec.get("insurance_enabled", True),
        insurance_mode=rec.get("insurance_mode", "fraction"),
        insurance_budget_fraction=rec.get("insurance_budget_fraction", 0.25),
        insurance_price_k=rec.get("insurance_price_k", 0.6),
    )

    loss_labels: Counter[str] = Counter()
    loss_days: list[dict[str, Any]] = []
    for d in days:
        if d["observed_max_f"] is None:
            continue
        t = next((x for x in cfg["trades"] if x["day"] == d["day"]), None)
        if t is None:
            continue
        if t["won"]:
            loss_labels["win"] += 1
            continue
        loss_labels[classify_loss({"won": False, "market_bin": t["market_bin"]}, d["observed_max_f"])] += 1
        loss_days.append({
            "day": d["day"],
            "forecast_bin": t["market_bin"],
            "observed_max_f": d["observed_max_f"],
            "pnl": t["pnl"],
            "insurance_covers_book": t.get("insurance_covers_book", False),
        })

    edge_curve = edge_sensitivity_curve(
        days,
        cap=rec.get("max_entry_yes_ask", 0.35),
        insurance_enabled=rec.get("insurance_enabled", True),
        insurance_mode=rec.get("insurance_mode", "fraction"),
        insurance_budget_fraction=rec.get("insurance_budget_fraction", 0.25),
    )

    out: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "source_sweep": str(sweep_file.resolve()),
        "recommended_policy": rec,
        "loss_taxonomy": dict(loss_labels),
        "loss_days": loss_days,
        "edge_sensitivity_cap_035": edge_curve,
        "forecast_days": len(days),
        "scored_trades": cfg["n_trades"],
    }

    out_path = None
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = output_dir / f"policy_pattern_analysis_{stamp}.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        out["output_path"] = str(out_path)

    return out


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Kalshi policy loss taxonomy + edge sensitivity")
    p.add_argument("--sweep-json", type=Path, default=None)
    p.add_argument("--backtest-dir", type=Path, default=None)
    p.add_argument("--price-history-dir", type=Path, default=None)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    from kmia_kalshi_paths import console2_backtest_dir

    result = run_analysis(
        sweep_path=args.sweep_json,
        backtest_dir=args.backtest_dir,
        price_history_dir=args.price_history_dir,
        output_dir=args.output_dir or console2_backtest_dir(),
    )
    print(json.dumps({
        "loss_taxonomy": result["loss_taxonomy"],
        "scored_trades": result["scored_trades"],
        "output_path": result.get("output_path"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
