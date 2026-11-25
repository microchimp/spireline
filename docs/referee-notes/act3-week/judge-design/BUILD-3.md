# Judge build 3: the boss-door ruler grows with the champion, and its exclusions reach the practice by themselves (built, tested, landed; not run on the real path)

Lane: build lane 19 (Sonnet 5.5), 2026-11-24. Brief `BRIEF-judge-build-3.md`, design `DESIGN.md` section 3, `docs/rl/KEEP_TEST_V3.md` "Route S", the earlier notes `BUILD-1.md` and `BUILD-2.md`.
Terms: **S1** = the arrival exam's reading (the candidate's fight network against the champion's from the champion's own first-Act-3-boss arrivals, in passes per 100 arrivals);
**ruler** = the set of arrival positions S1 plays; **hash** = the ruler's fingerprint, which names the exact set of positions a test was played on; **test k** = the k-th set of 6 draws
played on a ruler. `--route-s` stays **off by default everywhere**: a judgement with the flag off, and one with it on whose champion has no new arms, is unchanged. Nothing was played: no
game, no replay, no exam; every test replaces the replay pool and the exam. I did not read or write anything of the gym loop's folder, the lab's files, `agent/` or `QUIET.lock`.

## What landed on fork main

| step | commit | what |
|---|---|---|
| 1 | `b3eb1a66` | the ruler grows: `arrivals` extends a ruler by the arms it lacks, history in `meta.json`, the exam's games per hash, `s1_used_tests` per hash, no folder for a champion with nothing to read, the ledger's `S1 unavailable` words; `test_ruler_growth.py` (new) |
| 2 | `ebb1b862` | the exclusions: `act3_starts.merge_exclusions`, `gen_loop.sync_ruler_exclusions` called wherever a stage reads a usable ruler, `act3_starts.py merge-exclusions`; its tests in the same file |
| 3 | `663ed6d7` | `docs/rl/KEEP_TEST_V3.md` "Route S": the ruler grows, what a test index means per hash, the exclusions, the fresh-champion case with its cost |

Fork main `663ed6d7` (pushed; `7a651460` before). Landed fast-forward under `main.lock` (no one else's line stood and `origin/main` had not moved since `7a651460`, so no rebase), after the full gate on the final tip. No
`LAB/nightly/active` and no `QUIET.lock` line of the lab's night stood. The commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <<email>>`. The first commit was amended once before landing (a test fixture
left the exam module's list of QUIET tags to ignore set, which made a later test in the same process fail); nothing was pushed before.

## What went wrong, and what changed

**1. The ruler grows (`rl/act3_starts.py`, `rl/gen_loop.py`).**
- `arrivals` on a folder that already holds this champion's ruler (its starts hash to its meta) **extends** it: it replays only the arms the ruler lacks (no entry for the block, or more rows
  than the entry read: a block completed since), carries every other arm's starts over untouched, and writes the whole set again with a new `ruler_hash`. `--rebuild` ignores the ruler. With
  nothing to add it exits 0 and leaves the folder byte for byte as it was. Exit codes keep their meanings (0 built, extended or up to date; 2 no arm to read or arms another agent played; 3 stopped or blocked).
- `meta.json` keeps a `history` (when, which arms, starts each added, `previous_hash`; a ruler written before there was one gets the single entry it implies). The meta is written **last**: a write
  that stops half way leaves a starts file that does not hash to the meta, which `load_ruler` reads as no ruler, and the next run builds it again from the replays on disk.
- `s1_stage` compares the champion's eligible arms (`champion_arms`, `ruler_gap`) with the ruler's, and runs the same `arrivals` command when there is a gap. The block being judged is left out
  (`--exclude-block`): the champion is still playing it, and the ruler must not change between two tries of one judgement. A candidate whose own `s1.json` already stands for the ruler is
  returned **before** any growth, so a v3 extension block of the same judgement reads the same reading instead of a new test on a bigger ruler (this is my addition: without it the first block's arm would
  trigger an extension, and a re-exam, at the second block).
- **Test index per hash.** `s1_used_tests` counts the ledger's entries and the games files of the current hash only (an entry naming no hash still counts: it cannot be told apart, and a draw is never
  used twice). Choice made: the old hash's games move to `exam/<old hash first 8>/` when the ruler grows (`retire_exam`), and `exam/ruler_hash.txt` says which hash the games in `exam/` belong to
  (`exam_games`); `arrival-exam` applies the same rule to its `--out` folder, so a folder that names another hash is never read as played. A reading on the old hash is not applied to the new ruler
  (`keep_v2.s1_match` already checks; a test shows it).
- A fresh champion with no eligible arm: `s1_stage` raises `S1Unavailable` **before any child runs** and no ruler folder is made (`cmd_arrivals` also makes its folder only after the checks). The same
  fight network twice is refused before a ruler is built (it used to be refused after the 1.8 h build).
- The ledger's `guard` cell: `keep_v2.ledger_cells` did not say anything when S1 was unavailable (the 11-23 row printed only the v3 parts). `gen_loop.route_s_note` now appends
  `S1 unavailable: <why>; v3 decides` when route S was asked and there was no reading (not a fight-only swap, no arm to build a ruler from, same network, no reading in a rejudgement);
  `route_s_mode.reason` holds the reason. A reading that was played prints its own parts, as before.

**2. The exclusions reach the practice (`act3_starts.merge_exclusions`, `gen_loop.sync_ruler_exclusions`).**
- The function is the hand script of 2026-11-22 as code: union sorted, `by_stratum["arrival-own"]`, `arrival.<ruler folder>` (rule, written, starts, runs, added counts, ruler hash), the old file kept once as
  `exclude_runs.json.pre-arrival.bak`, a temporary file replaced over the target (`gym_loop.write_json`, patient with a reader that has the file open). Idempotent: a ruler whose entry names its present hash and
  whose ids are all in is not rewritten. The hand result (3,712 run seeds, 4,229 start ids, `arrival.gen20-candidate-chain`) reads as already merged, byte for byte, on a fixture built by the hand script's own
  algorithm. A file that is not the fight exam's rule, unreadable, or a ruler list that does not match its meta is an error and is never rewritten; a loop with no list gets none made.
- Called wherever a stage reads a usable ruler: the S1 stage (on every read, and again after a build or extension, before the exam plays; **strict**: a list that cannot be merged stops the stage with
  the ruler and replays kept), `rejudge --s1` and a candidate's stored reading (not strict: said, the reading is still read; a dry run writes nothing). So a ruler built outside the train job, as on 11-22,
  is merged the next time any stage reads it. Until then `act3_starts.py merge-exclusions --ruler DIR [--dry]` is the hand way (for the S1-v5.sh path the practice may draw the ruler's fights between the build and the
  next read: run it right after the build).

**3. Tests and the book.** `tests/python/test_ruler_growth.py` (new, 59 tests): extension (starts kept, only the new arm replayed, the extended hash equals a fresh build of all the arms, history, grown arm, up to date,
rebuild, stop and resume, an edited ruler built again, another champion's ruler, no arm makes no folder), the exam folder per hash, `s1_used_tests` per hash, `s1_stage` growth (first challenger builds, later one
extends, new hash starts at test 0, old games put away, a stored reading stands), the guard cell, the merge (union, idempotent, backup once, atomic, the hand result, a growing ruler, bad files, the command) and the
stage hooks. `test_route_s_plumbing.py`'s fixtures name the champion's arm as the ruler's (the champion's arms folder now has a `summary.json`, as a real arm does). `docs/rl/KEEP_TEST_V3.md` "Route S":
the ruler grows (what triggers it), what a test index means per hash, the exclusions, the fresh-champion case with its cost.

## Suite

Full Python suite, `gate-py.sh` FULL=1 (emulator Python, run beside the lab and the fight loop as a correctness gate does; the two runs overlapped in time), against `baseline-python-failures.txt` (60 known):

| | tip | tests | failing entries | new against the baseline |
|---|---|---|---|---|
| before | `7a651460` (main) | 6,612 | 17 (4 failures, 13 errors) | 1: `test_quiet_lock.WaitTest...` |
| after | `663ed6d7` | **6,671** (59 added: all of `test_ruler_growth.py`) | 17, the same 17 | **0** |

The one "new" entry before is a clock test, not a code one: `test_quiet_lock.WaitTest.test_the_fight_loop_drops_its_line_between_steps...` expects the lab's score line and gets `night-window`
when the clock is inside the night window (03:10 to 03:45Z); the before run (03:11 to 03:37Z) hit it and failed it alone too (still in the window); the after run (03:28 to 03:58Z) failed it in the suite and the gate's re-run alone passed (past 03:45Z); `test_quiet_lock` also passes on main at 03:49Z.
One flake in both runs (`test_solver_aot_sites.SolverAotSiteTests`, fails in setUpClass under load, passes alone). My own files also pass in their own gate step (`test_ruler_growth`, `test_route_s_plumbing`,
`test_arrival_exam`, `test_gen_loop`: rc 0). Also played: `test_funnel`, `test_gen0`, `test_keep_v3`, `test_keep_v3_route_s` with my files in one process (374 tests, OK). Two mutations of the code (`s1_used_tests` counting
the ledger whole; the exam files not put away at extension; the merge skipping its idempotence check; the stage not merging) each failed tests, then were restored. Evidence: `logs/fork-tests/663ed6d7.txt`.
The worktree's `out/` is a copy of the lab tree's (the native API the tree asks for is 40; `fork/sts2/out` is from 11-06 and exports 39, so a gate run from a copy of it fails every native test).

## What I could not verify, and what is left

- **Nothing ran on the real path.** No replay, no exam, no real arm, no real exclusion list. I was told not to touch the gym loop's folder, so the claim that the real 11-22 list reads as merged is on a fixture
  built the hand script's way (3,712 / 4,229 counts), not the file itself. The orchestrator can check it with `act3_starts.py merge-exclusions --ruler <gen20 ruler> --dry` (it writes nothing; it should say
  `already merged`).
- The first extension happens on the real data at the first judgement after the next presort that has an eligible arm: gen21 holds one base block (`E22-2026-11-23`, about 465 arrivals), so the **next
  challenger's S1 builds gen21's ruler from that one arm** (the empty folder `gym-loop/arrival/gen21-candidate-fight-v5/` is fine: it is built into) and the ruler grows by one block per judgement after that.
  Each growth gives a new hash, so each challenger starts at test 0 and the champion's games are played again on the bigger ruler (the exam is about 1.7 h at 1,100 starts for both players, half of it the champion's).
- A test's draws 0 to 5 on the starts an old ruler held are the draws an earlier test used on them (the brief asks for a new hash to start at test 0): the champion's games there are the same games,
  the candidate's are its own. Reusing the champion's old games would halve the exam's cost and keep the statistic the same; it was not built (the brief wants the old hash's games put away).
- Not built: dropping an arm from a ruler when its block becomes a selection block later (`--rebuild` does it); the fresh-champion case is stated, not fixed (the first challenger after each
  promotion is judged by v3).
- `rl/gen0.py` and the lab's `jobs.json` are untouched: `--route-s auto` is already on the train job; nothing for the orchestrator to change there. The lab tree moves to the landing at the next presort.

## Commands to repeat the checks

```
cd D:/spireline/fork/wt-judge-build-3/tests/python
STS2_REQUIRE_AOT=1 D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest test_ruler_growth test_route_s_plumbing test_arrival_exam
```
(the worktree needs an `out/` that exports the native API the tree asks for: copied from the lab's tree, not from `fork/sts2/out`, which was built on 11-06 and exports an older version.)
