# Judge build 1: margins in both judges, the Act 3 arrival exam as a measurement, the S1 run script

Lane: build lane 1 (Sonnet), 2026-11-22. Brief `BRIEF-judge-build-1.md`, design `DESIGN.md` sections 3 and 4. No rule changed: route S is not built.
Terms: **arrival** = a run that reached the first Act 3 boss; **S1** = the arrival exam of the design; **ruler** = the set of positions S1 plays;
**±** = plus or minus 2 standard errors (SE) unless marked.

## What landed on fork main (fast-forward, Python-only gate)

| step | commit | what |
|---|---|---|
| 1 | `a779235d` | margins in the run judge and in the fight gate's rule v5; the boss-cell flag |
| 2 | `ac1437cd` | the arrival ruler's builder, the exam's reading, `test_arrival_exam.py` |
| 3 | no commit | `judge-design/S1-v5.sh` (this folder), not run |

Suite counts (full Python suite, `gate-py.sh` FULL=1, emulator Python, base 3d4bd0fd): **6,502 tests before** (6,501 on c986a088 plus the one
test 3d4bd0fd added), **6,513 after step 1** (11 tests added), **6,540 after step 2** (27 added). At each tip 15 tests fail, all among the 60 of
`baseline-python-failures.txt`: 0 new failures, 0 flakes. Evidence: `logs/fork-tests/a779235d.txt` and `ac1437cd.txt`. Landed in order under `main.lock`,
fast-forward only; `origin/main` had not moved between the gate and the merge, so no rebase was needed.

## Step 1: margins (no rule change)

**Run judge** (`tools/lab/keep_v2.py`, `rl/gen_loop.py`). The verdict (`promotion.json` `keep_v2`) gains:
- `margins`: for B1, B2, B3a, wins, deep_f, floors and arrivals (first Act 3 boss): each arm's count, the paired difference (per 100 runs; floors in
  floors a run), its SE, ±2 SE, and the discordant pairs (`cand_ahead`, `base_ahead`).
- `per_arrival`: each arm's pass rate per 100 arrivals with its binomial SE, and the difference with the two SEs combined as independent. It is also
  written at the top of `promotion.json` (`compare_arms`).
- The ledger's `guard` cell shows ± beside deep_f and the floors and carries the margin parts. The wins co-primary now reads `wins guard ok|off|FAILS`
  so that `wins 1/3 -0.18 ±0.26` is the count. Routes, checks, funnel looks and the futility stop are untouched.

Checked on the stored v5 block (`gen21/candidate-fight-v5` against the champion on E21-r2, 1,100 pairs, min gain 0.5). The line now reads:
`... deep -1.27 ±1.74 (lower ...) K2 372/347 | floor +0.90 ±0.74 (99% upper ...) | ... | B3a 58/70 -1.09 ±1.69 | wins 1/3 -0.18 ±0.26 | arrivals 263/240 +2.09 ±2.66 | per arrival 22.1/29.2 -7.1 ±7.8 | B1 828/797 +2.82 ±2.81 | B2 372/347 +2.27 ±3.08`.
Every figure equals the design's example line.

**Fight gate, rule v5** (`rl/gym_gate.py`, `rl/gym_loop.py`). `strat_read` adds `win_pm2se` and `hp_pm2se` to every cell and part; `boss_flags` lists the
boss cells at -3 points or worse (`flags` on every v5 verdict row; `FLAG ...` in the stage line and in the promotion line); the stage line prints each
part and each cell with ±. `v5_decide` never reads a flag: a flag is information.
Checked on the stored verdicts of `gate/verdicts.jsonl`: **c0390 flags nothing; c0384 flags `act3-boss1-73` (-4.03 ±3.67) and `act3-boss2-78` (-3.75 ±5.23)**,
the two cells the design names (-4.0 ±3.7 and -3.8 ±5.2). c0397 flags `act3-boss2-73` (-4.38 ±4.34).

Tests: `test_keep_v3.py` `MarginsTests` (5), `test_gym_gate_v5.py` `Margins` (4) and two gate tests. Two assertions that read the ledger line were changed
(`floor -1.95 ±`).

## Step 2: the arrival exam, built and tested as a measurement

**Verification (the brief's first condition): the judge's arms load into the gym's replay step. Yes.** 20 arrivals chosen by a fixed hash across the three
blocks, replayed to the boss door with the champion's own agent on the engine the arms were played on (`old`; their summaries name none), 6 processes,
BelowNormal, 412 s of wall clock:

| block | rows | arrivals (ruler rows) | replayed | matched their row | mean seconds a replay |
|---|---|---|---|---|---|
| E21-2026-11-21 | 2,000 | 437 | 6 | 6 | 55.9 |
| E21-2026-11-21-r1 | 2,000 | 450 | 7 | 7 | 61.6 |
| E21-2026-11-21-r2 | 1,100 | 240 | 7 | 7 | 63.2 |
| total | 5,100 | 1,127 | 20 | 20 | 60.2 |

"Matched" is the gym's own test (map path, cards taken, rests up to the boss; every wanted position reached). All 5,100 rows were played with the prior on
the GPU server and the replay uses the in-process prior, so a mismatch was possible; none occurred in 20 (a one-sided 95% lower bound on the match rate
of 86%). The champion's selection block (E20) is left out of the ruler by rule: `champion_arms` reads `promotion.json` `seed_block`.

**Ruler's expected size:** 1,127 first-boss starts (437 + 450 + 240) and 282 second-boss starts (102 + 110 + 70: the arrivals that also entered the
second boss) = 1,409 starts if every replay matches; at the 86% lower bound about 970 first-boss starts. The exact count is in `meta.json` once built.
Cost to build: 1,127 x 60.2 s = 18.8 process-hours, about 1.6 h on 12 processes (the design said 1.8 h).

**What was built** (`rl/act3_starts.py`, new commands `arrivals` and `arrival-exam`; `rl/gym_gate.py` `arrival_exam`, `arrival_js`, `arrival_report`):
- `arrivals`: reads the champion's arms (`arms/*` minus the blocks it was selected on), makes one `fight_gym._replay_task` per arrival (the second boss's
  position too when the run entered it), runs them in the gym's own spawn pool (`fight_gym.MAX_PROCS` raised to `--procs`), keeps a start only when its
  replay matched, writes `starts-arrival.jsonl` (+ byte index, lite list), `meta.json` (counts per block, match counts, reasons, the ruler's hash),
  `exclude_runs.json` (every run behind a start, the `fight_exam.exclusion` shape; merging it into the loop's `exam/exclude_runs.json` is the loop owner's step:
  the file is only written beside the ruler) and the raw `replays-<block>.jsonl` (resumable: a replay with a row is not played again). `--limit N` only checks
  that N arrivals replay and writes `verify.json`, no ruler. Arms another agent played are refused.
- The ruler's hash: sha256 over the rule's name and, per start in id order, the start's id and the hash of its document. File layout, order and annotations do
  not change it; `load_ruler` recomputes it and refuses an edited file.
- `arrival-exam`: the candidate's and the champion's fight networks (any folder with `combat_policy.pt` and `model.json`: an agent folder or a gym player)
  play the ruler, config `a3-v1`, CPU prior, 6 draws a start, test k on draws 6k to 6k + 5, in the lockstep (`fight_exam.play_exam_tasks`), namespace `ar`
  (draws never shared with another experiment), the champion first and every game with a row kept. Stops under the gym's night window rule
  (`fight_exam.blocked_reason`: night, window 03:10 to 03:45Z, HALT, PAUSE, main.lock at a start, another's QUIET line), BelowNormal, one fight exam at a
  time (the exam's mutex). `--procs` default 12.
- The reading (`gym_gate.arrival_exam`): per-start mean survival difference (candidate minus champion, a capped game lost), averaged unweighted over the
  starts, SE over the starts; the report prints it with SE, ±2 SE, starts, games, draws, the ruler's hash, the 0.005 lower bound and the 95% upper bound with
  what each would mean (S1 holds at a gain of at least +1.0 passes per 100 with the lower bound above 0; a reversal when the upper bound is below 0), per
  cell, and the second-boss starts for the record. No rule reads any of it.

Tests: `tests/python/test_arrival_exam.py`, 27: the draw indexing, the statistic by hand, the SE over starts (not games), unweighted starts, the pairing,
capped games, the bounds and what they read as, the report, the replay-match filter, the second-boss rule, the arm selection, the hash, a written ruler
and its edit check, `arrivals` end to end (replay pool replaced) and `arrival-exam` end to end (lockstep replaced).

**Real-path smoke** (not a measurement): the exam driver was run once, one process, on a four-start ruler built from the verification's replays, one
draw, `gen21/candidate-fight-v5` against `gen20/candidate-chain`: 8 games in 43 s, report and `results.json` written. The numbers are meaningless (4
starts); it shows the agent folders load as players, the CPU prior plays, and the files are written.

## Step 3: the run script (not run)

`D:/spireline/referee/backlog/act3-week/judge-design/S1-v5.sh`: step 1 builds the generation-20 ruler into `gym-loop/arrival/gen20-candidate-chain/`; step 2 plays
v5's fight network against the champion's on it (test 0); writes `s1-v5/report.txt`, `s1-v5/results.json`, `s1-v5/s1.log`. Exit 0 done, 3 blocked or stopped
(run again), 9 setup problem, otherwise the failing step's own status; nothing is piped. It holds a QUIET line `judge-s1` (`HOLD=0` to leave that to the
caller; `ALLOW_QUIET="tag ..."` to ignore the orchestrator's own line), refuses to start under others' lines, the night, PAUSE, HALT or main.lock, and needs a tree
(`WT`, default the lab's `wt-lab`) that holds the code (it greps for `arrival_exam` and the `arrival-exam` command; it never names a commit). The lab's tree moves
to fork main at its presort: until then give `WT` a worktree that has the commits.
Expected time: ruler about 1.6 h, exam 1,409 starts x 6 draws x 2 players = 16,908 games at 5.3 process-seconds, about 2.1 h on 12 processes (1.7 h for the
first-boss starts alone): **about 3.7 h**.

## Not done, not verified, choices to know

- Engine: the replays run on `old` (the engine of the judge's arms); the exam plays on the gym's engine (`core2`), as the gate does, from documents dealt on
  `old` (the human starts of the gate were dealt the same way). The engine library's hash is in the report.
- The match test is the gym's (path, cards, rests): it does not compare HP at the door (the rows carry none). 20 of 20 matched; the match rate on the whole
  ruler is in `meta.json` (`matched` of `arrivals`, `why` by reason).
- The SE of S1 (about 0.4 on 1,127 arrivals, from the gate's paired Act 3 games) is a projection; the first real figure is the run of `S1-v5.sh`.
- The exclusion list for the practice is written beside the ruler, not merged (the loop's tree is not mine). The ruler's runs are the judge's E-block seeds, which
  the practice's pools (plain-run stores) do not draw.
- QUIET line: the verification and the smoke ran under a `judge-build-1` line (removed after), as the standing rules ask; COMMON.md says the file is the orchestrator's.
  Say so if it should have been left alone.
- The full Python suite was run on the final tip of each step (counts above); nothing under `src/` changed.

## To repeat

- Margins on the stored v5 block: build the verdict with `keep_v2.judge(cand_rows, base_rows, frontier=2, rule="v3", min_gain=0.5)` on the arms of
  `gen21/candidate-fight-v5` and `gen20/candidate-chain` for E21-2026-11-21-r2 and print `keep_v2.summary(v)`.
- Flags on the stored verdicts: `gym_gate.boss_flags(row["parts"])` on the rows of `gym-loop/gate/verdicts.jsonl` with rule `gym-loop-promote-v5`.
- The replay check: `D:/spireline/src/sts2/.venv/Scripts/python.exe -I rl/act3_starts.py arrivals --champion D:/spireline/referee/agent/gen20/candidate-chain
  --out <scratch folder> --limit 20 --procs 6` (about 7 minutes; hold a QUIET line).
- The tests: `STS2_REQUIRE_AOT=1 D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_arrival_exam.py` (and `test_keep_v3.py`,
  `test_gym_gate_v5.py`) from the fork tree.
