#!/usr/bin/env python3
"""DEPRECATED — simulated weather backfill is forbidden.

Use:
  ingest/scripts/kalshi_weather_coverage_scorecard.py  (read-only coverage)
  ingest/scripts/purge_simulated_weather.py            (remove bad artifacts)

Policy: .cursor/rules/no-simulated-weather-data.mdc
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "ERROR: backfill_kalshi_nws_ncei.py is disabled.\n"
        "Rule: no simulated or backfilled forecast/observed weather data.\n"
        "Use kalshi_weather_coverage_scorecard.py (report) or purge_simulated_weather.py (cleanup).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
