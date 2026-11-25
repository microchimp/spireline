# Brief: lane 23, the strict reader credits a boss fight our player actually played

Written 2026-11-24 04:25Z by the orchestrator. Spireline lane (the Spireline repo `D:/spireline/spireline`, not the fork), Sonnet. Read `COMMON.md` first (worker rules), then `REAL-ROWS-LOST.md` (lane 8: the strict reader and why), then `REFEREE-TRACK.md` (lane 21: group C and "For the orchestrator: the reader"), then the code: `tools/strict_rows.py` (the reader), its callers `tools/boss_entry.py`, `tools/morning_report.py`, `tools/weekly_numbers.py`, and the tests under `tests/` (lane 8 left 305 tests and a `--check` mode; keep both green).

## The fault

The strict reader reads a real-game row the referee lost its place on by the **first** loss of the whole run: everything after that floor is uncredited. Lane 21 showed from the divergence records that in 7 of the 95 "lost" arrivals of the 11-20 block our player did play the first Act 3 boss fight itself: the loss came at the second boss, or was lost and recovered before the first. The reader credits none of them. Read correctly, the 11-20 block (`D:/spireline/referee/LAB/nightly/2026-11-20T1904/g20/`: `runs.jsonl`, `divergences.jsonl`) reads 68 passes in 348 arrivals (19.5 in 100, not 17.5), and our player passed 68 of the 260 fights it finished itself (26.2 in 100, not 61 of 253 = 24.1). The same fault touches the 11-19 block (`2026-11-19T1103/g19/`, group C 5 rows).

## Tasks

1. **New rows** (from the next block on; fork `f98caf6c` writes them): a row's `stats.boss_fights` lists each boss fight {act, floor, first decision, decisions, stand_in, first_stand_in}; a boss fight is our player's when its `stand_in` is 0. The reader credits a boss as beaten by our player when the run went past it **and** its fight has `stand_in` 0; a fight with `stand_in` above 0 is the stand-in's (uncredited, as now). A loss recovered before a fight does not void that fight.
2. **Old rows** (11-19, 11-20, and any block without `boss_fights`): read the loss intervals from the block's `divergences.jsonl` as lane 21's `backlog/act3-week/referee-track/classify.py` and `spans.py` do (each loss lasts to the end of its not-ranked span; a fight is our player's when no loss interval covers any of its decisions), not `first_loss`. Where the divergence file is missing, fall back to today's first-loss rule and say so in the output.
3. **Every caller reads the same way**: `boss_entry.py`, `morning_report.py`, `weekly_numbers.py` (and anything else that reads `lost` rows; grep). One reader, no second rule. `--check` compares the new reading with the old on a block and lists the rows that changed, with the reason (recovered before the fight; lost at the second boss).
4. **Re-read both blocks** with the new reader and put the figures in your report and in `backlog/act3-week/REAL-ROWS-LOST.md` as a dated addendum: for 11-20 and 11-19, passes per 100 arrivals on all arrivals, passes per 100 on the fights our player finished, lost-track arrivals, per boss (Aeonglass, the Queen, the Test Subject), each count as "N of M". These are the numbers the paper and the stop rule will quote; they must be exact.

## Limits

Read-only under `D:/spireline/referee/LAB`; nothing under `D:/spireline/src`; no live-game script; no heavy CPU (the reader is pure Python). Python: `D:/spireline/spireline/.venv/Scripts/python.exe`; `D:/` paths for anything Python reads. Results and messages hold no host names, user names or absolute user paths; the rows hold no human data.

## Deliverables and report

The change with tests, committed to Spireline `main` and pushed once the tests pass (no PR; check `git log HEAD..origin/main` is empty first; add only your files, never `.claude/`, `morning-summary-2026-10-16.md` or `spireline/.gitignore.tmp`); the commit message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <<email>>`. Report in at most five lines: the commit hash, the test count, the 11-20 and 11-19 readings (all arrivals; player-finished; lost-track; as "N of M"), how many rows changed and why, what you could not verify.
