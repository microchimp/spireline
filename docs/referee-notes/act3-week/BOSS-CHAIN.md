# The boss chain: built, fitted, landed, two candidates ready (lane 3b)

Written 2026-11-19T03:45Z by lane 3b (Sonnet 5.5). Design: `REFIT-WIN-DESIGN.md`; brief: `BRIEF-3b-refit-build.md`. Paths are under `D:/spireline/`.

Words used:
- **Run brain:** the network that scores a position in the middle of a run (`run_value.npz`). It forecasts the floor the run ends on.
- **Boss chain:** a second, small network. It forecasts two chances: getting past the Act 2 boss (`q2`) and, once past it, getting past the first Act 3 boss (`q3`).
- **Door:** the last choice before a boss. **AUC:** how well a forecast tells winners from losers (0.5 is chance, 1 is perfect).
- **kappa:** floors per unit of log-chance that the player adds to each option's value. Here 0 in Act 1, 10 in Acts 2 and 3.

## What landed

Fork main `c7e10c95` (rebased on `7dd6474e`, ff-only, pushed). Commit trailer `Co-Authored-By: Claude Sonnet 5.5`.
- `rl/boss_chain.py` (new): builds rows from the plain-run stores of generations 15 to 18, fits the chain, reports it, and replays stored runs to count what it changes.
- `rl/imitation_chooser.py`: `BlendedPolicy(chain=, chain_kappa=)`. On Act 2 and Act 3 screens up to floor 47 (two or more options, all scored) each option's value gains kappa times the log chance. The blend, the guard, the draw and the skip gap read it; the recorded values and floor distributions stay the run brain's.
- `rl/macro_recipe.py`: the recipe part `+chain:<8 hex>@0/10/10`, last. `rl/gen_loop.py`: `Agent` fields, `boss_chain_identity` (file sha, kappa 0 to 50, the chain's FightNet must equal the run brain's), `build_chain_candidate`. `rl/gen0.py`: `build-chain`, and `boss_chain` in the emulator arm's identity check.
- Tests: `tests/python/test_boss_chain.py` (63) and `boss_chain_screens.py`. With no chain every choice, value and recipe is exactly the unmodified chooser's (pinned on 40 screens made by running the untouched main tree; `test_route_elite` also passes).
- Gate (Python-only, select mode, the rebased tip): 586 tests run, 0 new failures, 0 flakes. Evidence: `logs/fork-tests/c7e10c95.txt`. I ran it twice (before and after rebasing onto lanes 1, 4 and 6a).

## Rows and fit

- **Rows** (4 processes, BelowNormal, 25 minutes, no lost shard): 1,907 shards, 87,619 records, 62,369 runs, 1,266,965 rows (742,092 Act 2, 524,873 Act 3). Matches the design's counts: past the first Act 3 boss 1,681 runs, 67 wins (q4 recorded 0.040, never used). Parts: 1,116,267 fit, 124,442 chose the epoch, 26,256 report rows (a hash-fifth of generation 18's runs).

| Generation | q2 runs (positive) | q3 runs (positive) |
|---|---|---|
| 15 | 8,522 (1,377) | 1,377 (58) |
| 16 | 8,886 (2,076) | 2,076 (188) |
| 17 | 38,723 (12,048) | 12,048 (1,227) |
| 18 | 6,238 (2,024) | 2,024 (208) |

- **Fit** (graphics card, under 2 minutes): 3 seeds, 4 epochs, rate 1e-4, batch 512, dropout 0.3. Kept seed 0, best at step 2,180 (end of the first epoch; the best evaluation was never the first, so no rate retry). Validation loss q2 0.4306, q3 0.2589 (seeds 1 and 2: 0.6899 and 0.6904 against 0.6895). The loss rises after the first epoch: more epochs overfit.

## The smoke test (held-out generation 18 runs, never fitted on)

| Cell | Runs | Mean forecast | Actual | AUC chain | AUC run brain | Slope chain |
|---|---|---|---|---|---|---|
| q3 at the door, runs that reached the boss | 244 | 0.145 | 0.164 | **0.854** | 0.642 | 0.92 |
| q3 at Act 3 start | 384 | 0.087 | 0.104 | 0.783 | 0.742 | 0.79 |
| q2 at Act 2 start | 1,228 | 0.293 | 0.314 | 0.764 | 0.741 | 1.06 |
| q2 x q3 at Act 2 start | 1,228 | 0.026 | 0.033 | 0.679 | 0.641 | 0.54 |

Verdict `pass` (door AUC 0.854, slope 0.92, mean within 2 points). The run brain's own columns sit near lane 3's stored-forecast figures (0.72 at Act 3 start, 0.59 at the door on 1,320 runs): the rows are right. The door cell is small (244 runs, about 40 passes), so its AUC carries a standard error near 0.035; the decile table is in `agent/boss-chain/v1/report.md`.

## Flip check (400 held-out generation 18 runs replayed, champion against candidate)

- Act 1: 11,514 choices, **0 changed**. The champion reproduces its recorded pick 100 in 100 (all acts, 20,400 choices).
- Changed: Act 2 25.4 in 100 (1,773 of 6,982), Act 3 30.6 in 100 (582 of 1,904). Most: Act 3 shop 65, ancient 51, card 44; least: route 4 to 7.
- Act 3 rest sites below 70 in 100 HP (114): heal share 97.4 to 88.6 in 100 (**a fall of 0.088, against a veto at 0.10**). Act 3 shops: potion share of purchases 24.3 to 40.3 in 100 (226 and 196 purchases). Elite share on Act 2 and 3 routes 3.7 to 3.5.
- No veto fired. The heal fall is close to the line.

## Candidates (no marker written; the orchestrator writes it)

1. `agent/gen19/candidate-chain`: a copy of `gen18/candidate-fight-v3` plus `boss_chain.npz` (sha 2b427227f1ee..., kappa 0/10/10) and the recipe part `+chain:2b427227@0/10/10`. `screens.differing` reads `["settings"]`. Emulator smoke (20 seeds, 4 processes, 274 s): 20 runs, 0 crashes, 0 lost workers, the summary's agent block names `boss_chain: 2b427227@0/10/10`; floors 14 to 49, mean 27.7 (not a measure).
   - Marker: `D:/spireline/referee/LAB/train/ready-18-g19-chain`, one line of UTC time, e.g. `2026-11-19T21:40:00Z`.
2. `agent/gen19/candidate-cheapv3-fightv3`: the champion with the run brain of `gen18/candidate-cheap-v3` (`run_value.npz/.pt/.onnx` and `fight_net.onnx` byte for byte, run_value sha bfe6fa91...; the fit's `vrun_fit.json` beside them) and nothing else. `screens.differing` reads `["value"]`. agent.json carries the lineage (base `gen18/candidate-fight-v3`, run brain from `gen18/candidate-cheap-v3`, your text as why). Smoke (same seeds, 360 s): 20 runs, 0 crashes, 0 lost; floors 17 to 49, mean 32.4.
   - Marker: `D:/spireline/referee/LAB/train/ready-18-g19-cheapv3-fightv3`.
   - The recipe string stays the champion's: a run-brain swap is a new identity (prior sha, run head sha) under the same recipe, as every `build-vrun` candidate is; the lineage and note name it. `candidate-cheap-v3` has no `vrun_fit.json` of its own; I took it from its fit folder (`run-cheap/17/fits/A-all`), whose run files are byte-equal to the candidate's.
3. Marker conditions (chain): night block ended; lane 1's strict Act 3 reading live in the lab tree (it landed as `ee9b7f1d`); no other `ready-*` marker standing (so one at a time). Ask for the second block pre-registered (4,000 pairs pooled), as the design says: the extension bar of +1.0 is above the design's central +0.6.

## Not done, not verified

- Whether choices among options at one place improve: the door AUC ranks runs against each other (and the boss's identity is part of it), not options within a position. Only the judged blocks decide.
- kappa 10 is the design's value, untuned; Act 1 is off. `q4` is recorded, not used. The second Act 3 boss is left to the fight brain.
- I took no QUIET.lock line (COMMON: do not touch it); the file and the night file were absent at every heavy step, all at BelowNormal. I ran the rows before the gate (the machine was free and the gate needs the engine library unlocked); the gate then ran on the rebased tip. The engine library came first from the lab tree's copy (the fork's main `out/` is one version behind), then from a publish in `wt-chain`.

## Repeat

```
export STS2_LIB_PATH=D:/spireline/fork/wt-chain/out STS2_ALLOW_STALE_NATIVE=1
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py build --stores 15,16,17,18 --run-value agent/gen18/candidate-fight-v3/run_value.npz --out logs/boss-chain/rows --procs 4
D:/spireline/venv-gpu/Scripts/python.exe -I rl/boss_chain.py fit --rows logs/boss-chain/rows --init agent/gen18/candidate-fight-v3/run_value.npz --out agent/boss-chain/v1 --seeds 0,1,2
D:/spireline/venv-gpu/Scripts/python.exe -I rl/boss_chain.py report --rows logs/boss-chain/rows --model agent/boss-chain/v1/boss_chain.npz --out agent/boss-chain/v1 --champion
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py build-chain --base agent/gen18/candidate-fight-v3 --chain-dir agent/boss-chain/v1 --agent-root agent --target 19 --kappa 0/10/10 --tag chain --why TEXT
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py flips --champion agent/gen18/candidate-fight-v3 --candidate agent/gen19/candidate-chain --store run-cheap/18 --runs 400 --out logs/boss-chain/flips.json
D:/spireline/src/sts2/.venv/Scripts/python.exe -I logs/boss-chain/build_cheapv3_fightv3.py
```
(Run from `fork/wt-chain`; paths with no drive are under `D:/spireline/referee/` or `D:/spireline/`.) Gate: `bash logs/gym-loop/chain-gate.sh`. Outputs: `logs/boss-chain/` (rows, fit, flips, both smokes, gate logs).
