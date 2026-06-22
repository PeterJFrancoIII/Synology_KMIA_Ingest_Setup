#!/usr/bin/env python3
"""Tests for archived candlestick loader at 10 AM anchor."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from kalshi_candle_archive import candle_archive_filename
from kalshi_candle_archive_loader import (
    anchor_bin_prices_from_candles,
    load_anchor_candle_context,
)
from kalshi_price_history_loader import anchor_time_utc_for_settlement


def _write_synthetic_candles(
    path: Path,
    *,
    settlement_date: str = "2026-04-20",
    anchor: datetime,
) -> None:
    event = "KXHIGHMIA-26APR20"
    records = [
        {
            "settlement_date": settlement_date,
            "event_ticker": event,
            "market_ticker": f"{event}-T83",
            "column_header": "83° to 84°",
            "candle": {
                "end_period_ts": int(anchor.timestamp()) + 60,
                "yes_ask": {"close_dollars": "0.22"},
                "yes_bid": {"close_dollars": "0.18"},
                "volume": 15,
            },
        },
        {
            "settlement_date": settlement_date,
            "event_ticker": event,
            "market_ticker": f"{event}-T79",
            "column_header": "79° to 80°",
            "candle": {
                "end_period_ts": int(anchor.timestamp()) + 120,
                "yes_ask": {"close_dollars": "0.35"},
                "volume": 8,
            },
        },
        {
            "settlement_date": settlement_date,
            "event_ticker": event,
            "market_ticker": f"{event}-T83",
            "column_header": "83° to 84°",
            "candle": {
                "end_period_ts": int(anchor.timestamp()) + 600,
                "yes_ask": {"close_dollars": "0.30"},
            },
        },
    ]
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


class TestKalshiCandleArchiveLoader(unittest.TestCase):
    def test_load_anchor_candle_context_maps_bins(self):
        column_map = {"83° to 84°": "83-84", "79° to 80°": "79-80"}
        anchor = anchor_time_utc_for_settlement("2026-04-20")

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            path = archive / candle_archive_filename("2026-04-20")
            _write_synthetic_candles(path, anchor=anchor)

            ctx = load_anchor_candle_context("2026-04-20", column_map, archive)
            self.assertTrue(ctx.found)
            self.assertAlmostEqual(ctx.yes_ask_cents("83-84"), 22.0, places=1)
            self.assertAlmostEqual(ctx.yes_ask_cents("79-80"), 35.0, places=1)
            self.assertEqual(ctx.by_bin["83-84"]["volume"], 15)

    def test_picks_nearest_candle_to_anchor(self):
        column_map = {"83° to 84°": "83-84"}
        anchor = anchor_time_utc_for_settlement("2026-04-20")

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            path = archive / candle_archive_filename("2026-04-20")
            _write_synthetic_candles(path, anchor=anchor)

            ctx = load_anchor_candle_context("2026-04-20", column_map, archive)
            self.assertAlmostEqual(ctx.yes_ask_cents("83-84"), 22.0, places=1)

    def test_anchor_bin_prices_from_candles(self):
        column_map = {"83° to 84°": "83-84"}
        anchor = anchor_time_utc_for_settlement("2026-04-20")

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            path = archive / candle_archive_filename("2026-04-20")
            _write_synthetic_candles(path, anchor=anchor)
            ctx = load_anchor_candle_context("2026-04-20", column_map, archive)

            prices = anchor_bin_prices_from_candles(ctx)
            self.assertAlmostEqual(prices["83-84"], 22.0, places=1)

    def test_missing_archive_returns_reason(self):
        column_map = {"83° to 84°": "83-84"}
        with tempfile.TemporaryDirectory() as tmp:
            ctx = load_anchor_candle_context(
                "2026-04-20", column_map, Path(tmp) / "missing"
            )
            self.assertFalse(ctx.found)
            self.assertEqual(ctx.reason, "archive_dir_missing")


    def test_scan_limit_fill_uses_candle_when_book_missing(self):
        from kalshi_candle_archive_loader import AnchorCandleContext
        from kalshi_price_history_loader import scan_limit_fill

        ctx = AnchorCandleContext(
            settlement_date="2026-04-20",
            found=True,
            matched_timestamp_utc="2026-04-19T14:01:00+00:00",
            by_bin={
                "83-84": {
                    "yes_ask_dollars": 0.21,
                    "yes_ask_cents": 21.0,
                    "matched_timestamp_utc": "2026-04-19T14:01:00+00:00",
                }
            },
        )
        import pandas as pd

        fill = scan_limit_fill(
            pd.DataFrame(),
            "2026-04-20",
            "83-84",
            limit_bid=0.25,
            anchor_candle=ctx,
        )
        self.assertTrue(fill["filled"])
        self.assertEqual(fill["fill_source"], "archived_candle_at_anchor")


if __name__ == "__main__":
    unittest.main()
