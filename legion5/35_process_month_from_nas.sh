#!/usr/bin/env bash
# Pull one month of raw GRIB from NAS, extract KMIA point, filter VALID_ONLY, delete raw.
# Optimized: LAN SSH (nas-local), uncompressed tar, persistent ControlMaster.
set -euo pipefail

YEAR="${1:?YEAR required}"
MONTH="${2:?MONTH required (01-12)}"
MONTH=$(printf '%02d' "$((10#$MONTH))")

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}:$PATH"

export NAS_SSH_HOST="${NAS_SSH_HOST:-nas-local}"
export NAS_TAR_COMPRESS="${NAS_TAR_COMPRESS:-no}"
export NAS_ROOT="${NAS_KMIA_ROOT:-/volume2/Data/App_Development/KMIA_Ingest}"

LOG="$ROOT/logs/processing/month_${YEAR}${MONTH}.log"
mkdir -p "$ROOT/logs/processing" "$HOME/.ssh/controlmasters"

# shellcheck source=nas_pull_helpers.sh
source "$SCRIPTS/nas_pull_helpers.sh"
nas_pull_autodetect_mode

# Re-mount SMB if Z: dropped mid-batch (common on long runs).
if [ "${NAS_PULL_MODE:-}" = "smb" ] && [ -f "$ROOT/secrets/nas_smb_password" ]; then
  rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
  if [ -z "${NAS_SMB_DRIVE:-}" ] || [ ! -d "${NAS_SMB_DRIVE%/}/${rel}/raw" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"$LOG" 2>&1 || true
    nas_pull_autodetect_mode
  fi
fi

WORKERS="${KMIA_EXTRACT_WORKERS:-4}"

POINTS="$ROOT/processed/points/station=KMIA"
MONTHLY="$POINTS/monthly/${YEAR}"
MAXT_VALID="$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_VALID_ONLY.csv"
WDIR_VALID="$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_VALID_ONLY.csv"

mkdir -p "$MONTHLY" "$ROOT/raw/forecast/ndfd_aws"

log() { echo "$1" | tee -a "$LOG"; }

if [ -f "$MAXT_VALID" ] && [ -f "$WDIR_VALID" ]; then
  log "SKIP ${YEAR}-${MONTH} — VALID_ONLY already exists"
  exit 0
fi

log "=== Process ${YEAR}-${MONTH} from NAS $(date -u) pull=${NAS_PULL_MODE:-ssh} host=${NAS_SSH_HOST} workers=${WORKERS} ==="

if [ ! -f "$MAXT_VALID" ]; then
  dest="$ROOT/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}"
  local_n=0
  if [ -d "$dest" ]; then
    local_n=$(find "$dest" -type f 2>/dev/null | wc -l | tr -d ' ')
  fi
  if [ "${local_n:-0}" -gt 0 ]; then
    log "  local maxt raw present (${local_n} files) — skip NAS pull"
    n=$local_n
  else
    n=$(nas_pull_month_var maxt "$YEAR" "$MONTH" "$dest" "$LOG" || echo 0)
    log "  pulled ${n} maxt files"
  fi
  log "  extract maxt"
  "$PYTHON" "$SCRIPTS/22_batch_extract_local_gribs.py" \
    --subcategory maxt --year "$YEAR" --month "$MONTH" --pattern "YGUZ*" \
    --root "$ROOT" --workers "$WORKERS" \
    --output "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
  log "  filter maxt VALID_ONLY"
  "$PYTHON" "$SCRIPTS/23_filter_valid_only.py" \
    --input "$MONTHLY/ndfd_kmia_maxt_${YEAR}${MONTH}_point_forecasts.csv" \
    --output "$MAXT_VALID" >>"$LOG" 2>&1
fi

if [ ! -f "$WDIR_VALID" ]; then
  dest="$ROOT/raw/forecast/ndfd_aws/wdir/${YEAR}/${MONTH}"
  local_n=0
  if [ -d "$dest" ]; then
    local_n=$(find "$dest" -type f 2>/dev/null | wc -l | tr -d ' ')
  fi
  if [ "${local_n:-0}" -gt 0 ]; then
    log "  local wdir raw present (${local_n} files) — skip NAS pull"
    n=$local_n
  else
    n=$(nas_pull_month_var wdir "$YEAR" "$MONTH" "$dest" "$LOG" || echo 0)
    log "  pulled ${n} wdir files"
  fi
  log "  extract wdir"
  "$PYTHON" "$SCRIPTS/22_batch_extract_local_gribs.py" \
    --subcategory wdir --year "$YEAR" --month "$MONTH" --pattern "YBUZ*" \
    --root "$ROOT" --workers "$WORKERS" \
    --output "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" >>"$LOG" 2>&1
  log "  filter wdir VALID_ONLY"
  "$PYTHON" "$SCRIPTS/23_filter_valid_only.py" \
    --input "$MONTHLY/ndfd_kmia_wdir_${YEAR}${MONTH}_point_forecasts.csv" \
    --output "$WDIR_VALID" >>"$LOG" 2>&1
fi

log "  delete raw GRIB for ${YEAR}-${MONTH}"
rm -rf "$ROOT/raw/forecast/ndfd_aws/maxt/${YEAR}/${MONTH}" \
       "$ROOT/raw/forecast/ndfd_aws/wdir/${YEAR}/${MONTH}" 2>/dev/null || true

log "DONE ${YEAR}-${MONTH} $(date -u)"
