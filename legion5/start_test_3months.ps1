$bash = 'C:\Program Files\Git\bin\bash.exe'
$arg = '-lc "export KMIA_ROOT=/d/KMIA_Process KMIA_PYTHON=/e/Miniforge3/python.exe KMIA_PATH=/e/Miniforge3/Scripts:/e/Miniforge3/Library/bin:/c/Program Files/Amazon/AWSCLIV2 PATH=$KMIA_PATH:$PATH NAS_SSH_KEY=$HOME/.ssh/synology_nas_rsa; bash /d/KMIA_Process/scripts/38_test_3months.sh >> /d/KMIA_Process/logs/processing/test_3months.nohup.log 2>&1"'
Start-Process -FilePath $bash -ArgumentList $arg -WindowStyle Hidden
Write-Host 'Started 3-month test on Legion5'
