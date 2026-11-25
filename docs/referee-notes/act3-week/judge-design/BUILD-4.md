# Judge build 4: a fresh champion plays a base block before its first challenger's boss-door exam (built, tested, landed)

Lane: build lane 25 (Sonnet 5.5), 2026-11-25. Brief `BRIEF-base-block.md` (owner decision D68 addendum 7 item 2), design `DESIGN.md` section 3, `BUILD-3.md` (how the ruler grows), `docs/rl/KEEP_TEST_V3.md` "Route S".
Terms: **S1** = the arrival exam (the candidate's fight network against the champion's from the champion's own first-Act-3-boss arrivals); **ruler** = the set of arrival positions S1 plays, built from
the champion's own judged arms; **base block** = a block of runs the champion plays alone (no challenger beside it), 2,000 runs on fresh seeds. Nothing was played: no game, no replay, no exam; every test replaces
the block's player, the replay pool and the exam. I did not touch `LAB/jobs.json`, `PAUSE`, `HALT`, `ready-*`, `QUIET.lock`, `agent/`, `gym-loop/` or anything under `D:/spireline/src`.

## The problem, and what changed

A champion that has just been promoted has no judged arm outside the block it was selected on (excluded by design), so `s1_stage` raised `S1Unavailable` and keep rule v3 decided alone; under v3 a fight-only swap cannot
pass, so the first challenger after every promotion was a wasted judgement. Now, with `--base-block auto` (the default; it acts only under `--route-s auto`), `s1_stage` plays the missing arm itself:

- **When.** The champion has no usable ruler and no eligible arm (`act3_starts.ruler_gap` empty), or a base block of this judgement was started and not finished. Not for the same-network pair (refused before anything is built),
  not for a candidate that is not a fight swap, not for a champion that has arms (nothing changes for it), not when a reading already stands for this ruler, champion and candidate.
- **What.** `gen_loop.play_base_block`: 2,000 runs (`BASE_BLOCK_RUNS`) of the champion alone through `run_arm` (the whole-run stage's own block player; no second runner), `resume=True`, the judgement's config (`a3-v1`),
  ascension, prior transport (`arm_kw`) and 12 processes (`S1_PROCS`), into `<champion>/arms/<name>-a3-v1` where `<name>` is the judged E-block's name without a `-r<n>` suffix, plus `-base`
  (`E22-2026-11-25` -> `E22-2026-11-25-base`). The name is the same on every try, so a stopped job continues the block it started. About 1.7 to 2 hours on 12 processes (not measured here).
- **Seeds.** `gen0.e_block(name, 2000)` (derived from the name, like every E-block's), checked against every known block and the lab's self-play runs (`check_disjoint`, `known_seed_sets`), written to `<lab seeds folder>/<name>.json`
  so later blocks are checked against them. `resolve_e_block` now skips every `-base` seeds file: without that, the next candidate of the same generation would have found `E22-<date>-base.json` under its `E22-*.json` glob
  and been judged on the champion's own base block.
- **Registered.** The block is an ordinary arm folder (`runs.jsonl`, `summary.json` written by `run_block`), so `act3_starts.champion_arms` finds it; the stage then runs `act3_starts.py arrivals` as for any gap, builds the
  ruler from it, merges its runs and starts into the practice's exclusion list (`sync_ruler_exclusions`), and goes on to the exam as before. A ruler of one block grows by the later arms exactly as BUILD-3 says.
  `exclusion_of` needed no change for a ruler of one block (a test builds one through the real `arrivals` on the fake replay pool and reads its `exclude_runs.json`).
- **Unfinished blocks.** A block that ended short (the pool gave a row for fewer seeds) raises `S1Blocked`; a job killed mid-block leaves `runs.jsonl` without `summary.json`. In both cases the next try plays the block
  again with `resume=True` **before** the champion's arms are read, so a ruler is never built from half a block. A block played whose ruler build was stopped is not played again.
- **Record.** `<arm>/base-block.json` ({rule, written, block, for_block, candidate, runs, config, seeds_file}), written once when every seed has a row (a later try keeps the first time). `promote` puts
  `route_s_mode.base_block` (that record plus `arrivals`, `starts`, `matched` from the ruler's meta) into promotion.json, and the ledger's `guard` cell gets
  **`S1 on a base block played <UTC time>: <N> runs, <M> arrivals`** (N = the block's runs, M = its runs that reached the first Act 3 boss). When S1 had no reading after a base block was played (the ruler could not be built) the cell says
  `a base block was played <time>: <N> runs, no S1 reading` beside the usual `S1 unavailable: <why>; v3 decides`. The note appears only in the judgement the block was played for (`for_block`), not in a later extension block's row.
- **`--base-block off`.** The old way, word for word: `S1Unavailable("the champion gen<N>/<dir> has no arm outside the blocks it was selected on to build a ruler from")`, no ruler folder, no seeds file, v3 decides, the cell says
  `S1 unavailable: <that text>; v3 decides`. `gen0.py train` and `promote` take `--base-block auto|off` (default `auto`); `run_promote_subprocess` passes `--base-block off` only when it is off, so the default child command is unchanged.
  **The lab's train command already carries `--route-s auto`, so the base block is live in the lab as soon as its tree has this commit (the next presort); `jobs.json` is not touched.**

## Files

`rl/gen_loop.py` (the base-block section before `s1_stage`; `s1_stage(base_block=, play=)`; `promote(base_block=)`; `run_promote_subprocess(base_block=)`; the `resolve_e_block` skip), `rl/gen0.py` (`--base-block` on `train` and `promote`,
`BASE_BLOCK_HELP`), `docs/rl/KEEP_TEST_V3.md` ("A fresh champion and the base block"), `tests/python/test_base_block.py` (new, 26 tests).

## Tests (`test_base_block.py`: the existing fakes of `test_route_s_plumbing` and `test_ruler_growth`)

Naming and seeds (the flag, `-r<n>` stripped, `resolve_e_block` never returns a base block, seeds written once and refused when another block shares them); the no-arm path plays the block with the champion, config, 12
processes, `resume=True` and `server_opts` and builds the ruler from it (4 of 6 runs arrive: 6 starts); `champion_arms` finds the arm and the ruler's gap is empty after it; the runs reach the practice's exclusion list before
the exam plays; `off` raises as before (text, no folder, no seeds file, nothing played); the same-network case is unchanged (nothing played, no file); a champion with arms and a champion with a ruler play no block; a second try
neither replays the block nor rebuilds the ruler and keeps the first time; the champion's arm on the judged block, played between two tries, does not grow the ruler; a stopped ruler build does not replay the block; a block with no summary
or a short block is finished first; a short block is blocked and the next try finishes it; the record and the cell's words; through `promote` (real `s1_stage` on the fakes): `auto` plays the block, the row says so beside S1's reading and
`off`/default/`route-s off`/a champion with arms say nothing of it; the flag is an error when it is not a mode; the command line (defaults, child command, `promote_cmd`, `train`).

## Suite

Full Python suite, `gate-py.sh` FULL=1 (emulator Python, correctness gate beside the lab: it takes no QUIET line and the judgement's `lab-train` line does not hold it; started 03:50Z, after the night window), against `baseline-python-failures.txt` (60 known):

| | tip | tests | failing entries | new against the baseline |
|---|---|---|---|---|
| before | `6eeab4bd` (main) | 6,718 | 16 (3 failures, 13 errors; the lane 22 gate's own figures) | 0 |
| after | `9432e74b` | **6,744** (26 added: all of `test_base_block.py`) | 18 (5 failures, 13 errors), of which 3 flakes that pass alone | **0** |

The flakes: `test_solver_aot_sites.SolverAotSiteTests` (setUpClass under load, as in every recent gate), `test_envproto.FailedStartTest.test_a_silent_start_is_retried_on_a_fresh_process_and_the_failed_one_is_gone` and
`test_lab_jobs_student.PlateauAndDailyTests.test_the_banner_and_status_prefix_show_the_new_alerts_like_any_other` (the gate re-ran each alone: they pass; the suite ran beside the judgement). The gate's own step also ran
`test_base_block`, `test_route_s_plumbing`, `test_ruler_growth`, `test_keep_v3_route_s` alone (rc 0). Engine files changed against `origin/main`: 0. The suite took 2,684 s. Evidence: `logs/fork-tests/9432e74b.txt`.
The worktree's `out/` is a copy of the lab tree's (native API 40; `fork/sts2/out` is from 11-06 and exports 39).

## What I could not verify, and what is left

- **Nothing ran on the real path.** No block was played, no replay, no exam. The 2,000-run block's time (about 2 hours at 12 processes) is the brief's estimate; the train job's `timeout_min` is 720, and a fresh champion's judgement is then
  base block + ruler replays + exam + the two whole-run arms (the funnel's two 2,000-run arms, about 4 hours at 16 processes), so it fits with room, but the first real one is the check. A block killed by the runner's timeout resumes.
- With `--prior-server auto` the block's pool is the server's width (`--server-procs 20`), as the whole-run arms' is, not 12; `arm_kw` carries the prior server options exactly as the arms get them.
- The base block's replays on the ruler use the in-process prior while the block was played on the server when the lab's server is on (as every judged arm is); the ruler's meta keeps the match rate. A low match rate on the first real
  block would shrink the first ruler (the rule's own check, not new).
- `gen0.py promote --help` (and `train --help`) crash on main already: some help string holds a `% ` (the futility text, "95% upper") that argparse reads as a format. Not touched here; the flags parse.
- A judgement that is retried after a champion's arm on the judged block already exists and the ruler is still missing (a first try played arms before this landing) would now play the block and read S1 mid-judgement. It cannot arise
  from a try of the judgement running at landing time (S1 is read before any arm is played), and the landing waits for the lab to be idle.
- Not built: sharing a base block between two champions' judgements, a smaller block, reusing the champion's stored arm of the E-block as the ruler's first arm (it is the block being judged, which the ruler must not read).

## Commands to repeat the checks

```
cd D:/spireline/fork/wt-base-block      # (or any worktree at the landing)
STS2_LIB_PATH=<an out/ that exports the native API the tree asks for, e.g. a copy of the lab tree's> \
  D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_base_block.py
D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_route_s_plumbing.py   # and test_ruler_growth.py, test_keep_v3_route_s.py
TAG=<tag> WTN=<worktree folder> FULL=1 EXTRA="test_base_block.py" bash D:/spireline/logs/gym-loop/bin/gate-py.sh      # the full Python-only gate
```

## Landing

Fork main `9432e74b` (one commit on `6eeab4bd`; pushed 06:59Z). The full gate ran first (03:50Z to 04:36Z, beside the judgement, as a correctness gate does); the landing waited for the lab: the v7 judgement's
`lab-train` line went at 06:59:10Z, `LAB/nightly/active` did not exist, `main.lock` was mine for the minute of the rebase check (a no-op: main had not moved), the ff-only merge and the push. Commit trailer
`Co-Authored-By: Claude Sonnet 5.5 <<email>>`. The lab tree reaches it at the next presort; `jobs.json` is untouched. HANDOFF has the worker line.
