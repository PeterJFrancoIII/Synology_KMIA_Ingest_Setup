#!/usr/bin/env python3
"""Validate NBM spread prior vs historical forecast instability (hard gate).

Produces nbm_validation_report.json — production requires pass: true.

NO REAL TRADING EXECUTION — Console 2 research only.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from kalshi_nws_join import (
    default_kalshi_forecast_reports_dir,
    default_kalshi_nws_dir,
    default_kmia_daily_history_jsonl,
    forecast_high_at_anchor,
    load_settlement_observed_maxes_with_sources,
)
from kalshi_price_history_loader import (
    default_price_history_dir,
    discover_price_history_files,
    find_market_bin_for_temp,
    load_price_history_csv,
    model_probs_for_market_bins,
    temp_satisfies_bin_label,
)

_DEFAULT_ENRICHED = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv"
)
_DEFAULT_NBM = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/nbm_maxt_archive.jsonl"
)
_DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/nbm_validation_report.json"
)

PASS_SPEARMAN = 0.35
PASS_INSURANCE_MASS_ERR = 0.15


def _spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 5 or len(xs) != len(ys):
        return 0.0
    n = len(xs)
    rx = pd.Series(xs).rank().tolist()
    ry = pd.Series(ys).rank().tolist()
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def load_nbm_by_date(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        d = row.get("date_et")
        if d:
            out[str(d)] = row
    return out


def historical_week_instability(enriched_csv: Path) -> dict[int, float]:
    df = pd.read_csv(enriched_csv)
    if "forecast_range_f" not in df.columns:
        return {}
    df["target_date_et"] = df["target_date_et"].astype(str)
    daily = df.groupby("target_date_et", as_index=False)["forecast_range_f"].max()
    daily["week"] = pd.to_datetime(daily["target_date_et"]).dt.isocalendar().week.astype(int)
    return daily.groupby("week")["forecast_range_f"].mean().to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="NBM vs historical stability validation")
    parser.add_argument("--enriched-csv", type=Path, default=_DEFAULT_ENRICHED)
    parser.add_argument("--nbm-jsonl", type=Path, default=_DEFAULT_NBM)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--min-spearman", type=float, default=PASS_SPEARMAN)
    args = parser.parse_args()

    hist_week = historical_week_instability(args.enriched_csv)
    nbm = load_nbm_by_date(args.nbm_jsonl)

    nws = default_kalshi_nws_dir()
    reports = default_kalshi_forecast_reports_dir()
    ncei = default_kmia_daily_history_jsonl()
    price_dir = default_price_history_dir()
    temps, _ = load_settlement_observed_maxes_with_sources(ncei_history_jsonl=ncei)

    day_rows: list[dict[str, Any]] = []
    insurance_mass_errors: list[float] = []

    if price_dir and ncei:
        for day, path in sorted(discover_price_history_files(price_dir).items()):
            if day not in temps:
                continue
            fc = forecast_high_at_anchor(day, nws_dir=nws, reports_dir=reports)
            if not fc.get("found"):
                continue
            forecast_temp = float(fc["forecast_temp_f"])
            _, column_map = load_price_history_csv(path)
            market_bins = list(dict.fromkeys(column_map.values()))
            market_bin = find_market_bin_for_temp(int(round(forecast_temp)), column_map)
            if not market_bin:
                continue
            rules_probs = model_probs_for_market_bins(
                forecast_temp_f=forecast_temp,
                market_bins=market_bins,
            )
            nbm_row = nbm.get(day)
            nbm_width = None
            nbm_probs = rules_probs
            if nbm_row:
                nbm_width = float(nbm_row.get("p90_f", 0)) - float(nbm_row.get("p10_f", 0))
                from kalshi_integer_distribution import std_f_from_nbm_band

                std_f = std_f_from_nbm_band(
                    float(nbm_row.get("p10_f", forecast_temp - 2)),
                    float(nbm_row.get("p90_f", forecast_temp + 2)),
                )
                nbm_probs = model_probs_for_market_bins(
                    forecast_temp_f=forecast_temp,
                    market_bins=market_bins,
                    std_f=std_f,
                )
            obs_int = int(round(temps[day]))
            won = temp_satisfies_bin_label(obs_int, market_bin)
            day_rows.append({
                "day": day,
                "market_bin": market_bin,
                "rules_forecast_p": round(float(rules_probs.get(market_bin, 0)), 4),
                "nbm_forecast_p": round(float(nbm_probs.get(market_bin, 0)), 4),
                "settlement_won": int(won),
                "nbm_width_f": nbm_width,
            })
            if nbm_row:
                rules_neighbor = sum(
                    p for b, p in rules_probs.items() if b != market_bin
                )
                nbm_neighbor = sum(
                    p for b, p in nbm_probs.items() if b != market_bin
                )
                if rules_neighbor > 0:
                    insurance_mass_errors.append(
                        abs(nbm_neighbor - rules_neighbor) / rules_neighbor
                    )

    week_nbm: dict[int, list[float]] = {}
    for d, row in nbm.items():
        try:
            wk = datetime.strptime(d, "%Y-%m-%d").isocalendar().week
        except ValueError:
            continue
        width = float(row.get("p90_f", 0)) - float(row.get("p10_f", 0))
        week_nbm.setdefault(wk, []).append(width)
    nbm_week_mean = {wk: sum(v) / len(v) for wk, v in week_nbm.items() if v}

    common_weeks = sorted(set(hist_week) & set(nbm_week_mean))
    xs = [hist_week[w] for w in common_weeks]
    ys = [nbm_week_mean[w] for w in common_weeks]
    spearman = round(_spearman(xs, ys), 4) if common_weeks else 0.0
    ins_err = (
        round(sum(insurance_mass_errors) / len(insurance_mass_errors), 4)
        if insurance_mass_errors else None
    )

    pass_gate = bool(
        spearman >= args.min_spearman
        and (ins_err is None or ins_err <= PASS_INSURANCE_MASS_ERR)
        and len(day_rows) >= 10
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pass": pass_gate,
        "criteria": {
            "min_spearman_week_instability": args.min_spearman,
            "max_insurance_neighbor_mass_error": PASS_INSURANCE_MASS_ERR,
            "min_day_rows": 10,
        },
        "metrics": {
            "spearman_week_instability": spearman,
            "insurance_neighbor_mass_error_mean": ins_err,
            "n_day_rows": len(day_rows),
            "n_nbm_archive_days": len(nbm),
        },
        "day_sample": day_rows[:30],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} pass={pass_gate} spearman={spearman}")


if __name__ == "__main__":
    main()
