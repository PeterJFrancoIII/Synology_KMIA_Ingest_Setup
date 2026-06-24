#!/usr/bin/env python3
"""Integer-temperature probability model aligned with Kalshi live (integer_dist_v1).

Ports core logic from Kalshi ``forecasting/distribution_utils.py`` without
cross-repo imports. Use via ``KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1``.

NO REAL TRADING — research probability model only.
"""

from __future__ import annotations

import math
import os
from typing import Optional

INTEGER_DIST_MODEL = "integer_dist_v1"
GAUSSIAN_MODEL = "gaussian_v1_truncation_optional"
DEFAULT_STD_F = 2.2
DEFAULT_TEMP_RANGE = (60, 105)


def std_f_from_nbm_band(p10_f: float, p90_f: float) -> float:
    """Approximate Gaussian std from NBM p10–p90 band (80% interval)."""
    width = max(0.5, float(p90_f) - float(p10_f))
    return round(width / 2.56, 2)


def active_prob_model() -> str:
    return os.environ.get("KALSHI_BACKTEST_PROB_MODEL", GAUSSIAN_MODEL).strip().lower()


def use_integer_dist_model() -> bool:
    return active_prob_model() in (INTEGER_DIST_MODEL, "integer_dist", "integer")


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def build_integer_distribution(
    center_f: int,
    *,
    std_f: float = DEFAULT_STD_F,
    temp_range: tuple[int, int] = DEFAULT_TEMP_RANGE,
) -> dict[int, float]:
    """Discrete N(center, std) over integer °F buckets (live paper loop default)."""
    lo, hi = temp_range
    probs: dict[int, float] = {}
    for t in range(lo, hi + 1):
        z_low = (t - 0.5 - center_f) / std_f
        z_high = (t + 0.5 - center_f) / std_f
        p = _normal_cdf(z_high) - _normal_cdf(z_low)
        if p > 1e-8:
            probs[t] = p
    total = sum(probs.values())
    if total <= 0:
        return {}
    return {t: round(p / total, 6) for t, p in probs.items()}


def zero_impossible_temps(
    probs: dict[int, float],
    observed_min_f: int,
) -> dict[int, float]:
    zeroed = {t: (0.0 if t < observed_min_f else p) for t, p in probs.items()}
    total = sum(zeroed.values())
    if total <= 0:
        return {t: 0.0 for t in zeroed}
    return {t: round(p / total, 6) for t, p in zeroed.items()}


def normalize_probability_mass(probs: dict[int, float]) -> dict[int, float]:
    total = sum(probs.values())
    if total <= 0:
        return {t: 0.0 for t in probs}
    return {t: round(p / total, 6) for t, p in probs.items()}


def shift_distribution_fractional(probs: dict[int, float], shift_f: float) -> dict[int, float]:
    """Shift integer mass by fractional °F (linear interpolation between buckets)."""
    if shift_f == 0:
        return probs

    new_probs: dict[int, float] = {}
    s_int = math.floor(shift_f)
    s_frac = shift_f - s_int

    for t, p in probs.items():
        t_low = t + s_int
        new_probs[t_low] = new_probs.get(t_low, 0.0) + (1.0 - s_frac) * p
        if s_frac > 0:
            t_high = t + s_int + 1
            new_probs[t_high] = new_probs.get(t_high, 0.0) + s_frac * p

    return normalize_probability_mass(new_probs)


def _market_bin_int_range(bin_label: str) -> tuple[int, int]:
    if bin_label.startswith("<="):
        return 60, int(bin_label[2:])
    if bin_label.startswith(">="):
        return int(bin_label[2:]), 105
    if "-" in bin_label:
        lo, hi = bin_label.split("-", 1)
        return int(lo), int(hi)
    val = int(bin_label)
    return val, val


def prob_for_market_bin_from_integer_dist(
    integer_probs: dict[int, float],
    market_bin: str,
) -> float:
    lo, hi = _market_bin_int_range(market_bin)
    mass = sum(p for t, p in integer_probs.items() if lo <= t <= hi)
    return round(max(0.0, min(1.0, mass)), 4)


def model_probs_for_market_bins_integer(
    forecast_temp_f: float,
    market_bins: list[str],
    *,
    observed_max_so_far_f: Optional[float] = None,
    std_f: float = DEFAULT_STD_F,
    wind_shift_f: float = 0.0,
) -> dict[str, float]:
    center = int(round(forecast_temp_f))
    probs = build_integer_distribution(center, std_f=std_f)
    if wind_shift_f:
        probs = shift_distribution_fractional(probs, float(wind_shift_f))
    if observed_max_so_far_f is not None:
        probs = zero_impossible_temps(probs, math.ceil(observed_max_so_far_f))
    if not probs:
        return {b: 0.0 for b in market_bins}
    raw = {
        b: prob_for_market_bin_from_integer_dist(probs, b)
        for b in market_bins
    }
    total = sum(raw.values())
    if total <= 0:
        return {b: 0.0 for b in market_bins}
    return {b: round(v / total, 4) for b, v in raw.items()}
