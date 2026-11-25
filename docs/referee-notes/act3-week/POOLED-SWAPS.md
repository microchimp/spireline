# Pooled whole-run reading of fight-only swaps (lane 26)

Tool: `tools/pooled_fight_swaps.py` in the Spireline repo (main a83ec76; tests `tests/test_pooled_fight_swaps.py`, 41). It reads every fight-only candidate under `referee/agent/gen*/candidate-fight-*/` (judgement record, boss-door exam, ledger, the gym's promotion line) and prints one row per fighter and the precision-weighted pooled estimate. Re-run it at every judgement and append the output below, newest last. Every figure carries plus or minus 2 SE; "+/-" below is that margin. No seeds, run ids, block names or paths are printed.

## 2026-11-25T03:02Z, first run (v7's whole-run judgement was still running, so its row is pending)

Command, from the Spireline repo folder: `D:/spireline/spireline/.venv/Scripts/python.exe tools/pooled_fight_swaps.py`

```
Pooled reading of fight-only swaps (every figure plus or minus 2 SE)

Per fighter: gain at the gate's test fights (points; h = Acts 1 and 2 human starts, a3 = Act 3 boss starts), the boss-door exam (S1, first Act 3 boss, passes per 100 arrivals), the judge's verdict.
fighter  promoted    judged      champion                  gate gain (points)                 door S1 per 100 arrivals                   verdict   route
-------  ----------  ----------  ------------------------  ---------------------------------  -----------------------------------------  --------  ---------
v3       n/a         2026-11-18  gen17/candidate-cheap-v2  n/a                                none played                                promoted  F
v4       2026-11-20  2026-11-21  gen20/candidate-chain     h +1.34 +/-1.32                    none played                                rejected  none held
v5       2026-11-21  2026-11-22  gen20/candidate-chain     h +1.11 +/-1.06; a3 +0.64 +/-1.54  +1.10 +/-0.82 (1126 starts; holds)         promoted  S
v6       2026-11-23  2026-11-23  gen21/candidate-fight-v5  h +0.12 +/-1.06; a3 +2.27 +/-1.96  none played                                rejected  none held
v7       2026-11-24  n/a         gen21/candidate-fight-v5  h -0.44 +/-0.68; a3 +1.85 +/-1.58  +1.19 +/-1.32 (464 starts; does not hold)  pending   pending

Whole runs: first Act 3 boss passes per 100 runs, candidate against champion on the same seeds.
fighter  pairs    candidate passes (per 100)  champion passes (per 100)  paired difference  SE    arrive %  full carryover
-------  -------  --------------------------  -------------------------  -----------------  ----  --------  --------------
v3       2,000    52 (2.60)                   47 (2.35)                  +0.25 +/-0.88      0.44  16.1      n/a
v4       4,000    233 (5.83)                  212 (5.30)                 +0.53 +/-0.78      0.39  22.5      n/a
v5       2,000    130 (6.50)                  135 (6.75)                 -0.25 +/-1.28      0.64  23.5      +0.26 +/-0.19
v6       2,000    111 (5.55)                  128 (6.40)                 -0.85 +/-1.21      0.61  22.5      n/a
v7       pending

pooled whole run (v3, v4, v5, v6; 10,000 pairs): +0.11 +/-0.49 per 100 runs (SE 0.24; band -0.38 to +0.59)
  of which judged under keep rule v3 (v4, v5, v6; 8,000 pairs): +0.04 +/-0.58 per 100 runs (SE 0.29; band -0.54 to +0.63)
pooled door S1 (v5, v7; 1,590 starts): +1.12 +/-0.70 per 100 arrivals (SE 0.35)
full carryover (pooled door gain x 21.4% of runs arriving): +0.24 +/-0.15 per 100 runs
reading: not excluded: the pooled upper bound is not below the full-carryover reference
extrapolation only: about 13 more rows like the average so far would bring the pooled 2 SE down to the reference

pooled whole-run effect +0.11 per 100 runs, 2 SE 0.49, 4 rows, 10,000 pairs; upper bound +0.59 against a full-carryover reference of +0.24 (2 SE 0.15)

notes:
  v3: the record predates the strict boss reading (2026-11-19); the whole-run figure is the arms' rows read under it
  v5: 1 earlier judgement record(s) of this candidate are superseded by the newest
  v6: 1 record file(s) in the folder name another candidate's network and are not read
  v7: 1 record file(s) in the folder name another candidate's network and are not read
  v7: no judgement record yet: the whole-run reading is pending
  pending (no whole-run record yet): v7
```

Command: `... tools/pooled_fight_swaps.py --check` (exit code 1)

```
--check against the 11-24 sceptic review, section 3 (whole-run effect, first Act 3 boss passes per 100 runs)

figure                      review  tool   result
--------------------------  ------  -----  --------
v4 effect                   +0.5    +0.53  ok
v4 plus or minus 2 SE       2.0     0.78   MISMATCH
v4 pairs                    4000    4000   ok
v5 effect                   -0.25   -0.25  ok
v5 plus or minus 2 SE       1.28    1.28   ok
v5 pairs                    2000    2000   ok
v6 effect                   -0.85   -0.85  ok
v6 plus or minus 2 SE       1.21    1.21   ok
v6 pairs                    2000    2000   ok
pooled effect (v4, v5, v6)  -0.4    +0.04  MISMATCH
pooled plus or minus 2 SE   0.8     0.58   MISMATCH

with the review's v4 margin read as 2 SE = 2.0 the pooled reads -0.39 +/-0.80 (the review: -0.4 +/-0.8); with v4's own paired margin it reads +0.04 +/-0.58
v4's figure here is from: arms re-read (the record holds no margins)

check: MISMATCH beyond rounding (exit 1)
```

What the first run says:

- Five rows are found, not four: gen18/candidate-fight-v3 (fight v3 over gen17's champion, judged 11-18 under keep rule v2) is also marked a fight-only swap. The pooled line is printed with it and without it (the review's set, v4 to v6).
- v5 and v6 reproduce the review to its rounding (-0.25 +/-1.28 and -0.85 +/-1.21, from the records' own margins; re-reading the arms with `--recompute` gives the same figures). v4 does not: its record holds no margins, and its 4,000 pairs read +0.53 +/-0.78 (SE 0.39, paired), not +0.5 +/-2.0. The review's pooled figure follows from v4's margin read as 2 SE = 2.0 (-0.39 +/-0.80). With v4's own margin the three read +0.04 +/-0.58 per 100 runs.
- The door exam (v5 +1.10 +/-0.82 on 1,126 starts; v7 +1.19 +/-1.32 on 464) pooled reads +1.12 +/-0.70 per 100 arrivals. Times the share of runs that arrive (21 to 23 in 100) that is a full-carryover reference of about +0.24 +/-0.15 per 100 runs. The pooled whole-run upper bound (+0.6) is above it: full carryover is not excluded, and neither is zero. About 13 more rows of this precision would put the pooled 2 SE at the reference (an extrapolation, not a measurement).
- The gate gain printed for v4 (+1.34 +/-1.32, the gate's stage-2 line) is not the review's +1.94 +/-1.26; the check does not compare gate gains.

## Run 2026-11-25 07:01Z (orchestrator), after v7's judgement ended 06:59Z

`D:/spireline/spireline/.venv/Scripts/python.exe D:/spireline/spireline/tools/pooled_fight_swaps.py`

```
Pooled reading of fight-only swaps (every figure plus or minus 2 SE)

Per fighter: gain at the gate's test fights (points; h = Acts 1 and 2 human starts, a3 = Act 3 boss starts), the boss-door exam (S1, first Act 3 boss, passes per 100 arrivals), the judge's verdict.
fighter  promoted    judged      champion                  gate gain (points)                 door S1 per 100 arrivals                   verdict   route
-------  ----------  ----------  ------------------------  ---------------------------------  -----------------------------------------  --------  ---------
v3       n/a         2026-11-18  gen17/candidate-cheap-v2  n/a                                none played                                promoted  F
v4       2026-11-20  2026-11-21  gen20/candidate-chain     h +1.34 +/-1.32                    none played                                rejected  none held
v5       2026-11-21  2026-11-22  gen20/candidate-chain     h +1.11 +/-1.06; a3 +0.64 +/-1.54  +1.10 +/-0.82 (1126 starts; holds)         promoted  S
v6       2026-11-23  2026-11-23  gen21/candidate-fight-v5  h +0.12 +/-1.06; a3 +2.27 +/-1.96  none played                                rejected  none held
v7       2026-11-24  2026-11-25  gen21/candidate-fight-v5  h -0.44 +/-0.68; a3 +1.85 +/-1.58  +1.19 +/-1.32 (464 starts; does not hold)  rejected  none held

Whole runs: first Act 3 boss passes per 100 runs, candidate against champion on the same seeds.
fighter  pairs                candidate passes (per 100)  champion passes (per 100)  paired difference  SE    arrive %  full carryover
-------  -------------------  --------------------------  -------------------------  -----------------  ----  --------  --------------
v3       2,000                52 (2.60)                   47 (2.35)                  +0.25 +/-0.88      0.44  16.1      n/a
v4       4,000                233 (5.83)                  212 (5.30)                 +0.53 +/-0.78      0.39  22.5      n/a
v5       2,000                130 (6.50)                  135 (6.75)                 -0.25 +/-1.28      0.64  23.5      +0.26 +/-0.19
v6       2,000                111 (5.55)                  128 (6.40)                 -0.85 +/-1.21      0.61  22.5      n/a
v7       3,400 (provisional)  196 (5.76)                  188 (5.53)                 +0.24 +/-0.89      0.44  23.5      +0.28 +/-0.31

pooled whole run (v3, v4, v5, v6; 10,000 pairs): +0.11 +/-0.49 per 100 runs (SE 0.24; band -0.38 to +0.59)
  of which judged under keep rule v3 (v4, v5, v6; 8,000 pairs): +0.04 +/-0.58 per 100 runs (SE 0.29; band -0.54 to +0.63)
pooled door S1 (v5, v7; 1,590 starts): +1.12 +/-0.70 per 100 arrivals (SE 0.35)
full carryover (pooled door gain x 21.4% of runs arriving): +0.24 +/-0.15 per 100 runs
reading: not excluded: the pooled upper bound is not below the full-carryover reference
extrapolation only: about 13 more rows like the average so far would bring the pooled 2 SE down to the reference

pooled whole-run effect +0.11 per 100 runs, 2 SE 0.49, 4 rows, 10,000 pairs; upper bound +0.59 against a full-carryover reference of +0.24 (2 SE 0.15)

notes:
  v3: the record predates the strict boss reading (2026-11-19); the whole-run figure is the arms' rows read under it
  v5: 1 earlier judgement record(s) of this candidate are superseded by the newest
  v6: 1 record file(s) in the folder name another candidate's network and are not read
  v7: 1 record file(s) in the folder name another candidate's network and are not read
  v7: the record is not final (the block was extended or stopped early): its whole-run figure is shown and not pooled
```
