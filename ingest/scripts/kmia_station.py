"""Canonical KMIA station pin — single source for Console 2 ingest and backtests.

Must stay aligned with Kalshi ``backend/src/shared/kmia_station.py``.

NWS MapClick / settlement reference:
https://forecast.weather.gov/MapClick.php?lat=25.7906&lon=-80.3164
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "kmia_station.json"

STATION_ID = "KMIA"
KMIA_LAT = 25.7906
KMIA_LON = -80.3164
KMIA_LON_360 = 279.6836
NWS_GRID_ID = "MFL"
NWS_GRID_X = 105
NWS_GRID_Y = 51
NWS_GRID_URL_SUFFIX = f"{NWS_GRID_ID}/{NWS_GRID_X},{NWS_GRID_Y}"


def load_station_config() -> dict[str, Any]:
    if _CONFIG_PATH.is_file():
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "station_id": STATION_ID,
        "lat": KMIA_LAT,
        "lon": KMIA_LON,
        "lon_360": KMIA_LON_360,
        "nws_grid_id": NWS_GRID_ID,
        "nws_grid_x": NWS_GRID_X,
        "nws_grid_y": NWS_GRID_Y,
    }


def nws_points_url() -> str:
    return f"https://api.weather.gov/points/{KMIA_LAT},{KMIA_LON}"


def nws_daily_forecast_url() -> str:
    return f"https://api.weather.gov/gridpoints/{NWS_GRID_URL_SUFFIX}/forecast"


def nws_hourly_forecast_url() -> str:
    return f"https://api.weather.gov/gridpoints/{NWS_GRID_URL_SUFFIX}/forecast/hourly"
