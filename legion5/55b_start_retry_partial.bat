@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "nohup bash /d/KMIA_Process/scripts/55b_retry_partial_months.sh > /d/KMIA_Process/logs/processing/retry_partial_months.nohup.log 2>&1 &"
echo Started partial month retries. tail -f D:\KMIA_Process\logs\processing\retry_partial_months.log
