# The boss chain refit on generation 19 (lane 3c)

Written 2026-11-20T01:55Z by lane 3c (Sonnet 5.5). Follows `BOSS-CHAIN.md` (lane 3b), which has the words (run brain, boss chain, door, AUC, kappa) and the method. Paths are under `D:/spireline/`.

## What was done and why

Generation 19 (`agent/gen19/candidate-cheapv3-fightv3`, promoted 2026-11-19 11:02Z) carries another run brain than generation 18, so `build-chain` refuses the v1 chain on it. The chain had to be fitted again on generation 19's run brain. No code changed (the worktree `fork/wt-chain` is clean at `c7e10c95`).

**Do the rows depend on the run brain? Yes, so they were rebuilt.** Each row is the chosen option's input vector, and that vector carries the fight network's forecast block (H, plus H3 for the Act 3 pools), which comes from the run brain's own fight network; the row also records the run brain's own floor forecast. The two run brains hold different fight networks (arrays sha 486a7d39... against f31e9aaa...), so v1's rows would feed the new chain the wrong inputs.

## Steps and figures

1. **Rows** (`logs/boss-chain/rows-g19`, 4 processes, BelowNormal, 3,565 s beside the replay): 1,919 shards of stores 15 to 18, 0 lost; 62,756 runs, 1,275,216 rows (fit 1,121,873, epoch choice 125,197, report 28,146). Generation 18 now holds 6,625 Act 2 runs (2,143 past the Act 2 boss) and 2,143 Act 3 runs (222 past the first Act 3 boss); the other generations are as in v1. Past the first Act 3 boss 1,695 runs, 67 wins.
2. **Fit** (`agent/boss-chain/v2`, graphics card, seeds 0, 1, 2, 4 epochs, rate 1e-4): kept seed 0, best at step 2,192 (end of the first epoch, not the first evaluation); validation loss q2 0.4243, q3 0.2551 (total 0.6794; seeds 1 and 2: 0.6808 and 0.6797). The run brain's own fit used generations 15 to 17 only, so generation 18 is held out from both. Model sha 6ee1879c24f0...
3. **Report** on the held-out generation 18 runs (a hash-fifth, never fitted on): verdict **pass, band go**.

| Cell | Runs | Forecast | Mean | Actual | AUC | Slope |
|---|---|---|---|---|---|---|
| q3 at the door | 260 | chain | 0.161 | 0.169 | **0.851** | **0.868** |
| q3 at the door | 260 | generation 19's run brain | 0.150 | 0.169 | 0.787 | 1.302 |
| q3 at Act 3 start | 410 | chain / run brain | 0.088 / 0.058 | 0.107 | 0.788 / 0.720 | 0.81 / 1.06 |
| q2 at Act 2 start | 1,321 | chain / run brain | 0.294 / 0.207 | 0.312 | 0.762 / 0.745 | 1.06 / 1.02 |
| q2 x q3 at Act 2 start | 1,321 | chain / run brain | 0.028 / 0.016 | 0.033 | 0.709 / 0.680 | 0.65 / 0.59 |

   The door cell is small (260 runs, 44 passes): its AUC carries a standard error near 0.04. Generation 19's run brain tells the door apart better than generation 18's did (0.787 against 0.642 in v1's report), so the chain's edge over it is narrower (+0.06) than v1's (+0.21); the chain still ranks the door well and is better calibrated.
4. **Candidate** `agent/gen20/candidate-chain` (target 20, built on gen19/candidate-cheapv3-fightv3, kappa 0/10/10, tag chain). Recipe string: `vrun+pi_s:lambda=0.5:pi_h=2ebfe6d7:pi_s=e28aa3b8:card=0.5/0.5/0.5:rest=0/0.2385/0.2385:route=0.3715/2/2:shop=0.3038/0/0:event=0.8603/0.9014/0.9014:reward=0/0.6675/0.6675+stakes:a3-v1@h1e4b16+chain:6ee1879c@0/10/10`. The chain is verified to carry generation 19's fight network (the build's own identity check). The build suggested the marker name `ready-19-g20-chain`; **no marker written**.
5. **Smoke** (20 seeds of lane 3b's file, 4 processes plus the prior server, config a3-v1, 383 s): 20 runs, 0 crashes, 0 lost workers (pool: started 4, died 0, timed out 0), prior server not degraded, summary names `boss_chain: 6ee1879c@0/10/10`; floors 17 to 49, mean 31.45 (not a measure).
6. **Flip check**: 400 of generation 19's own plain runs (store `run-cheap/19`, the same hash-fifth rule, the first 400; the chain never saw them, and the champion played them, so its replay agreement is exactly 1.000 over 20,818 choices). Act 1: 11,651 choices, **0 changed**. Act 2: 22.4 in 100 changed (1,550 of 6,927). Act 3: 31.7 in 100 (710 of 2,240); both under the 50 in 100 veto. Act 3 rest sites below 70 in 100 HP (111): heal share 90.1 to 84.7 in 100, **a fall of 0.054 against the veto at 0.10** (lane 3b: 0.088; the fall must not exceed 0.10). Act 3 shop potions: 36.1 to 25.9 in 100 of purchases (219 and 201 purchases; v1 went the other way, 24.3 to 40.3). Elite share on Act 2 and 3 routes 4.2 to 4.0 in 100 (1,995 screens). **No veto fired.**

## Not done, not verified

- No judged block: the candidate is not tested for kills, only for ranking the door and for what it changes. The door cell's AUC edge over the new run brain is smaller than v1's. Whether choices among options at one place improve is not measured (as in lane 3b's memo). kappa 10 is the design's value, untuned; Act 1 off; `q4` recorded, not used.
- The replay used the first 400 report-set runs in store order (about the first 400 of the plain runs since the 2026-11-19 11:02Z promotion); a later store would shift the figures by sampling only.
- The marker (`LAB/train/ready-19-g20-chain`, one line of UTC time) is the orchestrator's; lane 3b's marker conditions apply (no other `ready-*` standing; the strict Act 3 reading live in the lab tree; the second block pre-registered).
- `agent/gen19/candidate-chain` (v1 on generation 18) is left alone; removal is the owner's.

## Repeat

```
export STS2_LIB_PATH=D:/spireline/fork/wt-chain/out STS2_ALLOW_STALE_NATIVE=1   (run from D:/spireline/fork/wt-chain)
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py build --stores 15,16,17,18 --run-value D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3/run_value.npz --out D:/spireline/logs/boss-chain/rows-g19 --procs 4
D:/spireline/venv-gpu/Scripts/python.exe -I rl/boss_chain.py fit --rows D:/spireline/logs/boss-chain/rows-g19 --init D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3/run_value.npz --out D:/spireline/referee/agent/boss-chain/v2 --seeds 0,1,2
D:/spireline/venv-gpu/Scripts/python.exe -I rl/boss_chain.py report --rows D:/spireline/logs/boss-chain/rows-g19 --model D:/spireline/referee/agent/boss-chain/v2/boss_chain.npz --out D:/spireline/referee/agent/boss-chain/v2 --champion
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py build-chain --base D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3 --chain-dir D:/spireline/referee/agent/boss-chain/v2 --agent-root D:/spireline/referee/agent --target 20 --kappa 0/10/10 --tag chain --why TEXT
bash D:/spireline/logs/boss-chain/smoke-g20.sh   (gen0.py emu, seeds file logs/boss-chain/smoke-seeds.json, --config a3-v1 --procs 4 --prior-server auto)
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/boss_chain.py flips --champion D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3 --candidate D:/spireline/referee/agent/gen20/candidate-chain --store D:/spireline/referee/run-cheap/19 --runs 400 --out D:/spireline/logs/boss-chain/flips-g20.json
```
Outputs: `D:/spireline/logs/boss-chain/` (`rows-g19`, `build-g19.log`, `fit-g19.log`, `report-g19.log`, `smoke-g20`, `smoke-g20.log`, `flips-g20.json`); the report is `agent/boss-chain/v2/report.md`.
