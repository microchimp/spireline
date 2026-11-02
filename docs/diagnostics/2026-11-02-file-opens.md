# What costs the 12 ms per file open in the lab's grouping step (2026-11-02)

Question (owner, after worker D's profile of `lab_groups.py`: 97,000 opens, about 12 ms each, 1,214 s of a 2,472 s run, D guessed the antivirus): what does the 12 ms consist of, and what is the right fix?

Everything below was measured read-only on the live machine while the self-play job and the fight trainer were running, at BelowNormal priority, each pass under about a minute (two of them stopped at a 40 s budget). Paths are relative to `D:/spireline/`. Raw per-call times and counter samples are not kept (scratch only).

## Answer in five lines

- The 12 ms is mostly the hard disk. `D:` is one 2 TB desktop hard disk (Seagate ST2000DM008) that also takes the jobs' writes (about 360 writes a second, 5 to 13 requests waiting). A file the code touches for the first time costs about 35 ms in total on it; the same file a second later costs 0.09 ms.
- Defender is real but second: about 7 to 12 ms of scan per file, on about half the files (those whose scan result it no longer remembers), so 3 to 4 ms of the 12 ms (a quarter to a third of the `open` call) and about an eighth of the whole cost of getting a file's contents. A Defender exclusion would not remove the disk part: the data would then be fetched by the code's own read instead.
- Repeated opens of the same file and machine load as CPU are not the cause (about 7.6% of opens are repeats, all served from memory at 0.05 ms; CPU scheduling added under 0.5% on warm calls).
- The step's own runs prove it: same code, same sources, 343 to 440 s when the files are still in memory (23 of the last 40 runs) and 800 to 3,915 s when they are not (mean 827 s, median 436 s).
- The fix is not to open the files at all: a cache of what the step learned from each finished job and each source, keyed by the file sizes and times the directory listing already gives (1.5 s for all 205,000 files). Expected run: about 4 to 6 minutes, flat.

## 1. The sources: what the step opens

Code: `tools/fidelity/lab_groups.py` (fork main `d5fcd126`): `lab_sources` (finds and sniffs), `batch_symptoms` and the other readers, `pool_size`.

| Item | Number |
|---|---|
| Job folders under `referee/lab/runs` | 848, of which 840 finished (`done.rc`) |
| Files under the finished jobs | 204,879 in 23,445 folders (70 GB for the whole `runs` tree); 67,748 of them inside `*.packs` folders |
| Sources the last run (04:22Z) used | 2,334: 1,832 setup/aimed batches, 215 invariants, 64 mutation, 64 runs, 60 codex walks, 58 corpus, 41 refset |
| Symptoms produced | 439,818 (codex 310,619; corpus 85,577; batches 21,689) |
| Opens by `lab_sources` (opens the first 4 KB of every `.json` that is not a verdicts/out/emu/reanchor/trace/runs/packs file, to tell what kind of output it is) | 40,938, all different files (matches D's 40,938) |
| Opens by `job_outputs` (reads each job's `job.json` again) | about 840 |
| Opens by the batch readers | 29.9 per batch (23.8 that find a file, 6.1 that find none: optional files such as `.aims.json`, `.shrink.json`); 1,832 batches gives about 54,700 (63 batches sampled) |
| Opens by the other readers | about 1,200 (sampled; codex reading is slow for its parsing, not its opens) |
| Total | about 97,700, D's figure |
| Opens of a file already opened earlier in the same run | about 7,400 (7.6%): each `verdicts.json` twice (`batch_symptoms`, `pool_size`: 1,832), each batch's spec, aims and shrink files read again after the sniff (4,128), `job.json` (about 840), the runs/corpus/refset/codex files once more in `pool_size`. The rest, about 90,000, are 90,000 different files |
| Opens that find no file | about 11,200, at 0.11 ms each |
| Size of the sniffed files (2,000 sampled) | median 21.8 KB, mean 39 KB, 90th percentile 69 KB, maximum 2.8 MB; 15% under 4 KB |
| Folders touched by a 2,000-file sample | 560 (the files are spread over the whole disk, not clustered) |

So: not the same files again and again. About 90,000 different files, each opened once, spread over 23,000 folders, with a small tail of repeats that are served from memory.

## 2. The disk

| Item | Value |
|---|---|
| `D:` | disk 0, Seagate ST2000DM008, 2 TB, SATA, Windows media type HDD (spindle speed not reported) |
| `C:` | disk 1, Samsung SSD 860 EVO 500 GB, SATA (269 GB free) |
| What is on `D:` | the repo, `referee/` (lab, runs, results), `venv-gpu`, the emulator checkout, the fork. The Python interpreter itself is on `C:`; the venv's packages are on `D:` |
| Disk counters during the 1,200-file pass (mean) | `D:` 44.6 reads/s, 63 ms per read, 5.5 requests waiting, disk busy 531% (more than five requests in flight on average); the 8 s before it: 5.8 reads/s, 362 writes/s, 7.4 waiting |
| Same during the old-folders pass | `D:` queue 10.5, an average of about 1.0 s per read (the jobs were writing hard) |
| Same on `C:` during the SSD pass | 0.18 ms per read, no queue |
| Machine | 16 logical CPUs, total CPU 56% before the pass and 92% during it, 8.4 GB of 32 GB free |

A 7,200 rpm drive needs about 12 ms for one random read when nothing else uses it; the jobs' traffic makes each read wait behind several others.

## 3. Open cost on the real files

Median / mean in ms. One pass is: open, read the first 512 bytes, close.

| Set (pass) | n | open | read | close | open+read+close | wall |
|---|---|---|---|---|---|---|
| Grouping files A, pass 1 (first touch) | 2,000 | 0.17 / 16.2 | 0.09 / 11.7 | 0.07 / 6.9 | 19.7 / 34.8 | 69.7 s |
| A, pass 2 (same files at once) | 2,000 | 0.05 / 0.05 | 0.02 / 0.03 | 0.01 / 0.01 | 0.09 / 0.09 | 0.2 s |
| A, pass 3 (full read, 78 MB) | 2,000 | 0.05 / 0.05 | 0.05 / 0.51 | 0.01 / 0.02 | 0.12 / 0.58 | 1.2 s |
| Grouping files B, pass 1 (with counters) | 1,200 | 0.14 / 19.1 | 0.08 / 11.5 | 0.07 / 6.8 | 21.9 / 37.4 | 44.9 s |
| B, pass 2 | 1,200 | 0.04 / 0.05 | 0.02 / 0.10 | 0.01 / 0.01 | 0.08 / 0.16 | 0.2 s |
| B, pass 3 (full read, 50 MB) | 1,200 | 0.04 / 0.05 | 0.05 / 2.27 | 0.01 / 0.01 | 0.11 / 2.34 | 2.8 s |
| Old folders (`referee/game-*`, `jobs-*`, `lab-*`, not touched for 5 days), pass 1 | 1,638 (40 s budget) | 0.03 / 23.4 | 0.02 / 0.88 | 0.01 / 0.35 | 0.05 / 24.6 | 40.3 s |
| Old folders, pass 2 | 1,638 | 0.03 / 0.03 | 0.01 / 0.01 | 0.01 / 0.01 | 0.05 / 0.05 | 0.1 s |
| Old folders, pass 3 (full read, 132 MB) | 1,638 | 0.03 / 0.03 | 0.04 / 8.75 | 0.01 / 0.03 | 0.08 / 8.82 | 14.4 s |
| `C:` SSD, 2,000 old Python library and docs files, pass 1 | 2,000 | 6.3 / 4.9 | 0.04 / 0.04 | 0.04 / 0.04 | 6.4 / 5.0 | 10.0 s |
| `C:` SSD, pass 2 | 2,000 | 0.06 / 0.06 | 0.01 / 0.01 | 0.01 / 0.01 | 0.08 / 0.08 | 0.2 s |

What the passes show:

- First touch costs 35 to 37 ms on `D:`; the second touch costs 0.09 ms (400 times less). The thread's CPU during pass 1 was 1% of the wall time: it is all waiting.
- The cost lands on one call only, never two. In set A, 49% of the files paid it in `open` (mean 33 ms there, and then read and close cost 0.1 and 0.3 ms); the other 51% opened in 0.1 ms and paid in `read` (mean 23 ms) and, for a third of them, `close` (13 ms). Under 0.5% of the files were slow in both. Set B: the same (550 slow opens, mean 41.6 ms; the rest read 20.9 ms plus close 12.0 ms).
- The old folders were mostly still remembered (87% of opens under 1 ms), but the 213 that were not cost 180 ms each, at a time when the disk queue was 10 to 13 deep and Defender was idle (10% of one core against 6.5% before). Their full read cost 8.8 ms a file later, with Defender idle: the disk alone.
- The 4-to-6 times difference between `C:` (6.3 ms, the cost of a Defender scan, see section 4) and `D:` (33 to 42 ms for the same kind of first open) is the disk.
- Slow-open cost by file size (set A / B means; SSD for comparison): under 4 KB 15 / 21 ms (SSD 6.8), 4 to 16 KB 29 / 40 (8.4), 16 to 64 KB 37 / 44 (9.8), over 64 KB 49 / 58 (11.7).

## 4. The antivirus's share

Defender: real-time protection and on-access protection on, behaviour monitoring on, signatures 1.463.79.0, `ScanAvgCPULoadFactor` 50. The exclusion list could not be read (needs an administrator); the engine process's CPU seconds could not be read either (the process is protected, `Get-Process` returns nothing), so the performance counter `% Processor Time` of `MsMpEng` was sampled once a second instead (100 = one core).

| Window | MsMpEng CPU (cores x 100) | Other counters |
|---|---|---|
| `D:` set B, 8 s before | 39 | `D:` 5.8 reads/s, 7.4 waiting |
| `D:` set B, pass 1 (45 s) | 99 | `D:` 44.6 reads/s, 63 ms per read, 5.5 waiting |
| `D:` set B, pass 2 and 3 | 25 and 15 | cached |
| `C:` SSD, 8 s before | 8 | |
| `C:` SSD, pass 1 (10 s) | 99.5 | `C:` 139 reads/s at 0.18 ms; `D:` unchanged |
| `C:` SSD, pass 2, pass 3, 5 s after | 80, 51, 6 | |
| `D:` old folders, pass 1 (40 s) | 10 (6.5 before) | `D:` 10.5 waiting, about 1 s per read |

- Defender scans a file when it is opened and it has no remembered clean result (new signatures, or an evicted entry). The engine's CPU rises to a full core exactly during the first-touch pass and falls back when the files are remembered (pass 2); it does not rise in the old-folders pass, whose files it still remembered, although those opens were slower (180 ms).
- The scan blocks the opening thread. On the SSD, where a disk read is 0.18 ms, a scanned open cost 6.8 ms (under 4 KB) to 11.7 ms (over 64 KB), 8.1 ms on average, for 61% of the files. That is the Defender cost with the disk taken out: 7 ms fixed plus about 0.1 ms per KB. By file size the `D:` files (mean 40 KB) would cost 9 to 12 ms.
- The scan also pulls the file's data into memory: on `D:`, a file that was scanned at open had a read of 0.1 ms afterwards, a file that was not scanned paid its data read (23 ms) later. That is why the cost lands on one call only, and why the scan "hides" the disk read inside `open`.
- Control, new 1 KB files (create, write, close, then read at once, then read after 3 s):

| Disk | create | close after write | open+read at once | after 3 s |
|---|---|---|---|---|
| `C:` SSD, 2,000 files | 0.24 ms | 0.15 ms | 0.51 ms (Defender 112% of a core) | 0.04 ms |
| `D:` HDD, 2,000 files | 10.9 mean, 0.14 median, 87% under 1 ms, 99th percentile 164 ms, maximum 1.9 s | 0.31 ms | 0.64 ms | 0.04 ms |

On the SSD Defender costs about 0.5 ms around a new small file (0.2 create, 0.5 first open against 0.04 later) and the writer is not held up. On the HDD the same files read at the same 0.64 ms once they are in memory, so Defender's cost does not depend on the disk; what the HDD adds is the create (10.9 ms mean, a metadata write that waits in the queue) and every read that is not in memory. The probe folder was deleted (`referee/backlog/file-open-probe`, gone).

## 5. The disk's counters and the machine's load

- During set B pass 1 the `D:` queue held 5.5 requests and each read took 63 ms; in the old-folders window 10.5 requests and about 1 s a read. The jobs write about 360 times a second (before the pass). The pass itself added about 39 reads a second.
- Machine load as CPU: a warm loop of 188,700 open+read+close of 300 remembered files over 12 s at BelowNormal ran at 99% of its thread, median 0.056 ms, 19 calls over 1 ms, 3 over 5 ms, none over 20 ms, maximum 8.8 ms: the CPU scheduler cost under 0.5% (0.05 s in 12 s). Pass 2 of every set shows the same.
- Stat calls are cheap: `os.stat` on 1,500 files of the grouping set: median 0.05 ms, mean 0.07 ms, maximum 4.4 ms. `os.scandir` with `DirEntry.stat` over all 848 jobs: 205,440 files in 23,840 folders in 1.49 s (0.007 ms a file); the first listing of the day took 2.9 s. So the sizes and times of all 205,000 files can be had for about 3 s, and the digest the step already computes needs nothing more.

## 6. Verdict

Per file the step touches for the first time (about 35 ms in samples A and B; the step's `open` call alone averaged 16 to 19 ms of that, and D's 12.5 ms is the same figure diluted by the 11,000 cheap failed lookups):

| Cause | Share of the cost of getting a file | Share of the `open` call | Evidence |
|---|---|---|---|
| The hard disk (random reads waiting behind the jobs' writes) | about 85% (about 30 of 35 ms) | about 75% | `D:` queue 5 to 13, 63 ms to 1 s a read; same files 0.09 ms from memory; old folders with Defender idle cost 24 ms a file and 180 ms for the slow ones; SSD first open 6 ms with a 0.18 ms disk |
| Defender's scan at open | about 12% (about 4.4 ms: 49% of files x about 9 ms) | about 25% | MsMpEng CPU at a full core only during first-touch passes; 6.8 to 11.7 ms per scanned file on the SSD; read after a scanned open is 0.1 ms |
| Opening the same files again and again | about 0 (7.6% of opens are repeats at 0.05 ms) | 0 | pass 2; histogram of opens per path in 63 sampled batches (1,756 files once, 63 twice) |
| CPU load of the machine | under 0.5% | | warm loop of 188,700 calls |
| Python's `open` / NTFS small-file overhead as such | 0.05 ms a file | | warm passes; stat 0.05 ms |

Caveat on the split: the 85% disk figure includes the jobs' queue. A quiet drive would answer a random read in about 12 ms (its specification, not measured here; the machine was never quiet), so of the roughly 30 ms of disk per file about 12 ms is the drive's own seek and the rest is waiting behind the jobs. The step's real durations show the same spread: of the last 40 runs 23 took under 500 s (the files still in memory: 343 s at the least), the rest 586 to 3,915 s; a cold run is limited by the disk, not by the code.

So D's guess (Defender) is right about a minority of the cost and wrong about the main part. Applied to D's 12.5 ms per open: Defender about 3 to 4 ms (a scan costs 7 to 12 ms and half the files need one; about 27% of the `open` call in my samples), the disk about 8 to 9 ms, repeated opens and load about nothing. Over the whole first touch (open, read, close: 35 ms) Defender is 4.4 ms and the disk about 30 ms.

## 7. The right fix

What to avoid: opening 90,000 finished, never-changing files on every run. A cheaper open is not available (the cost is the first touch), and a finished job's files do not change.

Recommended (two parts, one change, in `lab_groups.py` with the cache in `LAB/cache/`, using the `stepcache` helpers that exist):

1. A source list per finished job: `lab_sources` stores, per job folder, the list of (kind, path) it found, keyed by the job's name and `done.rc` time (a finished job is not written again; `stats_hash` already assumes it). The 40,938 sniffs and four recursive walks per job go; only new jobs are sniffed. Removes about 42% of the opens (all of D's 809 s `lab_sources` line).
2. A symptom list per source: the output of `batch_symptoms` / `run_symptoms` / `corpus_symptoms` / the other readers, stored per source, keyed by (a) the sizes and times of the source's files, which `source_files` and `inputs_parts` already compute for the skip digest, from one `scandir` listing instead of `os.stat` per file, and (b) a digest of what the symptoms depend on: `lab_groups.py`, `lab_targets.py`, `hook_table.py`, `referee/scenarios.py`, `tools/fidelity/fight_compare.py` (the derived verdicts), `data/id_map.json`. Removes the other 55,000 opens and the parse of 440,000 symptoms (the cache is about 860 MB as JSON, 610 MB of it the 60 codex walks, which could stay uncached or be stored compressed; loading all of it takes about 6 s of parsing and a sequential read). Failed lookups of absent optional files are replaced by the listing the step already makes (`ls`).

Expected grouping run after the fix, from the real durations (the step does grouping and writes 28 MB of `groups.json` after the reading, about 340 s on a warm run in total, of which opens and parsing are a part):

| | Run time |
|---|---|
| Today, files in memory | 343 to 440 s |
| Today, files not in memory | 800 to 3,915 s (mean of the last 40 runs 827 s) |
| After part 1 only | the cold part falls by about 42%: cold runs about 500 to 2,300 s |
| After parts 1 and 2 | a listing of 3 s, the cache load (6 to 20 s), the new sources only (1 to 3 jobs, a few hundred opens, about 10 s cold) and the grouping itself: about 4 to 6 minutes, whatever the state of memory |

D's own guess ("about the grouping's 10 minutes", cProfile) agrees. The cache also removes about 90,000 random reads from the disk the jobs write to, which slows the jobs as well as the step.

Cost to build: about 150 to 250 lines in `lab_groups.py` plus tests (changed file reruns, changed code reruns, deleted cache rebuilds, new job only reads the new job), the size of D's step D: one worker session of a few hours. The care is in the key: the cache must be thrown away on any change to the code or maps listed above; a stale hit would hide a fix. The step cache's `--force` should also clear it. Risk is low: deleting `LAB/cache/` returns today's behaviour.

Other options and why not first:

- A Defender exclusion for `referee/lab/runs` (the owner's setting, not touched here). Saves about 4.4 ms of 35 ms a file (12%; the data fetch that the scan does inside `open` moves to the code's `read`, it does not vanish), about 100 to 450 s of a cold run's 800 to 3,900 s, and some of the engine's CPU (a full core during every cold run, a quarter core while a job writes). It leaves the disk. Worth considering only for the CPU, after the cache. The folder holds only our own JSON.
- Moving `referee/lab/runs` (70 GB) to the SSD: first touch would fall from 35 ms to about 8 ms and the step would no longer share a disk with the jobs. A larger change (paths in `jobs.json`, the runner, the old runs) and 70 GB of the SSD's 269 GB free, with the jobs' writes then on the SSD. Possible later; the cache gets most of it for no hardware change.

## 8. What I could not measure

- Defender's exclusion list and its CPU seconds (administrator needed; the performance counter was used, once a second, with other activity on the machine in the baseline: 2 to 39% of a core).
- The disk with nothing else running: the jobs ran throughout, so the drive's own seek (12 ms) is its specification, not a measurement, and the cache could not be made cold on demand (no administrator); "first touch" means files not in memory at the time, about half of each sample.
- The `close` stall (12 to 13 ms on a third of the files that were not scanned at open, none on the SSD): not explained; probably the disk (read-ahead the close waits for), not Defender.
- The share between the disk's own seek and the jobs' queue for the main cost, and the exact count of opens per phase (the totals are a 63-batch sample scaled to 1,832 plus counts from the file listing; they match D's 97,000).
