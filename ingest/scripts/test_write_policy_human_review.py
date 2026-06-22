#!/usr/bin/env python3
"""Tests for write_policy_human_review.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from write_policy_human_review import build_human_review_text


class TestWritePolicyHumanReview(unittest.TestCase):
    def test_build_human_review_contains_key_sections(self):
        text = build_human_review_text(
            draft={
                "min_forecast_edge": 0.26,
                "max_entry_yes_ask": 0.35,
                "require_cheapest_at_open": True,
                "insurance_enabled": True,
                "confidence": "moderate",
                "backtest_metrics": {
                    "n_trades": 21,
                    "win_rate_pct": 28.6,
                    "total_pnl": 70.47,
                    "roi_pct": 136.76,
                },
            },
            recommended={"min_forecast_edge": 0.26},
            backtest={
                "n_days_tested": 62,
                "n_days_with_anchor_orderbook": 0,
                "n_days_with_anchor_candle": 0,
                "hit_rates": {"open_purchase_eligible_rate": 58.1},
            },
            archive={
                "n_price_history_days": 62,
                "coverage_pct": {"orderbook_vs_price_days": 0.0, "candles_vs_price_days": 0.0},
            },
            prob_compare={"max_abs_delta": 0.0},
        )
        self.assertIn("Human Review", text)
        self.assertIn("26%", text)
        self.assertIn("NOT APPROVED", text)

    def test_stale_approval_when_draft_differs(self):
        text = build_human_review_text(
            draft={"model_version": "integer_dist_v1", "min_forecast_edge": 0.26,
                   "max_entry_yes_ask": 0.35, "insurance_enabled": True, "confidence": "moderate"},
            recommended={},
            backtest=None,
            archive={"coverage_pct": {}},
            prob_compare=None,
            approved={"approved_by_human": True, "model_version": "gaussian_v1_truncation_optional",
                      "min_forecast_edge": 0.26, "max_entry_yes_ask": 0.35},
        )
        self.assertIn("STALE APPROVAL", text)


if __name__ == "__main__":
    unittest.main()
