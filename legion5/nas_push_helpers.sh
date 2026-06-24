#!/usr/bin/env bash
# SMB3 push helpers — Legion5 local GRIB -> NAS canonical lake (robocopy via Z:).
#
# kmia_legion5 on Z: is read-only on normal ACLs. Before push, SSH pre-creates the
# destination month dir with mode 777 so robocopy can write via SMB3.

# shellcheck source=kmia_legion5_env.sh
source "$(dirname "${BASH_SOURCE[0]}")/kmia_legion5_env.sh"
# shellcheck source=nas_pull_helpers.sh
source "$(dirname "${BASH_SOURCE[0]}")/nas_pull_helpers.sh"

NAS_SSH_HOST="${NAS_SSH_HOST:-nas-local}"
NAS_RAW="/volume2/Data/App_Development/KMIA_Ingest/raw/forecast/ndfd_aws"
NAS_SSH_OPTS="${NAS_SSH_OPTS:--o ControlMaster=no -o ConnectTimeout=30 -o BatchMode=yes}"

ssh_nas() {
  # -n prevents ssh from consuming stdin (required when called inside `while read` loops).
  # shellcheck disable=SC2086
  ssh -n $NAS_SSH_OPTS "$NAS_SSH_HOST" "$@"
}

ensure_smb_read_mount() {
  local rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
  if [ -n "${NAS_SMB_DRIVE:-}" ] && [ -d "${NAS_SMB_DRIVE%/}/${rel}/raw" ]; then
    return 0
  fi
  if [ -f "${KMIA_ROOT:-/d/KMIA_Process}/secrets/nas_smb_password" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$SCRIPTS/43_setup_nas_smb.ps1" >>"${TRANSFER_LOG:-/dev/null}" 2>&1 \
      || true
  fi
  [ -n "${NAS_SMB_DRIVE:-}" ] && [ -d "${NAS_SMB_DRIVE%/}/${rel}/raw" ]
}

smb_dest_month_dir() {
  local var="$1" year="$2" month="$3"
  local m_pad rel
  m_pad=$(printf '%02d' "$((10#$month))")
  rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}/raw/forecast/ndfd_aws/${var}/${year}/${m_pad}"
  echo "${NAS_SMB_DRIVE:-Z:}/${rel}"
}

smb_nas_month_count() {
  local var="$1" year="$2" month="$3"
  local dir
  dir=$(smb_dest_month_dir "$var" "$year" "$month")
  if [ -d "$dir" ]; then
    find "$dir" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' \r\n'
    return 0
  fi
  echo 0
}

nas_prepare_month_dest() {
  local var="$1" year="$2" month="$3"
  local m_pad dest
  m_pad=$(printf '%02d' "$((10#$month))")
  dest="${NAS_RAW}/${var}/${year}/${m_pad}"
  ssh_nas "sudo -n mkdir -p '${dest}' && sudo -n chmod 777 '${dest}'"
}

smb_push_month() {
  local src_root="$1" var="$2" year="$3" month="$4" log="$5"
  local m_pad src dest threads win_src win_dest rc n
  m_pad=$(printf '%02d' "$((10#$month))")
  src="${src_root}/${var}/${year}/${m_pad}"
  [ -d "$src" ] || src="${src_root}/${var}/${year}/$((10#$month))"
  [ -d "$src" ] || { echo "  ERROR: local src missing for ${var}/${year}/${m_pad}" | tee -a "$log"; return 1; }

  dest=$(smb_dest_month_dir "$var" "$year" "$month")
  nas_prepare_month_dest "$var" "$year" "$month"
  threads="${NAS_SMB_THREADS:-16}"
  win_src=$(to_win_path "$src")
  win_dest=$(to_win_path "$dest")
  n=$(find "$src" -type f ! -name 'Icon*' 2>/dev/null | wc -l | tr -d ' ')
  echo "  SMB3 robocopy ${var}/${year}/${m_pad} ($n files) /MT:${threads} ..." | tee -a "$log"
  MSYS2_ARG_CONV_EXCL='*' /c/Windows/System32/robocopy.exe "${win_src}" "${win_dest}" \
    /E /MT:${threads} /R:3 /W:5 /XO /XN /NP /NFL /NDL /NJH /NJS /nc /ns >>"$log" 2>&1
  rc=$?
  if [ "$rc" -ge 8 ]; then
    echo "  ERROR: robocopy rc=${rc} for ${var}/${year}/${m_pad}" | tee -a "$log"
    return 1
  fi
  echo "  OK ${var}/${year}/${m_pad} robocopy rc=${rc}" | tee -a "$log"
  return 0
}
