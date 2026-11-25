# Lights out: how the unattended machine runs

Written 2026-11-25 (D69/D70). The owner decided to run the machine for weeks with almost no Claude input. This page says what runs by itself, where
to read how it is doing, how to stop it, and how to read the one decision in January. The code is `tools/health_check.py`; its tests are
`tests/test_health_check.py`.

## What runs

| What | How it starts | What it does |
| --- | --- | --- |
| The lab runner, Windows task **"Spireline fix lab"** | at logon, always on, restarts after a reboot | the scheduler: the whole-run judge (a `ready-*` marker starts it), the code-tree checks, the weekly real-game test |
| The practice loop (the fight-loop daemon, `rl/gym_loop.py run`), Windows task **"Spireline gym daemon"** | at logon; the daily check starts it again when it is down | plays fights all day, trains the fighter, gates new fighters, writes `referee/gym-loop/loop.log` (one `daily` line a day) |
| The daily check, Windows task **"Spireline health"** | every day at 21:00 local time (10:00Z at UTC+11) | reads the lab, repairs the practice loop if it is down, writes `status/latest.md` and pushes it |
| The weekly real-game test | the lab runner, every 168 hours from 2026-11-20 19:03Z (11-27, 12-04, 12-11, ...) | 2,000 real-game runs of the champion; `referee/lab/nightly/<timestamp>` |

The practice loop's start line lives in one place, the constant `DAEMON_ARGS` of `tools/health_check.py` (`--gate-procs` must equal `--procs`; a
test pins that). A change to it is one edit there. The task "Spireline gym daemon" runs `health_check.py --start-daemon`: if a practice loop runs it
says so and exits; if `referee/health/STOP` or `referee/lab/HALT` exists it starts nothing; otherwise it starts the loop as a plain child
(BelowNormal priority, output appended to `logs/gym-loop/daemon.out`, its pid and time to `referee/health/daemon-start.log`) and **waits for it**: the 2026-11-25
self-test showed that a task whose action exits is "Ready" again at once even though its child lives on, so the waiting wrapper is what keeps the task
"Running" while the loop lives and lets Task Scheduler restart a crashed loop (three times, five minutes apart). "End task" ends the wrapper only; the loop it
started carries on (stop the loop with `gym_loop.py stop`, below).
`--no-wait` returns at once. A second loop could not run anyway (the daemon holds a mutex).

## Registering the two new tasks (once, by the orchestrator)

    powershell -ExecutionPolicy Bypass -File D:\spireline\spireline\pc-setup\register-health-tasks.ps1

It replaces both tasks if they exist (safe to repeat), prints them, and registers for the current user only (Interactive, no password stored), like
the lab task. `-WhatIf` prints and changes nothing; `-Selftest` registers a harmless pair under the names "Spireline health-selftest" and "Spireline gym daemon-selftest"
(the daemon one starts a 300-second sleeper, never the practice loop); `-Selftest -Unregister` removes them.

## Where the status appears

`https://github.com/microchimp/spireline/blob/main/status/latest.md`, rewritten every day by the daily check. Line 1 is
`# Spireline status: GREEN|AMBER|RED (date time)`.

- **GREEN**: everything runs, nothing to do.
- **AMBER**: worth a look, the machine works: a job failed in the last day, a stale line in the lock file, the weekly test is more than 8 days old, the
  check had to restart the practice loop, the machine is stopped on purpose (`referee/health/STOP`), a `PAUSE` or `HALT` file stands in the lab, the
  process list could not be read, or the practice loop's log has been silent for a day and a half.
- **RED**: something is down or stuck: the lab runner has not reported for two hours, the practice loop is down and could not be started, less than
  100 GB of disk, a judge job holds the lock for more than a day with no matching job running, the weekly test is more than 10 days old, or a new alert file
  appeared in `referee/lab/alerts`.

The page then says in plain words: the lab runner, the practice loop (fights played in the last day), the judge and the champion, the weekly real-game test (last ran,
next due), the first-Act-3-boss reading with its margin and the January rule, disk, alerts; then "Since the last check", "Repairs" and a table of the
raw figures. `status/latest.json` holds every figure, `status/history.csv` one row a day (colour, fights, promotions, generation, door rates, disk). The check's
own log is `logs/health/health-<date>.log` (not in the repo); its memory between days is `referee/health/state.json`.

The page is pushed by the check itself: `git fetch`, then add, commit (`status: <date> <COLOUR>`) and push of the three status files only. It is **skipped
(and said so on the page and in the log)** when the repo is not on `main`, is not level with `origin/main` (a clean tree that is behind is brought
forward; ahead only by its own status commits is fine), or has anything staged or modified outside `status/`. Keep the unattended tree clean: a stray edit
stops the daily push until it is committed or reverted. `health_check.py --allow-dirty-tree` pushes anyway (the commit names only the status files).

## How to stop everything

1. Create the file `D:\spireline\referee\health\STOP` (the check then leaves the practice loop stopped and shows AMBER).
2. From the daemon's worktree: `cd D:\spireline\fork\wt-gym-loop-run` then `D:\spireline\src\sts2\.venv\Scripts\python.exe rl/gym_loop.py stop --root D:/spireline/referee/gym-loop`
   (the loop stops; the waiting task "Spireline gym daemon" then ends by itself; `schtasks /change /tn "Spireline gym daemon" /disable` keeps it from starting at the next logon).
3. Stop the lab: `schtasks /change /tn "Spireline fix lab" /disable` and end the running task (`schtasks /end /tn "Spireline fix lab"`); a `referee/lab/PAUSE` file pauses its jobs, a `HALT` file halts them.
4. Optionally also `schtasks /change /tn "Spireline health" /disable`.

To start again: delete `STOP`, enable the tasks (`schtasks /change /tn "..." /enable`), and `schtasks /run /tn "Spireline gym daemon"`.

## The January decision (one reading, written 2026-11-25)

Copied from `D:\spireline\referee\backlog\STATE.md`, "If the project is read after a pause".

1. **The latest real block.** Folders `D:/spireline/referee/LAB/nightly/<timestamp>` (one a week from 11-20 19:03Z; `last-ok` names the last that finished). Read it with
   `D:/spireline/spireline/.venv/Scripts/python.exe D:/spireline/spireline/tools/strict_rows.py --check D:/spireline/referee/LAB/nightly/<timestamp>/g<N>`
   (the daily page quotes the same figures). Numbers to compare with (11-20 block, generation 20): the first Act 3 boss passed on **19.5 per 100 arrivals** (68 of 348) and
   **26.2 per 100 fights the player finished itself** (68 of 260); lost-track arrivals 88 of 348; wins 2 of 2,000. **Decision rule (D69): player-finished 35 or more per 100 is a case
   to continue; under 32 means close and keep the code; between the two, one more block.**
2. **What the machine did meanwhile.** `grep -a promoted D:/spireline/referee/gym-loop/loop.log | tail` (fighters promoted), `grep -a daily D:/spireline/referee/gym-loop/loop.log | tail -n 40` (one line a day; a missing day means
   the practice loop was down), `tail -n 40 D:/spireline/referee/LAB/runner.log` and the folder `D:/spireline/referee/LAB/alerts`, the generation folders `D:/spireline/referee/agent/gen*/`, and `status/history.csv` in this repo.
3. **The pooled reading of the fighters.** `D:/spireline/spireline/.venv/Scripts/python.exe D:/spireline/spireline/tools/pooled_fight_swaps.py` (last line: the pooled whole-run effect with its margin).

## The known ways it stops

- **A reboot without a logon.** All three tasks start at logon (or on the daily clock) of the current user; a PC that reboots and waits at the sign-in screen runs nothing until someone signs in.
  The daily check also runs only while the user is signed in (a missed run starts when the PC is next on).
- **A game update from the vendor.** The referee is built against 0.107.1; the weekly real-game block then fails (the check shows AMBER or RED by the block's age); the practice loop on the copy game carries on.
- **A stuck judge.** A `lab-train` or `lab-nightly` line in `referee/QUIET.lock` more than a day old with no such job in `referee/lab/status.txt` (RED): the practice loop waits for the judge, so one stuck line freezes it.
  Remove only that line after looking at `referee/lab/runner.log`.
- **Disk.** 1,625 GB were free on 2026-11-25 and the tree grew about 14 GB a week; under 100 GB is RED.
- **The push.** No network, a changed GitHub login, or a dirty tree: the page on GitHub goes stale while the local `status/latest.md` stays current; the next page's Repairs section says what failed.
- **Sleep.** A PC that sleeps runs nothing; keep its sleep timeout off while the machine runs unattended (the daily check's missed run starts when the PC wakes).
