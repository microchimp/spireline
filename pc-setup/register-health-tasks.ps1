<#
.SYNOPSIS
  Register (or remove) the two scheduled tasks of the unattended machine: "Spireline health" (the daily check) and
  "Spireline gym daemon" (starts the practice loop at logon).

.DESCRIPTION
  Both run tools\health_check.py of the Spireline repo with the repo's venv pythonw.exe (no console window), for the CURRENT user
  only: logon type Interactive, run level Limited, so they run only while that user is logged on and no password is stored (the
  same as the "Spireline fix lab" task).

  "Spireline health": every day at 21:00 local time (10:00Z at UTC+11), StartWhenAvailable (a missed run starts when the PC is
  next on), at most one hour, one instance. It reads the machine's files, restarts the practice loop when it is down (by running
  the second task), writes status\latest.md and pushes it to GitHub.

  "Spireline gym daemon": at logon of the current user, no time limit, one instance (a second start is ignored). Its action is
  `health_check.py --start-daemon`: it starts the practice loop (rl/gym_loop.py run, the arguments are one constant in
  tools\health_check.py) as a child unless one runs already or referee\health\STOP or LAB\HALT exists, and then waits for it
  (a task whose action exits shows Ready although its child lives, so the wrapper stays: the task is Running while the loop
  lives, and a crash (non-zero exit) is restarted by Task Scheduler three times, 5 minutes apart; "End task" ends the wrapper only, the
  loop it started carries on, so stop the loop with gym_loop.py stop).

  Idempotent: running it again replaces both tasks (-Force). -WhatIf is a plain switch here (Register-ScheduledTask's own is not
  reliable): it prints the definitions and changes nothing. -Selftest registers a pair under other names ("Spireline
  health-selftest" and "Spireline gym daemon-selftest") whose daemon task runs `--start-daemon --selftest`: its child is a harmless
  300-second sleeper, never the real practice loop. Run that task to see whether Task Scheduler keeps it "Running" while the child
  lives, then remove the pair with `-Selftest -Unregister`.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File pc-setup\register-health-tasks.ps1 -WhatIf
  powershell -ExecutionPolicy Bypass -File pc-setup\register-health-tasks.ps1
  powershell -ExecutionPolicy Bypass -File pc-setup\register-health-tasks.ps1 -Selftest
  powershell -ExecutionPolicy Bypass -File pc-setup\register-health-tasks.ps1 -Selftest -Unregister
  powershell -ExecutionPolicy Bypass -File pc-setup\register-health-tasks.ps1 -Unregister
#>
param(
    [switch]$WhatIf,
    [switch]$Unregister,
    [switch]$Selftest,
    [string]$Repo = 'D:\spireline\spireline',
    [string]$At = '21:00'
)
$ErrorActionPreference = 'Stop'

$Suffix = ''
$DaemonExtraArgs = ''
if ($Selftest) { $Suffix = '-selftest'; $DaemonExtraArgs = '--selftest' }
$healthName = 'Spireline health' + $Suffix
$daemonName = 'Spireline gym daemon' + $Suffix

if ($Unregister) {
    foreach ($n in @($healthName, $daemonName)) {
        if ($WhatIf) { Write-Output "What if: would unregister '$n'. Nothing changed."; continue }
        if (Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $n -Confirm:$false
            Write-Output "Unregistered '$n'."
        } else {
            Write-Output "'$n' is not registered."
        }
    }
    return
}

$python = Join-Path $Repo '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $python)) { $python = Join-Path $Repo '.venv\Scripts\python.exe' }
$script = Join-Path $Repo 'tools\health_check.py'
if (-not (Test-Path $script)) { throw "tools\health_check.py is not in $Repo" }
$user = '{0}\{1}' -f $env:USERDOMAIN, $env:USERNAME
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited

$healthArgs = '"{0}"' -f $script
$daemonArgs = ('"{0}" --start-daemon {1}' -f $script, $DaemonExtraArgs).Trim()
$healthAction = New-ScheduledTaskAction -Execute $python -Argument $healthArgs -WorkingDirectory $Repo
$daemonAction = New-ScheduledTaskAction -Execute $python -Argument $daemonArgs -WorkingDirectory $Repo

$healthTrigger = New-ScheduledTaskTrigger -Daily -At $At
$healthSettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -Priority 7

$daemonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$daemonSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -Priority 7

Write-Output "Task:     $healthName"
Write-Output "Action:   $python $healthArgs"
Write-Output "Trigger:  daily at $At local time; StartWhenAvailable; limit 1 hour; one instance"
Write-Output "Task:     $daemonName"
Write-Output "Action:   $python $daemonArgs"
Write-Output "Trigger:  at logon of the current user; no time limit; one instance; restart 3 times, 5 minutes apart, after a crash"
Write-Output "Start in: $Repo; runs as the current user, Interactive, Limited (no password stored)"

if ($WhatIf) {
    Write-Output "What if: would register both tasks as above. Nothing changed."
    return
}

Register-ScheduledTask -TaskName $healthName -Action $healthAction -Trigger $healthTrigger -Settings $healthSettings -Principal $principal -Force `
    -Description 'Spireline daily health check: reads the lab, restarts the practice loop if it is down, writes and pushes status/latest.md. See docs/LIGHTS_OUT.md.' | Out-Null
Register-ScheduledTask -TaskName $daemonName -Action $daemonAction -Trigger $daemonTrigger -Settings $daemonSettings -Principal $principal -Force `
    -Description 'Spireline practice loop (fight-loop daemon): starts at logon unless one runs or referee/health/STOP exists. See docs/LIGHTS_OUT.md.' | Out-Null

foreach ($n in @($healthName, $daemonName)) {
    $t = Get-ScheduledTask -TaskName $n
    $a = $t.Actions[0]
    $trig = ($t.Triggers | ForEach-Object { $_.CimClass.CimClassName -replace '^MSFT_Task', '' }) -join ','
    '{0,-34} state={1,-8} trigger={2,-14} limit={3,-6} multiple={4} priority={5}' -f $t.TaskName, $t.State, $trig, $t.Settings.ExecutionTimeLimit, $t.Settings.MultipleInstances, $t.Settings.Priority
    '    runs: {0} {1}' -f $a.Execute, $a.Arguments
}
