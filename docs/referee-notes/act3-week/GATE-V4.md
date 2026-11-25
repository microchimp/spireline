# Lane 12: the fight loop's gate, rule v4

Written 2026-11-20 about 17:10Z by lane 12 (Sonnet 5.5). Decision: D57 addendum 9. Words once: the **fight loop** is the daemon that trains the fight brain and **gates** each new brain (decides whether it replaces the current one); **v3** is the old gate, **v4** the new one; the **exam** is the fixed set of 400 fights taken from human runs (Acts 1 and 2) that the daemon also uses to compare the brain with the humans.

## 1. What changed (fork main `c617a4f5`, branch `fix/gate-v4`, `rl/gym_gate.py`, `rl/gym_loop.py`, `docs/rl/GYM_LOOP.md`, `tests/python/test_gym_gate_v4.py`)

- **The rule** (`PROMOTION_RULE_V4`, one dict; `--rule v4|v3`, v4 the default; `--rule v3` is the undo): the ruler is the exam's 400 human starts under `a3-v1` on the CPU prior, paired draws on the same seeds for candidate and incumbent; survival = won and not capped; HP lost = start HP less end HP (the whole start HP when lost); the paired difference per (start, draw), SE clustered on starts. Stage 1 = draws 0-1 (800 games): reject when the 95 in 100 upper bound of the survival gain is under -1.0 point. Stage 2 = draws 0-7 (3,200): promote at gain >= +0.75 points, 90 in 100 lower bound above 0, HP lost not worse by more than +0.5 a fight (point estimate); gain >= +0.5 without the bar: stage 3 = draws 0-15 (6,400), same test, else reject. The pooled-trend path is not used under v4 (`pooled` stays for v3). One promotion in 6 hours stays.
- **Stored incumbent games**: `exam/games-<name>.jsonl`, rows keep their `engine`. A row on another engine than the daemon's is used only after an identity check (24 stored games replayed by the same player on this engine; outcome, end HP, move hash all equal), recorded in `exam/identity.jsonl` (one record per player, stored engine, engine). A failed check puts those games back to be played again (never deleted). A gate plays only the candidate, plus the incumbent's missing draws once.
- **Act 3 guard** (`act3_guard`, `act3_gate_ids`, `act3_guard_due`, `run_act3_guard`): from 24 h after the first practice segment that drew an Act 3 start (`games/segments.jsonl`; the first was 2026-11-20 07:40Z, so from about 11-21 07:40Z), a would-be promotion also plays one draw of 120 Act 3 exam starts and is refused when the 95 in 100 upper bound of the survival difference is under -3.0 points; reported by cell in the verdict (`act3`). The sample is drawn once by a seeded hash and written to `exam/starts-act3-gate.jsonl` on first use.
- **Human bar**: every stage-2 or stage-3 verdict carries `human` (candidate, incumbent, humans: survival and HP lost overall, by act-and-kind cell, by boss; the exam's bootstrap line) in `gate/verdicts.jsonl` and the loop log; no game is played for it; `--human-bar` is a no-op under v4.
- **Pre-filter**: `best` (the gap to beat) records the rule that set it; a record of another rule, or none (v3's), is ignored under the active rule. `floor_h` 6 and `gate-every-min` stay.
- **First candidate**: `--first-candidate c0380` (v4 only) makes that checkpoint the next gate until it has a verdict; the old pre-filter had marked it skipped. New subcommand `gym_loop.py import-games --root R --into NAME --games FILE --provenance TEXT` appends the rows a file lacks, with a `provenance` field.
- Tests: 15 new (`test_gym_gate_v4.py`: statistics by hand calculation, every rule branch, stage 3, Act 3 sample and guard, identity pass and fail, pre-filter anchor, a whole gate on a scratch folder with `play_tasks` replaced); two v3 tests of the gate procs now run `--rule v3` and one checks v4's.

## 2. Dry run: c0380 against v3, through `run_gate_v4` itself (nothing played; `gate-v4/dry_run.py`, output `gate-v4/dry_run.out`)

Rows: c0380's 3,200 games of 11-20 (engine `080e96344837`) and v3's 1,600 stored of 11-09 (engine `aa0d3ebcc1ba`, identity 100 of 100 recorded from lane 11) plus 1,600 of 11-20; all imported through `import_games`.

- **Stage 1** (draws 0-1, 800 games): c0380 65.0, v3 64.5, +0.50 points, SE 1.16, 95 upper bound +2.41: continue.
- **Stage 2** (draws 0-7, 3,200 games, 400 starts): c0380 65.3, v3 64.0, **+1.34 points, SE 0.66, 90 lower bound +0.50 (the brief's +0.49 is the same figure on rounded inputs), HP lost -0.52 a fight (SE 0.19)**: **promote** (all three conditions). Human bar line: `cand 65.3 / inc 64.0 / human 79.8 in 100 on 400 starts; cand-inc +1.3 [+0.1, +2.6]; HP lost 37.7 / 38.2 / 33.2`.
- Act 3 guard: not due (the daemon has been drawing Act 3 starts for about 9 h).

By cell (survival in 100: c0380, v3, human; difference in points, SE; HP lost: c0380, v3, human; difference, SE), every figure equal to lane 11's `plateau-check/results.txt` (checked row by row):

```
act1-hallway   31   248 | 100.0 100.0 100.0  +0.00 0.00 |  9.8  9.8  7.7  +0.02 0.37
act1-elite     31   248 |  79.0  81.0  80.6  -2.02 1.43 | 30.0 30.1 26.0  -0.17 0.50
act1-boss     185  1480 |  55.7  53.3  71.4  +2.36 1.06 | 43.1 44.0 39.2  -0.87 0.25
act2-hallway   31   248 |  96.4  96.4 100.0  +0.00 0.82 | 14.4 14.5 14.1  -0.12 0.71
act2-elite     31   248 |  74.6  71.4  77.4  +3.23 2.24 | 32.7 34.0 28.9  -1.24 0.62
act2-boss      91   728 |  54.7  54.0  83.5  +0.69 1.65 | 48.4 48.4 40.1  -0.00 0.51
all           400  3200 |  65.3  64.0  79.8  +1.34 0.66 | 37.7 38.2 33.2  -0.52 0.19
```
(the humans' Act 2 boss HP lost reads 40.1 here and 40.2 in results.txt: rounding only; by boss in `dry_run.out`.)

## 3. Cost per stage (the rows' own `seconds`, CPU-seconds a game, c0380's 3,200)

By cell: Act 1 hallway 0.85, Act 1 elite 1.79, Act 1 boss 3.08, Act 2 hallway 2.25, Act 2 elite 2.26, Act 2 boss 4.2 (3,200 games, 9,381 CPU-seconds, mean 2.93). So stage 1 about 0.65 CPU-hours (800 games), stage 2 about 2.6, stage 3 about 5.2; an identity check 24 games (a minute or two); the Act 3 guard about 1 CPU-hour a player (the brief's figure; not measured, no Act 3 game was played), the incumbent's side once per incumbent. At 4 processes stage 2 is about 40 minutes of wall time.

## 4. Restart record

- Landed: fork main `c617a4f5` (two commits over `d3daa7d8`: `7bab4eb0`'s content and the test fix). Python-only gate on the tip: 6,487 tests, 3 failures and 12 errors, all among the 60 baseline failures, **0 new** (first run on `7bab4eb0` showed 2 new: the two v3 gate-procs tests that now ran under the new default rule; fixed by pinning them to `--rule v3`; the second full run is on `c617a4f5`). Evidence: `logs/fork-tests/c617a4f5.txt`.
- 16:59Z `gym_loop.py stop` while the daemon waited on `main.lock` (no step running); no process held the tree's DLL; `wt-gym-loop-run` moved from detached `24afec9c` to detached `c617a4f5`; `out/` rebuilt with `publish-wt.sh` (rc 0): **engine tag `426e1724e7a0`** (before: `080e96344837`; the fork's lane 10 engine change landed in between, so the identity checks will run on the first gate: v3's rows of both stored engines and c0380's rows, 24 games each).
- Imports with the daemon stopped: `exam/games-v3.jsonl` +1,600 rows (draws 4-7, provenance named), `exam/games-c0380.jsonl` 3,200 rows (provenance named).
- Started 17:00:39Z with the old command line plus `--rule v4 --first-candidate c0380`: **PID 24516**, commit `c617a4f5`, 4 generation processes, 4 gate processes. Start-up lines in `loop.log`: `daemon: start pid 24516 at c617a4f5 ... generation 4 processes K=2, gate 4 processes`; `state reloaded: incumbent v3, 380 checkpoints with a verdict, segment 461; gym-loop-promote-v4: the exam's human stratum under a3-v1 (cpu prior), stages of [2, 8, 16] draws; ...`; `human bar: under rule v4 every stage-2 or stage-3 verdict carries the human line ...`; `wiring on`; `practice mix`; then `wait start: quiet:act3-replay` (another lane's replay holds the daemon until its line goes) and `trainer: started`. The first gate is c0380; when it runs the log shows the identity checks, then `gate c0380: stage 1 ... stage 2 ...`.

## 5. Undo

Stop the daemon (`gym_loop.py stop --root D:/spireline/referee/gym-loop`), start again with `--rule v3` (drop `--first-candidate`). Verdict rows of both rules stay in `gate/verdicts.jsonl`, each with its `rule`. A v4 verdict leaves the v3 pool and the board's files untouched.

## 6. Departures from the brief, and what is not verified

- The Act 3 guard is played only for a would-be promotion (a candidate the main test would promote), not at every stage 2: a rejected candidate's Act 3 reading changes nothing and costs an hour. The brief says "played at stage 2 for the candidate"; the constant `act3_guard.when` is "promote".
- "Test Subject cells first": 80 of the 120 starts are Test Subject (53 and 27 over its two cells), 20 each from the Queen and Aeonglass cells (split over their cells); 120 of the 210 Test Subject starts alone would leave the other four cells unread.
- **A v4 promotion gets no fight-board row**: the board's page is built from games on the board's 200 starts, which v4 does not play; `promote` logs it, and `board_commit` now leaves out a version with no board games instead of stopping. `gate --rule v3` plays them. The orchestrator decides whether the board should read the exam.
- Not verified: the live path has not run. The unit tests and the dry run cover every branch with the play replaced; the real play of an identity check, of the candidate's games and of the Act 3 guard through `play_tasks` has not run in the daemon (same functions as the old human bar, but not run). The first gate will be the test; watch `loop.log`. If the 24-game check fails on the new engine (lane 10's change touched the solver), the incumbent's and c0380's draws are replayed (about 5 CPU-hours, a day's gate budget) and the verdict can differ from the dry run. The Act 3 guard's cost is the brief's figure. Rows with no `engine` field would be unused (all current rows have one).
- The incumbent's and candidate's games sit in `exam/` (`games-<name>.jsonl`, `identity*.jsonl`, `act3-gate/`), not in `gate/`; the exam's own player listing reads `exam/games-*.jsonl` and is unchanged.
