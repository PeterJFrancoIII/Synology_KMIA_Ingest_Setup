#!/usr/bin/env bash
# Pull chart portal + year studies + extracted point CSV lake from Legion5 to Mac Research.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${LEGION5_HOST:-Legion5}"
REMOTE="D:/KMIA_Process"
DEST="$REPO/Research/Agent Analysis of KMIA Forecast Precision"
DATA="$DEST/Legion5_Extract/processed/points/station=KMIA"
REMOTE_POINTS="${REMOTE}/processed/points/station=KMIA"

mkdir -p "$DEST" "$DATA/monthly"

remote_scp() {
  local src="$1" dst="$2"
  scp "${HOST}:${src}" "$dst"
}

remote_scp_dir() {
  local src="$1" dst="$2"
  mkdir -p "$dst"
  scp -r "${HOST}:${src}"/* "$dst/" 2>/dev/null || scp -r "${HOST}:${src}/." "$dst/"
}

echo "=== Pull chart portal ==="
remote_scp_dir "${REMOTE}/analysis/KMIA_Chart_Portal" "$DEST/KMIA_Chart_Portal"

echo "=== Pull year + all-years analysis / charts ==="
for study in \
  KMIA_NDFD_Year_MaxT_Precision_2020 \
  KMIA_NDFD_Year_MaxT_Precision_2021 \
  KMIA_NDFD_Year_MaxT_Precision_2022 \
  KMIA_NDFD_Year_MaxT_Precision_2023 \
  KMIA_NDFD_Year_MaxT_Precision_2024 \
  KMIA_NDFD_Year_MaxT_Precision_2025 \
  KMIA_NDFD_AllYears_MaxT_Precision; do
  echo "  $study"
  remote_scp_dir "${REMOTE}/analysis/${study}" "$DEST/${study}"
done

echo "=== Pull yearly merged forecasts + ISD (~3.5 GB) ==="
for f in \
  ndfd_kmia_point_forecasts_VALID_ONLY_2020.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_2021.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_2022.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_2023.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_2024.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_2025.csv \
  ndfd_kmia_point_forecasts_VALID_ONLY_ALL.csv; do
  echo "  $f"
  remote_scp "${REMOTE_POINTS}/${f}" "$DATA/"
done

for y in 2020 2021 2022 2023 2024 2025; do
  obs="kmia_ncei_global_hourly_${y}.csv"
  echo "  $obs"
  remote_scp "${REMOTE_POINTS}/${obs}" "$DATA/"
done

echo "=== Pull monthly VALID_ONLY extracts (~5–6 GB) ==="
for y in 2020 2021 2022 2023 2024 2025; do
  echo "  monthly/${y}/"
  mkdir -p "$DATA/monthly/${y}"
  remote_scp "${REMOTE_POINTS}/monthly/${y}/"*_VALID_ONLY.csv "$DATA/monthly/${y}/" 2>/dev/null \
    || scp "${HOST}:${REMOTE_POINTS}/monthly/${y}/*_VALID_ONLY.csv" "$DATA/monthly/${y}/"
done

echo ""
echo "=== Pull complete ==="
echo "Charts portal: $DEST/KMIA_Chart_Portal/kmia_chart_portal.html"
echo "Yearly forecasts: $DATA/ndfd_kmia_point_forecasts_VALID_ONLY_*.csv"
echo "Monthly extracts: $DATA/monthly/"
