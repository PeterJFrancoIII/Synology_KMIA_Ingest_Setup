# Install WSL2 + Ubuntu 24.04, import to E:\WSL when possible.
# Run as admin. May require one reboot if WSL feature was never enabled.
$ErrorActionPreference = 'Continue'

Write-Host "=== WSL install ===" -ForegroundColor Cyan

$distro = 'Ubuntu-24.04'
$wslRoot = 'E:\WSL'
$importName = 'Ubuntu'
$importDir = Join-Path $wslRoot 'Ubuntu'

if (-not (Test-Path $wslRoot)) { New-Item -ItemType Directory -Path $wslRoot | Out-Null }

# Enable WSL + VM platform
wsl --status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Enabling WSL (first-time)..."
    wsl --install --no-distribution
    Write-Host "REBOOT REQUIRED: restart Legion5, then re-run 01_install_wsl.ps1"
    exit 10
}

# List existing
$listed = wsl -l -v 2>$null
Write-Host $listed

if ($listed -match $importName) {
    Write-Host "WSL distro '$importName' already present"
    wsl -d $importName -- bash -lc "echo WSL_OK && uname -a"
    exit 0
}

Write-Host "Installing $distro..."
wsl --install -d $distro --no-launch
Start-Sleep -Seconds 5

# Move to E: if default install landed on C:
if ($listed -notmatch $importName) {
    $listed2 = wsl -l -v 2>$null
    if ($listed2 -match 'Ubuntu') {
        Write-Host "Exporting Ubuntu to E:\WSL..."
        $tar = Join-Path $wslRoot 'ubuntu-export.tar'
        wsl --export Ubuntu $tar
        wsl --unregister Ubuntu
        if (-not (Test-Path $importDir)) { New-Item -ItemType Directory -Path $importDir | Out-Null }
        wsl --import $importName $importDir $tar --version 2
        Remove-Item $tar -Force -ErrorAction SilentlyContinue
    }
}

# First-run user setup (default user on imported distros is root)
wsl -d $importName -- bash -lc "id; apt-get update -qq && apt-get install -y sudo"
$user = $env:USERNAME
wsl -d $importName -- bash -lc "id $user 2>/dev/null || useradd -m -s /bin/bash $user; usermod -aG sudo $user; echo '$user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-$user; chmod 440 /etc/sudoers.d/90-$user"

Write-Host "WSL ready. Default distro:" -ForegroundColor Green
wsl -l -v
