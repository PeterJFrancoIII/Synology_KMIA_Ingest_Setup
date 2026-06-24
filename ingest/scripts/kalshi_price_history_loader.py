#!/usr/bin/env python3
"""Load Kalshi KXHIGHMIA price-history CSV exports into per-event bin costs.

Kalshi uses sliding 6-bin windows per settlement day (not fixed <=78…>=87).
This loader parses each export's column headers dynamically, maps forecast
temperature to the matching market bin, and evaluates bin-open purchase policy
at the prior-day 10 AM ET anchor (forecast leg ≤ $0.35; insurance legs prob-weighted).

NO REAL TRADING — reference data for checksum backtests only.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd

# Fixed bins used by Console 2 MAE research (NDFD integer mapping).
CANONICAL_BINS: tuple[str, ...] = ("<=78", "79-80", "81-82", "83-84", "85-86", ">=87")

# Prior-day 10 AM ET — Kalshi bins become visible and bettable at this time.
ANCHOR_HOUR_ET = 10
# Purchase at the exact open moment (first tick within this many minutes after 10 AM).
BIN_OPEN_MAX_MINUTES = 5
# Standard bot entry cap: buy forecast-favored bin when yes ask ≤ this (dollars).
MAX_ENTRY_YES_ASK = 0.35
MIN_EXECUTABLE_EDGE = 0.05  # legacy alias
MIN_FORECAST_EXECUTABLE_EDGE = 0.18
MIN_INSURANCE_BIN_PROB = 0.10  # exclude bins at or below 10%
INSURANCE_BUDGET_FRACTION = 0.25  # insurance spend ≤ 25% of forecast leg cost (fraction mode)
INSURANCE_PRICE_K = 0.60  # max yes ask = k × P(bin) for insurance legs
INSURANCE_MODE_FRACTION = "fraction"
INSURANCE_MODE_COVER_BOOK = "cover_book"
DEFAULT_INSURANCE_MODE = INSURANCE_MODE_FRACTION
COVER_BOOK_DEFAULT_BUDGET_FRACTION = 1.0  # cover_book: up to 100% of forecast leg by default
DEFAULT_FORECAST_BET_DOLLARS = 5.0
# Thin-market cap when price-history CSV has no order-book depth (Console 2 backtest).
DEFAULT_EVENT_DAILY_VOLUME_USD = 121_000.0
DEFAULT_EVENT_VOLUME_PARTICIPATION = 0.005
DEFAULT_ABS_MAX_CONTRACTS_PER_LEG = 25
DEFAULT_TOP_OF_BOOK_PARTICIPATION = 0.25
FORECAST_MODEL_STD_F = 2.2
MODEL_VERSION = "gaussian_v1_truncation_optional"
ORDER_MODE_TAKER = "taker"
ORDER_MODE_MAKER_LIMIT = "maker_limit"
DEFAULT_ORDER_MODE = ORDER_MODE_MAKER_LIMIT
MIN_LIMIT_BID = 0.01
MAKER_FILL_MAX_HOURS = 36.0

_FILENAME_RE = re.compile(
    r"kalshi-price-history-kxhighmia-(\d{2})([a-z]{3})(\d{2})-(minute|hour)\.csv$",
    re.IGNORECASE,
)

_EVENT_TICKER_RE = re.compile(
    r"^KXHIGHMIA-(\d{2})([A-Z]{3})(\d{2})$",
    re.IGNORECASE,
)

SERIES_TICKER = "KXHIGHMIA"
DEFAULT_KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

_BELOW_RE = re.compile(r"(\d+)\s*(?:°|Â°|deg)?\s*or\s*below", re.I)
_ABOVE_RE = re.compile(r"(\d+)\s*(?:°|Â°|deg)?\s*or\s*above", re.I)
_RANGE_RE = re.compile(
    r"(\d+)\s*(?:°|Â°|deg)?\s*(?:to|through|-)\s*(\d+)\s*(?:°|Â°|deg)?",
    re.I,
)


def temp_to_bin(max_temp_f: int) -> str:
    """Map integer °F high to fixed research probability bin (Console 2 MAE)."""
    if max_temp_f <= 78:
        return "<=78"
    if max_temp_f <= 80:
        return "79-80"
    if max_temp_f <= 82:
        return "81-82"
    if max_temp_f <= 84:
        return "83-84"
    if max_temp_f <= 86:
        return "85-86"
    return ">=87"


def parse_kalshi_column_header(col: str) -> Optional[str]:
    """Parse Kalshi export column header into a bin label (e.g. '79-80', '>=87')."""
    raw = col.strip().replace("\u00b0", "").replace("Â°", "").replace("°", "")
    m = _RANGE_RE.search(raw)
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        return f"{low}-{high}"
    m = _BELOW_RE.search(raw)
    if m:
        return f"<={int(m.group(1))}"
    m = _ABOVE_RE.search(raw)
    if m:
        return f">={int(m.group(1))}"
    return None


def temp_satisfies_bin_label(temp: int, bin_label: str) -> bool:
    """Return True if integer temp falls in the Kalshi bin label."""
    if not bin_label:
        return False
    if bin_label.startswith("<="):
        return temp <= int(bin_label[2:])
    if bin_label.startswith(">="):
        return temp >= int(bin_label[2:])
    if bin_label.startswith("<"):
        return temp < int(bin_label[1:])
    if bin_label.startswith(">"):
        return temp > int(bin_label[1:])
    if "-" in bin_label:
        low, high = bin_label.split("-", 1)
        return int(low) <= temp <= int(high)
    try:
        return temp == int(float(bin_label))
    except ValueError:
        return False


def find_market_bin_for_temp(
    temp_f: int,
    column_to_label: dict[str, str],
) -> Optional[str]:
    """Find which market bin label contains the forecast temperature."""
    for _col, label in column_to_label.items():
        if temp_satisfies_bin_label(temp_f, label):
            return label
    return None


def _column_map_from_headers(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for col in columns:
        if col == "timestamp":
            continue
        label = parse_kalshi_column_header(col)
        if label:
            mapping[col] = label
    return mapping


def settlement_date_from_path(path: Path) -> Optional[str]:
    m = _FILENAME_RE.search(path.name)
    if not m:
        return None
    yy, mon, dd = m.group(1), m.group(2), m.group(3)
    try:
        dt = datetime.strptime(f"{dd}{mon}{yy}", "%d%b%y")
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%d")


def export_filename_for_settlement(
    settlement_date: str,
    *,
    granularity: str = "minute",
) -> str:
    """Canonical Kalshi price-history CSV filename for a settlement day."""
    dt = datetime.strptime(settlement_date, "%Y-%m-%d")
    token = dt.strftime("%y%b%d").lower()
    return f"kalshi-price-history-kxhighmia-{token}-{granularity}.csv"


def event_ticker_for_settlement(settlement_date: str) -> str:
    """Kalshi event ticker, e.g. KXHIGHMIA-26APR20."""
    dt = datetime.strptime(settlement_date, "%Y-%m-%d")
    return f"{SERIES_TICKER}-{dt.strftime('%y%b%d').upper()}"


def settlement_date_from_event_ticker(event_ticker: str) -> Optional[str]:
    m = _EVENT_TICKER_RE.match(event_ticker.strip())
    if not m:
        return None
    yy, mon, dd = m.group(1), m.group(2), m.group(3)
    try:
        dt = datetime.strptime(f"{dd}{mon}{yy}", "%d%b%y")
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%d")


def anchor_time_utc_for_settlement(settlement_date: str) -> datetime:
    et = ZoneInfo("America/New_York")
    target = datetime.strptime(settlement_date, "%Y-%m-%d")
    prior_day = target - timedelta(days=1)
    anchor_et = prior_day.replace(
        hour=ANCHOR_HOUR_ET, minute=0, second=0, microsecond=0, tzinfo=et
    )
    return anchor_et.astimezone(timezone.utc)


def load_price_history_csv(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load one Kalshi price-history CSV; returns (df, column→bin_label map)."""
    path = Path(path)
    raw = pd.read_csv(path)
    if "timestamp" not in raw.columns:
        raise ValueError(f"Missing timestamp column in {path}")

    column_map = _column_map_from_headers(list(raw.columns))
    if len(column_map) < 4:
        raise ValueError(f"Could not map bin columns in {path}: {list(raw.columns)}")

    rename = {col: label for col, label in column_map.items()}
    df = raw.rename(columns=rename)
    labels = list(dict.fromkeys(rename.values()))
    keep = ["timestamp", *labels]
    df = df[[c for c in keep if c in df.columns]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for label in labels:
        if label in df.columns:
            df[label] = pd.to_numeric(df[label], errors="coerce")
    return df, column_map


def prices_at_anchor(
    df: pd.DataFrame,
    settlement_date: str,
    *,
    column_map: Optional[dict[str, str]] = None,
    max_minutes_after_open: int = BIN_OPEN_MAX_MINUTES,
) -> dict[str, Any]:
    """First price tick at or immediately after prior-day 10 AM ET bin open."""
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)
    bin_labels = [c for c in df.columns if c != "timestamp"]

    if df.empty:
        return {
            "settlement_date": settlement_date,
            "anchor_time_utc": anchor_utc.isoformat(),
            "found": False,
            "reason": "empty_price_history",
            "bin_prices_cents": {},
            "market_bins": bin_labels,
            "column_map": column_map or {},
        }

    work = df.copy().sort_values("timestamp")
    window = work[work["timestamp"] >= anchor_utc].copy()
    if window.empty:
        return {
            "settlement_date": settlement_date,
            "anchor_time_utc": anchor_utc.isoformat(),
            "found": False,
            "reason": "no_rows_at_or_after_bin_open",
            "bin_prices_cents": {},
            "market_bins": bin_labels,
            "column_map": column_map or {},
        }

    window["minutes_after_open"] = (
        (window["timestamp"] - anchor_utc).dt.total_seconds() / 60.0
    )
    in_open_window = window[window["minutes_after_open"] <= max_minutes_after_open]
    row = in_open_window.iloc[0] if not in_open_window.empty else window.iloc[0]
    delta = float(row["minutes_after_open"])

    prices: dict[str, Optional[float]] = {}
    for label in bin_labels:
        val = row.get(label)
        prices[label] = None if pd.isna(val) else float(val)

    return {
        "settlement_date": settlement_date,
        "anchor_time_utc": anchor_utc.isoformat(),
        "matched_timestamp_utc": row["timestamp"].isoformat(),
        "delta_minutes_from_anchor": round(delta, 1),
        "found": delta <= max_minutes_after_open,
        "reason": None if delta <= max_minutes_after_open else "first_tick_after_open_window",
        "bin_prices_cents": prices,
        "market_bins": bin_labels,
        "column_map": column_map or {},
        "source_rows": len(df),
    }


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _market_bin_bounds(bin_label: str) -> tuple[float, float]:
    if bin_label.startswith("<="):
        return float("-inf"), float(int(bin_label[2:]))
    if bin_label.startswith(">="):
        return float(int(bin_label[2:])), float("inf")
    if "-" in bin_label:
        low, high = bin_label.split("-", 1)
        return float(int(low)), float(int(high))
    val = float(bin_label)
    return val, val


def calculate_kalshi_fee(yes_ask: float) -> float:
    """Taker fee in probability terms (``0.07 * p * (1 - p)``)."""
    return round(0.07 * yes_ask * (1.0 - yes_ask), 4)


def calculate_kalshi_maker_fee(_price: float = 0.0) -> float:
    """Resting limit bids that get hit are modeled as maker fills (no fee)."""
    return 0.0


def derive_limit_bid(
    model_prob: float,
    *,
    min_edge: float,
    max_cap: float = MAX_ENTRY_YES_ASK,
    is_maker: bool = True,
    min_price: float = MIN_LIMIT_BID,
) -> float:
    """Post a YES limit bid so P(bin) − price − fee ≥ min_edge."""
    fee = calculate_kalshi_maker_fee() if is_maker else calculate_kalshi_fee(max_cap)
    raw = model_prob - min_edge - fee
    bid = min(max(raw, 0.0), max_cap)
    if bid < min_price:
        return 0.0
    return round(bid, 4)


def fill_window_end_utc(settlement_date: str) -> datetime:
    """End of maker fill scan: dynamic trading cutoff, anchor-only, or settlement midnight ET."""
    import os

    mode = os.environ.get("BACKTEST_TRADING_WINDOW", "dynamic").strip().lower()
    if mode == "dynamic":
        try:
            from trading_window_priors import maker_fill_deadline_utc

            return maker_fill_deadline_utc(settlement_date)
        except Exception:
            pass
    elif mode == "anchor":
        return anchor_time_utc_for_settlement(settlement_date) + timedelta(
            minutes=BIN_OPEN_MAX_MINUTES
        )
    et = ZoneInfo("America/New_York")
    target = datetime.strptime(settlement_date, "%Y-%m-%d").replace(tzinfo=et)
    return target.astimezone(timezone.utc)


def _book_liquidity_cap(
    anchor_book: Optional[Any],
    bin_label: str,
    limit_price: float,
) -> int:
    yes_ask_size = None
    if anchor_book is not None and getattr(anchor_book, "found", False):
        yes_ask_size = anchor_book.yes_ask_size(bin_label)
    return backtest_max_contracts(limit_price, yes_ask_size=yes_ask_size)


def scan_limit_fill(
    df: pd.DataFrame,
    settlement_date: str,
    bin_label: str,
    limit_bid: float,
    *,
    max_hours_after_open: float = MAKER_FILL_MAX_HOURS,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
) -> dict[str, Any]:
    """Conservative fill: orderbook → candle archive → minute CSV."""
    anchor_utc = anchor_time_utc_for_settlement(settlement_date)

    if (
        anchor_book is not None
        and getattr(anchor_book, "found", False)
        and limit_bid > 0
    ):
        book_ask = anchor_book.yes_ask_dollars(bin_label)
        if book_ask is not None and book_ask <= limit_bid:
            return {
                "filled": True,
                "reason": None,
                "limit_bid": limit_bid,
                "fill_price": round(min(limit_bid, book_ask), 4),
                "fill_ask_cents": round(book_ask * 100.0, 2),
                "matched_timestamp_utc": getattr(anchor_book, "fetched_at_utc", None)
                or anchor_utc.isoformat(),
                "fill_source": "archived_orderbook_at_anchor",
            }

    if (
        anchor_candle is not None
        and getattr(anchor_candle, "found", False)
        and limit_bid > 0
    ):
        candle_ask = anchor_candle.yes_ask_dollars(bin_label)
        if candle_ask is not None and candle_ask <= limit_bid:
            row = anchor_candle.by_bin.get(bin_label) or {}
            return {
                "filled": True,
                "reason": None,
                "limit_bid": limit_bid,
                "fill_price": round(min(limit_bid, candle_ask), 4),
                "fill_ask_cents": round(candle_ask * 100.0, 2),
                "matched_timestamp_utc": row.get("matched_timestamp_utc")
                or getattr(anchor_candle, "matched_timestamp_utc", None)
                or anchor_utc.isoformat(),
                "fill_source": "archived_candle_at_anchor",
            }

    window_end = fill_window_end_utc(settlement_date)
    limit_cents = limit_bid * 100.0

    if df.empty or bin_label not in df.columns or limit_bid <= 0:
        return {
            "filled": False,
            "reason": "no_data_or_invalid_bid",
            "limit_bid": limit_bid,
            "fill_price": None,
            "fill_ask_cents": None,
            "matched_timestamp_utc": None,
        }

    work = df.copy().sort_values("timestamp")
    work = work[
        (work["timestamp"] >= anchor_utc) & (work["timestamp"] < window_end)
    ]
    if max_hours_after_open > 0:
        max_ts = anchor_utc + timedelta(hours=max_hours_after_open)
        work = work[work["timestamp"] <= max_ts]

    for _, row in work.iterrows():
        ask_cents = row.get(bin_label)
        if ask_cents is None or pd.isna(ask_cents):
            continue
        ask_cents = float(ask_cents)
        if ask_cents <= limit_cents:
            fill_price = round(min(limit_bid, ask_cents / 100.0), 4)
            return {
                "filled": True,
                "reason": None,
                "limit_bid": limit_bid,
                "fill_price": fill_price,
                "fill_ask_cents": ask_cents,
                "matched_timestamp_utc": row["timestamp"].isoformat(),
                "fill_source": "minute_csv",
            }

    return {
        "filled": False,
        "reason": "ask_never_at_or_below_limit",
        "limit_bid": limit_bid,
        "fill_price": None,
        "fill_ask_cents": None,
        "matched_timestamp_utc": None,
    }


def _bin_still_possible(bin_label: str, observed_ceil_f: int) -> bool:
    """False when observed max so far already rules out this market bin."""
    lo, hi = _market_bin_bounds(bin_label)
    if math.isinf(hi):
        return True
    if math.isinf(lo):
        return observed_ceil_f <= int(hi)
    return int(hi) >= observed_ceil_f


def model_prob_for_market_bin(
    forecast_temp_f: float,
    market_bin: str,
    *,
    std_f: float = FORECAST_MODEL_STD_F,
    observed_max_so_far_f: Optional[float] = None,
) -> float:
    """Gaussian mass for forecast temp centered on the market bin range."""
    center = int(round(forecast_temp_f))
    lo, hi = _market_bin_bounds(market_bin)
    if observed_max_so_far_f is not None:
        obs_ceil = math.ceil(observed_max_so_far_f)
        if not _bin_still_possible(market_bin, obs_ceil):
            return 0.0
        if not math.isinf(lo):
            lo = max(lo, float(obs_ceil))
    if math.isinf(lo):
        z_hi = (hi + 0.5 - center) / std_f
        mass = _normal_cdf(z_hi)
    elif math.isinf(hi):
        z_lo = (lo - 0.5 - center) / std_f
        mass = 1.0 - _normal_cdf(z_lo)
    else:
        z_lo = (lo - 0.5 - center) / std_f
        z_hi = (hi + 0.5 - center) / std_f
        mass = _normal_cdf(z_hi) - _normal_cdf(z_lo)
    return round(max(0.0, min(1.0, mass)), 4)


def model_probs_for_market_bins(
    forecast_temp_f: float,
    market_bins: list[str],
    *,
    observed_max_so_far_f: Optional[float] = None,
    std_f: float = FORECAST_MODEL_STD_F,
    wind_shift_f: float = 0.0,
) -> dict[str, float]:
    """Conditional P(bin) for each market bin; renormalized after observed-max truncation."""
    from kalshi_integer_distribution import use_integer_dist_model

    if use_integer_dist_model():
        from kalshi_integer_distribution import model_probs_for_market_bins_integer

        return model_probs_for_market_bins_integer(
            forecast_temp_f,
            market_bins,
            observed_max_so_far_f=observed_max_so_far_f,
            std_f=std_f,
            wind_shift_f=wind_shift_f,
        )

    raw = {
        b: model_prob_for_market_bin(
            forecast_temp_f,
            b,
            std_f=std_f,
            observed_max_so_far_f=observed_max_so_far_f,
        )
        for b in market_bins
    }
    total = sum(raw.values())
    if total <= 0:
        return {b: 0.0 for b in market_bins}
    return {b: round(v / total, 4) for b, v in raw.items()}


def max_insurance_yes_ask(
    bin_probability: float,
    *,
    k: float = INSURANCE_PRICE_K,
) -> float:
    """Relational insurance price cap: higher P(bin) → higher allowable yes ask."""
    return round(max(0.0, k * bin_probability), 4)


def size_yes_leg(
    yes_ask: float,
    budget_dollars: float,
    *,
    min_contracts: int = 0,
    fee: Optional[float] = None,
    max_contracts: Optional[int] = None,
) -> dict[str, Any]:
    """Size a YES purchase to a dollar budget, optionally capped by liquidity."""
    if fee is None:
        fee = calculate_kalshi_fee(yes_ask)
    cost_per = yes_ask + fee
    if cost_per <= 0 or budget_dollars <= 0:
        return {
            "yes_ask": yes_ask,
            "fee": fee,
            "cost_per_contract": cost_per,
            "contracts": 0,
            "total_cost": 0.0,
        }
    contracts = int(budget_dollars / cost_per)
    if max_contracts is not None:
        contracts = min(contracts, max_contracts)
    if contracts < min_contracts:
        contracts = min_contracts if budget_dollars >= cost_per else 0
        if max_contracts is not None:
            contracts = min(contracts, max_contracts)
    total_cost = round(contracts * cost_per, 4) if contracts else 0.0
    return {
        "yes_ask": yes_ask,
        "fee": fee,
        "cost_per_contract": round(cost_per, 4),
        "contracts": contracts,
        "total_cost": total_cost,
        "liquidity_capped": max_contracts is not None and contracts < int(budget_dollars / cost_per),
    }


def backtest_max_contracts(
    limit_price: float,
    *,
    yes_ask_size: Optional[int] = None,
    top_of_book_participation: float = DEFAULT_TOP_OF_BOOK_PARTICIPATION,
) -> int:
    """Per-leg cap: abs max, volume fraction, optional archived top-of-book size."""
    vol_cap = int(
        (DEFAULT_EVENT_DAILY_VOLUME_USD * DEFAULT_EVENT_VOLUME_PARTICIPATION) / limit_price
    ) if limit_price > 0 else DEFAULT_ABS_MAX_CONTRACTS_PER_LEG
    caps = [DEFAULT_ABS_MAX_CONTRACTS_PER_LEG, max(1, vol_cap)]
    if yes_ask_size is not None and yes_ask_size > 0:
        caps.append(max(1, int(yes_ask_size * top_of_book_participation)))
    return min(caps)


def select_insurance_bins(
    bin_probs: dict[str, float],
    forecast_market_bin: str,
    *,
    min_insurance_prob: float = MIN_INSURANCE_BIN_PROB,
) -> dict[str, float]:
    """Insurance candidates: outside forecast bin, P > min floor, P < forecast P."""
    forecast_prob = bin_probs.get(forecast_market_bin, 0.0)
    out: dict[str, float] = {}
    for bin_label, prob in bin_probs.items():
        if bin_label == forecast_market_bin:
            continue
        if prob <= min_insurance_prob:
            continue
        if prob >= forecast_prob:
            continue
        out[bin_label] = prob
    return out


def select_insurance_bins_bilateral(
    bin_probs: dict[str, float],
    forecast_market_bin: str,
    *,
    min_insurance_prob: float = MIN_INSURANCE_BIN_PROB,
) -> dict[str, float]:
    """Insurance candidates: all non-forecast bins with P > floor (both sides of forecast)."""
    out: dict[str, float] = {}
    for bin_label, prob in bin_probs.items():
        if bin_label == forecast_market_bin:
            continue
        if prob <= min_insurance_prob:
            continue
        out[bin_label] = prob
    return out


def allocate_insurance_legs(
    candidates: dict[str, float],
    bin_prices_cents: dict[str, Optional[float]],
    insurance_budget: float,
    *,
    price_k: float = INSURANCE_PRICE_K,
    anchor_book: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Prob-weighted insurance purchases with relational price caps."""
    if insurance_budget <= 0 or not candidates:
        return []

    affordable: dict[str, float] = {}
    meta: dict[str, dict[str, Any]] = {}
    for bin_label, prob in candidates.items():
        cents = bin_prices_cents.get(bin_label)
        yes_ask = cents_to_yes_ask(cents)
        if yes_ask is None:
            continue
        cap = max_insurance_yes_ask(prob, k=price_k)
        if yes_ask > cap:
            continue
        affordable[bin_label] = prob
        meta[bin_label] = {
            "model_probability": prob,
            "max_yes_ask": cap,
            "yes_ask": yes_ask,
        }

    if not affordable:
        return []

    total_prob = sum(affordable.values())
    legs: list[dict[str, Any]] = []
    remaining = insurance_budget
    ordered = sorted(affordable.items(), key=lambda x: (-x[1], x[0]))

    for idx, (bin_label, prob) in enumerate(ordered):
        if remaining <= 0:
            break
        if idx == len(ordered) - 1:
            dollars = round(remaining, 4)
        else:
            dollars = round(insurance_budget * (prob / total_prob), 4)
        yes_ask_size = None
        if anchor_book is not None and getattr(anchor_book, "found", False):
            yes_ask_size = anchor_book.yes_ask_size(bin_label)
        sized = size_yes_leg(
            meta[bin_label]["yes_ask"],
            dollars,
            min_contracts=0,
            max_contracts=backtest_max_contracts(
                meta[bin_label]["yes_ask"],
                yes_ask_size=yes_ask_size,
            ),
        )
        if sized["contracts"] <= 0:
            continue
        if idx != len(ordered) - 1:
            remaining = round(remaining - dollars, 4)
        legs.append({
            "market_bin": bin_label,
            "model_probability": meta[bin_label]["model_probability"],
            "max_yes_ask": meta[bin_label]["max_yes_ask"],
            "yes_ask": sized["yes_ask"],
            "fee": sized["fee"],
            "cost_per_contract": sized["cost_per_contract"],
            "contracts": sized["contracts"],
            "total_cost": sized["total_cost"],
            "budget_allocated": dollars,
        })

    return legs


def allocate_insurance_legs_maker(
    candidates: dict[str, float],
    insurance_budget: float,
    *,
    price_k: float = INSURANCE_PRICE_K,
    price_df: Optional[pd.DataFrame] = None,
    settlement_date: Optional[str] = None,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Prob-weighted insurance limit bids; include only conservatively filled legs."""
    if insurance_budget <= 0 or not candidates:
        return []

    meta: dict[str, dict[str, Any]] = {}
    for bin_label, prob in candidates.items():
        limit_bid = max_insurance_yes_ask(prob, k=price_k)
        if limit_bid < MIN_LIMIT_BID:
            continue
        fill = {"filled": False}
        if price_df is not None and settlement_date:
            fill = scan_limit_fill(
                price_df,
                settlement_date,
                bin_label,
                limit_bid,
                anchor_book=anchor_book,
                anchor_candle=anchor_candle,
            )
        meta[bin_label] = {
            "model_probability": prob,
            "limit_bid": limit_bid,
            "max_yes_ask": limit_bid,
            "fill": fill,
        }

    affordable = {
        b: p for b, p in candidates.items()
        if b in meta and (meta[b]["fill"]["filled"] or price_df is None)
    }
    if not affordable:
        return []

    total_prob = sum(affordable.values())
    legs: list[dict[str, Any]] = []
    remaining = insurance_budget
    ordered = sorted(affordable.items(), key=lambda x: (-x[1], x[0]))
    maker_fee = calculate_kalshi_maker_fee()

    for idx, (bin_label, prob) in enumerate(ordered):
        if remaining <= 0:
            break
        m = meta[bin_label]
        if price_df is not None and settlement_date and not m["fill"]["filled"]:
            continue
        fill_price = (
            m["fill"]["fill_price"] if m["fill"]["filled"] else m["limit_bid"]
        )
        if idx == len(ordered) - 1:
            dollars = round(remaining, 4)
        else:
            dollars = round(insurance_budget * (prob / total_prob), 4)
        sized = size_yes_leg(
            fill_price,
            dollars,
            min_contracts=0,
            fee=maker_fee,
            max_contracts=_book_liquidity_cap(anchor_book, bin_label, fill_price),
        )
        if sized["contracts"] <= 0:
            continue
        if idx != len(ordered) - 1:
            remaining = round(remaining - dollars, 4)
        legs.append({
            "market_bin": bin_label,
            "model_probability": m["model_probability"],
            "limit_bid": m["limit_bid"],
            "max_yes_ask": m["max_yes_ask"],
            "yes_ask": sized["yes_ask"],
            "fill_price": fill_price,
            "fee": sized["fee"],
            "cost_per_contract": sized["cost_per_contract"],
            "contracts": sized["contracts"],
            "total_cost": sized["total_cost"],
            "budget_allocated": dollars,
            "order_mode": ORDER_MODE_MAKER_LIMIT,
            "filled": m["fill"]["filled"],
            "fill_timestamp_utc": m["fill"].get("matched_timestamp_utc"),
        })

    return legs


def allocate_insurance_cover_book(
    candidates: dict[str, float],
    bin_prices_cents: dict[str, Optional[float]],
    forecast_cost: float,
    insurance_budget: float,
    *,
    price_k: float = INSURANCE_PRICE_K,
    anchor_book: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Size insurance legs so any winning leg covers the running book cost (taker)."""
    if insurance_budget <= 0 or forecast_cost <= 0 or not candidates:
        return []

    legs: list[dict[str, Any]] = []
    running_book = round(float(forecast_cost), 4)
    remaining_budget = insurance_budget
    ordered = sorted(candidates.items(), key=lambda x: (-x[1], x[0]))

    for bin_label, prob in ordered:
        if remaining_budget <= 0:
            break
        cents = bin_prices_cents.get(bin_label)
        yes_ask = cents_to_yes_ask(cents)
        if yes_ask is None:
            continue
        cap = max_insurance_yes_ask(prob, k=price_k)
        if yes_ask > cap:
            continue
        fee = calculate_kalshi_fee(yes_ask)
        cost_per = yes_ask + fee
        unit_profit = 1.0 - cost_per
        if unit_profit <= 0:
            continue
        need_contracts = int(math.ceil(running_book / unit_profit))
        yes_ask_size = None
        if anchor_book is not None and getattr(anchor_book, "found", False):
            yes_ask_size = anchor_book.yes_ask_size(bin_label)
        max_c = backtest_max_contracts(yes_ask, yes_ask_size=yes_ask_size)
        contracts = min(max(need_contracts, 1), max_c)
        leg_cost = round(contracts * cost_per, 4)
        if leg_cost > remaining_budget:
            contracts = int(remaining_budget / cost_per)
            if contracts <= 0:
                continue
            leg_cost = round(contracts * cost_per, 4)
        legs.append({
            "market_bin": bin_label,
            "model_probability": prob,
            "max_yes_ask": cap,
            "yes_ask": yes_ask,
            "fee": fee,
            "cost_per_contract": cost_per,
            "contracts": contracts,
            "total_cost": leg_cost,
            "budget_allocated": leg_cost,
            "cover_book_target": running_book,
        })
        remaining_budget = round(remaining_budget - leg_cost, 4)
        running_book = round(running_book + leg_cost, 4)

    return legs


def allocate_insurance_cover_book_maker(
    candidates: dict[str, float],
    forecast_cost: float,
    insurance_budget: float,
    *,
    price_k: float = INSURANCE_PRICE_K,
    price_df: Optional[pd.DataFrame] = None,
    settlement_date: Optional[str] = None,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Size insurance limit bids for book coverage (maker; filled legs only)."""
    if insurance_budget <= 0 or forecast_cost <= 0 or not candidates:
        return []

    meta: dict[str, dict[str, Any]] = {}
    for bin_label, prob in candidates.items():
        limit_bid = max_insurance_yes_ask(prob, k=price_k)
        if limit_bid < MIN_LIMIT_BID:
            continue
        fill = {"filled": False}
        if price_df is not None and settlement_date:
            fill = scan_limit_fill(
                price_df,
                settlement_date,
                bin_label,
                limit_bid,
                anchor_book=anchor_book,
                anchor_candle=anchor_candle,
            )
        meta[bin_label] = {
            "model_probability": prob,
            "limit_bid": limit_bid,
            "max_yes_ask": limit_bid,
            "fill": fill,
        }

    affordable = {
        b: p for b, p in candidates.items()
        if b in meta and (meta[b]["fill"]["filled"] or price_df is None)
    }
    if not affordable:
        return []

    legs: list[dict[str, Any]] = []
    running_book = round(float(forecast_cost), 4)
    remaining_budget = insurance_budget
    maker_fee = calculate_kalshi_maker_fee()
    ordered = sorted(affordable.items(), key=lambda x: (-x[1], x[0]))

    for bin_label, prob in ordered:
        if remaining_budget <= 0:
            break
        m = meta[bin_label]
        if price_df is not None and settlement_date and not m["fill"]["filled"]:
            continue
        fill_price = (
            m["fill"]["fill_price"] if m["fill"]["filled"] else m["limit_bid"]
        )
        cost_per = fill_price + maker_fee
        unit_profit = 1.0 - cost_per
        if unit_profit <= 0:
            continue
        need_contracts = int(math.ceil(running_book / unit_profit))
        max_c = _book_liquidity_cap(anchor_book, bin_label, fill_price)
        contracts = min(max(need_contracts, 1), max_c)
        leg_cost = round(contracts * cost_per, 4)
        if leg_cost > remaining_budget:
            contracts = int(remaining_budget / cost_per)
            if contracts <= 0:
                continue
            leg_cost = round(contracts * cost_per, 4)
        legs.append({
            "market_bin": bin_label,
            "model_probability": m["model_probability"],
            "limit_bid": m["limit_bid"],
            "max_yes_ask": m["max_yes_ask"],
            "yes_ask": fill_price,
            "fill_price": fill_price,
            "fee": maker_fee,
            "cost_per_contract": cost_per,
            "contracts": contracts,
            "total_cost": leg_cost,
            "budget_allocated": leg_cost,
            "order_mode": ORDER_MODE_MAKER_LIMIT,
            "filled": m["fill"]["filled"],
            "fill_timestamp_utc": m["fill"].get("matched_timestamp_utc"),
            "cover_book_target": running_book,
        })
        remaining_budget = round(remaining_budget - leg_cost, 4)
        running_book = round(running_book + leg_cost, 4)

    return legs


def forecast_bin_is_cheapest_at_open(
    bin_prices_cents: dict[str, Optional[float]],
    forecast_market_bin: str,
) -> dict[str, Any]:
    """At bin open, the forecast-favored bin often has the lowest yes ask."""
    valid = {b: p for b, p in bin_prices_cents.items() if p is not None}
    if not valid or forecast_market_bin not in valid:
        return {
            "passes": False,
            "reason": "missing_prices_or_forecast_bin",
            "forecast_market_bin": forecast_market_bin,
            "forecast_price_cents": valid.get(forecast_market_bin),
            "min_price_cents": min(valid.values()) if valid else None,
        }

    forecast_price = valid[forecast_market_bin]
    min_price = min(valid.values())
    min_bins = [b for b, p in valid.items() if p == min_price]
    passes = forecast_price <= min_price

    return {
        "passes": passes,
        "reason": None if passes else "forecast_bin_not_cheapest_at_open",
        "forecast_market_bin": forecast_market_bin,
        "forecast_price_cents": forecast_price,
        "min_price_cents": min_price,
        "min_bins": min_bins,
        "all_prices_cents": valid,
    }


def evaluate_bin_open_maker_limit(
    bin_prices_cents: dict[str, Optional[float]],
    forecast_market_bin: str,
    forecast_temp_f: float,
    *,
    market_bins: Optional[list[str]] = None,
    observed_max_so_far_f: Optional[float] = None,
    max_entry_yes_ask: float = MAX_ENTRY_YES_ASK,
    min_executable_edge: float = MIN_FORECAST_EXECUTABLE_EDGE,
    forecast_bet_dollars: float = DEFAULT_FORECAST_BET_DOLLARS,
    price_df: Optional[pd.DataFrame] = None,
    settlement_date: Optional[str] = None,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
    wind_shift_f: float = 0.0,
) -> dict[str, Any]:
    """Post a YES limit bid on the forecast bin; fill when ask ≤ bid (conservative)."""
    bins = market_bins or list(bin_prices_cents.keys())
    bin_probs = model_probs_for_market_bins(
        forecast_temp_f,
        bins,
        observed_max_so_far_f=observed_max_so_far_f,
        wind_shift_f=wind_shift_f,
    )
    model_prob = bin_probs.get(forecast_market_bin, 0.0)
    limit_bid = derive_limit_bid(
        model_prob,
        min_edge=min_executable_edge,
        max_cap=max_entry_yes_ask,
        is_maker=True,
    )
    maker_fee = calculate_kalshi_maker_fee()
    entry_within_cap = MIN_LIMIT_BID <= limit_bid <= max_entry_yes_ask
    executable_edge = (
        round(model_prob - (limit_bid + maker_fee), 4) if limit_bid > 0 else None
    )
    prob_aligned = (
        executable_edge is not None and executable_edge >= min_executable_edge
    )
    order_posted = entry_within_cap and prob_aligned and limit_bid > 0

    fill: dict[str, Any] = {"filled": False, "reason": "no_price_history"}
    if price_df is not None and settlement_date and order_posted:
        fill = scan_limit_fill(
            price_df,
            settlement_date,
            forecast_market_bin,
            limit_bid,
            anchor_book=anchor_book,
            anchor_candle=anchor_candle,
        )

    fill_price = fill.get("fill_price") if fill.get("filled") else None
    forecast_sized = (
        size_yes_leg(
            fill_price,
            forecast_bet_dollars,
            min_contracts=1,
            fee=maker_fee,
            max_contracts=_book_liquidity_cap(anchor_book, forecast_market_bin, fill_price),
        )
        if fill_price is not None
        else {"contracts": 0, "total_cost": 0.0, "cost_per_contract": None, "fee": maker_fee}
    )

    open_purchase_eligible = order_posted and fill.get("filled") and forecast_sized["contracts"] > 0

    return {
        "order_mode": ORDER_MODE_MAKER_LIMIT,
        "forecast_market_bin": forecast_market_bin,
        "forecast_bin_cheapest_at_open": True,
        "entry_within_cap": entry_within_cap,
        "max_entry_yes_ask": max_entry_yes_ask,
        "min_executable_edge": min_executable_edge,
        "forecast_limit_bid": limit_bid,
        "forecast_bin_yes_ask": fill_price,
        "forecast_price_cents": (
            round(fill_price * 100, 2) if fill_price is not None else None
        ),
        "min_bins_at_open": None,
        "model_probability": model_prob,
        "bin_probabilities": bin_probs,
        "executable_edge": executable_edge,
        "prob_aligned": prob_aligned,
        "order_posted": order_posted,
        "forecast_filled": fill.get("filled", False),
        "fill_timestamp_utc": fill.get("matched_timestamp_utc"),
        "fill_reason": fill.get("reason"),
        "fill_source": fill.get("fill_source"),
        "anchor_orderbook_used": bool(
            anchor_book is not None and getattr(anchor_book, "found", False)
        ),
        "anchor_candle_used": bool(
            anchor_candle is not None and getattr(anchor_candle, "found", False)
        ),
        "open_purchase_eligible": open_purchase_eligible,
        "forecast_contracts": forecast_sized["contracts"],
        "forecast_total_cost": forecast_sized["total_cost"],
        "forecast_cost_per_contract": forecast_sized.get("cost_per_contract"),
        "forecast_fee": maker_fee,
        "cheapest_check": {"passes": True, "reason": "maker_limit_mode"},
    }


def evaluate_bin_open_purchase(
    bin_prices_cents: dict[str, Optional[float]],
    forecast_market_bin: str,
    forecast_temp_f: float,
    *,
    market_bins: Optional[list[str]] = None,
    observed_max_so_far_f: Optional[float] = None,
    max_entry_yes_ask: float = MAX_ENTRY_YES_ASK,
    min_executable_edge: float = MIN_FORECAST_EXECUTABLE_EDGE,
    forecast_bet_dollars: float = DEFAULT_FORECAST_BET_DOLLARS,
    order_mode: str = DEFAULT_ORDER_MODE,
    price_df: Optional[pd.DataFrame] = None,
    settlement_date: Optional[str] = None,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
    wind_shift_f: float = 0.0,
) -> dict[str, Any]:
    """Bin-open forecast leg — taker (hit ask) or maker (post limit bid)."""
    if order_mode == ORDER_MODE_MAKER_LIMIT:
        return evaluate_bin_open_maker_limit(
            bin_prices_cents,
            forecast_market_bin,
            forecast_temp_f,
            market_bins=market_bins,
            observed_max_so_far_f=observed_max_so_far_f,
            max_entry_yes_ask=max_entry_yes_ask,
            min_executable_edge=min_executable_edge,
            forecast_bet_dollars=forecast_bet_dollars,
            price_df=price_df,
            settlement_date=settlement_date,
            anchor_book=anchor_book,
            anchor_candle=anchor_candle,
            wind_shift_f=wind_shift_f,
        )

    cheapest = forecast_bin_is_cheapest_at_open(bin_prices_cents, forecast_market_bin)
    yes_ask = cents_to_yes_ask(cheapest.get("forecast_price_cents"))
    entry_within_cap = yes_ask is not None and yes_ask <= max_entry_yes_ask

    bins = market_bins or list(bin_prices_cents.keys())
    bin_probs = model_probs_for_market_bins(
        forecast_temp_f,
        bins,
        observed_max_so_far_f=observed_max_so_far_f,
        wind_shift_f=wind_shift_f,
    )
    model_prob = bin_probs.get(forecast_market_bin, 0.0)
    fee = calculate_kalshi_fee(yes_ask) if yes_ask is not None else 0.0
    executable_edge = (
        round(model_prob - (yes_ask + fee), 4) if yes_ask is not None else None
    )
    prob_aligned = (
        executable_edge is not None and executable_edge >= min_executable_edge
    )

    forecast_sized = (
        size_yes_leg(
            yes_ask,
            forecast_bet_dollars,
            min_contracts=1,
            max_contracts=_book_liquidity_cap(anchor_book, forecast_market_bin, yes_ask),
        )
        if yes_ask is not None
        else {"contracts": 0, "total_cost": 0.0, "cost_per_contract": None}
    )

    open_purchase_eligible = (
        cheapest["passes"]
        and entry_within_cap
        and prob_aligned
        and yes_ask is not None
        and forecast_sized["contracts"] > 0
    )

    return {
        "order_mode": ORDER_MODE_TAKER,
        "forecast_market_bin": forecast_market_bin,
        "forecast_bin_cheapest_at_open": cheapest["passes"],
        "entry_within_cap": entry_within_cap,
        "max_entry_yes_ask": max_entry_yes_ask,
        "min_executable_edge": min_executable_edge,
        "forecast_bin_yes_ask": yes_ask,
        "forecast_price_cents": cheapest.get("forecast_price_cents"),
        "min_bins_at_open": cheapest.get("min_bins"),
        "model_probability": model_prob,
        "bin_probabilities": bin_probs,
        "executable_edge": executable_edge,
        "prob_aligned": prob_aligned,
        "open_purchase_eligible": open_purchase_eligible,
        "forecast_contracts": forecast_sized["contracts"],
        "forecast_total_cost": forecast_sized["total_cost"],
        "forecast_cost_per_contract": forecast_sized.get("cost_per_contract"),
        "cheapest_check": cheapest,
    }


def evaluate_hedged_open_purchase(
    bin_prices_cents: dict[str, Optional[float]],
    forecast_market_bin: str,
    forecast_temp_f: float,
    market_bins: list[str],
    *,
    observed_max_so_far_f: Optional[float] = None,
    max_entry_yes_ask: float = MAX_ENTRY_YES_ASK,
    min_forecast_edge: float = MIN_FORECAST_EXECUTABLE_EDGE,
    forecast_bet_dollars: float = DEFAULT_FORECAST_BET_DOLLARS,
    insurance_budget_fraction: float = INSURANCE_BUDGET_FRACTION,
    insurance_price_k: float = INSURANCE_PRICE_K,
    min_insurance_prob: float = MIN_INSURANCE_BIN_PROB,
    insurance_mode: str = DEFAULT_INSURANCE_MODE,
    order_mode: str = DEFAULT_ORDER_MODE,
    price_df: Optional[pd.DataFrame] = None,
    settlement_date: Optional[str] = None,
    anchor_book: Optional[Any] = None,
    anchor_candle: Optional[Any] = None,
    wind_shift_f: float = 0.0,
) -> dict[str, Any]:
    """Forecast leg + prob-weighted or cover-book insurance legs (taker or maker limit)."""
    forecast = evaluate_bin_open_purchase(
        bin_prices_cents,
        forecast_market_bin,
        forecast_temp_f,
        market_bins=market_bins,
        observed_max_so_far_f=observed_max_so_far_f,
        max_entry_yes_ask=max_entry_yes_ask,
        min_executable_edge=min_forecast_edge,
        forecast_bet_dollars=forecast_bet_dollars,
        order_mode=order_mode,
        price_df=price_df,
        settlement_date=settlement_date,
        anchor_book=anchor_book,
        anchor_candle=anchor_candle,
        wind_shift_f=wind_shift_f,
    )

    insurance_legs: list[dict[str, Any]] = []
    insurance_budget_cap = 0.0
    insurance_total_cost = 0.0

    order_posted = forecast.get("order_posted", forecast["open_purchase_eligible"])
    if order_posted or forecast["open_purchase_eligible"]:
        f_cost = float(forecast.get("forecast_total_cost") or 0.0)
        if f_cost <= 0 and forecast.get("forecast_limit_bid"):
            sized = size_yes_leg(
                forecast["forecast_limit_bid"],
                forecast_bet_dollars,
                min_contracts=0,
                fee=calculate_kalshi_maker_fee(),
                max_contracts=_book_liquidity_cap(
                    anchor_book,
                    forecast_market_bin,
                    forecast["forecast_limit_bid"],
                ),
            )
            f_cost = float(sized.get("total_cost") or forecast_bet_dollars * 0.25)
        budget_frac = insurance_budget_fraction
        if insurance_mode == INSURANCE_MODE_COVER_BOOK and budget_frac <= INSURANCE_BUDGET_FRACTION:
            budget_frac = max(budget_frac, COVER_BOOK_DEFAULT_BUDGET_FRACTION)
        insurance_budget_cap = round(max(f_cost, forecast_bet_dollars) * budget_frac, 4)
        if insurance_mode == INSURANCE_MODE_COVER_BOOK:
            candidates = select_insurance_bins_bilateral(
                forecast["bin_probabilities"],
                forecast_market_bin,
                min_insurance_prob=min_insurance_prob,
            )
        else:
            candidates = select_insurance_bins(
                forecast["bin_probabilities"],
                forecast_market_bin,
                min_insurance_prob=min_insurance_prob,
            )
        if insurance_mode == INSURANCE_MODE_COVER_BOOK:
            if order_mode == ORDER_MODE_MAKER_LIMIT:
                insurance_legs = allocate_insurance_cover_book_maker(
                    candidates,
                    f_cost,
                    insurance_budget_cap,
                    price_k=insurance_price_k,
                    price_df=price_df,
                    settlement_date=settlement_date,
                    anchor_book=anchor_book,
                    anchor_candle=anchor_candle,
                )
            elif forecast["open_purchase_eligible"]:
                insurance_legs = allocate_insurance_cover_book(
                    candidates,
                    bin_prices_cents,
                    f_cost,
                    insurance_budget_cap,
                    price_k=insurance_price_k,
                    anchor_book=anchor_book,
                )
        elif order_mode == ORDER_MODE_MAKER_LIMIT:
            insurance_legs = allocate_insurance_legs_maker(
                candidates,
                insurance_budget_cap,
                price_k=insurance_price_k,
                price_df=price_df,
                settlement_date=settlement_date,
                anchor_book=anchor_book,
                anchor_candle=anchor_candle,
            )
        elif forecast["open_purchase_eligible"]:
            insurance_legs = allocate_insurance_legs(
                candidates,
                bin_prices_cents,
                insurance_budget_cap,
                price_k=insurance_price_k,
                anchor_book=anchor_book,
            )
        insurance_total_cost = round(sum(l["total_cost"] for l in insurance_legs), 4)

    total_deployed = round(
        float(forecast.get("forecast_total_cost") or 0.0) + insurance_total_cost,
        4,
    )

    return {
        **forecast,
        "hedged_open_eligible": forecast["open_purchase_eligible"],
        "insurance_legs": insurance_legs,
        "insurance_budget_cap": insurance_budget_cap,
        "insurance_total_cost": insurance_total_cost,
        "insurance_budget_fraction": insurance_budget_fraction,
        "insurance_price_k": insurance_price_k,
        "insurance_mode": insurance_mode,
        "total_deployed": total_deployed,
    }


def forecast_bin_is_most_expensive(
    bin_prices_cents: dict[str, Optional[float]],
    forecast_market_bin: str,
) -> dict[str, Any]:
    """Check that the NWS-equivalent market bin has the highest yes price."""
    valid = {b: p for b, p in bin_prices_cents.items() if p is not None}
    if not valid or forecast_market_bin not in valid:
        return {
            "passes": False,
            "reason": "missing_prices_or_forecast_bin",
            "forecast_market_bin": forecast_market_bin,
            "forecast_price_cents": valid.get(forecast_market_bin),
            "max_price_cents": max(valid.values()) if valid else None,
        }

    forecast_price = valid[forecast_market_bin]
    max_price = max(valid.values())
    max_bins = [b for b, p in valid.items() if p == max_price]
    passes = forecast_price >= max_price

    return {
        "passes": passes,
        "reason": None if passes else "forecast_bin_not_most_expensive",
        "forecast_market_bin": forecast_market_bin,
        "forecast_price_cents": forecast_price,
        "max_price_cents": max_price,
        "max_bins": max_bins,
        "all_prices_cents": valid,
    }


def discover_price_history_files(directory: Path) -> dict[str, Path]:
    directory = Path(directory)
    out: dict[str, Path] = {}
    for path in sorted(directory.glob("kalshi-price-history-kxhighmia-*.csv")):
        day = settlement_date_from_path(path)
        if day:
            out[day] = path
    return out


def load_anchor_prices_for_date(
    price_dir: Path,
    settlement_date: str,
    *,
    forecast_temp_f: Optional[float] = None,
    order_mode: str = DEFAULT_ORDER_MODE,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
    min_forecast_edge: float = MIN_FORECAST_EXECUTABLE_EDGE,
    insurance_budget_fraction: float = INSURANCE_BUDGET_FRACTION,
    insurance_price_k: float = INSURANCE_PRICE_K,
    insurance_mode: str = DEFAULT_INSURANCE_MODE,
    min_insurance_prob: float = MIN_INSURANCE_BIN_PROB,
) -> dict[str, Any]:
    files = discover_price_history_files(price_dir)
    path = files.get(settlement_date)
    if path is None:
        return {
            "settlement_date": settlement_date,
            "found": False,
            "reason": "no_price_history_file",
            "bin_prices_cents": {},
        }
    df, column_map = load_price_history_csv(path)
    result = prices_at_anchor(df, settlement_date, column_map=column_map)
    result["source_file"] = str(path)
    result["order_mode"] = order_mode

    from kalshi_orderbook_archive_loader import load_anchor_orderbook_context

    archive_dir = orderbook_archive_dir
    if archive_dir is None:
        from kalshi_orderbook_archive_loader import default_orderbook_archive_dir

        archive_dir = default_orderbook_archive_dir()
    anchor_book = None
    if archive_dir is not None:
        anchor_book = load_anchor_orderbook_context(
            settlement_date, column_map, archive_dir
        )
        result["anchor_orderbook"] = anchor_book.to_dict()
        result["_anchor_orderbook"] = anchor_book

    from kalshi_candle_archive_loader import (
        default_candle_archive_dir,
        load_anchor_candle_context,
    )

    candle_dir = candle_archive_dir
    if candle_dir is None:
        candle_dir = default_candle_archive_dir()
    anchor_candle = None
    if candle_dir is not None:
        anchor_candle = load_anchor_candle_context(
            settlement_date, column_map, candle_dir
        )
        result["anchor_candle"] = anchor_candle.to_dict()
        result["_anchor_candle"] = anchor_candle

    if forecast_temp_f is not None:
        market_bin = find_market_bin_for_temp(int(round(forecast_temp_f)), column_map)
        result["forecast_market_bin"] = market_bin
        result["research_bin"] = temp_to_bin(int(round(forecast_temp_f)))
        if market_bin and result.get("bin_prices_cents"):
            purchase = evaluate_hedged_open_purchase(
                result["bin_prices_cents"],
                market_bin,
                forecast_temp_f,
                result.get("market_bins", list(result["bin_prices_cents"].keys())),
                min_forecast_edge=min_forecast_edge,
                insurance_budget_fraction=insurance_budget_fraction,
                insurance_price_k=insurance_price_k,
                insurance_mode=insurance_mode,
                min_insurance_prob=min_insurance_prob,
                order_mode=order_mode,
                price_df=df,
                settlement_date=settlement_date,
                anchor_book=anchor_book if anchor_book and anchor_book.found else anchor_book,
                anchor_candle=anchor_candle if anchor_candle and anchor_candle.found else anchor_candle,
            )
            result["open_purchase"] = purchase
            result["hedged_open_purchase"] = purchase
            result["forecast_bin_cheapest_at_open"] = purchase["forecast_bin_cheapest_at_open"]
            result["entry_within_cap"] = purchase["entry_within_cap"]
            result["open_purchase_eligible"] = purchase["open_purchase_eligible"]
            result["insurance_legs"] = purchase.get("insurance_legs", [])
            result["total_deployed"] = purchase.get("total_deployed", 0.0)

    return result


def cents_to_yes_ask(cents: Optional[float]) -> Optional[float]:
    if cents is None:
        return None
    return round(float(cents) / 100.0, 4)


def default_price_history_dir() -> Optional[Path]:
    """Default Kalshi bet-history export folder (Console 2 sibling repo)."""
    from kmia_kalshi_paths import kalshi_price_history_dir, optional_existing

    return optional_existing(kalshi_price_history_dir())
