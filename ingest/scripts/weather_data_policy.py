"""Weather data authenticity policy — no simulated forecast or observed records.

Console 2 and Kalshi backtest joins must use only live-captured or officially
sourced weather artifacts. Synthetic, backfilled, proxy, or model-replay rows
are rejected at load time.

NWS forecast snapshots must match the canonical KMIA MapClick grid (MFL/105,51).

NO REAL TRADING — data integrity guard only.
"""

from __future__ import annotations

from typing import Any

from kmia_station import KMIA_LAT, KMIA_LON, NWS_GRID_URL_SUFFIX

# Forecast snapshot sources that are never acceptable in weather sets.
_BLOCKED_FORECAST_SOURCES = frozenset({
    "iem_mos_gfs_backfill",
    "synthetic",
    "simulated",
    "proxy",
})

# Observed row providers injected by backfill scripts (not live NWS archive).
_BLOCKED_OBSERVED_PROVIDERS = frozenset({
    "ncei",
    "iem_asos",
    "synthetic",
    "simulated",
    "proxy",
})


def is_aligned_nws_snapshot(data: dict[str, Any]) -> bool:
    """True when snapshot forecast grid matches canonical KMIA MapClick pin."""
    url = str(data.get("api_daily_forecast_url") or "")
    if NWS_GRID_URL_SUFFIX.replace(",", "%2C") in url or NWS_GRID_URL_SUFFIX in url:
        return True
    pin_lat = data.get("forecast_pin_lat")
    pin_lon = data.get("forecast_pin_lon")
    if pin_lat is not None and pin_lon is not None:
        return (
            abs(float(pin_lat) - KMIA_LAT) < 0.001
            and abs(float(pin_lon) - KMIA_LON) < 0.001
        )
    # Legacy snapshots without grid metadata — reject (wrong pin era).
    return False


def is_simulated_nws_snapshot(data: dict[str, Any]) -> bool:
    """True when an NWS snapshot JSON was synthesized or backfilled."""
    if data.get("backfill") or data.get("simulated") or data.get("synthetic"):
        return True
    if data.get("backfill_method"):
        return True
    source = str(data.get("source") or "").lower()
    if any(token in source for token in ("backfill", "synthetic", "simulated", "iem_mos", "proxy")):
        return True
    warnings = data.get("warnings") or []
    for w in warnings:
        if isinstance(w, str) and "synthetic snapshot" in w.lower():
            return True
    return False


def is_usable_nws_snapshot(data: dict[str, Any]) -> bool:
    """Live-archived or NDFD point-archived NWS snapshot on the canonical KMIA forecast grid."""
    return not is_simulated_nws_snapshot(data) and is_aligned_nws_snapshot(data)


def is_ndfd_point_archival_snapshot(data: dict[str, Any]) -> bool:
    return str(data.get("source") or "") == "noaa_ndfd_point_archive"


def is_simulated_observed_row(row: dict[str, Any]) -> bool:
    """True when an observed JSONL row was injected rather than live-archived."""
    if row.get("backfill") or row.get("simulated") or row.get("synthetic"):
        return True
    if row.get("settlement_row"):
        return True
    provider = str(row.get("provider") or "").lower()
    if provider in _BLOCKED_OBSERVED_PROVIDERS:
        return True
    source = str(row.get("source") or "").lower()
    if any(token in source for token in ("backfill", "synthetic", "simulated", "iem_", "proxy")):
        return True
    return False
