# Spireline status: GREEN (2026-11-27 10:00Z)

Written by the daily health check from the machine's own files. It plays nothing: it reads, restarts the practice loop if that is down, and publishes this page.

**In short.** GREEN: everything is running and nothing needs attention.

**The lab runner** (the scheduler that runs the judge and the weekly test) is working: it last reported under two minutes ago and is idle. In the last day it finished 1 jobs; none failed.

**The practice loop** (the loop that plays fights to train the fighter) is running (since 2026-11-21 13:53Z). Its newest daily summary, for 2026-11-26, says it played 15,392 fights: 21.7 hours playing, 2.3 hours waiting (it waits while the judge or the weekly test holds the machine). Its log last wrote 10 minutes ago. 6 fighter versions have been promoted in all; the newest is v9 (2026-11-27).

**The whole-run judge** (the test that decides whether a new fighter is kept) has the champion at generation 22 (promoted 2026-11-25); the newest generation folder is gen23. It has finished 52 judgements in all; the last, on 2026-11-27, was rejected for candidate-fight-v9 on 800 paired runs.

**The weekly real-game test** last ran on 2026-11-20 (it began 2026-11-20 19:04Z and finished 2026-11-21 01:40Z). The next is due 2026-11-27, in 9.0 hours.

**Getting past the first Act 3 boss.** In the newest finished test (2026-11-20, generation 20, 2000 runs) the player got past the first Act 3 boss in 68 of the 260 fights it finished itself: 26.2 in 100, give or take 5.5. Counting every arrival at that boss, including fights where the referee lost its place and a stand-in played on, it is 68 of 348: 19.5 in 100, give or take 4.3; the stand-in played on in 88 of those 348 arrivals. The January rule says 35 or more in 100 means continue and under 32 means stop; in between, one more test. The reading today is under the stop line.

**Disk.** 1625 GB free of 1863 GB.

**Open alerts.** None.

## Since the last check

Since the check of 2026-11-26 10:00Z:
- The practice loop promoted fighter v9 over v8 on 2026-11-27 03:05Z.
- A new generation folder appeared: gen23.
- The whole-run judge finished a judgement on candidate-fight-v9 (2026-11-27 08:45Z): rejected, 800 paired runs.

## Repairs

- Nothing needed repair.

## The figures

| figure | value |
| --- | --- |
| colour | GREEN |
| checked | 2026-11-27 10:00Z |
| runner status age (s) | 9 |
| runner processes | 2 |
| runner job now | - (None) |
| jobs finished, last 24 h | 1 |
| failed jobs / steps, last 24 h | 0 / 0 |
| kinds backing off | none |
| last tree checked out | a18407c |
| practice loop processes | 2 |
| practice loop running since | 2026-11-21 13:53Z |
| practice loop log age (s) | 582 |
| newest daily summary | 2026-11-26: 15392 fights, 21.7 h played, 2.3 h waited |
| fighters promoted in all | 6 |
| newest fighter version | 9 |
| champion generation | 22 |
| newest generation folder | 23 |
| judgements finished | 52 |
| newest weekly test | 2026-11-20T1904 |
| weekly test age (days) | 6.62 |
| next weekly test due | 2026-11-27 19:03Z |
| test running now | no |
| door passes, player-finished | 68 of 260, 26.2 in 100, give or take 5.5 |
| door passes, all arrivals | 68 of 348, 19.5 in 100, give or take 4.3 |
| lost-track arrivals | 88 of 348, 25.3 in 100, give or take 4.7 |
| disk free (GB) | 1625.0 |
| lock-file lines | gym-loop (10 minutes) |
| open alert files | 0 |
