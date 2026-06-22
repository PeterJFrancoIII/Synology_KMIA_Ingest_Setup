@echo off
setlocal
set LOG=D:\KMIA_Process\logs\52_ndfd_kalshi_202604-06.log
if not exist D:\KMIA_Process\logs mkdir D:\KMIA_Process\logs
set KMIA_FORCE_REEXTRACT=1
set SKIP_STORAGE_CHECK=1
set KMIA_ROOT=D:\KMIA_Process
set SCRIPTS=D:\KMIA_Process\scripts
set KMIA_EXTRACT_WORKERS=10
set KMIA_AWS_DAY_PARALLEL=6
"C:\Program Files\Git\bin\bash.exe" -lc "export PYTHONPATH=/d/KMIA_Process/scripts KMIA_FORCE_REEXTRACT=1 SKIP_STORAGE_CHECK=1 KMIA_EXTRACT_WORKERS=10 KMIA_AWS_DAY_PARALLEL=6 KMIA_ROOT=/d/KMIA_Process SCRIPTS=/d/KMIA_Process/scripts; bash /d/KMIA_Process/scripts/52_kalshi_ndfd_anchor_backfill.sh 2026 04 2026 06" >> "%LOG%" 2>&1
