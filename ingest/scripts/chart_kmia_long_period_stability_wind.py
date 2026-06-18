#!/usr/bin/env python3
"""
Golden-master static chart for longer periods.

- detail: full per-release labels, chunked (default 7 days/page) — matches 4-day golden master readability
- overview: full date span, daily envelope only (no per-release label stack)
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

MAX_HOURS_BEFORE_TARGET_ANCHOR = 36.0
TARGET_ANCHOR_HOUR_ET = 16
DEFAULT_CHUNK_DAYS = 7


def deg_to_arrow(deg):
    if pd.isna(deg):
        return "·"
    flow = (float(deg) + 180.0) % 360.0
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    idx = int((flow + 22.5) // 45) % 8
    return arrows[idx]


def deg_to_cardinal(deg):
    if pd.isna(deg):
        return "NA"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((float(deg) + 22.5) // 45) % 8
    return dirs[idx]


def parse_wnd_dir(wnd_value):
    try:
        first = str(wnd_value).split(",")[0]
        deg = float(first)
        if deg >= 999:
            return math.nan
        return deg
    except Exception:
        return math.nan


def classify_stability(row):
    r = row["forecast_range_f"]
    std = row["forecast_std_f"]
    delta = abs(row["first_to_latest_change_f"])
    if pd.isna(r):
        return "NO DATA"
    if r <= 1.5 and std <= 0.75 and delta <= 1.0:
        return "STABLE"
    if r <= 3.0 and std <= 1.5 and delta <= 2.0:
        return "MIXED"
    return "UNSTABLE"


def classify_outcome(row):
    obs = row["observed_max_f"]
    lo = row["min_forecast_f"]
    hi = row["max_forecast_f"]
    if pd.isna(obs) or pd.isna(lo) or pd.isna(hi):
        return "NO VERIFY"
    if lo <= obs <= hi:
        return "VERIFIED"
    if obs > hi:
        return "WARM BUST" if obs - hi >= 2 else "WARM MISS"
    if obs < lo:
        return "COOL BUST" if lo - obs >= 2 else "COOL MISS"
    return "UNKNOWN"


def hour_to_label(h):
    if h is None or pd.isna(h):
        return "N/A"
    hour = int(h)
    minute = int(round((h - hour) * 60))
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {suffix}"


def load_prepared_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict]:
    forecast_csv = data_dir / "ndfd_kmia_point_forecasts_VALID_ONLY.csv"
    obs_csv = data_dir / "kmia_ncei_global_hourly_2020.csv"

    raw = pd.read_csv(forecast_csv)
    raw["grib_ref_time_utc"] = pd.to_datetime(raw["grib_ref_time_utc"], errors="coerce", utc=True)
    raw["valid_time_utc"] = pd.to_datetime(raw["valid_time_utc"], errors="coerce", utc=True)
    raw["value_f"] = pd.to_numeric(raw["value_f"], errors="coerce")
    raw["value_native"] = pd.to_numeric(raw["value_native"], errors="coerce")
    raw = raw.dropna(subset=["grib_ref_time_utc", "valid_time_utc"])
    raw["target_date_et"] = raw["valid_time_utc"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    raw["release_time_et"] = raw["grib_ref_time_utc"].dt.tz_convert("America/New_York")

    target_anchor_et = pd.to_datetime(
        raw["target_date_et"] + f" {TARGET_ANCHOR_HOUR_ET:02d}:00:00"
    ).dt.tz_localize("America/New_York")
    raw["hours_before_target_anchor"] = (
        target_anchor_et - raw["release_time_et"]
    ).dt.total_seconds() / 3600.0
    raw = raw[
        (raw["hours_before_target_anchor"] >= 0)
        & (raw["hours_before_target_anchor"] <= MAX_HOURS_BEFORE_TARGET_ANCHOR)
    ].copy()

    maxt = raw[raw["requested_subcategory"].eq("maxt")].dropna(subset=["value_f"]).copy()
    wdir = raw[raw["requested_subcategory"].eq("wdir")].dropna(subset=["value_native"]).copy()

    points = (
        maxt.groupby(["target_date_et", "release_time_et"], as_index=False)
        .agg(
            forecast_temp_f=("value_f", "median"),
            hours_before_target_anchor=("hours_before_target_anchor", "median"),
        )
        .sort_values(["target_date_et", "release_time_et"])
    )
    if not wdir.empty:
        wdir_points = (
            wdir.groupby(["target_date_et", "release_time_et"], as_index=False)
            .agg(forecast_wdir_deg=("value_native", "median"))
        )
        points = points.merge(wdir_points, on=["target_date_et", "release_time_et"], how="left")
    else:
        points["forecast_wdir_deg"] = math.nan

    points["forecast_wdir_arrow"] = points["forecast_wdir_deg"].apply(deg_to_arrow)
    points["forecast_wdir_cardinal"] = points["forecast_wdir_deg"].apply(deg_to_cardinal)
    points["release_label"] = (
        points["release_time_et"].dt.strftime("%m-%d %I:%M%p")
        + " | "
        + points["hours_before_target_anchor"].round(1).astype(str)
        + "h"
    )

    obs = pd.read_csv(obs_csv, low_memory=False)
    obs["DATE"] = pd.to_datetime(obs["DATE"], errors="coerce", utc=True)
    tmp_parts = obs["TMP"].astype(str).str.split(",", expand=True)
    obs["tmp_raw"] = pd.to_numeric(tmp_parts[0], errors="coerce")
    obs = obs[obs["tmp_raw"].notna() & (obs["tmp_raw"] != 9999)].copy()
    obs["temp_f"] = obs["tmp_raw"] / 10.0 * 9.0 / 5.0 + 32.0
    obs["target_date_et"] = obs["DATE"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    obs["obs_time_et"] = obs["DATE"].dt.tz_convert("America/New_York")
    obs["obs_hour_et"] = obs["obs_time_et"].dt.hour + obs["obs_time_et"].dt.minute / 60.0
    obs["observed_wdir_deg"] = obs["WND"].apply(parse_wnd_dir) if "WND" in obs.columns else math.nan

    obs_sorted = obs.sort_values(["target_date_et", "temp_f", "obs_time_et"], ascending=[True, False, True])
    daily_obs = (
        obs_sorted.groupby("target_date_et", as_index=False)
        .first()[["target_date_et", "temp_f", "obs_time_et", "obs_hour_et", "observed_wdir_deg"]]
        .rename(columns={"temp_f": "observed_max_f"})
    )
    daily_obs["observed_max_time_et"] = daily_obs["obs_time_et"].dt.strftime("%m-%d %I:%M%p")
    daily_obs["observed_wdir_arrow"] = daily_obs["observed_wdir_deg"].apply(deg_to_arrow)
    daily_obs["observed_wdir_cardinal"] = daily_obs["observed_wdir_deg"].apply(deg_to_cardinal)

    daily_range = (
        points.groupby("target_date_et", as_index=False)
        .agg(
            min_forecast_f=("forecast_temp_f", "min"),
            max_forecast_f=("forecast_temp_f", "max"),
            mean_forecast_f=("forecast_temp_f", "mean"),
            median_forecast_f=("forecast_temp_f", "median"),
            forecast_std_f=("forecast_temp_f", "std"),
            first_forecast_f=("forecast_temp_f", "first"),
            latest_forecast_f=("forecast_temp_f", "last"),
            release_count=("forecast_temp_f", "size"),
        )
    )
    daily_range["forecast_std_f"] = daily_range["forecast_std_f"].fillna(0.0)
    daily_range["forecast_range_f"] = daily_range["max_forecast_f"] - daily_range["min_forecast_f"]
    daily_range["first_to_latest_change_f"] = daily_range["latest_forecast_f"] - daily_range["first_forecast_f"]

    daily = daily_range.merge(daily_obs, on="target_date_et", how="left")
    daily["forecast_stability"] = daily.apply(classify_stability, axis=1)
    daily["outcome_class"] = daily.apply(classify_outcome, axis=1)

    points = points.merge(
        daily_obs[
            [
                "target_date_et",
                "observed_max_f",
                "observed_max_time_et",
                "observed_wdir_deg",
                "observed_wdir_arrow",
                "observed_wdir_cardinal",
            ]
        ],
        on="target_date_et",
        how="left",
    )
    points["error_f"] = points["forecast_temp_f"] - points["observed_max_f"]

    target_dates = sorted(points["target_date_et"].unique())
    timing_stats = daily_obs.dropna(subset=["obs_hour_et"])
    timing = {
        "mean": timing_stats["obs_hour_et"].mean() if not timing_stats.empty else None,
        "median": timing_stats["obs_hour_et"].median() if not timing_stats.empty else None,
        "earliest": timing_stats["obs_hour_et"].min() if not timing_stats.empty else None,
        "latest": timing_stats["obs_hour_et"].max() if not timing_stats.empty else None,
    }
    return points, daily, target_dates, timing


def chunk_dates(dates: list[str], chunk_days: int) -> list[list[str]]:
    chunks = []
    for i in range(0, len(dates), chunk_days):
        chunks.append(dates[i : i + chunk_days])
    return chunks


def add_timing_box(ax, timing: dict) -> None:
    timing_text = (
        "Observed max timing\n"
        f"Mean: {hour_to_label(timing['mean'])}\n"
        f"Median: {hour_to_label(timing['median'])}\n"
        f"Range: {hour_to_label(timing['earliest'])}–{hour_to_label(timing['latest'])}\n"
        "Wind arrows show flow direction"
    )
    ax.text(
        0.01,
        0.02,
        timing_text,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.78),
    )


def render_overview(
    daily: pd.DataFrame,
    points: pd.DataFrame,
    target_dates: list[str],
    timing: dict,
    title: str,
    out_path: Path,
) -> None:
    x_positions = {day: i for i, day in enumerate(target_dates)}
    daily = daily.copy()
    daily["x"] = daily["target_date_et"].map(x_positions)
    points = points.copy()
    points["x"] = points["target_date_et"].map(x_positions)

    n_days = len(target_dates)
    fig_w = max(16, min(48, n_days * 0.55))
    fig, ax = plt.subplots(figsize=(fig_w, 9))

    ax.vlines(daily["x"], daily["min_forecast_f"], daily["max_forecast_f"], linewidth=10, alpha=0.18, label="Forecast range")
    ax.scatter(points["x"], points["forecast_temp_f"], s=18, alpha=0.35, label="Forecast releases", zorder=3)
    ax.scatter(daily["x"], daily["mean_forecast_f"], marker="D", s=42, label="Mean forecast", zorder=5)
    ax.scatter(daily["x"], daily["median_forecast_f"], marker="_", s=280, linewidths=2.0, label="Median forecast", zorder=6)
    ax.plot(daily["x"], daily["latest_forecast_f"], marker="o", linewidth=1.5, markersize=4, label="Latest forecast", zorder=2)
    ax.scatter(daily["x"], daily["observed_max_f"], marker="x", s=90, linewidths=2.0, label="Observed max", zorder=7)

    y_top = max(daily["max_forecast_f"].max(), daily["observed_max_f"].max()) + 1.2
    for row in daily.itertuples(index=False):
        label = f"{row.forecast_stability}\n{row.outcome_class}\nrange {row.forecast_range_f:.1f}°"
        ax.annotate(
            label,
            xy=(row.x, y_top),
            textcoords="offset points",
            xytext=(0, 0),
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.78),
        )

    ax.set_xticks(list(x_positions.values()))
    ax.set_xticklabels(target_dates, rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.5, len(target_dates) - 0.2)
    ax.set_title(title)
    ax.set_xlabel("Target date")
    ax.set_ylabel("Forecasted / observed max temperature °F")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    add_timing_box(ax, timing)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()
    print(f"Wrote overview: {out_path}")


def render_detail_chunk(
    daily: pd.DataFrame,
    points: pd.DataFrame,
    chunk_dates_list: list[str],
    timing: dict,
    title: str,
    out_path: Path,
) -> None:
    x_positions = {day: i for i, day in enumerate(chunk_dates_list)}
    daily_chunk = daily[daily["target_date_et"].isin(chunk_dates_list)].copy()
    points_chunk = points[points["target_date_et"].isin(chunk_dates_list)].copy()
    daily_chunk["x"] = daily_chunk["target_date_et"].map(x_positions)
    points_chunk["x"] = points_chunk["target_date_et"].map(x_positions)

    n_days = len(chunk_dates_list)
    fig_w = max(14, n_days * 3.2)
    fig, ax = plt.subplots(figsize=(fig_w, 11))

    ax.vlines(daily_chunk["x"], daily_chunk["min_forecast_f"], daily_chunk["max_forecast_f"], linewidth=14, alpha=0.18, label="Forecasted range", zorder=1)
    ax.scatter(points_chunk["x"], points_chunk["forecast_temp_f"], s=72, alpha=0.95, label="Individual forecast release", zorder=3)
    ax.scatter(daily_chunk["x"], daily_chunk["mean_forecast_f"], marker="D", s=70, label="Mean forecast", zorder=5)
    ax.scatter(daily_chunk["x"], daily_chunk["median_forecast_f"], marker="_", s=450, linewidths=2.6, label="Median forecast", zorder=6)
    ax.plot(daily_chunk["x"], daily_chunk["latest_forecast_f"], marker="o", linewidth=2, label="Latest forecast", zorder=2)
    ax.scatter(daily_chunk["x"], daily_chunk["observed_max_f"], marker="x", s=150, linewidths=2.8, label="Observed max", zorder=7)

    for row in daily_chunk.itertuples(index=False):
        if pd.notna(row.observed_max_f):
            obs_arrow = row.observed_wdir_arrow if isinstance(row.observed_wdir_arrow, str) else "·"
            obs_dir = row.observed_wdir_cardinal if isinstance(row.observed_wdir_cardinal, str) else "NA"
            ax.annotate(
                f"OBS {row.observed_max_f:.1f}° {obs_arrow} {obs_dir}\n{row.observed_max_time_et}",
                xy=(row.x, row.observed_max_f),
                xytext=(-12, 0),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.72),
            )

    for row in daily_chunk.itertuples(index=False):
        ax.annotate(
            f"mean {row.mean_forecast_f:.1f}°",
            xy=(row.x, row.mean_forecast_f),
            xytext=(8, -10),
            textcoords="offset points",
            ha="left",
            va="top",
            fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.65),
        )
        ax.annotate(
            f"med {row.median_forecast_f:.1f}°",
            xy=(row.x, row.median_forecast_f),
            xytext=(8, 10),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.65),
        )

    y_top = max(daily_chunk["max_forecast_f"].max(), daily_chunk["observed_max_f"].max()) + 1.5
    for row in daily_chunk.itertuples(index=False):
        label = f"{row.forecast_stability}\n{row.outcome_class}\nrange {row.forecast_range_f:.1f}°"
        ax.annotate(
            label,
            xy=(row.x, y_top),
            textcoords="offset points",
            xytext=(0, 0),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.78),
        )

    for day, g in points_chunk.groupby("target_date_et"):
        g = g.sort_values("forecast_temp_f").copy()
        x = x_positions[day]
        ymax = float(g["forecast_temp_f"].max())
        min_gap_f = 0.45
        label_y_values = []
        last_y = None
        for y in g["forecast_temp_f"].tolist():
            y_label = y if last_y is None else max(y, last_y + min_gap_f)
            label_y_values.append(y_label)
            last_y = y_label
        max_allowed = ymax + 1.8
        if label_y_values and label_y_values[-1] > max_allowed:
            shift = label_y_values[-1] - max_allowed
            label_y_values = [v - shift for v in label_y_values]

        for (_, row), y_label in zip(g.iterrows(), label_y_values):
            ax.plot([x, x + 0.10], [row["forecast_temp_f"], y_label], linewidth=0.6, alpha=0.45, zorder=2)
            arrow = row["forecast_wdir_arrow"]
            cardinal = row["forecast_wdir_cardinal"]
            wind_text = "" if arrow == "·" else f" {arrow} {cardinal}"
            label = f"{row['release_label']}  {row['forecast_temp_f']:.1f}°{wind_text}"
            ax.annotate(
                label,
                xy=(x + 0.11, y_label),
                xytext=(3, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=7.2,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.72),
            )

    ax.set_xticks(list(x_positions.values()))
    ax.set_xticklabels(chunk_dates_list, rotation=35, ha="right")
    ax.set_xlim(-0.5, len(chunk_dates_list) - 0.2)
    ax.set_title(title)
    ax.set_xlabel("Target date")
    ax.set_ylabel("Forecasted / observed max temperature °F")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    add_timing_box(ax, timing)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()
    print(f"Wrote detail: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="KMIA long-period golden-master charts")
    parser.add_argument("--mode", choices=["detail", "overview", "both"], default="both")
    parser.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    parser.add_argument("--title-prefix", default="KMIA NDFD Forecasts vs Observed Max")
    parser.add_argument(
        "--data-dir",
        default=os.environ.get(
            "KMIA_DATA_DIR",
            str(Path(__file__).resolve().parent.parent / "nas_june2020_20260612/processed/points/station=KMIA"),
        ),
    )
    parser.add_argument("--out-dir", default=None, help="Defaults to --data-dir")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir or data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    points, daily, target_dates, timing = load_prepared_data(data_dir)
    if not target_dates:
        raise SystemExit("No target dates in forecast data")

    span = f"{target_dates[0]}_to_{target_dates[-1]}"
    prefix = args.title_prefix

    if args.mode in ("overview", "both"):
        render_overview(
            daily,
            points,
            target_dates,
            timing,
            f"{prefix} — Overview ({len(target_dates)} days)",
            out_dir / f"kmia_stability_wind_overview_{span}.png",
        )

    if args.mode in ("detail", "both"):
        for i, chunk in enumerate(chunk_dates(target_dates, args.chunk_days), start=1):
            chunk_span = f"{chunk[0]}_to_{chunk[-1]}"
            render_detail_chunk(
                daily,
                points,
                chunk,
                timing,
                f"{prefix} — Detail {i} ({chunk[0]} … {chunk[-1]})",
                out_dir / f"kmia_stability_wind_detail_{chunk_span}.png",
            )

    points_out = out_dir / "kmia_PLUS_mean_median_stability_wind_points.csv"
    daily_out = out_dir / "kmia_PLUS_mean_median_stability_wind_daily_summary.csv"
    if not points_out.exists():
        points.to_csv(points_out, index=False)
        daily.to_csv(daily_out, index=False)
        print(f"Wrote CSVs: {points_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
