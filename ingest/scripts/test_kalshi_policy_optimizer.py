#!/usr/bin/env python3
"""Tests for Kalshi policy optimizer."""

from __future__ import annotations

import unittest

from kalshi_policy_optimizer import (
    evaluate_config_grid,
    evaluate_policy_config,
    pareto_frontier,
    select_balanced_policy,
    select_max_pnl_policy,
    select_recommended_policy,
)


class TestParetoFrontier(unittest.TestCase):
    def test_identifies_non_dominated(self):
        configs = [
            {"n_trades": 2, "win_rate": 0.5, "total_pnl": 50.0},
            {"n_trades": 1, "win_rate": 1.0, "total_pnl": 19.0},
            {"n_trades": 1, "win_rate": 0.5, "total_pnl": 10.0},
        ]
        frontier = pareto_frontier(configs)
        self.assertEqual(len(frontier), 2)
        wr_pnl = {(c["win_rate"], c["total_pnl"]) for c in frontier}
        self.assertIn((0.5, 50.0), wr_pnl)
        self.assertIn((1.0, 19.0), wr_pnl)


class TestPolicySelect(unittest.TestCase):
    def test_prefers_insured_higher_pnl_with_enough_trades(self):
        configs = [
            {"n_trades": 25, "win_rate": 0.24, "total_pnl": 52.97, "n_wins": 6, "n_losses": 19,
             "win_rate_pct": 24.0, "total_deployed": 69.0, "roi_pct": 76.74,
             "min_forecast_edge": 0.24, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 1.5},
            {"n_trades": 9, "win_rate": 0.333, "total_pnl": 31.77, "n_wins": 3, "n_losses": 6,
             "win_rate_pct": 33.3, "total_deployed": 15.23, "roi_pct": 208.6,
             "min_forecast_edge": 0.30, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 1.6},
        ]
        rec = select_max_pnl_policy(configs)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["n_trades"], 25)
        self.assertEqual(rec["min_forecast_edge"], 0.24)

    def test_balanced_prefers_roi_times_win_rate(self):
        configs = [
            {"n_trades": 45, "win_rate": 0.733, "total_pnl": 292.0, "n_wins": 33, "n_losses": 12,
             "win_rate_pct": 73.3, "total_deployed": 380.0, "roi_pct": 76.99,
             "min_forecast_edge": 0.0, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True,
             "insurance_mode": "fraction", "insurance_budget_fraction": 1.0,
             "insurance_price_k": 0.6, "avg_insurance_legs": 2.0},
            {"n_trades": 32, "win_rate": 0.688, "total_pnl": 177.0, "n_wins": 22, "n_losses": 10,
             "win_rate_pct": 68.8, "total_deployed": 183.0, "roi_pct": 96.86,
             "min_forecast_edge": 0.06, "max_entry_yes_ask": 0.30,
             "require_cheapest_at_open": True, "insurance_enabled": True,
             "insurance_mode": "cover_book", "insurance_budget_fraction": 0.25,
             "insurance_price_k": 0.6, "avg_insurance_legs": 1.5},
        ]
        rec = select_balanced_policy(configs)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["min_forecast_edge"], 0.06)
        self.assertEqual(rec["insurance_mode"], "cover_book")

    def test_pnl_tiebreak_roi(self):
        configs = [
            {"n_trades": 22, "win_rate": 0.2, "total_pnl": 40.0, "n_wins": 4, "n_losses": 18,
             "win_rate_pct": 20.0, "total_deployed": 100.0, "roi_pct": 40.0,
             "min_forecast_edge": 0.18, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 0},
            {"n_trades": 22, "win_rate": 0.2, "total_pnl": 40.0, "n_wins": 4, "n_losses": 18,
             "win_rate_pct": 20.0, "total_deployed": 80.0, "roi_pct": 50.0,
             "min_forecast_edge": 0.20, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 0},
        ]
        rec = select_max_pnl_policy(configs)
        self.assertEqual(rec["roi_pct"], 50.0)

    def test_default_cap_tiebreak(self):
        configs = [
            {"n_trades": 22, "win_rate": 0.2, "total_pnl": 40.0, "n_wins": 4, "n_losses": 18,
             "win_rate_pct": 20.0, "total_deployed": 100.0, "roi_pct": 40.0,
             "min_forecast_edge": 0.18, "max_entry_yes_ask": 0.45,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 0},
            {"n_trades": 22, "win_rate": 0.2, "total_pnl": 40.0, "n_wins": 4, "n_losses": 18,
             "win_rate_pct": 20.0, "total_deployed": 100.0, "roi_pct": 40.0,
             "min_forecast_edge": 0.18, "max_entry_yes_ask": 0.35,
             "require_cheapest_at_open": True, "insurance_enabled": True, "avg_insurance_legs": 0},
        ]
        rec = select_max_pnl_policy(configs)
        self.assertEqual(rec["max_entry_yes_ask"], 0.35)


class TestMayIntegration(unittest.TestCase):
    KALSHI_PRICE_DIR = __import__("pathlib").Path(
        "/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History"
    )

    def _load_may_days(self):
        if not self.KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history not present")
        from kalshi_policy_optimizer import load_forecast_validated_days
        from kalshi_nws_join import default_kalshi_nws_dir, default_kalshi_observed_jsonl

        days = load_forecast_validated_days(
            self.KALSHI_PRICE_DIR,
            nws_dir=default_kalshi_nws_dir(),
            observed_jsonl=default_kalshi_observed_jsonl(),
        )
        return [d for d in days if d["day"] in ("2026-05-12", "2026-05-21")]

    def test_edge_14_beats_edge_0_on_win_rate(self):
        days = self._load_may_days()
        if len(days) < 2:
            self.skipTest("May 12/21 not in dataset")
        low = evaluate_policy_config(
            days, min_forecast_edge=0.0, max_entry_yes_ask=0.35,
            require_cheapest=True, insurance_enabled=True, order_mode="taker",
        )
        high = evaluate_policy_config(
            days, min_forecast_edge=0.14, max_entry_yes_ask=0.35,
            require_cheapest=True, insurance_enabled=True, order_mode="taker",
        )
        self.assertEqual(low["n_trades"], 2)
        self.assertEqual(high["n_trades"], 1)
        self.assertLess(low["win_rate"], high["win_rate"])
        self.assertGreater(high["total_pnl"], low["total_pnl"])


class TestParallelSweep(unittest.TestCase):
    def test_parallel_matches_serial_on_toy_grid(self):
        days = [
            {
                "day": "2026-05-12",
                "forecast_temp_f": 88.0,
                "forecast_source": "test",
                "observed_max_f": 89.0,
                "prices": {"86-87": 10.0, "88-89": 20.0, "90-91": 15.0},
                "market_bins": ["86-87", "88-89", "90-91"],
                "market_bin": "88-89",
                "column_map": {},
                "price_df": None,
                "order_mode": "taker",
            }
        ]
        grid = [
            {"min_forecast_edge": 0.0, "max_entry_yes_ask": 0.35, "require_cheapest": True, "insurance_enabled": True},
            {"min_forecast_edge": 0.14, "max_entry_yes_ask": 0.35, "require_cheapest": True, "insurance_enabled": False},
        ]
        serial = evaluate_config_grid(days, grid, order_mode="taker", workers=1)
        parallel = evaluate_config_grid(days, grid, order_mode="taker", workers=2)
        key = lambda c: (c["min_forecast_edge"], c["insurance_enabled"], c["n_trades"], c["total_pnl"])
        self.assertEqual(sorted(serial, key=key), sorted(parallel, key=key))


if __name__ == "__main__":
    unittest.main()
