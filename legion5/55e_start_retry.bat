@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "nohup bash /d/KMIA_Process/scripts/55e_retry_202302_202402.sh > /d/KMIA_Process/logs/processing/retry_202302_202402.nohup.log 2>&1 &"
echo Started 55e retry. tail -f D:\KMIA_Process\logs\processing\retry_202302_202402.log
