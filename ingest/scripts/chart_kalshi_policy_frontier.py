#!/usr/bin/env python3
"""Render interactive Kalshi policy frontier chart from policy_sweep JSON.

NO REAL TRADING — Console 2 research visualization only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _latest_sweep_json(directory: Path) -> Optional[Path]:
    files = sorted(directory.glob("policy_sweep_*.json"))
    return files[-1] if files else None


def _edge_sensitivity(configs: list[dict[str, Any]], recommended: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Best config per edge at recommended cap/cheapest/insurance settings."""
    if not recommended:
        return {"edges": [], "win_rates": [], "pnls": [], "n_trades": []}
    cap = recommended["max_entry_yes_ask"]
    cheapest = recommended["require_cheapest_at_open"]
    ins = recommended["insurance_enabled"]
    by_edge: dict[float, dict[str, Any]] = {}
    for c in configs:
        if c["n_trades"] == 0:
            continue
        if (
            c["max_entry_yes_ask"] != cap
            or c["require_cheapest_at_open"] != cheapest
            or c["insurance_enabled"] != ins
        ):
            continue
        edge = c["min_forecast_edge"]
        prev = by_edge.get(edge)
        if prev is None or (c["win_rate"], c["total_pnl"]) > (prev["win_rate"], prev["total_pnl"]):
            by_edge[edge] = c
    edges = sorted(by_edge.keys())
    return {
        "edges": [round(e * 100, 0) for e in edges],
        "win_rates": [by_edge[e]["win_rate_pct"] for e in edges],
        "pnls": [by_edge[e]["total_pnl"] for e in edges],
        "n_trades": [by_edge[e]["n_trades"] for e in edges],
    }


def build_chart_payload(sweep: dict[str, Any]) -> dict[str, Any]:
    configs = [c for c in sweep.get("configs", []) if c.get("n_trades", 0) > 0]
    recommended = sweep.get("recommended_policy")
    frontier_keys = {
        (
            c["min_forecast_edge"],
            c["max_entry_yes_ask"],
            c["require_cheapest_at_open"],
            c["insurance_enabled"],
        )
        for c in sweep.get("pareto_frontier", [])
    }

    points = []
    for c in configs:
        key = (
            c["min_forecast_edge"],
            c["max_entry_yes_ask"],
            c["require_cheapest_at_open"],
            c["insurance_enabled"],
        )
        is_frontier = key in frontier_keys
        is_recommended = False
        if recommended:
            is_recommended = (
                c["min_forecast_edge"] == recommended["min_forecast_edge"]
                and c["max_entry_yes_ask"] == recommended["max_entry_yes_ask"]
                and c["require_cheapest_at_open"] == recommended["require_cheapest_at_open"]
                and c["insurance_enabled"] == recommended["insurance_enabled"]
            )
        points.append({
            "edge_pct": round(c["min_forecast_edge"] * 100, 0),
            "cap": c["max_entry_yes_ask"],
            "cheapest": c["require_cheapest_at_open"],
            "insurance": c["insurance_enabled"],
            "n_trades": c["n_trades"],
            "win_rate_pct": c["win_rate_pct"],
            "total_pnl": c["total_pnl"],
            "roi_pct": c.get("roi_pct", 0),
            "is_frontier": is_frontier,
            "is_recommended": is_recommended,
            "label": (
                f"edge={c['min_forecast_edge']:.0%} cap=${c['max_entry_yes_ask']:.2f} "
                f"cheap={c['require_cheapest_at_open']} ins={c['insurance_enabled']}"
            ),
        })

    top_table = sorted(
        configs,
        key=lambda c: (c["win_rate"], c["total_pnl"], c["n_trades"]),
        reverse=True,
    )[:20]

    return {
        "title": "KMIA Kalshi Policy Frontier",
        "generated_at_utc": sweep.get("generated_at_utc"),
        "n_forecast_days": sweep.get("n_forecast_validated_days"),
        "n_observed_days": sweep.get("n_observed_days"),
        "model_version": sweep.get("model_version"),
        "selection_method": sweep.get("selection_method"),
        "recommended_policy": recommended,
        "points": points,
        "edge_sensitivity": _edge_sensitivity(sweep.get("configs", []), recommended),
        "top_table": top_table,
        "low_confidence": (
            recommended.get("confidence") == "low" if recommended else True
        ),
    }


def render_html(payload: dict[str, Any], out_path: Path) -> None:
    data_json = json.dumps(payload)
    rec = payload.get("recommended_policy") or {}
    conf_banner = ""
    if payload.get("low_confidence"):
        conf_banner = (
            f"<div class='warn'>Low confidence: only {rec.get('n_trades', 0)} scorable trades "
            f"(need ≥5 for moderate confidence). Treat recommendations as directional only.</div>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{payload["title"]}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0f1419; --panel: #1a2332; --text: #e8edf4; --muted: #8b9cb3;
      --border: #2d3a4f; --accent: #4c9aff; --warn: #f0a500;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); }}
    header {{ padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.15rem; }}
    .sub {{ color: var(--muted); font-size: 0.85rem; }}
    .warn {{ background: #3a2f14; color: var(--warn); padding: 0.6rem 1rem; margin: 0.75rem 1rem 0; border-radius: 6px; font-size: 0.85rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 1rem; padding: 1rem; }}
    @media (min-width: 1100px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
    .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; }}
    .full {{ grid-column: 1 / -1; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
    th, td {{ border-bottom: 1px solid var(--border); padding: 0.35rem 0.5rem; text-align: left; }}
    th {{ color: var(--muted); font-weight: 500; }}
    .rec {{ color: var(--accent); font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <h1>{payload["title"]}</h1>
    <div class="sub">Probability-first policy frontier · win rate vs total P&amp;L · {payload.get("generated_at_utc", "")}</div>
    <div class="sub">{payload.get("n_forecast_days", 0)} forecast days · {payload.get("n_observed_days", 0)} observed · model {payload.get("model_version", "")}</div>
  </header>
  {conf_banner}
  <div class="grid">
    <div class="panel full"><div id="frontier"></div></div>
    <div class="panel"><div id="edgeSensitivity"></div></div>
    <div class="panel"><div id="tradeCount"></div></div>
    <div class="panel full"><div id="policyTable"></div></div>
  </div>
  <script>
    const PAYLOAD = {data_json};

    const pts = PAYLOAD.points || [];
    const rec = PAYLOAD.recommended_policy;
    const frontierPts = pts.filter(p => p.is_frontier);
    const otherPts = pts.filter(p => !p.is_frontier && !p.is_recommended);
    const recPts = pts.filter(p => p.is_recommended);

    Plotly.newPlot("frontier", [
      {{
        x: otherPts.map(p => p.win_rate_pct),
        y: otherPts.map(p => p.total_pnl),
        mode: "markers",
        type: "scatter",
        name: "Configs",
        marker: {{ size: otherPts.map(p => 8 + p.n_trades * 3), color: otherPts.map(p => p.edge_pct), colorscale: "Viridis", showscale: true, colorbar: {{ title: "Edge %" }} }},
        text: otherPts.map(p => p.label + "<br>win=" + p.win_rate_pct + "% n=" + p.n_trades),
        hoverinfo: "text",
      }},
      {{
        x: frontierPts.map(p => p.win_rate_pct),
        y: frontierPts.map(p => p.total_pnl),
        mode: "markers",
        type: "scatter",
        name: "Pareto frontier",
        marker: {{ size: 14, symbol: "diamond-open", color: "#f0a500", line: {{ width: 2, color: "#f0a500" }} }},
        text: frontierPts.map(p => p.label),
        hoverinfo: "text",
      }},
      {{
        x: recPts.map(p => p.win_rate_pct),
        y: recPts.map(p => p.total_pnl),
        mode: "markers+text",
        type: "scatter",
        name: "Recommended",
        marker: {{ size: 18, symbol: "star", color: "#4c9aff" }},
        text: ["REC"],
        textposition: "top center",
        hovertext: recPts.map(p => "RECOMMENDED: " + p.label),
        hoverinfo: "text",
      }},
    ], {{
      title: "Win probability vs total profit",
      paper_bgcolor: "#1a2332",
      plot_bgcolor: "#1a2332",
      font: {{ color: "#e8edf4" }},
      xaxis: {{ title: "Win rate (%)", range: [0, 105] }},
      yaxis: {{ title: "Total simulated P&L ($)" }},
      margin: {{ t: 48, r: 20, b: 48, l: 56 }},
      showlegend: true,
    }}, {{ responsive: true }});

    const es = PAYLOAD.edge_sensitivity || {{}};
    Plotly.newPlot("edgeSensitivity", [
      {{ x: es.edges, y: es.win_rates, name: "Win %", type: "scatter", mode: "lines+markers", yaxis: "y" }},
      {{ x: es.edges, y: es.pnls, name: "P&L $", type: "scatter", mode: "lines+markers", yaxis: "y2" }},
    ], {{
      title: "Edge sensitivity (at recommended cap/cheapest/insurance)",
      paper_bgcolor: "#1a2332", plot_bgcolor: "#1a2332", font: {{ color: "#e8edf4" }},
      xaxis: {{ title: "Min forecast edge (%)" }},
      yaxis: {{ title: "Win rate (%)", side: "left" }},
      yaxis2: {{ title: "Total P&L ($)", overlaying: "y", side: "right" }},
      margin: {{ t: 48, r: 56, b: 48, l: 56 }},
    }}, {{ responsive: true }});

    Plotly.newPlot("tradeCount", [
      {{ x: es.edges, y: es.n_trades, type: "bar", marker: {{ color: "#4c9aff" }} }},
    ], {{
      title: "Trades per edge threshold",
      paper_bgcolor: "#1a2332", plot_bgcolor: "#1a2332", font: {{ color: "#e8edf4" }},
      xaxis: {{ title: "Min forecast edge (%)" }},
      yaxis: {{ title: "n trades" }},
      margin: {{ t: 48, r: 20, b: 48, l: 56 }},
    }}, {{ responsive: true }});

    const rows = (PAYLOAD.top_table || []).map(r => `
      <tr class="${{r.min_forecast_edge === (rec && rec.min_forecast_edge) && r.max_entry_yes_ask === (rec && rec.max_entry_yes_ask) ? 'rec' : ''}}">
        <td>${{(r.min_forecast_edge * 100).toFixed(0)}}%</td>
        <td>$${{r.max_entry_yes_ask.toFixed(2)}}</td>
        <td>${{r.require_cheapest_at_open}}</td>
        <td>${{r.insurance_enabled}}</td>
        <td>${{r.n_trades}}</td>
        <td>${{r.win_rate_pct}}%</td>
        <td>$${{r.total_pnl.toFixed(2)}}</td>
      </tr>`).join("");
    document.getElementById("policyTable").innerHTML = `
      <h3 style="margin:0 0 0.5rem;font-size:0.95rem;">Top configs (win rate, then P&amp;L)</h3>
      <table><thead><tr><th>Edge</th><th>Cap</th><th>Cheap</th><th>Ins</th><th>N</th><th>Win%</th><th>P&amp;L</th></tr></thead><tbody>${{rows}}</tbody></table>`;
  </script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Kalshi policy frontier HTML chart.")
    parser.add_argument("--sweep-json", type=Path, default=None, help="policy_sweep_*.json path")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    default_dir = (
        Path(__file__).resolve().parents[2]
        / "Research"
        / "Agent Analysis of KMIA Forecast Precision"
        / "Kalshi_Price_Backtest"
    )
    out_dir = args.output_dir or default_dir
    sweep_path = args.sweep_json or _latest_sweep_json(out_dir)
    if sweep_path is None or not sweep_path.is_file():
        raise SystemExit(f"No policy_sweep JSON found in {out_dir}")

    sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    payload = build_chart_payload(sweep)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    html_path = out_dir / f"policy_frontier_{ts}.html"
    render_html(payload, html_path)
    print(f"Chart written: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
