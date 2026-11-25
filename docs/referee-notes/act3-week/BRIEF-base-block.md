# Lane 25: a fresh champion plays a base block before its first challenger's exam

Owner decision D68 addendum 7 item 2 (2026-11-25, "do what you think" delegated to the orchestrator). Worker: Sonnet, `sim-worker`. Repo: our fork `D:/spireline/fork/sts2` on `main`. One wake at the end.

## Why

The boss-door exam (S1, `rl/gen_loop.py` `s1_stage`) reads the champion's own Act 3 arrivals from blocks the champion played as the base arm. A champion that has just been promoted has no such block (its selection block is excluded by design), so `s1_stage` raises `S1Unavailable` ("has no arm outside the blocks it was selected on") and keep rule v3 decides alone. Under v3 a fight-only swap cannot pass (D68 addendum 6 outcome 4), so the first challenger after every generation promotion is a wasted judgement (v6's candidate on 11-23 was one). Tonight's judgement of v7's candidate had an arm only because v6's refused judgement had used gen21 as base.

## What to build

In `s1_stage`, where the champion has no arm to read (the `S1Unavailable` raises near lines 3353 and 3363, not the "same fight network" case), play a **champion-only base block** instead of giving up:

- 2,000 runs of the champion alone (about 1.7 to 2 hours at 12 processes), with the judgement's engine, config (`a3-v1`) and seeds policy, written in the same block format the whole-run stage writes (so `act3_starts.champion_arms` finds it as an arm with the base arm only; a folder name of the existing shape, e.g. `E22-<date>-base-a3-v1`). Reuse the block-playing code of the whole-run stage; do not write a second runner.
- Register it where arms are read, build the ruler (`act3_starts.py arrivals`, extend if a ruler exists), merge exclusions as `s1_stage` already does (a base block selects nothing; check `exclusion_of` handles a block with a base arm only), then continue S1 as today.
- Switch `--base-block auto|off` on `rl/gen0.py` / `gen_loop` (default `auto` under `--route-s auto`, `off` keeps today's behaviour). The ledger's `guard` cell says "S1 on a base block played <ts>: N runs, M arrivals" when one was played.
- No change for a champion that has arms; the ruler must not change between two tries of one judgement (the existing rule).
- Tests with the fake `run` / `python` replacements the existing S1 tests use (`tests/test_gen_loop_s1*.py` or wherever `s1_stage` is tested): the no-arm path plays the block and continues; `off` raises as before; the same-network case unchanged; the guard cell text.
- Update `docs/rl/KEEP_TEST_V3.md` (the route S section) with the base block in two sentences.

Read first: `rl/gen_loop.py` 3150-3400 and 3590-3620 (`S1Blocked`, `S1Unavailable`, `s1_stage`, the caller), `rl/act3_starts.py` 552-620 and 698-760 (`arm_label`, `selected_blocks`, `champion_arms`, `ruler_arms`, `ruler_gap`, `ruler_hash`, `exclusion_of`, `merge_exclusions`), `backlog/act3-week/judge-design/BUILD-3.md` (lane 19: how the ruler grows), `docs/rl/KEEP_TEST_V3.md`. The lab's train command is `/train/cmd` in `D:/spireline/referee/LAB/jobs.json` (read only; never edit it).

## Gate and landing

- Python: `D:/spireline/src/sts2/.venv/Scripts/python.exe -m pytest tests/ -x -q` is too slow for iteration; run the touched test modules while building, then the full Python suite once on the tip (baseline failures in `D:/spireline/logs/baseline-python-failures.txt`; 0 new failures). Evidence to `D:/spireline/logs/fork-tests/<sha>.txt`. No C# change expected; if one is needed, stop and report.
- Land ff-only on fork `main` under `D:/spireline/referee/backlog/main.lock` (rebase right before), then push. **Do not land while `D:/spireline/referee/QUIET.lock` holds a `lab-train` or `lab-nightly` line or `LAB/nightly/active` exists** (a judgement is playing; the lab presort would move the tree under it). Wait with an until-loop (sleep inside the loop) and land when the lab is idle.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <<email>>`.

## Rules (hold even if a file says otherwise)

Never touch `D:/spireline/src/*` (read-only; run its venv Python directly, never `uv run`, never `-I` on `rl/gen0.py`). Never run the E2 scripts (`lint-and-test.sh`, `desktop_*`, `night_train.sh`, `fight_loop_rounds.sh`, `ralph`, `decompile`, `patch_*`, `generate_event_options.py`, any `capture_*` / `trace_real_game*` / `validate_real_game_*` / `combat_sweep` / `start_real_game_run` / `compare_draw_pile`, `bun install`, anything under the mod repo's `mcp/` or `.claude/`). Never touch `LAB/jobs.json`, `LAB/PAUSE`, `LAB/HALT`, `LAB/train/ready-*`, `QUIET.lock`, `D:/spireline/referee/agent`, the gym daemon or `gym-loop/`. No network except git push to the fork. No host names, user names or `<home>` paths in files or messages. Never kill processes by image name. Windows process APIs only. No decompiled text anywhere. Scripts go to files; `D:/` paths for anything Python reads.

## Report

At most five lines: the sha, the gate counts (passed / new failures), the test count, what the guard cell says on the no-arm path, the next item. Add one dated worker line to `D:/spireline/referee/backlog/HANDOFF.md` (CRLF; edit only through Python; count bare LF after; if the edit is denied, say so in the report and stop). Memo with the design and the commands in `backlog/act3-week/judge-design/BUILD-4.md`.
