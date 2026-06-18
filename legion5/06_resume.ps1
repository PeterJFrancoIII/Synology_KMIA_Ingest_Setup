# Resume Legion5 setup after reboot or SSH drop.
$ErrorActionPreference = 'Continue'
$setup = 'E:\KMIA_Setup'
$data = 'E:\KMIA_Ingest'
$mf = 'E:\Miniforge3'

foreach ($d in @($data, "$data\scripts", "$data\logs\ingestion", "$data\processed\points\station=KMIA")) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Copy-Item -Path "$setup\ingest\scripts\*" -Destination "$data\scripts\" -Force -ErrorAction SilentlyContinue
if (Test-Path "$setup\03_legion5_year_pipeline.sh") {
    Copy-Item -Path "$setup\03_legion5_year_pipeline.sh" -Destination "$data\scripts\" -Force -ErrorAction SilentlyContinue
}

$wslList = wsl -l -v 2>&1 | Out-String
if ($LASTEXITCODE -eq 0 -and $wslList -match 'Ubuntu') {
    Write-Host "WSL Ubuntu found" -ForegroundColor Cyan
    wsl -d Ubuntu -- bash -lc 'chmod +x /mnt/e/KMIA_Setup/02_bootstrap_kmia.sh /mnt/e/KMIA_Setup/03_legion5_year_pipeline.sh; bash /mnt/e/KMIA_Setup/02_bootstrap_kmia.sh'
    wsl -d Ubuntu -- bash -lc 'pgrep -f 03_legion5_year_pipeline >/dev/null || nohup bash /mnt/e/KMIA_Setup/03_legion5_year_pipeline.sh 2020 > /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020.nohup.log 2>&1 &'
    Start-Sleep -Seconds 5
    wsl -d Ubuntu -- bash -lc 'tail -20 /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020_pipeline.log 2>/dev/null || tail -10 /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020.nohup.log'
    Write-Host "LEGION5_WSL_INGEST_STARTED" -ForegroundColor Green
    exit 0
}

Write-Host "WSL not ready - native Miniforge + Git Bash" -ForegroundColor Yellow
if (-not (Test-Path "$mf\Scripts\conda.exe")) {
    Write-Host "Miniforge missing"
    exit 1
}

$conda = "$mf\Scripts\conda.exe"
& $conda install -y -c conda-forge python=3.11 pandas matplotlib requests tqdm 2>&1 | Out-Host
& $conda install -y -c conda-forge wgrib2 2>&1 | Out-Host

$bash = 'C:\Program Files\Git\bin\bash.exe'
if (-not (Test-Path $bash)) { Write-Host "Git Bash missing"; exit 1 }

& $bash -lc 'bash /e/KMIA_Ingest/scripts/start_ingest_gitbash.sh 2>/dev/null || bash /e/KMIA_Setup/start_ingest_gitbash.sh'
Write-Host "LEGION5_NATIVE_INGEST_STARTED" -ForegroundColor Green
