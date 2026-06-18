@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "export KMIA_EXTRACT_WORKERS=8 KMIA_BUILD_CHARTS=1; nohup bash /d/KMIA_Process/scripts/36b_resume_build.sh > /d/KMIA_Process/logs/processing/resume_build.nohup.log 2>&1 &"
echo Started resume BUILD (2022-2025 Mar-Dec). tail -f D:\KMIA_Process\logs\processing\process_all.log
