# Build and run kmia-arch-ingest on Legion5 (same image as NAS)
$ErrorActionPreference = 'Stop'

$data = 'E:\KMIA_Ingest'
$dockerDir = Join-Path $data 'docker\kmia-arch-ingest'

if (-not (Test-Path (Join-Path $dockerDir 'Dockerfile'))) {
    Write-Host "Missing $dockerDir\Dockerfile — deploy docker context first"
    exit 1
}

# Stop native Git Bash ingest if still running
Get-Process bash -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Stopping bash pid $($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "Building kmia-arch-ingest:latest (first build ~15-30 min)..."
docker build -t kmia-arch-ingest:latest $dockerDir
if ($LASTEXITCODE -ne 0) { exit 1 }

docker rm -f kmia-arch-ingest 2>$null
docker run -d `
  --name kmia-arch-ingest `
  --restart unless-stopped `
  -e TZ=America/New_York `
  -e KMIA_ROOT=/data/KMIA_Ingest `
  -e KMIA_LAT=25.7975 `
  -e KMIA_LON=-80.2872 `
  -e PYTHONUNBUFFERED=1 `
  -v "${data}:/data/KMIA_Ingest" `
  -w /data/KMIA_Ingest `
  --memory 10g `
  kmia-arch-ingest:latest sleep infinity

Start-Sleep -Seconds 3
docker exec kmia-arch-ingest bash -lc 'export PATH=/opt/miniforge3/bin:/opt/kmia-venv/bin:/usr/local/bin:$PATH; wgrib2 -version 2>&1 | head -1; /opt/kmia-venv/bin/python3 -c "import pandas; print(pandas.__version__)"'

# Copy latest scripts into mounted volume if setup_repo exists
$scripts = Join-Path $data 'scripts'
if (Test-Path $scripts) {
    docker exec kmia-arch-ingest bash -lc 'ls -la /data/KMIA_Ingest/scripts/27_nas_year_pipeline.sh 2>/dev/null || ls /data/KMIA_Ingest/scripts/ | head -5'
}

Write-Host "Starting 2020 year pipeline in container..."
docker exec -d kmia-arch-ingest bash -lc 'nohup bash /data/KMIA_Ingest/scripts/27_nas_year_pipeline.sh 2020 > /data/KMIA_Ingest/logs/ingestion/legion5_container_year_2020.nohup.log 2>&1 &'
Start-Sleep -Seconds 6
docker exec kmia-arch-ingest bash -lc 'tail -20 /data/KMIA_Ingest/logs/ingestion/nas_year_2020_pipeline.log 2>/dev/null || tail -15 /data/KMIA_Ingest/logs/ingestion/legion5_container_year_2020.nohup.log'

Write-Host "CONTAINER_INGEST_STARTED" -ForegroundColor Green
