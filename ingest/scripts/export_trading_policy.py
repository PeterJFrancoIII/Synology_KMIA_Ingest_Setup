#!/usr/bin/env python3
"""Export trading_policy.json draft + optional copy to Console 3 research dir.

Human must set approved_by_human: true on trading_policy.json after review.
NO REAL TRADING — Console 2 export only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from kalshi_price_history_loader import DEFAULT_ORDER_MODE
from kmia_kalshi_paths import console2_backtest_dir, kalshi_research_dir
from trading_policy_manifest import build_trading_policy_manifest

_DEFAULT_BACKTEST_DIR = console2_backtest_dir()
_DEFAULT_KALSHI_RESEARCH = kalshi_research_dir()


def _latest_json(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def _load_recommended(backtest_dir: Path) -> tuple[dict[str, Any], Optional[str]]:
    rec_path = backtest_dir / "recommended_policy.json"
    if not rec_path.is_file():
        sweep = _latest_json(backtest_dir, "policy_sweep_*.json")
        if sweep is None:
            raise FileNotFoundError(f"No recommended_policy or policy_sweep in {backtest_dir}")
        sweep_data = json.loads(sweep.read_text(encoding="utf-8"))
        recommended = sweep_data.get("recommended_policy")
        if not recommended:
            raise ValueError(f"No recommended_policy in {sweep}")
        return recommended, str(sweep)
    payload = json.loads(rec_path.read_text(encoding="utf-8"))
    recommended = payload.get("recommended_policy") or payload
    return recommended, payload.get("source_sweep")


def _policy_diff(approved: dict[str, Any], draft: dict[str, Any]) -> list[str]:
    keys = (
        "order_mode", "min_forecast_edge", "max_entry_yes_ask",
        "insurance_enabled", "require_cheapest_at_open",
    )
    lines: list[str] = []
    for k in keys:
        a, d = approved.get(k), draft.get(k)
        if a != d:
            lines.append(f"  {k}: approved={a!r} → draft={d!r}")
    return lines


def export_trading_policy(
    *,
    backtest_dir: Path,
    kalshi_research_dir: Path,
    order_mode: str = DEFAULT_ORDER_MODE,
    copy_to_kalshi: bool = True,
) -> dict[str, Any]:
    recommended, source_sweep = _load_recommended(backtest_dir)
    approved_path = kalshi_research_dir / "trading_policy.json"
    draft_path = kalshi_research_dir / "trading_policy_draft.json"

    approved_existing: Optional[dict[str, Any]] = None
    if approved_path.is_file():
        approved_existing = json.loads(approved_path.read_text(encoding="utf-8"))

    draft = build_trading_policy_manifest(
        recommended,
        source_sweep=source_sweep,
        approved_by_human=False,
        order_mode=order_mode,
    )
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")

    result: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "draft_path": str(draft_path),
        "approved_path": str(approved_path),
        "draft": draft,
        "diff_lines": [],
        "copied_to_kalshi": False,
    }

    if approved_existing:
        result["diff_lines"] = _policy_diff(approved_existing, draft)

    n_trades = int((draft.get("backtest_metrics") or {}).get("n_trades") or 0)
    if n_trades < 20:
        result["approval_warning"] = (
            f"Low confidence: backtest n_trades={n_trades} < 20. "
            "Hold approve_trading_policy.sh until sample grows or accept low_confidence cap."
        )
        print(f"WARN: {result['approval_warning']}", flush=True)

    if copy_to_kalshi and not approved_path.is_file():
        approved_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")
        result["copied_to_kalshi"] = True
        result["note"] = "No approved policy existed; draft copied to trading_policy.json (review and set approved_by_human)"

    try:
        from update_trade_policies_doc import update_trade_policies_doc

        doc_path = update_trade_policies_doc(backtest_dir=backtest_dir)
        result["trade_policies_doc"] = str(doc_path)
    except FileNotFoundError as exc:
        result["trade_policies_doc_warning"] = str(exc)

    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export trading_policy.json for Console 3.")
    parser.add_argument("--backtest-dir", type=Path, default=_DEFAULT_BACKTEST_DIR)
    parser.add_argument("--kalshi-research-dir", type=Path, default=_DEFAULT_KALSHI_RESEARCH)
    parser.add_argument("--order-mode", default=DEFAULT_ORDER_MODE)
    parser.add_argument("--no-copy", action="store_true", help="Only write draft, do not touch approved")
    args = parser.parse_args(argv)

    out = export_trading_policy(
        backtest_dir=args.backtest_dir,
        kalshi_research_dir=args.kalshi_research_dir,
        order_mode=args.order_mode,
        copy_to_kalshi=not args.no_copy,
    )
    print(f"Draft written: {out['draft_path']}")
    if out.get("diff_lines"):
        print("Diff vs approved trading_policy.json:")
        for line in out["diff_lines"]:
            print(line)
    elif out.get("note"):
        print(out["note"])
    else:
        print("Approved policy unchanged; draft ready for human review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
