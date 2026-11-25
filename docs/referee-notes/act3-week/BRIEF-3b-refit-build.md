# Lane 3b (build): the boss chain, fitted, built into a candidate, ready for the judge

Written 2026-11-19T02:15Z by lane 3 (Opus 5.5) for a Sonnet lane, to be done in one sitting.

**Read first:**
- `COMMON.md` in this folder. Its rules hold over anything here.
- `REFIT-WIN-DESIGN.md` beside this brief: what and why. Sections 2 and 5 are the specification.
- The fork's `CLAUDE.md`.

**Templates to copy patterns from (read them, do not import from them blindly):**
- `rl/act2_chance.py`: rows from run records with the run brain's nets, a trunk warm-started from `run_value.npz`, the fit, the report, `hive_block`, `part_of_seed`, `run_weights`, `below_normal`, `SupervisedPool`.
- `tests/python/test_act2_chance.py`.
- The route-elite path, a per-option bonus on the chooser plus an agent part plus a recipe part:
  - `imitation_chooser.BlendedPolicy.route_bonus` and `_vrun_with_bonus`;
  - `gen_loop.route_elite_identity`, `Agent.route_elite`, `load_agent`, `Agent.describe`, `Agent.recipe`;
  - `macro_recipe.full_recipe`, `split_recipe`, `elite_part`;
  - `tests/python/test_route_elite.py` and `route_elite_screens.py`.
- `gen_loop.build_vrun_candidate`, a one-part candidate build.
- `D:/spireline/referee/backlog/act2-build/FIGHT-V3-V-build.py` and `FIGHT-V3-V.md` (lane V's candidate and smoke).

## What you build, in one paragraph

You build a new module, `rl/boss_chain.py`. It builds training rows from the plain-run stores (generations 15 to 18) and fits a two-output network: `q2` is the chance of getting past the Act 2 boss, and `q3` the chance of getting past the first Act 3 boss once past the Act 2 boss. The network starts from the champion's run-brain layers and adds 8 numbers for the deck's fight forecast against Act 3's fights and one offset per generation. The module reports the network's calibration and can read it at play time with numpy alone.

The chooser `BlendedPolicy` then adds `kappa_act x log(chance of getting through)` to each option's value in Acts 2 and 3:
- Act 2, floor 32 or lower: `log q2 + log q3`.
- Act 2 floor 33 and Act 3 up to floor 47: `log q3`.
- Act 1 is unchanged byte for byte.

Kappa is `[0, 10, 10]` floors per nat and the chances are clipped below at 0.002. An agent gets this from an `agent.json` block `boss_chain` and a recipe part `+chain:<8 hex>@0/10/10`. Agents without it play exactly as before. Then build `agent/gen19/candidate-chain` from the champion `gen18/candidate-fight-v3`, check it offline and with a 20-seed smoke, and hand the orchestrator the marker text.

## Machine and timing rules for this lane

These come on top of COMMON.

- **What heavy means here.** The row build (4 processes), the fit (graphics card), the flip check (1 process, about 15 minutes), the 20-seed smoke (4 processes, under 5 minutes) and the gate.
- **When heavy steps may run.**
  - Only while `D:/spireline/referee/LAB/nightly/active` does not exist.
  - Only while `D:/spireline/referee/QUIET.lock` holds no line but `gym-loop`. Today `act3-replay` (lane 4) may hold one: wait with a Monitor until-loop, never by ending your turn.
  - Never between 10:30Z on 2026-11-19 and the end of tonight's real block (about 21:00Z; the `active` file goes away).
- **Do not touch** QUIET.lock, `LAB/jobs.json`, markers, `current.json` or `promotions.tsv`.
- **Priority.** Everything heavy runs BelowNormal through the Windows priority class (`act2_chance.below_normal` does it), with spawn pools.
- **Landing.** Land before 10:30Z, or after the block has ended.
- **If the clock bars a step,** do every light step you can (code, tests, memo draft). Then wait or stop and report what is left; do not widen the task.
- **Where you may write:**
  - your worktree `D:/spireline/fork/wt-chain`;
  - `D:/spireline/logs/boss-chain/` (rows, logs, smoke);
  - `D:/spireline/logs/gym-loop/chain-gate.sh`, plus the gate's own `D:/spireline/logs/gate-py-chain-3b/`;
  - `D:/spireline/logs/fork-tests/<hash>.txt`;
  - `D:/spireline/referee/agent/boss-chain/v1/` (the fit);
  - `D:/spireline/referee/agent/gen19/candidate-chain/`;
  - this folder (your memo `LANE-3b.md`).
- **Scripts.** Write them with the Write tool, never shell heredocs with quotes. Use `D:/` paths in anything Python reads.

## Steps

### 1. Worktree (light)

```
git -C D:/spireline/fork/sts2 fetch origin
git -C D:/spireline/fork/sts2 worktree add D:/spireline/fork/wt-chain -b feat/boss-chain main
```
Then, in PowerShell: `New-Item -ItemType Junction -Path D:\spireline\fork\wt-chain\out -Target D:\spireline\fork\sts2\out`. Check that local `main` equals `origin/main` first.

### 2. `rl/boss_chain.py` (new; light)

**Import rules.** Lazy imports as in `act2_chance.py`: the module must import with numpy alone. `fit` adds torch. `build` and `flips` need the native library, through `run_train.features` and `imitation_chooser`. Never print or write a seed into any JSON or log.

**Constants:**
- `FORMAT = "boss-chain/1"`, `STORES = (15, 16, 17, 18)`, `STORE_ROOT = D:/spireline/referee/run-cheap`, `READ_GEN = 18`.
- `PASS_B1, PASS_B2, PASS_B3A, WON = 18, 34, 49, 53` (final floor at or above which the run got past).
- `LAST_PRE_B2, LAST_PRE_B3A = 32, 47` (decision floors before those bosses).
- `ACT2_ROWS_PER_RUN = 12`, `CLIP = 0.002`, `KAPPA = (0.0, 10.0, 10.0)`, `H3_SIZE = 8`.
- `GENS = STORES`: offset index = position in `STORES`.

**Functions:**
- `passed(final_floor) -> (b1, b2, b3a, won)` from the final floor (53 means won).
- `region_queries(region)` and `region_block(fight, rows, region)`: `act2_chance.hive_queries` and `hive_block` with the region as a parameter. H3 = `region_block(nets.fight, rows, vocab.REGION_GLORY)`. Act 3 is always that region; a test holds it.
- `chain_rows(records, nets, skip_seeds)` takes the decisions of each record that passes `train.eligible_records`' filter (generation at most 18, not truncated, current era, deduplicated by (generation, seed)). Use the decisions that have a `chosen` option and whose chosen option is scorable (`train._chosen_scorable`). With `st = entry["state"]`:
  - `act_index == 1` and `floor <= 32`, run past B1: an Act 2 row, with `m2 = 1`, `y2 = b2`, `m3 = b2`, `y3 = b3a`.
  - `act_index == 2` and `floor <= 47`: an Act 3 row, with `m2 = 0`, `m3 = 1`, `y3 = b3a`.
  - Anything else gives no row.
  - At most 12 Act 2 rows a run, chosen deterministically by a hash of `(seed, decision index)`. All Act 3 rows are kept.
- What each row holds:
  - the chosen option's row `human_prior_infer.option_rows(nets, view, [option])[0]` (1,863 numbers, H from the champion's FightNet), with `view = shards.state_view(rec, entry)` and the option from `shards.entry_decision(entry)`;
  - `dense` (float16) and `counts` (uint8) from `models.value_inputs`, plus `h3`;
  - `gen`, `run`, `floor`, `act`;
  - flags `entry2` (first Act 2 row of the run), `entry3` (first Act 3 row), `door` (last Act 3 row) and `reached48` (final floor at least 48, or a win);
  - `pv`: the champion's own forecasts on the same row, two floats from `nets.value.floor_probs` (P(final at least 34) and P(final at least 49));
  - `part`: `report` for generation 18 runs whose seed hash falls in the report fifth (an `act2_chance.part_of_seed`-style hash with salt `boss-chain-report`), never for other generations; `val` for a tenth of the rest; else `train`.
- Seeds of other blocks are skipped (`act2_chance.other_block_seeds()`).
- `run_weights_masked(run, mask)`: each run's rows in a head weigh 1 / (its rows in that head), scaled to a mean of 1 over the head's masked rows.
- `init_params(value_arrays, seed)`:
  - the champion's trunk (embeddings, `hidden1` with 8 zero columns for H3, `hidden2`);
  - `head.weight` (2, 256) small uniform times 0.1, `head.bias` zeros(2);
  - `gen_off` (2, 4) zeros.
  - With None, a fresh init for the planted-relation tests.
- `np_logits(params, dense, counts, h3, gen) -> (n, 2)` in numpy. Its torch twin is used by the fit. Dropout sits before `hidden2`, as in the run brain, at 0.3.
- `fit_arrays(train, val, init, ...)`:
  - masked BCE, with each head's loss averaged over its masked rows with run weights, and the two heads summed;
  - AdamW at lr 1e-4, weight decay 1e-2, batch 512, 4 epochs, 4 evaluations an epoch, patience 8, cosine schedule (copy `act2_chance.fit_arrays`);
  - keep the evaluation with the lowest validation loss.
- `write_model(prefix, params, fight_arrays, meta)` writes `boss_chain.npz` (and `.pt`):
  - the weights, the FightNet arrays copied from the champion's `run_value.npz` (`fight/` part) and `fight_sha256`, the sha of those arrays;
  - meta: format, sizes, `READ_GEN`, `GENS`, `q4` (see below), counts per generation and head (runs, rows, positives; no seeds) and the fit record.
- `q4`: computed from the rows' runs as (wins + 1) / (runs past the first Act 3 boss + 2). It is recorded only, never used in a choice.
- `class ChainScorer(path)`, numpy only:
  - `.sha256` (of the file) and `.fight_sha256`;
  - `.log_q(rows)` for (n, 1,863) rows: H3 is computed from the file's own FightNet, the offset is read at `READ_GEN`, and the result is `log(clip(sigmoid(logit), CLIP, 1))` with shape (n, 2).
- `chain_terms(log_q, act_index, floor, kappa) -> np.ndarray | None`:
  - None when `kappa[act_index]` is 0, when `act_index` is 0 or not 1 to 2, or when `floor > 47`;
  - Act 2 with `floor <= 32`: `kappa x (log_q[:,0] + log_q[:,1])`;
  - otherwise `kappa x log_q[:,1]`.
- `fight_sha_of(run_value_npz)`: the sha of its `fight/` arrays, computed the way `write_model` computes `fight_sha256`.

**Commands (argparse `main`):**
- `build --stores 15,16,17,18 --run-value NPZ --out DIR --procs 4`:
  - find the shards through `gen_loop.find_manifests(STORE_ROOT/<g>/jobs)` and each manifest's `run_shards` (only jobs whose `shards/shards.json` exists, so complete ones);
  - pool tasks one shard file each, with the nets loaded once per worker, at most 4 processes, BelowNormal, and lost shards retried once (copy `act2_chance.cmd_build`);
  - write `rows.npz` and `build.json` (shard count, lost shards, counts per generation and head, run-brain sha, time).
- `fit --rows DIR --init NPZ --out DIR --seeds 0,1,2 [--epochs 4 --lr 1e-4 --weight-decay 1e-2 --dropout 0.3]`: in the GPU venv, keep the seed with the lowest validation loss, write `boss_chain.npz` and `fit.json`.
- `report --rows DIR --model NPZ --out DIR [--champion]`, numpy, on the `report` part only, using the stored `h3`. For `q3` at `entry3` and at `door` among `reached48`, and for `q2` and `q2 x q3` at `entry2`, it prints and writes:
  - n and runs, mean forecast and actual;
  - AUC;
  - calibration by decile (cells under 20 not shown);
  - the logistic slope of the outcome on the logit.
  - With `--champion`, the same for the champion's `pv` beside it.
  - A `verdict`: `pass` when the door AUC is at least 0.70, the door slope is between 0.7 and 1.3, and the door mean is within 3 points of actual.
  - Output: `report.json` and `report.md`.
- `flips --champion DIR --candidate DIR --store D:/spireline/referee/run-cheap/18 --runs 400 --out JSON`, in the emulator venv, one process:
  - For generation 18 runs in the report part (the fit never saw them), read `decisions.d/<seed>.record.json`.
  - For every decision with a `chosen`, rebuild `decision` and `view` as `chain_rows` does. Call `begin_run(seed)` when the policy has it, then `pick(view, decision, None)` on both agents' `macro_policy()`.
  - Count by act (from `act_index`) and by screen kind: decisions, changed share, and the champion's replay agreement (its pick equals the recorded `chosen`).
  - Also count:
    - Act 3 rest sites: the heal share at HP under 70 in 100 of max, for each agent;
    - Act 3 shops: the potion share of purchases, for each agent;
    - Act 2 and 3 route screens: the elite-room share, for each agent.
  - Write the JSON, with no seeds in it.

### 3. The chooser and the agent (light)

- **`rl/imitation_chooser.py`, `BlendedPolicy.__init__`:** new keyword arguments `chain` (a path or a `ChainScorer`) and `chain_kappa` (three numbers of at least 0). Both or neither, else ValueError.
- **`chain_extra(view, decision, rows)`:** None unless the chain is set, `kappa[act]` is above 0, the floor is at most 47, the screen has 2 or more options and all of them score. Otherwise `chain_terms(self.chain.log_q(rows), act_index, floor, kappa)` as a list.
- **In `pick`:**
  - When the chain may apply, compute `rows = option_rows(self.nets, view, options)` once, and pass rows and terms down.
  - The student path with a lambda of 0 and the no-screen path then go through `_vrun_with_bonus` with `extra = route bonus + chain terms`; take probs from `self.nets.value.floor_probs(rows)`, the same numbers as `floor_probs`.
  - `_decide` gains a `chain` argument (a list or None). Inside it, `u = values + chain` replaces `values` in `blend_rest`, `blend_pick`, `distribution` and `skip_gap`.
  - The recorded `Pick.values` and `p_floor` stay the run brain's (`values`, `probs[k]`).
  - When the chain does not apply, every line runs as today.
- **`describe()`:** adds `"boss_chain": "<8 hex>@<k1>/<k2>/<k3>"` only when set.
- **`rl/macro_recipe.py`:**
  - `chain_part(sha8, kappa) -> "+chain:<8 hex>@0/10/10"` (numbers as `format_lambda` writes them), a `_RECIPE_CHAIN` regex and `parse_chain(recipe) -> (sha8, kappa) | None`;
  - `split_recipe` cuts at the chain part too;
  - `full_recipe(..., chain=None)` appends it last, after stakes, hold and elite. A recipe without it is unchanged.
- **`rl/gen_loop.py`:**
  - `Agent` gains `chain: str | None = None` and `chain_kappa: tuple[float, float, float] | None = None`.
  - `recipe()` passes `chain=(sha8, kappa)`; `describe()` adds `boss_chain` when set; `macro_policy()` passes `chain` and `chain_kappa` to `BlendedPolicy`.
  - `boss_chain_identity(meta, folder)` reads `agent.json`'s block `{"file", "sha256", "kappa": [k1, k2, k3], ...}`. It checks that the file exists and its sha256 equals the block's, and that kappa is three numbers from 0 to 50. It checks that `ChainScorer(file).fight_sha256 == boss_chain.fight_sha_of(folder/run_value.npz)`: the chain was fitted with this agent's FightNet. It returns (path, kappa) or None. Errors name the folder, never a seed.
  - `load_agent` calls it, refuses a chain on a macro that is not blended, and builds the Agent with it. The existing recipe check then covers the `+chain` part.
  - `build_chain_candidate(base, chain_dir, agent_root, target, *, why, kappa, tag="chain")` mirrors `build_vrun_candidate`:
    - copy every base file but `VRUN_SWAP_NOT_COPIED`, keeping the value files;
    - `write_prior_model_json(cand, target)`;
    - copy `boss_chain.npz` and `fit.json` (as `boss_chain.json`) from `chain_dir`;
    - `agent.json`: the base's meta minus lineage, note and built, plus `generation`, `built_on`, `written`, `boss_chain` (file, sha256, kappa, clip, q4, `fit_dir`, `report_verdict`), `recipe = full_recipe(..., chain=...)`, and a built block with `swap: "chain"` and a note saying only the chain and recipe differ;
    - `train.json`;
    - end with `load_agent(cand)` and check that `screens.differing(cand, base) == ["settings"]`.
  - It never writes a marker and never writes over an existing folder.
- **`rl/gen0.py`:**
  - add `"boss_chain"` to the identity keys at the real-arm summary check (the tuple with `route_elite`, about line 1118);
  - add a subcommand `build-chain --base DIR --chain-dir DIR --agent-root DIR --target N --kappa 0/10/10 --tag chain --why TEXT`. It prints the candidate path and the marker name `ready-<base gen>-g<target>-<tag>`, and writes no marker.

### 4. Tests (light): `tests/python/test_boss_chain.py`

Use synthetic records and nets as `test_act2_chance.py` and `test_route_elite.py` do. Each test is one assertion family:

1. `passed`: 17, 18, 33, 34, 48, 49 and 53.
2. Row choice:
   - no Act 1 rows;
   - Act 2 rows only for runs past B1, with `m3 = b2`;
   - Act 3 rows only at floor 47 or below;
   - floors 48 and later excluded;
   - the cap of 12 deterministic;
   - an unscorable chosen option gives no row.
3. Parts: only generation 18 has `report` rows; the same seed always lands in the same part.
4. Masked run weights.
5. numpy and torch logits agree within 1e-5; H3 columns start at zero, so H3 changes no logit at initialisation.
6. A planted relation (`y3` follows one dense column) is learned, with report AUC above 0.8.
7. `chain_terms` in every act and floor case, and the clip.
8. `ChainScorer` reads the offset at 18.
9. A FightNet sha mismatch refuses the agent.
10. `BlendedPolicy`:
    - with `chain=None`, picks, values, `p_floor` and `last` are identical to today's on the route-elite and mask screen fixtures;
    - a chain giving every option the same chance changes no pick on Act 2 and 3 screens;
    - a chain strongly favouring option j makes j the pick on a rest screen (the `blend_rest` path), a card screen (`blend_pick`) and a screen with no student or prior (`_vrun_with_bonus`);
    - on an Act 1 screen any chain leaves everything identical.
11. Agent:
    - `+chain:<8 hex>@0/10/10` sits last in the recipe;
    - `describe()` names it;
    - a missing file, a wrong sha, kappa out of range or a non-blended macro is refused;
    - an `agent.json` without the block gives the same recipe and description as before (pin one existing recipe string).
12. `macro_recipe`: the round trip, and `split_recipe` the same with and without the chain part.
13. `build_chain_candidate` on a fake base folder:
    - files byte for byte except the listed ones;
    - `differing == ["settings"]` and `kind_of` None;
    - a second build refuses to overwrite.
14. The `gen0` identity check with `boss_chain`.

### 5. Gate and landing (heavy; before 10:30Z or after the block)

Write `D:/spireline/logs/gym-loop/chain-gate.sh` (copy `keep-u-gate.sh`), with `cd /d/spireline/fork/wt-chain`, `TAG=chain-3b WTN=wt-chain` and `EXTRA="test_boss_chain.py test_route_elite.py test_imitation_chooser.py test_gen_loop.py test_vrun_swap.py test_screens.py test_act2_chance.py"`. Run it in the background with output to `D:/spireline/logs/boss-chain/gate.log` and wait with Monitor. Pass means 0 new failures against `D:/spireline/logs/baseline-python-failures.txt`.

Land as COMMON says:
1. Write `main.lock` with your lane name and the UTC time.
2. Fetch, rebase onto `origin/main`, and check that local main equals origin/main.
3. `git merge --ff-only`, then push.
4. Remove the lock.

Abort and release if main moved under you. The trailer is `Co-Authored-By: Claude Sonnet 5.5 <<email>>`, unless your harness sets its own; say which you used. Save the gate's last 5 lines plus its counts line to `D:/spireline/logs/fork-tests/<short hash>.txt`.

The lab's tree moves to fork main at its next presort, which is harmless: no agent has a `boss_chain` block yet.

### 6. Rows (heavy: 4 processes, about 45 minutes)

From `D:/spireline/fork/wt-chain`, with `STS2_LIB_PATH=D:/spireline/fork/wt-chain/out` and `STS2_ALLOW_STALE_NATIVE=1`:
```
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py build --stores 15,16,17,18 --run-value D:/spireline/referee/agent/gen18/candidate-fight-v3/run_value.npz --out D:/spireline/logs/boss-chain/rows --procs 4
```
Expect:
- about 0.75 million Act 2 rows and 0.5 million Act 3 rows;
- about 62,000 runs in `q2` (17,500 positive);
- about 17,500 runs in `q3` (1,700 positive) or more, as generation 18 grows.

If memory runs short, set `ACT2_ROWS_PER_RUN` to 8 and say so.

### 7. Fit (graphics card, 15 to 30 minutes)

```
D:/spireline/venv-gpu/Scripts/python.exe rl/boss_chain.py fit --rows D:/spireline/logs/boss-chain/rows --init D:/spireline/referee/agent/gen18/candidate-fight-v3/run_value.npz --out D:/spireline/referee/agent/boss-chain/v1 --seeds 0,1,2
```
If the best evaluation is the very first one, the rate is too high (A2's experience). Rerun once with `--lr 5e-5` and record both.

### 8. Smoke test of the fit (minutes): the go or no-go

```
D:/spireline/venv-gpu/Scripts/python.exe rl/boss_chain.py report --rows D:/spireline/logs/boss-chain/rows --model D:/spireline/referee/agent/boss-chain/v1/boss_chain.npz --out D:/spireline/referee/agent/boss-chain/v1 --champion
```
- **What the champion's own columns should show.** About 0.72 AUC at Act 3 start and about 0.59 at the door; lane 3 measured those on stored forecasts. A big difference means the rows are wrong: stop and report.
- **Go.** `verdict: pass`, meaning door AUC at least 0.70, slope 0.7 to 1.3 and mean within 3 points.
- **Stop with no candidate** if the door AUC is under 0.65.
- **Between 0.65 and 0.70:** build, but say so in the first line of your report.

No other retries and no tuning of the marks.

### 9. Build the candidate (light)

```
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py build-chain --base D:/spireline/referee/agent/gen18/candidate-fight-v3 --chain-dir D:/spireline/referee/agent/boss-chain/v1 --agent-root D:/spireline/referee/agent --target 19 --kappa 0/10/10 --tag chain --why "Act 3 week (D68 item 3): the run brain's option values see the chance of getting past the Act 2 and first Act 3 bosses"
```

### 10. Flip check (1 process, about 15 minutes): the vetoes

```
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py flips --champion D:/spireline/referee/agent/gen18/candidate-fight-v3 --candidate D:/spireline/referee/agent/gen19/candidate-chain --store D:/spireline/referee/run-cheap/18 --runs 400 --out D:/spireline/logs/boss-chain/flips.json
```
**Veto** (no marker; report it) if any of these hold:
- any Act 1 decision changed;
- the champion's replay agreement is under 98 in 100 (the check is broken);
- Act 2 or Act 3 changed share is over 50 in 100;
- at Act 3 rest sites with HP under 70 in 100, the heal share falls by more than 0.10.

**One allowed fallback, for the over-50 case only:** build once more with `--kappa 0/5/5 --tag chain-k5` and run flips again.

**If fewer than 3 in 100 Act 3 decisions changed,** report "expect no effect": the orchestrator decides whether to judge it.

### 11. Emulator smoke (4 processes, under 5 minutes)

```
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py seeds --name CHAIN-SMOKE-2026-11-19 --n 20 --out D:/spireline/logs/boss-chain/smoke-seeds.json
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py emu --seeds-file D:/spireline/logs/boss-chain/smoke-seeds.json --config a3-v1 --procs 4 --prior-server auto --gpu-python D:/spireline/venv-gpu/Scripts/python.exe --gen-dir D:/spireline/referee/agent/gen19/candidate-chain --out D:/spireline/logs/boss-chain/smoke
```
Use the same environment variables as step 6, and check how lane V ran it (`FIGHT-V3-V.md`). Pass means: rc 0, 20 runs, no crashes or lost workers, and the summary's agent block names `boss_chain`. Record the floors reached; they are not a measure.

### 12. Hand-off (light)

Write the memo `D:/spireline/referee/backlog/act3-week/LANE-3b.md`, at most two pages. It covers:
- what landed (the sha);
- the gate counts;
- the build counts;
- the fit record, including the kept seed and the validation losses;
- the report table (chain against champion);
- the flip table;
- the smoke result;
- the candidate's file shas;
- what is unverified;
- the commands above as run.

**The marker for the orchestrator to write** (you do not write it):
- **Name:** `D:/spireline/referee/LAB/train/ready-18-g19-chain` (or `-chain-k5`).
- **Content:** one line, the UTC time of writing, for example `2026-11-19T21:40:00Z`.
- **Conditions:**
  - the night block has ended;
  - lane 1's strict Act 3 reading is live in the lab tree;
  - no other `ready-*` marker stands.
- **Second block.** Ask the orchestrator to pre-register it (4,000 pairs pooled), whatever the first block reads, via the lab's extension or by hand with `gen0.py promote --pool-block` / `rejudge --pool-block` (`docs/rl/KEEP_TEST_V3.md`). The rule's +1.0 extension bar is above the design's central +0.6.

**Report to the orchestrator, at most five lines:**
- the landed sha and the gate counts (tests run / new failures);
- the door AUC, chain against champion, and the verdict;
- the Act 2 and Act 3 changed shares, with Act 1 at 0;
- the candidate path and the marker line, or the veto that stopped it;
- your context size.
