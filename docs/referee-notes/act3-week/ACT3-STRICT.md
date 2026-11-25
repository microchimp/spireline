# Lane 1: counting Act 3 honestly (strict boss reading)

Written 2026-11-19 by lane 1 (Sonnet 5.5). Landed: fork main `7dd6474e` (commits `ee9b7f1d`, `7dd6474e`; Python-only gate, 642 selected tests, 0 new failures) and Spireline main `4cfe99a` (296 tests pass). Branch `feat/act3-strict`, worktree `D:/spireline/fork/wt-act3-strict`. Terms: a "boss beaten" is a count the judge keeps per run; B1, B2, B3a are the Act 1 boss, the Act 2 boss and the first of the two Act 3 bosses (floor 48 at Ascension 10; the second is floor 49); "the bar" is the fraction of the boss's health the run's record says it dealt (`boss_damage_acts`); "loose" is the old reading (bar at 1.0 means beaten), "strict" the new one (the run went past the boss).

## What changed

- **One strict rule**, `keep_v2.went_past` (fork `tools/lab/keep_v2.py`). A boss is beaten when the run won, or its floor is above that boss's floor. The boss's floor comes from the row's own room string when that is complete (floor = string length + 1: true of all 29,698 emulator rows of generations 15 to 18; false for the real game's rows, which leave rooms out), else the usual 17 / 33 / 48. One run in 400 that reaches Act 2 has an Act 2 of 18 floors (boss on 35, first Act 3 boss on 50); plain floor cuts misread those, the room string does not. A crash or lost row beats nothing (it was already a floor-0 loss). A row cut off by a deadline is read by its floor like any other (all arms on disk hold 2 of them, on floors 4 and 13, plus 5 lost and 2 crashed seeds: every one beats nothing under both readings). Where a row has no complete string, a fight it records as lost (that act's first bar entry below 1.0) is never "beaten".
- `bosses_beaten` is strict for all three bosses; the old reading lives on as `bosses_beaten_loose`, used only by comparison tables. Every verdict now carries `boss_reading: strict-2026-11-19`. `deep`, `frontier_record`, the kill tables, `verdict_covariate_retro` follow by construction; `rl/run_fields_backfill.py` calls the same rule. `gen_loop.boss_kill` (Act 1 only) and the nightly summary were already floor-based and agree on every row. Spireline `tools/morning_report.py` (both readers) and `tools/boss_entry.py` read the same strict rule (tonight's real-game report will count Act 3 kills by it).
- Tools (read-only on the lab): `tools/lab/ledger_strict.py` (re-scores every judgement), `tools/lab/act3_boss_table.py` (which boss, from the seed).

## The three comparisons (loose, strict; per 100 runs in brackets)

Every judged arm on disk, 111,900 runs (89,893 carry the bar): **Act 1 and Act 2 agree on every single run.** Act 3 differs on 1,127 runs, always loose above strict.

| agent (arms, runs) | Act 1 loose / strict | Act 2 loose / strict | Act 3 first boss, loose / strict | wins |
|---|---|---|---|---|
| gen 16 (2 arms, 2,500) | 1,675 / 1,675 | 374 / 374 | 106 [4.2] / 38 [1.5] | 3 |
| gen 17 (6 arms, 9,300) | 6,827 / 6,827 | 2,133 / 2,133 | 654 [7.0] / 216 [2.3] | 6 |
| gen 18 fight-v3 (1 arm, 2,000) | 1,530 / 1,530 | 490 / 490 | 158 [7.9] / 52 [2.6] | 2 |

Per arm, per judgement: `ledger-strict.tsv` (40 judgements; the ledger file has 41 lines with its header). Plain-run store, independent: generation 17's 52,816 runs record 2.3 in 100 with the Act 3 boss `won`.

## Every saved judgement, re-scored (`ledger-strict.tsv`)

| generation (all its judged arms) | runs | first Act 3 boss, loose / strict per 100 | wins per 100 |
|---|---|---|---|
| 13 | 6,500 | 0.74 / 0.23 | 0 |
| 14 | 3,800 | 1.42 / 0.37 | 0.05 |
| 15 | 5,500 | 1.49 / 0.24 | 0 |
| 16 | 2,500 | 4.24 / 1.52 | 0.12 |
| 17 | 9,300 | 7.03 / 2.32 | 0.07 |
| 18 | 2,000 | 7.90 / 2.60 | 0.10 |

Reading the promotion judgements strictly: generation 16's cheap-v beat its base 23 to 6 on 1,700 pairs (+1.0 per 100, SE 0.32): a real Act 3 gain. Generations 17 and 18 were promoted on floors (route F), and strictly their Act 3 gain is level: 16 against 15 on 800 pairs (+0.12, SE 0.6); 52 against 47 on 2,000 (+0.25, SE 0.44). `cheap-v3d` pooled over 4,000 pairs: 131 against 95 (+0.90, SE 0.34).

## The three dry judgements (rule v3, strict reading; `strict-dry-runs/`, nothing changed)

| case | deep_f gain per 100 (SE) | 0.005 lower bound | floors | verdict |
|---|---|---|---|---|
| gen 18 block r3, fight-v3 against gen 17 (2,000) | +0.35 (0.46); first boss 52/47, wins 2/0 | -0.80 | +0.70 | **refused** (route A fails the bound and the +1.0 minimum) |
| `cheap-v3d` pooled r1+r2 against gen 17 (4,000) | **+0.975** (0.36); first boss 131/95, wins 7/4 | **+0.075 (above 0)** | -2.06, no collapse | **refused, by one run**: the minimum gain is +1.0 (40 more deep kills in 4,000; it has 39) |
| gen 17 block against 16 (800) | 0.0 (0.61); first boss 16/15, wins 0/1 | -1.63 | +1.83 | **refused** (it was promoted on floors; v3 gives floors no route) |

The loose reading had v3d pooled at +0.75 with a bound of -0.575. The honest reading puts it just under the bar rather than clearly below it.

## Why the bar empties and the run still dies

The bar is the damage dealt to the creatures the fight began with, as a share of their starting health, at their lowest health reached (1.0 when the fight is won). It hits 1.0 when every starting creature has been at 0 health at some decision, which is not the same as the fight being won when a creature comes back.

**It is one mechanism: the Test Subject.** For each first Act 3 boss, the judged arms of generations 16 to 18 (3,124 runs that began the fight; `tools/lab/act3_boss_table.py`):

| first boss | arrivals | went past | bar at 1.0 | bar at 1.0 and died there |
|---|---|---|---|---|
| Aeonglass | 1,067 | 219 (20.5%) | 219 | 0 |
| Queen (with a torch-head partner) | 1,068 | 287 (26.9%) | 287 | 0 |
| **Test Subject** | 989 | **18 (1.8%)** | **957 (97%)** | **939** |

All 20 runs of a sample (first 20 by arm, from generations 17 and 18, fraction 1.0, floor 48, death) met the Test Subject; so did all 939. The Test Subject is a boss with several forms (the game gives it three), each with more health than the last; the bar reads the form the fight began with, so it hits 1.0 when that form falls, the boss comes back, and the run dies in a later form. The other two bosses read 1.0 only when they die, so the bar is right for them. The plain-run store says the same without the bar (`won` flags, 9,133 arrivals of generations 17 and 18): first-boss kills per 100 are Aeonglass 18, Queen 25 to 26, **Test Subject 3**. A Test Subject as the second boss is as bad: wins when it is second: 2 of 248 arrivals, against 12 of 122 with the Queen second and 10 of 154 with Aeonglass second. Two runs in three meet it (first or second boss). **So the Act 3 wall is one boss; the fraction is wrong only because of it.**

**One replay on the copy confirms it** (gen 18's fight-v3 on one of those seeds, one process, CPU path, 31 s; it reproduced the judged run exactly: floor 48, death, same bar): at each decision of the floor 48 fight the Test Subject had 111 health, fell 90, 69, 57, 41, 27, 8, then **0 (the bar reads 1.0)**, and at the next decision stood at **212 of 212**; the run took that second form to 64 and died. (Tool: `tools/lab/act3_bar_trace.py`, which runs `gen0.play_emu_run` with a hook that reads the enemy slots.)

## Not done, not verified

- Tonight's lab rules: the live judge reads strict as soon as fork main lands (the lab follows main at its next presort). The minimum gain +1.0 now asks for about +40% more Act 3 kills, and the frontier rate (1.5 in 100) still holds B3a for the lineage (strict 2.4). The orchestrator decides whether +1.0 is still the right bar and what to do about `cheap-v3d` (refused by one run).
- The boss of a seed comes from the emulator's act-generation (59 of 60 plain-run saved maps agree; the 60th had a second, 18-room Hive map). The real game's boss draw is not checked here.
- Spireline: the morning report's Act 3 kill uses the same rule; tonight's real-game rows have incomplete room strings, so they are read by floor cuts plus the lost-fight veto.

## Repeat it

```
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/lab/ledger_strict.py --agent D:/spireline/referee/agent --out ledger-strict.tsv --generations gens.tsv
D:/spireline/src/sts2/.venv/Scripts/python.exe -I tools/lab/act3_boss_table.py --agent D:/spireline/referee/agent --gens 16 17 18 --sample 20 --lib <fork tree>/out
D:/spireline/src/sts2/.venv/Scripts/python.exe rl/gen0.py rejudge --cand <agent>/gen18/candidate-cheap-v3d --base <agent>/gen17/candidate-cheap-v2 --seeds-file <lab>/seeds/E18-2026-11-18-r2.json --pool-block E18-2026-11-18-r1 --agent-root <agent> --review-guard --keep-rule v3 --note x --out DIR
```
(run from the fork tree after landing; the other two dry runs use the block r3 and E17-2026-11-15 seed files.)
