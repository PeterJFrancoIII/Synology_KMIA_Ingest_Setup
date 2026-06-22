#!/usr/bin/env python3
"""Plain-English policy review for human approval (Console 2 export).

Writes policy_review_for_human.txt into the backtest output dir and optionally
mirrors to Kalshi processed/status. Does not approve policy.

NO REAL TRADING — review artifact only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from export_trading_policy import export_trading_policy
from kalshi_archive_status import build_archive_status
from kalshi_integer_distribution import active_prob_model
from kmia_kalshi_paths import (
    console2_backtest_dir,
    kalshi_candle_archive_dir,
    kalshi_market_archive_dir,
    kalshi_price_history_dir,
    kalshi_research_dir,
)


def _latest_json(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def _load_json(path: Optional[Path]) -> Optional[dict[str, Any]]:
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return "unknown"


def _money(value: Any) -> str:
    try:
        return f"${float(value):.2f}"
    except (TypeError, ValueError):
        return "unknown"


def _tier_line(label: str, tier: Optional[dict[str, Any]]) -> str:
    if not tier:
        return f"  {label}: (none)"
    return (
        f"  {label}: edge={_pct(tier.get('min_forecast_edge'))} "
        f"cap={_money(tier.get('max_entry_yes_ask'))} "
        f"mode={tier.get('insurance_mode')} "
        f"→ win={tier.get('win_rate_pct')}% ROI={tier.get('roi_pct')}% "
        f"P&L={_money(tier.get('total_pnl'))} n={tier.get('n_trades')}"
    )


def build_human_review_text(
    *,
    draft: dict[str, Any],
    recommended: dict[str, Any],
    backtest: Optional[dict[str, Any]],
    archive: dict[str, Any],
    prob_compare: Optional[dict[str, Any]],
    approved: Optional[dict[str, Any]] = None,
    policy_tiers: Optional[dict[str, Any]] = None,
) -> str:
    lines: list[str] = [
        "KMIA Kalshi Trading Policy — Human Review",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "=== What this policy does ===",
        f"Order style: maker limit bids at prior-day 10 AM Eastern",
        f"Minimum edge: {_pct(draft.get('min_forecast_edge'))}",
        f"Max YES price (forecast leg): {_money(draft.get('max_entry_yes_ask'))}",
        f"Require cheapest bin at open: {draft.get('require_cheapest_at_open')}",
        f"Insurance legs: {'ON' if draft.get('insurance_enabled') else 'OFF'}",
        f"Research confidence: {str(draft.get('confidence', 'unknown')).upper()}",
        "",
        "=== Backtest evidence (historical, not a guarantee) ===",
    ]
    bm = draft.get("backtest_metrics") or recommended
    lines.extend([
        f"Trades with known outcome: {bm.get('n_trades', '?')}",
        f"Win rate: {bm.get('win_rate_pct', '?')}%",
        f"Total simulated P&L: {_money(bm.get('total_pnl'))}",
        f"ROI on deployed: {bm.get('roi_pct', '?')}%",
        f"Avg insurance legs per trade: {bm.get('avg_insurance_legs', '?')}",
    ])
    if policy_tiers:
        sel = (recommended.get("selection_method") or draft.get("selection_method") or "")
        if "max_roi" in sel and "winrate" not in sel:
            draft_label = "MAX ROI (this export)"
        elif "max_pnl" in sel:
            draft_label = "MAX P&L (this export)"
        else:
            draft_label = "RECOMMENDED (balanced ROI × win-rate, win≥68%)"
        lines.extend([
            "",
            f"=== Policy tiers from full sweep ({archive.get('n_price_history_days', '?')} days, 5642 configs) ===",
            f"Draft export uses {draft_label}.",
            _tier_line("Balanced (ROI×win)", policy_tiers.get("recommended_balanced")),
            _tier_line("Max ROI", policy_tiers.get("max_roi")),
            _tier_line("Max ROI guarded (win≥65%)", policy_tiers.get("max_roi_guarded")),
            _tier_line("Max total P&L", policy_tiers.get("max_pnl")),
            "",
            "Note: You cannot maximize ROI, win-rate, and total P&L simultaneously.",
        ])
    if backtest:
        hr = backtest.get("hit_rates") or {}
        lines.extend([
            "",
            "Latest maker backtest run:",
            f"  Days tested: {backtest.get('n_days_tested', '?')}",
            f"  Open purchase eligible rate: {hr.get('open_purchase_eligible_rate', '?')}%",
            f"  Maker fill sources: {hr.get('maker_fill_sources', 'CSV only')}",
            f"  Days with archived orderbook: {backtest.get('n_days_with_anchor_orderbook', 0)}",
            f"  Days with archived candles: {backtest.get('n_days_with_anchor_candle', 0)}",
        ])
    lines.extend([
        "",
        "=== Data coverage ===",
        f"Price history days: {archive.get('n_price_history_days', '?')}",
        f"Orderbook archive match: {archive.get('coverage_pct', {}).get('orderbook_vs_price_days', 0)}%",
        f"Candle archive match: {archive.get('coverage_pct', {}).get('candles_vs_price_days', 0)}%",
        f"Backtest P(bin) model: {active_prob_model()}",
    ])
    if prob_compare:
        lines.append(
            f"Gaussian vs integer_dist max |ΔP|: {prob_compare.get('max_abs_delta', '?')}"
        )
    lines.extend([
        "",
        "=== Approval status ===",
    ])
    stale = False
    if approved and draft:
        for key in ("model_version", "min_forecast_edge", "max_entry_yes_ask", "order_mode"):
            if approved.get(key) != draft.get(key):
                stale = True
                break
    if approved and approved.get("approved_by_human") and not stale:
        lines.append("APPROVED — paper loop uses trading_policy.json")
    elif approved and approved.get("approved_by_human") and stale:
        lines.append(
            "STALE APPROVAL — trading_policy.json was approved but differs from latest draft "
            "(model/edge/cap/mode). Re-approve after review."
        )
    elif approved:
        lines.append("trading_policy.json exists but approved_by_human is false")
    else:
        lines.append("NOT APPROVED — paper loop keeps legacy behavior until you approve")
    lines.extend([
        "",
        "To approve (Kalshi repo):",
        "  bash scripts/approve_trading_policy.sh",
        "Or set approved_by_human: true on backend/data/research/trading_policy.json",
        "",
        "NO REAL TRADING — research and paper simulation only.",
    ])
    return "\n".join(lines) + "\n"


def write_policy_human_review(
    *,
    backtest_dir: Path,
    kalshi_research: Path,
    price_dir: Path,
    orderbook_dir: Path,
    candle_dir: Path,
    mirror_status_dir: Optional[Path] = None,
    export_draft: bool = True,
) -> dict[str, Any]:
    backtest_dir = Path(backtest_dir)
    if export_draft:
        export_trading_policy(
            backtest_dir=backtest_dir,
            kalshi_research_dir=kalshi_research,
            copy_to_kalshi=False,
        )

    draft_path = kalshi_research / "trading_policy_draft.json"
    draft = _load_json(draft_path) or {}
    recommended_path = backtest_dir / "recommended_policy.json"
    rec_payload = _load_json(recommended_path) or {}
    recommended = rec_payload.get("recommended_policy") or rec_payload
    policy_tiers = rec_payload.get("policy_tiers")
    if not policy_tiers:
        sweep_path = rec_payload.get("source_sweep")
        if sweep_path:
            sweep = _load_json(Path(sweep_path))
            if sweep:
                policy_tiers = sweep.get("policy_tiers")
    approved = _load_json(kalshi_research / "trading_policy.json")

    backtest = _load_json(_latest_json(backtest_dir, "kalshi_price_backtest_*.json"))
    prob_compare = _load_json(backtest_dir / "prob_model_comparison.json")
    archive = build_archive_status(
        price_history_dir=price_dir,
        orderbook_archive_dir=orderbook_dir,
        candle_archive_dir=candle_dir,
    )

    text = build_human_review_text(
        draft=draft,
        recommended=recommended,
        backtest=backtest,
        archive=archive,
        prob_compare=prob_compare,
        approved=approved,
        policy_tiers=policy_tiers,
    )

    review_path = backtest_dir / "policy_review_for_human.txt"
    review_path.write_text(text, encoding="utf-8")

    bridge_status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "draft_path": str(draft_path),
        "review_path": str(review_path),
        "archive_coverage": archive.get("coverage_pct"),
        "backtest_prob_model": active_prob_model(),
        "recommended_edge": recommended.get("min_forecast_edge"),
        "approved_by_human": bool(approved and approved.get("approved_by_human")),
    }
    status_path = backtest_dir / "console2_bridge_status.json"
    status_path.write_text(json.dumps(bridge_status, indent=2), encoding="utf-8")

    mirrored: Optional[str] = None
    if mirror_status_dir:
        mirror_status_dir = Path(mirror_status_dir)
        mirror_status_dir.mkdir(parents=True, exist_ok=True)
        mirror = mirror_status_dir / "policy_review_for_human.txt"
        mirror.write_text(text, encoding="utf-8")
        mirrored = str(mirror)

    try:
        from update_trade_policies_doc import update_trade_policies_doc

        doc_path = update_trade_policies_doc(backtest_dir=backtest_dir)
        trade_policies_doc = str(doc_path)
    except FileNotFoundError:
        trade_policies_doc = None

    return {
        "review_path": str(review_path),
        "bridge_status_path": str(status_path),
        "mirrored_review_path": mirrored,
        "trade_policies_doc": trade_policies_doc,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write human policy review artifacts")
    parser.add_argument("--backtest-dir", type=Path, default=console2_backtest_dir())
    parser.add_argument("--kalshi-research-dir", type=Path, default=kalshi_research_dir())
    parser.add_argument("--mirror-status-dir", type=Path, default=None)
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args(argv)

    mirror = args.mirror_status_dir
    if mirror is None:
        default_mirror = (
            kalshi_research_dir().parent / "processed" / "status"
        )
        if default_mirror.parent.is_dir():
            mirror = default_mirror

    out = write_policy_human_review(
        backtest_dir=args.backtest_dir,
        kalshi_research=args.kalshi_research_dir,
        price_dir=kalshi_price_history_dir(),
        orderbook_dir=kalshi_market_archive_dir(),
        candle_dir=kalshi_candle_archive_dir(),
        mirror_status_dir=mirror,
        export_draft=not args.skip_export,
    )
    print(f"Review written: {out['review_path']}")
    if out.get("mirrored_review_path"):
        print(f"Mirrored: {out['mirrored_review_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
