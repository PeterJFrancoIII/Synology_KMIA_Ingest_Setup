# Bootstrap Legion5 as NAS processor on D: (keeps E: free)
$ErrorActionPreference = 'Stop'

$proc = 'D:\KMIA_Process'
$setup = 'E:\KMIA_Setup'
$mf = 'E:\Miniforge3'

foreach ($d in @($proc, "$proc\scripts", "$proc\logs\processing", "$proc\processed\points\station=KMIA", "$proc\analysis")) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# Toolchain on E: (already installed)
if (-not (Test-Path "$mf\python.exe")) {
    Write-Error "Miniforge not found at $mf — run 04_bootstrap_windows_native.ps1 first"
}

# Copy scripts from setup repo if present
if (Test-Path "$setup\ingest\scripts") {
    Copy-Item -Path "$setup\ingest\scripts\*" -Destination "$proc\scripts\" -Force
}
if (Test-Path "$setup\legion5\35_process_month_from_nas.sh") {
    Copy-Item -Path "$setup\legion5\35_process_month_from_nas.sh", "$setup\legion5\36_process_all_from_nas.sh", "$setup\legion5\analyze_kmia_forecast_accuracy.py" -Destination "$proc\scripts\" -Force
}

$launcher = @'
#!/usr/bin/env bash
set -euo pipefail
export KMIA_ROOT="/d/KMIA_Process"
export KMIA_PYTHON="/e/Miniforge3/python.exe"
export KMIA_PATH="/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2"
export NAS_SSH="Viper117@192.168.0.193"
export NAS_SSH_PORT="23921"
export PATH="$KMIA_PATH:$PATH"
nohup bash /d/KMIA_Process/scripts/36_process_all_from_nas.sh \
  > /d/KMIA_Process/logs/processing/process_all.nohup.log 2>&1 &
echo "Processor started. tail -f /d/KMIA_Process/logs/processing/process_all.log"
'@
Set-Content -Path "$proc\start_processor.sh" -Value $launcher -Encoding UTF8NoBOM

Write-Host "Legion5 processor ready at D:\KMIA_Process" -ForegroundColor Green
Write-Host "Run in Git Bash: bash /d/KMIA_Process/start_processor.sh"
