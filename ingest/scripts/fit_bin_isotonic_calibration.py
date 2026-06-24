#!/usr/bin/env python3
"""Walk-forward isotonic calibration for traded Kalshi bins.

NO REAL TRADING EXECUTION — Console 2 research export only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from isotonic_runtime import apply_isotonic_points
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

_SAFETY = {
    "no_real_trading": True,
    "no_order_execution": True,
    "disclaimer": "NO REAL TRADING EXECUTION - CONSOLE 2 CALIBRATION ONLY",
}

_DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "Research/Agent Analysis of KMIA Forecast Precision"
    / "Kalshi_Price_Backtest/bin_isotonic_v1.json"
)


def _prob_decile(p: float) -> int:
    return min(9, max(0, int(p * 10)))


def collect_rows(
    *,
    price_history_dir: Path,
    nws_dir: Path,
    reports_dir: Path,
    ncei_history: Path,
    train_end_year: int,
) -> tuple[list[dict], list[dict]]:
    temps, _ = load_settlement_observed_maxes_with_sources(ncei_history_jsonl=ncei_history)
    train: list[dict] = []
    test: list[dict] = []

    for day, path in sorted(discover_price_history_files(price_history_dir).items()):
        if day not in temps:
            continue
        fc = forecast_high_at_anchor(day, nws_dir=nws_dir, reports_dir=reports_dir)
        if not fc.get("found"):
            continue
        forecast_temp = float(fc["forecast_temp_f"])
        _, column_map = load_price_history_csv(path)
        market_bins = list(dict.fromkeys(column_map.values()))
        market_bin = find_market_bin_for_temp(int(round(forecast_temp)), column_map)
        if not market_bin:
            continue
        probs = model_probs_for_market_bins(
            forecast_temp_f=forecast_temp,
            market_bins=market_bins,
        )
        raw_p = float(probs.get(market_bin, 0.0))
        obs_int = int(round(temps[day]))
        won = temp_satisfies_bin_label(obs_int, market_bin)
        row = {
            "day": day,
            "bin": market_bin,
            "raw_p": raw_p,
            "won": int(won),
            "decile": _prob_decile(raw_p),
        }
        if int(day[:4]) <= train_end_year:
            train.append(row)
        else:
            test.append(row)
    return train, test


def fit_isotonic(train: list[dict]) -> dict:
    try:
        from sklearn.isotonic import IsotonicRegression
    except ImportError as exc:
        raise SystemExit("scikit-learn required: pip install scikit-learn") from exc
    if not train:
        return {"type": "identity", "points": []}
    xs = [r["raw_p"] for r in train]
    ys = [float(r["won"]) for r in train]
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(xs, ys)
    knots = sorted(zip(xs, iso.predict(xs)), key=lambda t: t[0])
    deduped: list[list[float]] = []
    for x, y in knots:
        yf = round(float(y), 4)
        xf = round(float(x), 4)
        if deduped and abs(deduped[-1][0] - xf) < 1e-9:
            deduped[-1][1] = yf
        else:
            deduped.append([xf, yf])
    return {"type": "isotonic_pooled", "points": deduped}


def reliability(rows: list[dict], points: list[list[float]]) -> list[dict]:
    buckets: dict[int, list[tuple[float, int]]] = {i: [] for i in range(10)}
    for r in rows:
        cal = apply_isotonic_points(r["raw_p"], points)
        buckets[r["decile"]].append((cal, r["won"]))
    out = []
    for dec in range(10):
        pairs = buckets[dec]
        if not pairs:
            continue
        out.append({
            "decile": dec,
            "n": len(pairs),
            "mean_predicted": round(sum(p for p, _ in pairs) / len(pairs), 4),
            "observed_rate": round(sum(w for _, w in pairs) / len(pairs), 4),
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit bin isotonic calibration")
    parser.add_argument("--train-end-year", type=int, default=2023)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    price_dir = default_price_history_dir()
    nws = default_kalshi_nws_dir()
    reports = default_kalshi_forecast_reports_dir()
    ncei = default_kmia_daily_history_jsonl()
    if not ncei or not price_dir:
        sys.exit("Missing price history or NCEI history paths")

    train, test = collect_rows(
        price_history_dir=price_dir,
        nws_dir=nws,
        reports_dir=reports,
        ncei_history=ncei,
        train_end_year=args.train_end_year,
    )
    model = fit_isotonic(train)
    points = model.get("points") or []

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": dict(_SAFETY),
        "schema_version": "1.0",
        "train_end_year": args.train_end_year,
        "n_train": len(train),
        "n_test": len(test),
        "model": model,
        "train_reliability": reliability(train, points),
        "test_reliability": reliability(test, points),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {args.out} (train={len(train)} test={len(test)})")

    kalshi_candidates: list[Path] = [
        Path("/d/KMIA_Process/kalshi_mirror/backend/data/research/calibration/bin_isotonic_v1.json"),
    ]
    script_parents = Path(__file__).resolve().parents
    if len(script_parents) > 3:
        kalshi_candidates.append(
            script_parents[3] / "Kalshi/backend/data/research/calibration/bin_isotonic_v1.json"
        )
    for kalshi_out in kalshi_candidates:
        try:
            kalshi_out.parent.mkdir(parents=True, exist_ok=True)
            kalshi_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Also wrote {kalshi_out}")
        except OSError:
            continue


if __name__ == "__main__":
    main()
