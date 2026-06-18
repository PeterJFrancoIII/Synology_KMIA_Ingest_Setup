#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--source-path", required=True)
    p.add_argument("--format", required=True)
    p.add_argument("--decoder", default="unknown")
    p.add_argument("--status", default="ok")
    p.add_argument("--error-text", default="")
    p.add_argument("--manifest", default="/data/KMIA_Ingest/manifest/run_log.jsonl")
    args = p.parse_args()

    path = Path(args.file)
    record = {
        "source": args.source,
        "source_path": args.source_path,
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "local_path": str(path),
        "sha256": sha256_file(path) if path.is_file() else None,
        "content_length": path.stat().st_size if path.is_file() else None,
        "format": args.format,
        "station_id": "KMIA",
        "station_lat": 25.7975,
        "station_lon": -80.2872,
        "decoder": args.decoder,
        "status": args.status,
        "error_text": args.error_text or None,
    }

    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
