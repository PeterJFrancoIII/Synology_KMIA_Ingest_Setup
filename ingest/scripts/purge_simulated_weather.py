#!/usr/bin/env python3
"""Remove simulated/backfilled weather artifacts from Kalshi weather sets.

Deletes synthetic NWS snapshots and injected observed JSONL rows. Rebuilds the
observed key index afterward.

NO REAL TRADING — data hygiene only. Never writes simulated replacements.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from kalshi_nws_join import default_kalshi_nws_dir, default_kalshi_observed_jsonl
from weather_data_policy import is_simulated_nws_snapshot, is_simulated_observed_row


def _observed_key(row: dict[str, Any], provider: str) -> str | None:
    ts = (
        row.get("timestamp_utc")
        or row.get("observation_time_utc")
        or row.get("valid_time_utc")
        or row.get("fetched_at_utc")
    )
    station = row.get("station") or "KMIA"
    if not ts:
        return None
    return f"{provider}|{station}|{ts}"


def purge_simulated_weather(
    *,
    nws_dir: Path,
    observed_jsonl: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    nws_dir = Path(nws_dir)
    observed_jsonl = Path(observed_jsonl)
    key_file = observed_jsonl.parent / "nws_observed_history.keys"

    removed_snapshots: list[str] = []
    for path in sorted(nws_dir.glob("nws_kmia_snapshot_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if is_simulated_nws_snapshot(data):
            removed_snapshots.append(path.name)
            if not dry_run:
                path.unlink()

    kept_rows: list[str] = []
    removed_observed = 0
    if observed_jsonl.is_file():
        for line in observed_jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                kept_rows.append(line)
                continue
            if is_simulated_observed_row(row):
                removed_observed += 1
                continue
            kept_rows.append(line)

        if not dry_run:
            observed_jsonl.write_text(
                ("\n".join(kept_rows) + "\n") if kept_rows else "",
                encoding="utf-8",
            )

    rebuilt_keys = 0
    if not dry_run and observed_jsonl.is_file():
        keys: set[str] = set()
        for line in kept_rows:
            row = json.loads(line)
            provider = str(row.get("provider") or "nws")
            key = _observed_key(row, provider)
            if key:
                keys.add(key)
        key_file.write_text("\n".join(sorted(keys)) + ("\n" if keys else ""))
        rebuilt_keys = len(keys)

    return {
        "dry_run": dry_run,
        "removed_snapshot_files": len(removed_snapshots),
        "removed_snapshot_names": removed_snapshots[:20],
        "removed_observed_rows": removed_observed,
        "kept_observed_rows": len(kept_rows),
        "rebuilt_key_count": rebuilt_keys,
        "paths": {
            "nws_dir": str(nws_dir),
            "observed_jsonl": str(observed_jsonl),
            "key_file": str(key_file),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--observed-jsonl", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    nws_dir = args.nws_dir or default_kalshi_nws_dir()
    observed_jsonl = args.observed_jsonl or default_kalshi_observed_jsonl()
    if nws_dir is None or observed_jsonl is None:
        print("ERROR: Kalshi weather paths not found.", file=sys.stderr)
        return 1

    result = purge_simulated_weather(
        nws_dir=nws_dir,
        observed_jsonl=observed_jsonl,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
