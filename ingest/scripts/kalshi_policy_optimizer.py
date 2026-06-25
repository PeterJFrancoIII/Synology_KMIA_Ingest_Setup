#!/usr/bin/env python3
"""Sweep Kalshi bin-open policy parameters; recommend safest high-profit config.

Probability-first selection: maximize win_rate, then total_pnl, then n_trades.
NO REAL TRADING — Console 2 research export only.

FILE MAP (do not read whole file — jump by line):
  L73-125   worker pool + grid eval helpers
  L126-163  evaluate_config_grid
  L164-251  load_forecast_validated_days
  L270-395  evaluate_policy_config (single config backtest)
  L396-420  pareto_frontier
  L460-599  policy tier selectors (max_pnl, max_roi, balanced, recommended)
  L621-655  default_sweep_grid
  L656-802  run_policy_sweep (writes policy_sweep_*.json)
  L851+     CLI main
Schema sample: ingest/scripts/fixtures/sample_policy_sweep.json
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Optional

from historical_checksum_backtest import (
    _allow_iem_mos_backfill,
    _resolve_iem_mos_archive,
    _settle_hedged_trade,
)
from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    default_kalshi_observed_jsonl,
    default_kmia_daily_history_jsonl,
    forecast_high_at_anchor,
    load_settlement_observed_maxes_with_sources,
)
from kalshi_price_history_loader import (
    DEFAULT_ORDER_MODE,
    MAX_ENTRY_YES_ASK,
    MIN_FORECAST_EXECUTABLE_EDGE,
    default_price_history_dir,
    discover_price_history_files,
    evaluate_hedged_open_purchase,
    find_market_bin_for_temp,
    load_price_history_csv,
    prices_at_anchor,
)
from trading_policy_manifest import build_trading_policy_manifest

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 POLICY RESEARCH ONLY",
}

MODEL_VERSION = "gaussian_v1_truncation_optional"
MIN_TRADES_DEFAULT = 20
LOW_CONFIDENCE_TRADE_THRESHOLD = 20
BALANCED_MIN_WIN_RATE = 0.68
MAX_ROI_MIN_WIN_RATE = 0.65
MAX_CALIBRATION_ECE = 0.12
MAX_MEAN_BRIER = 0.35
PURE_MAX_ROI_MIN_TRADES = 20


def _selection_mode() -> str:
    return os.environ.get("KALSHI_POLICY_SELECTION", "max_roi").strip().lower()

_POLICY_METRIC_KEYS = (
    "min_forecast_edge", "max_entry_yes_ask", "require_cheapest_at_open",
    "insurance_enabled", "insurance_mode", "insurance_budget_fraction",
    "insurance_price_k", "n_trades", "n_wins", "n_losses", "win_rate",
    "win_rate_pct", "total_pnl", "total_deployed", "roi_pct",
    "avg_insurance_legs", "insurance_covers_book_rate_pct",
    "mean_brier", "mean_crps", "ece", "calibration_pass",
)

_MP_DAYS: list[dict[str, Any]] | None = None
_MP_ORDER_MODE: str = DEFAULT_ORDER_MODE


def default_workers() -> int:
    """Parallel config evaluators; cap for NAS 2GB container."""
    raw = os.environ.get("POLICY_SWEEP_WORKERS")
    if raw:
        return max(1, int(raw))
    cpus = os.cpu_count() or 4
    return max(1, min(3, cpus - 1))


def _slim_config_result(result: dict[str, Any]) -> dict[str, Any]:
    slim = {k: v for k, v in result.items() if k != "trades"}
    slim["trade_days"] = [t["day"] for t in result["trades"]]
    return slim


def _mp_init(days: list[dict[str, Any]], order_mode: str) -> None:
    global _MP_DAYS, _MP_ORDER_MODE
    _MP_DAYS = days
    _MP_ORDER_MODE = order_mode


def _eval_params_worker(params: dict[str, Any]) -> dict[str, Any]:
    assert _MP_DAYS is not None
    result = evaluate_policy_config(
        _MP_DAYS,
        min_forecast_edge=params["min_forecast_edge"],
        max_entry_yes_ask=params["max_entry_yes_ask"],
        require_cheapest=params["require_cheapest"],
        insurance_enabled=params["insurance_enabled"],
        insurance_mode=params.get("insurance_mode", "fraction"),
        insurance_budget_fraction=params.get("insurance_budget_fraction", 0.25),
        insurance_price_k=params.get("insurance_price_k", 0.6),
        order_mode=_MP_ORDER_MODE,
    )
    return _slim_config_result(result)


def evaluate_config_grid(
    days: list[dict[str, Any]],
    grid: list[dict[str, Any]],
    *,
    order_mode: str = DEFAULT_ORDER_MODE,
    workers: int = 1,
) -> list[dict[str, Any]]:
    """Evaluate sweep grid; workers>1 uses ProcessPoolExecutor (Linux fork COW)."""
    if workers <= 1 or len(grid) <= 1:
        return [
            _slim_config_result(
                evaluate_policy_config(
                    days,
                    min_forecast_edge=params["min_forecast_edge"],
                    max_entry_yes_ask=params["max_entry_yes_ask"],
                    require_cheapest=params["require_cheapest"],
                    insurance_enabled=params["insurance_enabled"],
                    insurance_mode=params.get("insurance_mode", "fraction"),
                    insurance_budget_fraction=params.get("insurance_budget_fraction", 0.25),
                    insurance_price_k=params.get("insurance_price_k", 0.6),
                    order_mode=order_mode,
                )
            )
            for params in grid
        ]

    configs: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_mp_init,
        initargs=(days, order_mode),
    ) as pool:
        futures = [pool.submit(_eval_params_worker, params) for params in grid]
        for fut in as_completed(futures):
            configs.append(fut.result())
    return configs


def load_forecast_validated_days(
    price_history_dir: Path,
    *,
    nws_dir: Optional[Path] = None,
    forecast_reports_dir: Optional[Path] = None,
    observed_jsonl: Optional[Path] = None,
    ncei_history_jsonl: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    order_mode: str = DEFAULT_ORDER_MODE,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Build day rows with forecast, observed, and bin-open price snapshot."""
    price_history_dir = Path(price_history_dir)
    nws_dir = nws_dir or default_kalshi_nws_dir()
    forecast_reports_dir = forecast_reports_dir or default_kalshi_forecast_reports_dir()
    observed_jsonl = observed_jsonl or default_kalshi_observed_jsonl()
    ncei_history_jsonl = ncei_history_jsonl or default_kmia_daily_history_jsonl()
    observed_map, observed_sources = load_settlement_observed_maxes_with_sources(
        ncei_history_jsonl=ncei_history_jsonl,
    )

    from kalshi_orderbook_archive_loader import (
        default_orderbook_archive_dir,
        load_anchor_orderbook_context,
    )

    archive_dir = orderbook_archive_dir or default_orderbook_archive_dir()

    from kalshi_candle_archive_loader import (
        default_candle_archive_dir,
        load_anchor_candle_context,
    )

    candle_dir = candle_archive_dir or default_candle_archive_dir()

    rows: list[dict[str, Any]] = []
    for day, path in sorted(discover_price_history_files(price_history_dir).items()):
        df, column_map = load_price_history_csv(path)
        snap = prices_at_anchor(df, day, column_map=column_map)
        if not snap.get("found"):
            continue

        anchor_book = None
        if archive_dir is not None:
            anchor_book = load_anchor_orderbook_context(day, column_map, archive_dir)

        anchor_candle = None
        if candle_dir is not None:
            anchor_candle = load_anchor_candle_context(day, column_map, candle_dir)

        forecast_temp: Optional[float] = None
        forecast_source = "none"
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

        if forecast_temp is None:
            continue

        market_bin = find_market_bin_for_temp(int(round(forecast_temp)), column_map)
        if not market_bin:
            continue

        rows.append({
            "day": day,
            "forecast_temp_f": forecast_temp,
            "forecast_source": forecast_source,
            "observed_max_f": observed_map.get(day),
            "prices": snap["bin_prices_cents"],
            "market_bins": snap.get("market_bins", []),
            "market_bin": market_bin,
            "column_map": column_map,
            "price_df": df,
            "order_mode": order_mode,
            "anchor_orderbook": anchor_book,
            "anchor_candle": anchor_candle,
        })
    return rows


def _policy_eligible(
    purchase: dict[str, Any],
    *,
    require_cheapest: bool,
) -> bool:
    if purchase.get("forecast_bin_yes_ask") is None:
        return False
    if not purchase.get("entry_within_cap"):
        return False
    if not purchase.get("prob_aligned"):
        return False
    if require_cheapest and not purchase.get("forecast_bin_cheapest_at_open"):
        return False
    if int(purchase.get("forecast_contracts") or 0) <= 0:
        return False
    return True


def evaluate_policy_config(
    days: list[dict[str, Any]],
    *,
    min_forecast_edge: float,
    max_entry_yes_ask: float,
    require_cheapest: bool,
    insurance_enabled: bool,
    insurance_mode: str = "fraction",
    insurance_budget_fraction: float = 0.25,
    insurance_price_k: float = 0.6,
    order_mode: str = DEFAULT_ORDER_MODE,
) -> dict[str, Any]:
    """Replay hedged policy on observed days; return aggregate metrics."""
    from calibration_metrics import (
        crps_multiclass,
        expected_calibration_error,
        reliability_table,
    )

    trades: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    brier_scores: list[float] = []
    crps_scores: list[float] = []
    ins_frac = insurance_budget_fraction if insurance_enabled else 0.0

    for d in days:
        if d["observed_max_f"] is None:
            continue

        ins_frac = insurance_budget_fraction if insurance_enabled else 0.0
        purchase = evaluate_hedged_open_purchase(
            d["prices"],
            d["market_bin"],
            d["forecast_temp_f"],
            d["market_bins"],
            min_forecast_edge=min_forecast_edge,
            max_entry_yes_ask=max_entry_yes_ask,
            insurance_budget_fraction=ins_frac,
            insurance_price_k=insurance_price_k,
            insurance_mode=insurance_mode if insurance_enabled else "fraction",
            order_mode=order_mode,
            price_df=d.get("price_df"),
            settlement_date=d["day"],
            anchor_book=d.get("anchor_orderbook"),
            anchor_candle=d.get("anchor_candle"),
        )
        if not purchase.get("open_purchase_eligible"):
            continue
        if order_mode == "taker" and require_cheapest and not purchase.get("forecast_bin_cheapest_at_open"):
            continue

        if not insurance_enabled:
            purchase = {**purchase, "insurance_legs": [], "insurance_total_cost": 0.0}
            purchase["total_deployed"] = float(purchase.get("forecast_total_cost") or 0.0)

        trade = _settle_hedged_trade(purchase=purchase, observed_max_f=d["observed_max_f"])
        model_p = purchase.get("model_probability")
        if model_p is not None:
            won = trade["trade_result"] == "WIN"
            calibration_rows.append({
                "model_probability": float(model_p),
                "won": int(won),
            })
            brier_scores.append((float(model_p) - float(won)) ** 2)
            bin_probs = purchase.get("model_bin_probs") or {d["market_bin"]: float(model_p)}
            obs_bin = d["market_bin"] if won else f"__other__{d['day']}"
            if won:
                crps_scores.append(crps_multiclass(bin_probs, d["market_bin"]))
        trades.append({
            "day": d["day"],
            "market_bin": d["market_bin"],
            "won": trade["trade_result"] == "WIN",
            "pnl": trade["simulated_pnl"],
            "deployed": trade["total_deployed"],
            "n_insurance_legs": trade.get("n_insurance_legs", 0),
            "insurance_covers_book": trade.get("insurance_covers_book", False),
            "executable_edge": purchase.get("executable_edge"),
        })

    n_trades = len(trades)
    n_wins = sum(1 for t in trades if t["won"])
    total_pnl = round(sum(t["pnl"] for t in trades), 4)
    total_deployed = round(sum(t["deployed"] for t in trades), 4)
    win_rate = round(n_wins / n_trades, 4) if n_trades else 0.0
    roi_pct = round(100.0 * total_pnl / total_deployed, 2) if total_deployed else 0.0
    covers = sum(1 for t in trades if t.get("insurance_covers_book"))
    reliability = reliability_table(calibration_rows)
    ece = expected_calibration_error(reliability)
    mean_brier = round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None
    mean_crps = round(sum(crps_scores) / len(crps_scores), 4) if crps_scores else None
    calibration_pass = (
        ece <= MAX_CALIBRATION_ECE
        and (mean_brier is None or mean_brier <= MAX_MEAN_BRIER)
    )

    return {
        "min_forecast_edge": min_forecast_edge,
        "max_entry_yes_ask": max_entry_yes_ask,
        "require_cheapest_at_open": require_cheapest,
        "insurance_enabled": insurance_enabled,
        "insurance_mode": insurance_mode if insurance_enabled else None,
        "insurance_budget_fraction": ins_frac if insurance_enabled else 0.0,
        "insurance_price_k": insurance_price_k if insurance_enabled else None,
        "n_trades": n_trades,
        "n_wins": n_wins,
        "n_losses": n_trades - n_wins,
        "win_rate": win_rate,
        "win_rate_pct": round(100.0 * win_rate, 1),
        "total_pnl": total_pnl,
        "total_deployed": total_deployed,
        "roi_pct": roi_pct,
        "avg_insurance_legs": round(
            sum(t["n_insurance_legs"] for t in trades) / n_trades, 2
        ) if n_trades else 0.0,
        "insurance_covers_book_rate_pct": round(
            100.0 * covers / n_trades, 1
        ) if n_trades else 0.0,
        "mean_brier": mean_brier,
        "mean_crps": mean_crps,
        "ece": ece,
        "reliability": reliability,
        "calibration_pass": calibration_pass,
        "trades": trades,
    }


def pareto_frontier(configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Non-dominated configs in win_rate x total_pnl (higher is better)."""
    eligible = [c for c in configs if c["n_trades"] > 0]
    frontier: list[dict[str, Any]] = []
    for cand in eligible:
        dominated = False
        for other in eligible:
            if other is cand:
                continue
            if (
                other["win_rate"] >= cand["win_rate"]
                and other["total_pnl"] >= cand["total_pnl"]
                and (
                    other["win_rate"] > cand["win_rate"]
                    or other["total_pnl"] > cand["total_pnl"]
                )
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(cand)
    frontier.sort(key=lambda c: (c["win_rate"], c["total_pnl"]), reverse=True)
    return frontier


def _insured_pool(
    configs: list[dict[str, Any]],
    *,
    min_trades: int,
) -> list[dict[str, Any]]:
    pool = [c for c in configs if c["n_trades"] >= min_trades and c.get("insurance_enabled")]
    if not pool:
        pool = [c for c in configs if c["n_trades"] > 0 and c.get("insurance_enabled")]
    if not pool:
        pool = [c for c in configs if c["n_trades"] > 0]
    calibrated = [c for c in pool if c.get("calibration_pass", True)]
    return calibrated if calibrated else pool


def _confidence_for(best: dict[str, Any]) -> tuple[str, Optional[str]]:
    confidence = (
        "low" if best["n_trades"] < LOW_CONFIDENCE_TRADE_THRESHOLD else "moderate"
    )
    reason = (
        f"n_trades={best['n_trades']} < {LOW_CONFIDENCE_TRADE_THRESHOLD}"
        if confidence == "low" else None
    )
    return confidence, reason


def _policy_result(
    best: dict[str, Any],
    *,
    selection_method: str,
) -> dict[str, Any]:
    confidence, low_confidence_reason = _confidence_for(best)
    return {
        **{k: best[k] for k in _POLICY_METRIC_KEYS if k in best},
        "selection_method": selection_method,
        "confidence": confidence,
        "low_confidence_reason": low_confidence_reason,
    }


def select_max_pnl_policy(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = MIN_TRADES_DEFAULT,
) -> Optional[dict[str, Any]]:
    """Insured config with enough sample size; maximize total P&L, then ROI."""
    pool = _insured_pool(configs, min_trades=min_trades)
    if not pool:
        return None
    pool.sort(
        key=lambda c: (
            c["total_pnl"],
            c["roi_pct"],
            c["n_trades"],
            -c["max_entry_yes_ask"],
        ),
        reverse=True,
    )
    return _policy_result(pool[0], selection_method="max_total_pnl_insured_min_sample_then_roi")


def select_max_roi_policy(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = MIN_TRADES_DEFAULT,
    min_win_rate: float = MAX_ROI_MIN_WIN_RATE,
) -> Optional[dict[str, Any]]:
    """Maximize ROI among insured configs with minimum win-rate floor."""
    pool = [
        c for c in _insured_pool(configs, min_trades=min_trades)
        if c["win_rate"] >= min_win_rate
    ]
    if not pool:
        pool = _insured_pool(configs, min_trades=min_trades)
    if not pool:
        return None
    pool.sort(
        key=lambda c: (
            c["roi_pct"],
            c["win_rate"],
            c["min_forecast_edge"],
            c["total_pnl"],
            -abs(c["max_entry_yes_ask"] - MAX_ENTRY_YES_ASK),
        ),
        reverse=True,
    )
    return _policy_result(
        pool[0],
        selection_method=f"max_roi_insured_min_win_{int(min_win_rate * 100)}pct",
    )


def select_balanced_policy(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = MIN_TRADES_DEFAULT,
    min_win_rate: float = BALANCED_MIN_WIN_RATE,
) -> Optional[dict[str, Any]]:
    """Balance ROI and safety: maximize ROI×win_rate with win-rate floor and edge tie-break."""
    pool = [
        c for c in _insured_pool(configs, min_trades=min_trades)
        if c["win_rate"] >= min_win_rate
    ]
    if not pool:
        pool = _insured_pool(configs, min_trades=min_trades)
    if not pool:
        return None
    pool.sort(
        key=lambda c: (
            c["roi_pct"] * c["win_rate"],
            c["roi_pct"],
            c["min_forecast_edge"],
            c["win_rate"],
            c["total_pnl"],
            -abs(c["max_entry_yes_ask"] - MAX_ENTRY_YES_ASK),
        ),
        reverse=True,
    )
    return _policy_result(
        pool[0],
        selection_method=f"max_roi_x_winrate_insured_min_win_{int(min_win_rate * 100)}pct",
    )


def select_pure_max_roi_policy(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = PURE_MAX_ROI_MIN_TRADES,
) -> Optional[dict[str, Any]]:
    """Maximize ROI with minimum sample size only (no win-rate floor)."""
    pool = _insured_pool(configs, min_trades=min_trades)
    if not pool:
        return None
    pool.sort(
        key=lambda c: (
            c["roi_pct"],
            c["total_pnl"],
            c["win_rate"],
            c["min_forecast_edge"],
            c["n_trades"],
            -abs(c["max_entry_yes_ask"] - MAX_ENTRY_YES_ASK),
        ),
        reverse=True,
    )
    return _policy_result(
        pool[0],
        selection_method=f"max_roi_insured_min_trades_{min_trades}",
    )


def select_recommended_policy(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = MIN_TRADES_DEFAULT,
    selection: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Default export driven by KALSHI_POLICY_SELECTION or --selection."""
    mode = (selection or _selection_mode()).lower()
    if mode == "max_pnl":
        return select_max_pnl_policy(configs, min_trades=min_trades)
    if mode == "balanced":
        return select_balanced_policy(configs, min_trades=min_trades)
    if mode == "max_roi_guarded":
        return select_max_roi_policy(configs, min_trades=min_trades)
    # default: pure max ROI
    return select_pure_max_roi_policy(configs, min_trades=min_trades)


def select_policy_tiers(
    configs: list[dict[str, Any]],
    *,
    min_trades: int = MIN_TRADES_DEFAULT,
) -> dict[str, Optional[dict[str, Any]]]:
    return {
        "recommended_balanced": select_balanced_policy(configs, min_trades=min_trades),
        "max_roi": select_pure_max_roi_policy(configs, min_trades=min_trades),
        "max_roi_guarded": select_max_roi_policy(configs, min_trades=min_trades),
        "max_pnl": select_max_pnl_policy(configs, min_trades=min_trades),
    }


def _cap_grid_values(
    *,
    cap_min: Optional[float] = None,
    cap_max: Optional[float] = None,
    cap_step: float = 0.05,
) -> list[float]:
    """Build max_entry_yes_ask sweep values (default 0.15–0.45 step 0.05)."""
    lo = 0.15 if cap_min is None else float(cap_min)
    hi = 0.45 if cap_max is None else float(cap_max)
    step = float(cap_step)
    if step <= 0:
        raise ValueError("cap_step must be positive")
    caps: list[float] = []
    v = lo
    while v <= hi + 1e-9:
        caps.append(round(v, 4))
        v += step
    return caps


def default_sweep_grid(
    *,
    cap_values: Optional[list[float]] = None,
) -> list[dict[str, Any]]:
    edges = [round(i / 100, 2) for i in range(0, 31)]
    caps = cap_values or _cap_grid_values()
    insurance_modes = ["fraction", "cover_book"]
    insurance_budgets = [0.25, 0.5, 1.0]
    insurance_ks = [0.5, 0.6]
    grid: list[dict[str, Any]] = []
    for edge, cap, cheapest, ins in product(edges, caps, [True, False], [True, False]):
        if ins:
            for mode, ibudget, ik in product(insurance_modes, insurance_budgets, insurance_ks):
                grid.append({
                    "min_forecast_edge": edge,
                    "max_entry_yes_ask": cap,
                    "require_cheapest": cheapest,
                    "insurance_enabled": True,
                    "insurance_mode": mode,
                    "insurance_budget_fraction": ibudget,
                    "insurance_price_k": ik,
                })
        else:
            grid.append({
                "min_forecast_edge": edge,
                "max_entry_yes_ask": cap,
                "require_cheapest": cheapest,
                "insurance_enabled": False,
                "insurance_mode": "fraction",
                "insurance_budget_fraction": 0.25,
                "insurance_price_k": 0.6,
            })
    return grid


def run_policy_sweep(
    *,
    price_history_dir: Path,
    nws_dir: Optional[Path] = None,
    forecast_reports_dir: Optional[Path] = None,
    observed_jsonl: Optional[Path] = None,
    ncei_history_jsonl: Optional[Path] = None,
    iem_mos_archive: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    min_trades: int = MIN_TRADES_DEFAULT,
    order_mode: str = DEFAULT_ORDER_MODE,
    workers: Optional[int] = None,
    orderbook_archive_dir: Optional[Path] = None,
    candle_archive_dir: Optional[Path] = None,
    selection: Optional[str] = None,
    cap_min: Optional[float] = None,
    cap_max: Optional[float] = None,
    cap_step: float = 0.05,
) -> dict[str, Any]:
    days = load_forecast_validated_days(
        price_history_dir,
        nws_dir=nws_dir,
        forecast_reports_dir=forecast_reports_dir,
        observed_jsonl=observed_jsonl,
        ncei_history_jsonl=ncei_history_jsonl,
        iem_mos_archive=iem_mos_archive,
        order_mode=order_mode,
        orderbook_archive_dir=orderbook_archive_dir,
        candle_archive_dir=candle_archive_dir,
    )
    observed_days = [d for d in days if d["observed_max_f"] is not None]

    cap_values = _cap_grid_values(cap_min=cap_min, cap_max=cap_max, cap_step=cap_step)
    grid = default_sweep_grid(cap_values=cap_values)
    n_workers = workers if workers is not None else default_workers()
    configs = evaluate_config_grid(days, grid, order_mode=order_mode, workers=n_workers)

    frontier = pareto_frontier(configs)
    tiers = select_policy_tiers(configs, min_trades=min_trades)
    recommended = select_recommended_policy(
        configs, min_trades=min_trades, selection=selection,
    )

    from kalshi_orderbook_archive_loader import default_orderbook_archive_dir

    from kalshi_candle_archive_loader import default_candle_archive_dir

    resolved_orderbook_archive = orderbook_archive_dir or default_orderbook_archive_dir()
    resolved_candle_archive = candle_archive_dir or default_candle_archive_dir()

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "model_version": MODEL_VERSION,
        "order_mode": order_mode,
        "selection_method": recommended.get("selection_method") if recommended else None,
        "price_history_dir": str(Path(price_history_dir).resolve()),
        "orderbook_archive_dir": (
            str(Path(resolved_orderbook_archive).resolve())
            if resolved_orderbook_archive else None
        ),
        "candle_archive_dir": (
            str(Path(resolved_candle_archive).resolve())
            if resolved_candle_archive else None
        ),
        "n_days_with_anchor_orderbook": sum(
            1 for d in days if getattr(d.get("anchor_orderbook"), "found", False)
        ),
        "n_days_with_anchor_candle": sum(
            1 for d in days if getattr(d.get("anchor_candle"), "found", False)
        ),
        "n_forecast_validated_days": len(days),
        "n_observed_days": len(observed_days),
        "current_defaults": {
            "min_forecast_edge": MIN_FORECAST_EXECUTABLE_EDGE,
            "max_entry_yes_ask": MAX_ENTRY_YES_ASK,
        },
        "sweep_grid": {
            "edge_pct": "0-30 step 1",
            "max_entry_yes_ask": {
                "values": cap_values,
                "min": cap_values[0] if cap_values else None,
                "max": cap_values[-1] if cap_values else None,
                "step": cap_step,
                "n_values": len(cap_values),
            },
            "require_cheapest_at_open": [True, False],
            "insurance_enabled": [True, False],
            "n_configs": len(configs),
            "workers": n_workers,
        },
        "configs": configs,
        "pareto_frontier": [
            {k: c[k] for k in (
                "min_forecast_edge", "max_entry_yes_ask", "require_cheapest_at_open",
                "insurance_enabled", "n_trades", "win_rate_pct", "total_pnl",
            )}
            for c in frontier
        ],
        "recommended_policy": recommended,
        "policy_tiers": tiers,
        "human_summary": _format_summary(days, configs, recommended, frontier, tiers),
    }

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        sweep_path = out_dir / f"policy_sweep_{ts}.json"
        sweep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["sweep_path"] = str(sweep_path)

        if recommended:
            rec_path = out_dir / "recommended_policy.json"
            manifest = build_trading_policy_manifest(
                recommended,
                source_sweep=str(sweep_path),
                approved_by_human=False,
                order_mode=order_mode,
            )
            rec_payload = {
                "generated_at_utc": report["generated_at_utc"],
                "safety": report["safety"],
                "model_version": MODEL_VERSION,
                "source_sweep": str(sweep_path),
                "recommended_policy": recommended,
                "policy_tiers": tiers,
                "trading_policy_draft": manifest,
            }
            rec_path.write_text(json.dumps(rec_payload, indent=2), encoding="utf-8")
            report["recommended_policy_path"] = str(rec_path)

            draft_path = out_dir / "trading_policy_draft.json"
            draft_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            report["trading_policy_draft_path"] = str(draft_path)

            try:
                from update_trade_policies_doc import update_trade_policies_doc

                doc_path = update_trade_policies_doc(backtest_dir=out_dir)
                report["trade_policies_doc"] = str(doc_path)
            except FileNotFoundError:
                pass

    return report


def _format_summary(
    days: list[dict[str, Any]],
    configs: list[dict[str, Any]],
    recommended: Optional[dict[str, Any]],
    frontier: list[dict[str, Any]],
    tiers: Optional[dict[str, Optional[dict[str, Any]]]] = None,
) -> str:
    observed = sum(1 for d in days if d["observed_max_f"] is not None)
    traded_configs = sum(1 for c in configs if c["n_trades"] > 0)
    parts = [
        f"Policy sweep: {len(configs)} configs over {len(days)} forecast days "
        f"({observed} observed, {traded_configs} configs with trades).",
    ]
    if recommended:
        parts.append(
            f"Recommended ({recommended.get('selection_method', 'selected')}, n≥{MIN_TRADES_DEFAULT}): "
            f"edge={recommended['min_forecast_edge']:.0%}, "
            f"cap=${recommended['max_entry_yes_ask']:.2f}, "
            f"mode={recommended.get('insurance_mode')}, "
            f"cheapest={recommended['require_cheapest_at_open']}, "
            f"insurance={recommended['insurance_enabled']} → "
            f"win={recommended['win_rate_pct']:.1f}% "
            f"({recommended['n_wins']}/{recommended['n_trades']}), "
            f"ROI={recommended['roi_pct']:.1f}%, "
            f"P&L=${recommended['total_pnl']:.2f} "
            f"[{recommended['confidence']} confidence]."
        )
    else:
        parts.append("No config met min_trades threshold.")
    if tiers:
        alt = tiers.get("max_pnl")
        if alt and recommended and alt.get("selection_method") != recommended.get("selection_method"):
            parts.append(
                f"Max-P&L alternative: edge={alt['min_forecast_edge']:.0%} → "
                f"win={alt['win_rate_pct']:.1f}% ROI={alt['roi_pct']:.1f}% "
                f"P&L=${alt['total_pnl']:.2f}."
            )
        roi_alt = tiers.get("max_roi")
        if roi_alt and recommended and roi_alt.get("roi_pct", 0) > recommended.get("roi_pct", 0):
            parts.append(
                f"Max-ROI alternative (win≥{int(MAX_ROI_MIN_WIN_RATE*100)}%): "
                f"edge={roi_alt['min_forecast_edge']:.0%} → "
                f"win={roi_alt['win_rate_pct']:.1f}% ROI={roi_alt['roi_pct']:.1f}%."
            )
    parts.append(f"Pareto frontier: {len(frontier)} non-dominated configs.")
    return " ".join(parts)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sweep Kalshi bin-open policy; export recommended probability-first config."
    )
    parser.add_argument("--price-history-dir", type=Path, default=None)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--forecast-reports-dir", type=Path, default=None)
    parser.add_argument("--observed-jsonl", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--min-trades", type=int, default=MIN_TRADES_DEFAULT)
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel sweep workers (default: min(3, cpu_count-1); env POLICY_SWEEP_WORKERS)",
    )
    parser.add_argument(
        "--orderbook-archive-dir",
        type=Path,
        default=None,
        help="kalshi_market_archive orderbooks JSONL root (default: Kalshi processed dir)",
    )
    parser.add_argument(
        "--candle-archive-dir",
        type=Path,
        default=None,
        help="kalshi_candle_archive JSONL root (default: Kalshi processed dir)",
    )
    parser.add_argument(
        "--selection",
        choices=("max_roi", "max_roi_guarded", "balanced", "max_pnl"),
        default=None,
        help="Policy export selection (default: env KALSHI_POLICY_SELECTION or max_roi)",
    )
    parser.add_argument(
        "--order-mode",
        choices=("taker", "maker_limit"),
        default=os.environ.get("KALSHI_BACKTEST_ORDER_MODE", DEFAULT_ORDER_MODE),
        help="Execution model for sweep (default: env KALSHI_BACKTEST_ORDER_MODE or maker_limit)",
    )
    parser.add_argument(
        "--cap-min",
        type=float,
        default=None,
        help="Minimum max_entry_yes_ask in sweep (default 0.15)",
    )
    parser.add_argument(
        "--cap-max",
        type=float,
        default=None,
        help="Maximum max_entry_yes_ask in sweep (default 0.45)",
    )
    parser.add_argument(
        "--cap-step",
        type=float,
        default=0.05,
        help="Step for max_entry_yes_ask grid (use 0.01 for fine cap search)",
    )
    args = parser.parse_args(argv)

    price_dir = args.price_history_dir or default_price_history_dir()
    if price_dir is None:
        raise SystemExit("Price history dir not found; pass --price-history-dir")

    default_out = (
        Path(__file__).resolve().parents[2]
        / "Research"
        / "Agent Analysis of KMIA Forecast Precision"
        / "Kalshi_Price_Backtest"
    )
    report = run_policy_sweep(
        price_history_dir=price_dir,
        nws_dir=args.nws_dir or default_kalshi_nws_dir(),
        forecast_reports_dir=args.forecast_reports_dir or default_kalshi_forecast_reports_dir(),
        observed_jsonl=args.observed_jsonl or default_kalshi_observed_jsonl(),
        ncei_history_jsonl=default_kmia_daily_history_jsonl(),
        iem_mos_archive=_resolve_iem_mos_archive(None),
        output_dir=args.output_dir or default_out,
        min_trades=args.min_trades,
        workers=args.workers,
        orderbook_archive_dir=args.orderbook_archive_dir,
        candle_archive_dir=args.candle_archive_dir,
        selection=args.selection,
        order_mode=args.order_mode,
        cap_min=args.cap_min,
        cap_max=args.cap_max,
        cap_step=args.cap_step,
    )
    print(report["human_summary"])
    if report.get("sweep_path"):
        print(f"Sweep written: {report['sweep_path']}")
    if report.get("recommended_policy_path"):
        print(f"Recommended policy: {report['recommended_policy_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
