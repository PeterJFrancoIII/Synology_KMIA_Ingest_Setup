#!/usr/bin/env python3
"""Validate and promote Kalshi vendor orderbook bulk drops into research archive.

NO REAL TRADING — reference data only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

KXHIGHMIA_PREFIX = "KXHIGHMIA-"
SCHEMA_VERSION = "1.0"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _validate_ticker(ticker: str) -> bool:
    return ticker.upper().startswith(KXHIGHMIA_PREFIX)


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{lineno}: expected object")
            yield row


def _normalize_vendor_row(row: dict[str, Any]) -> dict[str, Any]:
    ticker = str(row.get("ticker") or "").upper()
    if not _validate_ticker(ticker):
        raise ValueError(f"non-KXHIGHMIA ticker: {ticker}")
    ts = row.get("snapshot_at_utc") or row.get("fetched_at_utc")
    if not ts:
        raise ValueError(f"missing snapshot_at_utc for {ticker}")
    ob: dict[str, Any] = {}
    if row.get("yes_bids") or row.get("no_bids"):
        ob["yes_bids"] = row.get("yes_bids") or []
        ob["no_bids"] = row.get("no_bids") or []
    elif isinstance(row.get("orderbooks"), dict) and ticker in row["orderbooks"]:
        ob = row["orderbooks"][ticker]
    else:
        raise ValueError(f"no ladder data for {ticker}")
    return {
        "snapshot_at_utc": ts,
        "ticker": ticker,
        "orderbook": ob,
        "source": row.get("source") or "kalshi_vendor_bulk",
        "schema_version": row.get("schema_version") or SCHEMA_VERSION,
    }


def _group_to_checkpoints(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group per-ticker rows into WS-checkpoint-compatible snapshots."""
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"orderbooks": {}})
    for row in rows:
        ts = str(row["snapshot_at_utc"])
        bucket = buckets[ts]
        bucket["snapshot_at_utc"] = ts
        bucket["source"] = row.get("source") or "kalshi_vendor_bulk"
        bucket["schema_version"] = row.get("schema_version") or SCHEMA_VERSION
        bucket["orderbooks"][row["ticker"]] = row["orderbook"]
    return list(buckets.values())


def _verify_manifest(inbound_dir: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for entry in manifest.get("files") or []:
        name = entry.get("name")
        expected = (entry.get("sha256") or "").lower()
        if not name:
            errors.append("manifest entry missing name")
            continue
        path = inbound_dir / name
        if not path.is_file():
            errors.append(f"missing file: {name}")
            continue
        if expected:
            actual = _sha256_file(path)
            if actual != expected:
                errors.append(f"checksum mismatch {name}: expected {expected}, got {actual}")
    return errors


def ingest_vendor_drop(
    *,
    inbound_dir: Path,
    archive_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    quarantine = inbound_dir / "quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)
    vendor_out = archive_dir / "orderbook_vendor"
    vendor_out.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inbound_dir": str(inbound_dir),
        "archive_dir": str(archive_dir),
        "files_processed": 0,
        "rows_valid": 0,
        "rows_quarantined": 0,
        "checkpoints_written": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    manifest_path = inbound_dir / "manifest.json"
    data_files: list[Path] = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report["errors"].append(f"manifest.json: {exc}")
            manifest = {}
        else:
            manifest_errors = _verify_manifest(inbound_dir, manifest)
            report["errors"].extend(manifest_errors)
            for entry in manifest.get("files") or []:
                name = entry.get("name")
                if name and (inbound_dir / name).is_file():
                    data_files.append(inbound_dir / name)
    else:
        data_files = sorted(
            p for p in inbound_dir.iterdir()
            if p.is_file() and p.suffix in {".jsonl", ".json"} and p.name != "manifest.json"
        )

    if not data_files:
        report["errors"].append("no data files found in inbound dir")
        return report

    normalized: list[dict[str, Any]] = []
    for path in data_files:
        report["files_processed"] += 1
        try:
            for row in _iter_jsonl(path):
                try:
                    normalized.append(_normalize_vendor_row(row))
                    report["rows_valid"] += 1
                except ValueError as exc:
                    report["rows_quarantined"] += 1
                    qname = f"bad_{path.stem}_{report['rows_quarantined']}.json"
                    if not dry_run:
                        (quarantine / qname).write_text(
                            json.dumps({"error": str(exc), "row": row}) + "\n",
                            encoding="utf-8",
                        )
        except ValueError as exc:
            report["errors"].append(str(exc))
            if not dry_run:
                shutil.move(str(path), str(quarantine / f"failed_{path.name}"))

    checkpoints = _group_to_checkpoints(normalized)
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cp in checkpoints:
        ts = _parse_ts(cp.get("snapshot_at_utc"))
        day = (ts or datetime.now(timezone.utc)).date().isoformat()
        by_day[day].append(cp)

    for day, records in sorted(by_day.items()):
        out_path = vendor_out / f"{day}.jsonl"
        report["checkpoints_written"] += len(records)
        if dry_run:
            continue
        with out_path.open("a", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

    report_path = vendor_out / f"ingest_report_{stamp}.json"
    if not dry_run:
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest Kalshi vendor orderbook bulk drop.")
    parser.add_argument("--inbound-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    report = ingest_vendor_drop(
        inbound_dir=args.inbound_dir,
        archive_dir=args.archive_dir,
        dry_run=args.dry_run,
    )
    print(json.dumps(report, indent=2))
    return 0 if not report.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
