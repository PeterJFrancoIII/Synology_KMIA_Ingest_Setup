# After reboot: start Docker Desktop, build/run kmia-arch-ingest, begin ingest
$ErrorActionPreference = 'Continue'
$here = 'E:\KMIA_Setup'
$log = 'E:\KMIA_Setup\post_reboot_container.log'
"=== $(Get-Date) post-reboot container start ===" | Out-File $log -Append

# One-shot: remove startup shortcut after first run
$startup = [Environment]::GetFolderPath('Startup')
Remove-Item (Join-Path $startup 'kmia_container_resume.cmd') -Force -ErrorAction SilentlyContinue

wsl --update 2>&1 | Out-File $log -Append
wsl --install -d Ubuntu-24.04 --no-launch 2>&1 | Out-File $log -Append
wsl -l -v 2>&1 | Out-File $log -Append

if (-not (Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue)) {
    Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
}

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    "wait docker $i" | Out-File $log -Append
    Start-Sleep -Seconds 10
}
if (-not $ready) {
    "Docker daemon not ready" | Out-File $log -Append
    exit 11
}

& "$here\09_run_kmia_container.ps1" 2>&1 | Out-File $log -Append
"exit $LASTEXITCODE" | Out-File $log -Append
