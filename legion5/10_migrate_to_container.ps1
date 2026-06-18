# Full migration: WSL + Docker + kmia-arch-ingest container
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$here\08_install_wsl_docker.ps1"
if ($LASTEXITCODE -eq 10) { exit 10 }
if ($LASTEXITCODE -eq 11) { exit 11 }

& "$here\09_run_kmia_container.ps1"
