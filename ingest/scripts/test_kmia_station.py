#!/usr/bin/env python3
import unittest

from kmia_station import (
    KMIA_LAT,
    KMIA_LON,
    NWS_GRID_URL_SUFFIX,
    nws_daily_forecast_url,
    nws_points_url,
)


class KmiaStationTest(unittest.TestCase):
    def test_canonical_pin(self):
        self.assertEqual(KMIA_LAT, 25.7906)
        self.assertEqual(KMIA_LON, -80.3164)
        self.assertEqual(NWS_GRID_URL_SUFFIX, "MFL/105,51")
        self.assertIn("25.7906", nws_points_url())
        self.assertIn("MFL/105,51", nws_daily_forecast_url())


if __name__ == "__main__":
    unittest.main()
