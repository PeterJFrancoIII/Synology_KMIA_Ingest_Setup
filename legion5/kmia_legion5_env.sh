#!/usr/bin/env bash
# Canonical Legion5 processor environment — source from all launchers.
# Default pull: SMB robocopy when Z: is mounted (43_setup_nas_smb.ps1); else SSH tar.

export KMIA_ROOT="${KMIA_ROOT:-/d/KMIA_Process}"
export KMIA_PYTHON="${KMIA_PYTHON:-/e/Miniforge3/python.exe}"
export KMIA_PATH="${KMIA_PATH:-/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2}"
export PATH="$KMIA_PATH:$PATH"

export NAS_SSH_HOST="${NAS_SSH_HOST:-nas-local}"
export NAS_SSH_OPTS="${NAS_SSH_OPTS:--o ControlMaster=no -o ConnectTimeout=15 -o BatchMode=yes}"
export NAS_TAR_COMPRESS="${NAS_TAR_COMPRESS:-no}"
export NAS_ROOT="${NAS_ROOT:-/volume2/Data/App_Development/KMIA_Ingest}"
export NAS_KMIA_ROOT="${NAS_KMIA_ROOT:-$NAS_ROOT}"

export NAS_SMB_HOST="${NAS_SMB_HOST:-192.168.0.193}"
export NAS_SMB_SHARE="${NAS_SMB_SHARE:-Data}"
export NAS_SMB_DRIVE="${NAS_SMB_DRIVE:-Z:}"
export NAS_SMB_USER="${NAS_SMB_USER:-kmia_legion5}"
export NAS_SMB_THREADS="${NAS_SMB_THREADS:-16}"
export NAS_SMB_KMIA_REL="${NAS_SMB_KMIA_REL:-App_Development/KMIA_Ingest}"

export KMIA_EXTRACT_WORKERS="${KMIA_EXTRACT_WORKERS:-10}"
export KMIA_AWS_DAY_PARALLEL="${KMIA_AWS_DAY_PARALLEL:-6}"
export KMIA_MONTH_DL_PARALLEL="${KMIA_MONTH_DL_PARALLEL:-2}"

mkdir -p "$HOME/.ssh/controlmasters"
