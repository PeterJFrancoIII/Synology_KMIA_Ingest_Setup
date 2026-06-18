#!/usr/bin/env python3
"""
Interactive KMIA forecast accuracy explorer (self-contained HTML).

Tab 1 — Forecast timeline: daily summary (median vs observed).
Tab 2 — Accuracy explorer: day/week/month buckets with stability toggles.

Reads analyze_kmia_forecast_accuracy.py output (accuracy_points_enriched.csv).
No extra Python deps beyond pandas.
"""

from __future__ import annotations

import argparse
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


def load_points(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["target_dt"] = pd.to_datetime(df["target_date_et"])
    for col in ("within_1f", "within_2f", "within_3f"):
        df[col] = df[col].astype(bool)
    return df


def calendar_bounds(df: pd.DataFrame) -> tuple[str, str, int]:
    years = df["target_dt"].dt.year
    year = int(years.mode().iloc[0]) if len(years) else int(years.iloc[0])
    return f"{year}-01-01", f"{year}-12-31", year


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
        "pct_within_1f": round(100.0 * float(g["within_1f"].mean()), 2),
        "pct_within_2f": round(100.0 * float(g["within_2f"].mean()), 2),
        "pct_within_3f": round(100.0 * float(g["within_3f"].mean()), 2),
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
                "pct_within_1f": round(100.0 * float(g["within_1f"].mean()), 2),
                "pct_within_2f": round(100.0 * float(g["within_2f"].mean()), 2),
                "pct_within_3f": round(100.0 * float(g["within_3f"].mean()), 2),
                "n_releases": int(len(g)),
            }
        )
    return rows


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
    h1 {{ font-size: 1.15rem; margin: 0 0 0.25rem; font-weight: 600; }}
    .sub {{ color: var(--muted); font-size: 0.85rem; }}
    .tabs {{
      display: flex;
      gap: 0;
      padding: 0 1.25rem;
      border-bottom: 1px solid var(--border);
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
  </style>
</head>
<body>
  <header>
    <h1>{payload["study_name"]}</h1>
    <div class="sub">KMIA NDFD max-temperature · 0–36h before 4 PM ET anchor · {payload["date_range"]}</div>
  </header>
  <div class="coverage" id="coverage-banner"></div>
  <nav class="tabs">
    <button class="tab active" data-tab="timeline">Forecast timeline</button>
    <button class="tab" data-tab="accuracy">Accuracy explorer</button>
  </nav>

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
        <select id="acc-threshold">
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

  <script>
    const PAYLOAD = {data_json};
    const STAB_COLORS = {json.dumps(STABILITY_COLORS)};
    const timeline = PAYLOAD.timeline;
    const buckets = PAYLOAD.buckets;
    const COV = PAYLOAD.coverage;

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

    function setTab(name) {{
      document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
      document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + name));
      if (name === 'timeline') drawTimeline();
      else if (name === 'accuracy') drawAccuracy();
    }}

    document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => setTab(t.dataset.tab)));

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
      return m ? '% of releases within ' + m[1] + '°F' : metricKey;
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
      const p1 = rows.length ? (rows.reduce((s,r)=>s+r.pct_within_1f,0)/rows.length).toFixed(1) : '—';
      const p2 = rows.length ? (rows.reduce((s,r)=>s+r.pct_within_2f,0)/rows.length).toFixed(1) : '—';
      const p3 = rows.length ? (rows.reduce((s,r)=>s+r.pct_within_3f,0)/rows.length).toFixed(1) : '—';
      document.getElementById('tl-stats').innerHTML =
        `<span><strong>${{rows.length}}</strong> days</span>` +
        `<span>Window MAE <strong>${{mae}}°F</strong></span>` +
        `<span>Within 1°F <strong>${{p1}}%</strong></span>` +
        `<span>Within 2°F <strong>${{p2}}%</strong></span>` +
        `<span>Within 3°F <strong>${{p3}}%</strong></span>`;
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
      const tol = document.getElementById('acc-threshold').value;
      document.getElementById('acc-stats').innerHTML =
        `<span><strong>${{n}}</strong> ${{freq}} buckets</span>` +
        `<span>Metric: <strong>${{ylab}}</strong></span>` +
        `<span>Layers: <strong>${{stabs.join(', ') || 'none'}}</strong></span>` +
        `<span>Use tolerance ±${{tol}}°F for hit-rate view, or switch to MAE (°F)</span>`;
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
      if (COV.missing_segments && COV.missing_segments.length) {{
        banner.innerHTML = '<strong>Data gap:</strong> no forecast/obs pairs for ' +
          COV.missing_segments.join('; ') +
          `. Chart axis shows full ${{COV.study_year}} calendar; <strong>${{COV.n_days_data}}</strong> days with data.`;
      }} else {{
        banner.innerHTML = `<strong>${{COV.n_days_data}}</strong> days with data · full ${{COV.study_year}} calendar on axis.`;
      }}
    }}

    ['tl-start','tl-end','tl-color-stab'].forEach(id =>
      document.getElementById(id).addEventListener('change', drawTimeline));
    ['acc-freq','acc-metric','acc-threshold','acc-start','acc-end','acc-combined'].forEach(id =>
      document.getElementById(id).addEventListener('change', drawAccuracy));
    ['tog-stable','tog-mixed','tog-unstable'].forEach(id =>
      document.getElementById(id).querySelector('input').addEventListener('change', drawAccuracy));

    initDates();
    drawTimeline();
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
    args = ap.parse_args()

    points_path = Path(args.points)
    out_path = Path(args.out)
    df = load_points(points_path)
    data_start = str(df["target_date_et"].min())
    data_end = str(df["target_date_et"].max())
    cal_start, cal_end, study_year = calendar_bounds(df)
    missing = missing_calendar_segments(data_start, data_end, cal_start, cal_end)

    payload = {
        "study_name": args.study_name,
        "date_range": f"{data_start} → {data_end}",
        "coverage": {
            "study_year": study_year,
            "calendar_start": cal_start,
            "calendar_end": cal_end,
            "data_start": data_start,
            "data_end": data_end,
            "n_days_data": int(df["target_date_et"].nunique()),
            "n_days_calendar": (pd.Timestamp(cal_end) - pd.Timestamp(cal_start)).days + 1,
            "missing_segments": missing,
        },
        "timeline": build_timeline(df),
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
