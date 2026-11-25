# Analyst C: process, machine and money (2026-11-18)

Written 2026-11-18 by analyst C (Opus), read-only. Covers 2026-10-22 00:00Z to 2026-11-18 20:10Z (27.8 days, five Claude weeks; the allowance resets Tuesdays 21:00Z). Paths are under `D:/spireline/`. Scripts: `referee/backlog/analysis-2026-11-18/scripts/C-machine.py`, `C-yield.py`, `C-fightloop.py`, `C-handoff.py`.

Words used once: a **core-hour** is one of the PC's 16 processor threads busy for an hour (8 physical cores, so 16 threads are not twice the work of 8). A **judgement** plays the candidate and the champion on the same dealt games, usually 2,000 pairs, and a fixed **keep rule** decides; a **promotion** makes the candidate champion. An **Act 3 kill** is a run that beats the first Act 3 boss, now the measure of progress. A **lane** is one Claude worker on one brief. A **budget point** is 1 in 100 of the week's Claude allowance. The **fight loop** is the separate fight-brain trainer. **Plain runs** are the champion playing ordinary games as data.

## The short answer

- **Machine:** about 5,000 core-hours are logged of the PC's 10,700 thread-hours. At least 900 of them (18 in 100) bought nothing: they failed, were repeated, or fed nothing that reached a champion. Up to 1,900 (38 in 100) counting work of doubtful use. No log accounts for the other 5,700 thread-hours.
- **Results:** 16 promotions, not 18 (generation numbers 4 and 10 were skipped). One promotion moved Act 3 kills by more than its own test's noise: generation 16, the first refit of the run value on plain runs. Generation 17 moved them nominally.
- **Money:** every full week spent 93 to 96 of its 100 points; the week's limit was raised about 15 times in four weeks and never stopped the spending.
- **Pattern:** failures came back wherever the fix was a written rule rather than code.

## Where the machine went

| Purpose | Core-hours | What it bought |
|---|---|---|
| Plain runs (data), 11-14 on | 1,104 (82,861 runs) | the data of generations 16 and 17; then four refused refits |
| Fight loop playing (estimate: 6 threads while playing, 142 h) | ~850 | fight brain v2 (in the champion 11-02), v3 (in the champion only 11-18) |
| Judgements (the lab's train job) | 648 | 40 verdicts, 16 promotions |
| Real-game nights and scoring | 613 | real-game checks to 11-06; 209 of it eight failed retries |
| Self-play practice | 580 | generations 8 and 9; after 11-01 two refused candidates |
| Fidelity bug hunting | 577 | the copy's agreement with the game; 406 of it after the owner's 10-30 cut |
| Teacher with search (labels) | 566 (3,012 runs) | the data of generations 14 and 15; dropped as no better than its student |
| Benches and builds | 70 | speed figures |
| **Logged total** | **~5,000** | of 10,691 thread-hours |

[`referee/LAB/runner.log` via `C-machine.py`; the run ledgers `referee/run-cheap/ledger.jsonl` and `referee/run-teacher/*/ledger.jsonl` (the lab's teacher hours agree with the runner's within 3 in 100: 1,382 against 1,340); fight-loop phases from `referee/gym-loop/gpu.jsonl`. Before 11-03 the runner logged only wall time: 1,141 of the lab's 3,828 core-hours are wall times the CPU-per-wall ratio measured after 11-03.]

| Week | Logged core-hours | Of the PC's threads | Promotions | Moved Act 3 | Budget used | Fork commits |
|---|---|---|---|---|---|---|
| W1 10-22 to 10-27 | 334 | 15 in 100 | 6 | 0 | 96 | 510 |
| W2 to 11-03 | 1,277 | 48 | 3 | 0 | 93 | 156 |
| W3 to 11-10 | 1,320 | 49 | 2 | 0 | ~94 | 103 |
| W4 to 11-17 | 1,822 | 68 | 4 | 1 (gen 16), arguably 2 (gen 17) | ~96 | 105 |
| W5, one day | 215 | 58 | 1 | 0 | 5 so far | 1 |

[Promotions: `referee/agent/promotions.tsv`; Act 3: `C-yield.py` over each promotion's judged games paired by seed (`gen*/candidate-*/arms/*/runs.jsonl`); budget: the last weekly reading in `referee/backlog/HANDOFF.md` (the D52 tool `spireline/tools/usage_ledger.py` and the "Budget N of M" lines); commits: fork main, merges excluded.]

**Yield:** 3.2 promotions per 1,000 logged core-hours, but 0.2 to 0.4 per 1,000 for promotions that moved Act 3 kills or wins. Gen 16 had 66 Act 3 kills against the champion's 32 on 1,700 pairs (+2.1 in 100); gen 17 52 against 40 on 800 (+1.4); gen 18 158 against 159 on 2,000. Gens 1 to 13 had 0 to 6 per block on either side and were promoted on floors and Act 1 or 2 measures. Wins stayed near 1 in 1,000: 4 in 4,500 pooled recent games [`gen18/candidate-fight-v3/promotion.json`, frontier record].

**The GPU was not the limit.** The fight trainer did 0.55 hours of GPU training in 19 days and logged 219 hours waiting for fresh fights [`referee/gym-loop/trainer/checkpoints.jsonl`, cumulative counters]. The card was busy about 77 of the 312 sampled hours [`gpu.jsonl`]. The round script's four fits took 8.7 GPU-hours. All four candidates were refused, and 3.5 of those hours went to a fit discarded unread [`logs/gym-loop/round-loop.log`].

**Idle and blocked:** the lab's main slot was paused 111 hours (54 by other heavy processes, 34 by `LAB/PAUSE`, 19 by landings, 4 by the keyboard). The fight trainer was held about 98 hours by other jobs' QUIET.lock lines: 40 by the score job, about 32 of them in its eight failed attempts, and at least 42 by 47 different hand-run tags. The fight loop was switched off 124 hours (11-11 to 11-14, 11-15 to 11-17). [`C-machine.py`; `referee/gym-loop/loop.log`.]

## What went right

- **The copy of the game is trustworthy:** 998 of 1,000 moves agree with the real game (DECISIONS D8, the paper's fidelity section). W1's 510 fork commits and the bug hunting bought this, and every later figure depends on it.
- **One step moved the goal measure.** Refitting the run value on the champion's own plain runs gave generations 16 and 17. The champion's Act 3 kill rate went from about 2 in 100 (generation 15 as champion, 32 of 1,700) to about 8 in 100 (generation 17, 159 of 2,000). In the copy, the Act 2 boss went from 2.2 in 100 (8,104 runs, D44) to about 23 (4,500 pooled runs). [`C-yield.py`; `promotion.json`. Whether different seed blocks compare is analyst B's question.]
- **Some failure kinds were fixed in code and have not come back.** The lab now stops a job kind after two failures and writes an alert; the guard is on self-play markers (the 10-31 unjudgeable training, 37 core-hours); the round script no longer reuses a fit by name; the student job keeps the champion's heads (fork `a6258302`). [`referee/LAB/jobs.json` `_note`; HANDOFF 713-714; HANDOFF alert block.]
- **The process sometimes caught itself.** D43 and D44 (11-01) found the idle practice, the unwired fight brain and a machine 44 in 100 idle; the Tuesday sceptic review (11-18) found v3 unused for nine days [DECISIONS D43, D44; HANDOFF line 14].

## What went wrong

**1. Machine work that bought nothing (about 900 core-hours, conservative).**

- **The score job retried silently** (11-05 to 11-09): 8 failures, 209 core-hours, and the fight trainer held 40 hours [runner.log; DECISIONS line 1389].
- **Self-play ran on after D43** (11-01 09:22Z) said more practice "adds nothing": 374 core-hours (486 since generation 9's promotion on 10-29). It fed two candidates, both refused, one at the 200-game smoke look. 1,828 of the filler's 4,496 runs never reached a data shard [HANDOFF line 528]. Generations 11 to 14 all reuse generation 9's run-value fit [`gen11..gen14/*/agent.json`].
- **The fight loop trained on after v3** (11-09 12:00Z to 11-18 16:05Z), improving a part no run player carried. About 47 hours of play (roughly 280 core-hours), 44,860 fights (61 in 100 of all it ever played), 51 gate verdicts, no promotion [`C-fightloop.py`]. When v3 finally went into a run candidate, Act 3 kills were 158 against 159.
- **Smaller:** seven training runs on 10-31 that could not be judged (37 core-hours); one block replayed for a candidate identical to the last (cheap-v3c, 4 core-hours).

**2. Work of doubtful use (about 1,000 more).** Fidelity hunting after the owner's 10-30 cut: 406 core-hours of kits for the top twelve groups while fixes landed "a few a day" against about 4,200 open groups, switched off only on 11-09 [DECISIONS D39, D57 addendum 1]. The teacher with search: 566 core-hours (11-11 to 11-15). Its two candidates moved Act 3 by +0.4 and +0.1 in 100, and it was dropped because "the teacher plays no better than its student" [DECISIONS D59 addendum 3].

**3. The judge's rule kept moving.**

- **Three keep rules in 26 days.** v1 (floors-led) promoted nine champions with 0 to 2 Act 3 kills per 2,000 games. v2 came on 11-05: five hard-coded checks were added and then made advisory (D64, 11-16), and the attempt cap went advisory on 11-17. v3 came on 11-18.
- **Two blocks were re-read under a new rule** (E1, E12-r3).
- **Generation 18 was judged under v2** because a worker's marker beat the switch to v3 by two minutes. v2 promoted it on floors; v3 would have refused it; it stands by the orchestrator's call. The fix is a memory note, not code [HANDOFF line 16].
- **The round loop's refits were refused four times in a row** (cheap-v3, v3b, v3c, v3d): about 118 core-hours of judging, 8.7 GPU-hours, and three faults in the orchestrator's own script ("my script's fault", HANDOFF 703, 713, 714).

**4. Failures came back where the fix was a rule.**

- **The unwired consumer.** D44 (11-01) set "no trainer is built or kept without its consumer wired first". On 11-09 the watcher that queued fight brains as run candidates was stopped and forgotten, and v3 sat unwired for nine days [HANDOFF 14, 717].
- **Clock errors:** the orchestrator's times ran 1 to 2 hours ahead (10-25) and up to 13 hours ahead (10-26), and it misread the reset by 12 hours (11-03) [HANDOFF 231, 262; DECISIONS line 1218].
- **About a dozen operating rules live only in the orchestrator's memory notes:** the quiet-lock process id, the landing race, the publish lock, suite order, PAUSE stopping hand-started jobs, the presort moving the tree, marker timing, night logs deleted. A fresh worker does not carry them.
- **The owner found the silent failure** by asking "how was this missed" on 11-09.

**5. The budget was spent to the limit every week, and raising the limit was the routine.**

- **Every full week ended near the top:** 96, 93, about 94, about 96. D21 set 15 (10-22) and D36 set 30; about 15 raises took the weekly ceilings to 80, 95, 95 and 99.
- **Points per promotion:** 16, 31, 47 and 24 in weeks 1 to 4. Only W4's 96 points bought a promotion that moved Act 3.
- **Where the points went is mostly unknown.** The October usage study found 86 in 100 of the cost is re-reading long contexts. The D52 ledger attributes only 14 of 93 points (W2) and 14 of 94 (W3) to named work; 79 to 80 are the orchestrator's or unreported. From 11-05, 51 of 101 worker lines say "usage at start not given", and nothing since 11-10 cites the ledger.
- **One long conversation, probably.** Memory notes created under the orchestrator's current conversation id date from 10-15 to 11-18. That suggests one long conversation, not D46's fresh start at each reset (uncertain: ids may survive a resume).
- **Checking moved back to the dearest model.** In W3 the lines cite the cheap checker 46 times and the orchestrator's own hand-checks 7 times; in W4 it was 7 and 18.

[`usage_ledger.py` output; DECISIONS D21, D36, D41-D51, D60-D65; HANDOFF 691-720.]

**6. The writing outgrew its readers.**

- **The documents:** HANDOFF is 188,000 words; its sections 1 to 10 still describe 10-22, and the orchestrator's lines average about 1,150 characters (266 lines, W2 to W5). DECISIONS is 66,000 words, 45,700 of them since 11-05; D58 alone has 27 addenda. The paper is 31,000 words over 80 commits. 355 Spireline commits, nearly all documents.
- **Nobody read the signals.** The runner log held the score failures and the clock signal ("nobody read it until D44", HANDOFF 422). The fight-plateau alert has been open since 11-11, although its own text demands a same-day diagnosis. No decision since 11-10 cites `promotions.tsv`.

**7. No real-game check since 11-06.** The nights became monthly and the score job was switched off (11-09). The real game last read 7.8 in 100 at the Act 2 boss, against the copy's 22 [paper line 216]. Champions 14 to 18 have never played the real game.

## What the evidence cannot tell us

- **What the other half of the machine did.** No log records the CPU of hand-run work (gates, by-hand judgements, lanes' measurements, W1's kernel proofs), so the files cannot split the 5,700 unlogged thread-hours into work and idle. 16 threads on 8 cores also overstate what an idle hour could have bought.
- **Exact figures for two estimates:** the fight loop's CPU (6 threads while playing) and the lab's CPU before 11-03 (1,141 core-hours).
- **The budget by purpose** (building, measuring, writing, orchestrating). The ledger lost its inputs on 11-05, and D60's "writing under a quarter" was never measured.
- **Whether W4's Act 3 gain is real.** Different seed blocks, no real game. If it is block noise, W4 bought nothing on the goal either (analyst B).
- **Money beyond the subscription.** $206 of a $250 cloud credit was spent in W1 (D30). Electricity and the price of a point are not in the files.
- **What the fidelity work was worth** against the same hours spent on learning.

## What we should do

**Change 1: let code keep the books and the rules.**

- **What:** every heavy job, including gates and by-hand judgements, runs through the lab runner or a thin `lab run --tag` wrapper that logs CPU, wall time, purpose and consumer. A script writes each lane's usage at start and end. A judgement's marker carries its keep rule. A trainer whose latest output is in neither the champion nor a queued run candidate within 24 hours pauses itself, and a promoted fight brain queues its own run candidate.
- **Cost:** two Sonnet lanes (4 to 6 points), Python only.
- **Effect:** closes the classes behind most of the 900 wasted core-hours (the retries, the unwired loop, the late self-play) and the gen-18 race, and makes the unlogged half visible.
- **We'd know within a week** if 90 in 100 of machine hours appear in a log with a purpose.

**Change 2: register each line of work before it starts.**

- **What:** each line states its expected Act 3 gain per 100 (pooled fresh seeds) and its stop (two refusals or a date). Keep rule v3 stays frozen for four weeks. The ceiling and the plan are not changed mid-week except to fix a failure.
- **Cost:** one Opus design pass (about 2 points).
- **Effect:** the four refused refits would have stopped after two (about 70 core-hours and the script faults saved), and self-play and the search teacher would have stopped at their first flat result. Judgements per promotion (now 40 for 16) fall.
- **We'd know** if every judgement names its registered line and no rule or ceiling moves.

**Change 3: cut what the orchestrator writes and re-reads by about two thirds.**

- **What:** a fresh conversation each day from a state file of at most two pages. HANDOFF split into an archive and a live page of at most three pages. Lane lines of at most five lines. DECISIONS for the owner's calls only. The paper as a one-page weekly scoreboard. Checks back on the cheap checker.
- **Cost:** about 1 point (a Haiku pass to split the files).
- **Effect:** re-reading is 86 in 100 of cost, so the same lanes should fit in about 40 to 50 points a week instead of 95. W5's first day (5 points, two lanes landed, one promotion; HANDOFF 717-720) is the only test, and it is one day.
- **We'd know** if the week ends under a ceiling set once, with its registered lanes done.

**What to stop outright:**

- Raising a week's ceiling once it is set.
- The fight loop and its gate on the fixed board of old fight starts, until a whole-run test is its gate (51 rejections in nine days; v3's +1.4 points at the gate was +0.05 at Act 3).
- Refitting the run value on more of the same plain runs (four refusals in a row).
- Heavy work run by hand outside the lab.
- Per-landing decision addenda, long orchestrator lines, and orchestrator re-checks of what the checker confirmed.
- Restarting self-play, the search teacher or bug hunting without a registered target.

**A lean week, if the owner continues:**

- **Budget:** ceiling 45, set Tuesday and kept.
- **Lanes:** at most three, each registered with an Act 3 target and a stop date: one Opus design of the next lever, one Sonnet builder, the Haiku checker. The orchestrator works in one fresh conversation a day of about ten turns, with status by script.
- **Machine:** plain runs only as the registered experiment needs; v3 judgements only of registered candidates on pooled fresh blocks; the fight loop's gate off; one 500-game real-game check of the champion in a quiet window (about 25 core-hours, 1 in 100 of the week). The rest idle, with no invented filler.
- **Writing:** one page on Tuesday.
- **Test:** the registered candidate's pooled Act 3 verdict, spend under 45, and 90 in 100 of machine hours logged.

**An orderly stop, if not:**

- **Freeze:** the owner halts the lab runner and the fight loop and disables the scheduled tasks; nothing is deleted.
- **Keep:** fork main (pushed), champions 17 and 18, `promotions.tsv` with every `promotion.json` and judged arm, `run-cheap/15..18` and the run-teacher stores, fight players v1 to v3, the human-bar tooling (exam fifth untouched), PLAN, DECISIONS, the paper, HANDOFF, `runner.log` and the `jobs.json` backups.
- **Record** (about 3 points and 30 core-hours):
  - A final scoreboard on one pooled fresh block: Act 1, 2 and 3 kills and wins per 100, with n.
  - One 500-game real-game check, so the last figure has a real counterpart.
  - This cost table.
  - The open questions (fight-brain swaps under v3, lane N's design).
  - A two-page note on how to restart.
- **Hand over:** offer upstream PRs for the fidelity fixes where they help (the owner's call).

## What would change this conclusion

- **The figure within a week:** the next registered candidate's Act 3 kills plus wins per 100, on about 4,000 pooled fresh pairs. It must not be another value refit. At +1.0 or more, with its bound above 0, the lean week is worth repeating. Flat at half the budget, an orderly stop is the rational call.
- **If W4's jump holds up:** a pooled fresh comparison of generation 17 or 18 against 15, with a real-game check agreeing, may show the jump from about 2 to about 8 in 100 is real. Then plain runs bought the project's only measured progress, and the case moves towards feeding that step, not stopping.
- **If it is block noise:** all five weeks bought no goal movement, and the case for stopping is stronger.
- **If the books show the orchestrator's share is small,** change 3 saves less than I claim.
- **If three registered lanes cannot finish at 45 points because the orchestrator was the throughput,** the cut was too deep.
