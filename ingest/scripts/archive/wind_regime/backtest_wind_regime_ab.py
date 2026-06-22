#!/usr/bin/env python3
"""A/B backtest: baseline vs season-stratified wind regime probability shifts.

Replays Kalshi price-history days with the recommended trading policy
(maker_limit, 26% edge, integer_dist_v1) and compares:

- baseline: no wind shift
- forecast_wind: shift from ``forecast_wdir_cardinal`` at anchor (deployable)
- forecast_wind_jja_only: same, but shift applied only in JJA
- observed_wind_oracle: shift from ``observed_wdir_cardinal`` (upper bound)

NO REAL TRADING — Console 2 research only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
_ARCHIVE_DIR = Path(__file__).resolve().parent
if str(_ARCHIVE_DIR) not in sys.path:
    sys.path.insert(0, str(_ARCHIVE_DIR))

import pandas as pd

from historical_checksum_backtest import (
    _ensure_within_columns,
    _settle_hedged_trade,
    select_anchor_row,
)
from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    default_kalshi_observed_jsonl,
    default_kmia_daily_history_jsonl,
    forecast_high_at_anchor,
    load_settlement_observed_maxes,
    nws_wind_compass_at_anchor,
    observed_wind_compass_at_daily_max,
)
from iem_mos_forecast_archive import default_iem_mos_archive_path
from kalshi_price_history_loader import (
    DEFAULT_ORDER_MODE,
    MAX_ENTRY_YES_ASK,
    ORDER_MODE_MAKER_LIMIT,
    discover_price_history_files,
    evaluate_hedged_open_purchase,
    find_market_bin_for_temp,
    load_price_history_csv,
    prices_at_anchor,
)
from kalshi_wind_regime_shifts import load_wind_regime_priors, wind_shift_for_cardinal
from kmia_kalshi_paths import console2_backtest_dir, console2_enriched_csv, kalshi_price_history_dir, optional_existing

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 WIND A/B RESEARCH ONLY",
}

RECOMMENDED_MIN_FORECAST_EDGE = 0.26


def _load_recommended_policy(path: Optional[Path]) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    draft = payload.get("trading_policy_draft") or {}
    rec = payload.get("recommended_policy") or {}
    return {
        "min_forecast_edge": draft.get("min_forecast_edge", rec.get("min_forecast_edge", RECOMMENDED_MIN_FORECAST_EDGE)),
        "max_entry_yes_ask": draft.get("max_entry_yes_ask", MAX_ENTRY_YES_ASK),
        "order_mode": draft.get("order_mode", DEFAULT_ORDER_MODE),
    }


def _day_context_from_enriched(
    day: str,
    enriched_df: pd.DataFrame,
) -> Optional[dict[str, Any]]:
    day_df = enriched_df[enriched_df["target_date_et"] == day]
    anchor_row = select_anchor_row(day_df) if not day_df.empty else None
    if anchor_row is None or pd.isna(anchor_row.get("observed_max_f")):
        return None
    forecast_wdir = (
        str(anchor_row["forecast_wdir_cardinal"])
        if pd.notna(anchor_row.get("forecast_wdir_cardinal"))
        else None
    )
    observed_wdir = (
        str(anchor_row["observed_wdir_cardinal"])
        if pd.notna(anchor_row.get("observed_wdir_cardinal"))
        else None
    )
    return {
        "forecast_temp_f": float(anchor_row["forecast_temp_f"]),
        "observed_max_f": float(anchor_row["observed_max_f"]),
        "forecast_wdir": forecast_wdir,
        "observed_wdir": observed_wdir,
        "forecast_source": "ndfd_enriched_csv",
        "wind_source_note": "enriched_csv",
    }


def _day_context_from_nws(
    day: str,
    *,
    nws_dir: Optional[Path],
    observed_jsonl: Optional[Path],
    ncei_history_jsonl: Optional[Path],
    forecast_reports_dir: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    observed_map = load_settlement_observed_maxes(
        ncei_history_jsonl=ncei_history_jsonl,
        nws_observed_jsonl=observed_jsonl,
    )
    if day not in observed_map:
        return None

    fc = forecast_high_at_anchor(
        day,
        nws_dir=nws_dir,
        reports_dir=forecast_reports_dir,
        iem_mos_archive=iem_mos_archive,
    )
    if not fc.get("found"):
        return None

    observed_max_f = float(observed_map[day])
    forecast_wdir = None
    observed_wdir = None
    if nws_dir:
        w = nws_wind_compass_at_anchor(nws_dir, day)
        if w.get("found"):
            forecast_wdir = w.get("wind_direction_compass")
    if observed_jsonl:
        ow = observed_wind_compass_at_daily_max(observed_jsonl, day, observed_max_f)
        if ow.get("found"):
            observed_wdir = ow.get("wind_direction_compass")

    return {
        "forecast_temp_f": float(fc["forecast_temp_f"]),
        "observed_max_f": observed_max_f,
        "forecast_wdir": forecast_wdir,
        "observed_wdir": observed_wdir,
        "forecast_source": str(fc.get("source") or "nws"),
        "wind_source_note": "nws_snapshot_and_observed_history",
    }


def _summarize_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    traded = [r for r in rows if r.get("open_purchase_eligible")]
    settled = [r for r in traded if r.get("trade")]
    wins = [r for r in settled if r["trade"].get("trade_result") == "WIN"]
    losses = [r for r in settled if r["trade"].get("trade_result") == "LOSS"]
    total_pnl = round(sum(r["trade"].get("simulated_pnl", 0) for r in settled), 2)
    total_deployed = round(sum(r["trade"].get("total_deployed", 0) for r in settled), 2)
    roi_pct = round(100.0 * total_pnl / total_deployed, 2) if total_deployed > 0 else None
    return {
        "n_days_evaluated": len(rows),
        "n_trades": len(traded),
        "n_settled": len(settled),
        "n_wins": len(wins),
        "n_losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(settled), 1) if settled else None,
        "total_simulated_pnl": total_pnl,
        "total_deployed": total_deployed,
        "roi_pct": roi_pct,
        "avg_insurance_legs": (
            round(sum(r["trade"].get("n_insurance_legs", 0) for r in settled) / len(settled), 2)
            if settled else None
        ),
    }


def _variant_shift(
    variant: str,
    *,
    settlement_date: str,
    forecast_wdir: Optional[str],
    observed_wdir: Optional[str],
    priors: dict[str, Any],
) -> dict[str, Any]:
    if variant == "baseline":
        return {"wind_shift_f": 0.0, "regime": None, "wind_source": None, "season": None}
    if variant == "forecast_wind":
        meta = wind_shift_for_cardinal(forecast_wdir, settlement_date_et=settlement_date, priors=priors)
        meta["wind_source"] = "forecast_wdir_cardinal"
        return meta
    if variant == "forecast_wind_jja_only":
        meta = wind_shift_for_cardinal(
            forecast_wdir,
            settlement_date_et=settlement_date,
            priors=priors,
            jja_only=True,
        )
        meta["wind_source"] = "forecast_wdir_cardinal_jja_only"
        return meta
    if variant == "observed_wind_oracle":
        meta = wind_shift_for_cardinal(observed_wdir, settlement_date_et=settlement_date, priors=priors)
        meta["wind_source"] = "observed_wdir_cardinal_oracle"
        return meta
    raise ValueError(f"unknown variant: {variant}")


def _evaluate_day_variant(
    *,
    day: str,
    forecast_temp_f: float,
    observed_max_f: float,
    price_snapshot: dict[str, Any],
    price_df: pd.DataFrame,
    variant: str,
    policy: dict[str, Any],
    priors: dict[str, Any],
    forecast_wdir: Optional[str],
    observed_wdir: Optional[str],
) -> dict[str, Any]:
    shift_meta = _variant_shift(
        variant,
        settlement_date=day,
        forecast_wdir=forecast_wdir,
        observed_wdir=observed_wdir,
        priors=priors,
    )
    market_bin = price_snapshot.get("forecast_market_bin")
    if market_bin is None:
        column_map = price_snapshot.get("column_map", {})
        market_bin = find_market_bin_for_temp(int(round(forecast_temp_f)), column_map)

    purchase = evaluate_hedged_open_purchase(
        price_snapshot["bin_prices_cents"],
        market_bin,
        forecast_temp_f,
        price_snapshot.get("market_bins", list(price_snapshot["bin_prices_cents"].keys())),
        max_entry_yes_ask=policy.get("max_entry_yes_ask", MAX_ENTRY_YES_ASK),
        min_forecast_edge=policy.get("min_forecast_edge", RECOMMENDED_MIN_FORECAST_EDGE),
        order_mode=policy.get("order_mode", ORDER_MODE_MAKER_LIMIT),
        price_df=price_df,
        settlement_date=day,
        anchor_book=price_snapshot.get("_anchor_orderbook"),
        anchor_candle=price_snapshot.get("_anchor_candle"),
        wind_shift_f=float(shift_meta.get("wind_shift_f") or 0.0),
    )

    trade = {}
    if purchase.get("open_purchase_eligible"):
        trade = _settle_hedged_trade(purchase=purchase, observed_max_f=observed_max_f)

    return {
        "target_date_et": day,
        "variant": variant,
        "forecast_temp_f": round(forecast_temp_f, 2),
        "observed_max_f": round(observed_max_f, 2),
        "wind_source": shift_meta.get("wind_source"),
        "wind_direction_compass": shift_meta.get("wind_direction_compass"),
        "regime": shift_meta.get("regime"),
        "season": shift_meta.get("season"),
        "wind_shift_f": shift_meta.get("wind_shift_f", 0.0),
        "open_purchase_eligible": purchase.get("open_purchase_eligible"),
        "model_probability": purchase.get("model_probability"),
        "executable_edge": purchase.get("executable_edge"),
        "forecast_limit_bid": purchase.get("forecast_limit_bid"),
        "trade": trade,
    }


def run_wind_regime_ab(
    *,
    price_history_dir: Path,
    enriched_csv: Path,
    policy_path: Optional[Path] = None,
    priors_path: Optional[Path] = None,
    nws_dir: Optional[Path] = None,
    observed_jsonl: Optional[Path] = None,
    ncei_history_jsonl: Optional[Path] = None,
    forecast_reports_dir: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> dict[str, Any]:
    os.environ.setdefault("KALSHI_BACKTEST_PROB_MODEL", "integer_dist_v1")

    price_history_dir = Path(price_history_dir)
    enriched_csv = Path(enriched_csv)
    if not price_history_dir.is_dir():
        raise FileNotFoundError(f"Price history dir not found: {price_history_dir}")
    if not enriched_csv.is_file():
        raise FileNotFoundError(f"Enriched CSV not found: {enriched_csv}")

    policy = _load_recommended_policy(policy_path)
    priors = load_wind_regime_priors(priors_path)

    enriched_df = pd.read_csv(enriched_csv)
    enriched_df["target_date_et"] = enriched_df["target_date_et"].astype(str)
    enriched_df = _ensure_within_columns(enriched_df)

    price_files = discover_price_history_files(price_history_dir)
    days = sorted(price_files.keys())
    if start_date:
        days = [d for d in days if d >= start_date]
    if end_date:
        days = [d for d in days if d <= end_date]

    variants = ("baseline", "forecast_wind", "forecast_wind_jja_only", "observed_wind_oracle")
    per_variant_rows: dict[str, list[dict[str, Any]]] = {v: [] for v in variants}
    skipped: list[dict[str, str]] = []
    observed_map = load_settlement_observed_maxes(
        ncei_history_jsonl=ncei_history_jsonl,
        nws_observed_jsonl=observed_jsonl,
    )

    for day in days:
        ctx = _day_context_from_enriched(day, enriched_df)
        if ctx is None:
            if day not in observed_map:
                skipped.append({"day": day, "reason": "missing_observed_settlement"})
                continue
            fc = forecast_high_at_anchor(
                day,
                nws_dir=nws_dir,
                reports_dir=forecast_reports_dir,
                iem_mos_archive=iem_mos_archive,
            )
            if not fc.get("found"):
                skipped.append({"day": day, "reason": "missing_forecast_at_anchor"})
                continue
            observed_max_f = float(observed_map[day])
            forecast_wdir = None
            observed_wdir = None
            if nws_dir:
                w = nws_wind_compass_at_anchor(nws_dir, day)
                if w.get("found"):
                    forecast_wdir = w.get("wind_direction_compass")
            if observed_jsonl:
                ow = observed_wind_compass_at_daily_max(observed_jsonl, day, observed_max_f)
                if ow.get("found"):
                    observed_wdir = ow.get("wind_direction_compass")
            ctx = {
                "forecast_temp_f": float(fc["forecast_temp_f"]),
                "observed_max_f": observed_max_f,
                "forecast_wdir": forecast_wdir,
                "observed_wdir": observed_wdir,
                "forecast_source": str(fc.get("source") or "nws"),
                "wind_source_note": "nws_snapshot_and_observed_history",
            }

        forecast_temp_f = ctx["forecast_temp_f"]
        observed_max_f = ctx["observed_max_f"]
        forecast_wdir = ctx.get("forecast_wdir")
        observed_wdir = ctx.get("observed_wdir")

        path = price_files[day]
        price_df, column_map = load_price_history_csv(path)
        price_snapshot = prices_at_anchor(price_df, day, column_map=column_map)
        if not price_snapshot.get("found"):
            skipped.append({"day": day, "reason": "no_anchor_prices"})
            continue

        from kalshi_candle_archive_loader import default_candle_archive_dir, load_anchor_candle_context
        from kalshi_orderbook_archive_loader import default_orderbook_archive_dir, load_anchor_orderbook_context

        ob_dir = default_orderbook_archive_dir()
        candle_dir = default_candle_archive_dir()
        anchor_book = load_anchor_orderbook_context(day, column_map, ob_dir) if ob_dir else None
        anchor_candle = load_anchor_candle_context(day, column_map, candle_dir) if candle_dir else None
        price_snapshot["_anchor_orderbook"] = anchor_book if anchor_book and anchor_book.found else anchor_book
        price_snapshot["_anchor_candle"] = anchor_candle if anchor_candle and anchor_candle.found else anchor_candle

        market_bin = find_market_bin_for_temp(int(round(forecast_temp_f)), column_map)
        price_snapshot["column_map"] = column_map
        price_snapshot["forecast_market_bin"] = market_bin
        price_snapshot["source_file"] = str(path)

        for variant in variants:
            if variant.startswith("forecast") and not forecast_wdir:
                continue
            if variant == "observed_wind_oracle" and not observed_wdir:
                continue
            row = _evaluate_day_variant(
                day=day,
                forecast_temp_f=forecast_temp_f,
                observed_max_f=observed_max_f,
                price_snapshot=price_snapshot,
                price_df=price_df,
                variant=variant,
                policy=policy,
                priors=priors,
                forecast_wdir=forecast_wdir,
                observed_wdir=observed_wdir,
            )
            per_variant_rows[variant].append(row)

    summaries = {v: _summarize_trades(rows) for v, rows in per_variant_rows.items()}
    baseline = summaries.get("baseline", {})
    forecast = summaries.get("forecast_wind", {})
    jja = summaries.get("forecast_wind_jja_only", {})
    oracle = summaries.get("observed_wind_oracle", {})

    def _delta(key: str, other: dict[str, Any]) -> Optional[float]:
        b = baseline.get(key)
        o = other.get(key)
        if b is None or o is None:
            return None
        if isinstance(b, (int, float)) and isinstance(o, (int, float)):
            return round(float(o) - float(b), 2)
        return None

    recommendation = _build_recommendation(
        baseline=baseline,
        forecast=forecast,
        jja=jja,
        oracle=oracle,
        per_variant_rows=per_variant_rows,
    )

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "prob_model": os.environ.get("KALSHI_BACKTEST_PROB_MODEL", "integer_dist_v1"),
        "policy": policy,
        "price_history_dir": str(price_history_dir.resolve()),
        "enriched_csv": str(enriched_csv.resolve()),
        "priors_path": str(priors_path) if priors_path else None,
        "date_range": {"start": days[0] if days else None, "end": days[-1] if days else None},
        "n_days_in_price_history": len(days),
        "n_days_skipped": len(skipped),
        "skipped_sample": skipped[:20],
        "variant_summaries": summaries,
        "delta_vs_baseline": {
            "forecast_wind": {
                "total_simulated_pnl": _delta("total_simulated_pnl", forecast),
                "win_rate_pct": _delta("win_rate_pct", forecast),
                "n_trades": _delta("n_trades", forecast),
            },
            "forecast_wind_jja_only": {
                "total_simulated_pnl": _delta("total_simulated_pnl", jja),
                "win_rate_pct": _delta("win_rate_pct", jja),
                "n_trades": _delta("n_trades", jja),
            },
            "observed_wind_oracle": {
                "total_simulated_pnl": _delta("total_simulated_pnl", oracle),
                "win_rate_pct": _delta("win_rate_pct", oracle),
                "n_trades": _delta("n_trades", oracle),
            },
        },
        "recommendation": recommendation,
        "daily_results": {v: rows for v, rows in per_variant_rows.items()},
    }

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = out_dir / f"wind_regime_ab_{ts}.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(out_path)

    return report


def _build_recommendation(
    *,
    baseline: dict[str, Any],
    forecast: dict[str, Any],
    jja: dict[str, Any],
    oracle: dict[str, Any],
    per_variant_rows: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Decide keep / jja_only / drop from A/B metrics."""
    base_pnl = float(baseline.get("total_simulated_pnl") or 0)
    fc_pnl = float(forecast.get("total_simulated_pnl") or 0)
    jja_pnl = float(jja.get("total_simulated_pnl") or 0)
    fc_trades = int(forecast.get("n_trades") or 0)
    base_trades = int(baseline.get("n_trades") or 0)

    pnl_delta = round(fc_pnl - base_pnl, 2)
    jja_delta = round(jja_pnl - base_pnl, 2)
    trade_delta = fc_trades - base_trades

    # Days where wind changed eligibility or outcome vs baseline
    changed_outcomes = []
    base_by_day = {r["target_date_et"]: r for r in per_variant_rows.get("baseline", [])}
    for row in per_variant_rows.get("forecast_wind", []):
        day = row["target_date_et"]
        base = base_by_day.get(day)
        if not base:
            continue
        base_trade = base.get("trade") or {}
        wind_trade = row.get("trade") or {}
        base_elig = bool(base.get("open_purchase_eligible"))
        wind_elig = bool(row.get("open_purchase_eligible"))
        if base_elig != wind_elig or (
            base_elig and wind_elig
            and base_trade.get("trade_result") != wind_trade.get("trade_result")
        ):
            changed_outcomes.append({
                "day": day,
                "wind_shift_f": row.get("wind_shift_f"),
                "regime": row.get("regime"),
                "baseline_eligible": base_elig,
                "wind_eligible": wind_elig,
                "baseline_pnl": base_trade.get("simulated_pnl"),
                "wind_pnl": wind_trade.get("simulated_pnl"),
            })

    if jja_delta > pnl_delta and jja_delta > 0:
        verdict = "keep_jja_only"
        rationale = (
            "JJA-only wind shifts improve simulated P&L without applying DJF cold-front "
            "confound (hot_unstable negative shift in winter)."
        )
    elif pnl_delta > 0 and trade_delta >= -2:
        verdict = "keep_full_year"
        rationale = (
            "Forecast-wind shifts improve total simulated P&L with stable trade count."
        )
    elif pnl_delta > 0 and trade_delta < -2:
        verdict = "keep_with_caution"
        rationale = (
            "Forecast-wind shifts raise P&L but reduce trade count materially — "
            "review changed days before live deployment."
        )
    elif pnl_delta == 0 and trade_delta == 0:
        verdict = "neutral_drop"
        rationale = "Wind shifts did not change trades or P&L on this sample."
    else:
        verdict = "drop"
        rationale = (
            "Forecast-wind shifts hurt simulated P&L or win rate on this Kalshi sample."
        )

    return {
        "verdict": verdict,
        "rationale": rationale,
        "baseline_pnl": base_pnl,
        "forecast_wind_pnl": fc_pnl,
        "forecast_wind_pnl_delta": pnl_delta,
        "jja_only_pnl_delta": jja_delta,
        "trade_count_delta": trade_delta,
        "oracle_pnl": float(oracle.get("total_simulated_pnl") or 0),
        "n_days_with_outcome_change": len(changed_outcomes),
        "outcome_change_sample": changed_outcomes[:15],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="A/B backtest wind regime probability shifts.")
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--enriched-csv", type=Path, default=None)
    parser.add_argument("--policy-json", type=Path, default=None)
    parser.add_argument("--priors-json", type=Path, default=None)
    parser.add_argument("--start", dest="start_date", default=None)
    parser.add_argument("--end", dest="end_date", default=None)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--observed-jsonl", type=Path, default=None)
    parser.add_argument("--ncei-history-jsonl", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    price_dir = args.price_history_dir or optional_existing(kalshi_price_history_dir())
    if price_dir is None:
        raise SystemExit("Kalshi price history dir not found; set KALSHI_PRICE_DIR")

    enriched = args.enriched_csv or console2_enriched_csv()
    policy_path = args.policy_json or (console2_backtest_dir() / "recommended_policy.json")
    output_dir = args.output_dir or console2_backtest_dir()

    report = run_wind_regime_ab(
        price_history_dir=price_dir,
        enriched_csv=enriched,
        policy_path=policy_path if policy_path.is_file() else None,
        priors_path=args.priors_json,
        nws_dir=args.nws_dir or default_kalshi_nws_dir(),
        observed_jsonl=args.observed_jsonl or default_kalshi_observed_jsonl(),
        ncei_history_jsonl=args.ncei_history_jsonl or default_kmia_daily_history_jsonl(),
        forecast_reports_dir=default_kalshi_forecast_reports_dir(),
        iem_mos_archive=default_iem_mos_archive_path(),
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=output_dir,
    )

    rec = report["recommendation"]
    summaries = report["variant_summaries"]
    print("=== Wind regime A/B backtest ===")
    for variant, summary in summaries.items():
        print(
            f"{variant:24s}  trades={summary.get('n_trades')}  "
            f"win_rate={summary.get('win_rate_pct')}%  "
            f"pnl=${summary.get('total_simulated_pnl')}  "
            f"roi={summary.get('roi_pct')}%"
        )
    print(f"\nVERDICT: {rec['verdict']}")
    print(rec["rationale"])
    if report.get("output_path"):
        print(f"\nWrote {report['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
