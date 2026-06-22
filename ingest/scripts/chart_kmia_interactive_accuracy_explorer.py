#!/usr/bin/env python3
"""
Interactive KMIA forecast accuracy explorer (self-contained HTML).

Tab 1 — Forecast timeline: daily summary (median vs observed).
Tab 3 — Week brackets: calendar date ranges (e.g. Aug 1–7) precision ranking.

Reads analyze_kmia_forecast_accuracy.py output (accuracy_points_enriched.csv).
No extra Python deps beyond pandas.
"""

from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path

import pandas as pd

STABILITY_ORDER = ["STABLE", "MIXED", "UNSTABLE"]
STABILITY_COLORS = {
    "STABLE": "#2e7d32",
    "MIXED": "#f9a825",
    "UNSTABLE": "#c62828",
    "ALL": "#1565c0",
}
TOLERANCES_F = (0, 1, 2, 3)


def within_tolerance(df: pd.DataFrame, tolerance_f: float) -> pd.Series:
    if tolerance_f == 0:
        return df["forecast_temp_f"].round() == df["observed_max_f"].round()
    return df["abs_error_f"] <= tolerance_f


def ensure_tolerance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "abs_error_f" not in df.columns and {"forecast_temp_f", "observed_max_f"}.issubset(df.columns):
        df["abs_error_f"] = (df["forecast_temp_f"] - df["observed_max_f"]).abs()
    if "abs_error_f" in df.columns:
        for t in TOLERANCES_F:
            col = f"within_{t}f"
            if col not in df.columns or t == 0:
                df[col] = within_tolerance(df, t)
            df[col] = df[col].astype(bool)
    return df


def pct_within_metrics(g: pd.DataFrame, decimals: int = 1) -> dict:
    return {
        f"pct_within_{t}f": round(100.0 * float(g[f"within_{t}f"].mean()), decimals)
        for t in TOLERANCES_F
    }


def load_points(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["target_dt"] = pd.to_datetime(df["target_date_et"])
    return ensure_tolerance_columns(df)


def calendar_bounds(df: pd.DataFrame) -> tuple[str, str, str]:
    years = df["target_dt"].dt.year
    ymin, ymax = int(years.min()), int(years.max())
    label = str(ymin) if ymin == ymax else f"{ymin}–{ymax}"
    return f"{ymin}-01-01", f"{ymax}-12-31", label


def missing_calendar_segments(data_start: str, data_end: str, cal_start: str, cal_end: str) -> list[str]:
    segments: list[str] = []
    ds, de = pd.Timestamp(data_start), pd.Timestamp(data_end)
    cs, ce = pd.Timestamp(cal_start), pd.Timestamp(cal_end)
    if ds > cs:
        segments.append(f"{cal_start} to {(ds - pd.Timedelta(days=1)).strftime('%Y-%m-%d')}")
    if de < ce:
        segments.append(f"{(de + pd.Timedelta(days=1)).strftime('%Y-%m-%d')} to {cal_end}")
    return segments


def all_bucket_labels(freq: str, cal_start: str, cal_end: str) -> list[str]:
    start = pd.Timestamp(cal_start)
    end = pd.Timestamp(cal_end)
    if freq == "day":
        return pd.date_range(start, end, freq="D").strftime("%Y-%m-%d").tolist()
    if freq == "week":
        cur = start - pd.Timedelta(days=int(start.dayofweek))
        labels: list[str] = []
        while cur <= end:
            labels.append(cur.strftime("%Y-%m-%d"))
            cur += pd.Timedelta(days=7)
        return labels
    if freq == "month":
        return pd.date_range(start.replace(day=1), end, freq="MS").strftime("%Y-%m").tolist()
    raise ValueError(freq)


def bucket_key(series: pd.Series, freq: str) -> pd.Series:
    if freq == "day":
        return series.dt.strftime("%Y-%m-%d")
    if freq == "week":
        start = series.dt.to_period("W-MON").dt.start_time
        return start.dt.strftime("%Y-%m-%d")
    if freq == "month":
        return series.dt.strftime("%Y-%m")
    raise ValueError(freq)


def metrics_for_group(g: pd.DataFrame) -> dict:
    return {
        "n_forecasts": int(len(g)),
        "n_days": int(g["target_date_et"].nunique()),
        "mae_f": round(float(g["abs_error_f"].mean()), 3),
        **pct_within_metrics(g, decimals=2),
    }


def build_accuracy_buckets(df: pd.DataFrame, freq: str, cal_start: str, cal_end: str) -> dict:
    out: dict[str, dict] = {}
    work = df.copy()
    work["bucket"] = bucket_key(work["target_dt"], freq)
    for b in work["bucket"].unique():
        sub = work[work["bucket"] == b]
        out[b] = {"ALL": metrics_for_group(sub)}
        for stab in STABILITY_ORDER:
            sg = sub[sub["forecast_stability"] == stab]
            if len(sg):
                out[b][stab] = metrics_for_group(sg)
    buckets = all_bucket_labels(freq, cal_start, cal_end)
    return {"freq": freq, "buckets": buckets, "data": out}


def build_timeline(df: pd.DataFrame) -> list[dict]:
    rows = []
    for date, g in df.groupby("target_date_et", sort=True):
        stab = g["forecast_stability"].iloc[0]
        rows.append(
            {
                "date": date,
                "observed_max_f": round(float(g["observed_max_f"].iloc[0]), 2),
                "forecast_median_f": round(float(g["forecast_temp_f"].median()), 2),
                "min_forecast_f": round(float(g["min_forecast_f"].iloc[0]), 2),
                "max_forecast_f": round(float(g["max_forecast_f"].iloc[0]), 2),
                "forecast_stability": stab,
                "mae_f": round(float(g["abs_error_f"].mean()), 3),
                **pct_within_metrics(g, decimals=2),
                "n_releases": int(len(g)),
            }
        )
    return rows


def _metrics_group(g: pd.DataFrame) -> dict:
    return {
        "n_forecasts": int(len(g)),
        "n_days": int(g["target_date_et"].nunique()),
        "mae_f": round(float(g["abs_error_f"].mean()), 2),
        **pct_within_metrics(g, decimals=1),
    }


def _pct_key(tolerance: int) -> str:
    return f"pct_within_{tolerance}f"


MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _month_day_bracket(day: int) -> int:
    if day <= 7:
        return 1
    if day <= 14:
        return 2
    if day <= 21:
        return 3
    return 4


def _bracket_date_range(month: int, bracket: int) -> tuple[int, int]:
    last = calendar.monthrange(2024, month)[1]
    ranges = ((1, 7), (8, 14), (15, 21), (22, last))
    return ranges[bracket - 1]


def _bracket_label(month: int, bracket: int) -> str:
    lo, hi = _bracket_date_range(month, bracket)
    return f"{MONTH_ABBR[month - 1]} {lo}–{hi}"


def build_date_week_brackets(df: pd.DataFrame) -> list[dict]:
    """Calendar week-of-month brackets pooled across years (e.g. Aug 1–7, Aug 8–14)."""
    work = df.copy()
    work["cal_month"] = work["target_dt"].dt.month.astype(int)
    work["cal_bracket"] = work["target_dt"].dt.day.map(_month_day_bracket).astype(int)
    within_cols = {f"within_{t}f": (f"within_{t}f", "mean") for t in TOLERANCES_F}
    daily = work.groupby(["target_date_et", "cal_month", "cal_bracket"]).agg(
        **within_cols,
        abs_error_f=("abs_error_f", "mean"),
    ).reset_index()
    grouped = daily.groupby(["cal_month", "cal_bracket"]).agg(
        n_days=("target_date_et", "count"),
        **within_cols,
        mae_f=("abs_error_f", "mean"),
    ).reset_index()
    min_days = max(3, int(daily["target_date_et"].nunique() / 48))

    brackets: list[dict] = []
    for _, r in grouped.iterrows():
        month = int(r["cal_month"])
        bracket = int(r["cal_bracket"])
        if int(r["n_days"]) < min_days:
            continue
        lo, hi = _bracket_date_range(month, bracket)
        brackets.append({
            "month": month,
            "bracket": bracket,
            "sort_key": month * 10 + bracket,
            "label": _bracket_label(month, bracket),
            "date_range": f"{MONTH_ABBR[month - 1]} {lo}–{hi}",
            "n_days": int(r["n_days"]),
            "metrics": {
                "mae_f": round(float(r["mae_f"]), 2),
                **{
                    f"pct_within_{t}f": round(100.0 * float(r[f"within_{t}f"]), 1)
                    for t in TOLERANCES_F
                },
            },
        })
    return brackets


# Back-compat alias used by payload builder
build_week_precision = build_date_week_brackets


def build_executive_summary(df: pd.DataFrame) -> dict:
    """Structured summary for ±0°F … ±3°F (client picks tolerance)."""
    min_cond_n = max(200, int(len(df) * 0.03))

    # 1 — Conditions
    conditions: list[dict] = []
    for label, col in [
        ("Forecast stability", "forecast_stability"),
        ("Forecast wind", "forecast_wdir_cardinal"),
        ("Observed wind", "observed_wdir_cardinal"),
        ("Forecast spread", None),
    ]:
        work = df.copy()
        if col is None:
            work["range_bucket"] = pd.cut(
                work["forecast_range_f"],
                bins=[-0.1, 1.5, 3.0, 100],
                labels=["narrow ≤1.5°F", "medium 1.5–3°F", "wide >3°F"],
            )
            col = "range_bucket"
        sub = work[work[col].notna() & (work[col].astype(str) != "NA")]
        for val, g in sub.groupby(col, observed=False):
            if len(g) < min_cond_n:
                continue
            conditions.append({"label": label, "value": str(val), "metrics": _metrics_group(g)})

    # 2 — Lead-time brackets
    lead_brackets: list[dict] = []
    for lo, hi, name in [
        (0, 6, "0–6h"),
        (7, 12, "7–12h"),
        (13, 18, "13–18h"),
        (19, 24, "19–24h"),
        (25, 36, "25–36h"),
    ]:
        g = df[(df["lead_hour_bucket"] >= lo) & (df["lead_hour_bucket"] <= hi)]
        if len(g) < 50:
            continue
        lead_brackets.append({"name": name, "metrics": _metrics_group(g)})

    weeks = build_date_week_brackets(df)

    overall = _metrics_group(df)
    if "forecast_wdir_deg" in df.columns:
        overall["forecast_wdir_coverage_pct"] = round(
            100.0 * float(df["forecast_wdir_deg"].notna().mean()), 1
        )

    return {
        "tolerances_f": list(TOLERANCES_F),
        "default_tolerance_f": 2,
        "overall": overall,
        "conditions": conditions,
        "lead_brackets": lead_brackets,
        "weeks": weeks,
    }


def render_html(payload: dict, out_path: Path) -> None:
    data_json = json.dumps(payload)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{payload["study_name"]} — KMIA Chart Suite</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0f1419;
      --panel: #1a2332;
      --text: #e8edf4;
      --muted: #8b9cb3;
      --border: #2d3a4f;
      --accent: #4c9aff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "SF Pro Text", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}
    header {{
      padding: 1rem 1.25rem 0.5rem;
      border-bottom: 1px solid var(--border);
    }}
    .nav-bar {{
      position: sticky;
      top: 0;
      z-index: 30;
      display: flex;
      align-items: stretch;
      gap: 0;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
    }}
    .nav-back {{
      display: flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0 1rem;
      color: var(--muted);
      text-decoration: none;
      font-size: 0.85rem;
      white-space: nowrap;
      border-right: 1px solid var(--border);
    }}
    .nav-back:hover {{ color: var(--accent); }}
    .nav-back .arrow {{ font-size: 1rem; line-height: 1; }}
    h1 {{ font-size: 1.15rem; margin: 0 0 0.25rem; font-weight: 600; }}
    .sub {{ color: var(--muted); font-size: 0.85rem; }}
    .tabs {{
      display: flex;
      gap: 0;
      flex: 1;
      padding: 0 0.5rem;
    }}
    .tab {{
      background: none;
      border: none;
      color: var(--muted);
      padding: 0.75rem 1rem;
      cursor: pointer;
      font-size: 0.9rem;
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
    }}
    .tab.active {{
      color: var(--text);
      border-bottom-color: var(--accent);
    }}
    .panel {{ display: none; padding: 1rem 1.25rem 1.5rem; }}
    .panel.active {{ display: block; }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem 1.5rem;
      align-items: center;
      margin-bottom: 0.75rem;
      padding: 0.75rem 1rem;
      background: var(--panel);
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    label {{ font-size: 0.85rem; color: var(--muted); display: flex; align-items: center; gap: 0.4rem; }}
    select, input[type="date"] {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 0.35rem 0.5rem;
      font-size: 0.85rem;
    }}
    .stab-toggle {{
      display: flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      cursor: pointer;
      font-size: 0.8rem;
      user-select: none;
    }}
    .stab-toggle input {{ accent-color: var(--accent); }}
    .stab-toggle.stable {{ border-color: #2e7d32; }}
    .stab-toggle.mixed {{ border-color: #f9a825; }}
    .stab-toggle.unstable {{ border-color: #c62828; }}
    .stab-toggle.off {{ opacity: 0.45; }}
    #chart-timeline, #chart-accuracy {{ width: 100%; min-height: 480px; }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-top: 0.75rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .stats strong {{ color: var(--text); }}
    .coverage {{
      margin: 0.5rem 1.25rem 0;
      padding: 0.5rem 0.75rem;
      background: rgba(249, 168, 37, 0.12);
      border: 1px solid rgba(249, 168, 37, 0.35);
      border-radius: 6px;
      font-size: 0.82rem;
      color: var(--muted);
    }}
    .coverage strong {{ color: #f9a825; }}
    .exec-summary {{
      margin: 0.75rem 1.25rem 0;
      padding: 1rem 1.1rem;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.88rem;
    }}
    .exec-summary h2 {{
      margin: 0 0 0.6rem;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--accent);
    }}
    .exec-summary section {{ margin-bottom: 0.85rem; }}
    .exec-summary section:last-child {{ margin-bottom: 0; }}
    .exec-summary h3 {{
      margin: 0 0 0.35rem;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .exec-summary ul {{
      margin: 0;
      padding-left: 1.15rem;
      color: var(--text);
    }}
    .exec-summary li {{ margin: 0.2rem 0; }}
    .exec-summary .cond-root {{ list-style: none; padding-left: 0; }}
    .exec-summary .cond-group {{ margin: 0.45rem 0; }}
    .exec-summary .cond-group > ul {{
      list-style: disc;
      margin: 0.15rem 0 0 1.1rem;
      padding-left: 0.4rem;
    }}
    .exec-summary .overall {{
      font-size: 0.82rem;
      color: var(--muted);
      margin-bottom: 0.75rem;
    }}
    .tol-bar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem 0.75rem;
      margin: 0.65rem 1.25rem 0;
      padding: 0.55rem 0.85rem;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.85rem;
    }}
    .tol-bar span.label {{ color: var(--muted); margin-right: 0.25rem; }}
    .tol-btn {{
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 0.3rem 0.75rem;
      border-radius: 999px;
      cursor: pointer;
      font-size: 0.82rem;
    }}
    #chart-week-brackets {{ min-height: 480px; }}
    .tol-btn.active {{
      background: rgba(76, 154, 255, 0.18);
      border-color: var(--accent);
      color: var(--text);
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{payload["study_name"]}</h1>
    <div class="sub">KMIA NDFD max-temperature · 0–36h before 4 PM ET anchor · <span id="header-date-range">{payload["date_range"]}</span></div>
  </header>
  <div class="tol-bar" id="tol-bar">
    <span class="label">Tolerance</span>
    <button type="button" class="tol-btn" data-tol="0">±0°F</button>
    <button type="button" class="tol-btn" data-tol="1">±1°F</button>
    <button type="button" class="tol-btn active" data-tol="2">±2°F</button>
    <button type="button" class="tol-btn" data-tol="3">±3°F</button>
  </div>
  <div class="exec-summary" id="exec-summary"></div>
  <div class="coverage" id="coverage-banner"></div>
  <div class="nav-bar">
    <a class="nav-back" id="nav-portal" href="{payload.get('nav', {}).get('portal_href', '../KMIA_Chart_Portal/kmia_chart_portal.html')}">
      <span class="arrow">←</span> Chart portal
    </a>
    <nav class="tabs">
      <button class="tab active" data-tab="timeline">Forecast timeline</button>
      <button class="tab" data-tab="accuracy">Accuracy explorer</button>
      <button class="tab" data-tab="weeks">Week brackets</button>
    </nav>
  </div>

  <section id="panel-timeline" class="panel active">
    <div class="controls">
      <label>From <input type="date" id="tl-start"/></label>
      <label>To <input type="date" id="tl-end"/></label>
      <label><input type="checkbox" id="tl-color-stab" checked/> Color by stability</label>
    </div>
    <div id="chart-timeline"></div>
    <div class="stats" id="tl-stats"></div>
  </section>

  <section id="panel-accuracy" class="panel">
    <div class="controls">
      <label>Timeframe
        <select id="acc-freq">
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month" selected>Month</option>
        </select>
      </label>
      <label>Metric
        <select id="acc-metric">
          <option value="hit_rate">% within tolerance</option>
          <option value="mae_f">MAE (°F)</option>
        </select>
      </label>
      <label id="acc-threshold-wrap">Tolerance
        <span id="acc-threshold-pills">
          <button type="button" class="tol-btn acc-tol" data-tol="0">±0°F</button>
          <button type="button" class="tol-btn acc-tol" data-tol="1">±1°F</button>
          <button type="button" class="tol-btn acc-tol active" data-tol="2">±2°F</button>
          <button type="button" class="tol-btn acc-tol" data-tol="3">±3°F</button>
        </span>
        <select id="acc-threshold" style="display:none">
          <option value="0">±0°F</option>
          <option value="1">±1°F</option>
          <option value="2" selected>±2°F</option>
          <option value="3">±3°F</option>
        </select>
      </label>
      <label>From <input type="date" id="acc-start"/></label>
      <label>To <input type="date" id="acc-end"/></label>
      <span style="color:var(--muted);font-size:0.8rem">Stability layers</span>
      <label class="stab-toggle stable" id="tog-stable"><input type="checkbox" checked/> STABLE</label>
      <label class="stab-toggle mixed" id="tog-mixed"><input type="checkbox" checked/> MIXED</label>
      <label class="stab-toggle unstable" id="tog-unstable"><input type="checkbox" checked/> UNSTABLE</label>
      <label><input type="checkbox" id="acc-combined" checked/> Combined (selected)</label>
    </div>
    <div id="chart-accuracy"></div>
    <div class="stats" id="acc-stats"></div>
  </section>

  <section id="panel-weeks" class="panel">
    <div class="controls">
      <label>Sort
        <select id="wk-sort">
          <option value="precision" selected>Highest precision first</option>
          <option value="calendar">Calendar order (Jan→Dec)</option>
        </select>
      </label>
      <label>Metric
        <select id="wk-metric">
          <option value="hit_rate" selected>% within tolerance</option>
          <option value="mae_f">MAE (°F)</option>
        </select>
      </label>
    </div>
    <div id="chart-week-brackets"></div>
    <div class="stats" id="wk-stats"></div>
  </section>

  <script>
    const PAYLOAD = {data_json};
    const STAB_COLORS = {json.dumps(STABILITY_COLORS)};
    const EXEC = PAYLOAD.executive_summary || {{}};
    const timeline = PAYLOAD.timeline;
    const buckets = PAYLOAD.buckets;
    const weekPrecision = PAYLOAD.week_precision || [];
    const COV = PAYLOAD.coverage;
    const NAV = PAYLOAD.nav || {{}};
    const VALID_TABS = ['timeline', 'accuracy', 'weeks'];
    let activeTolerance = String((EXEC.default_tolerance_f || 2));
    let currentTab = 'timeline';

    function pctForTol(metrics, tol) {{
      if (!metrics) return '—';
      const k = 'pct_within_' + tol + 'f';
      return metrics[k] != null ? metrics[k] : '—';
    }}

    function setActiveTolerance(tol) {{
      activeTolerance = String(tol);
      document.querySelectorAll('#tol-bar .tol-btn, #acc-threshold-pills .tol-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.dataset.tol === activeTolerance);
      }});
      const sel = document.getElementById('acc-threshold');
      if (sel) sel.value = activeTolerance;
      renderExecutiveSummary();
      if (document.getElementById('panel-accuracy').classList.contains('active')) drawAccuracy();
      if (document.getElementById('panel-weeks').classList.contains('active')) drawWeekPrecision();
    }}

    document.querySelectorAll('#tol-bar .tol-btn, #acc-threshold-pills .tol-btn').forEach(btn => {{
      btn.addEventListener('click', () => setActiveTolerance(btn.dataset.tol));
    }});

    function renderExecutiveSummary() {{
      const el = document.getElementById('exec-summary');
      if (!EXEC.overall) {{ el.style.display = 'none'; return; }}
      const tol = activeTolerance;
      const pct = pctForTol(EXEC.overall, tol);
      const TOLS = EXEC.tolerances_f || [0, 1, 2, 3];
      const tolBreakdown = TOLS.map(t => '±' + t + '°F <strong>' + pctForTol(EXEC.overall, t) + '%</strong>').join(' / ');

      const sortByTol = (items, topN) => {{
        return [...items].sort((a, b) => (b.metrics['pct_within_' + tol + 'f'] || 0) - (a.metrics['pct_within_' + tol + 'f'] || 0)).slice(0, topN);
      }};

      const condGroups = ['Forecast stability', 'Forecast wind', 'Observed wind', 'Forecast spread'];
      const condLines = condGroups.map(label => {{
        const items = sortByTol((EXEC.conditions || []).filter(c => c.label === label), 2);
        if (!items.length) return '';
        const lines = items.map(c =>
          `<li><strong>${{c.value}}</strong> — ${{pctForTol(c.metrics, tol)}}% within ±${{tol}}°F ` +
          `(MAE ${{c.metrics.mae_f}}°F, n=${{c.metrics.n_forecasts.toLocaleString()}})</li>`
        ).join('');
        return `<li class="cond-group"><strong>${{label}}</strong><ul>${{lines}}</ul></li>`;
      }}).join('');

      const leadSorted = sortByTol(EXEC.lead_brackets || [], EXEC.lead_brackets.length);
      let leadHtml = '';
      if (leadSorted.length) {{
        const best = leadSorted[0];
        leadHtml = `<li>Best bracket: <strong>${{best.name}} before anchor</strong> — ${{pctForTol(best.metrics, tol)}}% within ±${{tol}}°F ` +
          `(MAE ${{best.metrics.mae_f}}°F)</li>`;
        leadHtml += leadSorted.slice(0, 3).map(b =>
          `<li>· ${{b.name}}: ${{pctForTol(b.metrics, tol)}}% within ±${{tol}}°F, MAE ${{b.metrics.mae_f}}°F</li>`
        ).join('');
      }}

      const weekBest = sortByTol(EXEC.weeks || [], 5);
      const weekWorst = [...(EXEC.weeks || [])]
        .sort((a, b) => (a.metrics['pct_within_' + tol + 'f'] || 0) - (b.metrics['pct_within_' + tol + 'f'] || 0))
        .slice(0, 3);
      const weekLines = weekBest.map(w =>
        `<li><strong>${{w.label}}</strong> — ${{pctForTol(w.metrics, tol)}}% within ±${{tol}}°F ` +
        `(MAE ${{w.metrics.mae_f}}°F, ${{w.n_days}} target days pooled)</li>`
      ).join('');
      const weekWorstLines = weekWorst.map(w =>
        `<li><strong>${{w.label}}</strong> — ${{pctForTol(w.metrics, tol)}}% within ±${{tol}}°F ` +
        `(MAE ${{w.metrics.mae_f}}°F, ${{w.n_days}} target days pooled)</li>`
      ).join('');

      const wdirCov = EXEC.overall.forecast_wdir_coverage_pct;
      const wdirNote = wdirCov != null
        ? ' · NDFD forecast wind on <strong>' + wdirCov + '%</strong> of releases'
        : '';

      const tolTitle = tol === '0' ? 'exact integer (±0°F)' : '±' + tol + '°F';
      el.innerHTML =
        '<h2>Accuracy at a glance (' + tolTitle + ' vs observed daily max)</h2>' +
        '<div class="overall">Overall ' + tolBreakdown + ' · ' +
        'MAE <strong>' + EXEC.overall.mae_f + '°F</strong> · ' +
        EXEC.overall.n_forecasts.toLocaleString() + ' releases · ' + EXEC.overall.n_days + ' target days · ' +
        'viewing <strong>±' + tol + '°F</strong> (' + pct + '%)' + wdirNote + '</div>' +
        '<section><h3>1 · Best conditions</h3><ul class="cond-root">' + (condLines || '<li style="color:var(--muted)">Insufficient data</li>') + '</ul></section>' +
        '<section><h3>2 · Lead time before 4 PM ET anchor</h3><ul>' + (leadHtml || '<li style="color:var(--muted)">Insufficient data</li>') + '</ul></section>' +
        '<section><h3>3 · Calendar week brackets (pooled)</h3>' +
        '<p style="color:var(--muted);font-size:0.82rem;margin:0 0 0.35rem">e.g. Aug 1–7 across all study years · see <strong>Week brackets</strong> tab</p>' +
        '<h4 style="font-size:0.78rem;color:var(--muted);margin:0.5rem 0 0.2rem">Highest precision</h4><ul>' +
        (weekLines || '<li style="color:var(--muted)">Insufficient data</li>') + '</ul>' +
        '<h4 style="font-size:0.78rem;color:var(--muted);margin:0.5rem 0 0.2rem">Lowest precision</h4><ul>' +
        (weekWorstLines || '<li style="color:var(--muted)">Insufficient data</li>') + '</ul></section>';
    }}

    function dateXAxis(title, withSlider) {{
      const axis = {{
        title,
        type: 'date',
        gridcolor: '#2d3a4f',
        tickformat: '%b %d',
        range: [COV.calendar_start, COV.calendar_end],
      }};
      if (withSlider) axis.rangeslider = {{ visible: true, bgcolor: '#1a2332', thickness: 0.08 }};
      return axis;
    }}

    function monthXAxis(title) {{
      return {{
        title,
        type: 'category',
        gridcolor: '#2d3a4f',
        categoryorder: 'array',
      }};
    }}

    const layoutBase = {{
      paper_bgcolor: '#0f1419',
      plot_bgcolor: '#1a2332',
      font: {{ color: '#e8edf4', size: 12 }},
      margin: {{ l: 56, r: 24, t: 40, b: 56 }},
      legend: {{ orientation: 'h', y: 1.12, x: 0 }},
      hovermode: 'x unified',
    }};

    function setTab(name, pushHistory) {{
      if (!VALID_TABS.includes(name)) name = 'timeline';
      if (pushHistory !== false && name !== currentTab) {{
        const url = new URL(window.location.href);
        url.hash = name;
        history.pushState({{ tab: name }}, '', url);
      }}
      currentTab = name;
      document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
      document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + name));
      if (name === 'timeline') drawTimeline();
      else if (name === 'accuracy') drawAccuracy();
      else if (name === 'weeks') drawWeekPrecision();
    }}

    function tabFromLocation() {{
      const hash = (location.hash || '').replace(/^#/, '');
      if (VALID_TABS.includes(hash)) return hash;
      if (history.state && VALID_TABS.includes(history.state.tab)) return history.state.tab;
      return NAV.default_tab || 'timeline';
    }}

    document.querySelectorAll('.tab').forEach(t => {{
      t.addEventListener('click', (e) => {{
        e.preventDefault();
        setTab(t.dataset.tab);
      }});
    }});
    window.addEventListener('popstate', () => setTab(tabFromLocation(), false));

    function filterByDate(rows, start, end) {{
      return rows.filter(r => (!start || r.date >= start) && (!end || r.date <= end));
    }}

    function pctMetricForThreshold(t) {{
      return 'pct_within_' + t + 'f';
    }}

    function resolveAccuracyMetric() {{
      const kind = document.getElementById('acc-metric').value;
      if (kind === 'mae_f') return 'mae_f';
      const t = document.getElementById('acc-threshold').value;
      return pctMetricForThreshold(t);
    }}

    function metricLabel(metricKey) {{
      if (metricKey === 'mae_f') return 'MAE (°F)';
      const m = metricKey.match(/^pct_within_(\\d)f$/);
      if (!m) return metricKey;
      return m[1] === '0' ? '% exact integer (±0°F)' : '% within ±' + m[1] + '°F';
    }}

    function syncThresholdVisibility() {{
      const wrap = document.getElementById('acc-threshold-wrap');
      const isHit = document.getElementById('acc-metric').value === 'hit_rate';
      wrap.style.display = isHit ? 'flex' : 'none';
    }}

    function drawTimeline() {{
      const start = document.getElementById('tl-start').value;
      const end = document.getElementById('tl-end').value;
      const colorStab = document.getElementById('tl-color-stab').checked;
      const rows = filterByDate(timeline, start, end);
      const dates = rows.map(r => r.date);
      const obs = rows.map(r => r.observed_max_f);
      const fc = rows.map(r => r.forecast_median_f);
      const lo = rows.map(r => r.min_forecast_f);
      const hi = rows.map(r => r.max_forecast_f);

      const traces = [
        {{
          x: dates, y: hi, mode: 'lines', line: {{ width: 0 }}, showlegend: false,
          hoverinfo: 'skip', name: '_hi'
        }},
        {{
          x: dates, y: lo, mode: 'lines', fill: 'tonexty',
          fillcolor: 'rgba(76,154,255,0.12)', line: {{ width: 0 }},
          name: 'Forecast range', hoverinfo: 'skip'
        }},
        {{
          x: dates, y: fc, mode: 'lines+markers', name: 'Forecast median',
          line: {{ color: '#4c9aff', width: 2 }}, marker: {{ size: 5 }}
        }},
        {{
          x: dates, y: obs, mode: 'markers', name: 'Observed daily max',
          marker: {{ color: '#ef5350', size: 9, symbol: 'x', line: {{ width: 2, color: '#ef5350' }} }}
        }},
      ];

      if (colorStab) {{
        ['STABLE','MIXED','UNSTABLE'].forEach(stab => {{
          const sub = rows.filter(r => r.forecast_stability === stab);
          if (!sub.length) return;
          traces.push({{
            x: sub.map(r => r.date), y: sub.map(r => r.forecast_median_f),
            mode: 'markers', name: stab,
            marker: {{ color: STAB_COLORS[stab], size: 8, symbol: 'circle' }},
            hovertemplate: '%{{x}}<br>%{{y}}°F · ' + stab + '<extra></extra>'
          }});
        }});
      }}

      const layout = {{
        ...layoutBase,
        title: 'Daily forecast vs observed max temperature',
        xaxis: dateXAxis('Target date (ET)', true),
        yaxis: {{ title: 'Temperature (°F)', gridcolor: '#2d3a4f' }},
      }};
      Plotly.react('chart-timeline', traces, layout, {{ responsive: true }});

      const mae = rows.length ? (rows.reduce((s,r)=>s+r.mae_f,0)/rows.length).toFixed(2) : '—';
      const tolSpans = (EXEC.tolerances_f || [0, 1, 2, 3]).map(t => {{
        const key = 'pct_within_' + t + 'f';
        const val = rows.length ? (rows.reduce((s,r)=>s+(r[key]||0),0)/rows.length).toFixed(1) : '—';
        return `<span>±${{t}}°F <strong>${{val}}%</strong></span>`;
      }}).join('');
      document.getElementById('tl-stats').innerHTML =
        `<span><strong>${{rows.length}}</strong> days</span>` +
        `<span>Window MAE <strong>${{mae}}°F</strong></span>` +
        tolSpans;
    }}

    function activeStabilities() {{
      const s = [];
      if (document.getElementById('tog-stable').querySelector('input').checked) s.push('STABLE');
      if (document.getElementById('tog-mixed').querySelector('input').checked) s.push('MIXED');
      if (document.getElementById('tog-unstable').querySelector('input').checked) s.push('UNSTABLE');
      return s;
    }}

    function combinedFromBuckets(pack, cats, stabs, metric) {{
      return cats.map(b => {{
        let num = 0, den = 0;
        stabs.forEach(stab => {{
          const cell = pack.data[b] && pack.data[b][stab];
          if (!cell || !cell.n_forecasts) return;
          num += cell[metric] * cell.n_forecasts;
          den += cell.n_forecasts;
        }});
        return den ? num / den : null;
      }});
    }}

    function filterBuckets(pack, freq, start, end) {{
      let cats = pack.buckets;
      const lo = start || COV.calendar_start;
      const hi = end || COV.calendar_end;
      if (freq === 'month') {{
        const s = lo.slice(0, 7);
        const e = hi.slice(0, 7);
        return cats.filter(b => b >= s && b <= e);
      }}
      return cats.filter(b => b >= lo && b <= hi);
    }}

    function drawAccuracy() {{
      syncThresholdVisibility();
      const freq = document.getElementById('acc-freq').value;
      const metric = resolveAccuracyMetric();
      const start = document.getElementById('acc-start').value;
      const end = document.getElementById('acc-end').value;
      const showCombined = document.getElementById('acc-combined').checked;
      const stabs = activeStabilities();
      const pack = buckets[freq];
      if (!pack) {{
        console.error('Missing bucket pack for freq', freq);
        return;
      }}
      const cats = filterBuckets(pack, freq, start, end);

      const ylab = metricLabel(metric);
      const traces = [];

      if (showCombined && stabs.length) {{
        const vals = combinedFromBuckets(pack, cats, stabs, metric);
        traces.push({{
          x: cats, y: vals,
          mode: 'lines+markers', name: 'Combined (selected)',
          line: {{ color: STAB_COLORS.ALL, width: 3 }},
          marker: {{ size: 7 }},
          connectgaps: false,
        }});
      }}

      stabs.forEach(stab => {{
        const y = cats.map(b => {{
          const cell = pack.data[b] && pack.data[b][stab];
          return cell ? cell[metric] : null;
        }});
        traces.push({{
          x: cats, y, mode: 'lines+markers', name: stab,
          line: {{ color: STAB_COLORS[stab], width: 2, dash: 'dot' }},
          marker: {{ size: 6 }},
          connectgaps: false,
        }});
      }});

      const titleMap = {{ day: 'Daily', week: 'Weekly (Mon start)', month: 'Monthly' }};
      const xaxis = (freq === 'month')
        ? {{ ...monthXAxis('Period'), categoryarray: cats }}
        : dateXAxis('Period', freq === 'day');
      const layout = {{
        ...layoutBase,
        title: `${{titleMap[freq]}} forecast accuracy · ${{ylab}}`,
        xaxis,
        yaxis: {{
          title: ylab,
          gridcolor: '#2d3a4f',
          ...(metric.startsWith('pct_within_') ? {{ range: [0, 100] }} : {{}}),
        }},
      }};
      Plotly.react('chart-accuracy', traces.length ? traces : [{{
        x: cats, y: cats.map(() => null), mode: 'markers', name: 'No data', marker: {{ opacity: 0 }}
      }}], layout, {{ responsive: true }});

      ['tog-stable','tog-mixed','tog-unstable'].forEach(id => {{
        const el = document.getElementById(id);
        el.classList.toggle('off', !el.querySelector('input').checked);
      }});

      const n = cats.length;
      const tol = activeTolerance;
      const tolNote = metric.startsWith('pct_within_')
        ? (EXEC.tolerances_f || [0, 1, 2, 3]).map(t =>
            `<span>±${{t}}°F <strong>${{pctForTol(EXEC.overall, t)}}%</strong></span>`
          ).join('') + `<span>Chart: ±${{tol}}°F</span>`
        : `<span>MAE mode — switch metric to hit-rate for ±0/±1/±2/±3°F</span>`;
      document.getElementById('acc-stats').innerHTML =
        `<span><strong>${{n}}</strong> ${{freq}} buckets</span>` +
        `<span>Metric: <strong>${{ylab}}</strong></span>` +
        `<span>Layers: <strong>${{stabs.join(', ') || 'none'}}</strong></span>` +
        tolNote;
    }}

    function weekBarColor(val, isMae) {{
      if (val == null) return '#555';
      if (isMae) {{
        if (val <= 1.0) return '#2e7d32';
        if (val <= 1.5) return '#4c9aff';
        if (val <= 2.0) return '#f9a825';
        return '#c62828';
      }}
      if (val >= 80) return '#2e7d32';
      if (val >= 70) return '#4c9aff';
      if (val >= 60) return '#f9a825';
      return '#c62828';
    }}

    function drawWeekPrecision() {{
      const weeks = weekPrecision.length ? weekPrecision : (EXEC.weeks || []);
      const el = document.getElementById('chart-week-brackets');
      if (!weeks.length) {{
        el.innerHTML = '<p style="color:var(--muted);padding:1rem">No week bracket data.</p>';
        return;
      }}
      const tol = activeTolerance;
      const sortMode = document.getElementById('wk-sort').value;
      const useMae = document.getElementById('wk-metric').value === 'mae_f';
      const hitKey = 'pct_within_' + tol + 'f';
      let rows = [...weeks];
      if (sortMode === 'precision') {{
        rows.sort((a, b) => useMae
          ? (a.metrics.mae_f || 999) - (b.metrics.mae_f || 999)
          : (b.metrics[hitKey] || 0) - (a.metrics[hitKey] || 0));
      }} else {{
        rows.sort((a, b) => (a.sort_key || 0) - (b.sort_key || 0));
      }}
      const labels = rows.map(w => w.label);
      const vals = rows.map(w => useMae ? w.metrics.mae_f : w.metrics[hitKey]);
      const displayLabels = labels.slice().reverse();
      const displayVals = vals.slice().reverse();
      const displayColors = displayVals.map(v => weekBarColor(v, useMae));
      const displayHover = rows.slice().reverse().map(w => {{
        const pct = pctForTol(w.metrics, tol);
        return `${{w.label}}<br>${{pct}}% within ±${{tol}}°F<br>MAE ${{w.metrics.mae_f}}°F<br>${{w.n_days}} target days`;
      }});
      const tolLabel = tol === '0' ? 'exact integer (±0°F)' : '±' + tol + '°F';
      const ylab = useMae ? 'MAE (°F)' : '% within ' + tolLabel;
      const layout = {{
        ...layoutBase,
        title: useMae
          ? 'Calendar week brackets · mean absolute error (pooled years)'
          : 'Calendar week brackets · forecast precision (pooled years)',
        height: Math.max(480, rows.length * 22 + 120),
        margin: {{ l: 140, r: 24, t: 48, b: 48 }},
        xaxis: {{
          title: ylab,
          gridcolor: '#2d3a4f',
          ...(useMae ? {{}} : {{ range: [0, 100] }}),
        }},
        yaxis: {{
          title: '',
          automargin: true,
          gridcolor: '#2d3a4f',
        }},
        showlegend: false,
      }};
      Plotly.react('chart-week-brackets', [{{
        type: 'bar',
        orientation: 'h',
        y: displayLabels,
        x: displayVals,
        marker: {{ color: displayColors }},
        text: displayVals.map(v => v == null ? '' : (useMae ? v.toFixed(2) + '°F' : v + '%')),
        textposition: 'outside',
        cliponaxis: false,
        hovertext: displayHover,
        hoverinfo: 'text',
      }}], layout, {{ responsive: true }});

      const ranked = [...weeks].sort((a, b) =>
        (b.metrics[hitKey] || 0) - (a.metrics[hitKey] || 0));
      const top = ranked.slice(0, 5);
      const bottom = ranked.slice(-3).reverse();
      document.getElementById('wk-stats').innerHTML =
        `<span><strong>${{weeks.length}}</strong> date brackets</span>` +
        `<span>Tolerance: <strong>${{tolLabel}}</strong></span>` +
        `<span>Best: <strong>${{top.map(w => w.label + ' ' + pctForTol(w.metrics, tol) + '%').join(', ')}}</strong></span>` +
        `<span>Worst: <strong>${{bottom.map(w => w.label + ' ' + pctForTol(w.metrics, tol) + '%').join(', ')}}</strong></span>`;
    }}

    function initDates() {{
      const dataMin = COV.data_start;
      const dataMax = COV.data_end;
      const calMin = COV.calendar_start;
      const calMax = COV.calendar_end;
      ['tl-start','tl-end','acc-start','acc-end'].forEach(id => {{
        const el = document.getElementById(id);
        el.min = calMin;
        el.max = calMax;
      }});
      document.getElementById('tl-start').value = dataMin;
      document.getElementById('tl-end').value = dataMax;
      document.getElementById('acc-start').value = calMin;
      document.getElementById('acc-end').value = calMax;

      const banner = document.getElementById('coverage-banner');
      const yearNote = COV.is_multiyear
        ? `${{COV.years_in_data.length}} years (${{COV.years_in_data.join(', ')}})`
        : `full ${{COV.study_year}} calendar`;
      if (COV.missing_segments && COV.missing_segments.length) {{
        banner.innerHTML =
          '<strong>Coverage:</strong> ' + yearNote + ' · ' +
          '<strong>' + COV.n_days_data + '</strong> target days with data (' +
          COV.data_start + ' → ' + COV.data_end + ')' +
          ' · <strong>Gaps:</strong> ' + COV.missing_segments.join('; ');
      }} else {{
        banner.innerHTML =
          '<strong>' + COV.n_days_data + '</strong> target days · ' +
          COV.data_start + ' → ' + COV.data_end + ' · ' + yearNote;
      }}
    }}

    ['tl-start','tl-end','tl-color-stab'].forEach(id =>
      document.getElementById(id).addEventListener('change', drawTimeline));
    ['acc-freq','acc-metric','acc-threshold','acc-start','acc-end','acc-combined'].forEach(id =>
      document.getElementById(id).addEventListener('change', drawAccuracy));
    ['wk-sort','wk-metric'].forEach(id =>
      document.getElementById(id).addEventListener('change', drawWeekPrecision));
    ['tog-stable','tog-mixed','tog-unstable'].forEach(id =>
      document.getElementById(id).querySelector('input').addEventListener('change', drawAccuracy));

    initDates();
    setActiveTolerance(EXEC.default_tolerance_f || 2);
    const initialTab = tabFromLocation();
    if (!location.hash) {{
      history.replaceState({{ tab: initialTab }}, '', '#' + initialTab);
    }}
    setTab(initialTab, false);
  </script>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build KMIA interactive chart suite HTML")
    ap.add_argument("--points", required=True, help="accuracy_points_enriched.csv")
    ap.add_argument("--out", required=True, help="Output .html path")
    ap.add_argument("--study-name", default="KMIA Forecast Accuracy")
    ap.add_argument(
        "--portal-href",
        default="../KMIA_Chart_Portal/kmia_chart_portal.html",
        help="Relative link back to chart portal from study folder",
    )
    args = ap.parse_args()

    points_path = Path(args.points)
    out_path = Path(args.out)
    df = load_points(points_path)
    data_start = str(df["target_date_et"].min())
    data_end = str(df["target_date_et"].max())
    cal_start, cal_end, study_year = calendar_bounds(df)
    missing = missing_calendar_segments(data_start, data_end, cal_start, cal_end)
    years_in_data = sorted(df["target_dt"].dt.year.unique().astype(int).tolist())

    payload = {
        "study_name": args.study_name,
        "date_range": f"{data_start} → {data_end}",
        "executive_summary": build_executive_summary(df),
        "coverage": {
            "study_year": study_year,
            "years_in_data": years_in_data,
            "calendar_start": cal_start,
            "calendar_end": cal_end,
            "data_start": data_start,
            "data_end": data_end,
            "n_days_data": int(df["target_date_et"].nunique()),
            "n_days_calendar": (pd.Timestamp(cal_end) - pd.Timestamp(cal_start)).days + 1,
            "missing_segments": missing,
            "is_multiyear": len(years_in_data) > 1,
        },
        "nav": {
            "portal_href": args.portal_href,
            "default_tab": "timeline",
        },
        "timeline": build_timeline(df),
        "week_precision": build_date_week_brackets(df),
        "buckets": {
            "day": build_accuracy_buckets(df, "day", cal_start, cal_end),
            "week": build_accuracy_buckets(df, "week", cal_start, cal_end),
            "month": build_accuracy_buckets(df, "month", cal_start, cal_end),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_html(payload, out_path)
    print(f"Wrote {out_path} ({out_path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
