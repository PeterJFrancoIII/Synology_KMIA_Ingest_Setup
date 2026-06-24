# Post-reboot: finish WSL install and migrate ingest to WSL (optional upgrade path).
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$here\01_install_wsl.ps1"
if ($LASTEXITCODE -eq 0) {
    wsl -d Ubuntu -- bash -lc "bash /mnt/e/KMIA_Setup/02_bootstrap_kmia.sh"
}
