#!/usr/bin/env python3
"""Read-only Kalshi public API client for KXHIGHMIA market data ingest.

Uses the elections API base (same data as Kalshi web exports). Optional auth
via KALSHI_USE_AUTH / KALSHI_API_KEY_ID when rate limits require it.

NO REAL TRADING — market data read only.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional

from kalshi_price_history_loader import DEFAULT_KALSHI_API_BASE, SERIES_TICKER

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - MARKET DATA READ ONLY",
}


def default_kalshi_api_base() -> str:
    return os.environ.get("KALSHI_API_BASE_URL", DEFAULT_KALSHI_API_BASE)


def _http_get_json(path: str, *, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    base = default_kalshi_api_base().rstrip("/")
    url = f"{base}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"

    cmd = ["curl", "-sfL", url, "-H", "Accept: application/json"]
    use_auth = os.environ.get("KALSHI_USE_AUTH", "false").lower() == "true"
    if use_auth:
        from kalshi_api_auth import auth_configured, create_kalshi_auth_headers

        if not auth_configured():
            raise RuntimeError(
                "KALSHI_USE_AUTH=true but KALSHI_API_KEY_ID + private key path are not set"
            )
        path_only = path.split("?", 1)[0]
        for header, value in create_kalshi_auth_headers("GET", path_only).items():
            cmd.extend(["-H", f"{header}: {value}"])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Kalshi API GET failed ({path}): {proc.stderr or proc.stdout}")
    data = json.loads(proc.stdout)
    return data if isinstance(data, dict) else {}


def list_kxhighmia_events(
    *,
    status: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"series_ticker": SERIES_TICKER, "limit": limit}
    if status:
        params["status"] = status
    data = _http_get_json("/events", params=params)
    return list(data.get("events") or [])


def get_event_markets(event_ticker: str, *, limit: int = 50) -> list[dict[str, Any]]:
    data = _http_get_json(
        "/markets",
        params={"event_ticker": event_ticker, "limit": limit},
    )
    markets = list(data.get("markets") or [])
    return sorted(markets, key=_market_column_sort_key)


def get_market_candlesticks(
    market_ticker: str,
    *,
    start_ts: int,
    end_ts: int,
    period_interval: int = 1,
) -> list[dict[str, Any]]:
    """Minute (or hour) yes-price candlesticks for one contract."""
    series, _ = market_ticker.split("-", 1)
    path = f"/series/{series}/markets/{market_ticker}/candlesticks"
    data = _http_get_json(
        path,
        params={
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
        },
    )
    return list(data.get("candlesticks") or [])


def _market_column_sort_key(market: dict[str, Any]) -> tuple[float, float, str]:
    """Order bins left-to-right: below, ranges low→high, above."""
    strike = (market.get("strike_type") or "").lower()
    floor = market.get("floor_strike")
    cap = market.get("cap_strike")
    floor_f = float(floor) if floor is not None else -999.0
    cap_f = float(cap) if cap is not None else 999.0
    if strike == "less":
        return (-999.0, cap_f, market.get("ticker", ""))
    if strike == "greater":
        return (floor_f, 999.0, market.get("ticker", ""))
    return (floor_f, cap_f, market.get("ticker", ""))


def market_window_unix(markets: list[dict[str, Any]]) -> tuple[int, int]:
    """Use Kalshi open/close timestamps from contract metadata."""
    opens: list[int] = []
    closes: list[int] = []
    for m in markets:
        for field, bucket in (("open_time", opens), ("close_time", closes)):
            raw = m.get(field)
            if not raw:
                continue
            try:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            bucket.append(int(dt.timestamp()))
    if not opens or not closes:
        raise ValueError("markets missing open_time/close_time")
    return min(opens), max(closes)


def candlestick_yes_ask_cents(candle: dict[str, Any]) -> Optional[float]:
    """Yes ask close in cents (matches backtest taker entry semantics)."""
    yes_ask = candle.get("yes_ask") or {}
    close = yes_ask.get("close_dollars")
    if close in (None, ""):
        return None
    try:
        return round(float(close) * 100.0, 2)
    except (TypeError, ValueError):
        return None


def candlestick_side_dollars(candle: dict[str, Any], side: str, field: str = "close_dollars") -> Optional[float]:
    """Extract open/high/low/close dollars for yes_bid, yes_ask, etc."""
    block = candle.get(side) or {}
    val = block.get(field)
    if val in (None, ""):
        return None
    try:
        return round(float(val), 6)
    except (TypeError, ValueError):
        return None


def normalize_candlestick(candle: dict[str, Any]) -> dict[str, Any]:
    """Flatten API candlestick for JSONL archive (full payload retained under raw)."""
    ts = candle.get("end_period_ts")
    out: dict[str, Any] = {"end_period_ts": ts}
    for side in ("yes_bid", "yes_ask", "no_bid", "no_ask", "price"):
        block = candle.get(side)
        if isinstance(block, dict):
            out[side] = {
                k: block.get(k)
                for k in ("open_dollars", "high_dollars", "low_dollars", "close_dollars")
                if block.get(k) not in (None, "")
            }
    vol = candle.get("volume")
    if vol is not None:
        out["volume"] = vol
    out["raw"] = candle
    return out


def timestamp_iso_from_unix(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def minute_end_timestamps(start_ts: int, end_ts: int) -> list[int]:
    """UTC minute-end timestamps (Kalshi end_period_ts) from open through close."""
    first = start_ts - (start_ts % 60) + 60
    out: list[int] = []
    t = first
    while t <= end_ts:
        out.append(t)
        t += 60
    return out


def candles_to_price_series(candles: list[dict[str, Any]]) -> dict[int, float]:
    """Map end_period_ts → yes-ask close cents for minutes with API data."""
    out: dict[int, float] = {}
    for candle in candles:
        ts = candle.get("end_period_ts")
        if ts is None:
            continue
        price = candlestick_yes_ask_cents(candle)
        if price is not None:
            out[int(ts)] = price
    return out


def forward_fill_on_grid(
    grid: list[int],
    series: dict[int, float],
) -> dict[int, Optional[float]]:
    """Carry last quoted yes-ask across each minute (empty until first quote)."""
    last: Optional[float] = None
    filled: dict[int, Optional[float]] = {}
    for ts in grid:
        if ts in series:
            last = series[ts]
        filled[ts] = last
    return filled
