# Spireline status: GREEN (2026-11-25 10:39Z)

Written by the daily health check from the machine's own files. It plays nothing: it reads, restarts the practice loop if that is down, and publishes this page.

**In short.** GREEN: everything is running and nothing needs attention.

**The lab runner** (the scheduler that runs the judge and the weekly test) is working: it last reported under two minutes ago and is busy with a whole-run judgement of a new fighter. In the last day it finished 2 jobs; none failed.

**The practice loop** (the loop that plays fights to train the fighter) is running (since 2026-11-21 13:53Z). Its newest daily summary, for 2026-11-24, says it played 13,428 fights: 19.7 hours playing, 4.3 hours waiting (it waits while the judge or the weekly test holds the machine). Its log last wrote 2.0 hours ago. 5 fighter versions have been promoted in all; the newest is v8 (2026-11-25).

**The whole-run judge** (the test that decides whether a new fighter is kept) has the champion at generation 21 (promoted 2026-11-22); the newest generation folder is gen22. It has finished 50 judgements in all; the last, on 2026-11-25, was rejected for candidate-fight-v7 on 3400 paired runs. A judge job is running now (its lock line is 2 minutes old).

**The weekly real-game test** last ran on 2026-11-20 (it began 2026-11-20 19:04Z and finished 2026-11-21 01:40Z). The next is due 2026-11-27, in 2.3 days.

**Getting past the first Act 3 boss.** In the newest finished test (2026-11-20, generation 20, 2000 runs) the player got past the first Act 3 boss in 68 of the 260 fights it finished itself: 26.2 in 100, give or take 5.5. Counting every arrival at that boss, including fights where the referee lost its place and a stand-in played on, it is 68 of 348: 19.5 in 100, give or take 4.3; the stand-in played on in 88 of those 348 arrivals. The January rule says 35 or more in 100 means continue and under 32 means stop; in between, one more test. The reading today is under the stop line.

**Disk.** 1625 GB free of 1863 GB.

**Open alerts.** None.

## Since the last check

Since the check of 2026-11-25 10:35Z:
- Nothing new.

## Repairs

- Nothing needed repair.

## The figures

| figure | value |
| --- | --- |
| colour | GREEN |
| checked | 2026-11-25 10:39Z |
| runner status age (s) | 11 |
| runner processes | 2 |
| runner job now | 20261125T0836-train (train) |
| jobs finished, last 24 h | 2 |
| failed jobs / steps, last 24 h | 0 / 0 |
| kinds backing off | none |
| last tree checked out | 9432e74 |
| practice loop processes | 2 |
| practice loop running since | 2026-11-21 13:53Z |
| practice loop log age (s) | 7225 |
| newest daily summary | 2026-11-24: 13428 fights, 19.7 h played, 4.3 h waited |
| fighters promoted in all | 5 |
| newest fighter version | 8 |
| champion generation | 21 |
| newest generation folder | 22 |
| judgements finished | 50 |
| newest weekly test | 2026-11-20T1904 |
| weekly test age (days) | 4.65 |
| next weekly test due | 2026-11-27 19:03Z |
| test running now | no |
| door passes, player-finished | 68 of 260, 26.2 in 100, give or take 5.5 |
| door passes, all arrivals | 68 of 348, 19.5 in 100, give or take 4.3 |
| lost-track arrivals | 88 of 348, 25.3 in 100, give or take 4.7 |
| disk free (GB) | 1625.2 |
| lock-file lines | lab-train (2 minutes) |
| open alert files | 0 |
