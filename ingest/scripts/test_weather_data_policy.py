#!/usr/bin/env python3
"""Tests for no-simulated-weather policy and purge helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from kalshi_nws_join import load_observed_daily_maxes, nws_forecast_high_at_anchor
from purge_simulated_weather import purge_simulated_weather
from weather_data_policy import (
    is_aligned_nws_snapshot,
    is_ndfd_point_archival_snapshot,
    is_simulated_nws_snapshot,
    is_simulated_observed_row,
    is_usable_nws_snapshot,
)


class WeatherDataPolicyTest(unittest.TestCase):
    def test_detects_mos_backfill_snapshot(self):
        snap = {
            "backfill": True,
            "source": "iem_mos_gfs_backfill",
            "daily_forecast": [{"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 81}],
        }
        self.assertTrue(is_simulated_nws_snapshot(snap))

    def test_allows_live_nws_snapshot(self):
        snap = {
            "source": "api.weather.gov",
            "fetched_at_utc": "2026-05-11T04:46:30+00:00",
            "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/105,51/forecast",
            "forecast_pin_lat": 25.7906,
            "forecast_pin_lon": -80.3164,
            "daily_forecast": [],
        }
        self.assertFalse(is_simulated_nws_snapshot(snap))
        self.assertTrue(is_aligned_nws_snapshot(snap))
        self.assertTrue(is_usable_nws_snapshot(snap))

    def test_allows_iem_afos_archival_snapshot(self):
        snap = {
            "source": "nws_iem_afos_archive",
            "fetched_at_utc": "2026-04-19T14:00:00+00:00",
            "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/105,51/forecast",
            "forecast_pin_lat": 25.7906,
            "forecast_pin_lon": -80.3164,
            "daily_forecast": [
                {"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 82}
            ],
        }
        self.assertFalse(is_simulated_nws_snapshot(snap))
        self.assertTrue(is_usable_nws_snapshot(snap))

    def test_allows_ndfd_point_archival_snapshot(self):
        snap = {
            "source": "noaa_ndfd_point_archive",
            "fetched_at_utc": "2026-04-19T14:00:00+00:00",
            "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/105,51/forecast",
            "forecast_pin_lat": 25.7906,
            "forecast_pin_lon": -80.3164,
            "daily_forecast": [
                {"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 86}
            ],
        }
        self.assertFalse(is_simulated_nws_snapshot(snap))
        self.assertTrue(is_usable_nws_snapshot(snap))
        self.assertTrue(is_ndfd_point_archival_snapshot(snap))

    def test_rejects_wrong_grid_snapshot(self):
        snap = {
            "source": "api.weather.gov",
            "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/106,51/forecast",
            "daily_forecast": [],
        }
        self.assertFalse(is_aligned_nws_snapshot(snap))
        self.assertFalse(is_usable_nws_snapshot(snap))

    def test_detects_injected_observed_row(self):
        row = {
            "provider": "ncei",
            "date_et": "2026-04-20",
            "temperature_f": 86.0,
            "backfill": True,
            "settlement_row": True,
        }
        self.assertTrue(is_simulated_observed_row(row))

    def test_allows_live_archived_observed_row(self):
        row = {
            "provider": "nws",
            "date_et": "2026-05-07",
            "temperature_f": 82.4,
            "timestamp_utc": "2026-05-08T00:25:00+00:00",
        }
        self.assertFalse(is_simulated_observed_row(row))

    def test_join_skips_wrong_grid_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            nws_dir = Path(tmp)
            anchor = datetime(2026, 4, 19, 14, 0, tzinfo=timezone.utc)
            bad = {
                "fetched_at_utc": (anchor - timedelta(minutes=5)).isoformat(),
                "source": "api.weather.gov",
                "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/106,51/forecast",
                "daily_forecast": [
                    {"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 81}
                ],
            }
            (nws_dir / "nws_kmia_snapshot_2026-04-19_095500.json").write_text(json.dumps(bad))
            result = nws_forecast_high_at_anchor(nws_dir, "2026-04-20")
            self.assertFalse(result["found"])

    def test_join_accepts_canonical_grid_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            nws_dir = Path(tmp)
            anchor = datetime(2026, 4, 19, 14, 0, tzinfo=timezone.utc)
            good = {
                "fetched_at_utc": (anchor - timedelta(minutes=5)).isoformat(),
                "source": "api.weather.gov",
                "api_daily_forecast_url": "https://api.weather.gov/gridpoints/MFL/105,51/forecast",
                "daily_forecast": [
                    {"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 93}
                ],
            }
            (nws_dir / "nws_kmia_snapshot_2026-04-19_095500.json").write_text(json.dumps(good))
            result = nws_forecast_high_at_anchor(nws_dir, "2026-04-20")
            self.assertTrue(result["found"])
            self.assertEqual(result["forecast_temp_f"], 93.0)

    def test_join_skips_simulated_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            nws_dir = Path(tmp)
            anchor = datetime(2026, 4, 19, 14, 0, tzinfo=timezone.utc)
            bad = {
                "fetched_at_utc": (anchor - timedelta(minutes=5)).isoformat(),
                "backfill": True,
                "source": "iem_mos_gfs_backfill",
                "daily_forecast": [
                    {"forecast_date_et": "2026-04-20", "isDaytime": True, "temperature_f": 81}
                ],
            }
            (nws_dir / "nws_kmia_snapshot_2026-04-19_095500.json").write_text(json.dumps(bad))
            result = nws_forecast_high_at_anchor(nws_dir, "2026-04-20")
            self.assertFalse(result["found"])

    def test_load_observed_skips_injected_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            jsonl = Path(tmp) / "obs.jsonl"
            rows = [
                {"provider": "nws", "date_et": "2026-05-07", "temperature_f": 82.0,
                 "timestamp_utc": "2026-05-08T00:25:00+00:00"},
                {"provider": "ncei", "date_et": "2026-04-20", "temperature_f": 86.0,
                 "backfill": True, "settlement_row": True},
            ]
            jsonl.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            out = load_observed_daily_maxes(jsonl)
            self.assertIn("2026-05-07", out)
            self.assertNotIn("2026-04-20", out)

    def test_purge_removes_simulated_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            nws_dir = Path(tmp) / "nws"
            nws_dir.mkdir()
            jsonl = nws_dir / "nws_observed_history.jsonl"
            bad_snap = nws_dir / "nws_kmia_snapshot_2026-04-19_095500.json"
            bad_snap.write_text(json.dumps({"backfill": True, "source": "iem_mos_gfs_backfill"}))
            jsonl.write_text(
                json.dumps({"provider": "ncei", "date_et": "2026-04-20", "temperature_f": 86,
                            "backfill": True, "settlement_row": True}) + "\n"
                + json.dumps({"provider": "nws", "date_et": "2026-05-07", "temperature_f": 82,
                              "timestamp_utc": "2026-05-08T00:25:00+00:00"}) + "\n"
            )
            result = purge_simulated_weather(nws_dir=nws_dir, observed_jsonl=jsonl)
            self.assertEqual(result["removed_snapshot_files"], 1)
            self.assertEqual(result["removed_observed_rows"], 1)
            self.assertEqual(result["kept_observed_rows"], 1)
            self.assertFalse(bad_snap.exists())


if __name__ == "__main__":
    unittest.main()
