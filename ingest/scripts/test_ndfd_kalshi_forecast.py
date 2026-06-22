#!/usr/bin/env python3
"""Tests for NDFD Kalshi anchor forecast join."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ndfd_kalshi_forecast import (
    build_ndfd_nws_snapshot,
    ndfd_forecast_high_at_anchor,
)
from weather_data_policy import is_ndfd_point_archival_snapshot, is_usable_nws_snapshot


class NdfdKalshiForecastTest(unittest.TestCase):
    def _write_csv(self, path: Path) -> None:
        rows = [
            {
                "requested_subcategory": "maxt",
                "station_lat": 25.7906,
                "station_lon": -80.3164,
                "grib_ref_time_utc": "2026-04-19T14:00:00Z",
                "valid_time_utc": "2026-04-20T18:00:00Z",
                "value_f": 86.0,
                "local_path": "/tmp/a.grib2",
            },
            {
                "requested_subcategory": "maxt",
                "station_lat": 25.7906,
                "station_lon": -80.3164,
                "grib_ref_time_utc": "2026-04-19T14:00:00Z",
                "valid_time_utc": "2026-04-20T22:00:00Z",
                "value_f": 88.0,
                "local_path": "/tmp/a.grib2",
            },
        ]
        pd.DataFrame(rows).to_csv(path, index=False)

    def test_anchor_picks_daytime_max(self):
        with tempfile.TemporaryDirectory() as td:
            csv = Path(td) / "maxt.csv"
            self._write_csv(csv)
            fc = ndfd_forecast_high_at_anchor(csv, "2026-04-20")
            self.assertTrue(fc.get("found"))
            self.assertEqual(fc["forecast_temp_f"], 88.0)
            self.assertEqual(fc["source"], "noaa_ndfd_point_archive")

    def test_snapshot_passes_policy(self):
        from datetime import datetime, timezone

        snap = build_ndfd_nws_snapshot(
            "2026-04-20",
            high_f=88.0,
            release_time_utc=datetime(2026, 4, 19, 14, 0, tzinfo=timezone.utc),
        )
        self.assertTrue(is_usable_nws_snapshot(snap))
        self.assertTrue(is_ndfd_point_archival_snapshot(snap))


if __name__ == "__main__":
    unittest.main()
