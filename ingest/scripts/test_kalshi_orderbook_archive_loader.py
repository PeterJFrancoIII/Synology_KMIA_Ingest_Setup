#!/usr/bin/env python3
"""Tests for archived orderbook loader and maker-fill replay at 10 AM anchor."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from kalshi_orderbook_archive_loader import (
    AnchorOrderbookContext,
    extract_top_of_book,
    load_anchor_orderbook_context,
)
from kalshi_price_history_loader import (
    anchor_time_utc_for_settlement,
    scan_limit_fill,
)


def _synthetic_archive_record(
    *,
    settlement_date: str = "2026-04-20",
    fetched_at_utc: str = "2026-04-19T14:02:00+00:00",
) -> dict:
    event = "KXHIGHMIA-26APR20"
    return {
        "fetched_at_utc": fetched_at_utc,
        "markets_compact": [
            {
                "event_ticker": event,
                "ticker": f"{event}-T83",
                "subtitle": "83° to 84°",
            },
            {
                "event_ticker": event,
                "ticker": f"{event}-T79",
                "subtitle": "79° to 80°",
            },
        ],
        "orderbooks": {
            f"{event}-T83": {
                "top_yes_ask_dollars": 0.22,
                "yes_ask_size": 50,
            },
            f"{event}-T79": {
                "top_yes_ask_dollars": 0.40,
                "yes_ask_size": 120,
            },
        },
    }


class TestKalshiOrderbookArchiveLoader(unittest.TestCase):
    def test_extract_top_of_book_from_ladder(self):
        ob = {
            "yes_bids": [[18, 10]],
            "no_bids": [[75, 30]],
        }
        top = extract_top_of_book(ob)
        self.assertAlmostEqual(top["yes_bid_dollars"], 0.18, places=2)
        self.assertAlmostEqual(top["yes_ask_dollars"], 0.25, places=2)
        self.assertEqual(top["yes_ask_size"], 30)

    def test_load_anchor_orderbook_context_maps_bins(self):
        column_map = {
            "83° to 84°": "83-84",
            "79° to 80°": "79-80",
        }
        anchor = anchor_time_utc_for_settlement("2026-04-20")
        fetched = anchor.replace(minute=2).isoformat()

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            ob_dir = archive / "orderbooks"
            ob_dir.mkdir(parents=True)
            record = _synthetic_archive_record(fetched_at_utc=fetched)
            (ob_dir / f"{anchor.date().isoformat()}.jsonl").write_text(
                json.dumps(record) + "\n",
                encoding="utf-8",
            )

            ctx = load_anchor_orderbook_context(
                "2026-04-20", column_map, archive
            )
            self.assertTrue(ctx.found)
            self.assertAlmostEqual(ctx.yes_ask_dollars("83-84"), 0.22, places=2)
            self.assertEqual(ctx.yes_ask_size("83-84"), 50)
            self.assertIsNotNone(ctx.delta_minutes_from_anchor)

    def test_load_returns_missing_when_no_archive(self):
        column_map = {"83° to 84°": "83-84"}
        with tempfile.TemporaryDirectory() as tmp:
            ctx = load_anchor_orderbook_context(
                "2026-04-20", column_map, Path(tmp) / "empty"
            )
            self.assertFalse(ctx.found)
            self.assertEqual(ctx.reason, "archive_dir_missing")

    def test_scan_limit_fill_prefers_archived_book_at_anchor(self):
        ctx = AnchorOrderbookContext(
            settlement_date="2026-04-20",
            found=True,
            fetched_at_utc="2026-04-19T14:02:00+00:00",
            by_bin={
                "83-84": {
                    "yes_ask_dollars": 0.20,
                    "yes_ask_cents": 20.0,
                    "yes_ask_size": 40,
                }
            },
        )
        anchor = anchor_time_utc_for_settlement("2026-04-20")
        df = pd.DataFrame(
            [{
                "timestamp": anchor.replace(minute=30),
                "83-84": 35.0,
            }]
        )
        fill = scan_limit_fill(
            df,
            "2026-04-20",
            "83-84",
            limit_bid=0.22,
            anchor_book=ctx,
        )
        self.assertTrue(fill["filled"])
        self.assertEqual(fill["fill_source"], "archived_orderbook_at_anchor")
        self.assertAlmostEqual(fill["fill_price"], 0.20, places=2)

    def test_scan_limit_fill_falls_back_to_csv_when_book_ask_too_high(self):
        ctx = AnchorOrderbookContext(
            settlement_date="2026-04-20",
            found=True,
            fetched_at_utc="2026-04-19T14:02:00+00:00",
            by_bin={
                "83-84": {
                    "yes_ask_dollars": 0.30,
                    "yes_ask_cents": 30.0,
                }
            },
        )
        anchor = anchor_time_utc_for_settlement("2026-04-20")
        df = pd.DataFrame(
            [{
                "timestamp": anchor.replace(minute=15),
                "83-84": 18.0,
            }]
        )
        fill = scan_limit_fill(
            df,
            "2026-04-20",
            "83-84",
            limit_bid=0.22,
            anchor_book=ctx,
        )
        self.assertTrue(fill["filled"])
        self.assertEqual(fill["fill_source"], "minute_csv")
        self.assertAlmostEqual(fill["fill_price"], 0.18, places=2)


if __name__ == "__main__":
    unittest.main()
