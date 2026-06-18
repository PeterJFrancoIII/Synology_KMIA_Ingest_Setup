@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File E:\KMIA_Setup\05_post_reboot_wsl.ps1 >> E:\KMIA_Setup\post_reboot.log 2>&1
