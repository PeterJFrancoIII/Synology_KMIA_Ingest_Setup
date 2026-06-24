# RAM audit - what is actually consuming memory right now.
$ErrorActionPreference = 'Continue'

Write-Host '=== TOTAL RAM ===' -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$free  = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$used  = [math]::Round($total - $free, 1)
Write-Host "Total: ${total} GB | Used: ${used} GB | Free: ${free} GB"

Write-Host ''
Write-Host '=== TOP 30 PROCESSES BY RAM (MB) ===' -ForegroundColor Cyan
Get-Process -ErrorAction SilentlyContinue |
    Sort-Object WorkingSet64 -Descending |
    Select-Object -First 30 Name,
        @{n='RAM_MB';e={[math]::Round($_.WorkingSet64/1MB,1)}},
        @{n='PM_MB';e={[math]::Round($_.PM/1MB,1)}},
        Id |
    Format-Table -AutoSize

Write-Host '=== GROUPED BY PROCESS NAME (MB) ===' -ForegroundColor Cyan
Get-Process -ErrorAction SilentlyContinue |
    Group-Object Name |
    ForEach-Object {
        $sum = ($_.Group | Measure-Object WorkingSet64 -Sum).Sum
        [PSCustomObject]@{
            Name   = $_.Name
            RAM_MB = [math]::Round($sum/1MB, 1)
            Count  = $_.Count
        }
    } |
    Sort-Object RAM_MB -Descending |
    Select-Object -First 25 |
    Format-Table -AutoSize

Write-Host '=== RUNNING NON-MICROSOFT SERVICES ===' -ForegroundColor Cyan
$skip = '^(Adobe|Apple|Bitdefender|Google|Intel|Lenovo|Logitech|Malwarebytes|Microsoft|NVIDIA|Nvidia|Realtek|Steam|Surfshark|Tailscale|Valve|Windows)'
Get-CimInstance Win32_Service |
    Where-Object { $_.State -eq 'Running' -and $_.Name -notmatch $skip -and $_.DisplayName -notmatch $skip } |
    Select-Object Name, DisplayName, State |
    Sort-Object DisplayName |
    Format-Table -AutoSize -Wrap
