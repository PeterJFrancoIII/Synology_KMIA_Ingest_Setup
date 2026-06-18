#!/usr/bin/env bash
# NAS pull helpers for Legion5 month processing.
#
# NAS_PULL_MODE:
#   ssh (default) — tar stream over SSH (works everywhere; single stream)
#   smb           — robocopy from Synology SMB share (faster on LAN; needs mount)
#
# SMB one-time: powershell -File legion5/43_setup_nas_smb.ps1
# Extra OpenSSH flags (Legion5+Synology: ControlMaster auto can hang).
NAS_SSH_OPTS="${NAS_SSH_OPTS:--o ControlMaster=no -o ConnectTimeout=15 -o BatchMode=yes}"

ssh_nas() {
  # shellcheck disable=SC2086
  ssh $NAS_SSH_OPTS "$@"
}

# Count transferred GRIB files (day subdirs under month folder).
count_pulled_files() {
  local dest="$1"
  find "$dest" -type f 2>/dev/null | wc -l | tr -d ' '
}

# Resolve NAS raw month directory (handles 08 vs 8 folder naming) — SSH path.
resolve_nas_month_dir() {
  local var="$1" year="$2" month="$3"
  local base="${NAS_ROOT}/raw/forecast/ndfd_aws/${var}/${year}"
  local m_pad m_unpad
  m_pad=$(printf '%02d' "$((10#$month))")
  m_unpad=$((10#$month))
  local remote host
  host="${NAS_SSH_HOST:-nas-local}"
  for m in "$m_pad" "$m_unpad"; do
    if ssh_nas "$host" "test -d '${base}/${m}' && ls '${base}/${m}' 2>/dev/null | head -1" 2>/dev/null | grep -q .; then
      echo "${base}/${m}"
      return 0
    fi
  done
  return 1
}

# Resolve SMB source path for one variable/month (returns Git-Bash path).
resolve_smb_month_dir() {
  local var="$1" year="$2" month="$3"
  local m_pad m_unpad
  m_pad=$(printf '%02d' "$((10#$month))")
  m_unpad=$((10#$month))
  local host share rel base drive
  drive="${NAS_SMB_DRIVE:-}"
  rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
  # Prefer mapped drive (Z:) when available — faster and uses existing session.
  if [ -n "$drive" ]; then
    base="${drive%/}/${rel}/raw/forecast/ndfd_aws/${var}/${year}"
    for m in "$m_pad" "$m_unpad"; do
      if [ -d "${base}/${m}" ] && [ -n "$(ls -A "${base}/${m}" 2>/dev/null)" ]; then
        echo "${base}/${m}"
        return 0
      fi
    done
  fi
  host="${NAS_SMB_HOST:-192.168.0.193}"
  share="${NAS_SMB_SHARE:-Data}"
  base="//${host}/${share}/${rel}/raw/forecast/ndfd_aws/${var}/${year}"
  for m in "$m_pad" "$m_unpad"; do
    if [ -d "${base}/${m}" ] && [ -n "$(ls -A "${base}/${m}" 2>/dev/null)" ]; then
      echo "${base}/${m}"
      return 0
    fi
  done
  return 1
}

# Convert Git-Bash path to Windows path for robocopy.
to_win_path() {
  local p="$1"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$p"
    return
  fi
  if [[ "$p" == [A-Za-z]:* ]]; then
    echo "${p//\//\\}"
    return
  fi
  if [[ "$p" == //* ]]; then
    p="\\\\${p#//}"
    p="${p//\//\\}"
  fi
  echo "$p"
}

nas_pull_month_var_ssh() {
  local var="$1" year="$2" month="$3" dest="$4" log="$5"
  local host="${NAS_SSH_HOST:-nas-local}"
  local remote
  remote=$(resolve_nas_month_dir "$var" "$year" "$month") || {
    echo "  WARN: no NAS raw dir for ${var} ${year}-${month}" | tee -a "$log"
    return 1
  }
  mkdir -p "$dest"
  local tar_flags="cf"
  if [ "${NAS_TAR_COMPRESS:-no}" = "yes" ]; then
    tar_flags="czf"
  fi
  echo "  pull ${var} from ${remote} (tar ${tar_flags} over ssh via ${host})..." >>"$log"
  if [ "$tar_flags" = "czf" ]; then
    ssh_nas "$host" "tar czf - -C '${remote}' ." | tar xzf - -C "$dest" 2>>"$log"
  else
    ssh_nas "$host" "tar cf - -C '${remote}' ." | tar xf - -C "$dest" 2>>"$log"
  fi
  count_pulled_files "$dest"
}

nas_pull_month_var_smb() {
  local var="$1" year="$2" month="$3" dest="$4" log="$5"
  local src threads win_src win_dest rc
  src=$(resolve_smb_month_dir "$var" "$year" "$month") || {
    echo "  WARN: SMB path not found for ${var} ${year}-${month} (run 43_setup_nas_smb.ps1?)" | tee -a "$log"
    return 1
  }
  mkdir -p "$dest"
  threads="${NAS_SMB_THREADS:-16}"
  win_src=$(to_win_path "$src")
  win_dest=$(to_win_path "$dest")
  echo "  pull ${var} from ${src} (robocopy /MT:${threads})..." >>"$log"
  MSYS2_ARG_CONV_EXCL='*' /c/Windows/System32/robocopy.exe "${win_src}" "${win_dest}" \
    /E /MT:${threads} /R:3 /W:5 /NP /NFL /NDL /NJH /NJS /nc /ns >>"$log" 2>&1
  rc=$?
  # robocopy: 0-7 = success (copied or nothing new)
  if [ "$rc" -ge 8 ]; then
    echo "  ERROR: robocopy failed rc=${rc} for ${var} ${year}-${month}" | tee -a "$log"
    return 1
  fi
  count_pulled_files "$dest"
}

# Pull one variable/month. SMB with SSH fallback on failure.
nas_pull_month_var() {
  local var="$1" year="$2" month="$3" dest="$4" log="$5"
  case "${NAS_PULL_MODE:-ssh}" in
    smb)
      if nas_pull_month_var_smb "$var" "$year" "$month" "$dest" "$log"; then
        count_pulled_files "$dest"
        return 0
      fi
      echo "  SMB pull failed for ${var} ${year}-${month} — falling back to SSH" >>"$log"
      nas_pull_month_var_ssh "$var" "$year" "$month" "$dest" "$log"
      ;;
    *) nas_pull_month_var_ssh "$var" "$year" "$month" "$dest" "$log" ;;
  esac
}

# Use SMB when Z: (or NAS_SMB_DRIVE) is mounted; else UNC; else SSH tar.
nas_pull_autodetect_mode() {
  if [ -n "${NAS_PULL_MODE:-}" ]; then
    return 0
  fi
  local drive rel host share unc
  drive="${NAS_SMB_DRIVE:-}"
  rel="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"
  host="${NAS_SMB_HOST:-192.168.0.193}"
  share="${NAS_SMB_SHARE:-Data}"
  if [ -n "$drive" ] && [ -d "${drive%/}/${rel}/raw" ]; then
    export NAS_PULL_MODE=smb
    return 0
  fi
  unc="//${host}/${share}/${rel}/raw"
  if [ -d "$unc" ]; then
    export NAS_PULL_MODE=smb
    export NAS_SMB_DRIVE=""
    return 0
  fi
  export NAS_PULL_MODE=ssh
}
