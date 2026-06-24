"""Forecast stability classification (golden-master thresholds).

Shared by Console 2 accuracy analysis and Kalshi live paper (mirrored logic).
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence


def classify_stability_from_metrics(
    forecast_range_f: float,
    forecast_std_f: float,
    first_to_latest_change_f: float,
) -> str:
    """Classify intraday forecast stability from range/std/drift metrics."""
    if forecast_range_f is None or math.isnan(float(forecast_range_f)):
        return "NO DATA"
    r = float(forecast_range_f)
    std = float(forecast_std_f or 0.0)
    delta = abs(float(first_to_latest_change_f or 0.0))
    if r <= 1.5 and std <= 0.75 and delta <= 1.0:
        return "STABLE"
    if r <= 3.0 and std <= 1.5 and delta <= 2.0:
        return "MIXED"
    return "UNSTABLE"


def stability_metrics_from_highs(highs: Sequence[float]) -> dict[str, Any]:
    """Compute stability metrics from a time-ordered series of forecast highs (°F)."""
    vals = [float(h) for h in highs if h is not None]
    if not vals:
        return {
            "n_samples": 0,
            "min_forecast_f": None,
            "max_forecast_f": None,
            "forecast_range_f": None,
            "forecast_std_f": None,
            "first_to_latest_change_f": None,
            "forecast_stability": "NO DATA",
        }
    n = len(vals)
    mn = min(vals)
    mx = max(vals)
    rng = mx - mn
    if n >= 2:
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / (n - 1)
        std = math.sqrt(var)
    else:
        std = 0.0
    delta = vals[-1] - vals[0]
    stability = classify_stability_from_metrics(rng, std, delta)
    return {
        "n_samples": n,
        "min_forecast_f": round(mn, 2),
        "max_forecast_f": round(mx, 2),
        "forecast_range_f": round(rng, 4),
        "forecast_std_f": round(std, 4),
        "first_to_latest_change_f": round(delta, 4),
        "forecast_stability": stability,
    }


def classify_stability_row(row: Any) -> str:
    """Pandas-row adapter for analyze_kmia_forecast_accuracy."""
    return classify_stability_from_metrics(
        row["forecast_range_f"],
        row.get("forecast_std_f", 0.0),
        abs(row["first_to_latest_change_f"]),
    )
