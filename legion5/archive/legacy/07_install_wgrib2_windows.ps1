# Install NOAA prebuilt wgrib2 for Windows (v3.1.1) into E:\Miniforge3\Scripts
$ErrorActionPreference = 'Stop'
$dest = 'E:\Miniforge3\Scripts'
$tmp = Join-Path $env:TEMP 'wgrib2_win'
$base = 'https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/Windows10/v3.1.1'
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

$files = @('wgrib2.exe','cygwin1.dll','cyggcc_s-seh-1.dll','cyggfortran-5.dll','cygquadmath-0.dll','cygssp-0.dll','cyggomp-1.dll','cygz.dll')
foreach ($f in $files) {
    $url = "$base/$f"
    Write-Host "Downloading $f"
    try {
        Invoke-WebRequest -Uri $url -OutFile (Join-Path $tmp $f) -UseBasicParsing
    } catch {
        Write-Host "Skip optional $f"
    }
}

Get-ChildItem $tmp -Filter '*.dll' | Copy-Item -Destination $dest -Force
Get-ChildItem $tmp -Filter 'wgrib2.exe' | Copy-Item -Destination $dest -Force
& "$dest\wgrib2.exe" -version 2>&1 | Select-Object -First 1
Write-Host "WGRIB2_WINDOWS_OK"
