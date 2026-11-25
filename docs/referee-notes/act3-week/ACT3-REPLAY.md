# Lane 4: what more search buys at the Act 3 bosses (replay tool, smoke, full-run script)

Written 2026-11-19 02:40Z by lane 4 (Sonnet). Landed on the fork as `e0c4faf4` (two commits, `8a77d23a` and `e0c4faf4`; branch `feat/act3-replay`, worktree `D:/spireline/fork/wt-act3-replay`).

## The question, in one line

If the champion's fight player thinks four or sixteen times longer at an Act 3 boss, does it win the fight more often? "1x" is what it thinks today at a boss (its own setting, `a3-v1@h1e4b16`: 480 trial games a plain move, 1,920 where a target or choice is asked); "4x" and "16x" are four and sixteen times that. Nothing else changes: same fight network, same shuffles, same per-move random seeds at every budget, so the three games of one position differ only in how long the player thought.

## What was built

- `rl/act3_replay.py` (fork, lab code only, no engine change) and `tests/python/test_act3_replay.py` (26 tests; gate: 262 tests in the selected files, 0 new failures against the 60 known; summary in `D:/spireline/logs/fork-tests/e0c4faf4.txt`).
- Positions. The plain runs already save, for every fight of every run, the state going in (deck, relics, potions, HP, relic counters, the boss) in `referee/run-cheap/<generation>/decisions.d/<seed>.record.json`. The tool picks Act 3 boss fights from generations 17 and 18 in a fixed hash order (same stores, same salt, same picks) and rebuilds each opening on the copy the way the human-run starts are built (`native.reset_arena`), at the floor's number, Ascension 10. Position = one Act 3 boss fight of one run: boss 1 the first, boss 2 the second (only runs that beat the first reach it). 9,133 runs met a first Act 3 boss and 1,412 a second (at 02:00Z; the generation 18 store grows). Each position keeps the run's own result at that fight for the split.
- Games. One game per (position, budget) on the champion's own fight network (generation 18, `candidate-fight-v3`), on the old engine (what the plain runs and the judge play; `--engine core2` is an option), in-process CPU prior (no server, exact, GPU-free). A row per game: kill, HP left, turns, moves, trial games, wall seconds, a hash of the moves played. A game with a row is never played twice, so a stop only loses games in flight.
- Report: kills per budget with a 95% interval, paired differences (bootstrap over positions, sign test), how many pairs played the very same moves, the share of positions the search itself calls lost at the first move, splits by boss, boss number and by the run's own result, wall per budget, and `size` (the full run's size from a measured sample).

## Smoke (2026-11-19 01:58Z to 02:28Z, 4 processes, BelowNormal, machine otherwise idle; `act3-replay-smoke/`)

30 positions (24 first-boss, 6 second-boss; 9 Aeonglass, 9 Queen, 12 Test Subject; 27 from generation 17 runs, 3 from 18). All 30 played at 1x and 4x; 16x was cut by the 30-minute limit at 16 positions. No game capped, longest fight 50 moves, a worker used at most 0.73 GB.

| budget | games | kills | per 100 (95% interval) | wall s a game: mean / median / longest |
|---|---|---|---|---|
| 1x | 30 | 5 | 16.7 (7.3 to 33.6) | 17 / 12 / 43 |
| 4x | 30 | 5 | 16.7 (7.3 to 33.6) | 67 / 44 / 185 |
| 16x | 16 | 4 | 25.0 (10.2 to 49.5) | 250 / 152 / 654 |

Paired (same position, same shuffles): 4x against 1x on 30 positions: 5 kills against 5, no pair differs (0 more, 0 fewer), though the very same moves were played in only 18 of 30. 16x against 1x on 16 positions: 3 kills against 4, one position turned (a Queen fight lost at 1x and 4x, won at 16x): +6 per 100, interval 0 to +19, sign test p = 1. By boss, 1x/4x/16x: Aeonglass 3/9, 3/9, 1/4; Queen 2/9, 2/9, 3/4; Test Subject 0/12, 0/12, 0/8. By boss number: first boss 5/24 at 1x and 4x (4/13 at 16x), second boss 0/6 (0/3). By the run's own result: the 3 positions whose run beat the boss were won at every budget; of the 27 whose run lost, 1x and 4x won 2, 16x 2 of 14.

What it says, and what it does not: nothing is decided at this size. The 4x result (no pair changed, upper end about +10 per 100) is the only firm line, and it is on 30 positions. The picture is consistent with the search not being the wall: at the very first move the search's own trial games die in at least 95 of 100 in 27 of 30 positions at 1x and 4x (14 of 16 at 16x), yet two of those were won, so the figure is a rough warning rather than a verdict; the moves differed from 1x's in 12 of 30 pairs at 4x and 8 of 16 at 16x, and the outcome changed once. The first-boss kill at 1x (5 of 24, 21 per 100, interval 9 to 40) fits the runs' own 15.5 to 16 per arrival but is too small to confirm that the rebuilt openings are faithful; the full run's 1x row (about 400 first-boss positions, plus or minus 4 points) is that check, and the 3 of 3 "run beat it" positions all won is the first sign.

## Cost, and the full run

Measured wall a game on the 4-process smoke: 1x 17 s, 4x 67 s (4.2 times), 16x about 245 s (14 times; the 16 finished positions averaged 250 s against 17.6 s at 1x, scaled to the 1x mean of all 30). A position at all three budgets costs about 330 CPU-seconds. Winning games cost about twice a losing one.

`ACT3-REPLAY-full.sh` (this folder): 500 positions (400 first boss, 100 second) at all three budgets, 12 processes, BelowNormal, stops after 8 hours, whole positions finish before the next starts (a stop leaves a random subset, never a half-pair). It takes a `QUIET.lock` line `act3-replay` (Windows PID, rewritten every ten minutes, removed at the end), refuses to start under another's line, the night, PAUSE, HALT or `main.lock`, and the Python stops for the same. Output in `act3-replay-full/` (positions, games, meta, `report.txt`, log). Expected: about 46 core-hours, 3.8 hours wall at the smoke's speed; 12 processes on this 8-core, 16-thread machine will run each game slower than 4 did, so allow 1.5 times: about 68 core-hours and 5.7 hours. Not measured (the brief allowed at most 4 processes); the 8-hour stop is the guard. Launch it after tonight's block, with the lab's teacher job not running (the runner holds a new teacher block while the line stands, but does not stop one in flight; the smoke started just after a block ended). The lab's plain runs stop for the run's length. Resumable: run it again and it plays only the missing games. Rerun `report` or `size` any time.

To change what it plays: `N_FIRST`, `N_SECOND`, `N_PER_MULT` (e.g. `1:500,4:500,16:300`), `PROCS`, `WALL_HOURS`, `ENGINE`, `AGENT_DIR`, `WT` (the tree; default my worktree, `/d/spireline/fork/wt-lab` also holds the same code and the same engine build). The positions are drawn when the run starts, from the then-current stores.

## Not done or not verified

- Openings are rebuilt from the run's saved state, not captured inside the run: they carry the deck, relics, potions, HP and relic counters of the record (22 of 30 positions had a counter written), not a card's in-fight bonuses (none persist across fights as far as the record shows). The full run's 1x kill per first-boss position against the runs' own 16 per 100 is the fidelity test.
- Old engine only was run; the real-game block tonight measures the copy's Act 3 separately.
- 12-process speed unmeasured. One draw per position (the tool takes `--draws`); the paired interval is over positions.
- The sample interleaves boss 1 and boss 2 positions in a fixed ratio (4 to 1) that is not the arrival ratio (about 6.5 to 1); splits are by boss number and by boss.

## Repeat

Smoke: `OUT=D:/spireline/referee/backlog/act3-week/act3-replay-smoke PROCS=4 N_FIRST=24 N_SECOND=6 N_PER_MULT=1:30,4:30,16:30 ORDER=cheapest WALL_HOURS=0.5 bash ACT3-REPLAY-full.sh` (from this folder; needs an idle machine and no other QUIET line). Table: `D:/spireline/venv-gpu/Scripts/python.exe -I D:/spireline/fork/wt-act3-replay/rl/act3_replay.py report --out <folder>`; size: `... size --out <folder> --positions 500 --core-hours 90`. Tests: `STS2_REQUIRE_AOT=1 D:/spireline/src/sts2/.venv/Scripts/python.exe -I -m unittest discover -s tests/python -p test_act3_replay.py` from the fork tree.
