#!/usr/bin/env python3
"""
KMIA NDFD max-temperature forecast accuracy analysis.

Answers:
  1. Lead-time accuracy — hours before 4 PM ET anchor vs observed daily max
  2. Weather-condition accuracy — wind regime, stability, forecast range
  3. Seasonal accuracy — month/quarter patterns and drivers

Uses golden-master methodology (4 PM ET anchor, 0–36h window).
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

MAX_HOURS_BEFORE_TARGET_ANCHOR = 36.0
TARGET_ANCHOR_HOUR_ET = 16
ACCURACY_THRESHOLDS_F = (0.0, 1.0, 2.0, 3.0)


def parse_wnd_dir(wnd_value) -> float:
    try:
        deg = float(str(wnd_value).split(",")[0])
        return math.nan if deg >= 999 else deg
    except Exception:
        return math.nan


def deg_to_cardinal(deg: float) -> str:
    if pd.isna(deg):
        return "NA"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((float(deg) + 22.5) // 45) % 8]


def classify_stability(row: pd.Series) -> str:
    r, std, delta = row["forecast_range_f"], row["forecast_std_f"], abs(row["first_to_latest_change_f"])
    if pd.isna(r):
        return "NO DATA"
    if r <= 1.5 and std <= 0.75 and delta <= 1.0:
        return "STABLE"
    if r <= 3.0 and std <= 1.5 and delta <= 2.0:
        return "MIXED"
    return "UNSTABLE"


def classify_outcome(obs, lo, hi) -> str:
    if pd.isna(obs) or pd.isna(lo) or pd.isna(hi):
        return "NO VERIFY"
    if lo <= obs <= hi:
        return "VERIFIED"
    if obs > hi:
        return "WARM BUST" if obs - hi >= 2 else "WARM MISS"
    if obs < lo:
        return "COOL BUST" if lo - obs >= 2 else "COOL MISS"
    return "UNKNOWN"


def load_forecast_points(forecast_csv: Path) -> pd.DataFrame:
    raw = pd.read_csv(forecast_csv, low_memory=False)
    raw["grib_ref_time_utc"] = pd.to_datetime(raw["grib_ref_time_utc"], errors="coerce", utc=True)
    raw["valid_time_utc"] = pd.to_datetime(raw["valid_time_utc"], errors="coerce", utc=True)
    raw["value_f"] = pd.to_numeric(raw.get("value_f"), errors="coerce")
    raw["value_native"] = pd.to_numeric(raw.get("value_native"), errors="coerce")
    raw = raw.dropna(subset=["grib_ref_time_utc", "valid_time_utc"])

    raw["target_date_et"] = raw["valid_time_utc"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    raw["release_time_et"] = raw["grib_ref_time_utc"].dt.tz_convert("America/New_York")
    anchor = pd.to_datetime(
        raw["target_date_et"] + f" {TARGET_ANCHOR_HOUR_ET:02d}:00:00"
    ).dt.tz_localize("America/New_York")
    raw["hours_before_target_anchor"] = (anchor - raw["release_time_et"]).dt.total_seconds() / 3600.0
    raw = raw[
        (raw["hours_before_target_anchor"] >= 0)
        & (raw["hours_before_target_anchor"] <= MAX_HOURS_BEFORE_TARGET_ANCHOR)
    ].copy()

    maxt = raw[raw["requested_subcategory"].eq("maxt")].dropna(subset=["value_f"])
    wdir = raw[raw["requested_subcategory"].eq("wdir")].dropna(subset=["value_native"])

    points = (
        maxt.groupby(["target_date_et", "release_time_et"], as_index=False)
        .agg(
            forecast_temp_f=("value_f", "median"),
            hours_before_target_anchor=("hours_before_target_anchor", "median"),
        )
        .sort_values(["target_date_et", "release_time_et"])
    )
    if not wdir.empty:
        wdir_pts = (
            wdir.groupby(["target_date_et", "release_time_et"], as_index=False)
            .agg(forecast_wdir_deg=("value_native", "median"))
        )
        points = points.merge(wdir_pts, on=["target_date_et", "release_time_et"], how="left")
    else:
        points["forecast_wdir_deg"] = math.nan
    points["forecast_wdir_cardinal"] = points["forecast_wdir_deg"].apply(deg_to_cardinal)
    points["lead_hour_bucket"] = points["hours_before_target_anchor"].round().astype(int)
    return points


def load_observed_daily(obs_paths: list[Path]) -> pd.DataFrame:
    frames = []
    for p in obs_paths:
        if not p.exists():
            continue
        obs = pd.read_csv(p, low_memory=False)
        obs["DATE"] = pd.to_datetime(obs["DATE"], errors="coerce", utc=True)
        tmp = pd.to_numeric(obs["TMP"].astype(str).str.split(",").str[0], errors="coerce")
        obs = obs[tmp.notna() & (tmp != 9999)].copy()
        obs["temp_f"] = tmp[obs.index] / 10.0 * 9.0 / 5.0 + 32.0
        obs["target_date_et"] = obs["DATE"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        obs["obs_time_et"] = obs["DATE"].dt.tz_convert("America/New_York")
        obs["observed_wdir_deg"] = obs["WND"].apply(parse_wnd_dir) if "WND" in obs.columns else math.nan
        obs = obs.sort_values(["target_date_et", "temp_f", "obs_time_et"], ascending=[True, False, True])
        daily = (
            obs.groupby("target_date_et", as_index=False)
            .first()[["target_date_et", "temp_f", "obs_time_et", "observed_wdir_deg"]]
            .rename(columns={"temp_f": "observed_max_f"})
        )
        frames.append(daily)
    if not frames:
        raise SystemExit("No observed ISD files found")
    return pd.concat(frames, ignore_index=True).drop_duplicates("target_date_et")


def enrich_points(points: pd.DataFrame, daily_obs: pd.DataFrame) -> pd.DataFrame:
    daily_range = (
        points.groupby("target_date_et", as_index=False)
        .agg(
            min_forecast_f=("forecast_temp_f", "min"),
            max_forecast_f=("forecast_temp_f", "max"),
            forecast_std_f=("forecast_temp_f", "std"),
            first_forecast_f=("forecast_temp_f", "first"),
            latest_forecast_f=("forecast_temp_f", "last"),
        )
    )
    daily_range["forecast_range_f"] = daily_range["max_forecast_f"] - daily_range["min_forecast_f"]
    daily_range["first_to_latest_change_f"] = (
        daily_range["latest_forecast_f"] - daily_range["first_forecast_f"]
    )
    daily_range["forecast_std_f"] = daily_range["forecast_std_f"].fillna(0.0)
    daily_range["forecast_stability"] = daily_range.apply(classify_stability, axis=1)

    df = points.merge(daily_obs, on="target_date_et", how="inner")
    df = df.merge(
        daily_range[["target_date_et", "forecast_stability", "min_forecast_f", "max_forecast_f", "forecast_range_f"]],
        on="target_date_et",
        how="left",
    )
    df["observed_wdir_cardinal"] = df["observed_wdir_deg"].apply(deg_to_cardinal)
    df["abs_error_f"] = (df["forecast_temp_f"] - df["observed_max_f"]).abs()
    df["signed_error_f"] = df["forecast_temp_f"] - df["observed_max_f"]
    for t in ACCURACY_THRESHOLDS_F:
        if t == 0:
            df["within_0f"] = df["forecast_temp_f"].round() == df["observed_max_f"].round()
        else:
            df[f"within_{int(t)}f"] = df["abs_error_f"] <= t
    df["verified_in_daily_range"] = (
        (df["observed_max_f"] >= df["min_forecast_f"]) & (df["observed_max_f"] <= df["max_forecast_f"])
    )
    df["target_dt"] = pd.to_datetime(df["target_date_et"])
    df["month"] = df["target_dt"].dt.month
    df["week_of_year"] = df["target_dt"].dt.isocalendar().week.astype(int)
    df["quarter"] = df["target_dt"].dt.quarter
    season_map = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
                  6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
    df["season"] = df["month"].map(season_map)
    df["sample_season"] = df["month"].apply(sample_season)
    return df


def accuracy_table(df: pd.DataFrame, group_cols: list[str], min_n: int = 30) -> pd.DataFrame:
    rows = []
    for keys, g in df.groupby(group_cols):
        if len(g) < min_n:
            continue
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n_forecasts"] = len(g)
        row["n_target_days"] = g["target_date_et"].nunique()
        row["mae_f"] = g["abs_error_f"].mean()
        row["bias_f"] = g["signed_error_f"].mean()
        for t in ACCURACY_THRESHOLDS_F:
            row[f"pct_within_{int(t)}f"] = 100.0 * g[f"within_{int(t)}f"].mean()
        row["pct_verified_in_range"] = 100.0 * g["verified_in_daily_range"].mean()
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("pct_within_2f", ascending=False)


def best_lead_per_day(df: pd.DataFrame) -> pd.DataFrame:
    """Per target date: lead hour with smallest absolute error."""
    idx = df.groupby("target_date_et")["abs_error_f"].idxmin()
    best = df.loc[idx].copy()
    best["best_lead_hours"] = best["hours_before_target_anchor"].round(1)
    return best[
        ["target_date_et", "best_lead_hours", "forecast_temp_f", "observed_max_f", "abs_error_f", "forecast_stability"]
    ].sort_values("target_date_et")


def sample_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Fall"


def write_report(
    out_dir: Path,
    lead: pd.DataFrame,
    conditions: pd.DataFrame,
    seasonal: pd.DataFrame,
    best_lead: pd.DataFrame,
    df: pd.DataFrame,
    study_name: str | None = None,
    season_sample: pd.DataFrame | None = None,
    lead_by_season: pd.DataFrame | None = None,
) -> None:
    title = study_name or "KMIA Max-Temperature Forecast Accuracy Report"
    lines = [f"# {title}\n"]
    lines.append(f"- Target dates analyzed: **{df['target_date_et'].nunique()}**")
    lines.append(f"- Forecast releases (0–36h before 4 PM ET): **{len(df)}**")
    lines.append(f"- Overall MAE: **{df['abs_error_f'].mean():.2f}°F**")
    lines.append(f"- Overall within 2°F: **{100*df['within_2f'].mean():.1f}%**\n")

    lines.append("## 1. Lead-time accuracy (hours before 4 PM ET anchor)\n")
    if not lead.empty:
        top = lead.nlargest(5, "pct_within_2f")
        for _, r in top.iterrows():
            lines.append(
                f"- **{int(r['lead_hour_bucket'])}h lead**: {r['pct_within_2f']:.1f}% within 2°F "
                f"(MAE {r['mae_f']:.2f}°F, n={int(r['n_forecasts'])})"
            )
        med_best = best_lead["best_lead_hours"].median()
        lines.append(f"\nMedian best lead hour per day: **{med_best:.1f}h** before anchor.\n")

    lines.append("## 2. Weather-condition accuracy\n")
    for col in ["forecast_stability", "observed_wdir_cardinal", "forecast_wdir_cardinal", "range_bucket"]:
        if col not in conditions.columns:
            continue
        sub = conditions[conditions[col].notna() & (conditions[col].astype(str) != "NA")]
        if sub.empty:
            continue
        best = sub.nlargest(1, "pct_within_2f").iloc[0]
        lines.append(f"- Best **{col}** = **{best[col]}**: {best['pct_within_2f']:.1f}% within 2°F (n={int(best['n_forecasts'])})")

    lines.append("\n## 3. Seasonal accuracy\n")
    if season_sample is not None and not season_sample.empty:
        lines.append("### Four-season sample (one month per season)\n")
        for _, r in season_sample.sort_values("pct_within_2f", ascending=False).iterrows():
            lines.append(
                f"- **{r['sample_season']}** (month {int(r['month'])}): "
                f"{r['pct_within_2f']:.1f}% within 2°F, "
                f"{r['pct_within_1f']:.1f}% within 1°F, MAE {r['mae_f']:.2f}°F "
                f"(n={int(r['n_forecasts'])} forecasts, {int(r['n_target_days'])} days)"
            )
        if lead_by_season is not None and not lead_by_season.empty:
            lines.append("\n### Best lead hour by season (highest % within 2°F)\n")
            for season in ["Winter", "Spring", "Summer", "Fall"]:
                sub = lead_by_season[lead_by_season["sample_season"] == season]
                if sub.empty:
                    continue
                top = sub.nlargest(1, "pct_within_2f").iloc[0]
                lines.append(
                    f"- **{season}**: {int(top['lead_hour_bucket'])}h lead — "
                    f"{top['pct_within_2f']:.1f}% within 2°F"
                )
    if not seasonal.empty:
        by_month = seasonal[seasonal["month"].notna()].sort_values("pct_within_2f", ascending=False)
        for _, r in by_month.head(4).iterrows():
            lines.append(
                f"- Month **{int(r['month'])}**: {r['pct_within_2f']:.1f}% within 2°F (MAE {r['mae_f']:.2f}°F)"
            )
        worst = by_month.tail(1).iloc[0]
        lines.append(
            f"- Worst month **{int(worst['month'])}**: {worst['pct_within_2f']:.1f}% within 2°F"
        )
        lines.append(
            "\n**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow "
            "tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing "
            "shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate."
        )

    (out_dir / "accuracy_report.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".", help="KMIA data root (processed/ under here)")
    p.add_argument("--forecast", help="Merged forecast VALID_ONLY CSV (overrides --root)")
    p.add_argument("--obs-glob", help="Glob or comma-separated ISD CSV paths")
    p.add_argument("--out", help="Analysis output directory")
    p.add_argument("--study-name", help="Descriptive study title for report header")
    p.add_argument("--four-season-sample", action="store_true", help="Emit sample_season precision tables")
    args = p.parse_args()

    root = Path(args.root)
    data = root / "processed" / "points" / "station=KMIA"
    out_dir = Path(args.out) if args.out else root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    forecast_csv = Path(args.forecast) if args.forecast else data / "ndfd_kmia_point_forecasts_VALID_ONLY_ALL.csv"
    if not forecast_csv.exists():
        yearly = sorted(data.glob("ndfd_kmia_point_forecasts_VALID_ONLY_20*.csv"))
        if not yearly:
            raise SystemExit(f"No forecast CSV at {forecast_csv}")
        pd.concat([pd.read_csv(f) for f in yearly], ignore_index=True).to_csv(forecast_csv, index=False)
        print(f"Built combined forecast: {forecast_csv}")

    obs_paths = sorted(data.glob("kmia_ncei_global_hourly_20*.csv"))
    if args.obs_glob:
        obs_paths = []
        for part in args.obs_glob.split(","):
            part = part.strip()
            obs_paths.extend(sorted(Path(".").glob(part)) if "*" in part else [Path(part)])
    obs_paths = [Path(p) for p in obs_paths]
    print(f"Loading forecast: {forecast_csv}")
    points = load_forecast_points(forecast_csv)
    daily_obs = load_observed_daily(obs_paths)
    df = enrich_points(points, daily_obs)
    df.to_csv(out_dir / "accuracy_points_enriched.csv", index=False)

    lead = accuracy_table(df, ["lead_hour_bucket"], min_n=5)
    lead.to_csv(out_dir / "lead_hour_accuracy.csv", index=False)

    cond_stab = accuracy_table(df, ["forecast_stability"], min_n=5)
    cond_obs_wind = accuracy_table(df, ["observed_wdir_cardinal"], min_n=5)
    cond_fc_wind = accuracy_table(df, ["forecast_wdir_cardinal"], min_n=5)
    cond_range = accuracy_table(
        df.assign(
            range_bucket=pd.cut(
                df["forecast_range_f"],
                bins=[-0.1, 1.5, 3.0, 100],
                labels=["narrow_<=1.5F", "medium_1.5-3F", "wide_>3F"],
            )
        ),
        ["range_bucket"],
        min_n=5,
    )
    conditions = pd.concat([cond_stab, cond_obs_wind, cond_fc_wind, cond_range], ignore_index=True)
    conditions.to_csv(out_dir / "conditions_accuracy.csv", index=False)

    seasonal_month = accuracy_table(df, ["month"], min_n=5)
    seasonal_month.to_csv(out_dir / "seasonal_by_month.csv", index=False)
    seasonal_week = accuracy_table(df, ["week_of_year"], min_n=5)
    seasonal_week.to_csv(out_dir / "seasonal_by_week_of_year.csv", index=False)
    seasonal_q = accuracy_table(df, ["quarter"], min_n=5)
    seasonal_q.to_csv(out_dir / "seasonal_by_quarter.csv", index=False)
    seasonal_s = accuracy_table(df, ["season"], min_n=5)
    seasonal_s.to_csv(out_dir / "seasonal_by_season.csv", index=False)
    seasonal = seasonal_month

    season_sample = pd.DataFrame()
    lead_by_season = pd.DataFrame()
    if args.four_season_sample:
        season_sample = accuracy_table(df, ["sample_season", "month"], min_n=3)
        if not season_sample.empty:
            season_sample.to_csv(out_dir / "four_season_precision_summary.csv", index=False)
        lead_by_season = accuracy_table(df, ["sample_season", "lead_hour_bucket"], min_n=3)
        if not lead_by_season.empty:
            lead_by_season.to_csv(out_dir / "lead_hour_accuracy_by_season.csv", index=False)

    best_lead = best_lead_per_day(df)
    best_lead.to_csv(out_dir / "best_lead_hour_per_day.csv", index=False)

    write_report(
        out_dir, lead, conditions, seasonal, best_lead, df,
        study_name=args.study_name,
        season_sample=season_sample if args.four_season_sample else None,
        lead_by_season=lead_by_season if args.four_season_sample else None,
    )
    print(f"Wrote analysis to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
