#!/usr/bin/env python3
"""Filter NDFD point CSV to KMIA-valid rows only."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    df = pd.read_csv(src, engine="python", on_bad_lines="skip")

    for col in ("lon_returned", "lat_returned", "value_native"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = df[
        df["lon_returned"].notna()
        & df["lat_returned"].notna()
        & df["value_native"].notna()
        & (df["lon_returned"] < 900)
        & (df["lat_returned"] < 900)
        & (df["value_native"] < 1.0e19)
    ].copy()

    dst.parent.mkdir(parents=True, exist_ok=True)
    valid.to_csv(dst, index=False)
    print(f"Input rows: {len(df)}")
    print(f"Valid rows: {len(valid)}")
    print(f"Wrote: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
