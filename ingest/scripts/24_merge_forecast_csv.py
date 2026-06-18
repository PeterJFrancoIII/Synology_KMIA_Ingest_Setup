#!/usr/bin/env python3
"""Merge per-variable VALID_ONLY point CSVs into one chart-ready forecast file."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    frames = []
    for path in args.inputs:
        src = Path(path)
        if not src.exists():
            raise SystemExit(f"Missing input: {src}")
        frames.append(pd.read_csv(src))

    merged = pd.concat(frames, ignore_index=True)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, index=False)
    print(f"Merged rows: {len(merged)}")
    print(f"Subcategories: {sorted(merged['requested_subcategory'].dropna().unique().tolist())}")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
