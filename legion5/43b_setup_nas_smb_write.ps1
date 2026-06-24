# Writable SMB mount for Legion5 -> NAS pushes (GRIB consolidation, kalshi_mirror sync).
# Maps Y: to \\NAS\Data with write-capable credentials (default: Viper117).
#
# One-time: store password in D:\KMIA_Process\secrets\nas_smb_write_password
# (never commit secrets to git).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43b_setup_nas_smb_write.ps1

param(
    [string]$NasHost = '192.168.0.193',
    [string]$Share = 'Data',
    [string]$Drive = 'Y:',
    [string]$User = 'Viper117',
    [string]$Password = '',
    [string]$PasswordFile = 'D:\KMIA_Process\secrets\nas_smb_write_password'
)

$ErrorActionPreference = 'Stop'
$unc = "\\$NasHost\$Share"
$driveLetter = $Drive.TrimEnd(':')
$kmiaRel = 'App_Development\KMIA_Ingest'

if (-not $Password -and (Test-Path $PasswordFile)) {
    $Password = (Get-Content -Raw $PasswordFile).Trim()
}

Write-Host '=== KMIA NAS SMB WRITE setup ===' -ForegroundColor Cyan
Write-Host "UNC: $unc -> $Drive (user: $User)"

cmd /c "net use $Drive /delete /y >nul 2>&1"
$existing = Get-PSDrive -Name $driveLetter -PSProvider FileSystem -ErrorAction SilentlyContinue
if ($existing) {
    Remove-PSDrive -Name $driveLetter -Force -ErrorAction SilentlyContinue
}

if (-not $Password) {
    Write-Error "No password. Create $PasswordFile or pass -Password."
}

$sec = ConvertTo-SecureString $Password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($User, $sec)
New-PSDrive -Name $driveLetter -PSProvider FileSystem -Root $unc -Credential $cred -Persist -Scope Global | Out-Null

$kmia = Join-Path $Drive $kmiaRel
if (-not (Test-Path $kmia)) {
    Write-Error "KMIA path not found at $kmia"
}

# Verify write access
$probe = Join-Path $kmia 'raw\forecast\ndfd_aws\_smb_write_probe'
New-Item -ItemType File -Path $probe -Force | Out-Null
Remove-Item $probe -Force

Write-Host "OK: writable $kmia" -ForegroundColor Green
