#!/usr/bin/env python3
"""Tests for export_trading_policy.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_trading_policy import export_trading_policy
from trading_policy_manifest import build_trading_policy_manifest


class TestExportTradingPolicy(unittest.TestCase):
    def test_build_manifest_schema(self):
        rec = {
            "min_forecast_edge": 0.18,
            "max_entry_yes_ask": 0.35,
            "insurance_enabled": True,
            "confidence": "low",
            "n_trades": 4,
            "win_rate_pct": 50.0,
            "total_pnl": 25.15,
        }
        manifest = build_trading_policy_manifest(rec, source_sweep="policy_sweep_test.json")
        self.assertEqual(manifest["min_forecast_edge"], 0.18)
        self.assertEqual(manifest["order_mode"], "maker_limit")
        self.assertFalse(manifest["approved_by_human"])
        self.assertEqual(manifest["live_model_version"], "integer_dist_v1")
        self.assertTrue(manifest["safety"]["no_real_trading"])

    def test_export_writes_draft_only_with_no_copy(self):
        with tempfile.TemporaryDirectory() as td:
            backtest_dir = Path(td) / "backtest"
            research_dir = Path(td) / "research"
            backtest_dir.mkdir()
            research_dir.mkdir()
            (backtest_dir / "recommended_policy.json").write_text(
                json.dumps({
                    "recommended_policy": {
                        "min_forecast_edge": 0.18,
                        "max_entry_yes_ask": 0.35,
                        "insurance_enabled": True,
                        "confidence": "low",
                        "n_trades": 1,
                    }
                }),
                encoding="utf-8",
            )
            out = export_trading_policy(
                backtest_dir=backtest_dir,
                kalshi_research_dir=research_dir,
                copy_to_kalshi=False,
            )
            draft = research_dir / "trading_policy_draft.json"
            approved = research_dir / "trading_policy.json"
            self.assertTrue(draft.is_file())
            self.assertFalse(approved.is_file())
            self.assertEqual(out["draft"]["min_forecast_edge"], 0.18)


if __name__ == "__main__":
    unittest.main()
