# What on this machine waits for the hard disk, and what the solid-state drive would buy (2026-11-02)

Question (owner): what else on this machine is bound by the hard disk (`D:`), and what would moving each thing to the solid-state drive (`C:`)
buy? Paths are relative to `D:/spireline/`. Read-only investigation; scratch and scripts are in `referee/backlog/disk-bound/` (not committed).
It follows [2026-11-02-file-opens.md](2026-11-02-file-opens.md), which measured one step (the grouping step) and found about 35 ms for the
first touch of a small file on `D:` against 0.09 ms for the second.

## The answer in six lines

- **One group of steps is disk-bound, and it is the presort's reading tail.** Over the last 7 days the lab ran 159.6 hours of step wall (the four codex shards run side by side, so about 130 hours of clock);
  against each step's own warm run, **about 19 hours of it (12%) was waiting for the disk**: the grouping step 14.7 h (54% of its wall), the
  fix-kit step 2.4 h (16%), the corpus check 1.1 h, the reference-set check 0.7 h. Nothing else in the lab is: self-play, training, the scenario
  batches, the codex walk (four shards) and the night's real-game arm are CPU- or game-bound (section 1).
- **The grouping step's share is about to fall by itself.** The cache that landed this morning (fork `c529339d`) stops it opening 90,000 old
  files; its first run is in the presort that started 11:52Z. After it, the disk-bound part of the lab clock is about 5 h a week (3%), of which
  the SSD would return about 3 h.
- **Process start-up is not a disk problem now.** A worker's imports cost 0.64 s of CPU warm (emulator worker set), 2.5 s for torch; the
  whole week's starts are about 4 hours of process time, spread over 16 cores. Only a start after the file cache has been flushed pays the
  disk, once per job: at most 2 hours a week of single-process wall, probably under 1 (section 2).
- **The game itself loads from copies on `D:`** (`referee/game-env`, `referee/game-lab`, 2.9 GB each, the `.pck` file 1.9 GB). A boot is 4.8 to
  5.6 s on three of the last six nights, 16 s, 17 s and 89 s on the others; on two nights 15 to 20% of the block's wall was disk-stalled.
- **Everything that matters fits on the SSD:** 83 GB of candidates (112 GB at the lab's 100 GB cap) against 303 GB free on `C:`. `D:` holds 149 GB
  in all; 61% of the 200 GB the machine read in the last 26 hours was read by the grouping step.
- **Ranked move list (section 6):** (1) `referee/lab/runs`, 70.5 GB, (2) the corpus and reference-set trees, 3.7 GB, (3) `venv-gpu`, 3.3 GB
  (and the emulator checkout's `.venv`, 0.75 GB, the owner's step), (4) the game copies, 2.9 GB, (5) the codex data and the decompile, 2.2 GB.
  Not the loop's folder, the fork's `out/` folders, the repo, or anything under `src/`.

## Facts and limits (read first)

- **The machine watcher records no disk queue and no latency.** `referee/machine-watch/samples-2026-11-01.jsonl` (9,276 samples, every 10 s,
  2026-11-01 09:10Z to 11-02 11:27Z, no gap over 21 s) holds total CPU, free memory, disk read and write MB/s (both drives; `C:` is under
  0.2 MB/s of it), GPU, the python process count, the game process count and the top 10 processes' CPU. So "queue and latency during each job"
  is not recoverable from it. Three other sources carry them and are used below: the real-game arm's own sampler
  (`referee/lab/nightly/*/g*/machine.jsonl`: queue, latency, bytes, CPU every 30 s, six nights); a live probe I ran of the disk counters of `D:` and
  `C:` every 5 s from 11:23Z to 12:03Z (440 samples) covering two self-play jobs and the presort's start; and the file-open
  report's earlier readings (queue 5 to 13, 63 ms to 1 s a read, during the jobs' writes).
- **The attribution of a step's wait to the disk is inferred** from (a) its reads: a run that read 300 MB or more against a warm run of the
  same step that read under 100 MB; (b) its wall minus the warm median; (c) the file-open report's measured first-touch cost. The machine's CPU
  cannot discriminate: the grouping step is one thread, the machine's other CPU is the loop's six workers, and the cold and warm runs show the
  same machine CPU (38 to 42% median).
- **Cold start-up wall time was not measurable.** Every probe ran with the machine at 100% CPU (self-play, 20 workers), so a BelowNormal
  process got about half a core and wall times are scheduling noise; CPU time and I/O counts are the robust figures (section 2). Evicting
  the file cache to get a truly cold start needs administrator rights.
- Load at each measurement is stated with it. Other work running throughout: the always-on loop, the lab's runner, another worker's two-minute
  probes (`probe_emu.py`), the owner's sessions.

## 1. The timeline join

Sources: the watcher (above), `referee/lab/runner.log` (a line per finished command with its wall; start = end minus wall), the loop's
phases `referee/gym-loop/gpu.jsonl` (one-minute records: `generate`, `gate`, `yield`, `starts`, `waiting`) and `loop.log`, the night's
`machine.jsonl`. Window 26.3 h. The whole machine: mean CPU 56% (median 50%), 199.6 GB read, 126.7 GB written.

### 1.1 Where the reads and writes went (the window; each sample given to the lab step running; "no lab step" = between steps)

| Step | Hours | Read GB (share) | Written GB (share) | Machine CPU mean |
|---|---|---|---|---|
| groups | 5.83 | **121.7 (61%)** | 15.9 (13%) | 35% |
| no lab step (job gaps, the loop's rebuild, housekeeping) | 2.33 | 36.5 (18%) | 16.4 (13%) | 63% |
| kits | 3.14 | 11.8 (6%) | 5.4 (4%) | 36% |
| corpus | 0.49 | 9.0 (4.5%) | 23.6 (19%) | 40% |
| score-real | 0.98 | 5.5 | 11.3 (9%) | 60% |
| invariants | 0.12 | 4.7 | 2.0 | 35% |
| scenario batches (fights) | 7.50 | 0.9 | 27.6 (22%) | 73% |
| codex shards | 1.23 | 3.4 | 8.0 | 51% |
| nightly real-game arm | 0.92 | 0.9 | 6.0 | 64% |
| bench-env | 0.33 | 3.2 | 1.4 | 69% |
| refset | 0.04 | 0.2 | 3.7 | 65% |
| self-play | 1.02 | 0.3 | 2.4 | 99% |
| train | 2.01 | 0.3 | 1.9 | 68% |

One grouping run (01:49Z, 3,915 s) read 87.9 GB, the week's record; the typical cold run reads 3.3 to 6.8 GB in 1,200 to 1,800 s (3 to 4 MB/s). The 127 GB written
is 48 times what the runs tree kept (2.6 GB of new files in the last 24 h): nearly all written bytes are scratch, logs and files deleted or
overwritten later, or land in other trees (the destination of the writes was not traced).

### 1.2 The jobs and steps (wall from the runner log, the week 2026-10-26 11:38Z to 11-02 11:30Z; CPU and rates from the watcher over the window)

"Disk wait" is the step's wall minus its warm run, summed over its runs that read 300 MB or more (window) or ran over 1.3 times a rolling floor
(week: the 20th percentile of the 21 runs around it). The CPU column is the whole machine.

| Job / step | Week: runs, wall | Machine CPU median / p90 | Read / write MB/s (mean) | Disk wait share | Evidence |
|---|---|---|---|---|---|
| **presort: groups** | 149, 27.1 h | 40 / 45 | 5.8 (p90 13.5) / 0.8 | **54% of wall, 14.7 h** (window: 46%, 2.82 of 6.10 h) | 17 warm runs: median 408 s, 0 to 20 MB read. 8 cold runs (read 500 MB or more): 436 to 3,915 s, 1.1 to 87.9 GB read, 3.73 h of wall, 121 GB; the typical one 1,220 to 1,800 s and 3.3 to 6.8 GB, i.e. 3 to 4 MB/s of random small files (the 88 GB run 14 MB/s). The 97,000 opens at 12 to 35 ms (file-open report) account for the excess |
| **presort: kits** | 149, 14.9 h | 42 / 46 | 1.0 / 0.5 | 16%, 2.4 h (window 16%, 0.49 of 3.16 h) | 19 warm runs median 345 s; 4 cold runs 731 to 871 s read 2.5 to 3.0 GB each |
| **presort: corpus** | 25, 1.5 h | 40 / 70 | 5.1 / 13.5 | 69%, 1.1 h | median 86 s against a floor of 52 s; every window run reads 1 to 4.6 GB and writes 4 to 12 GB; also write-bound |
| **presort: reference set** | 25, 1.0 h | 70 / 94 | 1.2 / 29.8 | 70% of 1 h, 0.7 h | writes 1.3 to 2.4 GB in 55 to 70 s. Live: 18.5 MB/s written, write latency 34 ms mean (max 183) in the 55 s |
| presort: codex walk (4 shards) | 100, 40.3 h (about 10 h of clock: the four run side by side) | 59 / 71 | 0.8 / 2.1 | about 5% | CPU-bound parsing of the 2.2 GB codex file; only the first run after a flush reads it (3.3 GB). Live, the shards of the 11:52Z presort: `D:` queue mean 0.17 (max 2.8), busy in 14 of 100 five-second samples, machine CPU 69% |
| presort: build, publish, driver, targets, checkout | 25 each, 0.4 h in all | 36 to 55 | up to 18 | under 20%, under 0.1 h | tens of seconds each |
| invariants | 26 jobs, 0.5 h of steps | 43 / 50 | 10.9 / 4.6 | once per flush: 171 s against 64 s (4.7 GB read) | one cold run in the window |
| fights: scenario batches (7 game processes) | 256, 24.3 h | 76 / 99 | 0.03 / 1.0 | none | 85% of samples at 50% CPU or more; reads nothing; writes 27.6 GB in 7.5 h (game scratch, small files) |
| self-play (20 workers, GPU prior) | 34, 11.7 h | 100 / 100 | 0.04 / 0.2 (watcher); live 0.05 to 0.2 / 0.46 to 0.50 | none | live: `D:` idle 82% of the time, queue mean 0.12 to 0.15 (max 2.8); busy (under 50% idle) in 12 of 93 and 16 of 198 five-second samples; each job writes about 450 MB in 43,000 small writes, of which 32 MB stay in 41 files |
| train | 12, 13.6 h | 100 / 100 (one 40-minute stretch at 7%: one thread, GPU 0, no disk traffic) | 0.04 / 0.26 | none | read 276 MB in 7,320 s |
| score-real (12 game processes, then the emulator arm) | 4, 2.9 h | 54 / 100 | 1.6 / 3.2 | not separable | 5.5 GB read and 11.3 GB written in the hour; 46% of samples under 50% CPU; no queue figures exist for it |
| **night's real-game arm** | 6 in the week, 0.93 h now (both arms; the real arm 33 min) | 74 / 79 | 0.3 / 1.8 | last 3 nights: none. 10-29 and 10-30: 15 to 20% of the block | see 1.3 |
| the always-on loop | 24 h a day | 44 / 49 in `starts`, 27 to 72 in the other phases | 4.3 (`starts`) / 1 | none | whole folder 0.47 GB in 754 files; its rebuild of the start set (10:24Z to 11:10Z) runs its six workers, not the disk |

### 1.3 The real-game arm, with its own queue and latency (`machine.jsonl`, `D:`, every 30 s)

| Night, block | Samples | Queue median / p90 / max | Latency ms median / p90 / max | CPU median | Share of samples queue over 2 / latency over 20 ms | Buckets of 5 min under half the night's decision rate, and what they looked like |
|---|---|---|---|---|---|---|
| 10-27 g7 (2,000 runs, 386 min) | 766 | 0 / 9 / 28 | 22 / 1,391 / 9,045 | 10 | 38% / 52% | 36 of 78: queue 0.7, latency 6 ms, CPU 9%: stalls, not the disk |
| 10-29 g7 (126 min) | 251 | 1 / 8 / 18 | 33 / 304 / 11,706 | 60 | 35% / 82% | 4 of 26: **latency 1,604 ms against 105, queue 4.7 against 2.4, CPU 10 against 57** |
| 10-30 g9 (149 min) | 299 | 1 / 8 / 14 | 29 / 1,710 / 14,845 | 44 | 36% / 75% | 6 of 30: **latency 2,253 ms against 98, queue 5.9 against 1.7, CPU 16 against 53** |
| 10-31 g9 (500 runs, 31 min) | 63 | 1 / 4 / 5 | 20 / 34 / 41 | 64 | 27% / 51% | 1 of 7 |
| 11-01 g9 (33 min) | 66 | 0 / 3 / 8 | 19 / 34 / 47 | 68 | 18% / 47% | 1 of 7 |
| 11-02 g9 (33 min) | 67 | 1 / 3 / 9 | 19 / 32 / 50 | 70 | 24% / 43% | 1 of 7 |

So the real arm hit the disk on two of six nights (10-29, 10-30), in windows of seconds-long latency with the CPU idle: the "8 to 13 times
slower, CPU low" windows. They were 4 and 6 of 26 and 30 five-minute buckets, 15% and 20% of those blocks. The last three nights (500 runs,
game-bound at 65 to 70% CPU) show a steady 19 ms median and 32 to 34 ms 90th percentile on `D:`, a drive loaded by its own 12 games.
Game boots (time to ready, medians over the night's distinct boots): 4.8 s (11-02, 14 boots), 5.6 s (10-29, 41; 10-31, 13), 15.9 s (10-30, 33), 16.7 s (11-01, 19), 89 s (10-27, 44). What was
reading or writing on 10-29 and 10-30 at those times was not recorded.

## 2. Process start-up

Measured once per case, two passes (the second is the warm one; the first is not cold, see below), one process at BelowNormal, with
`-X importtime` and counters read inside the process (CPU time, read operations, loaded files). The cases follow what the drivers import:
the `gen0.py` workers (`numpy`, `gen_loop`, `live_search`, `run_fields`, `search_configs`, `run_train.engine`, `sts2_gym.native`, which loads the
emulator DLL), `envproto.py` (the real-game arm), and torch in `venv-gpu` (the prior server and the trainer). Load: the lab's self-play job
(CPU 100% in every watcher sample) and the loop; my process got about half a core.

| Case (venv) | Python files read from `D:` | DLLs from `D:` | Read operations (MB) | CPU seconds, warm | Wall seconds, pass 1 / pass 2 (starved) |
|---|---|---|---|---|---|
| bare interpreter (either venv) | 2 | 0 (28 MB on `C:`) | 38 (0.1) | 0.03 to 0.06 | 2.1 to 7.8 / 3.2 to 6.1 |
| `import numpy` | 86 | 4 (24.8 MB) | 268 (3.2) | 0.17 to 0.22 | 0.7 to 41 / 1.8 to 2.8 |
| emulator worker set (`gen0` per-run imports) | 179 | 14 (46.7 MB) | 614 (7.1) | 0.64 | 8.4 / 4.6 |
| `envproto` import (real-game arm) | 90 | 4 | 340 (4.3) | 0.30 to 0.36 | 7.6 / 11.8 |
| `import numpy, torch` (`venv-gpu`) | 821 | 43 (2,846 MB mapped) | 2,189 (22.7) | 2.5 to 2.6 | 48 / 130 |
| matplotlib, onnxruntime, networkx, sympy (`venv-gpu`, the nearest to a cold venv test) | 1,006 | 12 | 2,459 (31.1) | 3.0 to 3.45 | **24.3 / 13.0** |

- Site-packages: `venv-gpu` 24,412 files (3.27 GB); the emulator checkout's `.venv` 21,530 files (0.69 GB). Both are read-only in use (newest
  file 197 h and 492 h old).
- The wall column is not usable: wall times and `-X importtime` totals follow the CPU starvation (the same case varied from 1 s to 41 s).
  The one informative pair is the last row: 11.3 s more wall in the first pass for about 1,020 files, about **11 ms a file on a nearly idle
  `D:`** (one pair, not a distribution). The file-open report measured 35 ms a file while the jobs wrote.
- **Cold-start cost, inferred** = files first touched x the per-file figure, counting each module once (double it for the `.pyc` and
  directory entries): emulator worker set 193 files = 6.8 s at 35 ms, 2.1 s at 11 ms, 1.5 s at 8 ms; torch 864 files = 30 s, 9.5 s, 6.9 s
  (plus the pages of the 2.8 GB of DLLs actually touched, at 127 MB/s).
- **Starts per week** (runner log, loop log, `LAB/jobs.json`): 247 jobs; 1,458 lab commands (each a new python or dotnet process); self-play
  36 jobs x about 59 worker starts (776 runs / `WORKER_RECYCLE` 20 = 39 recycles, plus 20 workers) = 2,100; real-game processes 99 fights jobs
  x 7 + 7 nights x 12 + score and bench jobs = about 2,100; loop daemon starts 11 in all. Warm cost: 2,100 x 0.64 s = 0.4 h; 1,458 x about
  1 s = 0.4 h; 2,100 game boots x 5 s = 2.9 h of process time, seven at a time. **About 4 h of process time a week, 0.15% of the
  machine's 2,688 core-hours; the SSD does not touch the warm part.**
- **What the SSD would cut** is the cold start, at most once per job (the file cache serves the other 19 workers and the next jobs while it
  holds): 247 jobs x 7 s (worker set) + 48 jobs x 30 s (torch: prior server or trainer) = 0.5 + 0.4 h, plus cold game boots (the nights of
  10-27 and 10-30) 99 jobs x about 20 s = 0.55 h. **At most 2 hours a week of single-process wall at job starts, probably under 1**; the cold
  fraction is unknown and cannot be measured without flushing the cache. After a 88 GB read (the grouping step's worst run) it is certainly cold.

## 3. The emulator DLLs and the game

- Each emulator process loads `out/Sts2Emulator.dll` of the fork worktree named in the job: `fork/wt-reset-c-run/out` (self-play today),
  `fork/wt-lab/out` (the lab tree), `fork/wt-gym-loop-run/out` (the loop; not sized). The two sized `out/` folders are 6 files, 0.139 GB each; the DLL is mapped and cached after the
  first process. Cold: 6 files = 0.2 s plus about 1 s of reading. **Nothing to gain.**
- The real game: every job's game path is on `D:` (`LAB/jobs.json`: `referee/game-env` for the night, score-real and bench-env; the lab runner's
  `--game referee/game-lab`). Each is 222 files, 2.91 GB (`SlayTheSpire2.pck` 1.90 GB, the exe 0.89 GB), and the lab makes them with
  `referee/linkcopy.py` (a link copy: check for hard links before moving, section 6). The install they were copied from was not touched. A game
  boot reads about 60 to 70 MB through `ReadFile` (the night's 14 boots read 870 MB with the rest of the block); a boot is 4.8 to 5.6 s warm.

## 4. Sizes, write rates, and what the SSD would buy

Directory metadata only (`scandir`, one tree at a time, BelowNormal; the 205,000-file tree listed in 1.5 s from cache, nothing took over 20 s).
"New files 24 h / 7 d" = files whose modification time is that recent (a floor for the write rate: overwritten files count once).

| Candidate | GB | Files | New files, last 24 h / 7 d | Read by | Gain from the SSD |
|---|---|---|---|---|---|
| `referee/lab/runs` | 70.48 | 205,547 (23,867 dirs) | 8,475 files 2.62 GB / 39,179 files 12.9 GB | grouping, kits, invariants, train (shards), prune | grouping and kits cold excess 17.1 h a week x 77% (35 to 8 ms a file) = **13.2 h a week against today's code; about 2.1 h after the grouping cache** (kits 1.8, new files for groups 0.3); the reads of the grouping step (61% of all reads) and the self-play bursts leave the shared disk |
| `referee/corpus` + `referee/refset` | 1.12 + 2.57 | 18,077 + 4,817 | 2,428 files 0.02 GB / 12,851 files 0.10 GB; refset 3 / 26 files | corpus check, reference-set score | corpus 1.1 h + reference set 0.7 h a week, about 60% of it: **about 1.1 h a week** (the reference set is write-bound: 1.3 to 2.4 GB per 60 s run; the SSD writes about 4 times faster sequentially). Where their scratch writes go (corpus 4 to 12 GB a run) was not traced |
| `venv-gpu` | 3.27 | 24,444 | none (197 h old) | prior server, trainer, torch jobs | cold torch start 30 s to 7 s; **under 1 h a week**; every restart of the loop and the lab is faster |
| emulator checkout `.venv` (inside `src/sts2`) | 0.75 | 21,562 | none | every `{python}` command and worker | cold worker set 6.8 s to 1.5 s; **about 0.5 h a week**. **The owner's step**: it is inside the read-only checkout |
| `referee/game-env`, `referee/game-lab`, `referee/game` | 2.91 each (may share data by links) | 222 each | none | night, score-real, bench-env, the lab's fights | cold boots 16 to 89 s down to about 5 s; protects the night from a busy neighbour (15 to 20% of two nights' wall); **about 0.5 h a week** |
| `data/spire-codex`, `referee/decompiled` | 2.19 + 0.02 | 3 + 3,426 | none | the four codex shards | the file is read sequentially (127 MB/s: 17 s for a cold shard, 4.5 s on the SSD); the decompile is 3,426 small files; **under 0.2 h a week** |
| `referee/gym-loop` (buffer, checkpoints, starts, gate, games) | 0.47 | 754 | 374 files 0.32 GB | the loop | **nothing measurable**: its rebuild and segments are CPU-bound |
| `referee/lab/results`, `lab/nightly`, `lab/cache` | 0.32 + 0.03 + 0.015 | 240 + 109 + 4 | small | the checks | nothing |
| the fork's `out/` folders | 0.139 each | 6 | none | emulator processes | nothing (section 3) |
| `fork/*` worktrees, `spireline/` repo | 0.3 to 0.55 each; 0.16 | 2,500 to 4,700 each; 3,468 | 0.4 GB in 24 h in the lab tree and the loop's tree | git, builds, the runner | not measured; git paths stay where they are |

Both drives, for scale: `D:` 1,863 GB, 148.9 used; `C:` 465 GB, 162 used, 303 free.

Raw device figures, measured once (unbuffered reads, so the file cache plays no part; 11:54Z, self-play at 100% CPU and the presort starting;
`D:` about 80% idle at the time):

| | `D:` hard disk | `C:` solid-state |
|---|---|---|
| sequential, 1 MB reads, 256 MB | 127 MB/s | 491 MB/s (3.9 times) |
| random 4 KB reads inside one 317 MB file (n = 300), median / p90 / max | 4.1 / 9.3 / 18.0 ms | 0.13 / 0.15 / 0.24 ms |

The random figure is within one file (short seeks) and understates the drive's full-stroke seek (about 12 ms; the first touch of a
small file anywhere on the disk was 35 ms loaded, 11 ms on a nearly idle disk).

## 5. Who writes while the readers read

- **Self-play** is the one regular writer while nothing else uses `D:`. Live, with 20 workers: 450 MB in 19 minutes in 43,200 write operations
  (about 10 KB each) as short bursts of 500 to 1,700 writes a second (4 to 13 MB/s, 5 to 10 s long) every one or two minutes, produced by all
  the workers together (each 40 to 140 write operations a second in the process counters, which include pipe traffic, so the target files are
  not proven). It keeps 32 MB. Write latency in the bursts is 1 to 6 ms with outliers of 100 to 500 ms.
- **The scenario batches** write about 1 MB/s (27.6 GB in 7.5 h) and read nothing; **the night** about 1.1 MB/s; **the loop** under 1 MB/s; the
  grouping step itself writes 0.8 MB/s (28 MB of `groups.json` at the end, plus its cache).
- **Heavy single writers**: the corpus check (13.5 MB/s, 4 to 12 GB a run), the reference-set check (18 to 30 MB/s for 55 to 70 s), score-real
  (3.2 MB/s, 11 GB in the hour).
- During a cold grouping run the other writers are the loop and its games (a few MB/s at most). The waiting there is the grouping step's own
  reads queueing behind each other and behind the small-write bursts (file-open report: queue 5 to 13, 63 ms to 1 s a read), not behind a
  heavy writer. The watcher does not record per-process disk figures; the live probe's per-process figures count I/O of every kind.

## 6. The ranked move list

Decision text (`docs/DECISIONS.md`, D46): the lab's run files move to the SSD in the first quiet window after the 2026-11-03 night, by a
directory link at the old path, the old copy kept a day. In the order of value:

| # | Move | GB | What it buys (lab clock) | Risk |
|---|---|---|---|---|
| 1 | `referee/lab/runs` | 70.5 (cap 100; weekly growth 12.9) | **13 h a week against today's code, about 2 h after the grouping cache**; the self-play write bursts and 61% of all reads leave the shared disk. The grouping step's first run on the cache is the test of how much the move is still worth (prediction: 4 to 6 minutes) | none to the data; one slow first read of the whole tree after the copy (Defender sees 205,000 new files: about 25 to 40 minutes of its CPU) |
| 2 | `referee/corpus`, `referee/refset` | 3.7 | about 1.1 h a week (corpus and reference-set checks) | low |
| 3 | `venv-gpu` (ours); the emulator `.venv` later, by the owner | 3.3 (+0.75) | under 1 h a week of cold starts; faster restarts | a venv holds absolute paths: a directory link keeps them valid; do not recreate it |
| 4 | `referee/game-env` (one copy, then link `game-lab` and `game` to it) | 2.9 | about 0.5 h a week; a steadier night | `linkcopy.py` may make hard links: copy once and link the three paths, do not make three copies; the night's build check on the game folder must still match |
| 5 | `data/spire-codex`, `referee/decompiled` | 2.2 | under 0.2 h a week | none; do last, or never |

Total 83 GB (112 GB at the lab's cap) of the 303 GB free on `C:`.

**How, per item (the lab's own practice, in a quiet window after the night's block, with the runner between jobs):**

1. Stop the writers of the tree at a job boundary: the lab runner writes `runs`; for items 3 and 4 also the loop. Do not move anything while
   `QUIET.lock` names a running block.
2. `robocopy <old> <new> /MIR /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8` while the lab is still running (70 GB, 205,000 files: about 10 minutes of
   bytes at 127 MB/s and up to 40 more for the files, so a first pass can run in advance), then a second `/MIR` pass with the writers stopped
   (minutes).
3. Check that file and byte counts are equal (205,547 files, 70.48 GB for `runs` as of this report; more by then), rename the old folder
   (`runs.old`) and create the junction at the old path (`mklink /J <old path> <new path>`; a junction crosses drives and needs no
   privilege). Paths in `jobs.json`, the runner, the loop and the old job folders stay valid; nothing is edited.
4. Restart the runner; the next job, then the next presort's grouping run, are the check (a cold run should no longer occur).
5. Keep `runs.old` one day, then delete it. Rolling back = remove the junction, rename `runs.old` back.

**What must not move:** `src/sts2` and its checkout (read-only; the unlock and the `.venv` move are the owner's steps); the fork repository and its
worktrees (git records their absolute paths); `spireline/` (the repo); `LAB/jobs.json`, `LAB/state.json`, `QUIET.lock` and the logs (small, edited
by hand or by many writers, no gain). The `versions*.lock` files, `results/`, `data/` contents and game DLLs are never committed wherever they
live. Do not exclude `runs` from Defender: the 8 ms SSD figure already contains its scan.

## 7. What was and was not measured

Measured: the join of 9,276 watcher samples to 1,458 command lines; the six nights' queue and latency; the 440-sample live disk probe;
start-up CPU time, read operations and file counts of six import sets; sequential and random raw reads on both drives; tree sizes and write
recency; the weekly walls and the cold and warm runs of the reading steps.

Inferred: the disk's share of each step (cold minus warm); the per-file SSD gain (the file-open report's 35 ms and 8 ms); the cold-start hours;
the post-cache residue (the cache's first run has not happened yet); the hours returned.

Not measured: queue and latency during the grouping, kits and corpus steps (the watcher lacks them; the live probe ended before the presort
reached them); a true cold start of any venv; who wrote the 120 GB a day that no tree keeps; the Defender exclusion list; score-real's disk wait;
what hit the disk on the nights of 10-29 and 10-30; the effect of the cold grouping reads on a job running beside it (the running runner
started 2026-10-29 and still runs groups and kits as serial steps; step D's "beside the next job" is in the code but not in that process).
