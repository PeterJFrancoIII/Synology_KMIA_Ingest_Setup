#!/usr/bin/env python3
"""Build canonical trading_policy.json manifest from optimizer recommendation.

NO REAL TRADING — Console 2 export for Console 3 file-only integration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from kalshi_integer_distribution import (
    GAUSSIAN_MODEL,
    INTEGER_DIST_MODEL,
    use_integer_dist_model,
)
from kalshi_price_history_loader import (
    ANCHOR_HOUR_ET,
    DEFAULT_INSURANCE_MODE,
    DEFAULT_ORDER_MODE,
    INSURANCE_BUDGET_FRACTION,
    INSURANCE_MODE_COVER_BOOK,
    INSURANCE_MODE_FRACTION,
    INSURANCE_PRICE_K,
    MAX_ENTRY_YES_ASK,
    MIN_FORECAST_EXECUTABLE_EDGE,
    MIN_INSURANCE_BIN_PROB,
)

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 POLICY EXPORT ONLY",
}

LOW_CONFIDENCE_MAX_FORECAST_DOLLARS = 5.0


def build_trading_policy_manifest(
    recommended: dict[str, Any],
    *,
    source_sweep: Optional[str] = None,
    approved_by_human: bool = False,
    order_mode: str = DEFAULT_ORDER_MODE,
) -> dict[str, Any]:
    """Canonical manifest consumed by Console 3 paper loop."""
    confidence = recommended.get("confidence", "low")
    backtest_model = INTEGER_DIST_MODEL if use_integer_dist_model() else GAUSSIAN_MODEL
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "schema_version": "1.0",
        "model_version": backtest_model,
        "live_model_version": INTEGER_DIST_MODEL,
        "order_mode": order_mode,
        "anchor_hour_et": ANCHOR_HOUR_ET,
        "trading_window_mode": "dynamic",
        "expected_max_hour_priors": "expected_max_hour_priors.json",
        "min_forecast_edge": recommended.get("min_forecast_edge", MIN_FORECAST_EXECUTABLE_EDGE),
        "max_entry_yes_ask": recommended.get("max_entry_yes_ask", MAX_ENTRY_YES_ASK),
        "require_cheapest_at_open": recommended.get("require_cheapest_at_open", True),
        "insurance_enabled": recommended.get("insurance_enabled", True),
        "insurance_mode": recommended.get("insurance_mode", DEFAULT_INSURANCE_MODE),
        "insurance_budget_fraction": recommended.get(
            "insurance_budget_fraction", INSURANCE_BUDGET_FRACTION
        ),
        "insurance_price_k": recommended.get("insurance_price_k", INSURANCE_PRICE_K),
        "min_insurance_bin_prob": MIN_INSURANCE_BIN_PROB,
        "confidence": confidence,
        "low_confidence_max_forecast_dollars": LOW_CONFIDENCE_MAX_FORECAST_DOLLARS,
        "avg_event_volume_usd": 121_000.0,
        "max_top_of_book_participation": 0.25,
        "max_event_volume_participation": 0.005,
        "abs_max_contracts_per_leg": 25,
        "approved_by_human": approved_by_human,
        "source_sweep": source_sweep,
        "selection_method": recommended.get("selection_method"),
        "backtest_metrics": {
            "n_trades": recommended.get("n_trades"),
            "n_wins": recommended.get("n_wins"),
            "win_rate_pct": recommended.get("win_rate_pct"),
            "total_pnl": recommended.get("total_pnl"),
            "roi_pct": recommended.get("roi_pct"),
            "avg_insurance_legs": recommended.get("avg_insurance_legs"),
            "insurance_covers_book_rate_pct": recommended.get(
                "insurance_covers_book_rate_pct"
            ),
        },
    }
