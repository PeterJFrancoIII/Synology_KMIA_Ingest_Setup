# Stop listed RAM hogs from auto-starting. Does not uninstall games or ingest tools.
$ErrorActionPreference = 'Continue'

function Write-Step($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }

function Disable-AutoService {
    param([string[]]$Names)
    foreach ($name in $Names) {
        $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
        if (-not $svc) {
            Write-Host "    skip service (not found): $name" -ForegroundColor DarkGray
            continue
        }
        Write-Host "    disable service: $($svc.DisplayName) [$name]"
        if ($svc.Status -eq 'Running') {
            Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
        }
        Set-Service -Name $name -StartupType Disabled -ErrorAction SilentlyContinue
    }
}

function Remove-RunKey {
    param([string[]]$Names)
    $paths = @(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
    )
    foreach ($path in $paths) {
        foreach ($name in $Names) {
            if (Get-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue) {
                Write-Host "    remove Run key: $name"
                Remove-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Step 'Intel Driver and Support Assistant - uninstall + stop services'
Disable-AutoService @('DSAService', 'SurSvc')
Remove-RunKey @('DSATray', 'Intel Driver & Support Assistant', 'Intel Driver and Support Assistant')
winget uninstall --name 'Intel Driver and Support Assistant' --silent --accept-source-agreements --disable-interactivity 2>&1 | Out-Host
winget uninstall --name 'Intelr Driver & Support Assistant' --silent --accept-source-agreements --disable-interactivity 2>&1 | Out-Host
Get-Process DSATray, DSAService -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Step 'VMware background services'
Disable-AutoService @('VMAuthdService', 'VMnetDHCP', 'VMUSBArbService', 'VMware NAT Service')

Write-Step 'WD Drive Manager'
Disable-AutoService @('WDDriveService')

Write-Step 'Bonjour'
Disable-AutoService @('Bonjour Service')

Write-Step 'PunkBuster'
Disable-AutoService @('PnkBstrA', 'PnkBstrB')

Write-Step 'HidHide Watchdog'
Disable-AutoService @('HidHideWatchdog.exe')

Write-Step 'Logitech G HUB Updater (keep G HUB app, stop background updater)'
Disable-AutoService @('LGHUBUpdaterService')
Remove-RunKey @('LGHUB', 'Logitech G HUB')

Write-Step 'Windows Widgets + WebView2 panel'
# TaskbarDa=0 hides Widgets button/panel (stops most msedgewebview2 instances)
New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' -Name 'TaskbarDa' -Value 0 -Type DWord
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Dsh' -Name 'AllowNewsAndInterests' -Value 0 -Type DWord
Get-Process Widgets -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Step 'Phone Link / PhoneExperienceHost'
Disable-AutoService @('PhoneSvc')
# Disable Phone Link companion on Start
$companion = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Start\Companions'
if (Test-Path $companion) {
    Get-ChildItem $companion -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.PSChildName -match 'YourPhone|Phone') {
            Write-Host "    disable companion: $($_.PSChildName)"
            Set-ItemProperty -Path $_.PSPath -Name 'IsEnabled' -Value 0 -ErrorAction SilentlyContinue
        }
    }
}
Get-AppxPackage -Name 'Microsoft.YourPhone*' -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "    remove provisioned Phone Link for current user: $($_.Name)"
    Remove-AppxPackage -Package $_.PackageFullName -ErrorAction SilentlyContinue
}
Get-Process PhoneExperienceHost -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Step 'Kill currently running targets (will stay off until reboot for some)'
$procs = @('DSATray', 'Widgets', 'PhoneExperienceHost')
foreach ($p in $procs) {
    Get-Process $p -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "    stop process: $($_.Name) ($([math]::Round($_.WorkingSet64/1MB,1)) MB)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Step 'Done. Reboot Legion5 once to fully clear WebView2/Phone shell processes.'
Write-Host 'Preserved: Bitdefender, Tailscale, OpenSSH, NVIDIA, ingest tools.' -ForegroundColor Green
