#!/usr/bin/env bash
# Storage headroom check before NDFD pull/extract/backfill.
# Run on Legion5 (Git Bash). Uses SMB Z: for NAS totals when mounted.
#
# Usage:
#   bash D:/KMIA_Process/scripts/53_check_storage_headroom.sh
#   MIN_NAS_FREE_GB=100 MIN_LEGION5_FREE_GB=50 bash .../53_check_storage_headroom.sh

set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"

MIN_NAS_FREE_GB="${MIN_NAS_FREE_GB:-100}"
MIN_LEGION5_FREE_GB="${MIN_LEGION5_FREE_GB:-50}"
# Rough budget: one maxt month YGUZ-only on Legion5 local (~12 GB) + extract scratch
NEEDED_LEGION5_GB="${NEEDED_LEGION5_GB:-15}"
# Rough budget: one full NDFD year on NAS (maxt ~57 GB; wdir ~490 GB if ever pulled)
NEEDED_NAS_MAXT_YEAR_GB="${NEEDED_NAS_MAXT_YEAR_GB:-60}"
NEEDED_NAS_FULL_YEAR_GB="${NEEDED_NAS_FULL_YEAR_GB:-550}"

REL="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
NAS_ROOT=""
if [ -n "${NAS_SMB_DRIVE:-}" ] && [ -d "${NAS_SMB_DRIVE%/}/${REL}" ]; then
  NAS_ROOT="${NAS_SMB_DRIVE%/}/${REL}"
fi

gb_from_bytes() {
  awk -v b="$1" 'BEGIN { printf "%.1f", b / 1073741824 }'
}

log() { echo "[storage] $*"; }

fail=0

# --- Legion5 D: (local scratch / AWS download target) ---
if command -v powershell.exe >/dev/null 2>&1; then
  read -r d_free d_total <<<"$(powershell.exe -NoProfile -Command \
    "\$d=(Get-PSDrive D -ErrorAction SilentlyContinue); if(\$d){Write-Output (\$d.Free.ToString()+' '+(\$d.Used+\$d.Free).ToString())}else{Write-Output '0 0'}" \
    | tr -d '\r' | tail -1)"
  d_free_gb="$(gb_from_bytes "$d_free")"
  d_total_gb="$(gb_from_bytes "$d_total")"
  log "Legion5 D: ${d_free_gb} GB free / ${d_total_gb} GB total"
  if awk -v free="$d_free_gb" -v min="$MIN_LEGION5_FREE_GB" 'BEGIN { exit (free >= min) ? 0 : 1 }'; then
    log "  OK — above minimum ${MIN_LEGION5_FREE_GB} GB"
  else
    log "  WARN — below minimum ${MIN_LEGION5_FREE_GB} GB; pause pulls/extracts"
    fail=1
  fi
  if awk -v free="$d_free_gb" -v need="$NEEDED_LEGION5_GB" 'BEGIN { exit (free >= need) ? 0 : 1 }'; then
    log "  OK — enough for ~1 maxt month local scratch (${NEEDED_LEGION5_GB} GB)"
  else
    log "  WARN — need ~${NEEDED_LEGION5_GB} GB for next maxt month on D:"
    fail=1
  fi
else
  log "Legion5 D: (powershell unavailable — skip)"
fi

# --- NAS via Z: ---
if [ -n "$NAS_ROOT" ]; then
  if command -v powershell.exe >/dev/null 2>&1; then
    read -r z_free z_total <<<"$(powershell.exe -NoProfile -Command \
      "\$z=(Get-PSDrive Z -ErrorAction SilentlyContinue); if(\$z){Write-Output (\$z.Free.ToString()+' '+(\$z.Used+\$z.Free).ToString())}else{Write-Output '0 0'}" \
      | tr -d '\r' | tail -1)"
    z_free_gb="$(gb_from_bytes "$z_free")"
    z_total_gb="$(gb_from_bytes "$z_total")"
    log "NAS (Z: Data share) ${z_free_gb} GB free / ${z_total_gb} GB total"
    if awk -v free="$z_free_gb" -v min="$MIN_NAS_FREE_GB" 'BEGIN { exit (free >= min) ? 0 : 1 }'; then
      log "  OK — above minimum ${MIN_NAS_FREE_GB} GB"
    else
      log "  WARN — below minimum ${MIN_NAS_FREE_GB} GB"
      fail=1
    fi
    if awk -v free="$z_free_gb" -v need="$NEEDED_NAS_MAXT_YEAR_GB" 'BEGIN { exit (free >= need) ? 0 : 1 }'; then
      log "  OK — room for another maxt year (~${NEEDED_NAS_MAXT_YEAR_GB} GB)"
    else
      log "  WARN — tight for maxt-year ingest (~${NEEDED_NAS_MAXT_YEAR_GB} GB needed)"
      fail=1
    fi
    if awk -v free="$z_free_gb" -v need="$NEEDED_NAS_FULL_YEAR_GB" 'BEGIN { exit (free >= need) ? 0 : 1 }'; then
      log "  OK — room for maxt+wdir year (~${NEEDED_NAS_FULL_YEAR_GB} GB)"
    else
      log "  NOTE — not enough for maxt+wdir year without cleanup (~${NEEDED_NAS_FULL_YEAR_GB} GB)"
    fi
    log "KMIA_Ingest on NAS: $NAS_ROOT"
    for sub in raw processed logs; do
      if [ -d "$NAS_ROOT/$sub" ]; then
        sz="$(powershell.exe -NoProfile -Command \
          "\$s=(Get-ChildItem -LiteralPath '$NAS_ROOT/$sub' -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum; [math]::Round(\$s/1GB,1)" \
          | tr -d '\r' | tail -1)"
        log "  $sub/: ${sz} GB"
      fi
    done
    if [ -d "$NAS_ROOT/raw/forecast/ndfd_aws/maxt/2026" ]; then
      m26="$(powershell.exe -NoProfile -Command \
        "\$s=(Get-ChildItem -LiteralPath '$NAS_ROOT/raw/forecast/ndfd_aws/maxt/2026' -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum; [math]::Round(\$s/1GB,1)" \
        | tr -d '\r' | tail -1)"
      log "  maxt/2026 on NAS: ${m26} GB"
    else
      log "  maxt/2026 on NAS: not present (2026 Kalshi job may be on D: only)"
    fi
  fi
else
  log "NAS Z: not mounted — cannot audit NAS free space (run 43_setup_nas_smb.ps1)"
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  log "RESULT: FAIL — resolve storage before large backfill"
  exit 1
fi

log "RESULT: PASS — storage headroom OK for planned NDFD work"
exit 0
