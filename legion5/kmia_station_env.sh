#!/usr/bin/env bash
# Canonical KMIA MapClick pin — source from Legion5 launchers after kmia_legion5_env.sh.
# Must match ingest/config/kmia_station.json and ingest/scripts/kmia_station.py

export KMIA_STATION_ID="${KMIA_STATION_ID:-KMIA}"
export KMIA_LAT="${KMIA_LAT:-25.7906}"
export KMIA_LON="${KMIA_LON:--80.3164}"
export NWS_GRID_ID="${NWS_GRID_ID:-MFL}"
export NWS_GRID_X="${NWS_GRID_X:-105}"
export NWS_GRID_Y="${NWS_GRID_Y:-51}"
