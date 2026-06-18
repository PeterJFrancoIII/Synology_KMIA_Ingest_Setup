#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/KMIA_Ingest"
MANIFEST="$ROOT/manifest/run_log.jsonl"
LOG="$ROOT/logs/ingestion/gap_audit_$(date -u +%Y%m%d).log"

mkdir -p "$(dirname "$LOG")"

{
  echo "=== Gap Audit ==="
  echo "Started: $(date -u)"
  echo "Manifest: $MANIFEST"
} | tee "$LOG"

if [ ! -f "$MANIFEST" ]; then
  echo "No manifest found at $MANIFEST" | tee -a "$LOG"
  echo "Run smoke tests first to populate manifest." | tee -a "$LOG"
  exit 1
fi

total_records="$(wc -l < "$MANIFEST" | tr -d ' ')"
error_records="$(grep -c '"status": "error"' "$MANIFEST" 2>/dev/null || true)"
partial_records="$(grep -c '"status": "partial"' "$MANIFEST" 2>/dev/null || true)"

echo "Total manifest records: $total_records" | tee -a "$LOG"
echo "Error records: $error_records" | tee -a "$LOG"
echo "Partial records: $partial_records" | tee -a "$LOG"

echo "Recent records:" | tee -a "$LOG"
tail -5 "$MANIFEST" | tee -a "$LOG"

echo "Gap audit complete." | tee -a "$LOG"
