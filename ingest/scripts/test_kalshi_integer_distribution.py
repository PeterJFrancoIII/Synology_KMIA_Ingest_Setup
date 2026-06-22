#!/usr/bin/env python3
"""Tests for integer_dist_v1 backtest probability model."""

from __future__ import annotations

import os
import unittest

from kalshi_integer_distribution import (
    build_integer_distribution,
    model_probs_for_market_bins_integer,
    prob_for_market_bin_from_integer_dist,
)
from kalshi_price_history_loader import model_prob_for_market_bin, model_probs_for_market_bins


class TestKalshiIntegerDistribution(unittest.TestCase):
    def test_build_integer_distribution_sums_to_one(self):
        dist = build_integer_distribution(84)
        self.assertAlmostEqual(sum(dist.values()), 1.0, places=4)
        self.assertGreater(dist.get(84, 0), 0.1)

    def test_prob_for_market_bin_range(self):
        dist = build_integer_distribution(84)
        p = prob_for_market_bin_from_integer_dist(dist, "83-84")
        self.assertGreater(p, 0.2)

    def test_integer_vs_gaussian_close_for_center_bin(self):
        bins = ["81-82", "83-84", "85-86"]
        forecast = 84.0
        g = model_probs_for_market_bins(forecast, bins)
        i = model_probs_for_market_bins_integer(forecast, bins)
        for b in bins:
            self.assertAlmostEqual(g[b], i[b], delta=0.02, msg=b)

    def test_active_prob_model_env(self):
        os.environ["KALSHI_BACKTEST_PROB_MODEL"] = "integer_dist_v1"
        from kalshi_integer_distribution import active_prob_model, use_integer_dist_model

        self.assertTrue(use_integer_dist_model())
        self.assertEqual(active_prob_model(), "integer_dist_v1")
        del os.environ["KALSHI_BACKTEST_PROB_MODEL"]


if __name__ == "__main__":
    unittest.main()
