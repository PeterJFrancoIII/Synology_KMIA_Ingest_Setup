#!/usr/bin/env python3
"""Tests for IEM NWS zone forecast parser."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from nws_iem_zone_parser import (
    parse_zone_daytime_high,
    phrase_to_high_f,
    pick_product_before_anchor,
    settlement_weekday_period,
    split_iem_products,
)


SAMPLE_FLZ173 = """
FLZ173-200200-
Coastal Miami Dade County-
Including the city of Miami
222 PM EDT Sun Apr 19 2026

.TONIGHT...Mostly cloudy. Lows in the lower 70s.
.MONDAY...Partly sunny. Highs in the lower 80s. Northeast winds 10 to 15 mph.
.MONDAY NIGHT...Mostly cloudy. Lows around 70.
.TUESDAY...Mostly sunny. Highs in the upper 70s.
$$"""


class NwsIemZoneParserTest(unittest.TestCase):
    def test_phrase_mapping(self):
        self.assertEqual(phrase_to_high_f("lower 80s"), 82)
        self.assertEqual(phrase_to_high_f("upper 70s"), 78)
        self.assertEqual(phrase_to_high_f("around 80"), 80)

    def test_parse_monday_high(self):
        high = parse_zone_daytime_high(SAMPLE_FLZ173, "2026-04-20")
        self.assertEqual(high, 82)

    def test_settlement_weekday(self):
        self.assertEqual(settlement_weekday_period("2026-04-20"), "MONDAY")

    def test_pick_product_before_anchor(self):
        products = split_iem_products(
            "FPUS52 KMFL 181822\n" + SAMPLE_FLZ173 + "\nFPUS52 KMFL 191400\n" + SAMPLE_FLZ173
        )
        anchor = datetime(2026, 4, 19, 14, 0, tzinfo=timezone.utc)
        picked = pick_product_before_anchor(products, anchor)
        self.assertIsNotNone(picked)
        issued, _ = picked  # type: ignore[misc]
        self.assertEqual(issued.day, 19)
        self.assertEqual(issued.hour, 14)


if __name__ == "__main__":
    unittest.main()
