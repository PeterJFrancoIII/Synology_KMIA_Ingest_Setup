#!/usr/bin/env python3
"""Classify NAS paper ledger trades for forward analysis dossiers.

NO REAL TRADING EXECUTION — read-only diagnostics.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

POLICY_APPROVED_FALLBACK_DATE = "2026-06-24"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_mock(ticker: str) -> bool:
    return ticker.startswith("MOCK")


def _is_real_kxhighmia(ticker: str) -> bool:
    return ticker.startswith("KXHIGHMIA-") and not _is_mock(ticker)


def _parse_utc(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def classify_ledger(
    ledger: dict[str, Any],
    *,
    policy_approved_at: Optional[str] = None,
) -> dict[str, Any]:
    trades = ledger.get("trades") or []
    cutoff_raw = policy_approved_at or POLICY_APPROVED_FALLBACK_DATE
    cutoff = _parse_utc(cutoff_raw)
    if cutoff is None:
        try:
            cutoff = datetime.strptime(str(cutoff_raw)[:10], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            cutoff = None
    elif cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    mock_trades = [t for t in trades if _is_mock(str(t.get("market_ticker") or ""))]
    real_trades = [t for t in trades if _is_real_kxhighmia(str(t.get("market_ticker") or ""))]

    def _status_bucket(trade_list: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        open_t: list[dict[str, Any]] = []
        settled_t: list[dict[str, Any]] = []
        for t in trade_list:
            status = str(t.get("status", "")).lower()
            if status == "open":
                open_t.append(t)
            elif status in ("settled", "closed", "won", "lost"):
                settled_t.append(t)
        return {"open": open_t, "settled": settled_t}

    real_buckets = _status_bucket(real_trades)
    real_settled = real_buckets["settled"]
    real_open = real_buckets["open"]

    wins = losses = flat = 0
    pnl_total = 0.0
    for t in real_settled:
        pnl = float(t.get("pnl") or 0)
        pnl_total += pnl
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
        else:
            flat += 1

    order_modes = Counter(str(t.get("order_mode") or "unknown") for t in real_trades)
    forecast_bins = Counter(str(t.get("forecast_bin") or "unknown") for t in real_trades)

    post_policy_settled = 0
    maker_limit_settled = 0
    for t in real_settled:
        if str(t.get("order_mode") or "").lower() == "maker_limit":
            maker_limit_settled += 1
        if cutoff is not None:
            ts = _parse_utc(t.get("timestamp_utc") or t.get("settled_at_utc"))
            if ts is None and t.get("target_date"):
                try:
                    ts = datetime.strptime(str(t["target_date"]), "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    ts = None
            if ts is not None and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts is not None and ts >= cutoff:
                post_policy_settled += 1

    loss_samples = sorted(
        [
            {
                "market_ticker": t.get("market_ticker"),
                "target_date": t.get("target_date"),
                "pnl": t.get("pnl"),
                "forecast_bin": t.get("forecast_bin"),
                "execution_price": t.get("execution_price"),
                "quantity": t.get("quantity"),
                "model_probability": t.get("model_probability"),
                "order_mode": t.get("order_mode"),
                "loss_taxonomy": t.get("loss_taxonomy"),
            }
            for t in real_settled
            if float(t.get("pnl") or 0) < 0
        ],
        key=lambda x: float(x.get("pnl") or 0),
    )[:12]

    win_samples = [
        {
            "market_ticker": t.get("market_ticker"),
            "target_date": t.get("target_date"),
            "pnl": t.get("pnl"),
            "forecast_bin": t.get("forecast_bin"),
            "order_mode": t.get("order_mode"),
        }
        for t in real_settled
        if float(t.get("pnl") or 0) > 0
    ]

    settled_by_month: Counter[str] = Counter()
    for t in real_settled:
        td = t.get("target_date")
        if td:
            settled_by_month[str(td)[:7]] += 1

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_trades": len(trades),
        "mock_trades": len(mock_trades),
        "real_trades": len(real_trades),
        "real_settled": len(real_settled),
        "real_open": len(real_open),
        "post_policy_settled": post_policy_settled,
        "maker_limit_settled": maker_limit_settled,
        "wins": wins,
        "losses": losses,
        "flat": flat,
        "win_rate_pct": round(100.0 * wins / len(real_settled), 2) if real_settled else None,
        "total_pnl_settled_real": round(pnl_total, 4),
        "settled_by_month": dict(settled_by_month),
        "order_modes": dict(order_modes),
        "top_forecast_bins": forecast_bins.most_common(10),
        "open_tickers": [t.get("market_ticker") for t in real_open],
        "loss_samples": loss_samples,
        "win_samples": win_samples,
        "gates": {
            "real_settled_target": 20,
            "real_settled_current": len(real_settled),
            "maker_limit_settled_target": 10,
            "maker_limit_settled_current": maker_limit_settled,
            "policy_reapproval_allowed": len(real_settled) >= 20 and maker_limit_settled >= 10,
        },
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify paper ledger trades")
    parser.add_argument("ledger", type=Path, help="Path to ledger.json")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--policy-approved-at", default=POLICY_APPROVED_FALLBACK_DATE)
    args = parser.parse_args(argv)

    ledger = _load_json(args.ledger)
    result = classify_ledger(ledger, policy_approved_at=args.policy_approved_at)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
