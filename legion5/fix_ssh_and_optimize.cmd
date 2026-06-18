@echo off
REM Run on Legion5 — restores SSH + Tailscale (disables Surfshark conflict).
powershell -NoProfile -ExecutionPolicy Bypass -File E:\KMIA_Setup\fix_tailscale_network.ps1
pause
