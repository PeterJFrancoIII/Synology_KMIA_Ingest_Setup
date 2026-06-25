#!/usr/bin/env python3
"""Pilot WS maker replay on 1-2 days of NAS orderbook archive (read-only).

Run on Legion5 or NAS after WS archive has >=1 day of snapshots.
After the 14-day gate (~2026-07-06), use for maker fill validation.

Usage:
  KALSHI_ROOT=/data/Kalshi python3 ingest/scripts/pilot_ws_maker_replay.py 2026-06-22
  python3 ingest/scripts/pilot_ws_maker_replay.py 2026-06-22 2026-06-23
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from kalshi_orderbook_archive_loader import (  # noqa: E402
    default_orderbook_archive_dir,
    load_anchor_orderbook_context,
)
from kalshi_price_history_loader import build_column_map_for_csv  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot WS maker replay at 10 AM anchor")
    parser.add_argument("dates", nargs="+", help="Settlement dates YYYY-MM-DD")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON report path (default: docs/ops/paper_forward_analysis/ws_replay_pilot/)",
    )
    parser.add_argument("--kalshi-root", type=Path, default=None)
    args = parser.parse_args(argv)

    if sys.platform == "darwin" and os.environ.get("ALLOW_MAC_POLICY_REFRESH") != "1":
        print("ERROR: Run on Legion5 or NAS. Set ALLOW_MAC_POLICY_REFRESH=1 to override.", file=sys.stderr)
        return 1

    archive_dir = default_orderbook_archive_dir()
    if archive_dir is None or not archive_dir.is_dir():
        print(f"ERROR: orderbook archive missing: {archive_dir}", file=sys.stderr)
        return 1

    column_map: dict[str, str] = {}
    try:
        from kmia_kalshi_paths import kalshi_price_history_dir

        csv_dir = kalshi_price_history_dir()
        sample_csv = next(csv_dir.glob("*.csv"), None) if csv_dir and csv_dir.is_dir() else None
        if sample_csv:
            column_map = build_column_map_for_csv(sample_csv)
    except Exception:
        column_map = {}

    rows: list[dict] = []
    for day in args.dates:
        ws_jsonl = archive_dir / "orderbook_ws" / f"{day}.jsonl"
        snap_dir = archive_dir / "orderbook_ws_snapshots"
        snap_count = len(list(snap_dir.glob(f"{day}*.json"))) if snap_dir.is_dir() else 0
        ctx = load_anchor_orderbook_context(day, column_map, archive_dir=archive_dir)
        sample_bin = next(iter(ctx.by_bin.keys()), None) if ctx.by_bin else None
        sample_book = ctx.by_bin.get(sample_bin) if sample_bin else None
        rows.append({
            "settlement_date": day,
            "ws_jsonl_exists": ws_jsonl.is_file(),
            "ws_jsonl_bytes": ws_jsonl.stat().st_size if ws_jsonl.is_file() else 0,
            "snapshot_files": snap_count,
            "anchor_found": ctx.found,
            "anchor_reason": ctx.reason,
            "delta_minutes_from_anchor": ctx.delta_minutes_from_anchor,
            "archive_path": ctx.archive_path,
            "sample_bin": sample_bin,
            "sample_yes_ask_dollars": (sample_book or {}).get("yes_ask_dollars"),
            "bins_mapped": len(ctx.by_bin or {}),
        })

    out_dir = REPO_ROOT / "docs" / "ops" / "paper_forward_analysis" / "ws_replay_pilot"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output or (out_dir / f"pilot_ws_maker_replay_{stamp}.json")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_dir": str(archive_dir),
        "dates": rows,
        "gate_ws_archive_days_target": 14,
        "pilot_ready": any(r.get("anchor_found") for r in rows),
        "notes": (
            "Full validation requires >=14 days WS archive (~2026-07-06). "
            "Compare sample_yes_ask_dollars to paper fill_vwap when trades exist."
        ),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {out_path}")
    return 0 if payload["pilot_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
