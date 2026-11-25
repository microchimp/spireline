# Sceptic review: keep the project going or close it? (2026-11-25)

The owner asked (2026-11-25): "thinking of closing this project down - run skeptic cycle on whether to keep it going or not", then "not worth the extra spend on claude a month". This review answers from the primary records (the paper's scoreboard, the real-game blocks of 11-19 and 11-20, the promotion ledger, the pooled-reading tool, the lab and fight-loop logs). Every figure carries its margin (two standard errors) or says it has none. Unlike the 11-21 and 11-24 reviews, no independent paid reviewer was run: the question is the Claude spend, and a second model's opinion would have cost a visible slice of a week's allowance to answer a question the records answer.

## 1. How far from the goal are we?

The goal is to play better than the best human players at Ascension 10, Ironclad first. The only yardstick we have measured is the average human (the public run export, aggregates only); the best players sit well above it and we hold no measured figure for them.

| Measure (Ironclad, Ascension 10) | Average human | Our AI in the real game |
|---|---|---|
| Floors reached, average | 27 | 30.1 (2,000 runs, 11-19) |
| Kills the Act 1 boss, share of all runs | 55 in 100 | 72 in 100 |
| Kills the Act 2 boss | 29 in 100 | 24 in 100 (476 of 1,997, plus or minus 1.9) |
| Gets past the first Act 3 boss | 18 in 100 of runs; about 70 in 100 of arrivals | 3.4 in 100 of runs (68 of 2,000); 19.5 in 100 of arrivals (68 of 348, plus or minus 4.2); 26.2 on the 260 fights our player finished itself |
| Wins the run | 11 in 100 | 0.1 in 100 (2 of 2,000; both blocks) |
| Survives the humans' own 400 fights | 80 in 100 | 65 in 100 |

Reading: the AI is at or above the average human until the third act, then it falls off a cliff at the Act 3 bosses, which it passes about one time in four where humans pass about seven in ten. The run win rate is a hundred times below the average human's, and the goal is the best human, not the average.

## 2. What moved in six and a half weeks (10-11 to 11-25)?

- Real wins: 2 of 2,000 on both real blocks (11-19 and 11-20). No movement.
- Real Act 3 boss door: 12.7 per 100 arrivals (11-19, generation 19) to 19.5 (11-20, generation 20), plus or minus about 4 each. About half of that move is the referee fix of lane 10 (fewer stalled fights), not the player; the player-finished rate went 19.4 to 26.2.
- On the copy, the champion's first Act 3 boss passes per 100 runs: 2.68 (generation 18) to 5.10 (generation 20) to about 6.5 (generation 21). Real: 3.4.
- The last two weeks (the "Act 3 week"): the fight loop promoted four fighters; at the boss door they pool to +1.12 passes per 100 arrivals plus or minus 0.70 (two fighters, 1,590 starts); in whole runs they pool to +0.11 per 100 runs plus or minus 0.49 (four fighters, 10,000 pairs), consistent with full carryover (+0.24 plus or minus 0.15) and with zero. Most of the two weeks' landed work was measurement: the reader correction (17.5 to 19.5), the exam at the boss door, the referee fixes for the 25 in 100 of boss fights where it loses its place (landed, untested on the real game until 11-27).

## 3. What does the Claude spend buy, and what runs without it?

The machine's learning runs by itself: the fight loop practices, gates and promotes fighters (one every one to two days lately), the lab judges each one in whole runs and promotes generations, and a real-game block of 2,000 runs plays once a week (every 168 hours from 11-20: 11-27, 12-04, 12-11, ...). None of that needs a Claude session.

Claude buys: hand-checks of every landing, the diagnosis and fixing of faults in the copy and the referee (the biggest single gain of the month, the referee's lost fights, came from this), the measurement tools, the records and the paper. In the last week that was about four to six worker lanes a day plus the orchestrator, roughly 80 to 95 in 100 of the weekly allowance. Without it: nothing is fixed when it breaks, nobody reads the alerts, the paper and records freeze at today's state. The machine still learns and still measures.

## 4. At the current pace, when would the goal arrive?

The one gain we can measure is about one more pass per 100 arrivals at the boss door per promoted fighter, a fighter every one to two days. The door gap to the average human is about 44 points (26 to 70). If every gain stacked perfectly, which gains in learning systems do not, that is about 44 fighters, two to three months, to reach the average human at that one door. Runs also die in the Act 3 hallways and elite fights (12.6 of 100 real runs) and at the second Act 3 boss (7 in 100 arrivals pass), neither of which the practice set covers. A fair order of magnitude for reaching the average human's win rate with this method on this machine is a year, with a large margin either way. For the best human we have no honest estimate: the method has not yet shown a gain in whole runs at all.

## 5. What would a sceptic say?

About continuing: that a monthly spend bought, in the last two weeks, better measurement and one near-tie promotion, and that the best case for the method is the average human in about a year, with the goal (the best human) beyond any estimate the records support. That the two numbers that matter, real wins and real Act 3 door passes by the player, have not moved beyond noise in a month.

About stopping: that the spend and the machine are separable. The one question worth paying for, whether the fight loop's small door gains stack over weeks and reach whole runs, is answered for free by leaving the machine running and reading its weekly real blocks a month later. Stopping the machine as well forfeits that answer for no saving beyond electricity. Sunk cost argues for nothing either way.

About lights-out: that unattended machines stall. In the past month there was about one incident a week that needed a hand (a dead worker, a stuck lock, a job that retried silently). Each costs time, never data; a stall just means less learning until someone looks. A game update from the vendor would break the weekly real block (the referee is built against game version 0.107.1); the copy-game learning would continue. Disk is not a constraint: 1,625 GB free of 1,863, and the learning folders hold about 5 GB. The lab runner is a Windows scheduled task ("Spireline fix lab") and comes back after a reboot; the fight loop is a hand-started process and would not, so a Windows update that reboots the PC stops the practice until someone restarts it, while the lab's judgements and the weekly real block continue.

## Recommendation (orchestrator)

1. **Stop the Claude spend now**: cancel or drop to the cheapest plan. The project's measured pace does not justify a monthly bill against the stated goal.
2. **Leave the machine running lights-out** for four to six weeks: the fight loop, the lab's judge and the weekly real block need no session. The cost is electricity.
3. **Read it once, early January**, in one short session (a cheap plan for one month, or none: the three commands and the numbers to compare are written in `referee/backlog/STATE.md`, "If the project is read after a pause"). The reading: the player-finished rate at the first Act 3 boss door in the latest real block. At 26 today (plus or minus 5.4). If it reads 35 or more, the gains stack and a case to continue exists; if it reads under 32, close for good and keep the code (the copy, the referee, the corpus aggregates, the learning pipeline, all pushed) as the deliverable.
4. **Before going dark (today, cheap)**: let lane 25 land (the fresh-champion base block, so promotions keep working unattended), record v7's verdict, write the reading instructions into STATE, push everything. No new lanes.

The owner's choices: close now (stop the machine too), lights-out as above, or continue as before. The orchestrator recommends lights-out.
