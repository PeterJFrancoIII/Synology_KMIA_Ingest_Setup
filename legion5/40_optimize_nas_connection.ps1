# Optimize Legion5 <-> MediaServer2 connection for KMIA processing.
$ErrorActionPreference = 'Stop'
$repo = 'E:\KMIA_Setup'
$configSrc = Join-Path $repo 'legion5\config\nas_ssh_config'
$sshDir = Join-Path $env:USERPROFILE '.ssh'
$controlDir = Join-Path $sshDir 'controlmasters'

foreach ($d in @($sshDir, $controlDir, 'D:\KMIA_Process\scripts')) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# Deploy SSH config block (idempotent append)
$configDest = Join-Path $sshDir 'config'
$marker = '# KMIA NAS connection (Legion5)'
if (Test-Path $configSrc) {
    $existing = if (Test-Path $configDest) { Get-Content $configDest -Raw } else { '' }
    if ($existing -notmatch [regex]::Escape($marker)) {
        Add-Content -Path $configDest -Value "`n$marker"
        Get-Content $configSrc | Add-Content -Path $configDest
        Write-Host "Appended nas-local SSH config to $configDest"
    } else {
        Write-Host "SSH config already contains NAS block"
    }
}

# Copy helpers
Copy-Item -Path (Join-Path $repo 'legion5\kmia_legion5_env.sh') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $repo 'legion5\41_benchmark_nas_connection.sh') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $repo 'legion5\43_benchmark_pull_modes.sh') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $repo 'legion5\43_setup_nas_smb.ps1') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $repo 'ingest\scripts\22_batch_extract_local_gribs.py') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $repo 'legion5\35_process_month_from_nas.sh') -Destination 'D:\KMIA_Process\scripts\' -Force -ErrorAction SilentlyContinue

# Connectivity test
Write-Host "`n=== Connectivity ===" -ForegroundColor Cyan
ping -n 2 192.168.0.193
$gitBash = 'C:\Program Files\Git\bin\bash.exe'
& $gitBash -lc "ssh -o ConnectTimeout=8 nas-local 'echo NAS_OK; df -h /volume2 | tail -1'"

Write-Host "`n=== Env for processing (add to Git Bash profile) ===" -ForegroundColor Green
@'
export NAS_SSH_HOST=nas-local
export NAS_TAR_COMPRESS=no
export NAS_ROOT=/volume2/Data/App_Development/KMIA_Ingest
export NAS_SMB_DRIVE=Z:
export KMIA_EXTRACT_WORKERS=4
# Optional faster LAN pulls (after 43_setup_nas_smb.ps1):
# export NAS_PULL_MODE=smb
'@ | Write-Host

Write-Host "`nSMB setup (one-time, faster pulls): powershell -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1" -ForegroundColor Yellow
Write-Host "Run pull benchmark: bash /d/KMIA_Process/scripts/43_benchmark_pull_modes.sh" -ForegroundColor Yellow
Write-Host "Run tar benchmark: bash /d/KMIA_Process/scripts/41_benchmark_nas_connection.sh" -ForegroundColor Yellow
