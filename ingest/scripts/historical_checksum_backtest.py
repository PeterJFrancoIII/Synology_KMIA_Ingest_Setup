#!/usr/bin/env python3
"""Historical forecast-vs-observed checksum backtest (Console 2).

Replays enriched NDFD rows against observed ISD truth and optional Kalshi
price-history bin costs.  Validates tolerance math, bin mapping, and bin-open
purchase policy (10 AM ET prior day, entry ≤ $0.35, forecast bin cheapest, prob edge).

NO REAL TRADING — regression guard / checksum export for Console 3.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    default_kalshi_observed_jsonl,
    default_kmia_daily_history_jsonl,
    forecast_high_at_anchor,
    load_ncei_climatology_tmaxes,
    load_settlement_observed_maxes,
    load_settlement_observed_maxes_with_sources,
)
from kalshi_price_history_loader import (
    BIN_OPEN_MAX_MINUTES,
    CANONICAL_BINS,
    DEFAULT_INSURANCE_MODE,
    DEFAULT_ORDER_MODE,
    INSURANCE_BUDGET_FRACTION,
    INSURANCE_MODE_COVER_BOOK,
    INSURANCE_MODE_FRACTION,
    INSURANCE_PRICE_K,
    MAX_ENTRY_YES_ASK,
    MIN_FORECAST_EXECUTABLE_EDGE,
    MIN_INSURANCE_BIN_PROB,
    ORDER_MODE_MAKER_LIMIT,
    ORDER_MODE_TAKER,
    calculate_kalshi_fee,
    cents_to_yes_ask,
    discover_price_history_files,
    evaluate_hedged_open_purchase,
    find_market_bin_for_temp,
    load_anchor_prices_for_date,
    temp_satisfies_bin_label,
    temp_to_bin,
)

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 CHECKSUM ONLY",
}

DEFAULT_ANCHOR_LEAD_MIN = 19
DEFAULT_ANCHOR_LEAD_MAX = 24
DEFAULT_ANCHOR_LEAD_TARGET = 20
DEFAULT_BET_DOLLARS = 5.0


def _allow_iem_mos_backfill() -> bool:
    return os.environ.get("KALSHI_BACKTEST_ALLOW_IEM_MOS", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _resolve_iem_mos_archive(explicit: Optional[Path]) -> Optional[Path]:
    if not _allow_iem_mos_backfill():
        return None
    if explicit is not None:
        return explicit
    from iem_mos_forecast_archive import default_iem_mos_archive_path

    return default_iem_mos_archive_path()


def _kalshi_fee(yes_ask: float) -> float:
    return calculate_kalshi_fee(yes_ask)


def _settle_leg(
    *,
    market_bin: str,
    observed_max_f: float,
    yes_ask: float,
    contracts: int,
    fee: Optional[float] = None,
) -> dict[str, Any]:
    """Settle one YES leg against the actual Kalshi market bin."""
    obs_int = int(round(observed_max_f))
    won = temp_satisfies_bin_label(obs_int, market_bin)
    leg_fee = _kalshi_fee(yes_ask) if fee is None else fee
    cost_per = yes_ask + leg_fee
    total_cost = round(contracts * cost_per, 4)
    unit_pnl = (1.0 - cost_per) if won else -cost_per
    return {
        "market_bin": market_bin,
        "observed_settlement_temp_f": obs_int,
        "market_bin_hit": won,
        "trade_result": "WIN" if won else "LOSS",
        "contracts": contracts,
        "limit_price": yes_ask,
        "total_cost": total_cost,
        "simulated_pnl": round(unit_pnl * contracts, 4),
    }


def _settle_hedged_trade(
    *,
    purchase: dict[str, Any],
    observed_max_f: float,
) -> dict[str, Any]:
    """Settle forecast + insurance legs; P&L uses purchased market bins only."""
    obs_int = int(round(observed_max_f))
    legs: list[dict[str, Any]] = []

    forecast_bin = purchase.get("forecast_market_bin")
    forecast_ask = purchase.get("forecast_bin_yes_ask")
    forecast_contracts = int(purchase.get("forecast_contracts") or 0)
    forecast_fee = purchase.get("forecast_fee")
    if forecast_bin and forecast_ask is not None and forecast_contracts > 0:
        legs.append(_settle_leg(
            market_bin=forecast_bin,
            observed_max_f=observed_max_f,
            yes_ask=float(forecast_ask),
            contracts=forecast_contracts,
            fee=forecast_fee,
        ))

    for ins in purchase.get("insurance_legs") or []:
        if ins.get("contracts", 0) <= 0:
            continue
        legs.append(_settle_leg(
            market_bin=ins["market_bin"],
            observed_max_f=observed_max_f,
            yes_ask=float(ins.get("fill_price") or ins["yes_ask"]),
            contracts=int(ins["contracts"]),
            fee=ins.get("fee"),
        ))

    total_deployed = round(sum(l["total_cost"] for l in legs), 4)
    total_pnl = round(sum(l["simulated_pnl"] for l in legs), 4)
    winning = [l["market_bin"] for l in legs if l["market_bin_hit"]]
    insurance_legs = legs[1:] if len(legs) > 1 else []
    insurance_wins = [l for l in insurance_legs if l["market_bin_hit"]]
    insurance_covers_book = any(
        l["simulated_pnl"] + sum(
            x["simulated_pnl"] for x in legs if x["market_bin"] != l["market_bin"]
        ) >= 0
        for l in insurance_wins
    )

    forecast_leg = legs[0] if legs else {}
    return {
        "observed_settlement_temp_f": obs_int,
        "winning_market_bins": winning,
        "forecast_leg": forecast_leg,
        "insurance_legs": insurance_legs,
        "all_legs": legs,
        "total_deployed": total_deployed,
        "simulated_pnl": total_pnl,
        "trade_result": "WIN" if total_pnl > 0 else ("LOSS" if total_pnl < 0 else "FLAT"),
        "insurance_covers_book": insurance_covers_book,
        "n_insurance_legs": len(insurance_legs),
    }


def _settle_market_bin_trade(
    *,
    market_bin: str,
    observed_max_f: float,
    yes_ask: float,
    bet_dollars: float = DEFAULT_BET_DOLLARS,
) -> dict[str, Any]:
    """Legacy single-leg settle (forecast only, sized from budget)."""
    fee = _kalshi_fee(yes_ask)
    cost_per = yes_ask + fee
    contracts = max(1, int(bet_dollars / cost_per)) if cost_per > 0 else 1
    leg = _settle_leg(
        market_bin=market_bin,
        observed_max_f=observed_max_f,
        yes_ask=yes_ask,
        contracts=contracts,
    )
    return {
        "purchased_market_bin": market_bin,
        "observed_settlement_temp_f": leg["observed_settlement_temp_f"],
        "market_bin_hit": leg["market_bin_hit"],
        "trade_result": leg["trade_result"],
        "recommended_contracts": leg["contracts"],
        "recommended_dollars": leg["total_cost"],
        "limit_price": yes_ask,
        "simulated_pnl": leg["simulated_pnl"],
    }


def _ensure_within_columns(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "within_0f" not in work.columns:
        work["within_0f"] = (
            work["forecast_temp_f"].round() == work["observed_max_f"].round()
        )
    for tol in (1, 2, 3):
        col = f"within_{tol}f"
        if col not in work.columns:
            work[col] = work["abs_error_f"] <= tol
    return work


def select_anchor_row(
    day_df: pd.DataFrame,
    *,
    lead_min: int = DEFAULT_ANCHOR_LEAD_MIN,
    lead_max: int = DEFAULT_ANCHOR_LEAD_MAX,
    lead_target: int = DEFAULT_ANCHOR_LEAD_TARGET,
) -> Optional[pd.Series]:
    if day_df.empty:
        return None
    if "lead_hour_bucket" not in day_df.columns:
        return day_df.iloc[0]
    in_window = day_df[
        (day_df["lead_hour_bucket"] >= lead_min)
        & (day_df["lead_hour_bucket"] <= lead_max)
    ]
    pool = in_window if not in_window.empty else day_df
    idx = (pool["lead_hour_bucket"] - lead_target).abs().idxmin()
    return pool.loc[idx]


def evaluate_day(
    anchor: pd.Series,
    *,
    price_snapshot: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Checksum one settlement day from its anchor release row."""
    target_date = str(anchor["target_date_et"])
    forecast_temp = float(anchor["forecast_temp_f"])
    has_observed = pd.notna(anchor.get("observed_max_f"))
    observed_max = float(anchor["observed_max_f"]) if has_observed else None
    abs_error = (
        abs(forecast_temp - observed_max) if observed_max is not None else None
    )

    forecast_bin = temp_to_bin(int(round(forecast_temp)))
    observed_bin = (
        temp_to_bin(int(round(observed_max))) if observed_max is not None else None
    )

    tolerance_checks: dict[str, bool] = {}
    tolerance_mismatches: list[str] = []
    if observed_max is not None and abs_error is not None:
        for tol in (0, 1, 2, 3):
            col = f"within_{tol}f"
            if tol == 0:
                expected = abs(round(forecast_temp) - round(observed_max)) == 0
            else:
                expected = abs_error <= tol
            if col in anchor.index and pd.notna(anchor[col]):
                csv_val = bool(anchor[col])
                tolerance_checks[col] = csv_val
                if csv_val != expected:
                    tolerance_mismatches.append(col)
            else:
                tolerance_checks[col] = expected

    checksum_failures: list[str] = []
    if observed_bin is not None and forecast_bin != observed_bin:
        checksum_failures.append("forecast_bin_vs_observed_bin")
    checksum_failures.extend(f"csv_{c}_mismatch" for c in tolerance_mismatches)

    market: dict[str, Any] = {
        "price_source": "none",
        "bin_prices_cents": {},
        "forecast_bin_cheapest_at_open": None,
        "entry_within_cap": None,
        "open_purchase_eligible": None,
        "market_checksum_failures": [],
    }

    if price_snapshot and price_snapshot.get("found"):
        prices = price_snapshot.get("bin_prices_cents", {})
        market_bin = price_snapshot.get("forecast_market_bin")
        if market_bin is None:
            column_map = price_snapshot.get("column_map", {})
            market_bin = find_market_bin_for_temp(int(round(forecast_temp)), column_map)

        market["price_source"] = "kalshi_price_history"
        market["bin_prices_cents"] = prices
        market["market_bins"] = price_snapshot.get("market_bins", list(prices.keys()))
        market["forecast_market_bin"] = market_bin
        market["research_bin"] = forecast_bin
        market["matched_timestamp_utc"] = price_snapshot.get("matched_timestamp_utc")
        market["delta_minutes_from_open"] = price_snapshot.get("delta_minutes_from_anchor")
        market["source_file"] = price_snapshot.get("source_file")
        market["max_entry_yes_ask"] = MAX_ENTRY_YES_ASK
        order_mode = price_snapshot.get("order_mode", DEFAULT_ORDER_MODE)
        market["order_mode"] = order_mode

        purchase = price_snapshot.get("hedged_open_purchase") or price_snapshot.get("open_purchase")
        if purchase is None and market_bin:
            purchase = evaluate_hedged_open_purchase(
                prices,
                market_bin,
                forecast_temp,
                market.get("market_bins", list(prices.keys())),
                order_mode=order_mode,
                price_df=price_snapshot.get("price_df"),
                settlement_date=target_date,
                anchor_book=price_snapshot.get("_anchor_orderbook"),
                anchor_candle=price_snapshot.get("_anchor_candle"),
            )

        if purchase:
            market.update({
                "order_mode": purchase.get("order_mode", order_mode),
                "forecast_bin_cheapest_at_open": purchase["forecast_bin_cheapest_at_open"],
                "entry_within_cap": purchase["entry_within_cap"],
                "open_purchase_eligible": purchase["open_purchase_eligible"],
                "hedged_open_eligible": purchase.get("hedged_open_eligible"),
                "order_posted": purchase.get("order_posted"),
                "forecast_filled": purchase.get("forecast_filled"),
                "forecast_limit_bid": purchase.get("forecast_limit_bid"),
                "forecast_bin_yes_ask": purchase.get("forecast_bin_yes_ask"),
                "model_probability": purchase.get("model_probability"),
                "bin_probabilities": purchase.get("bin_probabilities"),
                "executable_edge": purchase.get("executable_edge"),
                "prob_aligned": purchase.get("prob_aligned"),
                "min_bins_at_open": purchase.get("min_bins_at_open"),
                "forecast_contracts": purchase.get("forecast_contracts"),
                "forecast_total_cost": purchase.get("forecast_total_cost"),
                "forecast_fee": purchase.get("forecast_fee"),
                "fill_timestamp_utc": purchase.get("fill_timestamp_utc"),
                "fill_source": purchase.get("fill_source"),
                "insurance_legs": purchase.get("insurance_legs", []),
                "insurance_budget_cap": purchase.get("insurance_budget_cap"),
                "insurance_total_cost": purchase.get("insurance_total_cost"),
                "total_deployed": purchase.get("total_deployed"),
            })
            if purchase.get("order_mode") != ORDER_MODE_MAKER_LIMIT:
                if not purchase["forecast_bin_cheapest_at_open"]:
                    market["market_checksum_failures"].append("forecast_bin_not_cheapest_at_open")
            if not purchase["entry_within_cap"]:
                market["market_checksum_failures"].append("entry_above_cap")
            if not purchase["prob_aligned"]:
                market["market_checksum_failures"].append("prob_not_aligned")
            if purchase.get("order_posted") and not purchase.get("forecast_filled"):
                if purchase.get("order_mode") == ORDER_MODE_MAKER_LIMIT:
                    market["market_checksum_failures"].append("limit_not_filled")
        elif not market_bin:
            market["market_checksum_failures"].append("forecast_temp_not_in_market_bins")
            checksum_failures.append("forecast_temp_not_in_market_bins")
        else:
            market["market_checksum_failures"].append("forecast_bin_unpriced_at_open")

    trade: dict[str, Any] = {}
    if market.get("open_purchase_eligible") and observed_max is not None:
        trade = _settle_hedged_trade(
            purchase={
                "forecast_market_bin": market.get("forecast_market_bin"),
                "forecast_bin_yes_ask": market.get("forecast_bin_yes_ask"),
                "forecast_contracts": market.get("forecast_contracts"),
                "insurance_legs": market.get("insurance_legs", []),
            },
            observed_max_f=observed_max,
        )

    return {
        "target_date_et": target_date,
        "anchor_lead_hour_bucket": int(anchor.get("lead_hour_bucket", 0)),
        "anchor_release_time_et": str(anchor.get("release_time_et", "")),
        "forecast_temp_f": round(forecast_temp, 2),
        "observed_max_f": round(observed_max, 2) if observed_max is not None else None,
        "abs_error_f": round(abs_error, 2) if abs_error is not None else None,
        "forecast_bin": forecast_bin,
        "observed_bin": observed_bin,
        "forecast_bin_hit": (
            forecast_bin == observed_bin if observed_bin is not None else None
        ),
        "tolerance": tolerance_checks,
        "checksum_failures": checksum_failures,
        "market": market,
        "trade": trade,
    }


def aggregate_hit_rates(daily: list[dict[str, Any]]) -> dict[str, float]:
    if not daily:
        return {f"pct_within_{t}f": 0.0 for t in (0, 1, 2, 3)}
    n = len(daily)
    out: dict[str, float] = {}
    for tol in (0, 1, 2, 3):
        col = f"within_{tol}f"
        hits = sum(1 for d in daily if d.get("tolerance", {}).get(col))
        out[f"pct_within_{tol}f"] = round(100.0 * hits / n, 1)
    hits = [d for d in daily if d.get("forecast_bin_hit") is True]
    eligible = [d for d in daily if d.get("forecast_bin_hit") is not None]
    out["forecast_bin_hit_rate"] = round(
        100.0 * len(hits) / len(eligible), 1
    ) if eligible else 0.0
    priced = [d for d in daily if d.get("market", {}).get("price_source") == "kalshi_price_history"]
    if priced:
        eligible = [d for d in priced if d.get("market", {}).get("open_purchase_eligible") is not None]
        if eligible:
            out["open_purchase_eligible_rate"] = round(
                100.0 * sum(1 for d in eligible if d["market"]["open_purchase_eligible"]) / len(eligible),
                1,
            )
            out["forecast_bin_cheapest_at_open_rate"] = round(
                100.0
                * sum(1 for d in eligible if d["market"].get("forecast_bin_cheapest_at_open"))
                / len(eligible),
                1,
            )
            out["entry_within_cap_rate"] = round(
                100.0 * sum(1 for d in eligible if d["market"].get("entry_within_cap")) / len(eligible),
                1,
            )
        out["days_with_kalshi_prices"] = len(priced)
    return out


def _build_anchor_from_sources(
    settlement_date: str,
    *,
    forecast_temp_f: float,
    observed_max_f: Optional[float],
    forecast_source: str,
    observed_source: str,
) -> pd.Series:
    obs = observed_max_f if observed_max_f is not None else float("nan")
    abs_err = abs(forecast_temp_f - obs) if observed_max_f is not None else float("nan")
    return pd.Series({
        "target_date_et": settlement_date,
        "release_time_et": "",
        "forecast_temp_f": forecast_temp_f,
        "observed_max_f": obs,
        "abs_error_f": abs_err,
        "lead_hour_bucket": DEFAULT_ANCHOR_LEAD_TARGET,
        "forecast_source": forecast_source,
        "observed_source": observed_source,
    })


def run_kalshi_price_backtest(
    *,
    price_history_dir: Path,
    nws_dir: Optional[Path] = None,
    forecast_reports_dir: Optional[Path] = None,
    observed_jsonl: Optional[Path] = None,
    ncei_history_jsonl: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    enriched_csv: Optional[Path] = None,
    use_enriched_forecast: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_dir: Optional[Path] = None,
    order_mode: str = DEFAULT_ORDER_MODE,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
    insurance_enabled: bool = True,
    insurance_mode: str = DEFAULT_INSURANCE_MODE,
    insurance_budget_fraction: float = INSURANCE_BUDGET_FRACTION,
    insurance_price_k: float = INSURANCE_PRICE_K,
    min_forecast_edge: float = MIN_FORECAST_EXECUTABLE_EDGE,
) -> dict[str, Any]:
    """Backtest all Kalshi price-history settlement days with NWS forecast/observed joins."""
    price_history_dir = Path(price_history_dir)
    if not price_history_dir.is_dir():
        raise FileNotFoundError(f"Price history dir not found: {price_history_dir}")

    price_files = discover_price_history_files(price_history_dir)
    days = sorted(price_files.keys())
    if start_date:
        days = [d for d in days if d >= start_date]
    if end_date:
        days = [d for d in days if d <= end_date]

    observed_map, observed_sources = load_settlement_observed_maxes_with_sources(
        ncei_history_jsonl=ncei_history_jsonl,
    )
    enriched_df: Optional[pd.DataFrame] = None
    if use_enriched_forecast and enriched_csv and Path(enriched_csv).is_file():
        enriched_df = pd.read_csv(enriched_csv)
        enriched_df["target_date_et"] = enriched_df["target_date_et"].astype(str)
        enriched_df = _ensure_within_columns(enriched_df)

    ins_fraction = insurance_budget_fraction if insurance_enabled else 0.0

    daily_results: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    n_days_with_anchor_orderbook = 0
    n_days_with_anchor_candle = 0

    for day in days:
        forecast_temp: Optional[float] = None
        observed_max: Optional[float] = None
        forecast_source = "none"
        observed_source = "none"

        if enriched_df is not None:
            day_df = enriched_df[enriched_df["target_date_et"] == day]
            anchor_row = select_anchor_row(day_df) if not day_df.empty else None
            if anchor_row is not None:
                forecast_temp = float(anchor_row["forecast_temp_f"])
                forecast_source = "ndfd_enriched_csv"

        if forecast_temp is None:
            fc = forecast_high_at_anchor(
                day,
                nws_dir=nws_dir,
                reports_dir=forecast_reports_dir,
                iem_mos_archive=iem_mos_archive,
                allow_iem_mos=_allow_iem_mos_backfill(),
            )
            if fc.get("found"):
                forecast_temp = float(fc["forecast_temp_f"])
                forecast_source = str(fc.get("source") or "unknown")

        if observed_max is None and day in observed_map:
            observed_max = observed_map[day]
            observed_source = observed_sources.get(day, "ncei_climatology")

        price_snapshot = load_anchor_prices_for_date(
            price_history_dir, day,
            forecast_temp_f=forecast_temp if forecast_temp is not None else None,
            order_mode=order_mode,
            orderbook_archive_dir=orderbook_archive_dir,
            candle_archive_dir=candle_archive_dir,
            min_forecast_edge=min_forecast_edge,
            insurance_budget_fraction=ins_fraction,
            insurance_price_k=insurance_price_k,
            insurance_mode=insurance_mode if insurance_enabled else INSURANCE_MODE_FRACTION,
        )
        if not price_snapshot.get("found"):
            skipped.append({"day": day, "reason": "no_anchor_prices"})
            continue

        book_meta = price_snapshot.get("anchor_orderbook") or {}
        if book_meta.get("found"):
            n_days_with_anchor_orderbook += 1
        candle_meta = price_snapshot.get("anchor_candle") or {}
        if candle_meta.get("found"):
            n_days_with_anchor_candle += 1

        if forecast_temp is None:
            obs = observed_map.get(day)
            obs_src = observed_sources.get(day, "none") if obs is not None else "none"
            # Market-only day: still record Kalshi bin costs at anchor.
            prices = price_snapshot.get("bin_prices_cents", {})
            valid = {b: p for b, p in prices.items() if p is not None}
            max_bins = (
                [b for b, p in valid.items() if p == max(valid.values())]
                if valid else []
            )
            daily_results.append({
                "target_date_et": day,
                "forecast_temp_f": None,
                "forecast_source": "none",
                "observed_source": obs_src,
                "observed_max_f": obs,
                "forecast_bin_hit": None,
                "checksum_failures": [],
                "market": {
                    "price_source": "kalshi_price_history",
                    "bin_prices_cents": prices,
                    "market_bins": price_snapshot.get("market_bins", list(prices.keys())),
                    "market_favorite_bins": max_bins,
                    "matched_timestamp_utc": price_snapshot.get("matched_timestamp_utc"),
                    "source_file": price_snapshot.get("source_file"),
                    "open_purchase_eligible": None,
                    "note": "no_forecast_source_for_validation",
                },
            })
            skipped.append({"day": day, "reason": "no_forecast_market_only"})
            continue

        anchor = _build_anchor_from_sources(
            day,
            forecast_temp_f=forecast_temp,
            observed_max_f=observed_max,
            forecast_source=forecast_source,
            observed_source=observed_source,
        )
        result = evaluate_day(anchor, price_snapshot=price_snapshot)
        result["forecast_source"] = forecast_source
        result["observed_source"] = observed_source
        if book_meta.get("found"):
            result.setdefault("market", {})["anchor_orderbook"] = book_meta
        if candle_meta.get("found"):
            result.setdefault("market", {})["anchor_candle"] = candle_meta
        daily_results.append(result)

    all_failures = [
        {"target_date_et": d["target_date_et"], "failures": d["checksum_failures"]}
        for d in daily_results if d["checksum_failures"]
    ]
    market_failures = [
        d for d in daily_results if d.get("market", {}).get("market_checksum_failures")
    ]
    with_observed = [d for d in daily_results if d.get("observed_max_f") is not None]
    hit_rates = aggregate_hit_rates(with_observed) if with_observed else {}
    priced = [d for d in daily_results if d.get("market", {}).get("price_source") == "kalshi_price_history"]
    if priced:
        hit_rates["days_with_kalshi_prices"] = len(priced)
        validated = [d for d in priced if d.get("market", {}).get("open_purchase_eligible") is not None]
        if validated:
            hit_rates["open_purchase_eligible_rate"] = round(
                100.0 * sum(1 for d in validated if d["market"]["open_purchase_eligible"]) / len(validated),
                1,
            )
            hit_rates["forecast_bin_cheapest_at_open_rate"] = round(
                100.0
                * sum(1 for d in validated if d["market"].get("forecast_bin_cheapest_at_open"))
                / len(validated),
                1,
            )
            hit_rates["entry_within_cap_rate"] = round(
                100.0 * sum(1 for d in validated if d["market"].get("entry_within_cap")) / len(validated),
                1,
            )
        traded = [
            d for d in daily_results
            if d.get("market", {}).get("open_purchase_eligible")
        ]
        if traded:
            hit_rates["n_traded_days"] = len(traded)
            settled = [d for d in traded if d.get("trade")]
            if settled:
                hit_rates["hedged_win_rate"] = round(
                    100.0
                    * sum(1 for d in settled if d["trade"].get("trade_result") == "WIN")
                    / len(settled),
                    1,
                )
                hit_rates["avg_insurance_legs"] = round(
                    sum(d["trade"].get("n_insurance_legs", 0) for d in settled) / len(settled),
                    2,
                )
                hit_rates["total_simulated_pnl"] = round(
                    sum(d["trade"].get("simulated_pnl", 0) for d in settled),
                    2,
                )
                hit_rates["total_deployed"] = round(
                    sum(d["trade"].get("total_deployed", 0) for d in settled),
                    4,
                )
                total_pnl = hit_rates["total_simulated_pnl"]
                total_dep = hit_rates["total_deployed"]
                hit_rates["roi_pct"] = round(
                    100.0 * total_pnl / total_dep, 2
                ) if total_dep else 0.0
                covers = sum(
                    1 for d in settled if d["trade"].get("insurance_covers_book")
                )
                hit_rates["insurance_covers_book_rate"] = round(
                    100.0 * covers / len(settled), 1
                )

    fill_sources: dict[str, int] = {}
    for d in daily_results:
        market = d.get("market") or {}
        src = market.get("fill_source")
        if src:
            fill_sources[src] = fill_sources.get(src, 0) + 1
    if fill_sources:
        hit_rates["maker_fill_sources"] = fill_sources

    from kalshi_orderbook_archive_loader import default_orderbook_archive_dir
    from kalshi_candle_archive_loader import default_candle_archive_dir

    resolved_orderbook_archive = orderbook_archive_dir or default_orderbook_archive_dir()
    resolved_candle_archive = candle_archive_dir or default_candle_archive_dir()

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "mode": "kalshi_price_primary",
        "price_history_dir": str(price_history_dir.resolve()),
        "orderbook_archive_dir": (
            str(Path(resolved_orderbook_archive).resolve())
            if resolved_orderbook_archive else None
        ),
        "n_days_with_anchor_orderbook": n_days_with_anchor_orderbook,
        "n_days_with_anchor_candle": n_days_with_anchor_candle,
        "candle_archive_dir": (
            str(Path(resolved_candle_archive).resolve())
            if resolved_candle_archive else None
        ),
        "nws_dir": str(nws_dir) if nws_dir else None,
        "forecast_reports_dir": str(forecast_reports_dir) if forecast_reports_dir else None,
        "observed_jsonl": str(observed_jsonl) if observed_jsonl else None,
        "ncei_history_jsonl": str(ncei_history_jsonl) if ncei_history_jsonl else None,
        "iem_mos_archive": str(iem_mos_archive) if iem_mos_archive else None,
        "enriched_csv": str(enriched_csv) if enriched_csv and use_enriched_forecast else None,
        "use_enriched_forecast": use_enriched_forecast,
        "date_range": {"start": days[0] if days else None, "end": days[-1] if days else None},
        "kalshi_anchor_config": {
            "hour_et": 10,
            "max_minutes_after_open": BIN_OPEN_MAX_MINUTES,
            "max_entry_yes_ask": MAX_ENTRY_YES_ASK,
            "min_forecast_executable_edge": min_forecast_edge,
            "insurance_enabled": insurance_enabled,
            "insurance_mode": insurance_mode if insurance_enabled else None,
            "insurance_budget_fraction": ins_fraction,
            "insurance_price_k": insurance_price_k,
            "min_insurance_bin_prob": MIN_INSURANCE_BIN_PROB,
            "order_mode": order_mode,
            "forecast_join": (
                "ndfd_enriched_csv" if use_enriched_forecast
                else "kalshi_nws_join_10am"
            ),
            "settlement_observed": "ncei_climatology",
            "description": (
                f"Prior-day 10 AM ET — post limit bids (maker) or take asks (taker); "
                f"forecast leg ≤ ${MAX_ENTRY_YES_ASK:.2f} with {MIN_FORECAST_EXECUTABLE_EDGE:.0%} edge; "
                "insurance prob-weighted at k×P(bin)"
            ),
            "selection": (
                "maker_limit: post P−edge bid, fill when ask ≤ bid; "
                "taker: first tick within 5 minutes of bin open"
            ),
        },
        "n_price_history_files": len(price_files),
        "n_days_tested": len(daily_results),
        "n_days_skipped": len(skipped),
        "skipped": skipped[:50],
        "hit_rates": hit_rates,
        "checksum_failures": {"count": len(all_failures), "failure_days": all_failures[:100]},
        "market_validation": {
            "days_with_kalshi_prices": hit_rates.get("days_with_kalshi_prices", 0),
            "open_purchase_eligible_rate": hit_rates.get("open_purchase_eligible_rate"),
            "forecast_bin_cheapest_at_open_rate": hit_rates.get("forecast_bin_cheapest_at_open_rate"),
            "entry_within_cap_rate": hit_rates.get("entry_within_cap_rate"),
            "open_purchase_failures": len(market_failures),
            "failure_days": [
                {
                    "target_date_et": d["target_date_et"],
                    "forecast_temp_f": d["forecast_temp_f"],
                    "market": d["market"],
                }
                for d in market_failures[:50]
            ],
        },
        "daily_results": daily_results,
        "human_summary": _format_kalshi_summary(
            n_tested=len(daily_results),
            n_skipped=len(skipped),
            n_files=len(price_files),
            hit_rates=hit_rates,
            market_failures=len(market_failures),
            with_observed=len(with_observed),
            n_days_with_anchor_orderbook=n_days_with_anchor_orderbook,
            n_days_with_anchor_candle=n_days_with_anchor_candle,
        ),
    }

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = out_dir / f"kalshi_price_backtest_{ts}.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(out_path)

    return report


def _hit_rate_summary(report: dict[str, Any]) -> dict[str, Any]:
    hr = report.get("hit_rates") or {}
    return {
        "n_traded_days": hr.get("n_traded_days"),
        "hedged_win_rate": hr.get("hedged_win_rate"),
        "total_simulated_pnl": hr.get("total_simulated_pnl"),
        "open_purchase_eligible_rate": hr.get("open_purchase_eligible_rate"),
    }


def _latest_backtest_summary(
    output_dir: Path,
    order_mode: str,
) -> Optional[dict[str, Any]]:
    """Load hit-rate summary from newest saved backtest with matching order_mode."""
    out_dir = Path(output_dir)
    if not out_dir.is_dir():
        return None
    candidates = sorted(out_dir.glob("kalshi_price_backtest_*.json"), reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cfg = payload.get("kalshi_anchor_config") or {}
        if cfg.get("order_mode") == order_mode:
            summary = _hit_rate_summary(payload)
            summary["source_report"] = str(path)
            return summary
    return None


def write_dual_mode_comparison(
    *,
    price_history_dir: Path,
    output_dir: Path,
    nws_dir: Optional[Path] = None,
    forecast_reports_dir: Optional[Path] = None,
    observed_jsonl: Optional[Path] = None,
    ncei_history_jsonl: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    enriched_csv: Optional[Path] = None,
    use_enriched_forecast: bool = False,
    reuse_maker_from_dir: Optional[Path] = None,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Run taker + maker backtests and write side-by-side summary."""
    summaries: dict[str, Any] = {}

    maker_cached = (
        _latest_backtest_summary(Path(reuse_maker_from_dir), ORDER_MODE_MAKER_LIMIT)
        if reuse_maker_from_dir else None
    )
    if maker_cached:
        summaries[ORDER_MODE_MAKER_LIMIT] = {
            k: maker_cached[k]
            for k in (
                "n_traded_days",
                "hedged_win_rate",
                "total_simulated_pnl",
                "open_purchase_eligible_rate",
            )
        }
        summaries[ORDER_MODE_MAKER_LIMIT]["reused_report"] = maker_cached.get("source_report")
    else:
        r = run_kalshi_price_backtest(
            price_history_dir=price_history_dir,
            nws_dir=nws_dir,
            forecast_reports_dir=forecast_reports_dir,
            observed_jsonl=observed_jsonl,
            ncei_history_jsonl=ncei_history_jsonl,
            iem_mos_archive=iem_mos_archive,
            enriched_csv=enriched_csv,
            use_enriched_forecast=use_enriched_forecast,
            output_dir=None,
            order_mode=ORDER_MODE_MAKER_LIMIT,
            orderbook_archive_dir=orderbook_archive_dir,
            candle_archive_dir=candle_archive_dir,
        )
        summaries[ORDER_MODE_MAKER_LIMIT] = _hit_rate_summary(r)

    r_taker = run_kalshi_price_backtest(
        price_history_dir=price_history_dir,
        nws_dir=nws_dir,
        forecast_reports_dir=forecast_reports_dir,
        observed_jsonl=observed_jsonl,
        ncei_history_jsonl=ncei_history_jsonl,
        iem_mos_archive=iem_mos_archive,
        enriched_csv=enriched_csv,
        use_enriched_forecast=use_enriched_forecast,
        output_dir=None,
        order_mode=ORDER_MODE_TAKER,
        orderbook_archive_dir=orderbook_archive_dir,
        candle_archive_dir=candle_archive_dir,
    )
    summaries[ORDER_MODE_TAKER] = _hit_rate_summary(r_taker)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "comparison": summaries,
        "maker_taker_ab": {
            "taker": summaries.get(ORDER_MODE_TAKER),
            "maker_limit": summaries.get(ORDER_MODE_MAKER_LIMIT),
            "note": "Same signals; taker crosses at ask, maker posts limit until dynamic window end",
        },
        "note": "Low observed sample — compare modes directionally only until n_trades ≥ 20",
    }
    ab_path = output_dir / "maker_taker_ab.json"
    ab_path.write_text(json.dumps(payload["maker_taker_ab"], indent=2), encoding="utf-8")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "dual_mode_comparison.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["output_path"] = str(path)
    return payload


def _format_kalshi_summary(
    *,
    n_tested: int,
    n_skipped: int,
    n_files: int,
    hit_rates: dict[str, float],
    market_failures: int,
    with_observed: int,
    n_days_with_anchor_orderbook: int = 0,
    n_days_with_anchor_candle: int = 0,
) -> str:
    parts = [
        f"Kalshi price backtest: {n_tested} days from {n_files} price-history files ({n_skipped} without forecast validation).",
    ]
    if n_days_with_anchor_orderbook:
        parts.append(
            f"Archived orderbook at anchor: {n_days_with_anchor_orderbook} day(s)."
        )
    if n_days_with_anchor_candle:
        parts.append(
            f"Archived candles at anchor: {n_days_with_anchor_candle} day(s)."
        )
    fill_sources = hit_rates.get("maker_fill_sources") or {}
    if fill_sources:
        src_bits = ", ".join(f"{k}={v}" for k, v in sorted(fill_sources.items()))
        parts.append(f"Maker fill sources: {src_bits}.")
    if hit_rates.get("days_with_kalshi_prices"):
        parts.append(
            f"Bin-open purchase eligible: {hit_rates.get('open_purchase_eligible_rate', 0):.1f}% "
            f"(cheapest {hit_rates.get('forecast_bin_cheapest_at_open_rate', 0):.1f}%, "
            f"≤${MAX_ENTRY_YES_ASK:.2f} {hit_rates.get('entry_within_cap_rate', 0):.1f}%)."
        )
    if with_observed:
        parts.append(
            f"Observed join: {with_observed} days; forecast bin hit rate {hit_rates.get('forecast_bin_hit_rate', 0):.1f}%."
        )
    return " ".join(parts)


def run_checksum_backtest(
    *,
    csv_path: Path,
    price_history_dir: Optional[Path] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sample: Optional[int] = None,
    output_dir: Optional[Path] = None,
    seed: int = 42,
    order_mode: str = DEFAULT_ORDER_MODE,
) -> dict[str, Any]:
    """Run checksum backtest and write JSON report."""
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Enriched CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df = _ensure_within_columns(df)
    df["target_date_et"] = df["target_date_et"].astype(str)

    if start_date:
        df = df[df["target_date_et"] >= start_date]
    if end_date:
        df = df[df["target_date_et"] <= end_date]

    unique_days = sorted(df["target_date_et"].unique())
    if sample is not None and sample > 0 and len(unique_days) > sample:
        rng = random.Random(seed)
        unique_days = sorted(rng.sample(unique_days, sample))

    daily_results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for day in unique_days:
        day_df = df[df["target_date_et"] == day]
        anchor = select_anchor_row(day_df)
        if anchor is None:
            skipped.append(day)
            continue

        price_snapshot = None
        if price_history_dir is not None:
            anchor_temp = float(anchor["forecast_temp_f"])
            price_snapshot = load_anchor_prices_for_date(
                price_history_dir, day, forecast_temp_f=anchor_temp, order_mode=order_mode
            )

        daily_results.append(evaluate_day(anchor, price_snapshot=price_snapshot))

    all_failures: list[dict[str, Any]] = []
    for d in daily_results:
        if d["checksum_failures"]:
            all_failures.append({
                "target_date_et": d["target_date_et"],
                "failures": d["checksum_failures"],
                "forecast_bin": d["forecast_bin"],
                "observed_bin": d["observed_bin"],
            })

    hit_rates = aggregate_hit_rates(daily_results)
    market_failures = [
        d for d in daily_results
        if d.get("market", {}).get("market_checksum_failures")
    ]

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "source_csv": str(csv_path.resolve()),
        "price_history_dir": str(price_history_dir) if price_history_dir else None,
        "date_range": {
            "start": start_date or (unique_days[0] if unique_days else None),
            "end": end_date or (unique_days[-1] if unique_days else None),
        },
        "kalshi_anchor_config": {
            "hour_et": 10,
            "max_minutes_after_open": BIN_OPEN_MAX_MINUTES,
            "max_entry_yes_ask": MAX_ENTRY_YES_ASK,
            "min_forecast_executable_edge": MIN_FORECAST_EXECUTABLE_EDGE,
            "insurance_budget_fraction": INSURANCE_BUDGET_FRACTION,
            "insurance_price_k": INSURANCE_PRICE_K,
            "min_insurance_bin_prob": MIN_INSURANCE_BIN_PROB,
            "order_mode": order_mode,
            "description": (
                f"Prior-day 10 AM ET — post limit bids (maker) or take asks (taker); "
                f"forecast leg ≤ ${MAX_ENTRY_YES_ASK:.2f} with {MIN_FORECAST_EXECUTABLE_EDGE:.0%} edge; "
                "insurance prob-weighted at k×P(bin)"
            ),
            "selection": (
                "maker_limit: post P−edge bid, fill when ask ≤ bid; "
                "taker: first tick within 5 minutes of bin open"
            ),
        },
        "ndfd_anchor_config": {
            "lead_hour_min": DEFAULT_ANCHOR_LEAD_MIN,
            "lead_hour_max": DEFAULT_ANCHOR_LEAD_MAX,
            "lead_hour_target": DEFAULT_ANCHOR_LEAD_TARGET,
            "description": "NDFD enriched CSV: prior-day ~4 PM ET via lead_hour_bucket 19–24h",
        },
        "canonical_bins": list(CANONICAL_BINS),
        "n_days_tested": len(daily_results),
        "n_days_skipped": len(skipped),
        "hit_rates": hit_rates,
        "checksum_failures": {
            "count": len(all_failures),
            "failure_days": all_failures[:100],
        },
        "market_validation": {
            "days_with_kalshi_prices": hit_rates.get("days_with_kalshi_prices", 0),
            "open_purchase_eligible_rate": hit_rates.get("open_purchase_eligible_rate"),
            "forecast_bin_cheapest_at_open_rate": hit_rates.get("forecast_bin_cheapest_at_open_rate"),
            "entry_within_cap_rate": hit_rates.get("entry_within_cap_rate"),
            "open_purchase_failures": len(market_failures),
            "failure_days": [
                {
                    "target_date_et": d["target_date_et"],
                    "forecast_bin": d["forecast_bin"],
                    "market": d["market"],
                }
                for d in market_failures[:50]
            ],
        },
        "daily_results": daily_results,
        "human_summary": _format_human_summary(
            n_days=len(daily_results),
            hit_rates=hit_rates,
            failure_count=len(all_failures),
            market_failures=len(market_failures),
        ),
    }

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = out_dir / f"historical_checksum_{ts}.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(out_path)

    return report


def _format_human_summary(
    *,
    n_days: int,
    hit_rates: dict[str, float],
    failure_count: int,
    market_failures: int,
) -> str:
    parts = [
        f"Historical checksum: {n_days} settlement days.",
        (
            f"Tolerance hit rates: ±0°F {hit_rates.get('pct_within_0f', 0):.1f}%, "
            f"±1°F {hit_rates.get('pct_within_1f', 0):.1f}%, "
            f"±2°F {hit_rates.get('pct_within_2f', 0):.1f}%, "
            f"±3°F {hit_rates.get('pct_within_3f', 0):.1f}%."
        ),
        f"Forecast bin hit rate: {hit_rates.get('forecast_bin_hit_rate', 0):.1f}%.",
        f"Checksum failure days (bin/tolerance mismatch): {failure_count}.",
    ]
    if hit_rates.get("days_with_kalshi_prices"):
        parts.append(
            f"Kalshi-priced days: {int(hit_rates['days_with_kalshi_prices'])}; "
            f"open purchase eligible: {hit_rates.get('open_purchase_eligible_rate', 0):.1f}%; "
            f"market check failures: {market_failures}."
        )
    return " ".join(parts)


def _default_csv_path() -> Path:
    from kmia_kalshi_paths import console2_enriched_csv

    return console2_enriched_csv()


def _default_price_dir() -> Optional[Path]:
    from kmia_kalshi_paths import kalshi_price_history_dir, optional_existing

    return optional_existing(kalshi_price_history_dir())


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run historical forecast-vs-observed checksum backtest (Console 2)."
    )
    parser.add_argument(
        "--mode",
        choices=("kalshi", "enriched"),
        default="kalshi",
        help="kalshi=iterate price-history files; enriched=iterate accuracy_points_enriched.csv",
    )
    parser.add_argument("--csv", type=Path, default=None, help="Enriched CSV path (enriched mode)")
    parser.add_argument(
        "--price-history-dir",
        type=Path,
        default=None,
        help="Folder with kalshi-price-history-kxhighmia-*.csv files",
    )
    parser.add_argument(
        "--nws-dir",
        type=Path,
        default=None,
        help="Kalshi NWS snapshot dir for forecast join (kalshi mode)",
    )
    parser.add_argument(
        "--forecast-reports-dir",
        type=Path,
        default=None,
        help="Kalshi rules_v2 forecast reports dir (kalshi mode)",
    )
    parser.add_argument(
        "--observed-jsonl",
        type=Path,
        default=None,
        help="NWS observed history JSONL for settlement truth (kalshi mode)",
    )
    parser.add_argument(
        "--ncei-history-jsonl",
        type=Path,
        default=None,
        help="Official NCEI CLIMIA TMAX history (kmia_daily_history.jsonl)",
    )
    parser.add_argument("--start", dest="start_date", default=None)
    parser.add_argument("--end", dest="end_date", default=None)
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--sweep-policy",
        action="store_true",
        help="After kalshi backtest, run policy optimizer + frontier chart",
    )
    parser.add_argument(
        "--order-mode",
        choices=(ORDER_MODE_TAKER, ORDER_MODE_MAKER_LIMIT),
        default=DEFAULT_ORDER_MODE,
        help="taker=hit yes ask at open; maker_limit=post limit bid, fill when ask≤bid",
    )
    parser.add_argument(
        "--dual-report",
        action="store_true",
        help="Write dual_mode_comparison.json (taker vs maker) without saving main report",
    )
    parser.add_argument(
        "--orderbook-archive-dir",
        type=Path,
        default=None,
        help="kalshi_market_archive orderbooks JSONL root for anchor maker-fill replay",
    )
    parser.add_argument(
        "--use-enriched-csv",
        action="store_true",
        help="Use 4 PM MAE enriched CSV for forecast only (kalshi mode; NCEI settlement unchanged)",
    )
    parser.add_argument(
        "--no-enriched-csv",
        action="store_true",
        help="Explicitly disable enriched CSV (default for --mode kalshi)",
    )
    parser.add_argument(
        "--insurance-mode",
        choices=(INSURANCE_MODE_FRACTION, INSURANCE_MODE_COVER_BOOK),
        default=DEFAULT_INSURANCE_MODE,
        help="Insurance sizing: fraction (prob-weighted) or cover_book (dynamic book coverage)",
    )
    parser.add_argument(
        "--no-insurance",
        action="store_true",
        help="Disable insurance legs in kalshi backtest",
    )
    parser.add_argument(
        "--candle-archive-dir",
        type=Path,
        default=None,
        help="kalshi_candle_archive JSONL root for anchor candle fill fallback",
    )
    args = parser.parse_args(argv)

    price_dir = args.price_history_dir or _default_price_dir()
    out_dir = args.output_dir or (
        Path(__file__).resolve().parents[2]
        / "Research"
        / "Agent Analysis of KMIA Forecast Precision"
        / "Kalshi_Price_Backtest"
    )

    ncei_history = args.ncei_history_jsonl or default_kmia_daily_history_jsonl()
    iem_archive = _resolve_iem_mos_archive(None)

    use_enriched = args.use_enriched_csv and not args.no_enriched_csv
    enriched_path: Optional[Path] = None
    if args.mode == "enriched" or use_enriched:
        enriched_path = args.csv or _default_csv_path()

    if args.mode == "kalshi":
        if price_dir is None:
            raise SystemExit("Kalshi mode requires --price-history-dir or default bet history folder.")
        if args.dual_report:
            dual = write_dual_mode_comparison(
                price_history_dir=price_dir,
                output_dir=out_dir,
                nws_dir=args.nws_dir or default_kalshi_nws_dir(),
                forecast_reports_dir=args.forecast_reports_dir or default_kalshi_forecast_reports_dir(),
                observed_jsonl=args.observed_jsonl or default_kalshi_observed_jsonl(),
                ncei_history_jsonl=ncei_history,
                iem_mos_archive=iem_archive,
                enriched_csv=enriched_path,
                use_enriched_forecast=use_enriched,
                reuse_maker_from_dir=out_dir,
                orderbook_archive_dir=args.orderbook_archive_dir,
                candle_archive_dir=args.candle_archive_dir,
            )
            print(f"Dual-mode comparison: {dual['output_path']}")
            return 0
        report = run_kalshi_price_backtest(
            price_history_dir=price_dir,
            nws_dir=args.nws_dir or default_kalshi_nws_dir(),
            forecast_reports_dir=args.forecast_reports_dir or default_kalshi_forecast_reports_dir(),
            observed_jsonl=args.observed_jsonl or default_kalshi_observed_jsonl(),
            ncei_history_jsonl=ncei_history,
            iem_mos_archive=iem_archive,
            enriched_csv=enriched_path,
            use_enriched_forecast=use_enriched,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=out_dir,
            order_mode=args.order_mode,
            orderbook_archive_dir=args.orderbook_archive_dir,
            candle_archive_dir=args.candle_archive_dir,
            insurance_enabled=not args.no_insurance,
            insurance_mode=args.insurance_mode,
        )
    else:
        csv_path = args.csv or _default_csv_path()
        report = run_checksum_backtest(
            csv_path=csv_path,
            price_history_dir=price_dir,
            start_date=args.start_date,
            end_date=args.end_date,
            sample=args.sample,
            output_dir=out_dir,
            seed=args.seed,
            order_mode=args.order_mode,
        )
    print(report["human_summary"])
    if report.get("output_path"):
        print(f"Report written: {report['output_path']}")

    if args.sweep_policy and args.mode == "kalshi" and price_dir is not None:
        from chart_kalshi_policy_frontier import main as chart_main
        from kalshi_policy_optimizer import run_policy_sweep

        sweep = run_policy_sweep(
            price_history_dir=price_dir,
            nws_dir=args.nws_dir or default_kalshi_nws_dir(),
            forecast_reports_dir=args.forecast_reports_dir or default_kalshi_forecast_reports_dir(),
            observed_jsonl=args.observed_jsonl or default_kalshi_observed_jsonl(),
            ncei_history_jsonl=ncei_history,
            iem_mos_archive=iem_archive,
            output_dir=out_dir,
            orderbook_archive_dir=args.orderbook_archive_dir,
            candle_archive_dir=args.candle_archive_dir,
        )
        print(sweep["human_summary"])
        if sweep.get("sweep_path"):
            chart_main(["--sweep-json", sweep["sweep_path"], "--output-dir", str(out_dir)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
