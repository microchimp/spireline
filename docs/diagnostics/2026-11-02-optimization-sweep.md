# Optimization sweep, 2026-11-02: where the machine's time goes and what would buy it back

Owner's request: "Run a sweep across the code to see if anything can be optimized." Read-only sweep worker, 11:19Z to
11:50Z. Paths are relative to `D:/spireline/`. Code read on fork main (`fork/wt-lab` at f95d094b, the lab's tree; the
landings since, d5fcd126 to c529339d, are not proposed again). Disk waits and the SSD question are the separate report
[2026-11-02-disk-bound.md](2026-11-02-disk-bound.md); this sweep only notes them where its profiles hit them.

**Load during the probes.** Every probe ran 11:23Z to 11:42Z while the lab's self-play job (20 workers plus the GPU prior
server) and the always-on loop (rebuilding its start set) were running: machine CPU at 100% in every watcher sample, my
one probe process at BelowNormal got the CPU about 55% of the time (CPU 16.2 s in 29.7 s of wall). Read the probe walls as
loaded; the shares and the same-seed ratios are the robust part.

## The answer in five lines

- **Hung runs idle the whole machine during promotions.** 3 of the last 6 promotion arms had one run that never finished;
  each was killed at 2,100 s, run again, killed again, while the 19 other workers had nothing left to do. Those three
  tails cost 6,631 s (1.8 h) in the last three attempts; today 05:20Z-05:59Z the machine sat at 6.9% CPU waiting on one run.
- **The new engine kernel's combat step is three times the old one's.** Same seed, same decisions: 0.54 ms against
  0.18 ms a step; it is 53% of a run's time under core2. Both arms of the night run core2, so the night pays it.
- **The day's real-game check fights the loop.** Today's score-real took 9,460 s for 495 real runs (12 load-guard stops,
  471 ms a decision); the night played the same size of block in 2,041 s (262 ms a decision).
- **The GPU is not the bottleneck anywhere and the "prior server degraded" flag is noise.** Every run of A's block was
  served by the GPU (1,999 and 2,000 of 2,000); the flag fired only because the client's 99th-percentile wait was 20.9 and
  20.1 ms against a 20 ms line. The night's emulator arm, though, never uses the server (CPU path, 500 of 500).
- **The rest is near its floor or small:** shard reading in the train job (13-37 s), the night's ranking (about 66 s),
  the real game's message pipe (blocking reads, no polling), worker start-up on the server path (no measurable cost).

## 0. Where the core-hours and the GPU went (watcher, 2026-11-01 11:20Z to 11-02 11:20Z, 8,473 samples)

Joined to the lab's job intervals (`referee/lab/runner.log`) and the loop's phases (`referee/gym-loop/gpu.jsonl`).
Script: `referee/backlog/sweep/watch24.py`.

| group | hours | CPU % | core-h used | core-h idle | GPU % |
|---|---|---|---|---|---|
| whole day | 23.5 | 56.5 | 212.7 | 163.9 | 21.3 |
| lab: fights | 10.3 | 60.2 | 99.4 | 65.7 | 22.0 |
| lab: presort | 3.6 | 40.3 | 23.4 | 34.7 | 20.0 |
| lab: invariants | 3.0 | 37.0 | 17.8 | 30.4 | 22.6 |
| lab: score-real | 2.6 | 64.9 | 26.7 | 14.4 | 21.3 |
| lab: train (gen 11 build and its block) | 2.0 | 67.7 | 21.6 | 10.3 | 23.4 |
| lab: nightly-real | 0.9 | 64.4 | 9.4 | 5.2 | 0.3 |
| lab: selfplay | 0.5 | 98.8 | 7.6 | 0.1 | 35.4 |
| loop: generate | 11.1 | 58.2 | 103.0 | 74.1 | 23.5 |
| loop: gate | 5.2 | 60.5 | 50.6 | 33.0 | 31.4 |
| loop: waiting / yield / starts | 6.9 | 49 | 53.8 | 56.8 | 9 |

GPU: under 10% in 26% of samples, 30-60% in 33%, 60% or more in 0.1%. Process names in the top-10 lists (a lower bound):
python 46%, the real game 14%, pythonw 10%, Defender 5.5% (about 0.9 of a core all day), dotnet 2.7%.

## 1. The emulator arm (self-play, promotion blocks, the night's copy arm)

### 1a. Where a decision's time goes (probe, one process, gen 11 agent, seed NGEGDAAY8Z: 157 decisions, 115 fights decisions, 4,650 simulations, floor 17)

Script `referee/backlog/sweep/probe_emu2.py`: imports first, then the run timed plain and again under cProfile; CPU prior
path (the probe cannot start the GPU server: that is a second process).

| item | old engine (self-play, promotion blocks) | core2 (the night, both arms) |
|---|---|---|
| run wall / CPU, plain | 29.7 s / 16.2 s | 55.6 s / 24.3 s and 52.7 s / 34.1 s (two runs) |
| per decision, plain | 189 ms wall, 103 ms CPU | 336-354 ms wall, 155-217 ms CPU |
| profiled run | 36.2 s | 59.2 s |
| engine combat step (`native.step`, 57,545 calls) | 10.2 s, 0.177 ms a step, **28%** | 31.1 s, 0.54 ms a step, **53%** |
| other engine calls (legal actions, clone, run step) | 3.1 s, 9% | 3.5 s, 6% |
| prior forward on the CPU incl. encoding (958 calls) | 7.9 s, **22%** (8.2 ms a call profiled) | 6.4 s+ |
| run-level choice (V_run lookahead, 42 picks) | 1.0 s, 3% | 1.4 s, 2% |
| search and rollout logic in Python | about 14 s, 39% profiled (about 25% unprofiled: the profiler added 6.6 s, nearly all to Python) | about 16 s |

Per simulation: 3.2 tree steps and 8.5 rollout steps; a rollout plays to the fight's end with the tempo policy. Inside
the rollouts (old engine) the Python around each step (legal actions, `live_rollout_weights` building a numpy array per
step, `rng.choice` with weights, target choice, ctypes reads of the observation) costs 0.23 ms against the step's 0.18 ms
(profiled).

The import of the worker's modules (894 files, mostly torch) took 39 to 62 s in each of the five probe processes, with
the files warm in memory (41 ms per file open at 100% CPU): see the disk-bound report; it hits CPU-path workers only.

### 1b. The blocks themselves (summary.json files; `referee/backlog/sweep/arms.py`)

| block | procs | runs | wall s | ideal s (run time / procs) | tail s | prior path | ms per decision |
|---|---|---|---|---|---|---|---|
| E11 gen 11 arm (today) | 20 | 2,000 | 5,021 | 2,488 | **2,533** (1 hung run, 2 attempts) | server 1,999 | 124 |
| E11 gen 9 arm (today) | 20 | 2,000 | 2,284 | 2,217 | 67 | server 2,000 | 116 |
| E10-10-30-r1, both arms | 20 | 2,000 | 2,589 / 2,901 | | 66 / 91 | server | 130 / 141 |
| E10-10-29 gen 10 arm | 20 | 2,000 | 4,431 | 3,140 | **1,290** (1 hung run) | server 1,999 | 170 |
| E10-10-29 gen 9 arm | 20 | 2,000 | 6,134 | 3,326 | **2,808** (1 hung run) | server 1,999 | 171 |
| self-play, today 10:50Z | 20 | 776 | 1,237 | 1,186 | 51 | server 776 | 165 |
| night emulator arm, 11-02 | 12 | 500 | 1,255 | 1,180 | 75 | **cpu 500** | 145 |

- The hung runs: seeds 6QURX34B9Q (gen 10 arm), CEF8JGHTX5 (gen 9 arm, E10) and WGQE3H9PW6 (gen 11 arm, E11); each
  timed out at 2,100 s on both attempts (so the hang replays: a retry only doubles it). The run's own 1,800 s cap is
  checked between decisions, so one decision never returned. 3,999 finished runs of E11: slowest 123 s.
- Server-path workers cost nothing measurable to start: their first run is as fast per decision as their later ones
  (0.150 against 0.146 s in self-play, 0.107 against 0.109 in E11). Pool restarts (recycle about every 18 runs) are
  inside the 2-4% tail.
- **The "prior server degraded" flag** (`rl/gen0.py` run_block): set when the pool shrank, fewer than 99% of runs were
  served, or the client's p99 call latency is over `--latency-p99-ms` 20. A's two arms: served 1,999 and 2,000 of 2,000,
  no restart, no shrink; p99 20.9 and 20.1 ms; today's self-play p99 29.8 ms. So no fallback to the CPU path happened; the
  flag fires on any block run at full load. The server side: 1.27-1.33 ms per batch (queue 0.34, graph replay 0.89-0.97),
  mean batch 1.37 positions (74% of batches are one position), 6.8 prior calls per decision, host CPU 20% of one core.
- **The night's emulator arm never uses the server**: `rl/gen0.py` `play_emu_arm` calls `run_block` without a server,
  while `rl/nightly_real.py` (lines 18 and 290) says the arm "plays through the prior server on the GPU". The GPU lane's
  design kept the score's emulator arm on the CPU path on purpose (same transport as the real arm), so the comment is
  the error, and the choice is open (change 4). Measured gain of the server in the GPU lane (docs/rl/GPU_INFERENCE.md 9.1,
  idle machine): +13.8% decisions per second at 16 workers, +21.6% at 20.

## 2. The real-game arm

| item | night 11-02 (g9, 23:25Z-23:58Z) | score-real of gen 11 (today 06:37Z-09:14Z) |
|---|---|---|
| runs, processes | 498, 12 | 495, 12 |
| wall | 2,041 s (+1,255 s emulator arm first, +66 s ranking) | **9,460 s job** (step 3,595 s after its last restart) |
| run time summed / decisions | 22,811 s / 87,074 = **262 ms a decision** | 41,338 s / 87,703 = **471 ms a decision** |
| machine CPU (watcher / the night's own sampler) | 62% (tree 58%), free memory min 6.7 GB | 65%, free memory min 3.1 GB |
| load-guard stops | 0 | 12 (four in 90 s at 07:35Z-07:36Z), 25 min paused |
| game restarts (recycle) | 71 x 4.8 s boot = 341 s, 1.5% of run time | |

Where the night's 262 ms goes (inference): the driver's own search is the same agent on the same kernel as the emulator
arm, 145 ms a decision there (core2, CPU path); the rest, about 117 ms, is the game's own step and the pipe. The pipe is a
blocking line reader with a queue (`referee/envproto.py`, no polling interval on the step path); the game runs with
`--fixed-fps` already. CPU use per decision (driver plus game) is about 218 ms against 262 ms of wall, so the arm is CPU
bound, not waiting. More processes: 6 logical CPUs were idle, but they are SMT siblings; 14 processes might give
+10-15% at about 3.8 GB less free memory (inference, not measured). The day's score-real was slow because the lab's load
guard stops it whenever the loop's six workers push "other processes" over 50% (the loop yields to the night and to
QUIET lines, not to a daytime real-game job: `rl/gym_loop.py` `why_blocked`), and each stop kills the games in flight.

## 3. The train job

| item | gen 9 | gen 10 | gen 10 r1 | gen 10 r2 | gen 11 (build only) |
|---|---|---|---|---|---|
| fights kept / samples | 6,400 / 77k | 6,400 / 79k | 12,800 / 156k | 19,200 / 232k | - |
| shard reading (`build_s`) | 20 s | 13 s | 16 s | 37 s | - |
| combat fit wall / CPU | 2.8 / 2.9 min | 3.4 / 3.4 | 6.2 / 6.2 | 9.9 / 9.8 | - |
| V_run fit wall / CPU | 9.3 / 12.4 min | 9.2 / 11.8 | 10.9 / 14.2 | 24.0 / 30.9 | - |
| two promotion arms | 92 min | 176 min (two hung runs) | 92 min | (no block) | 122 min (one hung run) |

Reading is not the bottleneck: at the new 32,000-fight cap it extrapolates to about 1 minute, the combat fit to about 16
minutes (linear in samples, 16 epochs). The combat fit's CPU time equals its wall: batch 64 on a 2-layer, 128-wide net is
host-bound and the GPU mostly waits (inference: no training ran while the watcher was sampling, so the GPU share during a
fit is not measured). The promotion arms are 84-93% of every train job.

## 4. The always-on loop (last 24 h, `referee/gym-loop/loop.log`, `trainer/trainer.log`)

| item | value |
|---|---|
| generation | 36 segments, 5,085 fights in 15.5 h of segment time: **328 fights an hour, 55 per process** (6 processes, teacher x16) |
| gates | 38 plays, 5.3 h (stage 1: 400 games in 5-8 min; stage 2: 1,600 in about 20 min) plus 1.3 h between verdict and next segment |
| known games replayed | only after the engine move: v2's 400 + 1,600 again (28 min), about 12% of the day's gate games; otherwise cached |
| verdicts | 0 promotions since v2 (10-31 14:30Z); in the last day 19 stage-1 rejects, 3 stage-2 rejects (+0.4, +0.5 points) |
| trainer | 37-41 optimizer steps per checkpoint, a checkpoint every 30-36 min; GPU training time about 0 (it waits for new fights) |
| start-set rebuild after 8462415d | 245 runs a night replayed in 9-16 min each, once; then one night a day |

## 5. The lab's presort checks and the night's tools

Today's presort, 96 min: refset 57 s; `codex-s0..3` 1,456-1,577 s (four dotnet processes, one shard each, in parallel;
restarted from zero once after three load stops, 11 min lost); corpus 746 s (already a process pool); groups 1,797 s and
kits 764 s (both now cached or skipped by d5fcd126 and c529339d). The week since 10-26: codex 27 runs at about 1,450 s,
the engine source changed in 14 of 26 presorts (4 of the last 12), so with step D's skip the codex check still runs a few times
a week. Bench-env 6 runs of about 20 min. The night's ranking and comparison take about 66 s. Nothing here re-parses the
same input inside one run beyond what the file-opens report covered.

## 6. Python-level hot spots found by profile

Old engine, profiled (section 1a): `live_rollout_weights` 36,343 calls, 2.9 s (a fresh numpy array, `ones`, sum and
divide for 2-6 numbers per rollout step); `rng.choice(legal, p=...)` per step (numpy's checks on a tiny array);
`_hand_size` 93,415 calls, 1.2 s (ten ctypes reads per call, twice per step); `native.valid_actions` 57,167 calls, 2.5 s.
No per-decision JSON parsing or file opens in the emulator path; the real arm parses one JSON line per message (small
next to 262 ms). The run-level choice (V_run lookahead) costs 24-34 ms per pick, 3% of a run.

## 7. The C# engine

Only what the Python profile shows: under core2, `Sts2_Step` (`native.step`) is 0.54 ms a call against 0.18 ms on old,
3.0x, on the same seed, decisions and load; the other entry points moved little (legal actions 2.86 against 2.45 s,
clone 0.48 against 0.35 s). At core2's landing (10-25, D31) the bench said steps -24%; the kernel has taken on more
families since. Which part of the kernel's step (its queue, the hook dispatch) is the cost needs a C# profile, left to an
engine brief with its own byte-proof.

## Ranked changes (saving per cost)

| # | change | measured number it rests on | expected saving | cost to build | risk | confidence |
|---|---|---|---|---|---|---|
| 1 | Promotion arms, self-play and the night's emulator arm: a run timeout of 600 s (not 2,100) and no second attempt after a timeout (only after a worker death); a fix-info brief for the three hung seeds | 3 of the last 6 promotion arms hung; tails 1,290 / 2,808 / 2,533 s; machine at 6.9% CPU for 39 min today; slowest finished run 123 s of 3,999 | about 35-40 min per hung attempt; 1.5-2 h a week of lab clock at this week's rate | about 0.2 point (Sonnet: two arguments, one rule, tests) | a legitimate run over 600 s would count as lost (none seen); no game-facing change, no byte-proof | high |
| 2 | Real-game jobs hold the loop off as the night does (score-real takes the nightly marker or a QUIET line), or score-real moves into the promoted generation's first night | score-real today 9,460 s for 495 runs, 471 ms a decision, 12 stops; the night 2,041 s, 262 ms | about 1.7 h (loop held off) to 2.6 h (moved into the night) of lab clock per promotion (2-3 a week: 3.5-8 h); the loop loses about 1 h of generation per promotion | about 0.2-0.3 point; folding into the night is an orchestrator decision | none game-facing; the loop pauses longer | high on the cost, medium on the split between thrash and load |
| 3 | core2's combat step brought to old's cost (engine brief: profile the kernel's step in C#, fix, byte-proof) | 0.54 against 0.18 ms a step, 53% of a core2 run; the night runs core2 on both arms (16.2 h of night clock this week) | about 1 h a night at 2,000 runs (emulator arm about -35 min, real arm's search about -30 min); 4-7 h a week of night clock; also the price of ever moving self-play to core2 | Opus engine brief, about 2-4 points plus a build and the byte-proof | engine change: byte-proof and the 75-min gate; regen of the hash-pinned files | high on the ratio, medium on the saving |
| 4 | The night's emulator arm on the GPU prior server at 20 workers (`play_emu_arm` passes the server options; fix the comment either way) | 500 of 500 runs on the CPU path; server +21.6% decisions per second at 20 workers (GPU lane 9.1) | about 15 min a night at 2,000 runs with core2 as it is (about 1-2 h a week) | about 0.3 point | the copy arm's transport would differ from the real arm's CPU path (tolerance and sample-quality tests passed, 9.2-9.3); pairing per seed may shift: an orchestrator choice | medium |
| 5 | The loop gates a checkpoint only when its held-out loss beats the incumbent's by a margin (or after N new fights) | gates 5.3 h a day of six workers; 0 promotions in about 35 verdicts since v2; trainer gain 0.0055 nats | about 2.5 h a day back to generation, about +800 fights a day (+25%) | about 0.3-0.5 point | a candidate the gate would pass could be screened out; nothing game-facing | medium-low |
| 6 | Rollout glue in `rl/live_search.py` without per-step numpy (a list copy of the observation per step, plain floats for the weights, the same draw as `rng.choice` computed by hand) | Python and the legal-actions call around each rollout step 0.23 ms against the step's 0.18 ms (profiled); about a quarter of a profiled run | 5-8% more decisions per second in self-play and promotion blocks (about 15 min per 8,000-run self-play, inference) | about 0.5-1 point plus a decision-identity proof (same decisions on 50+ seeds) | must stay decision-identical; a float or RNG slip changes the agent | medium-low |
| 7 | The lab's load guard suspends a job's processes instead of killing them, with a hysteresis before resuming | 56 load stops since 10-26; codex shards restarted from zero today (11 min); four stop-resume cycles in 90 s | overlaps 2; 10-20 min per stopped presort | about 0.5 point | suspended real games could time out their pipe; memory stays held | medium |
| 8 | Codex check in 8 shards instead of 4 | four shards of about 1,450 s each at 63% machine CPU | about 12 min per presort that changes the engine (2-5 a week: 0.4-1 h) | about 0.2 point | memory per dotnet process; stamp names change once | medium |
| 9 | Base the "prior server degraded" flag on fallbacks and pool shrink (or a 40 ms line) | p99 20.1-29.8 ms on every loaded block, 0 fallbacks | no machine time; stops a false alarm reaching briefs | under 0.1 point | none | high |
| 10 | Combat fit with a larger batch | CPU = wall in all four fits, batch 64 | about 10 min per attempt at the 32,000 cap | small code, but a recipe change: needs a promotion test | changes the trained prior | low |

Already near the floor (with the number): shard reading in the train job (13-37 s of 12-34 min), the night's ranking and
comparison (about 66 s of 56 min), the real arm's pipe (blocking reads) and game restarts (1.5%), server-path worker
start-up (first run 0.7 s slower at most), the GPU prior server (1.3 ms a batch, 20% of a core; the GPU is under 60% busy
in 99.9% of samples).

## Facts and inferences

Measured (sure): the watcher table; every block's wall, ideal and tail; the three hung seeds and their attempts; the
server's statistics and the degraded rule; the night's arm on the CPU path; the probe's per-call times and the 3.0x core2
step on one seed at full load; the train.json times; the loop's segment and gate hours; the score-real and night per-
decision times and stops.

Inferred: the unprofiled split of a decision (the profiler's 6.6 s went mostly to Python); the real game's own 117 ms a
decision; the savings of changes 3-6 and 10 (from ratios, not runs); the GPU's idleness during a fit (CPU equals wall);
the +10-15% from more real-arm processes.

Not measured, and the probe that would: the hang's location (replay WGQE3H9PW6, index 649, gen 11, old engine, on the
server path as in the block, with `faulthandler.dump_traceback_later` at 150 s; on the CPU path it may not follow the
same line); core2 against old on 20+ seeds (`gen0.py bench-emu --engine core2` and `--engine old`, same seeds, a quiet
window); the GPU share during a combat fit (watch one train job); the loop's own decision split (judge-v0, x16; profile
one fight while the loop is stopped); CPU-path worker start-up (bounded at 27 s a start by the night's arm).
