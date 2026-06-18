# Disable non-essential startup entries on Legion5 ingest box.
$remove = @(
    'Steam',
    'Surfshark',
    'Jabra Direct',
    'LGHUB',
    'Adobe Acrobat Synchronizer',
    'MicrosoftEdgeAutoLaunch_DACE14515307BE0E88180313DB784574',
    'Lenovo Fundamental USB Keyboard',
    'ISUSPM',
    'nefarius_HidHide_Updater'
)
foreach ($name in $remove) {
    Write-Host "Removing startup: $name"
    Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $name -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $name -ErrorAction SilentlyContinue
}
Write-Host 'Startup cleanup done.'
