#!/bin/sh
set -eu

ROOT="/volume2/Data/App_Development"

mkdir -p "$ROOT/Kalshi" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest" 2>/dev/null || true
mkdir -p "$ROOT/Docker" 2>/dev/null || true
mkdir -p "$ROOT/Backups" 2>/dev/null || true
mkdir -p "$ROOT/Logs" 2>/dev/null || true
mkdir -p "$ROOT/Scripts" 2>/dev/null || true
mkdir -p "$ROOT/Archives" 2>/dev/null || true

mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/maxt" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/temp" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/td" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/sky" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/wdir" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/wspd" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/pop12" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_aws/qpf" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_thredds" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/forecast/ndfd_airs" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/isd" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/isd_lite" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/lcd" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/rtma" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/urma" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/synoptic" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/raw/observed/madis" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/messages" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/points" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/daily" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/joins" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/parquet" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/processed/csv" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/manifest" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/config" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/scripts" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/logs/host" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/logs/container" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/logs/ingestion" 2>/dev/null || true
mkdir -p "$ROOT/KMIA_Ingest/logs/smoke_tests" 2>/dev/null || true
mkdir -p "$ROOT/Docker/kmia-arch-ingest" 2>/dev/null || true
mkdir -p "$ROOT/Docker/kmia-paper-research" 2>/dev/null || true
mkdir -p "$ROOT/Kalshi/scripts" 2>/dev/null || true
mkdir -p "$ROOT/Kalshi/backend/data/processed/mae" 2>/dev/null || true
mkdir -p "$ROOT/Kalshi/backend/data/research" 2>/dev/null || true
mkdir -p "$ROOT/logs/paper_research" 2>/dev/null || true
mkdir -p "$ROOT/logs/paper_trading" 2>/dev/null || true
mkdir -p "$ROOT/secrets" 2>/dev/null || true
mkdir -p "$ROOT/Backups/kmia_ingest_config" 2>/dev/null || true
mkdir -p "$ROOT/Backups/manifests" 2>/dev/null || true
mkdir -p "$ROOT/Backups/scripts" 2>/dev/null || true

find "$ROOT" -maxdepth 4 -type d 2>/dev/null | sort
