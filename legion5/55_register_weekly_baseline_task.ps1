# Register Legion5 weekly quant-core baseline (Sunday 3:00 AM Eastern).
#
# Usage (Legion5 PowerShell as admin):
#   powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_register_weekly_baseline_task.ps1

param(
    [string]$TaskName = 'KMIA_Weekly_Quant_Core_Baseline',
    [string]$ScriptPath = 'D:\KMIA_Process\scripts\55_quant_core_baseline.sh',
    [string]$GitBash = 'C:\Program Files\Git\bin\bash.exe',
    [string]$DayOfWeek = 'Sunday',
    [string]$Time = '03:00'
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
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "Registered weekly task: $TaskName on $DayOfWeek at $Time"
Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State
