# Brief: judge build 1 (margins in both judges, the Act 3 arrival exam as a measurement, the S1 run script)

Written 2026-11-22 02:05Z by the orchestrator. Build lane, Sonnet. Read `COMMON.md` first (worker rules; they hold even when another file says otherwise), then `judge-design/DESIGN.md` sections 3 and 4 (the design you build) and `BRIEF-judge-design.md` (the facts). Read-only on `D:/spireline/src`; no network; the lab, `QUIET.lock`, markers and `jobs.json` are the orchestrator's. **No rule change in this lane**: route S itself (DESIGN.md step 5) waits for the owner. Work in a fork worktree of `D:/spireline/fork/sts2` (its `CLAUDE.md` rules), land on fork main ff-only under `D:/spireline/referee/backlog/main.lock` with the Python-only gate, one focused commit per step. Heavy CPU: none, except a verification replay of at most 20 rows (minutes) in step 2; the S1 run itself is the orchestrator's to start.

## Step 1: margins, no rule change (DESIGN.md section 4)

- `tools/lab/keep_v2.py`: `promotion.json` gains `keep_v2.margins` (for B1, B2, B3a, wins, deep_f, floors and arrivals: the counts, the paired difference per 100 runs, its SE and plus or minus 2 SE, the discordant pairs) and `per_arrival` (each arm's first-Act-3-boss pass rate per 100 arrivals with its SE). The ledger line shows plus or minus 2 SE beside every figure (the memo gives v5's line as the example). Nothing about the decision changes; the existing tests stay green unchanged except where they parse the ledger line.
- `rl/gym_gate.py` (`strat_read`) and `rl/gym_loop.py`: every stage line and verdict row of rule v5 carries plus or minus 2 SE per cell, and a boss cell at -3 points or worse is flagged in the stage line and in the verdict record (`flags`), a flag, never a refusal. Check on the stored verdicts that c0390 flags nothing and c0384 flags the two Act 3 cells the memo names.
- Tests in `test_keep_v3.py` and `test_gym_gate_v5.py`.

## Step 2: the arrival exam, built and tested as a measurement (DESIGN.md section 3, "S1's ruler" and "S1's play")

- `rl/act3_starts.py`: a builder for the champion's first-Act-3-boss arrivals from its judged base arms (generation 20: blocks E21, E21-r1, E21-r2 under `D:/spireline/referee/agent/gen20/candidate-chain/arms/`; the memo expects 437 + 450 + 240 = 1,127 rows), rebuilt to the boss door by the gym's replay step, keeping only replays that match their row; second-boss arrivals kept for the record; the ruler written with its hash to `D:/spireline/referee/gym-loop/arrival/<champion>/`; every run used is listed for exclusion from practice. **First verify, on at most 20 rows, that the judge's arms load into the replay step** (the memo's unverified point); if they do not, say exactly what is missing and stop this step: do not improvise a loader.
- `rl/gym_gate.py` (`arrival_exam`): candidate fight network against the champion's on the ruler, config `a3-v1` on the CPU prior, 6 draws per start, test k on draws 6k to 6k+5; the statistic is the per-start mean survival difference (candidate minus champion), averaged unweighted over the arrivals, SE over starts; the reading printed with its SE, plus or minus 2 SE, starts, draws, the ruler's hash, and the two bounds the memo names (0.005 lower bound for a hold; 95% upper bound below 0 as a reversal), as a report only. The exam runs under the gym's night window rule and BelowNormal priority, 12 processes.
- New test `test_arrival_exam.py` (a tiny synthetic ruler; the statistic, the SE, the bounds, the hash, the draw indexing).

## Step 3: the run script, not run

- `D:/spireline/referee/backlog/act3-week/judge-design/S1-v5.sh`: builds the generation-20 ruler (about 1.8 h), then plays `gen21/candidate-fight-v5`'s fight network against the champion's (v3) on it (about 1.7 h on 12 processes), writing `judge-design/s1-v5/report.txt` and `results.json`; exits non-zero on any failure (a pipeline's status is its last command's: no `| tail`); requires the lab tree or a named worktree to contain your landed commit (never an exact hash). The orchestrator starts it under its own QUIET line. **Do not run it.**

## Deliverables and report

The commits on fork main (hashes), test counts (full Python suite before and after, 0 new failures), the verification result of step 2 (arms load: yes or no, with the row counts per block), the ruler's expected size, and the script's path. Report at most five lines; detail in `judge-design/BUILD-1.md`. No decompiled text, no host or user names, no human seeds or run ids. If step 2's verification fails, land step 1 alone and report.
