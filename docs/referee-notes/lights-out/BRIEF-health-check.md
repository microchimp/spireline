# Brief: the daily health check of the unattended machine (lights-out, D70)

Worker rules: `D:/spireline/referee/backlog/act3-week/COMMON.md` applies in full (no `D:/spireline/src` writes, no E2 scripts, no user names, host names or `C:/Users` paths in any committed file or memo, Windows process APIs only, never kill a process by image name, never touch `LAB/jobs.json`, `LAB/PAUSE`, `LAB/HALT`, `LAB/train/ready-*`, `QUIET.lock` or the gym daemon, no heavy runs). Repo: `D:/spireline/spireline` (Spireline, Python, `.venv/Scripts/python.exe`, tests `python -m pytest -q`, 368 pass today). Commit to `main` and push once the suite passes; trailer `Co-Authored-By: Claude Sonnet 5.5 <<email>>`. Lab files are read-only inputs for you; the lab's own paths: `D:/spireline/referee/lab` (= `LAB`), `D:/spireline/referee/gym-loop`, `D:/spireline/referee/QUIET.lock`, `D:/spireline/referee/agent`.

## Why

The owner has decided (D69/D70, 2026-11-25) to run the machine unattended for weeks with almost no Claude input. The machine today: the fight-loop daemon (`rl/gym_loop.py run`, hand-started, dies with a reboot), the lab runner (Windows scheduled task "Spireline fix lab", `tools\lab\runner.py`, returns after a reboot), a whole-run judge job whenever a `ready-*` marker exists, a real-game block every 168 h from 2026-11-20T19:03Z. We need a daily, Claude-free check that writes a plain-language status into the public Spireline repo (so the owner reads it on a phone and a weekly cloud agent reads it), and that restarts the daemon when it is down.

## Build

### 1. `tools/health_check.py` (default mode: the daily check)

Reads (all read-only):
- `LAB/status.txt` first line: `<UTC> running|idle ... job=... step=...` (its age tells whether the runner is alive; written every cycle, task interval 5 min).
- `LAB/runner.log`: job outcomes in the last 24 h (`rc=` not 0, `backoff`, `killed at limit`, `finished rc=`), the last presort tree hash.
- `LAB/alerts/` (files = open alerts; names and mtimes).
- `LAB/nightly/`: folders `<timestamp>` (newest = last real block; `last-ok` holds the last finished one's time); expected every 168 h from 2026-11-20T19:03Z.
- `D:/spireline/referee/QUIET.lock`: lines `<tag> <UTC> pid=<windows pid>`; a `lab-train` or `lab-nightly` line older than 24 h with no matching job in status.txt is a stuck judge; a line whose pid is dead is stale.
- `gym-loop/loop.log`: `grep -a daily` lines (one a day: fights, hours played and waited), `grep -a promoted` lines (fighters promoted), the last line's age.
- `D:/spireline/referee/agent/`: newest `gen<N>` folder, `current.json` (the champion), `promotions.tsv`.
- Processes: PowerShell `Get-CimInstance Win32_Process` (python.exe and pythonw.exe) with `CommandLine` and `CreationDate`, via `subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command", ...ConvertTo-Json])`. The daemon is a process whose command line contains `rl/gym_loop.py run --root D:/spireline/referee/gym-loop`; the runner one containing `tools\lab\runner.py`. (uv's venv `python.exe` is a trampoline: a venv process shows twice, as the venv exe and as `C:\...\uv\python\...\python.exe` with the same command line; "at least one" is alive.) `psutil` is not installed; do not add it.
- Disk: `shutil.disk_usage("D:/")`.
- The latest finished real block's strict reading: `tools/strict_rows.py` has the reader (`--check <block>/g<N>`); import its functions to compute first-Act-3-boss passes per 100 arrivals (all arrivals) and per 100 player-finished fights, with 2 SE, and lost-track arrivals; `tools/weekly_numbers.py` may already compute these (`--root`, `--no-write`, `--json-only`): reuse, do not rewrite. The January rule (D69): player-finished 35 or more per 100 = a case to continue; under 32 = close; between = one more block.

Colour: **RED** when the runner's status.txt is older than 2 h, or the daemon is absent and could not be started, or disk free under 100 GB, or a stuck judge line (above), or the newest real block is older than 10 days, or a new alert file appeared since the last check. **AMBER** when runner.log shows a failed job in the last 24 h, a stale QUIET line, the newest block older than 8 days, the daemon restarted by this check, or `D:/spireline/referee/health/STOP` exists (stopped on purpose). Else **GREEN**.

Writes:
- `status/latest.md` in the Spireline repo: line 1 `# Spireline status: GREEN|AMBER|RED (YYYY-MM-DD HH:MMZ)`; then a plain-language paragraph per item in everyday words (the owner reads this on a phone: "the practice loop is running, it has played N fights in the last day"; "the weekly real-game test last ran on <date>; the next is due <date>"; "the player got past the first Act 3 boss in N of M fights it finished itself, N in 100, give or take K; the January rule says 35 or more means continue, under 32 means stop"), then "Since the last check" (promotions, new generations, finished judgements, alerts), then "Repairs" (what this check did), then a table of the raw figures.
- `status/latest.json` (every figure) and one row appended to `status/history.csv` (date, colour, runner_alive, daemon_alive, fights_last_day, promotions_total, newest_generation, last_block, door_rate_player_finished, door_rate_all, disk_free_gb, repairs).
- A log `D:/spireline/logs/health/health-<date>.log` (not in the repo).

Every output line passes through `tools/landing_evidence.scrub` (user paths become `<home>`); tests assert the output holds no `C:/Users`, `C:\Users`, host name or user name (read them at test time from `os.environ`, never write them in the test).

Git step, after writing: in `D:/spireline/spireline` run `git fetch origin`; if `HEAD` is not `origin/main`, or `git status --porcelain` shows anything staged, or anything modified outside `status/`, skip the push and record why in the log and in latest.md's Repairs section; else `git add status/latest.md status/latest.json status/history.csv`, commit `status: <date> <COLOUR>` (no trailer: a machine commit), `git push origin main`; on a push failure log it and leave the commit. Never `git add -A`, never touch other files.

### 2. `--start-daemon` mode

Used by the scheduled task "Spireline gym daemon" (at logon) and by the daily check when the daemon is absent (`schtasks /run /tn "Spireline gym daemon"`; never start the daemon from the daily check's own process). Behaviour: if a daemon process exists, print it and exit 0; if `D:/spireline/referee/health/STOP` or `LAB/HALT` exists, print why and exit 0; else start, as a plain child (not detached, so the scheduled task stays "Running" while the daemon lives), with `cwd=D:/spireline/fork/wt-gym-loop-run`, `creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NEW_PROCESS_GROUP`, stdout and stderr appended to `D:/spireline/logs/gym-loop/daemon.out`:

```
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gym_loop.py run --root D:/spireline/referee/gym-loop --max-epochs 8 --gate-every-min 120 --teacher-store D:/spireline/referee/run-teacher --procs 12 --gate-procs 12 --trainer-extra-rows-root D:/spireline/referee/run-cheap --trainer-extra-window 150000 --rule v5
```

(`--gate-procs` must equal `--procs`.) Read the arguments from one place (a constant or `status/daemon-args.json`), so a change is one edit. Write the started pid and time to `D:/spireline/referee/health/daemon-start.log`. Never start a second daemon. Today's daemon (pid 10516, hand-started 11-24) keeps running; the task takes over only when it is gone.

Verify the "task stays Running after the wrapper exits" assumption empirically with a self-test, never with the real daemon: a temporary task "Spireline health selftest" whose action is `health_check.py --start-daemon --selftest` (the child is `python -c "import time; time.sleep(300)"` started the same way); run it, check `schtasks /query /tn ... /v` shows Running and the child alive after the wrapper has exited, then end and delete the test task. Record the result in the memo. If the child dies with the wrapper, keep the wrapper alive (`child.wait()`) instead and say so.

### 3. `pc-setup/register-health-tasks.ps1`

Idempotent registration (Windows PowerShell 5.1, `ScheduledTasks` module) of two tasks for the current user, logon type Interactive like the existing "Spireline fix lab" task: "Spireline health" (daily at 21:00 local = 10:00Z; action `D:\spireline\spireline\.venv\Scripts\pythonw.exe D:\spireline\spireline\tools\health_check.py`, working directory `D:\spireline\spireline`, StartWhenAvailable, execution limit 1 h) and "Spireline gym daemon" (AtLogOn for the current user; action `... health_check.py --start-daemon`; no execution limit; MultipleInstances IgnoreNew). `-WhatIf` is not reliable for Register-ScheduledTask: test with names suffixed `-selftest`, then unregister them. Print the two tasks at the end. The orchestrator runs this script; you do not register the real tasks.

### 4. `docs/LIGHTS_OUT.md`

How the unattended machine runs (the three tasks, the daemon, the weekly block), where the status appears (`https://github.com/microchimp/spireline/blob/main/status/latest.md`), how to stop everything (create `D:/spireline/referee/health/STOP`, then `python rl/gym_loop.py stop --root D:/spireline/referee/gym-loop` from the daemon's worktree; the lab task is disabled with `schtasks /change /tn "Spireline fix lab" /disable`), how to read the January decision (copy the rule and the commands from `D:/spireline/referee/backlog/STATE.md` section "If the project is read after a pause"), the known ways it stops (reboot without logon, a game update from the vendor, a stuck judge line).

## Tests

`tests/test_health_check.py`: fixtures for status.txt, runner.log, QUIET.lock, loop.log, nightly folders, agent folders and a canned PowerShell JSON; every colour rule with one case each; the scrub assertions; the git step with a fake `git` (a recorded command list, never the real repo); `--start-daemon` with a fake Popen (never a real start); the daemon-args constant has `--gate-procs` equal to `--procs`. No test reads the live lab or starts a process.

## Done

1. Suite green (368 + yours), committed and pushed to Spireline `main`.
2. One live run of the default mode from the repo (`.venv/Scripts/python.exe tools/health_check.py`): `status/latest.md` written and pushed by the script itself (this is the path's test); its head in the memo.
3. The selftest result (task stays Running: yes/no, and what you did about it).
4. Memo `D:/spireline/referee/backlog/lights-out/HEALTH-CHECK.md` (at most 40 lines): what was built, the live run's head, the selftest, the exact command for the orchestrator to register the tasks, anything unverified.
5. Report at most 5 lines: commit hash, test counts, the colour of the live run, the selftest answer, what is unverified.
