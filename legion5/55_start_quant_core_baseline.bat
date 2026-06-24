@echo off
REM Legion5: Quant Core baseline backtest (Git Bash). NO REAL TRADING.
set LOG=D:\KMIA_Process\logs\research\quant_core_baseline_nohup.log
if not exist D:\KMIA_Process\logs\research mkdir D:\KMIA_Process\logs\research
"C:\Program Files\Git\bin\bash.exe" -lc "bash /d/KMIA_Process/scripts/55_quant_core_baseline.sh" >> "%LOG%" 2>&1
echo Exit code: %ERRORLEVEL%
echo Log: %LOG%
