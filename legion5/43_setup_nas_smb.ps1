# One-time SMB mount for Legion5 <-> Synology KMIA_Ingest pulls.
# Maps Z: to \\NAS\Data (override with -NasHost / -Share / -Drive).
param(
    [string]$NasHost = '192.168.0.193',
    [string]$Share = 'Data',
    [string]$Drive = 'Z:',
    [string]$User = 'kmia_legion5',
    [string]$Password = '',
    [string]$PasswordFile = 'D:\KMIA_Process\secrets\nas_smb_password'
)

$ErrorActionPreference = 'Stop'
$unc = "\\$NasHost\$Share"
$driveLetter = $Drive.TrimEnd(':')
$kmiaRel = 'App_Development\KMIA_Ingest'

if (-not $Password -and (Test-Path $PasswordFile)) {
    $Password = (Get-Content -Raw $PasswordFile).Trim()
}

Write-Host '=== KMIA NAS SMB setup ===' -ForegroundColor Cyan
Write-Host "UNC: $unc -> $Drive"

$existing = Get-PSDrive -Name $driveLetter -PSProvider FileSystem -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing $Drive mapping..."
    Remove-PSDrive -Name $driveLetter -Force -ErrorAction SilentlyContinue
    & net.exe use $Drive /delete /y 2>$null | Out-Null
}

if ($Password) {
    Write-Host 'Mapping drive with supplied credentials...'
    $sec = ConvertTo-SecureString $Password -AsPlainText -Force
    $cred = New-Object System.Management.Automation.PSCredential($User, $sec)
    New-PSDrive -Name $driveLetter -PSProvider FileSystem -Root $unc -Credential $cred -Persist -Scope Global | Out-Null
} else {
    Write-Host 'Mapping drive (enter NAS password if prompted)...'
    & net.exe use $Drive $unc "/user:$User" '/persistent:yes'
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'net use failed. Check credentials and Synology SMB.'
    }
}

$kmia = Join-Path $Drive $kmiaRel
if (-not (Test-Path $kmia)) {
    Write-Error "KMIA path not found at $kmia - verify share layout on NAS."
}

Write-Host "OK: $kmia" -ForegroundColor Green
Write-Host ''
Write-Host 'Env is automatic via kmia_legion5_env.sh' -ForegroundColor Yellow
Write-Host 'Benchmark: bash /d/KMIA_Process/scripts/43_benchmark_pull_modes.sh' -ForegroundColor Yellow
