# Lane 6b: five honest weekly numbers, the HANDOFF split, the one-page scoreboard

Written 2026-11-19T02:10Z by lane 6b (Sonnet 5.5). Spireline `main`: `7a91139` (the tools, 41 new tests) and `9bbc51c` (a reading note, a skip for a block just started, 1 more test). Whole suite 294 passed, 0 failed; summaries in `D:/spireline/logs/spireline-tests/7a91139.txt` and `9bbc51c.txt`. Nothing heavy ran; `tools/morning_report.py` and `tools/boss_entry.py` untouched; nothing written outside Spireline and this memo.

Words once: **the copy** is our rebuilt game; **the real game** is the game itself; a **real block** is about 2,000 real runs of one player; an **arrival** is a run that reaches the first Act 3 boss (floor 48); **strict** means a run is past that boss only if it won or ended above floor 48.

## 1. `tools/weekly_numbers.py`

One command prints the table and writes `weekly-numbers-<date>.json` and `.md` (`--out-dir`, default `referee/backlog/weekly`; `--no-write` prints only). Every rate has n and a 95% interval; what the files do not hold prints "no data". Output holds relative paths and no seed. Checked against analyst B's counts on the real folders: 62 real arrivals ever at the first Act 3 boss, 2 past it; generation 18 past it 52 of 2,000 (2.6 in 100), +0.35 over generation 17.

The numbers for the champion (generation 18), as printed at 02:04Z:

| # | number | now | n | humans |
|---|---|---|---|---|
| 1 | wins per 100, real game | **no data for generation 18.** Newest block (generation 13, 2026-11-06, 12.7 days old): 0.00 (0.00 to 0.19) | 2,000 | 11.3 (8.0 counting quits) |
| 2 | first Act 3 boss passed, strict | generation 13 real: 0.00 per 100 runs (0.00 to 0.19), 0.0 per 100 arrivals (0.0 to 14.9). On the 200 seeds the copy also holds: real 0 of 200 (0 arrivals), copy 0 of 200 (1 arrival) | 2,000 real, 22 arrivals | 18.2 per 100 runs, 72.7 per 100 arrivals |
| 3 | copy honesty | both arms end in the same act in 67.5 of 100 pairs (60.7 to 73.6); copy minus real +1.15 floors (se 0.65). **Alarm** against the 11-06 block (generation 11): Act 1 floors +2.74, Act 1 share -12.6 points, Act 2 share -2.0 | 200 pairs | |
| 4 | distance to winning humans | **no exam of generation 18.** Newest, generation 14 (2026-11-12): 22.0 floors behind on seeds a human won (20.8 to 23.3); 0 of those 200 seeds won (0 of 400 draws) | 200 seeds | won all of them |
| 5 | champion against last week's | generation 18 against 17, 2,000 pairs, **the block it was promoted on (not fresh)**: passed 2.60 against 2.35 in 100, +0.25 (se 0.44); wins 0.10 against 0.00; the new rule's measure (passes plus wins) +0.35 (se 0.46) | 2,000 pairs | |

Stop rule (D68): 15.8 in 100 arrivals past the first Act 3 boss now (not fresh; 52 of 330), started at 16, target 30; wins 0.10 in 100, target 0.5; fresh pairs 0 of 4,000; real block of the champion: not yet; 13.9 days left.

Reading it:
- Numbers 1, 2 (real half) and 4 have no champion reading today. Tonight's block fills 1 to 3; the seed exam of generation 18 (B's option 4) fills 4 with no code change.
- Number 5 has no fresh pairs, so +0.25 is the best of several candidates and still level. A fresh replay must write its arms to `referee/agent/gen18/candidate-fight-v3/arms/<block>-a3-v1/` (the base's under `gen17/candidate-cheap-v2/arms/`); the tool then pools them and marks them fresh. Arms stored elsewhere are not seen.
- Number 3's two-point alarm is inside the noise: at 200 pairs a one-act share moves 4 to 5 points by chance (the -12.6 is "within its noise of 12.7"; the Act 1 floor move is beyond its 2.0, but that block is another player). The tool prints each move beside its noise and flags past two points regardless. Per-act rows are conditioned on where the real arm ended (an early real end is a low draw, so the copy reads higher there); only the all-runs floor difference is a plain bias. The arms end in the same act in only 67.5 of 100 pairs because they diverge at the first differing move: that is the baseline for the next block, not a defect.

## 2. `tools/handoff_split.py`

`python tools/handoff_split.py --handoff D:/spireline/referee/backlog/HANDOFF.md --archive D:/spireline/referee/backlog/HANDOFF-archive.md --keep-days 7 --dry-run` (dry run is the default). `--apply` writes the backup `HANDOFF.md.<UTC>.bak`, appends the archive, then replaces the live file, and writes nothing if the file changed while it ran. A block is a stamped line (`- *2026-11-18 12:47Z`, `- *2026-10-28T15:55Z`, date-only counts as the end of its day, or `- 2026-10-28T07:05Z`) plus its indented lines, tables, blanks and undated sub-bullets; old blocks move in file order under one dated heading with their section named. Alerts block, headers and introductions stay; CRLF kept, zero bare LF.

On a copy of today's HANDOFF (189,000 words, 568 stamped blocks; I did not run `--apply` on the real file):
- `--keep-days 7`: 487 blocks and 156,000 words move; the live page is still 33,000 words, because the last 7 days hold 81 blocks of about 320 words each. Three pages needs short lane lines.
- `--keep-days 2 --max-words 2500 --archive-intros --archive-sections "^0\.|^[1-9]"`: live page 2,613 words (the alerts block 1,490, three blocks, the title); 0 original lines missing from live plus archive, 100% CRLF. The alerts block alone is about three pages: shorten it by hand. That regex also archives plan sections 1 to 10; leave them out to keep them.

## 3. `docs/paper/SCOREBOARD-TEMPLATE.md`

The Tuesday page on one screen: the five numbers in plain words, the stop rule's distance, the landings (one line each), what waits on the owner. Its comment holds the commands: `tools/weekly_numbers.py --out-dir D:/spireline/referee/backlog/weekly`, then `tools/weekly_numbers.py --fill docs/paper/SCOREBOARD-TEMPLATE.md --no-write > .../scoreboard-<date>.md` (`{{key.path}}` is a JSON value, `{{key.path:2}}` rounds, a missing value prints "no data"), then `git log` of the fork and Spireline since last Tuesday 21:00Z for the landings and a grep of HANDOFF's alerts for the owner's items. A test fills the real template on a made-up lab and fails if a token stops naming a key. The paper is not edited.

## Not done, not verified

- Tonight's block has not happened: choosing `g18` and `g18-emu` in a `LAB/nightly/YYYY-MM-DDTHHMM` folder follows the 11-06 layout and is unverified on a new one. A running block is read from its `runs.jsonl` and flagged "summary.json not written yet".
- Seed exams live at `referee/seed-exam/<date>-gen<N>/summary.json`: generations 13 and 14 exist, none for 18 (nothing under `referee/agent/*/` or `referee/backlog/`; the tool searches those too).
- The human figures (11.3, 8.0, 18.2, 72.7) are constants from the fork's `docs/reference/codex-a10-ironclad.md`.
- Applying the split to the real HANDOFF is the orchestrator's; I changed nothing in the lab.

## Commands to repeat

```
cd D:/spireline/spireline
.venv/Scripts/python.exe -I tools/weekly_numbers.py --no-write
.venv/Scripts/python.exe -I tools/weekly_numbers.py --fill docs/paper/SCOREBOARD-TEMPLATE.md --no-write
.venv/Scripts/python.exe -I tools/handoff_split.py --handoff D:/spireline/referee/backlog/HANDOFF.md --archive D:/spireline/referee/backlog/HANDOFF-archive.md --keep-days 7 --dry-run
.venv/Scripts/python.exe -m pytest tests/test_weekly_numbers.py tests/test_handoff_split.py -q
```
