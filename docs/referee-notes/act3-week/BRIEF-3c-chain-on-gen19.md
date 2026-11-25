# Lane 3c: the boss chain refit on generation 19

Read `COMMON.md` in this folder first, then `BOSS-CHAIN.md` (lane 3b: the chain network, its rows, fit, report, build, smoke, flip check; the Repeat section has every command). Sonnet lane. Worktree `D:/spireline/fork/wt-chain` (lane 3b's, at `c7e10c95`, its `out/` current; the chain code is unchanged on fork main since). Memo `BOSS-CHAIN-V2.md` here, one page.

## Why

Generation 19 (`D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3`, promoted 2026-11-19 11:02Z) is the incumbent. It carries another run brain than generation 18, and `rl/gen0.py build-chain` refuses the v1 chain on it: "v1/boss_chain.npz was fitted with another FightNet than the base's run brain". The chain must be refit on generation 19's run brain so that `agent/gen20/candidate-chain` (target 20, kappa 0/10/10, tag chain) can be judged against generation 19. `agent/gen19/candidate-chain` (built on generation 18) is left alone (removals are the owner's).

## Tasks

1. Decide whether the rows (`wt-chain/logs/boss-chain/rows`, built with `--run-value` generation 18's `run_value.npz`) depend on the run brain they were built with. If they do, rebuild them with generation 19's run brain (`build --stores 15,16,17,18 --run-value D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3/run_value.npz --out logs/boss-chain/rows-g19 --procs 4`, BelowNormal, about 45 minutes); if not, reuse them and say why.
2. Fit `D:/spireline/referee/agent/boss-chain/v2` with `--init D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3/run_value.npz`, seeds 0,1,2 (GPU python `-I`).
3. Report on the held-out generation 18 runs as lane 3b did (door AUC at least 0.70, calibration slope, the pass band), with `--champion` pointing at generation 19.
4. `build-chain --base D:/spireline/referee/agent/gen19/candidate-cheapv3-fightv3 --chain-dir D:/spireline/referee/agent/boss-chain/v2 --agent-root D:/spireline/referee/agent --target 20 --kappa 0/10/10 --tag chain --why "Act 3 week (D68 item 3): the run brain's option values see the chance of getting past the Act 2 and first Act 3 bosses; refit on generation 19 (promoted 2026-11-19 11:02Z)"` with absolute paths (relative ones resolve against the tree and load an empty agent). Then the 20-seed emulator smoke (4 processes) and the flip check on 400 held-out runs (`flips --champion <gen19> --candidate agent/gen20/candidate-chain --store run-cheap/19 or 18`), with lane 3b's veto (the Act 3 low-HP heal share must not fall under 0.10 of its value... read lane 3b's memo for the exact veto and apply the same).
5. No marker, no `jobs.json`, no `QUIET.lock` line of yours. The Act 3 replay holds 12 processes from about 00:45Z under its own QUIET line `act3-replay`: your 4 processes beside it are allowed by this brief; do not stop for that line (COMMON's rule on foreign lines is waived for `act3-replay` and `act3-exam` here). No code change is expected; if one is needed, land it per COMMON.md (no night tonight).

Report in five lines: the report's door AUC and slope (n), the smoke (runs, crashes, lost workers), the flip check (Act 1 changed, Act 2 and 3 shares, the veto), the candidate folder and its recipe string, your context size.
