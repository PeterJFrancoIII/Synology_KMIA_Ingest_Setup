#!/usr/bin/env python3
"""List NDFD AWS S3 objects for a given variable and date prefix."""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subcategory", default="maxt")
    p.add_argument("--year", default="2020")
    p.add_argument("--month", default="06")
    p.add_argument("--day", default="01")
    args = p.parse_args()

    prefix = f"s3://noaa-ndfd-pds/wmo/{args.subcategory}/{args.year}/{args.month}/{args.day}/"
    print(f"Listing: {prefix}")
    result = subprocess.run(
        ["aws", "s3", "ls", "--no-sign-request", prefix],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
