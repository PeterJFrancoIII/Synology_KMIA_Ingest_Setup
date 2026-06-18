# Remove safe bloat via winget one at a time.
$ErrorActionPreference = 'Continue'
$apps = @(
    'Surfshark',
    'Intel Driver and Support Assistant',
    'Intelr Driver & Support Assistant',
    'Bonjour',
    'Bitdefender VPN',
    'Chrome Remote Desktop Host'
)
foreach ($app in $apps) {
    Write-Host "--- Uninstall: $app ---"
    winget uninstall --name $app --silent --accept-source-agreements --disable-interactivity 2>&1
}
Write-Host 'Winget debloat pass done.'
