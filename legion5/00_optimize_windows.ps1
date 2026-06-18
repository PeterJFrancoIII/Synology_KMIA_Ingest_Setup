# Legion5 safe cleanup and WSL tuning (AV-friendly).
# Run as admin: powershell -ExecutionPolicy Bypass -File E:\KMIA_Setup\00_optimize_windows.ps1
#
# This script intentionally avoids bulk uninstalls, registry policy edits, and
# service shutdowns - those patterns trigger Bitdefender and similar AV.
#
# For bloatware removal, use Windows Settings > Apps manually, then re-run this.
param(
    [switch]$InventoryOnly
)

$ErrorActionPreference = 'Continue'
$logDir = 'E:\KMIA_Setup\logs'
$logFile = Join-Path $logDir ("optimize_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Color = 'White')
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    Add-Content -Path $logFile -Value $line
    Write-Host $line -ForegroundColor $Color
}

Write-Log '=== Legion5 optimize (safe mode) ===' 'Cyan'

# --- Inventory only (no changes) ---
Write-Log 'Third-party installed programs:' 'Cyan'
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -and $_.Publisher -notmatch 'Microsoft' } |
    Select-Object DisplayName, Publisher, DisplayVersion |
    Sort-Object DisplayName |
    ForEach-Object {
        Write-Log ("  {0} v{1} - {2}" -f $_.DisplayName, $_.DisplayVersion, $_.Publisher)
    }

Write-Log 'Startup programs:' 'Cyan'
Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue |
    Sort-Object Name |
    ForEach-Object { Write-Log ("  {0} -> {1}" -f $_.Name, $_.Command) }

if ($InventoryOnly) {
    Write-Log 'InventoryOnly - no changes applied.' 'Magenta'
    Write-Log "Log saved to $logFile" 'Green'
    exit 0
}

# --- Disk hygiene (safe) ---
Write-Log 'Cleaning temp files and recycle bin...' 'Cyan'
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# --- Ensure data dirs on E: ---
$setup = 'E:\KMIA_Setup'
$data  = 'E:\KMIA_Ingest'
$wslRoot = 'E:\WSL'
foreach ($d in @($setup, $data, $wslRoot)) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Log "Created $d"
    }
}

# --- WSL2 resource limits (leave ~4 GB for Windows on 16 GB machine) ---
$wslConfig = @"
[wsl2]
memory=12GB
processors=10
swap=8GB
localhostForwarding=true
"@
$wslConfigPath = Join-Path $env:USERPROFILE '.wslconfig'
Set-Content -Path $wslConfigPath -Value $wslConfig -Encoding ASCII
Write-Log "Wrote $wslConfigPath"

# --- Power plan: high performance, no sleep on AC ---
try {
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c | Out-Null
    powercfg /change standby-timeout-ac 0 | Out-Null
    powercfg /change hibernate-timeout-ac 0 | Out-Null
    powercfg /change monitor-timeout-ac 0 | Out-Null
    Write-Log 'Power plan: High performance, sleep disabled on AC'
} catch {
    Write-Log 'Power plan tweak skipped'
}

Write-Log 'Disk free (GB):' 'Cyan'
Get-PSDrive C, D, E -ErrorAction SilentlyContinue | Select-Object Name,
    @{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}},
    @{n='UsedGB';e={[math]::Round($_.Used/1GB,1)}} |
    Format-Table -AutoSize |
    Out-String |
    ForEach-Object { $_.TrimEnd() -split "`n" | ForEach-Object { Write-Log $_ } }

Write-Log "Log saved to $logFile" 'Green'
Write-Log 'Done. Remove bloatware manually via Settings > Apps (see chat for list).' 'Green'
