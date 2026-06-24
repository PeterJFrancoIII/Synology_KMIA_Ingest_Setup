#!/usr/bin/env python3
"""Build week-of-year expected daily-max hour priors for dynamic trading window.

Uses ISD-derived obs_hour_et from accuracy_points_enriched.csv (research only).
Each target week pools ±window_days surrounding dates in that ISO week.

NO REAL TRADING EXECUTION — Console 2 research export only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

_DEFAULT_CSV = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv"
)
_DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/expected_max_hour_priors.json"
)

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 RESEARCH ONLY",
}


def _obs_hour_from_row(row: pd.Series) -> Optional[float]:
    if "obs_hour_et" in row.index and pd.notna(row["obs_hour_et"]):
        return float(row["obs_hour_et"])
    if "obs_time_et" not in row.index or pd.isna(row["obs_time_et"]):
        return None
    try:
        ts = pd.to_datetime(row["obs_time_et"])
        return float(ts.hour) + float(ts.minute) / 60.0
    except (TypeError, ValueError):
        return None


def daily_obs_hours(df: pd.DataFrame) -> pd.DataFrame:
    """One row per target_date_et with observed max hour (ET decimal)."""
    work = df.copy()
    work["target_date_et"] = work["target_date_et"].astype(str)
    if "obs_hour_et" not in work.columns:
        work["obs_hour_et"] = work.apply(_obs_hour_from_row, axis=1)
    daily = (
        work.sort_values(["target_date_et", "obs_hour_et"])
        .groupby("target_date_et", as_index=False)
        .first()[["target_date_et", "obs_hour_et"]]
    )
    daily = daily.dropna(subset=["obs_hour_et"])
    daily["week"] = pd.to_datetime(daily["target_date_et"]).dt.isocalendar().week.astype(int)
    daily["doy"] = pd.to_datetime(daily["target_date_et"]).dt.dayofyear
    return daily


def build_week_priors(
    daily: pd.DataFrame,
    *,
    window_days: int = 7,
) -> dict[str, Any]:
    """Pool obs hours for dates within ±window_days of each week's center."""
    if daily.empty:
        return {"weeks": {}, "meta": {"n_days": 0}}

    all_doy = daily[["target_date_et", "doy", "obs_hour_et"]].copy()
    weeks: dict[str, Any] = {}

    for week in sorted(daily["week"].unique()):
        center_rows = daily[daily["week"] == week]
        center_doys = center_rows["doy"].tolist()
        pool_hours: list[float] = []
        for doy in center_doys:
            lo = doy - window_days
            hi = doy + window_days
            mask = (all_doy["doy"] >= lo) & (all_doy["doy"] <= hi)
            pool_hours.extend(all_doy.loc[mask, "obs_hour_et"].astype(float).tolist())
        if not pool_hours:
            continue
        s = pd.Series(pool_hours)
        weeks[f"week:{int(week):02d}"] = {
            "median_hour_et": round(float(s.median()), 2),
            "p10_hour_et": round(float(s.quantile(0.10)), 2),
            "p90_hour_et": round(float(s.quantile(0.90)), 2),
            "mean_hour_et": round(float(s.mean()), 2),
            "n_samples": int(len(pool_hours)),
            "window_days": window_days,
        }

    return {
        "generated_at_utc": datetime.utcnow().replace(tzinfo=None).isoformat() + "Z",
        "safety": dict(_SAFETY),
        "schema_version": "1.0",
        "window_days": window_days,
        "trading_cutoff_rule": "expected_median_max_hour_et_minus_1h",
        "n_days": int(len(daily)),
        "weeks": weeks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build expected max-hour priors by ISO week")
    parser.add_argument("--csv", type=Path, default=_DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--window-days", type=int, default=7)
    args = parser.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")

    df = pd.read_csv(args.csv)
    daily = daily_obs_hours(df)
    payload = build_week_priors(daily, window_days=args.window_days)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} ({len(payload['weeks'])} weeks, {payload['n_days']} days)")


if __name__ == "__main__":
    main()
