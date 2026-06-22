#!/usr/bin/env python3
"""Move NWS snapshots that are not on the canonical KMIA MapClick grid out of the live archive.

Misaligned snapshots (legacy MFL/106,51, MFL/109,96, missing grid metadata) must not
feed Kalshi backtests or paper-trading feature builds.

NO REAL TRADING — data hygiene only.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from kmia_kalshi_paths import kalshi_nws_dir, optional_existing
from weather_data_policy import is_usable_nws_snapshot


def quarantine_mismatched_snapshots(
    nws_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    nws_dir = Path(nws_dir)
    quarantine = nws_dir / "_quarantine_wrong_grid"
    quarantine.mkdir(parents=True, exist_ok=True)

    stats = {"scanned": 0, "kept": 0, "quarantined": 0, "latest_reset": 0}

    for path in sorted(nws_dir.glob("nws_kmia_snapshot_*.json")):
        stats["scanned"] += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            stats["quarantined"] += 1
            if not dry_run:
                shutil.move(str(path), str(quarantine / path.name))
            continue

        if is_usable_nws_snapshot(data):
            stats["kept"] += 1
            continue

        stats["quarantined"] += 1
        if not dry_run:
            shutil.move(str(path), str(quarantine / path.name))

    latest = nws_dir / "latest_nws_kmia_snapshot.json"
    if latest.is_file():
        try:
            latest_data = json.loads(latest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            latest_data = {}
        if not is_usable_nws_snapshot(latest_data):
            stats["latest_reset"] += 1
            if not dry_run:
                latest.unlink(missing_ok=True)

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nws-dir", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    nws_dir = args.nws_dir or optional_existing(kalshi_nws_dir())
    if nws_dir is None:
        print("NWS dir not found — nothing to quarantine.")
        return 0

    stats = quarantine_mismatched_snapshots(nws_dir, dry_run=args.dry_run)
    mode = "DRY-RUN" if args.dry_run else "DONE"
    print(
        f"[{mode}] scanned={stats['scanned']} kept={stats['kept']} "
        f"quarantined={stats['quarantined']} latest_reset={stats['latest_reset']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
