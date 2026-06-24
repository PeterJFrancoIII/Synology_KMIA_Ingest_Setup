# Legion5: WSL2 + Docker Desktop for kmia-arch-ingest container
$ErrorActionPreference = 'Continue'

Write-Host "=== WSL + Docker install ===" -ForegroundColor Cyan

# WSL
$wslOut = wsl -l -v 2>&1 | Out-String
if ($wslOut -match 'not installed') {
    Write-Host "Installing WSL..."
    wsl --install --no-distribution
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WSL feature install initiated; reboot may be required."
        exit 10
    }
    wsl --update 2>$null
    wsl --install -d Ubuntu-24.04 --no-launch 2>$null
    if (-not ((wsl -l -v 2>&1 | Out-String) -match 'Ubuntu')) {
        Write-Host "REBOOT_REQUIRED: restart Legion5 then re-run 10_migrate_to_container.ps1"
        exit 10
    }
}

# Docker Desktop
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    $installer = Join-Path $env:TEMP 'DockerDesktopInstaller.exe'
    if (-not (Test-Path $installer)) {
        Write-Host "Downloading Docker Desktop..."
        Invoke-WebRequest -Uri 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' -OutFile $installer -UseBasicParsing
    }
    Write-Host "Installing Docker Desktop (quiet)..."
    Start-Process -Wait -FilePath $installer -ArgumentList 'install','--accept-license','--quiet'
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
}

# Wait for docker daemon (start Desktop if installed but not running)
if (-not (Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue)) {
    $dde = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $dde) { Start-Process $dde }
}
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Write-Host "Waiting for Docker daemon... ($i)"
    Start-Sleep -Seconds 10
}
if (-not $ready) {
    Write-Host "Docker not ready; start Docker Desktop manually then re-run."
    exit 11
}

docker --version
wsl -l -v
Write-Host "WSL_DOCKER_OK" -ForegroundColor Green
