#!/usr/bin/env python3
"""Read-only status of Kalshi archive dirs used by Console 2 backtest.

NO REAL TRADING — inventory only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from kalshi_candle_archive import candle_archive_filename
from kalshi_price_history_loader import discover_price_history_files, default_price_history_dir
from kmia_kalshi_paths import (
    kalshi_candle_archive_dir,
    kalshi_market_archive_dir,
    kalshi_price_history_dir,
)


def _count_jsonl_lines(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def _dir_status(root: Optional[Path], subdir: str, pattern: str) -> dict[str, Any]:
    if root is None or not root.is_dir():
        return {"path": str(root) if root else None, "exists": False, "files": 0}
    folder = root / subdir if subdir else root
    if not folder.is_dir():
        return {"path": str(folder), "exists": False, "files": 0}
    files = sorted(folder.glob(pattern))
    return {
        "path": str(folder),
        "exists": True,
        "files": len(files),
        "latest": files[-1].name if files else None,
        "oldest": files[0].name if files else None,
    }


def build_archive_status(
    *,
    price_history_dir: Optional[Path] = None,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
) -> dict[str, Any]:
    price_dir = price_history_dir or default_price_history_dir()
    ob_root = orderbook_archive_dir or kalshi_market_archive_dir()
    candle_root = candle_archive_dir or kalshi_candle_archive_dir()

    price_days: list[str] = []
    if price_dir and price_dir.is_dir():
        price_days = sorted(discover_price_history_files(price_dir).keys())

    ob_status = _dir_status(ob_root, "orderbooks", "*.jsonl")
    candle_files = []
    if candle_root.is_dir():
        candle_files = sorted(candle_root.glob("*-candles.jsonl"))

    candle_days = set()
    for path in candle_files:
        name = path.name
        if name.startswith("kalshi-price-history-kxhighmia-"):
            token = name.replace("kalshi-price-history-kxhighmia-", "").replace("-candles.jsonl", "")
            # best-effort: map via price history discovery instead
            pass
    for day in price_days:
        if candle_root.is_dir():
            cand = candle_root / candle_archive_filename(day)
            if cand.is_file():
                candle_days.add(day)

    ob_days = set()
    if ob_root.is_dir():
        ob_folder = ob_root / "orderbooks"
        if ob_folder.is_dir():
            for path in ob_folder.glob("*.jsonl"):
                ob_days.add(path.stem)

    overlap_price_candle = len(candle_days)
    overlap_price_ob = sum(
        1 for d in price_days
        if (ob_root / "orderbooks" / f"{d}.jsonl").is_file()
    )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "price_history_dir": str(price_dir) if price_dir else None,
        "n_price_history_days": len(price_days),
        "price_date_range": {
            "start": price_days[0] if price_days else None,
            "end": price_days[-1] if price_days else None,
        },
        "orderbook_archive": ob_status,
        "n_orderbook_jsonl_files": ob_status.get("files", 0),
        "n_price_days_with_orderbook": overlap_price_ob,
        "candle_archive": {
            "path": str(candle_root),
            "exists": candle_root.is_dir(),
            "files": len(candle_files),
            "latest": candle_files[-1].name if candle_files else None,
        },
        "n_price_days_with_candles": overlap_price_candle,
        "coverage_pct": {
            "orderbook_vs_price_days": round(
                100.0 * overlap_price_ob / len(price_days), 1
            ) if price_days else 0.0,
            "candles_vs_price_days": round(
                100.0 * overlap_price_candle / len(price_days), 1
            ) if price_days else 0.0,
        },
        "note": (
            "Orderbook JSONL uses UTC date filenames; candle files use settlement-day names. "
            "Backtest falls back to minute CSV when archives missing."
        ),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Kalshi archive coverage status (read-only)")
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--orderbook-archive-dir", type=Path, default=None)
    parser.add_argument("--candle-archive-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args(argv)

    status = build_archive_status(
        price_history_dir=args.price_history_dir or kalshi_price_history_dir(),
        orderbook_archive_dir=args.orderbook_archive_dir,
        candle_archive_dir=args.candle_archive_dir,
    )

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(
            f"Price history: {status['n_price_history_days']} days "
            f"({status['price_date_range']['start']} → {status['price_date_range']['end']})"
        )
        print(
            f"Orderbook archive: {status['n_orderbook_jsonl_files']} JSONL files; "
            f"{status['n_price_days_with_orderbook']} match price days "
            f"({status['coverage_pct']['orderbook_vs_price_days']}%)"
        )
        print(
            f"Candle archive: {status['candle_archive']['files']} files; "
            f"{status['n_price_days_with_candles']} match price days "
            f"({status['coverage_pct']['candles_vs_price_days']}%)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
