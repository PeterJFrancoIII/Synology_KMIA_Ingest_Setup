#!/usr/bin/env python3

from pathlib import Path
import math
import pandas as pd
import matplotlib.pyplot as plt

import os
ROOT = Path(os.environ.get("KMIA_ROOT", "/data/KMIA_Ingest"))
DATA = ROOT / "processed" / "points" / "station=KMIA"
YEAR = os.environ.get("KMIA_YEAR", "2020")
FORECAST_CSV = Path(os.environ.get("KMIA_FORECAST_CSV", DATA / f"ndfd_kmia_point_forecasts_VALID_ONLY_{YEAR}.csv"))
OBS_RAW = Path(os.environ.get("KMIA_OBS_CSV", DATA / f"kmia_ncei_global_hourly_{YEAR}.csv"))
OUT_DIR = Path(os.environ.get("KMIA_CHART_OUT_DIR", DATA))
OUT_CSV = OUT_DIR / f"kmia_{YEAR}_PLUS_mean_median_stability_wind_points.csv"
OUT_DAILY_CSV = OUT_DIR / f"kmia_{YEAR}_PLUS_mean_median_stability_wind_daily_summary.csv"
OUT_CHART = OUT_DIR / f"kmia_{YEAR}_stability_wind.png"

MAX_HOURS_BEFORE_TARGET_ANCHOR = 36.0
TARGET_ANCHOR_HOUR_ET = 16

def deg_to_arrow(deg):
    if pd.isna(deg):
        return "·"
    # Meteorological wind direction is direction FROM.
    # Arrow here shows approximate flow direction TO.
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

print("Loading forecast data...")
raw = pd.read_csv(FORECAST_CSV)

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
            raw_min_f=("value_f", "min"),
            raw_max_f=("value_f", "max"),
            raw_rows=("value_f", "size"),
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

print("Loading observed data...")
obs = pd.read_csv(OBS_RAW, low_memory=False)
obs["DATE"] = pd.to_datetime(obs["DATE"], errors="coerce", utc=True)

tmp_parts = obs["TMP"].astype(str).str.split(",", expand=True)
obs["tmp_raw"] = pd.to_numeric(tmp_parts[0], errors="coerce")
obs = obs[obs["tmp_raw"].notna()].copy()
obs = obs[obs["tmp_raw"] != 9999].copy()

obs["temp_c"] = obs["tmp_raw"] / 10.0
obs["temp_f"] = obs["temp_c"] * 9.0 / 5.0 + 32.0
obs["target_date_et"] = obs["DATE"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
obs["obs_time_et"] = obs["DATE"].dt.tz_convert("America/New_York")
obs["obs_hour_et"] = obs["obs_time_et"].dt.hour + obs["obs_time_et"].dt.minute / 60.0
obs["observed_wdir_deg"] = obs["WND"].apply(parse_wnd_dir) if "WND" in obs.columns else math.nan

obs_sorted = obs.sort_values(
    ["target_date_et", "temp_f", "obs_time_et"],
    ascending=[True, False, True]
).copy()

daily_obs = (
    obs_sorted.groupby("target_date_et", as_index=False)
        .first()[["target_date_et", "temp_f", "obs_time_et", "obs_hour_et", "observed_wdir_deg"]]
        .rename(columns={"temp_f": "observed_max_f"})
)

daily_obs["observed_max_time_et"] = daily_obs["obs_time_et"].dt.strftime("%m-%d %I:%M%p")
daily_obs["observed_wdir_arrow"] = daily_obs["observed_wdir_deg"].apply(deg_to_arrow)
daily_obs["observed_wdir_cardinal"] = daily_obs["observed_wdir_deg"].apply(deg_to_cardinal)

timing_stats = daily_obs.dropna(subset=["obs_hour_et"]).copy()
mean_obs_hour = timing_stats["obs_hour_et"].mean() if not timing_stats.empty else None
median_obs_hour = timing_stats["obs_hour_et"].median() if not timing_stats.empty else None
earliest_obs_hour = timing_stats["obs_hour_et"].min() if not timing_stats.empty else None
latest_obs_hour = timing_stats["obs_hour_et"].max() if not timing_stats.empty else None

target_dates = sorted(points["target_date_et"].unique())

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
daily["median_error_f"] = daily["median_forecast_f"] - daily["observed_max_f"]
daily["mean_error_f"] = daily["mean_forecast_f"] - daily["observed_max_f"]
daily["latest_error_f"] = daily["latest_forecast_f"] - daily["observed_max_f"]
daily["forecast_stability"] = daily.apply(classify_stability, axis=1)
daily["outcome_class"] = daily.apply(classify_outcome, axis=1)

points = points.merge(
    daily_obs[[
        "target_date_et",
        "observed_max_f",
        "observed_max_time_et",
        "observed_wdir_deg",
        "observed_wdir_arrow",
        "observed_wdir_cardinal",
    ]],
    on="target_date_et",
    how="left"
)
points["error_f"] = points["forecast_temp_f"] - points["observed_max_f"]

x_positions = {day: i for i, day in enumerate(target_dates)}
daily["x"] = daily["target_date_et"].map(x_positions)
points["x"] = points["target_date_et"].map(x_positions)

points.to_csv(OUT_CSV, index=False)
daily.to_csv(OUT_DAILY_CSV, index=False)

print(f"Wrote point CSV: {OUT_CSV}")
print(f"Wrote daily summary CSV: {OUT_DAILY_CSV}")

n_days = len(target_dates)
fig_w = max(24, n_days * 1.1)
fig, ax = plt.subplots(figsize=(fig_w, 11))

ax.vlines(daily["x"], daily["min_forecast_f"], daily["max_forecast_f"], linewidth=14, alpha=0.18, label="Forecasted range", zorder=1)
ax.scatter(points["x"], points["forecast_temp_f"], s=72, alpha=0.95, label="Individual forecast release", zorder=3)

ax.scatter(daily["x"], daily["mean_forecast_f"], marker="D", s=70, label="Mean forecast", zorder=5)
ax.scatter(daily["x"], daily["median_forecast_f"], marker="_", s=450, linewidths=2.6, label="Median forecast", zorder=6)
ax.plot(daily["x"], daily["latest_forecast_f"], marker="o", linewidth=2, label="Latest forecast", zorder=2)
ax.scatter(daily["x"], daily["observed_max_f"], marker="x", s=150, linewidths=2.8, label="Observed max", zorder=7)

for row in daily.itertuples(index=False):
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
            zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.72),
        )

for row in daily.itertuples(index=False):
    ax.annotate(
        f"mean {row.mean_forecast_f:.1f}°",
        xy=(row.x, row.mean_forecast_f),
        xytext=(8, -10),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=7.5,
        zorder=8,
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
        zorder=8,
        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.65),
    )

y_top = max(daily["max_forecast_f"].max(), daily["observed_max_f"].max()) + 1.5

for row in daily.itertuples(index=False):
    label = f"{row.forecast_stability}\n{row.outcome_class}\nrange {row.forecast_range_f:.1f}°"
    ax.annotate(
        label,
        xy=(row.x, y_top),
        xytext=(0, 0),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        zorder=8,
        bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.78),
    )

for day, g in points.groupby("target_date_et"):
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
            rotation=0,
            zorder=6,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.72),
        )

ax.set_xticks(list(x_positions.values()))
ax.set_xticklabels(target_dates, rotation=35, ha="right")
ax.set_xlim(-0.5, len(target_dates) - 0.2)

ax.set_title(f"KMIA NDFD Forecasts vs Observed Max — {YEAR}")
ax.set_xlabel("Target date")
ax.set_ylabel("Forecasted / observed max temperature °F")
ax.grid(axis="y", alpha=0.25)
ax.legend(loc="best", fontsize=8)

timing_text = (
    "Observed max timing\n"
    f"Mean: {hour_to_label(mean_obs_hour)}\n"
    f"Median: {hour_to_label(median_obs_hour)}\n"
    f"Range: {hour_to_label(earliest_obs_hour)}–{hour_to_label(latest_obs_hour)}\n"
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

plt.tight_layout()
plt.savefig(OUT_CHART, dpi=220)
print(f"Wrote chart: {OUT_CHART}")
