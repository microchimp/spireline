# Lane 6c: the fight loop's output reaches the run player by itself, or the trainer pauses

Written 2026-11-19 by lane 6c (Sonnet). Fork branch `feat/gym-wiring` (worktree `D:/spireline/fork/wt-gym-wiring`), commit `a0768b95`, landed on fork main 2026-11-19 02:02Z (ff-only over `e1250b69`, pushed; no night or main.lock standing).

## What was wrong, in one paragraph

The fight loop ("the gym": a trainer that practises the fight brain on saved fight positions, plus a gate that compares each new brain with the current one on a fixed board) promoted its player v3 on 2026-11-09. Nothing carried v3 into the run player until a worker built the candidate by hand on 2026-11-18. For nine days (the state file says 2026-11-09 12:00Z; the brief said 11-13) the trainer's card hours bought nothing, and nothing in code said so.

## What changed (all in `rl/gym_wiring.py`, hooks in `rl/gym_loop.py`, one line in `rl/gym_clock.py`)

1. **A promoted player queues its own run candidate.** Right after the gym promotes a player, and at every daemon start, the loop looks at the latest promoted player. If neither the champion (`agent/current.json`) nor any candidate folder carries its fight network, it builds `agent/gen<k+1>/candidate-fight-v<N>` (k = the champion's generation): the champion's folder with only the fight network swapped. It then writes the lab's marker `LAB/train/ready-<k>-g<k+1>-fight-v<N>`: first line the UTC stamp as ever, second line `keep_rule: <the lab's rule now>` (read from `jobs.json`: a `train.keep_rule` field if present, else the train command's `--keep-rule`). Lane 6a's marker reader uses the same two-line form (`keep_rule: v3`), checked in its branch. The lab's train job judges it; the gym promotes nothing itself. If the champion changes, the next promotion builds on the new champion. A failed build is logged once and retried every ten minutes. Re-running changes nothing (no second build, no second marker, a consumed `done-` marker counts).
2. **The trainer pauses when nothing uses it.** A player is "used" when the champion's fight network is the player's, or a candidate carrying it is queued (a marker) or judged (`promotion.json`). Not used 24 hours after its promotion: the loop writes `LAB/alerts/gym-unconsumed.txt` (the reason, why the build failed) and stops generating, gating and training. It resumes by itself when the player becomes used, or when the orchestrator removes the file (which also means "do not alert on this player again"). The wait shows in the loop's clock as `unconsumed`; the status file says `paused` and `generation: off`.
3. **The gate's gain next to the run judge's verdict.** When a candidate that was built with a promoted player in place of its base's network gets its `promotion.json`, the loop writes one `run judge:` line to `loop.log`, one row to `gate/run-judge.jsonl` (version, gate checkpoint, candidate, verdict, pairs, keep rule, boss kills Act 1/2/first Act 3, wins, candidate then base) and ends that day's `daily` line with it. A log line cannot be edited afterwards, so the join is a new line plus a sidecar keyed by checkpoint and version.

## Figures (nothing played; one scratch build of 8 s)

- Rebuilt v3 on generation 17 with the new builder into a scratch folder and compared with the hand-built `gen18/candidate-fight-v3`: all 11 weight, ONNX and prior files have identical bytes; `agent.json` and `train.json` differ only in the build time, the "why", the lineage and the note text.
- The same call through the daemon's path (queue, GPU-venv child process, marker) on scratch folders: built in 7 s, marker `ready-17-g18-fight-v3` with `keep_rule: v3` (the live jobs.json's rule), a second call did nothing.
- On the real state (read only): v3 is the champion's fight network (generation 18), so the first start of the new code builds nothing and pauses nothing. It will log two `run judge:` lines: v3 (gen18 candidate, promoted under the then-rule v2, first Act 3 boss kills 158 against 159, wins 2 against 0 of 2,000 pairs) and an old one for v2 (no Act 3 figures in that old document).
- 26 new tests (`tests/python/test_gym_wiring.py`): queue, rule field, idempotence, champion change, half-built folder, failed build, the three consumption states, the 24-hour pause, resume by use, resume by removing the file and no second alert, the join, the daily line, the daemon's tick and pause, and the real builder on the repo's tiny fixture network. Python-only gate (select mode, tests of the changed modules plus the smoke set): 365 tests run, 0 new failures, 0 flakes (`gate_py bad=0`); evidence in `D:/spireline/logs/fork-tests/a0768b95.txt`.

## What the orchestrator must do

- **The running loop keeps its old code until restarted.** Restart: stop it with `gym_loop.py stop` at a verdict or idle point, check out fork main in `D:/spireline/fork/wt-gym-loop-run`, republish that worktree's own `out/` (the engine moved since 350dbe3e; the gate then replays the incumbent's games once on the new engine tag), start with the same line it runs now plus nothing: `rl/gym_loop.py run --root D:/spireline/referee/gym-loop --max-epochs 8 --gate-every-min 120 --teacher-store D:/spireline/referee/run-teacher --procs 0 --gate-procs 4 --trainer-extra-rows-root D:/spireline/referee/run-cheap --trainer-extra-window 150000` (`--wiring on` is the default; `--wiring off` gives the old behaviour). The builder needs the GPU venv (torch and onnx) and a matching `out/` in that tree.
- `jobs.json`: nothing needed. (If lane 6a adds a `train.keep_rule` field, the marker follows it.)
- Remove `LAB/alerts/gym-unconsumed.txt` to resume a paused loop; it will not come back for that player.

## Not done, not verified

- **Not run live.** The daemon's main loop (tick between steps, the pause, the build inside a promotion) is covered by unit tests of its parts and by reading, not by a running daemon (no heavy runs allowed); the first real promotion after the restart is the live test. Watch `loop.log` for `wiring:` lines.
- A second promotion while the first candidate still waits queues a second marker (the lab judges them in order). Superseding the older one was left out.
- The "used" test compares fight network hashes; a candidate that only inherited a network from its base is not counted as having carried it (needs `built.base` in `agent.json`, which every built candidate has).
- Task 3 is minimal: no rewrite of the gate's own verdict rows (a concurrent reader could hold the file); readers join `gate/run-judge.jsonl` by checkpoint.

## Repeat the checks

- Tests: `STS2_LIB_PATH=<a built out/> D:/spireline/src/sts2/.venv/Scripts/python.exe -I -m unittest discover -s tests/python -p test_gym_wiring.py` from the worktree (26 tests, about 5 s).
- State of the latest promoted player, nothing written: `D:/spireline/venv-gpu/Scripts/python.exe -I rl/gym_wiring.py queue --dry-run`.
- Builder comparison: build into a scratch agent root with `python rl/gym_wiring.py build --base <gen17 candidate-cheap-v2> --player-dir <players/v3> --agent-root <scratch> --target 18 --tag fight-v3 --why test` and compare file hashes with `agent/gen18/candidate-fight-v3`.
