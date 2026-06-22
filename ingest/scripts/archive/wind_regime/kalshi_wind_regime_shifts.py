#!/usr/bin/env python3
"""KMIA wind-direction regime shifts for Console 2 backtests.

Mirrors Kalshi ``weather/kmia_wind_regime.py`` without cross-repo imports.
Shift magnitudes are season-stratified °F deltas vs cool_stable baseline from
``accuracy_points_enriched.csv`` (2020–2025 all-years daily max).

NO REAL TRADING — research probability adjustment only.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

HOT_UNSTABLE_DIRS = frozenset({"W", "NW", "N", "WNW"})
WARM_MIXED_DIRS = frozenset({"SW", "WSW"})
COOL_STABLE_DIRS = frozenset({"S", "SE", "E", "NE", "ESE", "SSE", "ENE", "SSW", "NNE"})

_EMBEDDED_SHIFT_F: dict[str, dict[str, float]] = {
    "DJF": {"hot_unstable": -5.25, "warm_mixed": 2.23, "cool_stable": 0.0},
    "MAM": {"hot_unstable": 1.75, "warm_mixed": 4.82, "cool_stable": 0.0},
    "JJA": {"hot_unstable": 1.55, "warm_mixed": 0.96, "cool_stable": 0.0},
    "SON": {"hot_unstable": -0.74, "warm_mixed": 1.57, "cool_stable": 0.0},
}


def regime_from_cardinal(wind_compass: Optional[str]) -> str:
    direction = (wind_compass or "").strip().upper()
    if direction in HOT_UNSTABLE_DIRS:
        return "hot_unstable"
    if direction in WARM_MIXED_DIRS:
        return "warm_mixed"
    if direction in COOL_STABLE_DIRS:
        return "cool_stable"
    return "unknown"


def month_to_season(month: Optional[int]) -> str:
    if month is None:
        return "JJA"
    if month in (12, 1, 2):
        return "DJF"
    if month in (3, 4, 5):
        return "MAM"
    if month in (6, 7, 8):
        return "JJA"
    if month in (9, 10, 11):
        return "SON"
    return "JJA"


def season_from_date(date_et: str) -> str:
    try:
        month = datetime.strptime(date_et[:10], "%Y-%m-%d").month
    except ValueError:
        month = None
    return month_to_season(month)


def load_wind_regime_priors(path: Optional[Path] = None) -> dict[str, Any]:
    """Load wind_regime_shifts from mae_priors.json when available."""
    if path is None:
        from kmia_kalshi_paths import kalshi_research_dir

        path = kalshi_research_dir() / "mae" / "mae_priors.json"
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def resolve_wind_regime_shift_f(
    regime: str,
    *,
    month: Optional[int] = None,
    season: Optional[str] = None,
    priors: Optional[dict[str, Any]] = None,
    jja_only: bool = False,
) -> float:
    """Historical °F adjustment vs cool_stable baseline for season + regime."""
    if regime in ("unknown", "cool_stable", "", None):
        return 0.0

    resolved_season = season or month_to_season(month)
    if jja_only and resolved_season != "JJA":
        return 0.0

    if priors:
        by_season = (priors.get("wind_regime_shifts") or {}).get("by_season", {})
        block = by_season.get(resolved_season, {})
        entry = block.get(regime)
        if isinstance(entry, dict) and entry.get("delta_obs_max_vs_cool_stable_f") is not None:
            return float(entry["delta_obs_max_vs_cool_stable_f"])

    return float(_EMBEDDED_SHIFT_F.get(resolved_season, {}).get(regime, 0.0))


def wind_shift_for_cardinal(
    wind_compass: Optional[str],
    *,
    settlement_date_et: str,
    priors: Optional[dict[str, Any]] = None,
    jja_only: bool = False,
) -> dict[str, Any]:
    """Resolve regime + shift for a compass direction on a settlement day."""
    regime = regime_from_cardinal(wind_compass)
    season = season_from_date(settlement_date_et)
    month = None
    try:
        month = datetime.strptime(settlement_date_et[:10], "%Y-%m-%d").month
    except ValueError:
        pass
    shift_f = resolve_wind_regime_shift_f(
        regime,
        month=month,
        season=season,
        priors=priors,
        jja_only=jja_only,
    )
    return {
        "wind_direction_compass": (wind_compass or "").strip().upper() or None,
        "regime": regime,
        "season": season,
        "wind_shift_f": round(shift_f, 4),
    }
