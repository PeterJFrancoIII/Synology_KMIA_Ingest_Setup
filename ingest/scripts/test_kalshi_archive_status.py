#!/usr/bin/env python3
"""Tests for kalshi_archive_status.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kalshi_archive_status import build_archive_status


class TestKalshiArchiveStatus(unittest.TestCase):
    def test_build_status_empty_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            price = root / "prices"
            price.mkdir()
            (price / "kalshi-price-history-kxhighmia-26apr20-minute.csv").write_text(
                "timestamp,79° to 80°\n2026-04-19T14:00:00Z,25\n",
                encoding="utf-8",
            )
            status = build_archive_status(
                price_history_dir=price,
                orderbook_archive_dir=root / "ob",
                candle_archive_dir=root / "candles",
            )
            self.assertEqual(status["n_price_history_days"], 1)
            self.assertEqual(status["n_price_days_with_orderbook"], 0)
            self.assertEqual(status["n_price_days_with_candles"], 0)


if __name__ == "__main__":
    unittest.main()
