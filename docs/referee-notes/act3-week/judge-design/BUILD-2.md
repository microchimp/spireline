# Judge build 2: route S in the judge, the funnel and the flags (built, tested, landed; not run on the real path)

Lane: build lane 2 (Sonnet 5.5), 2026-11-22. Brief `BRIEF-judge-build-2.md`, design `DESIGN.md` sections 3 and 5, lane 1's notes `BUILD-1.md`. The owner adopted route S as designed
(D68 addendum 6 outcome 4, 2026-11-22 03:49Z). Terms: **S1** = the arrival exam's reading (the candidate's fight network against the champion's from the champion's own first-Act-3-boss
arrivals, in passes per 100 arrivals); **S2** = the whole-run judgement as the breakage check; **ruler** = the set of arrival positions S1 plays; **±** = plus or minus 2 standard errors (SE).
The flag `--route-s` is **off by default everywhere**: a landing leaves the judge unchanged. Nothing was played: no game, no exam, no real-path smoke (the live exam `judge-s1` held the machine); every test replaces the
replay pool, the exam and the arms. No QUIET line of mine was written; no file of the lab, the markers or `jobs.json` was touched.

## What landed on fork main (fast-forward, Python-only gate)

| step | commit | what |
|---|---|---|
| 1 | `e17419b7` | route S in the keep test: `s1_reading`, `route_s1`, `judge_v3(s1=)`, `seq_call_v3(route_s=True)`, the ledger line; `test_keep_v3_route_s.py` |
| 2 | `ce2f80e0` | the S1 stage of `promote`, S2 as the funnel, the base-arm reuse, `--route-s` on `train`/`promote`/`rejudge`, `rejudge --s1` and `--complete-block`; `test_route_s_plumbing.py`, additions to `test_funnel.py` and `test_gym_wiring.py` |
| 3 | `40e65c2d` | `docs/rl/KEEP_TEST_V3.md`: the route S section, the switches |
| 2b | `fbf265d4` | `rejudge --complete-block` copies each arm's stored rows aside before anything plays into the arms |
| 1b | `7a651460` | `keep_v2.route_s` composes S1 and S2's final bound in one function (the name the brief used); `judge_v3` calls it; its tests |

Fork main `7a651460` (pushed; `ac1437cd` before). Landed in one go under `main.lock` (no one else's line stood; `origin/main` had not moved since `ac1437cd`, so no rebase), after the full gate on the final tip. The commit trailer is
`Co-Authored-By: Claude Sonnet 5.5 <<email>>`.

Suite (full Python suite, `gate-py.sh` FULL=1 via a copy of the script that ignores the `judge-s1` line, emulator Python, BelowNormal; one earlier run was stopped and restarted after a code change): **6,540 tests before** (lane 1's tip `ac1437cd`),
**6,612 after** (74 added, two fewer ran than the sum: the flaked class `test_solver_aot_sites.SolverAotSiteTests` failed in setUpClass under load and passes alone added); 17 failing in the run (4 failures, 13 errors; 16 named in the gate's list, all among the 60 of `baseline-python-failures.txt`, plus that 1 flake): **0 new failures**, 1 flake. Evidence: `logs/fork-tests/7a651460.txt`.

## Step 1: route S in the keep test (`tools/lab/keep_v2.py`)

- `s1_reading(result, expect)`: the arrival exam's `results.json` in the shape the rule reads (mean and SE in passes per 100 arrivals, starts, pairs, draws, test, `complete`, the ruler's hash, the sha256 of the candidate's and of the champion's
  fight network), and `match` (`s1_match`): the reading's ruler hash, candidate and champion must equal `expect`'s; a key the pair cannot name is unchecked, and an unchecked reading is not applied.
- `route_s1(reading, fight_swap=)`: S1 holds when the mean is at least `S1_MIN` (1.0) and the mean minus `S1_Z` (2.576) SE is above 0. A reading that does not match, is incomplete, has no mean/SE or belongs to a candidate that is not a fight-only swap is
  **not applied** (`applied` false, the words in `reasons`) and never holds.
- `route_s(deep_diffs, s1, ...)`: S1, then S2's final bound (deep_f's one-sided 95% upper bound, the bootstrap's, not below 0) when S1 holds. `judge_v3(..., s1=, fight_swap=)` calls it and adds the guards: when S1 holds the decision is S's
  (collapse, crash, wins as before; the ledger route `S`, or `AS` when route A holds too; **no extension**); when S1 does not hold or is not applied, v3 decides exactly as before and the reason is recorded. With no reading the verdict has no new key.
  `judge(..., rule="v3", s1=)` passes it through; under v2 it is an error.
- `seq_call_v3(route_s=True)` (and `seq_call(rule="v3", route_s=True)`): the looks refuse only: from `S2_FROM_PAIRS` (500) pairs on, deep_f's 99% upper bound (`S2_LOOK_ALPHA`) below 0 or a floor collapse; never eligible to promote; the smoke and last looks as before.
- `summary` (the ledger's `guard` cell) shows `S1 +x.xx ±y.yy per 100 arrivals (N starts, 6 draws, ruler <8 hex>): holds | does not hold, v3 decides` or `S1 not applied (reason)`, and `S2 deep 95% upper +z.zz (final bound 0: ok|FAILS; 99% upper +w.ww)`;
  `ledger_cells` gives the route `S`/`AS`. The ledger's columns are unchanged (the S figures are in the `guard` cell and in promotion.json). The parameters are named constants and are written under `keep_v2.route_s.parameters`
  with the S1 reading, the S2 bounds and `state_shift` (the whole-run pass rate per 100 arrivals' difference minus S1's, with its SE: DESIGN section 4).
- Tests: `tests/python/test_keep_v3_route_s.py` (25): no S1 = v3 unchanged (equal verdicts, no `route_s`, no S in the line); S1 and S2 holding promote by S where v3 extends; S1 failing (mean under +1.0, bound not above 0) leaves v3; S2's final bound failing
  refuses and extends nothing; collapse, crash and wins still block; the harm stop at a look (99% bound, from 500 pairs, never eligible, smoke refuses nothing); the reading refused on a ruler, champion or candidate mismatch, unnamed, incomplete, not a fight swap;
  the field names checked against `gym_gate.arrival_exam`'s own output.

## Step 2: the funnel, the S1 stage, the base-arm reuse and the flags (`rl/gen_loop.py`, `rl/gen0.py`)

- **Detection**: `gen_loop.fight_only_swap` reads `agent.json` `built.swap == "fight"`, the field `gym_wiring.build_fight_candidate` writes (test: the real builder's candidate and the wiring's queued one are detected; the champion's folder, the vrun/chain/prior builders' are not). No other field.
- **`promote(route_s="auto")`**: after the cheap fight screen and before any arm is played, `s1_stage` (below). S1 holding: the funnel with `route_s=True` (looks refuse only, **no futility stop, no early promotion, no extension**), the base-arm check, the verdict by S.
  S1 not holding, or S1 unavailable for the pair (the champion has no arms; the same fight network): v3 exactly as today, the reason in promotion.json (`route_s_mode.why`, `s1`). S1 stopped or blocked (the night window, PAUSE, HALT, a landing, another's line, incomplete): `S1Blocked`,
  `gen0 promote` exits 3, the train job fails and the runner retries; the ruler's replays and the exam's games resume. promotion.json gains `s1`, `route_s_mode`, `state_shift`, `base_reuse`; `sequential.route` = `S`.
- **`s1_stage`**: the champion's ruler `gym-loop/arrival/<champion folder name>/` is used when its `meta.json` names this champion and `act3_starts.load_ruler` verifies the hash, else built there (`arrivals`, 12 processes). Test index k = one more than any test played against the ruler (the ledger
  `s1-ledger.json` beside it, plus any draws a games file in its `exam` folder holds), written before the games are, so a resumed judgement keeps its draws and no candidate's draws (6k to 6k + 5) are another's; a reading that stands in the candidate's folder (`s1.json`) for this ruler,
  champion and candidate is not played again (the requeue after a v3 extension reads it). Then `arrival-exam`, 12 processes, report in `<candidate>/s1/`, reading in `<candidate>/s1.json`. Both children are told `--allow-quiet lab-train` (the runner's own tag; a test pins it to `runner.TRAIN_TAG`
  and shows `fight_exam.blocked_reason` stops on the lab's line without the flag and not with it, and still stops on anyone else's), inherit the train job's priority, hold no line and never touch the gym daemon.
- **Base-arm reuse** (`base_arm_reuse`): before S2 reuses the champion's stored arm on seeds the candidate did not play beside it, the first 20 such seeds of the block (in order, no gap, each with its index in the block, since the agent's random numbers are [seed, index]) are replayed by the champion on this tree into
  `<candidate>/arms-check/` with the arms' own prior transport; the outcome rows (`OUTCOME_FIELDS`: index, win, floor, end, crash, lost, nodes, cards, rests, boss damage) must equal the stored ones. All 20 equal: reused. One differs: the stored arm is moved to `<champion>/arms-stale/` and the champion plays the block afresh.
  Recorded in promotion.json (`base_reuse`). Where the candidate played the rows beside the champion (a fresh block, a resumed one, the completion of E21-r2) there is nothing to check.
- **Flags**: `--route-s {auto,off}` (default `off`) on `gen0 train` (passed to the child only when `auto`; `auto` under v1/v2 is refused before anything is trained or judged, the marker stays), `promote` and `rejudge`. `rejudge --route-s auto --s1 <results.json>`: the reading is checked against the champion's ruler hash and both fight networks
  (a mismatch is not applied, the reason recorded; a ruler that cannot be read leaves it unchecked and unapplied) and its test is entered in the ruler's ledger (not on a dry run). Without `--s1` the candidate's own `s1.json` is read, else v3 decides. `--s1` and `--complete-block` need `--route-s auto`.
  **`--complete-block`**: the funnel has a resume mechanism (`run_arm(resume=True)`: a seed with a row is not played again), so a block the funnel stopped (v5's `futility@1100`) is completed with it: both arms' `runs.jsonl` are first copied beside them (`runs.before-completion-<UTC>.jsonl`; the resume rewrites the file and starts it empty when
  the identity changed), the looks are walked again over the stored rows under S2's rules (so a harm at 500 to 1100 pairs refuses there), the remaining pairs are played with `--procs`, `--ascension`, `--lib` and the prior-server flags, and the 2,000 pairs are judged by S2's final bound. Without the flag an S1 that holds on a stopped block
  is an error that says how many pairs are missing; with `--out` (a dry run) it is refused. The earlier promotion.json is kept beside the new one; `rejudged.completed` says what was added.
- Tests: `tests/python/test_route_s_plumbing.py` (42), additions to `test_funnel.py` (5: the looks refuse only, no futility, no early promotion, the decision at 2,000 pairs is `judge`'s) and `test_gym_wiring.py` (2: the swap field of the wiring's and the real builder's candidates).

## Step 3: the book

`docs/rl/KEEP_TEST_V3.md`: a "Route S" section (when it applies, S1, S1 inside `promote`, S2, what is recorded, the parameters, rejudging, the undo, what is not verified), the switches table rows for `--route-s`, `rejudge --s1` and `--complete-block`, D66 as amended by D68 addendum 6 outcome 4.

## The two things the orchestrator does

**1. Rejudge v5 under S, after S1 finishes** (`judge-design/s1-v5/results.json` exists; run from the lab's tree once it holds these commits, under a QUIET line of the orchestrator's; about 1.9 h of arms on 16 processes; it promotes if S holds, and then writes `current.json`):

```
D:/spireline/src/sts2/.venv/Scripts/python.exe D:/spireline/fork/wt-lab/rl/gen0.py rejudge --cand D:/spireline/referee/agent/gen21/candidate-fight-v5 --base D:/spireline/referee/agent/gen20/candidate-chain --seeds-file D:/spireline/referee/lab/seeds/E21-2026-11-21-r2.json --agent-root D:/spireline/referee/agent --keep-rule v3 --min-gain 0.5 --route-s auto --s1 D:/spireline/referee/backlog/act3-week/judge-design/s1-v5/results.json --complete-block --procs 16 --lib D:/spireline/fork/wt-lab/out --prior-server auto --gpu-python D:/spireline/venv-gpu/Scripts/python.exe --server-procs 20 --note "D68 addendum 6 outcome 4: route S on v5 (S1 from the arrival exam on the generation-20 ruler; the block completed to 2,000 pairs under S2)"
```

`--prior-server auto ...` is the same transport both stored arms were played on (their summaries name the server), so the funnel's resume reuses them. Add `--lab D:/spireline/referee/lab` if a promotion should write `LAB/score/pending`. If S1 does not hold, no completion is needed: the command is a re-read of the 1,100 stored pairs under v3 (the funnel's futility stop stands) and plays nothing. If S1 holds and `--complete-block` is left out it stops with an error and plays nothing.
It registers test 0 (v5) in the ruler's ledger `gym-loop/arrival/gen20-candidate-chain/s1-ledger.json`: **do this before the train job runs `--route-s auto` on the next fight-swap candidate**, or that candidate takes draws 0 to 5 again.

**2. `LAB/jobs.json`, the `train` job's `cmd`: add `"--route-s", "auto"` after `"--min-gain", "0.5"`** (the `--min-gain` and `--keep-rule v3` entries stay; `--route-s auto` is refused under any other rule). Only after the lab's tree holds these commits (it moves to fork main at its presort: before then `gen0.py train` does not know the flag and the job fails and retries),
and after item 1 (the ledger). Back up `jobs.json` first and date a sentence in its `_note`, as the standing rules say. The undo is removing the two entries.

## Choices, differences from the design, and what is not verified

- **Ledger columns unchanged.** The brief asks `ledger_cells` to show S1's figure and S2's bound; the TSV's nine v2 columns are fixed (adding one changes the file's header for every reader), so the route (`S`/`AS`) is in `route`, and the figures are in the `guard` cell and in promotion.json.
- **Names**: the brief's `route_s(...)` is `keep_v2.route_s` (S1, then S2's final bound), with `route_s1` (S1 alone) and `s1_reading` (the reading and its identity check) beside it; the funnel's looks are `seq_call_v3(route_s=True)`.
- **Looks from 500 pairs apply to the collapse refusal under S as well** (the design names the 500 for both refusals); under v3 the collapse refuses from the second look at any size.
- **A stopped S1 fails the job** (exit 3, retried) rather than falling back to v3: a block must not be judged by the weaker rule because the night came. A pair S1 cannot be played for at all (no champion arms, one network) does fall back to v3, with the reason in promotion.json.
- **Test index** is one more than the highest used (not the count); a test played by hand (the v5 run) enters the ledger only through `rejudge --s1` (above).
- **Base-arm check not verified on the real path**: whether a champion run replayed through the GPU prior server reproduces its stored row bit for bit. If it does not, the check refuses the reuse and the champion plays the block afresh (time, not error). The completion of E21-r2 does not need it (nothing is reused unchecked).
- **Not run on real data.** No dry run of `rejudge` on v5's folders (the live exam held the machine and the brief said no real-path smoke of the judge); the first real figure is the orchestrator's rejudge above. The fields read from the exam's `results.json` are those `act3_starts.cmd_arrival_exam` writes, pinned by a test against `gym_gate.arrival_exam`'s output;
  the candidate's and the champion's network shas were checked by hand on v5's and generation 20's folders (`combat_policy.pt` bytes equal `model.json`'s `policy_sha256`; `built.swap` reads `fight` in v5's `agent.json`).
- **The ruler for a new champion** (when a promotion changes it) is built by the first fight-swap judgement against it (about 1.6 h inside the train job, resumable).

## To repeat

`STS2_REQUIRE_AOT=1 D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p test_keep_v3_route_s.py` (and `test_route_s_plumbing.py`, `test_funnel.py`, `test_gym_wiring.py`, `test_keep_v3.py`) from the fork tree with a built `out/`.
