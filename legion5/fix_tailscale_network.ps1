# Restore Legion5 Tailscale connectivity (run as admin on Legion5 or via SSH).
# Surfshark VPN breaks Tailscale DNS/coordination — disable it for the ingest box.
$ErrorActionPreference = 'Continue'

Write-Host '=== Legion5 Tailscale fix ===' -ForegroundColor Cyan

Get-Process -Name 'Surfshark*' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Service -Name 'Surfshark*' -ErrorAction SilentlyContinue | Stop-Service -Force -ErrorAction SilentlyContinue
Disable-NetAdapter -Name 'SurfsharkWireGuard' -Confirm:$false -ErrorAction SilentlyContinue

Start-Service sshd -ErrorAction SilentlyContinue
Set-Service sshd -StartupType Automatic -ErrorAction SilentlyContinue

New-NetFirewallRule -DisplayName 'OpenSSH-Server-In-TCP' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'Tailscale-In-UDP-41641' -Direction Inbound -Protocol UDP -LocalPort 41641 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'Tailscale-Out-UDP-41641' -Direction Outbound -Protocol UDP -LocalPort 41641 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'RDP-Tailscale-In' -Direction Inbound -Protocol TCP -LocalPort 3389 -InterfaceAlias 'Tailscale*' -Action Allow -ErrorAction SilentlyContinue | Out-Null

Set-Service TermService -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service TermService -ErrorAction SilentlyContinue
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0 -ErrorAction SilentlyContinue
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue

# RDP Shortpath UDP listener (port 3390) + classic RDP UDP
$tsPolicy = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services'
if (-not (Test-Path $tsPolicy)) { New-Item -Path $tsPolicy -Force | Out-Null }
New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations' -Name fUseUdpPortRedirector -Value 1 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations' -Name UdpPortNumber -Value 3390 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
New-ItemProperty -Path $tsPolicy -Name fUseUdpPortRedirector -Value 1 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
New-ItemProperty -Path $tsPolicy -Name SelectTransport -Value 2 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'RDP-Shortpath-UDP-3390-In' -Direction Inbound -Protocol UDP -LocalPort 3390 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'RDP-Shortpath-Ephemeral-UDP-In' -Direction Inbound -Protocol UDP -LocalPort 49152-65535 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null

Restart-Service Tailscale -Force -ErrorAction SilentlyContinue
Start-Sleep 8

$ts = 'C:\Program Files\Tailscale\tailscale.exe'
& $ts status 2>&1
Write-Host
Write-Host 'If status shows Logged out, open this link on any device signed into your Tailscale account:' -ForegroundColor Yellow
& $ts login --timeout=15s --unattended=true 2>&1
