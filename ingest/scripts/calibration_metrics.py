"""Probability calibration metrics for Console 2 policy gates."""

from __future__ import annotations

import math
from typing import Any, Optional


def brier_score_multiclass(probability_bins: dict[str, float], actual_bin: str) -> float:
    score = 0.0
    for b, prob in probability_bins.items():
        actual = 1.0 if b == actual_bin else 0.0
        score += (prob - actual) ** 2
    return score


def crps_multiclass(probability_bins: dict[str, float], actual_bin: str) -> float:
    bins = sorted(probability_bins.keys())
    score = 0.0
    cumulative_p = 0.0
    cumulative_y = 0.0
    for b in bins:
        cumulative_p += probability_bins.get(b, 0.0)
        cumulative_y += 1.0 if b == actual_bin else 0.0
        score += (cumulative_p - cumulative_y) ** 2
    return score


def reliability_table(
    rows: list[dict[str, Any]],
    *,
    prob_key: str = "model_probability",
    outcome_key: str = "won",
    n_buckets: int = 10,
) -> list[dict[str, Any]]:
    buckets: dict[int, list[tuple[float, int]]] = {i: [] for i in range(n_buckets)}
    for r in rows:
        p = r.get(prob_key)
        y = r.get(outcome_key)
        if p is None or y is None:
            continue
        dec = min(n_buckets - 1, max(0, int(float(p) * n_buckets)))
        buckets[dec].append((float(p), int(y)))
    out = []
    for dec in range(n_buckets):
        pairs = buckets[dec]
        if not pairs:
            continue
        mean_p = sum(p for p, _ in pairs) / len(pairs)
        hit = sum(w for _, w in pairs) / len(pairs)
        out.append({
            "bucket": dec,
            "n": len(pairs),
            "mean_predicted": round(mean_p, 4),
            "observed_rate": round(hit, 4),
            "gap": round(abs(mean_p - hit), 4),
        })
    return out


def expected_calibration_error(reliability: list[dict[str, Any]]) -> float:
    if not reliability:
        return 0.0
    total = sum(r["n"] for r in reliability)
    if total == 0:
        return 0.0
    return round(
        sum(r["n"] * abs(r["mean_predicted"] - r["observed_rate"]) for r in reliability) / total,
        4,
    )
