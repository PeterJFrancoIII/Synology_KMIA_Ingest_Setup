#!/usr/bin/env bash
set +e
ROOT=/d/KMIA_Process
BENCH=$ROOT/raw/bench_w
rm -rf "$BENCH"
mkdir -p "$BENCH/raw/forecast/ndfd_aws/maxt/2021/07/15"
t1=$(date +%s)
cp -r "Z:/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2021/07/15/"* "$BENCH/raw/forecast/ndfd_aws/maxt/2021/07/15/"
t2=$(date +%s)
echo "SMB_CP_DAY=$((t2-t1))s files=$(find "$BENCH" -type f | wc -l)"
for w in 1 4 8; do
  t1=$(date +%s)
  /e/Miniforge3/python.exe "$ROOT/scripts/22_batch_extract_local_gribs.py" \
    --root "$BENCH" --subcategory maxt --year 2021 --month 07 \
    --pattern "YGUZ*" --workers "$w" --output "$BENCH/out_w${w}.csv" 2>/dev/null | tail -1
  t2=$(date +%s)
  echo "WORKERS_${w}=$((t2-t1))s"
done
