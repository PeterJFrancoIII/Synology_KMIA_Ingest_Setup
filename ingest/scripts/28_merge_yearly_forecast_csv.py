#!/usr/bin/env python3
"""Concatenate per-month VALID_ONLY forecast CSVs into one year file."""

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
            print(f"Skip missing: {src}")
            continue
        frames.append(pd.read_csv(src))

    if not frames:
        raise SystemExit("No input files found")

    merged = pd.concat(frames, ignore_index=True)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, index=False)
    subs = sorted(merged["requested_subcategory"].dropna().unique().tolist())
    print(f"Merged rows: {len(merged)}")
    print(f"Subcategories: {subs}")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
