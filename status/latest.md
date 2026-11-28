# Spireline status: RED (2026-11-28 10:00Z)

Written by the daily health check from the machine's own files. It plays nothing: it reads, restarts the practice loop if that is down, and publishes this page.

**In short.** RED: something needs attention.

- RED: the lab runner's status file cannot be read (the first line of LAB/status.txt is not in the usual form)
- RED: a new alert file appeared: train.txt
- AMBER: the lab runner's log shows trouble in the last day (2 job(s) ended with an error; 2 step(s) failed)

**The lab runner** could not be checked: the first line of LAB/status.txt is not in the usual form. In the last day it finished 3 jobs; trouble: 2 ended with an error, 2 steps failed, 0 kinds are backing off, 0 were killed at their time limit.

**The practice loop** (the loop that plays fights to train the fighter) is running (since 2026-11-21 13:53Z). Its newest daily summary, for 2026-11-27, says it played 8,521 fights: 12.6 hours playing, 11.4 hours waiting (it waits while the judge or the weekly test holds the machine). Its log last wrote 27 minutes ago. 7 fighter versions have been promoted in all; the newest is v10 (2026-11-28).

**The whole-run judge** (the test that decides whether a new fighter is kept) has the champion at generation 22 (promoted 2026-11-25); the newest generation folder is gen23. It has finished 52 judgements in all; the last, on 2026-11-27, was rejected for candidate-fight-v9 on 800 paired runs.

**The weekly real-game test** last ran on 2026-11-27 (it began 2026-11-27 19:04Z and finished 2026-11-28 01:39Z). The next is due 2026-12-04, in 6.4 days.

**Getting past the first Act 3 boss.** In the newest finished test (2026-11-27, generation 22, 2000 runs) the player got past the first Act 3 boss in 105 of the 379 fights it finished itself: 27.7 in 100, give or take 4.6. Counting every arrival at that boss, including fights where the referee lost its place and a stand-in played on, it is 105 of 449: 23.4 in 100, give or take 4.0; the stand-in played on in 70 of those 449 arrivals. The January rule says 35 or more in 100 means continue and under 32 means stop; in between, one more test. The reading today is under the stop line.

**Disk.** 1625 GB free of 1863 GB.

**Open alerts.** train.txt (changed 2026-11-28).

## Since the last check

Since the check of 2026-11-27 10:00Z:
- The practice loop promoted fighter v10 over v9 on 2026-11-28 02:37Z.
- A new weekly real-game test folder appeared: 2026-11-27T1904.
- New alert: train.txt.

## Repairs

- Nothing needed repair.

## The figures

| figure | value |
| --- | --- |
| colour | RED |
| checked | 2026-11-28 10:00Z |
| runner status age (s) | None |
| runner processes | 2 |
| runner job now | unknown |
| jobs finished, last 24 h | 3 |
| failed jobs / steps, last 24 h | 2 / 2 |
| kinds backing off | none |
| last tree checked out | a18407c |
| practice loop processes | 2 |
| practice loop running since | 2026-11-21 13:53Z |
| practice loop log age (s) | 1635 |
| newest daily summary | 2026-11-27: 8521 fights, 12.6 h played, 11.4 h waited |
| fighters promoted in all | 7 |
| newest fighter version | 10 |
| champion generation | 22 |
| newest generation folder | 23 |
| judgements finished | 52 |
| newest weekly test | 2026-11-27T1904 |
| weekly test age (days) | 0.62 |
| next weekly test due | 2026-12-04 19:03Z |
| test running now | no |
| door passes, player-finished | 105 of 379, 27.7 in 100, give or take 4.6 |
| door passes, all arrivals | 105 of 449, 23.4 in 100, give or take 4.0 |
| lost-track arrivals | 70 of 449, 15.6 in 100, give or take 3.4 |
| disk free (GB) | 1624.8 |
| lock-file lines | gym-loop (27 minutes) |
| open alert files | 1 |
