#!/usr/bin/env python3
"""Tests for full candlestick JSONL archive."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kalshi_candle_archive import (
    archive_settlement_candles,
    candle_archive_filename,
)
from kalshi_market_data_client import normalize_candlestick


class TestCandleArchive(unittest.TestCase):
    def test_filename(self):
        self.assertEqual(
            candle_archive_filename("2026-04-20"),
            "kalshi-price-history-kxhighmia-26apr20-candles.jsonl",
        )

    def test_normalize_candlestick(self):
        raw = {
            "end_period_ts": 100,
            "yes_ask": {"close_dollars": "0.25", "open_dollars": "0.20"},
            "yes_bid": {"close_dollars": "0.22"},
            "volume": 42,
        }
        out = normalize_candlestick(raw)
        self.assertEqual(out["end_period_ts"], 100)
        self.assertEqual(out["yes_ask"]["close_dollars"], "0.25")
        self.assertEqual(out["volume"], 42)
        self.assertEqual(out["raw"], raw)

    @patch("kalshi_candle_archive.get_market_candlesticks")
    @patch("kalshi_candle_archive.get_event_markets")
    def test_archive_writes_jsonl(self, mock_markets, mock_candles):
        mock_markets.return_value = [
            {"ticker": f"KXHIGHMIA-26APR20-T{i}", "subtitle": f"bin{i}", "open_time": "2026-04-19T14:00:00Z", "close_time": "2026-04-21T04:59:00Z"}
            for i in range(6)
        ]
        mock_candles.return_value = [
            {"end_period_ts": 100, "yes_ask": {"close_dollars": "0.25"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            out = archive_settlement_candles("2026-04-20", Path(td), force=True)
            self.assertEqual(out["status"], "ok")
            path = Path(out["output_path"])
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 6)
            rec = json.loads(lines[0])
            self.assertIn("KXHIGHMIA-26APR20", rec["market_ticker"])
            self.assertEqual(rec["candle"]["yes_ask"]["close_dollars"], "0.25")


if __name__ == "__main__":
    unittest.main()
