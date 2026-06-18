# One-shot Legion5 setup from Mac: powershell -ExecutionPolicy Bypass -File E:\KMIA_Setup\run_setup.ps1
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$here\00_optimize_windows.ps1"
$wslRc = 0
& "$here\01_install_wsl.ps1"
$wslRc = $LASTEXITCODE
if ($wslRc -eq 10) { exit 10 }

Write-Host "Running WSL bootstrap..."
wsl -d Ubuntu -- bash -lc "chmod +x /mnt/e/KMIA_Setup/02_bootstrap_kmia.sh /mnt/e/KMIA_Setup/03_legion5_year_pipeline.sh && bash /mnt/e/KMIA_Setup/02_bootstrap_kmia.sh"

Write-Host "Starting 2020 year ingest in background..."
wsl -d Ubuntu -- bash -lc "nohup bash /mnt/e/KMIA_Setup/03_legion5_year_pipeline.sh 2020 > /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020.nohup.log 2>&1 &"
Start-Sleep -Seconds 5
wsl -d Ubuntu -- bash -lc "tail -20 /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020_pipeline.log 2>/dev/null || tail -10 /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020.nohup.log"

Write-Host "LEGION5_SETUP_COMPLETE" -ForegroundColor Green
