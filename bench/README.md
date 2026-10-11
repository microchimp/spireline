# Day-4 benchmarks: r33hab/sts2 @ b745217 on the Windows PC (WSL2 Ubuntu)

**Status: UNTESTED.** Written 2026-10-10 on the Mac by reading the emulator source at
`b745217`. None of the emulator's code was built, imported or run. The plumbing (process
pool retry, barrier, JSON, table, driver) was run once against a throwaway stub of
`combat_mcts` in the scratchpad. That proves the control flow, not the emulator calls.

| file | what it is |
|---|---|
| `run_all.sh` | Runs every step below in order and writes raw output to `results/<host>-<date>/` |
| `sts2bench.py` | **UNTESTED wrapper** for what the emulator's scripts do not expose: combat-handle sims/s, a clean scaling curve, the c-sweep with visit entropy, and the CRN variance check. It uses only `combat_mcts`/`sts2_gym` calls, made exactly as the emulator's own scripts make them; each call cites the line it copies |
| `collect.py` | Standard library only. Turns a results directory into `summary.json` and prints one comparison table |

## 0. Before starting (PC, inside WSL2 Ubuntu)

1. The emulator is cloned on the Linux filesystem, not `/mnt/c` (for example `~/git/sts2`), at `b745217`, and built following HANDOFF.md:47-66 with `bash scripts/build.sh linux-x64` (build.sh:10-29: `linux-x64` is picked from `uname` at :17, published to `out/` at :24-28). This must produce `out/Sts2Emulator.so` (native.py:11-15, searched at native.py:167-180).
2. The emulator's venv exists: `uv sync` in the checkout creates `.venv`. The steps need only numpy and gymnasium (pyproject.toml:5-11). `uv sync` also downloads torch 2.12.0, which none of these steps uses.
3. This `bench/` folder is copied into WSL, for example `~/code/spireline/bench`.
4. Quiet machine: the game is closed, nothing heavy is running, and Windows is set to plugged in, sleep Never, best performance.
5. Optional: `sudo apt install time` (GNU time), so each log records peak RSS.

Checks (all read-only):

```bash
cd ~/git/sts2 && git rev-parse --short HEAD          # expect b745217
ls -l out/Sts2Emulator.so
.venv/bin/python -c "import numpy, gymnasium; print('ok')"
nproc; lscpu | grep -E 'Model name|Thread|Core|Socket'; free -g
ps -p 1 -o comm=                                      # 'systemd' if systemd-inhibit can work
```

## 1. Run

```bash
cd ~/code/spireline/bench
EMU=~/git/sts2 bash run_all.sh                        # foreground, about 15-30 min
```

**Unattended (the Linux version of `caffeinate`):**

```bash
EMU=~/git/sts2 nohup systemd-inhibit --what=idle:sleep --who=spireline --why="day-4 bench" \
    bash run_all.sh > run_all.$(date +%F-%H%M).out 2>&1 &
tail -f run_all.*.out
```

- If PID 1 is not systemd, or `systemd-inhibit` is refused (polkit may deny it outside a local seat), run `EMU=~/git/sts2 nohup setsid bash run_all.sh > run_all.out 2>&1 &`. Running `tmux` inside an open WSL terminal also works.
- **In WSL, `systemd-inhibit` only stops sleep inside the Linux VM.** Windows decides whether the machine sleeps. On this PC the real `caffeinate` is Windows set to never sleep (Settings → System → Power → Sleep: Never) or PowerToys Awake. You change that setting yourself; the scripts never touch Windows.
- WSL can shut its VM down once no terminal is attached. Confirm a detached job survives by closing the terminal and running `wsl -l --running` in PowerShell. If it does not survive, keep one WSL terminal (or the Claude Code session) open.

Partial runs: `STEPS="03 06" EMU=... bash run_all.sh` runs only steps whose names start with those prefixes. `RESUME=1 OUT=<dir>` writes into an existing directory. Otherwise a second run the same day gets a `-HHMMSS` suffix. Each step is killed after `STEP_TIMEOUT` (default 5400 s), which gives exit code 124 in `steps.tsv`.

## 2. The steps, in order

All emulator scripts run from `$EMU` with `$EMU/.venv/bin/python -u` (as `uv run python rl/...`, HANDOFF.md:65), with `OMP/OPENBLAS/MKL_NUM_THREADS=1`. Runtimes are **estimates**: r33hab's M4 Max figures (rl/run_train/DESIGN.md:356-378) × 1.5-2 for an assumed per-core slowdown. The first real run replaces them.

| # | step | command (abridged) | est. runtime | number it produces | compared with |
|---|---|---|---|---|---|
| 00 | `00_env` | uname, nproc, lscpu, free, emulator HEAD, lib sha256, venv versions, Windows CPU via `powershell.exe` | < 30 s | machine record | – |
| 01 | `01_verify_combat` | `rl/combat_mcts.py --verify` | < 10 s | combat clone independent / faithful / resampled; draw pile reordered, same cards (combat_mcts.py:929-1011) | must say `ok`, no `FAIL` |
| 01 | `01_verify_run` | `rl/mcts_probe.py --section invariants` | < 10 s | run clone independent / faithful / resampled (mcts_probe.py:81-140) | must say `ok` |
| 02 | `02_agent_probe` | `rl/agent_probe.py` (defaults `--runs 20 --steps 2000`) | 0.5-1.5 min | **single-core gym step µs and steps/s** (agent_probe.py:201); clone+destroy/s with resampling at a run start (:223) | design 58-72 µs (design:15) |
| 03 | `03_micro` | `rl/run_train/probe_throughput.py --micro-only --json 03_micro.json` | 0.5-1.5 min | **clone cost with `resample_hidden`**: run handle at fight 1 and fight 6, run and combat handle at turn 0, faithful run clone; turn-0 rollout µs/sim and **native µs/step** on both handles (probe_throughput.py:712-840) | M4 Max 8.8 / 1.4 µs, 648 / 448 µs, 25.6 / 17.9 µs (DESIGN.md:356-359) |
| 04 | `04_mcts_search` | `rl/mcts_probe.py --section search --sims 300` | < 30 s | run-level random search, c=1.4: sims/s, µs/sim (mcts_probe.py:216-252). Information only | – |
| 04 | `04_mcts_pressure` | `rl/mcts_probe.py --section pressure` | < 30 s | clones held before the 256-handle pool refuses (mcts_probe.py:255-280) | about 255 |
| 05 | `05_runs` | `probe_throughput.py --sims 60,300 --runs 10 --no-micro --workers 8 --json 05_runs.json` | 5-7 min | whole Act-1 runs, one process: s/run, and **in-run ms/sim on run handles at 60 and 300** (Σ decisions×sims / Σ search s) | M4 Max 2.89 s/run at 60 (DESIGN.md:373), about 15.6 at 300 (interpolated from :376, :378); 0.40-0.41 ms/sim (:361-363) |
| 06 | `06_search` | `sts2bench.py search --sims 60,300 --fights 16` | 1-2 min | **combat-search sims/s per core at 60 and 300**: c=0.1, tempo rollout, CRN 0.2, `best_action`, on combat handles; ms/sim, ms/decision, s/fight | design 0.4-0.7 ms/sim (design:15); target ≥ 1,000 sims/s/core, replan below 600 (design:972) |
| 07 | `07_scale` | `sts2bench.py scale --workers-list 1,2,4,6,8,PHYS,N --sims 60 --fights 8` | 1.5-3 min | **multi-worker scaling**: each W runs the same 8 fights per worker, all starting from one barrier; aggregate sims/s and per-worker speed relative to W=1 | design 5,000-8,000 sims/s at 6 workers (design:81, :465); M4 Max 0.93 per worker at 8 (DESIGN.md:586) |
| 08 | `08_parallel_8`, `08_parallel_N` | `probe_throughput.py --sims 60 --runs 8 --no-micro --parallel {8,N}` | 1-2 min each | the emulator's own multi-process check: runs/h at W workers | DESIGN.md:439 linear 9,980 runs/h at 60 sims, 8 workers |
| 09 | `09_csweep_historical` | `sts2bench.py csweep --c-values 0.1,1.4 --fights 240 --sims 60 --rollout uniform --crn-fraction 0 --select visits` | 1-4 min | **c=0.1 vs c=1.4, 240 fights each on the same seeds**: P(death) with Wilson CI, mean end HP, visit entropy / uniform, exact McNemar on the pairs | FINDINGS.md:116-119 (0.092 / 0.183) |
| 09 | `09_csweep_current` | same, with `--rollout tempo --crn-fraction 0.2 --select value` | 1-4 min | the same figures under today's defaults (play_net.py:179-195) | same |
| 10 | `10_crn_tempo`, `10_crn_uniform` | `sts2bench.py crn --encounter 29 --seed 406 --pairs 1500` | < 30 s each | variance reduction of a Bash-vs-Strike root comparison: shared vs independent determinizations | FINDINGS.md:301-304 (4.6×) |
| 11 | collect | `python3 collect.py results/<host>-<date>` | < 1 s | `summary.json` plus the table | – |

All are single-core except 07, 08 and 09. The single-core steps come first, while the machine is cool and quiet. The c-sweep pool size has no effect on its results: each fight seeds its own RNG from `(encounter, seed)` (play_net.py:168).

## 3. Worker counts

- `N` is `nproc` inside WSL, which is the number of vCPUs WSL was given. By default that is every logical processor; `%UserProfile%\.wslconfig` `[wsl2] processors=` and `memory=` change it, and the change needs a `wsl --shutdown`. That is a Windows configuration change for you to make. WSL2's default memory cap is a share of host RAM; `07_scale` records each worker's peak RSS so the cap can be checked.
- `PHYS` is the number of physical cores, from `lscpu -p=CORE,SOCKET`. With SMT, compare W=PHYS with W=N.
- Overrides: `N=12`, `PHYS=6`, `WORKERS_LIST="1,2,4,6,8,12"`, `POOL=10` (c-sweep processes, default N−2), `RUNS`, `SEARCH_FIGHTS`, `SCALE_FIGHTS`, `CSWEEP_FIGHTS`, `CRN_PAIRS`, and `C_VALUES="0.0,0.1,0.6,1.4"` for the full FINDINGS table.
- For production, as opposed to these benchmarks: the design runs workers at `nice 10`, and at most 3 while the game is running (design:479-480). `probe_throughput --parallel` workers already set `os.nice(10)` (probe_throughput.py:970). `sts2bench scale` does not, unless given `--nice 10`.

## 4. Collect

```bash
python3 collect.py results/<host>-<date>      # → results/<host>-<date>/summary.json
```

The table has four comparison columns:
- **measured**
- **design est.**: the Spireline design's M1 Pro estimates, which were never measured.
- **M4 Max**: r33hab's measured figures (rl/run_train/DESIGN.md).
- **note**: includes FINDINGS.md figures, which come from evangambit's unnamed machine.

The checks printed under the table are:
- failed or timed-out steps, crashed c-sweep jobs, and failed scale workers (design:1074 asks for 0 unretried crashes);
- whether both invariant checks passed;
- sims/s/core at 60 against the 1,000 target and the 600 replan floor;
- machine-wide sims/s at 6 workers against 5,000-8,000;
- whether each c-sweep arm reproduced.

"Reproduced" means all of the following hold:
- each published P(death) is inside the Wilson 95% CI of its own arm;
- c=0.1 has fewer deaths than c=1.4;
- the exact two-sided McNemar test on the 240 pairs gives p < 0.05.

The design's day-4 output name was `bench/m1pro-2026-10.json`. Since this now runs on the PC, copy `summary.json` back as `bench/<host>-2026-10.json`.

## 5. Finding: which script produced the c-sweep and the CRN measurement

**Neither script is in the repo, and git history cannot recover them.**

- The c-sweep table is at FINDINGS.md:114-119 and is repeated in combat_mcts.py:23-34 and in the `--c` help text at train_combat.py:514-525 and combat_mcts.py:1039-1050. Nothing at `b745217` prints "visit entropy / uniform". In a full-history clone (730 commits), `git log -S "visit entropy"` finds only `f31c430` (2026-09-09, evangambit). That commit added the whole `rl/` directory at once: 16 files, 5,525 lines, the sweep already written up. The driver was never committed. `git log -S "independent seeds"` (the CRN measurement) also returns only `f31c430`.
- None of the scripts that take `--c` produce the published table:
  - `combat_mcts.py:1039`: one encounter per run, no entropy, and the "native steps" it prints are moves (see section 6).
  - `play_net.py:233`: imports torch (:47), no entropy.
  - `waste_probe.py:182`: no entropy, 20 workers by default (:183).
  - `target_info.py:113`: computes visit entropy (:64-67, :99) but for fixed budget and CRN configurations, not a c-sweep.
  - `train_combat.py:514`: imports torch (:36) and overwrites `rl/data/combat_dataset.npz`.
- The sweep's settings can be inferred but are not certain:
  - It had relics. The label death rate went 0.243 → 0.188 when relics were added and → 0.092 when c was fixed (FINDINGS.md:176-177).
  - It used a uniform rollout. The c=0.1 row's 41.0 HP is close to the uniform-rollout row's 41.6 (FINDINGS.md:141) and plain MCTS at 60 sims, 42.0 (:394).
  - It ran without CRN and selected by argmax visits. The CRN results are reported "against the pre-CRN numbers" (:333), and the switch from visits to mean-value selection came with CRN (:323-326).
  - The budget was 40 (the label sets used 40, :436) or 60 (play_net's default, play_net.py:232).
  - The fight layout was probably play_net's held-out set: seeds 400+, encounter `pool[i % 16]` (play_net.py:248-253). The CRN case "fogmog seed 406" (FINDINGS.md:282) is exactly fight i=6 of that set: `pool[6]` = `OVERGROWTH_NORMAL[2]` = 29 = fogmog (combat_mcts.py:71-72, env.py:43).
- So step 09 runs two arms on that layout, with extra cards 2-8, relics 0-5 and A8:
  - **historical**: uniform rollout, no CRN, select by visits, 60 sims;
  - **current**: today's defaults.
- At A8 the fight start is unchanged since `f31c430`. The A8 deck, HP 64/80 and the samplers are the same: compare `git show f31c430:rl/combat_mcts.py` lines 91 and 240-255 with combat_mcts.py:93 and 243-262, and `Generated/` has no commits since. The **combat engine has changed**, so absolute HP can drift even with the right settings.
- Statistical power: with 240 fights per arm, the SE of the P(death) difference is about 0.03. The published gap of 0.091 is therefore about 3σ, and one arm landing just outside its CI does not settle anything. The design rule is "P(death) ≈ 0.09 vs 0.18 within CI; if it doesn't reproduce, stop and debug" (design:1073-1074).

## 6. Other findings from reading that change how to read the numbers

1. **`combat_mcts.py` mislabels its throughput.** Its `steps/s` is decisions per second. `total_steps` counts only the moves played (combat_mcts.py:870-886) but is printed as "native steps" (:1174). It is not used here.
2. **agent_probe's µs/step includes Python overhead.** It is a gym `Sts2RunEnv.step` timing (agent_probe.py:176-201), including `_obs()` and `_info()` (run_env.py:144-171). The native per-step cost is the probe_throughput micro A/B (probe_throughput.py:822-839). The design's "58-72 µs per step" (design:15) is FINDINGS.md:614 plus mcts_probe.py:249, which are gym-level, unspecified figures.
3. **The design's clone cost conflicts with r33hab's measurement.** The design says "~17 µs (evangambit) to ~70 µs (r33hab) per clone" (design:411). r33hab measured 8.8 µs per run clone and 1.4 µs per combat clone on the M4 Max (DESIGN.md:356). Step 03 settles it.
4. **The design mixes two machines.** FINDINGS.md figures are not from the M4 Max: its reproduce block builds `win-x64` (FINDINGS.md:720) and its label generation ran on 24 workers (:615). The design's "435-714 µs/sim" (design:465) and "0.4-0.7 ms per sim" (design:15) mix the two.
5. **The 85 ms per 300-sim decision is derived, not measured.** It is r33hab's estimate from 0.4 ms ÷ 1.45 (DESIGN.md:1881-1884).
6. **The design's "20-run A0 Defect smoke test" (design:1071; now A10, docs/DECISIONS.md D11) cannot be run through `sts2_gym` at `b745217`.** `Sts2RunEnv` takes only seed, max_episode_steps, max_floors and ascension (run_env.py:56-62). `native.run_reset` has no character parameter (native.py:1303-1330). It is not in `run_all.sh`.
7. **Every run figure here is Ironclad at A8.** `probe_throughput` hard-codes A8 (probe_throughput.py:110-112). Spireline's target is Defect at A10, Acts 1-3 (docs/DECISIONS.md D11, D12; the design's Track D said A0, design:34). These are throughput benchmarks, kept at A8 so they compare with the published figures; they are not play results.
8. **`--parallel` runs/h are not comparable across worker counts.** `probe_throughput --parallel W` draws W×max(1, runs//2) fresh `PRBPAR` seeds (probe_throughput.py:1155-1158), so each W plays a different seed set. That is why the scaling curve comes from `sts2bench scale`, where every worker does identical work. The "rough per-worker" figure that collect.py derives from step 08 compares different seeds, and the table says so.
9. **A known seed aborts the process.** `PRB00011` aborts at 120/500 (DESIGN.md:331-333). Step 05 uses `PRB00000`-`PRB00009`. A native abort elsewhere shows as a non-zero exit in `steps.tsv`, or as a named crashed job in the c-sweep JSON (after two pool retries, the remaining jobs run one per process).

## 7. Assumptions to check tomorrow

**Build and environment**
1. `bash scripts/build.sh linux-x64` emits `out/Sts2Emulator.so`. That exact name is what native.py:13 expects; NativeAOT on Linux should produce `<assembly>.so`. Check with `ls out/`.
2. The library reports API versions 32 and 22 (native.py:17-18); the import fails otherwise.
3. The library's mtime is newer than every `.cs` file under `src/Sts2Emulator` (native.py:55-71). A checkout or touch after building trips this check; rebuild rather than setting `STS2_ALLOW_STALE_NATIVE=1`.
4. `$EMU/.venv/bin/python` imports numpy 2.4.6 and gymnasium 1.2.3 (pyproject.toml:5-11). run_all calls python directly, not `uv run`, so nothing re-syncs mid-run.
5. The checkout is on ext4, not `/mnt/*` (run_all warns), and the emulator HEAD is `b745217` (run_all warns otherwise).
6. GNU `timeout`, `nproc`, `lscpu`, `sha256sum` and `awk` exist (stock Ubuntu). `/usr/bin/time -v` is optional.
7. `python3` exists for collect.py. It needs 3.8 or later for `math.comb`; Ubuntu 22.04 has 3.10.

**Machine and WSL**

8. `nproc` is the vCPU count WSL was given, and `lscpu -p=CORE,SOCKET` gives the physical core count. Check against Task Manager.
9. WSL's memory cap covers N workers. Check `max_rss_mb` in `07_scale` against `free -g`.
10. Windows does not sleep, and the WSL VM keeps a `nohup` job alive after its terminal closes (section 1).
11. Systemd is PID 1 and `systemd-inhibit` is allowed. If not, use the `setsid` fallback; it changes nothing on the Windows side.
12. The game, browsers and GPU jobs are idle. `00_env` greps `tasklist.exe` for the game, and `steps.tsv` records the 1-minute load around each step; collect lists steps that started with load above 1.
13. `time.monotonic()` (CLOCK_MONOTONIC) is comparable across processes. It is on Linux, and `scale` spans rely on it.

**The wrapper's reading of the API (never executed)**

14. These calls are used exactly as defined:
    - `Combat.opening` (combat_mcts.py:225-282), `.fork` (:284-297), `.legal/.step/.hp/.max_hp/.won/.close` (:299-317);
    - `run_search` (:791-819), `best_action` (:822-846), `rollout` (:472-500);
    - `sample_extra_cards` / `sample_relics` (:158-208);
    - `STEP_CAP` (:88) and the Overgrowth pools (:71-72).
15. A hand card's action index is its slot (waste_probe.py:61-69, :152-153). `names.cards()[id].name` gives `"Bash"` and `"StrikeIronclad"` (names.py:174-200; Cards.g.cs:40, :507). If fogmog seed 406's opening hand lacks either card, `crn` falls back to the first two distinct playable cards and flags `fallback_actions`.
16. The fight layout matches play_net's held-out set (play_net.py:163-169, :248-253).
17. "Visit entropy / uniform" means the mean over decisions with at least 2 legal moves of H(root visits) ÷ ln(n legal), counting unvisited legal moves as 0. FINDINGS never defines it; collect also reports the ratio of the means.
18. Search seeds `move*sims + k` (combat_mcts.py:767-773) stay below 2^31 at 300 sims. The crn wrapper uses seeds from 1,000,000 and 5,000,000.

**Interpretation**

19. The historical arm's settings are inferred (section 5). If neither arm reproduces, sweep `--sims 40`, then `C_VALUES=0.0,0.1,0.6,1.4`, before suspecting the engine.
20. The CRN position (deck, relics, which move) is inferred from the seed-406/fogmog match. FINDINGS' 4.6× came from a different estimator size (its SE 0.0071 → 0.0033), so compare orders of magnitude, not digits.
21. The M4 Max → PC per-core factor of 1.5-2 used for the runtimes is a guess; the PC's CPU is unknown.
22. The design's M1 Pro estimates are compared against a PC, not an M1 Pro. They test the extrapolation method, not the Mac. The Mac itself remains unmeasured.
