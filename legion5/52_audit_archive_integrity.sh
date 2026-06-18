#!/usr/bin/env bash
# Run GRIB archive integrity audit via Legion5 SMB mount (Z:).
set -euo pipefail

ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
SCRIPTS="${SCRIPTS:-$ROOT/scripts}"
PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
REL="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"

# shellcheck source=kmia_legion5_env.sh
source "$SCRIPTS/kmia_legion5_env.sh"

if [ -f "$ROOT/secrets/nas_smb_password" ]; then
  powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >/dev/null 2>&1 || true
fi

NAS_ROOT=""
if [ -n "${NAS_SMB_DRIVE:-}" ] && [ -d "${NAS_SMB_DRIVE%/}/${REL}" ]; then
  NAS_ROOT="${NAS_SMB_DRIVE%/}/${REL}"
elif [ -d "//${NAS_SMB_HOST:-192.168.0.193}/${NAS_SMB_SHARE:-Data}/${REL}" ]; then
  NAS_ROOT="//${NAS_SMB_HOST}/${NAS_SMB_SHARE}/${REL}"
else
  echo "ERROR: NAS not reachable via SMB. Run 43_setup_nas_smb.ps1" >&2
  exit 1
fi

echo "Auditing: $NAS_ROOT"
"$PYTHON" "$SCRIPTS/audit_ndfd_archive_integrity.py" \
  --nas-root "$NAS_ROOT" \
  --out-dir "$ROOT/manifest" \
  --years "2020,2021,2022,2023,2024,2025"
