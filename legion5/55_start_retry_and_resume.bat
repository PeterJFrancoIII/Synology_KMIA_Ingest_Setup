@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "nohup bash /d/KMIA_Process/scripts/55_retry_and_resume_build.sh > /d/KMIA_Process/logs/processing/retry_and_resume.nohup.log 2>&1 &"
echo Started retry + full BUILD. tail -f D:\KMIA_Process\logs\processing\retry_and_resume.log
