# Sync only kalshi_mirror research artifacts to NAS (writable creds required).
#
# One-time setup: powershell -File D:\KMIA_Process\scripts\43b_setup_nas_smb_write.ps1
# Store password in D:\KMIA_Process\secrets\nas_smb_write_password (never commit).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_sync_research_to_nas.ps1

param(
    [string]$Source = "D:\KMIA_Process\kalshi_mirror\backend\data\research",
    [string]$Dest = "\\192.168.0.193\Data\App_Development\Kalshi\backend\data\research",
    [string]$User = 'Viper117',
    [string]$PasswordFile = 'D:\KMIA_Process\secrets\nas_smb_write_password'
)

$ErrorActionPreference = 'Stop'
$uncRoot = "\\192.168.0.193\Data"

if (-not (Test-Path $Source)) {
    Write-Error "Source missing: $Source"
}

$Password = ''
if (Test-Path $PasswordFile) {
    $Password = (Get-Content -Raw $PasswordFile).Trim()
}
if ($Password) {
    cmd /c "net use $uncRoot /delete /y >nul 2>&1"
    $netArgs = "use `"$uncRoot`" /user:$User $Password"
    cmd /c "net $netArgs"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "net use failed for $uncRoot"
    }
}

Write-Host "robocopy $Source -> $Dest /E /XO"
robocopy $Source $Dest /E /XO /R:2 /W:5 /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) { exit 1 }

$manifest = @{
    synced_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = $Source
    dest = $Dest
    files = @()
}
$policyPath = Join-Path $Dest "trading_policy.json"
if (Test-Path $policyPath) {
    $policy = Get-Content -Raw $policyPath | ConvertFrom-Json
    $manifest.policy_order_mode = $policy.order_mode
    $manifest.policy_generated_at = $policy.generated_at_utc
    if (-not $manifest.policy_generated_at) { $manifest.policy_generated_at = $policy.approved_at_utc }
}
Get-ChildItem -Path $Dest -File | ForEach-Object {
    $manifest.files += $_.Name
}
$manifestPath = Join-Path $Dest "legion5_sync_manifest.json"
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $manifestPath
Write-Host "wrote manifest $manifestPath"
Write-Host "research sync ok"
Write-Host "Verify from Mac: NAS_HOST=MediaServer2 python3 ingest/scripts/verify_nas_research_sync.py"
