@echo off
REM Legion5: prep mirror artifacts + NAS sync (Step 1 of quant core follow-up)
set LOG=D:\KMIA_Process\logs\research\quant_core_sync_nohup.log
if not exist D:\KMIA_Process\logs\research mkdir D:\KMIA_Process\logs\research
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43b_setup_nas_smb_write.ps1 >> "%LOG%" 2>&1
"C:\Program Files\Git\bin\bash.exe" -lc "bash /d/KMIA_Process/scripts/55_prep_mirror_sync.sh" >> "%LOG%" 2>&1
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_sync_research_to_nas.ps1 >> "%LOG%" 2>&1
echo Exit: %ERRORLEVEL% Log: %LOG%
