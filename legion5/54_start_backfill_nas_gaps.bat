@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "nohup bash /d/KMIA_Process/scripts/54_backfill_nas_gaps.sh > /d/KMIA_Process/logs/ingestion/backfill_gaps.nohup.log 2>&1 &"
echo Started gap backfill+extract on Legion5 D:. tail -f D:\KMIA_Process\logs\ingestion\backfill_gaps.log
