# Enable WSL2 features, install Ubuntu, schedule post-reboot container start
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Enable WSL features ===" -ForegroundColor Cyan
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

Write-Host "=== wsl --install ==="
wsl --install -d Ubuntu-24.04 --no-launch 2>&1

$wslList = wsl -l -v 2>&1 | Out-String
if ($wslList -match 'Ubuntu') {
    Write-Host "Ubuntu WSL ready" -ForegroundColor Green
    & "$here\08_install_wsl_docker.ps1"
    if ($LASTEXITCODE -eq 0) {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Start-Sleep -Seconds 30
        & "$here\09_run_kmia_container.ps1"
        exit $LASTEXITCODE
    }
}

# Schedule post-reboot resume
$startup = [Environment]::GetFolderPath('Startup')
Copy-Item -Path "$here\11_post_reboot_container.cmd" -Destination (Join-Path $startup 'kmia_container_resume.cmd') -Force
Write-Host 'REBOOT_REQUIRED in 90s - container auto-starts after login' -ForegroundColor Yellow
shutdown /r /t 90 /f /c 'KMIA WSL Docker setup'
