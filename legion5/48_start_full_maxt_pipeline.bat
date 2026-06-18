@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "export KMIA_EXTRACT_WORKERS=8 KMIA_BUILD_CHARTS=1; nohup bash /d/KMIA_Process/scripts/36_process_all_from_nas.sh > /d/KMIA_Process/logs/processing/process_all.nohup.log 2>&1 &"
echo Started full max-t pipeline. Check D:\KMIA_Process\logs\processing\process_all.log
