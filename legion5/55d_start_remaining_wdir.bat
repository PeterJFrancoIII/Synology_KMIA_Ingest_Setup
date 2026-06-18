@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "nohup bash /d/KMIA_Process/scripts/55d_process_remaining_wdir.sh > /d/KMIA_Process/logs/processing/retry_remaining_wdir.nohup.log 2>&1 &"
echo Started 55d remaining wdir batch. tail -f D:\KMIA_Process\logs\processing\retry_remaining_wdir.log
