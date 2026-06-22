#!/usr/bin/env python3
"""Compare gaussian_v1 vs integer_dist_v1 P(bin) for backtest diagnostics.

NO REAL TRADING — research only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from kalshi_integer_distribution import (
    GAUSSIAN_MODEL,
    INTEGER_DIST_MODEL,
    model_probs_for_market_bins_integer,
)
from kalshi_price_history_loader import (
    discover_price_history_files,
    load_price_history_csv,
    model_probs_for_market_bins,
    prices_at_anchor,
)


def compare_day(
    forecast_temp_f: float,
    market_bins: list[str],
) -> dict[str, Any]:
    gauss = model_probs_for_market_bins(forecast_temp_f, market_bins)
    integer = model_probs_for_market_bins_integer(forecast_temp_f, market_bins)
    deltas = {
        b: round(abs(gauss.get(b, 0) - integer.get(b, 0)), 4)
        for b in market_bins
    }
    forecast_bin = max(gauss, key=gauss.get) if gauss else None
    return {
        "forecast_temp_f": forecast_temp_f,
        "market_bins": market_bins,
        "gaussian_v1": gauss,
        "integer_dist_v1": integer,
        "abs_delta_by_bin": deltas,
        "max_abs_delta": max(deltas.values()) if deltas else 0.0,
        "forecast_bin_gaussian": forecast_bin,
        "forecast_bin_integer": max(integer, key=integer.get) if integer else None,
    }


def run_comparison(
    price_history_dir: Path,
    *,
    sample_forecasts: Optional[list[float]] = None,
) -> dict[str, Any]:
    price_history_dir = Path(price_history_dir)
    rows: list[dict[str, Any]] = []
    max_delta = 0.0
    forecasts = sample_forecasts or [78.0, 81.0, 84.0, 87.0, 90.0]

    for day, path in sorted(discover_price_history_files(price_history_dir).items()):
        df, column_map = load_price_history_csv(path)
        snap = prices_at_anchor(df, day, column_map=column_map)
        if not snap.get("found"):
            continue
        bins = snap.get("market_bins") or list(column_map.values())
        for ft in forecasts:
            row = compare_day(ft, bins)
            row["settlement_date"] = day
            rows.append(row)
            max_delta = max(max_delta, row["max_abs_delta"])

    mismatched_bins = sum(
        1 for r in rows
        if r.get("forecast_bin_gaussian") != r.get("forecast_bin_integer")
    )
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gaussian_model": GAUSSIAN_MODEL,
        "integer_model": INTEGER_DIST_MODEL,
        "price_history_dir": str(price_history_dir.resolve()),
        "n_comparisons": len(rows),
        "max_abs_delta": round(max_delta, 4),
        "n_forecast_bin_mismatches": mismatched_bins,
        "sample_rows": rows[:30],
        "recommendation": (
            "Models align within 2pp for typical bins; safe to opt in via "
            "KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1 when validating policy."
            if max_delta <= 0.05
            else "Material deltas detected — review sample_rows before switching default."
        ),
    }


def main(argv: Optional[list[str]] = None) -> int:
    from kmia_kalshi_paths import kalshi_price_history_dir

    parser = argparse.ArgumentParser(description="Compare backtest probability models")
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    price_dir = args.price_history_dir or kalshi_price_history_dir()
    report = run_comparison(price_dir)
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    print(
        f"\nSummary: max |ΔP|={report['max_abs_delta']}, "
        f"bin mismatches={report['n_forecast_bin_mismatches']}/{report['n_comparisons']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
