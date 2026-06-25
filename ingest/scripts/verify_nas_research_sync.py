#!/usr/bin/env python3
"""Verify NAS research sync matches Legion5 mirror manifest (read-only).

Usage:
  NAS_HOST=MediaServer2 python3 ingest/scripts/verify_nas_research_sync.py
  python3 ingest/scripts/verify_nas_research_sync.py --local-policy /path/to/trading_policy.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _load_json(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _policy_stamp(policy: Optional[dict[str, Any]]) -> Optional[str]:
    if not policy:
        return None
    for key in ("generated_at_utc", "exported_at_utc", "approved_at_utc", "approved_at"):
        val = policy.get(key)
        if val:
            return str(val)
    return None


def fetch_nas_policy(nas_host: str) -> Optional[dict[str, Any]]:
    remote = "/volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy.json"
    manifest_remote = "/volume2/Data/App_Development/Kalshi/backend/data/research/legion5_sync_manifest.json"
    _ = manifest_remote  # reserved for future manifest-first checks
    try:
        proc = subprocess.run(
            ["ssh", nas_host, f"sudo cat '{remote}'"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"SSH failed: {exc}")
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        print(f"Could not read NAS policy (rc={proc.returncode})")
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("NAS policy JSON invalid")
        return None


def fetch_nas_manifest(nas_host: str) -> Optional[dict[str, Any]]:
    remote = "/volume2/Data/App_Development/Kalshi/backend/data/research/legion5_sync_manifest.json"
    try:
        proc = subprocess.run(
            ["ssh", nas_host, f"sudo cat '{remote}'"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verify NAS vs local research policy sync")
    parser.add_argument("--nas-host", default="MediaServer2")
    parser.add_argument(
        "--local-policy",
        type=Path,
        default=Path.home() / "Desktop/App Development/Kalshi/backend/data/research/trading_policy.json",
    )
    parser.add_argument(
        "--legion5-mirror",
        type=Path,
        default=None,
        help="Optional Legion5 mirror path if mounted locally",
    )
    args = parser.parse_args(argv)

    nas_policy = fetch_nas_policy(args.nas_host)
    nas_manifest = fetch_nas_manifest(args.nas_host)
    local_policy = _load_json(args.local_policy)
    mirror_policy = _load_json(args.legion5_mirror) if args.legion5_mirror else None

    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "nas_host": args.nas_host,
        "nas_policy_stamp": _policy_stamp(nas_policy),
        "local_policy_stamp": _policy_stamp(local_policy),
        "mirror_policy_stamp": _policy_stamp(mirror_policy),
        "nas_order_mode": (nas_policy or {}).get("order_mode"),
        "local_order_mode": (local_policy or {}).get("order_mode"),
        "legion5_sync_manifest_at": (nas_manifest or {}).get("synced_at_utc"),
        "legion5_sync_file_count": len((nas_manifest or {}).get("files") or []),
        "in_sync_local_nas": _policy_stamp(nas_policy) == _policy_stamp(local_policy)
        if nas_policy and local_policy
        else None,
        "warnings": [],
    }

    if nas_policy is None:
        report["warnings"].append("NAS trading_policy.json unreadable")
    if nas_manifest is None:
        report["warnings"].append("legion5_sync_manifest.json missing on NAS (run 55_sync_research_to_nas.ps1)")
    if local_policy is None:
        report["warnings"].append("Local trading_policy.json missing")
    if nas_policy and local_policy:
        if nas_policy.get("order_mode") != local_policy.get("order_mode"):
            report["warnings"].append("order_mode mismatch between NAS and local")
        if nas_policy.get("min_forecast_edge") != local_policy.get("min_forecast_edge"):
            report["warnings"].append("min_forecast_edge mismatch between NAS and local")

    print(json.dumps(report, indent=2))
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
