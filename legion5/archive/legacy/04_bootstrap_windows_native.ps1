# Native Windows bootstrap (no WSL) — Git Bash + Miniforge on E:
$ErrorActionPreference = 'Stop'

$data = 'E:\KMIA_Ingest'
$setup = 'E:\KMIA_Setup'
$mf = 'E:\Miniforge3'
$mfSh = 'https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe'

foreach ($d in @($data, $setup, "$data\scripts", "$data\logs\ingestion", "$data\processed\points\station=KMIA")) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# AWS CLI (silent MSI)
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Installing AWS CLI..."
    $msi = Join-Path $env:TEMP 'AWSCLIV2.msi'
    Invoke-WebRequest -Uri 'https://awscli.amazonaws.com/AWSCLIV2.msi' -OutFile $msi
    Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qn" -Wait
}

# Miniforge
if (-not (Test-Path "$mf\Scripts\conda.exe")) {
    Write-Host "Installing Miniforge to E:\Miniforge3..."
    $exe = Join-Path $env:TEMP 'Miniforge3.exe'
    Invoke-WebRequest -Uri $mfSh -OutFile $exe
    Start-Process $exe -ArgumentList '/InstallationType=JustMe /RegisterPython=0 /S /D=E:\Miniforge3' -Wait
}

$conda = 'E:\Miniforge3\Scripts\conda.exe'
& $conda install -y -c conda-forge python=3.11 pandas matplotlib requests tqdm 2>&1 | Out-Host
& $conda install -y -c conda-forge wgrib2 2>&1 | Out-Host

# Copy scripts
Copy-Item -Path "$setup\ingest\scripts\*" -Destination "$data\scripts\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "$setup\03_legion5_year_pipeline.sh" -Destination "$data\scripts\" -Force

# Git Bash launcher
$launcher = @'
#!/usr/bin/env bash
set -euo pipefail
export KMIA_ROOT="/e/KMIA_Ingest"
export KMIA_PYTHON="/e/Miniforge3/python.exe"
export KMIA_PATH="/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2"
export PATH="$KMIA_PATH:$PATH"
ROOT="$KMIA_ROOT"
mkdir -p "$ROOT/logs/ingestion" "$ROOT/processed/points/station=KMIA/monthly/2020"
cd "$ROOT"
echo "=== ISD smoke ==="
ISD_YEAR=2020 KMIA_ROOT="$KMIA_ROOT" KMIA_PYTHON="$KMIA_PYTHON" bash "$ROOT/scripts/11_isd_smoke_kmia.sh"
echo "=== Starting year pipeline ==="
nohup bash "$ROOT/scripts/03_legion5_year_pipeline.sh" 2020 > "$ROOT/logs/ingestion/legion5_year_2020.nohup.log" 2>&1 &
sleep 4
tail -20 "$ROOT/logs/ingestion/legion5_year_2020_pipeline.log" 2>/dev/null || tail -10 "$ROOT/logs/ingestion/legion5_year_2020.nohup.log"
'@
Set-Content -Path "$setup\start_ingest_gitbash.sh" -Value $launcher -Encoding UTF8NoBOM

Write-Host "Native toolchain ready. wgrib2:" -ForegroundColor Green
& 'E:\Miniforge3\Scripts\wgrib2.exe' -version 2>&1 | Select-Object -First 1
& 'E:\Miniforge3\python.exe' -c "import pandas; print('pandas', pandas.__version__)"
