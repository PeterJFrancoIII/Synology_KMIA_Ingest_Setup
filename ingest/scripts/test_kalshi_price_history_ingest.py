#!/usr/bin/env python3
"""Tests for Kalshi price-history API ingest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kalshi_market_data_client import forward_fill_on_grid, minute_end_timestamps
from kalshi_price_history_ingest import (
    build_price_history_table,
    column_header_for_market,
    ingest_settlement_day,
    write_price_history_csv,
)
from kalshi_price_history_loader import (
    discover_price_history_files,
    event_ticker_for_settlement,
    export_filename_for_settlement,
    load_price_history_csv,
    settlement_date_from_event_ticker,
)


class TestNomenclature(unittest.TestCase):
    def test_filename_and_event_ticker(self):
        self.assertEqual(
            export_filename_for_settlement("2026-04-20"),
            "kalshi-price-history-kxhighmia-26apr20-minute.csv",
        )
        self.assertEqual(event_ticker_for_settlement("2026-04-20"), "KXHIGHMIA-26APR20")
        self.assertEqual(
            settlement_date_from_event_ticker("KXHIGHMIA-26APR20"),
            "2026-04-20",
        )

    def test_column_header_uses_subtitle(self):
        m = {"subtitle": "87° to 88°", "title": "Will it be hot?"}
        self.assertEqual(column_header_for_market(m), "87° to 88°")


class TestMinuteGrid(unittest.TestCase):
    def test_minute_end_timestamps(self):
        grid = minute_end_timestamps(1776607200, 1776607320)  # 14:00–14:02 UTC
        self.assertEqual(grid, [1776607260, 1776607320])

    def test_forward_fill_carries_last_quote(self):
        grid = [100, 160, 220]
        series = {100: 4.0, 220: 9.0}
        filled = forward_fill_on_grid(grid, series)
        self.assertEqual(filled[100], 4.0)
        self.assertEqual(filled[160], 4.0)
        self.assertEqual(filled[220], 9.0)


class TestBuildTable(unittest.TestCase):
    @patch("kalshi_price_history_ingest.get_market_candlesticks")
    def test_merge_timestamps_across_bins(self, mock_candles):
        markets = [
            {"ticker": "KXHIGHMIA-26MAY12-T85", "subtitle": "84° or below"},
            {"ticker": "KXHIGHMIA-26MAY12-B85.5", "subtitle": "85° to 86°"},
        ]
        candle_a = {"end_period_ts": 100, "yes_ask": {"close_dollars": "0.0400"}}
        candle_b1 = {"end_period_ts": 100, "yes_ask": {"close_dollars": "0.2500"}}
        candle_b2 = {"end_period_ts": 160, "yes_ask": {"close_dollars": "0.3000"}}
        mock_candles.side_effect = [[candle_a], [candle_b1, candle_b2]]
        headers, rows = build_price_history_table(
            markets, start_ts=60, end_ts=200, minute_grid=False
        )
        self.assertEqual(headers, ["84° or below", "85° to 86°"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["timestamp"], "1970-01-01T00:01:40Z")
        self.assertEqual(rows[0]["84° or below"], 4.0)
        self.assertEqual(rows[0]["85° to 86°"], 25.0)
        self.assertIsNone(rows[1].get("84° or below"))

    @patch("kalshi_price_history_ingest.get_market_candlesticks")
    def test_minute_grid_one_row_per_minute(self, mock_candles):
        markets = [{"ticker": "KX-T1", "subtitle": "84° or below"}]
        mock_candles.return_value = [
            {"end_period_ts": 120, "yes_ask": {"close_dollars": "0.0400"}},
            {"end_period_ts": 180, "yes_ask": {"close_dollars": "0.0500"}},
        ]
        headers, rows = build_price_history_table(
            markets, start_ts=60, end_ts=180, minute_grid=True
        )
        self.assertEqual(len(rows), 2)  # minutes 120 and 180
        self.assertEqual(rows[0]["84° or below"], 4.0)
        self.assertEqual(rows[1]["84° or below"], 5.0)


class TestWriteAndLoad(unittest.TestCase):
    def test_csv_roundtrip_through_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / export_filename_for_settlement("2026-06-01")
            headers = ["78° or below", "79° to 80°", "81° to 82°", "83° to 84°"]
            rows = [
                {
                    "timestamp": "2026-05-31T14:02:00Z",
                    "78° or below": 4.0,
                    "79° to 80°": None,
                    "81° to 82°": 10.0,
                    "83° to 84°": 20.0,
                }
            ]
            write_price_history_csv(path, headers, rows)
            df, column_map = load_price_history_csv(path)
            self.assertIn("<=78", column_map.values())
            self.assertIn("79-80", column_map.values())
            self.assertEqual(len(df), 1)
            discovered = discover_price_history_files(Path(tmp))
            self.assertIn("2026-06-01", discovered)


class TestIngestSettlementDay(unittest.TestCase):
    @patch("kalshi_price_history_ingest.get_event_markets")
    @patch("kalshi_price_history_ingest.build_price_history_table")
    @patch("kalshi_price_history_ingest.market_window_unix")
    def test_writes_file_and_manifest(self, mock_window, mock_table, mock_markets):
        mock_markets.return_value = [
            {"ticker": "KXHIGHMIA-26JUN19-T96", "subtitle": "95° or below", "open_time": "2026-06-18T14:00:00Z", "close_time": "2026-06-20T04:59:00Z"},
            {"ticker": "KXHIGHMIA-26JUN19-B95.5", "subtitle": "95° to 96°", "open_time": "2026-06-18T14:00:00Z", "close_time": "2026-06-20T04:59:00Z"},
            {"ticker": "KXHIGHMIA-26JUN19-B93.5", "subtitle": "93° to 94°", "open_time": "2026-06-18T14:00:00Z", "close_time": "2026-06-20T04:59:00Z"},
            {"ticker": "KXHIGHMIA-26JUN19-B91.5", "subtitle": "91° to 92°", "open_time": "2026-06-18T14:00:00Z", "close_time": "2026-06-20T04:59:00Z"},
        ]
        mock_window.return_value = (1, 2)
        mock_table.return_value = (
            ["95° or below", "95° to 96°", "93° to 94°", "91° to 92°"],
            [{
                "timestamp": "2026-06-18T14:02:00Z",
                "95° or below": 3.0,
                "95° to 96°": 12.0,
                "93° to 94°": 8.0,
                "91° to 92°": 5.0,
            }],
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = ingest_settlement_day("2026-06-19", out)
            self.assertEqual(result["status"], "written")
            manifest = json.loads((out / ".kalshi_price_history_ingest_manifest.json").read_text())
            self.assertIn("2026-06-19", manifest["records"])


if __name__ == "__main__":
    unittest.main()
