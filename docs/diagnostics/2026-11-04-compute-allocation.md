# Where the fight-practice compute goes (2026-11-04)

Question (owner, before the teacher-depth design): seconds per fight by search config and fight kind, and the card's busy share over time. Measured from the always-on loop's own records (read-only), plus one timed benchmark where the records were silent (section 6). No design here; the last section lists what was not measured. Numbers are as of 10:25-10:55Z; the loop has run since 2026-10-30 (150 practice segments, 144 gated checkpoints), the card sampler since 2026-10-31.

**Units.** *Own seconds* are the loop's per-fight clock (`rl/gym_lockstep.py`, `OwnClock`): the time the fight's own steps ran plus its share of each network batch it was in. *CPU-seconds* are the six game processes' own CPU clocks (the prior and judge servers are counted apart, as "server CPU"). Over 19,428 practice fights with both figures, CPU-seconds were 0.83 of own seconds (882,695 against 1,059,172). The machine has 16 logical cores, so a day holds 1,382,400 CPU-seconds. Kinds: A1 and A2 are acts 1 and 2; hall, elite and boss are the fight kinds.

## 1. Seconds per fight, by config and kind (records)

Own seconds per fight, mean (number of fights). Sources: the loop's kind-weights pass for a3-v1 (`gym-loop/starts/weights_games.jsonl`, lockstep 16, 6 processes); the loop's practice segments 5 to 150 for x16 (`gym-loop/games/seg*.jsonl`, lockstep 2, 6 processes, uncapped fights); the fight board (M2, `lab/results/fight-gym/2026-10-29-m2`) for x4; the loop's gate games for judge-v0 (`gym-loop/gate/c*-judge-v0*.jsonl`, lockstep 32, 6 processes, 112+ gates).

| config | A1 hall | A1 elite | A1 boss | A2 hall | A2 elite | A2 boss |
|---|---|---|---|---|---|---|
| a3-v1 (the player: 30 simulations a decision, rollout leaves) | 1.16 (200) | 2.54 (200) | 4.55 (200) | 2.41 (200) | 3.13 (140) | 3.53 (136) |
| x4 (4 times a3-v1's simulations) | not in records | not in records | 18.9 (2,000) | not in records | 5.4 (2) | 35.6 (3) |
| x16 (the teacher) | 20.4 (5,128) | 42.9 (2,432) | 79.6 (7,351) | 46.4 (2,790) | 52.3 (1,191) | 79.8 (1,379) |
| judge-v0 (3 times a3-v1's simulations, judge at the leaves) | not in records | not in records | 5.52 (62,397) | not in records | not in records | not in records |

Simulations a fight: a3-v1 479, 731, 998, 736, 754, 930; x16 8,524, 11,413, 14,736, 11,827, 11,360, 17,434 (same kind order); x4 3,387 (A1 boss, M2); judge-v0 2,958 (A1 boss). Rows a fight (decisions recorded by the teacher): 11.9, 18.8, 28.7, 14.4, 16.4, 21.3. x16 costs 17 to 23 times a3-v1 in every kind (16 times the simulations plus the extra exact-solver grading). M2's own Act 1 boss figures, 200 starts by 10 draws: a3-v1 6.4, x4 18.9, x16 74.7 own seconds (older engine and K); the loop's x16 on the same kind reads 79.6.

Where a segment's seconds go (`state.json` `kind_s`, 20,300 fights; the segment is filled by kind weights, so this is the practice mix):

| kind | share of fights | share of own seconds | own seconds a fight |
|---|---|---|---|
| A1 boss | 36.3% | 53.4% | 79.5 |
| A2 hall | 13.7% | 11.8% | 46.4 |
| A2 boss | 6.8% | 10.1% | 79.7 |
| A1 elite | 12.0% | 9.5% | 42.9 |
| A1 hall | 25.3% | 9.5% | 20.4 |
| A2 elite | 5.9% | 5.7% | 52.3 |

## 2. CPU a row costs, and the day's CPU

Training rows are the decisions the teacher recorded. 405,258 rows are in the shards (9.3% held out for scoring); the buffer took 106,078, 70,563 and 75,782 rows on 11-01, 11-02 and 11-03.

Table 2a, CPU-seconds per 1,000 rows by source. Sources: `gym-loop/games/steps.jsonl` (process CPU per step), `segments.jsonl` and `buffer/index.jsonl` (rows), the segment fight rows (own seconds by kind), and the gate steps.

| source | rows made | CPU-seconds per 1,000 rows | note |
|---|---|---|---|
| practice fights, x16, all kinds | 386,710 (19,428 fights) | 2,283 (2,517 per 1,000 training rows) | 45.4 CPU-s and 19.9 rows a fight |
| practice, own seconds per 1,000 rows by kind | | A1 hall 1,716; A1 elite 2,306; A1 boss 2,834; A2 elite 3,226; A2 hall 3,268; A2 boss 3,831 | multiply by 0.83 for CPU |
| gates (stage 1, 400 games) | 0 | no rows | 1,874 CPU-s a gate = the CPU of 821 practice rows |
| gates (a 2,000-game gate) | 0 | no rows | 8,807 CPU-s = 3,858 practice rows |
| kind-weights pass (a3-v1, 1,076 games) | 0 | no rows | about 3,000 CPU-s, run when the start set changes |

Table 2b, the day's CPU by who used it (UTC days; whole days 11-01 to 11-03). Sources: the loop's step records for the loop; `LAB/yield.tsv` for the lab, by the day a job ended (`cpu_min`; two jobs without a CPU reading counted at their wall minutes); "night" is the `nightly-real` job.

| day | loop practice | loop gates (and weights pass) | lab night | lab daytime jobs | total | share of 1,382,400 |
|---|---|---|---|---|---|---|
| 11-01 | 218,624 | 81,717 | 67,260 | 308,052 | 675,653 | 48.9% |
| 11-02 | 141,931 | 57,714 | 0 | 388,326 | 587,971 | 42.5% |
| 11-03 | 190,326 | 41,343 | 170,784 | 404,358 | 806,811 | 58.4% |
| three days | 550,881 (26.6%) | 180,774 (8.7%) | 238,044 (11.5%) | 1,100,736 (53.2%) | 2,070,435 | 49.9% |

The 11-03 night figure holds two nights: the 2,000-run night that ran 11-02 20:06Z to 11-03 00:18Z (2,266 CPU-minutes) and the 500-run night of 11-03 evening (581). Lab daytime, three days, by strategy: aimed-bugs 592,890; the lab's own selfplay 157,386; the lab's own train 154,404; presort 91,350; score-real 41,730; bench-env 27,936; the rest under 12,000 each. The lab's all-time ledger (`LAB/state.json` `strategy_cpu`, since 10-15, wall seconds where a job had no CPU reading) totals 5,757,290: aimed-bugs 1,534,603, train 1,034,536, selfplay 989,655, nightly-real 646,362, aimed-gaps 546,027. Whole-machine CPU percent: the machine log (`nightly/*/machine.jsonl`) covers night blocks only: 52.4% of 16 logical cores over the 2.8-hour 2,000-run night (11-02/03) and 51.9% over the 500-run night (11-03), tree 47.8% and 42.3%. Since 10-30 the loop has used 1,174,700 CPU-seconds, of which practice 882,695 (75%), gates 289,048 (24.6%) and the weights pass 2,995; in wall time 54.5 hours practice and 19.4 hours gates.

## 3. The card

Source: `gym-loop/gpu.jsonl`, one sample a minute (Windows' per-process GPU engine counter, the busiest engine of each process; two snapshots one second apart), split into the loop's prior and judge servers ("inference"), the trainer, other python processes (the lab's) and everything else. Window: 2026-11-01 10:25Z to 2026-11-04 10:24Z, 3,770 samples.

Over the three days: inference 16.8% mean busy; trainer 0.03%; lab python 2.7%; other 0.7%. By phase of the loop: practice 22.5% (50.4% of samples), gate 35.1% (15.4%), yield between steps 0% (10.6%), waiting for a lock or the night 0% (20.8%), start-set rebuild 0% (2.6%). While the loop was playing (practice or gate, 65.7% of the samples) the inference mean was 25.5%, its p95 over all samples 40.6% and its maximum 47.5%.

| hour (Z) | samples | loop inference busy % | everything else busy % | samples with the loop playing | samples waiting or yielding |
|---|---|---|---|---|---|
| 00 | 167 | 13.8 | 2.0 | 57% | 32% |
| 01 | 170 | 17.3 | 5.0 | 74% | 26% |
| 02 | 169 | 18.7 | 2.1 | 72% | 28% |
| 03 | 167 | 9.1 | 14.3 | 33% | 67% |
| 04 | 163 | 18.9 | 7.0 | 80% | 20% |
| 05 | 165 | 8.6 | 6.5 | 38% | 62% |
| 06 | 159 | 10.6 | 8.5 | 40% | 60% |
| 07 | 126 | 18.2 | 2.0 | 75% | 25% |
| 08 | 147 | 19.7 | 2.8 | 80% | 20% |
| 09 | 169 | 23.0 | 3.4 | 88% | 12% |
| 10 | 159 | 19.5 | 1.3 | 77% | 8% |
| 11 | 123 | 23.6 | 2.5 | 80% | 11% |
| 12 | 170 | 18.8 | 1.8 | 70% | 11% |
| 13 | 152 | 22.3 | 1.8 | 87% | 13% |
| 14 | 102 | 18.7 | 4.4 | 82% | 18% |
| 15 | 115 | 21.0 | 4.8 | 85% | 15% |
| 16 | 168 | 21.6 | 2.4 | 84% | 16% |
| 17 | 166 | 21.0 | 2.0 | 90% | 10% |
| 18 | 169 | 23.4 | 1.8 | 86% | 14% |
| 19 | 168 | 23.1 | 1.6 | 87% | 13% |
| 20 | 169 | 12.3 | 0.8 | 52% | 48% |
| 21 | 171 | 7.8 | 1.6 | 29% | 70% |
| 22 | 167 | 10.0 | 0.6 | 30% | 59% |
| 23 | 169 | 5.8 | 0.4 | 22% | 78% |

The dips at 03 to 06 and 20 to 23 are the lab's night windows and their locks. By day: 11-01 22.1%, 11-02 15.0%, 11-03 14.7% mean inference busy.

How the card is used while the loop plays (servers' own stats, `gym-loop/games/server-*.json` and `judge-server-*.json`, 15 stage-1 gates and 50 segments): the prior server answers 2.04 rows a batch in practice (replay 3.2 ms a batch, 28% busy, 1.6 ms a row), 4.7 rows a batch in a gate (1.4 ms, 17.7% busy, 0.29 ms a row) and the judge server 15.8 leaves a batch (1.4 ms, 19.6% busy, 0.082 ms a leaf). The server takes whatever has arrived (no wait, at most 128 rows, one captured graph per size bucket); a search asks one leaf at a time, so a batch is as large as the fights in flight (6 processes times K: 2 in practice, 32 in a gate). Calls a game in a gate: 628 prior, 2,440 judge.

The trainer (`gym-loop/trainer/checkpoints.jsonl`, 145 checkpoints, `train_s` and `idle_s` are cumulative; code `rl/gym_loop_train.py`). Busy is `train_s` (time inside the training steps: batch build, forward, backward, update); idle causes are logged every 15 s.

| window | wall | busy (card) | idle, "fresh" (all rows used 4 times) | idle, paused by a lock | not logged |
|---|---|---|---|---|---|
| since 10-30 (c0001 to c0145) | 394,858 s (109.7 h) | 179.4 s (0.045%) | 345,240 s (87.4%) | 42,375 s (10.7%), and 1,455 s (0.4%) with no data yet | 5,609 s (1.4%) |
| last 3 days (c0048 to c0145) | 260,294 s | 114.9 s (0.044%) | 221,625 s (85.1%) | 25,050 s (9.6%) | 13,504 s (5.2%) |
| last day (c0105 to c0145) | 85,707 s | 43.0 s (0.050%) | 80,250 s (93.6%) | 5,070 s (5.9%) | 344 s (0.4%) |

Idle causes, ranked, since the start: fresh (waiting for new rows) 345,240 s; paused for `judge-v0` 10,125 s; `reset-a` 7,500; `pillage-fix` 5,340; `gym-loop-gate` 2,985; `pause` 2,085; `d49-prefilter` 1,815; `gym-gate-pair` 1,710; `d48` 1,605; `test-funnel` 1,545; then `f16-gate` 1,485, `no-data` 1,455, `funnel-stall` 1,410 and others under 1,200 s. Each 30-minute checkpoint trains about 38 steps of 256 rows (9,700 samples) in 1.0 to 1.3 s of card time, a rate of 8,140 samples a second of training time; each checkpoint interval brings about 2,400 new rows, and the cap is 4 passes over each new row. At the buffer's recent intake (84,000 rows a day, 90.7% trainable) four passes cost about 40 s of card time a day.

## 4. One judge leaf against one rollout

Sources: the benchmark (section 6, 20 starts, 2 processes), the gate games (62,397 judge-v0 games on A1 boss starts), the kind-weights pass (a3-v1, A1 boss), the judge servers' stats, and the earlier judge board (`lab/results/fight-gym/2026-10-30-judge`, 2,000 games a side, 6 processes, lockstep 64). No record times a rollout on its own; its cost below is the difference between two configs and is derived.

| quantity | a3-v1 (rollout leaf) | judge-v0 (judge leaf) | source |
|---|---|---|---|
| CPU ms a simulation, 20 starts, 2 processes | 5.14 | 1.70 (0.33 of a3-v1) | benchmark |
| own-second ms a simulation, A1 boss | 4.56 (4.55 s over 998 sims, weights pass) | 1.87 (5.52 s over 2,958 sims, gates) | records |
| earlier judge board, ms a simulation, A1 boss | 5.2 (0.162 s over 31.3 sims a decision) | 1.43 (0.132 s over 92.3) | 2026-10-30 judge board |
| simulations a game, A1 boss | 998 | 2,958 | records |
| CPU-seconds a fight, same 10 starts, 2 processes | 6.9 (scaled from own seconds) | 7.6 (scaled) | benchmark |
| wall for 20 fights, 2 processes | 90 s | 147 s | benchmark |
| card time a judge leaf | | 0.63 ms at 4.5 leaves a batch (benchmark); 0.082 ms at 15.8 (gates); 0.023 ms at 41 (judge board) | server stats |
| a process's wait for the judge a leaf | | 1.0 ms (benchmark, 62.7 s over 62,703 leaves); 0.34 ms (judge board, one process, 31.0 s over 91,019) | process stats |
| encode on the CPU a leaf | | about 0.1 ms | `docs/rl/JUDGE.md` section 4 |

Derived: a rolled-out leaf costs about 3.4 CPU-ms more than a judged one (5.14 minus 1.70). A judged leaf costs about 0.1 ms CPU to encode plus its share of a card batch, 0.02 to 0.6 ms depending on how many fights share the batch. The judge saves CPU at any batch size but its wall time depends on batch size: at 2 processes holding 10 fights each, 20 judge fights took 1.6 times a3-v1's wall; in a gate (6 processes, 32 fights each) the two arms play equal fights an hour (`JUDGE.md`: 4,772 against 4,802 an hour on the judge board).

## 5. What a gate costs

Source: `gym-loop/games/steps.jsonl` (wall and process CPU a step, means over gate steps with no stop), `judge-server-gate-*.json` and `server-gate-*.json` (server CPU), 6 processes, K 32, judge-v0 at A1 boss starts.

| gate | games | wall | process CPU-s | server CPU-s | CPU-s a game | steps measured |
|---|---|---|---|---|---|---|
| stage 1: the rotating pair, candidate only (the incumbent's games are kept) | 400 | 423 s (7.1 min) | 1,743 | 131 | 4.7 | 112 |
| stage 2: the other 1,600 games | 1,600 | 1,386 s (23.1 min) | 6,537 | 396 | 4.3 | 10 |
| a 2,000-game gate (stage 1 then 2) | 2,000 | 1,809 s (30.2 min) | 8,280 | 527 | 4.4 | |
| the incumbent's own 2,000 games, once for each incumbent | 2,000 | 1,786 s (29.8 min) | 8,569 | about 530 | 4.3 | 2 + 4 |

128 candidate gate steps have run since 10-30: 112 whole stage-1 steps (400 games), 10 whole stage-2 steps (1,600 games; each followed its stage 1), 6 stopped part-way. Candidate gate steps a day: 41, 26 and 18 on 11-01, 11-02 and 11-03; gates were 27%, 29% and 18% of the loop's CPU on those days.

## 6. The benchmark (records silent for x4 and judge-v0 off the A1 boss)

Protocol. Twenty saved starts from the loop's start set, chosen by a fixed hash: 10 Act 1 boss and 10 Act 2 elite; game 0 of each; the incumbent (version 2) as the network; the loop's own gate path (`gym_loop.gen_game_steps` in the loop's worktree code, prior on the card, judge on its own server for judge-v0), 2 processes, K 32, BelowNormal. QUIET.lock line `bench-config` (Windows pid, written by the job itself) from 10:29:49Z to 10:50:45Z; GPU_OK taken once the loop had let go of it; the loop paused for the window and the lab's filler did not start, but the lab's running job (real-game fight batches, about 5 to 6 cores: two whole batches inside the window, 2,536 and 2,929 CPU-s in 540 and 505 s) carried on beside the benchmark, so these timings are under that load on 16 logical cores; `nvidia-smi` utilisation once a second to a file; no night active. The lock was held 21 minutes against the 20 allowed: a3-v1, judge-v0 and x4 ran on all 20 starts (10:29:49 to 10:39:14Z), then x16 on all 20 would not have fit, so it was stopped at its start (25 s gap) and re-run on 10 of the same starts (5 boss, 5 elite; 10:39:57 to 10:50:45Z). Rows and stats stayed in a scratch folder, not committed.

| config | fights | A1 boss own s | A2 elite own s | CPU-s a fight | wall | sims a fight | CPU ms a simulation | card busy (nvidia-smi mean) |
|---|---|---|---|---|---|---|---|---|
| a3-v1 | 20 | 7.13 | 5.27 | 5.90 | 90 s | 1,148 | 5.14 | 3.3% |
| judge-v0 | 20 | 10.31 | 9.74 | 6.32 | 147 s | 3,726 | 1.70 | 28.3% |
| x4 | 20 | 24.88 | 16.61 | 19.78 | 302 s | 4,740 | 4.17 | 3.6% |
| x16 | 10 (5 + 5) | 134.8 | 79.1 | 99.75 | 650 s | 20,112 | 4.96 | 5.3% |

Same 10 starts for all four (the x16 set): CPU-seconds a fight 6.9 (a3-v1), 7.6 (judge-v0), 23.5 (x4), 99.75 (x16, measured; the other three scaled from own seconds by their CPU to own-second ratio). So x4 is 3.4 times and x16 14.5 times a3-v1 in CPU; own seconds on those 10 starts: 7.2, 12.0, 24.7, 106.9. Idle at the end of each run (the other process waiting for the slower one): 54.7 s a3-v1, 90.2 judge-v0, 187.8 x4, 229.4 x16 (process-seconds), so wall times are longer than CPU per fight suggests. The card's servers: prior 4.5 rows a batch (3.5 ms) for a3-v1; for judge-v0 the prior 1.6 rows (2.6 ms) beside the judge's 4.5 leaves a batch (2.85 ms, 26% busy); x16's prior 2.35 rows (3.1 ms, 6.5% busy). The 20 starts run longer than the population (a3-v1 7.1 s on the boss ones against 4.55 in the weights pass) and x16's two long boss fights took 282 and 308 own seconds, so read these as a same-starts comparison, not as kind means; section 1 has the means.

## What the numbers say

1. A practice fight costs 54 own seconds (45 CPU-s) and yields 20 rows, 2.3 CPU-s a row; Act 1 boss fights are 36% of fights and 53% of the seconds, Act 1 hallways 25% of fights and 10% of the seconds, and a row costs 1.7 s (A1 hall) to 3.8 s (A2 boss) of the fight's own seconds.
2. x16 costs 17 to 23 times a3-v1 per fight in every kind (14.5 times in CPU on the benchmark starts), x4 about 3.4 times, and judge-v0 at 3 times the simulations costs about a3-v1's CPU a fight (6.3 against 5.9 CPU-s) because a judged simulation is 1.7 CPU-ms against 5.1 for a rolled-out one.
3. The card is 17% busy on average (25% while the loop plays: 23% in practice, 35% in gates, 0 between steps), in batches of 2 to 16 rows; the trainer holds it about 1 second in every 30 minutes (179 s in 110 hours), and 87% of its time it waits for new rows, not for the card.
4. A 400-game gate costs 7.1 minutes and 1,874 CPU-s and a 2,000-game gate 30 minutes and 8,807; gates are a quarter of the loop's CPU since 10-30 and make no rows.
5. Over the last three whole days the 16 cores ran at 49.9% of capacity on the job ledgers: the loop 35% of the CPU used, the lab's daytime jobs 53%, the nights 11.5%.

## Not measured

- x4 and judge-v0 per kind off A1 boss and A2 elite (hallways, A1 elite, A2 boss); x16 on all 20 starts (10 played; two heavy-tailed boss fights); more than one draw a start.
- Judge-v0 at x4 or x16 simulation counts: only arithmetic (x16's 20,112 simulations at 1.7 CPU-ms would be about 34 CPU-s a fight against 100), not played.
- A rollout timed on its own (derived from two configs); card time at more than 60 rows a batch (`docs/rl/GPU_INFERENCE.md` says 128 rows cost little more than 2; not re-measured); the card's compute occupancy (the counter is engine time, sampled once a minute, so a one-second burst such as the trainer's is not seen: its time comes from `train_s`).
- Machine CPU percent over a whole day (the machine log covers the nights only); lab CPU by the day a job ended; the trainer's own CPU, checkpoint writing and the gate pre-filter scoring (the 1% to 5% not logged above).
- Disk and memory pressure; the effect of a larger K in practice (K 2 is set so that a stop loses few fights).
