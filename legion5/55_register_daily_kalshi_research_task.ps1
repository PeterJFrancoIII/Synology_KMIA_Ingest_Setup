# Register Legion5 daily Kalshi research task (6:00 AM Eastern).
# NBM fetch, price ingest, NCEI refresh, mirror sync to NAS.
#
# Usage (Legion5 PowerShell as admin):
#   powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_register_daily_kalshi_research_task.ps1

param(
    [string]$TaskName = 'KMIA_Daily_Kalshi_Research',
    [string]$ScriptPath = 'D:\KMIA_Process\scripts\55_daily_kalshi_research.sh',
    [string]$GitBash = 'C:\Program Files\Git\bin\bash.exe',
    [string]$Time = '06:00'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $GitBash)) {
    Write-Error "Git Bash not found: $GitBash"
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script missing: $ScriptPath"
}

$bashArg = "-lc `"bash '$($ScriptPath -replace "'", "''")'`""
$action = New-ScheduledTaskAction -Execute $GitBash -Argument $bashArg -WorkingDirectory 'D:\KMIA_Process'
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "Registered daily task: $TaskName at $Time"
Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State
