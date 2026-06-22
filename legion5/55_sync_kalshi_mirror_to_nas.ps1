# Sync Legion5 kalshi_mirror writes to canonical NAS Kalshi tree (requires write creds).
# kmia_legion5 SMB user is read-only; run with admin DSM account or from NAS container.
#
# Usage (Legion5 PowerShell as admin / writable share user):
#   powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_sync_kalshi_mirror_to_nas.ps1

param(
  [string]$Source = "D:\KMIA_Process\kalshi_mirror",
  [string]$Dest = "\\192.168.0.193\Data\App_Development\Kalshi"
)

if (-not (Test-Path $Source)) {
  Write-Error "Source missing: $Source"
  exit 1
}

Write-Host "robocopy $Source -> $Dest /E /XO"
robocopy $Source $Dest /E /XO /R:2 /W:5 /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) { exit 1 }
Write-Host "sync ok"
