#!/usr/bin/env python3
"""Tests for Kalshi price-history loader and Console 2 checksum backtest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from historical_checksum_backtest import (
    aggregate_hit_rates,
    evaluate_day,
    run_checksum_backtest,
    select_anchor_row,
)
from kalshi_price_history_loader import (
    MAX_ENTRY_YES_ASK,
    ORDER_MODE_MAKER_LIMIT,
    ORDER_MODE_TAKER,
    anchor_time_utc_for_settlement,
    derive_limit_bid,
    evaluate_bin_open_purchase,
    evaluate_hedged_open_purchase,
    forecast_bin_is_cheapest_at_open,
    load_anchor_prices_for_date,
    load_price_history_csv,
    model_prob_for_market_bin,
    parse_kalshi_column_header,
    scan_limit_fill,
    settlement_date_from_path,
    temp_to_bin,
)

KALSHI_PRICE_DIR = Path(
    "/Users/computer/Desktop/App Development/Kalshi/Kalshi - Miami Max Temp. Bet History"
)


def _fixture_rows() -> list[dict]:
    return [
        {
            "target_date_et": "2024-08-01",
            "release_time_et": "2024-07-31 16:00:00-04:00",
            "forecast_temp_f": 90.0,
            "observed_max_f": 90.0,
            "abs_error_f": 0.0,
            "within_0f": True,
            "within_1f": True,
            "within_2f": True,
            "within_3f": True,
            "lead_hour_bucket": 20,
            "forecast_stability": "STABLE",
        },
        {
            "target_date_et": "2024-08-03",
            "release_time_et": "2024-08-02 16:00:00-04:00",
            "forecast_temp_f": 85.0,
            "observed_max_f": 91.0,
            "abs_error_f": 6.0,
            "within_0f": False,
            "within_1f": False,
            "within_2f": False,
            "within_3f": False,
            "lead_hour_bucket": 21,
            "forecast_stability": "UNSTABLE",
        },
    ]


class TestKalshiPriceHistoryLoader(unittest.TestCase):
    def test_settlement_date_from_path(self):
        p = Path("kalshi-price-history-kxhighmia-26apr20-minute.csv")
        self.assertEqual(settlement_date_from_path(p), "2026-04-20")

    def test_temp_to_bin(self):
        self.assertEqual(temp_to_bin(78), "<=78")
        self.assertEqual(temp_to_bin(80), "79-80")
        self.assertEqual(temp_to_bin(87), ">=87")

    def test_parse_kalshi_column_header(self):
        self.assertEqual(parse_kalshi_column_header("79° to 80°"), "79-80")
        self.assertEqual(parse_kalshi_column_header("83° or above"), ">=83")
        self.assertEqual(parse_kalshi_column_header("74° or below"), "<=74")

    def test_forecast_bin_cheapest_at_open(self):
        prices = {"<=78": 4.0, "79-80": 25.0, "81-82": 59.0, "83-84": 22.0, "85-86": 32.0, ">=87": 26.0}
        result = forecast_bin_is_cheapest_at_open(prices, "<=78")
        self.assertTrue(result["passes"])
        result2 = forecast_bin_is_cheapest_at_open(prices, "81-82")
        self.assertFalse(result2["passes"])

    def test_model_prob_for_market_bin(self):
        p = model_prob_for_market_bin(84.0, "83-84")
        self.assertGreater(p, 0.1)

    def test_evaluate_bin_open_purchase(self):
        prices = {"<=78": 4.0, "79-80": 25.0, "81-82": 59.0, "83-84": 22.0, "85-86": 32.0, ">=87": 26.0}
        out = evaluate_bin_open_purchase(
            prices, "83-84", 84.0, market_bins=list(prices.keys()), order_mode=ORDER_MODE_TAKER
        )
        self.assertTrue(out["entry_within_cap"])
        self.assertLessEqual(out["forecast_bin_yes_ask"], MAX_ENTRY_YES_ASK)

    def test_derive_limit_bid_respects_edge_and_cap(self):
        bid = derive_limit_bid(0.3422, min_edge=0.18, max_cap=0.35)
        self.assertAlmostEqual(bid, 0.1622, places=3)
        self.assertGreaterEqual(0.3422 - bid, 0.18)

    def test_insurance_relational_price_cap(self):
        from kalshi_price_history_loader import max_insurance_yes_ask

        self.assertGreater(max_insurance_yes_ask(0.28), max_insurance_yes_ask(0.12))

    def test_evaluate_hedged_open_purchase_allocates_insurance(self):
        from kalshi_price_history_loader import evaluate_hedged_open_purchase

        prices = {
            "87-88": 8.0,
            "89-90": 20.0,
            "91-92": 12.0,
            "93-94": 4.0,
            "95-96": 3.0,
            ">=97": 2.0,
        }
        out = evaluate_hedged_open_purchase(
            prices,
            "89-90",
            90.0,
            list(prices.keys()),
            min_forecast_edge=0.0,
            order_mode=ORDER_MODE_TAKER,
        )
        if out["open_purchase_eligible"]:
            self.assertLessEqual(
                out.get("insurance_total_cost", 0),
                out.get("forecast_total_cost", 0) * 0.25 + 0.01,
            )

    def test_settle_hedged_trade_may12(self):
        from historical_checksum_backtest import _settle_hedged_trade

        purchase = {
            "forecast_market_bin": "89-90",
            "forecast_bin_yes_ask": 0.20,
            "forecast_contracts": 23,
            "insurance_legs": [{
                "market_bin": "87-88",
                "yes_ask": 0.08,
                "contracts": 5,
            }],
        }
        trade = _settle_hedged_trade(purchase=purchase, observed_max_f=91.4)
        self.assertEqual(trade["forecast_leg"]["trade_result"], "LOSS")

    def test_forecast_edge_18pct_constant(self):
        from kalshi_price_history_loader import MIN_FORECAST_EXECUTABLE_EDGE

        self.assertAlmostEqual(MIN_FORECAST_EXECUTABLE_EDGE, 0.18)

    def test_forecast_edge_18pct_filters_low_edge_days(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        for day, forecast_temp_f, note in (
            ("2026-05-12", 90.0, "edge ~13.1%"),
            ("2026-05-21", 89.0, "edge ~14.1%"),
        ):
            with self.subTest(day=day, forecast_temp_f=forecast_temp_f):
                snap = load_anchor_prices_for_date(
                    KALSHI_PRICE_DIR, day, forecast_temp_f=forecast_temp_f, order_mode=ORDER_MODE_TAKER
                )
                purchase = snap.get("open_purchase") or {}
                self.assertFalse(
                    purchase.get("open_purchase_eligible"),
                    msg=f"{day} should fail 18% gate ({note})",
                )

    def test_forecast_edge_18pct_allows_jun05(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        snap = load_anchor_prices_for_date(
            KALSHI_PRICE_DIR, "2026-06-05", forecast_temp_f=81.0, order_mode=ORDER_MODE_TAKER
        )
        purchase = snap.get("open_purchase") or {}
        self.assertTrue(purchase.get("open_purchase_eligible"))  # edge ~33% >= 18%

    def test_maker_limit_may22_fills_with_zero_fee(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        snap = load_anchor_prices_for_date(
            KALSHI_PRICE_DIR, "2026-05-22", forecast_temp_f=85.0, order_mode=ORDER_MODE_MAKER_LIMIT
        )
        purchase = snap.get("open_purchase") or {}
        self.assertTrue(purchase.get("order_posted"))
        self.assertTrue(purchase.get("forecast_filled"))
        self.assertTrue(purchase.get("open_purchase_eligible"))
        self.assertEqual(purchase.get("forecast_fee"), 0.0)
        self.assertLessEqual(purchase.get("forecast_bin_yes_ask"), purchase.get("forecast_limit_bid"))

    def test_maker_limit_may12_fills_and_loses(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        from historical_checksum_backtest import _settle_hedged_trade

        snap = load_anchor_prices_for_date(
            KALSHI_PRICE_DIR, "2026-05-12", forecast_temp_f=88.0, order_mode=ORDER_MODE_MAKER_LIMIT
        )
        purchase = snap.get("open_purchase") or {}
        self.assertTrue(purchase.get("open_purchase_eligible"))
        trade = _settle_hedged_trade(purchase=purchase, observed_max_f=91.4)
        self.assertEqual(trade["trade_result"], "LOSS")

    def test_settle_market_bin_trade_loss_when_observed_above_range(self):
        from historical_checksum_backtest import _settle_market_bin_trade

        out = _settle_market_bin_trade(
            market_bin="89-90",
            observed_max_f=91.4,
            yes_ask=0.20,
        )
        self.assertFalse(out["market_bin_hit"])
        self.assertEqual(out["trade_result"], "LOSS")
        self.assertLess(out["simulated_pnl"], 0)

    def test_settle_market_bin_trade_win_when_observed_in_range(self):
        from historical_checksum_backtest import _settle_market_bin_trade

        out = _settle_market_bin_trade(
            market_bin="89-90",
            observed_max_f=89.6,
            yes_ask=0.19,
        )
        self.assertTrue(out["market_bin_hit"])
        self.assertEqual(out["trade_result"], "WIN")
        self.assertGreater(out["simulated_pnl"], 0)

    def test_load_real_kalshi_csv(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        path = KALSHI_PRICE_DIR / "kalshi-price-history-kxhighmia-26apr20-minute.csv"
        df, column_map = load_price_history_csv(path)
        self.assertIn("<=78", df.columns)
        self.assertGreater(len(df), 100)

    def test_anchor_prices_apr20_bin_open(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        snap = load_anchor_prices_for_date(KALSHI_PRICE_DIR, "2026-04-20", forecast_temp_f=84.0)
        self.assertTrue(snap["found"])
        self.assertLessEqual(snap["delta_minutes_from_anchor"], 5)
        self.assertEqual(snap["forecast_market_bin"], "83-84")


    def test_load_anchor_prices_includes_orderbook_when_archive_present(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        import json
        import tempfile

        anchor = anchor_time_utc_for_settlement("2026-04-20")
        fetched = anchor.replace(minute=2).isoformat()
        record = {
            "fetched_at_utc": fetched,
            "markets_compact": [{
                "event_ticker": "KXHIGHMIA-26APR20",
                "ticker": "KXHIGHMIA-26APR20-T83",
                "subtitle": "83° to 84°",
            }],
            "orderbooks": {
                "KXHIGHMIA-26APR20-T83": {
                    "top_yes_ask_dollars": 0.22,
                    "yes_ask_size": 50,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            ob_dir = archive / "orderbooks"
            ob_dir.mkdir(parents=True)
            (ob_dir / f"{anchor.date().isoformat()}.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )
            snap = load_anchor_prices_for_date(
                KALSHI_PRICE_DIR,
                "2026-04-20",
                forecast_temp_f=84.0,
                order_mode=ORDER_MODE_MAKER_LIMIT,
                orderbook_archive_dir=archive,
            )
            self.assertTrue(snap.get("anchor_orderbook", {}).get("found"))
            self.assertIsNotNone(snap.get("_anchor_orderbook"))


class TestHistoricalChecksumBacktest(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(_fixture_rows())

    def test_select_anchor_row(self):
        day_df = self.df[self.df["target_date_et"] == "2024-08-01"]
        anchor = select_anchor_row(day_df)
        self.assertEqual(int(anchor["lead_hour_bucket"]), 20)

    def test_evaluate_day_hit(self):
        anchor = select_anchor_row(self.df[self.df["target_date_et"] == "2024-08-01"])
        result = evaluate_day(anchor)
        self.assertTrue(result["forecast_bin_hit"])

    def test_evaluate_day_with_kalshi_prices(self):
        if not KALSHI_PRICE_DIR.is_dir():
            self.skipTest("Kalshi price history folder not present")
        snap = load_anchor_prices_for_date(KALSHI_PRICE_DIR, "2026-04-20", forecast_temp_f=84.0)
        anchor = pd.Series({
            "target_date_et": "2026-04-20",
            "forecast_temp_f": 84.0,
            "observed_max_f": 84.0,
            "abs_error_f": 0.0,
            "within_0f": True,
            "within_1f": True,
            "within_2f": True,
            "within_3f": True,
            "lead_hour_bucket": 20,
            "release_time_et": "2026-04-19 10:00:00-04:00",
        })
        result = evaluate_day(anchor, price_snapshot=snap)
        self.assertEqual(result["market"]["price_source"], "kalshi_price_history")
        self.assertEqual(result["market"]["forecast_market_bin"], "83-84")
        self.assertLessEqual(result["market"].get("delta_minutes_from_open", 99), 5)

    def test_aggregate_hit_rates(self):
        daily = [
            {"tolerance": {"within_0f": True, "within_1f": True, "within_2f": True, "within_3f": True},
             "forecast_bin_hit": True},
            {"tolerance": {"within_0f": False, "within_1f": False, "within_2f": False, "within_3f": False},
             "forecast_bin_hit": False},
        ]
        rates = aggregate_hit_rates(daily)
        self.assertAlmostEqual(rates["pct_within_0f"], 50.0)

    def test_run_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "fixture.csv"
            pd.DataFrame(_fixture_rows()).to_csv(csv_path, index=False)
            out_dir = Path(tmp) / "reports"
            report = run_checksum_backtest(csv_path=csv_path, output_dir=out_dir)
            self.assertEqual(report["n_days_tested"], 2)
            out_path = Path(report["output_path"])
            loaded = json.loads(out_path.read_text())
            self.assertEqual(loaded["n_days_tested"], 2)


class TestInsuranceAllocation(unittest.TestCase):
    def test_cover_book_sizes_to_running_book(self):
        from kalshi_price_history_loader import (
            allocate_insurance_cover_book,
            select_insurance_bins_bilateral,
        )

        probs = {"79-80": 0.25, "81-82": 0.35, "83-84": 0.20}
        candidates = select_insurance_bins_bilateral(probs, "81-82")
        prices = {"79-80": 8.0, "81-82": 30.0, "83-84": 12.0}
        legs = allocate_insurance_cover_book(
            candidates,
            prices,
            forecast_cost=4.0,
            insurance_budget=10.0,
            price_k=0.6,
        )
        self.assertTrue(len(legs) >= 1)
        for leg in legs:
            self.assertGreater(leg["contracts"], 0)
            self.assertIn("cover_book_target", leg)

    def test_fraction_budget_no_leak_on_zero_contracts(self):
        from kalshi_price_history_loader import allocate_insurance_legs

        # All asks above cap → no legs, budget not consumed
        legs = allocate_insurance_legs(
            {"79-80": 0.3},
            {"79-80": 99.0},
            insurance_budget=2.0,
            price_k=0.01,
        )
        self.assertEqual(legs, [])


if __name__ == "__main__":
    unittest.main()
