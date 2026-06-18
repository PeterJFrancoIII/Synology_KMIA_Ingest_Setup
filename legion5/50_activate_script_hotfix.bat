@echo off
cd /d D:\KMIA_Process\scripts
if exist nas_pull_helpers.sh.new move /y nas_pull_helpers.sh.new nas_pull_helpers.sh
if exist 35_process_month_from_nas.sh.new move /y 35_process_month_from_nas.sh.new 35_process_month_from_nas.sh
if exist 36_process_all_from_nas.sh.new (
  echo Note: 36_process_all swap deferred until current pipeline run ends.
)
echo Hotfix scripts activated.
