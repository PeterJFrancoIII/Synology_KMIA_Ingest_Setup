# Fast month-level GRIB integrity audit via SMB (Z:).
param(
    [string]$Drive = 'Z:',
    [string]$Rel = 'App_Development\KMIA_Ingest'
)

$base = Join-Path $Drive (Join-Path $Rel 'raw\forecast\ndfd_aws')
if (-not (Test-Path $base)) {
    Write-Error "NAS path not found: $base (run 43_setup_nas_smb.ps1)"
}

$years = 2020..2025
$gaps = @()
$rows = @()

foreach ($year in $years) {
    $first = if ($year -eq 2020) { 4 } else { 1 }
    for ($m = $first; $m -le 12; $m++) {
        $mm = '{0:D2}' -f $m
        $maxtPath = Join-Path $base "maxt\$year\$mm"
        $wdirPath = Join-Path $base "wdir\$year\$mm"
        if (-not (Test-Path $maxtPath)) {
            $maxtPath = Join-Path $base "maxt\$year\$m"
        }
        if (-not (Test-Path $wdirPath)) {
            $wdirPath = Join-Path $base "wdir\$year\$m"
        }
        $maxtN = if (Test-Path $maxtPath) { (Get-ChildItem $maxtPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count } else { 0 }
        $wdirN = if (Test-Path $wdirPath) { (Get-ChildItem $wdirPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count } else { 0 }
        $status = 'OK'
        if ($maxtN -eq 0 -and $wdirN -eq 0) { $status = 'MISSING_BOTH' }
        elseif ($maxtN -eq 0) { $status = 'MISSING_MAXT' }
        elseif ($wdirN -eq 0) { $status = 'MISSING_WDIR' }
        if ($status -ne 'OK') { $gaps += "${year}-${mm}: $status" }
        $rows += [PSCustomObject]@{ YearMonth = "${year}-${mm}"; Maxt = $maxtN; Wdir = $wdirN; Status = $status }
        Write-Host ("{0,-10} maxt={1,6} wdir={2,6} {3}" -f "${year}-${mm}", $maxtN, $wdirN, $status)
    }
}

$outDir = 'D:\KMIA_Process\manifest'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$jsonPath = Join-Path $outDir 'archive_integrity_smb_latest.json'
$rows | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 $jsonPath
Write-Host ""
Write-Host "=== Summary: $($rows.Count) months, $($gaps.Count) gaps ==="
$gaps | Select-Object -First 25 | ForEach-Object { Write-Host "  $_" }
if ($gaps.Count -gt 25) { Write-Host "  ... and $($gaps.Count - 25) more" }
Write-Host "Wrote $jsonPath"
