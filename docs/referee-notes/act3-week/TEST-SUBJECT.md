# Lane 5: the Test Subject in the fight exam and the practice

Written 2026-11-19 by lane 5 (Sonnet 5.5). Landed on fork main as `4f2757a2` (three commits; Python-only gate: 401 selected tests, 0 new failures; summary in `D:/spireline/logs/fork-tests/4f2757a2.txt`). Branch `feat/test-subject`, worktree `D:/spireline/fork/wt-test-subject`. Words once: an **arrival** is a run that began the fight; **went past** means the run got through it (a first boss: it went on; the second boss: it won the run); the **human bar** is the share of human runs (Ironclad, Ascension 10, the corpus's four training fifths, never the exam fifth) that went past the same boss; an **exam cell** is one boss in one turn (`act3-boss1-80`: the Test Subject as the first Act 3 boss, `act3-boss2-80`: as the second).

**The smoke was not run** (the lab's training job held the machine from 03:46Z and extended itself past the 10:30Z limit; the orchestrator withdrew it). It is covered by `TEST-SUBJECT-exam.sh` after the block. Nothing below is a kill rate of the champion on these cells.

## 1. The per-boss table (task 1)

Humans: 11,961 usable runs of the training fifths. The corpus names the boss in every floor's room record, so nothing is guessed. Ours: the judged arms of generations 16 to 18 (lane 1, strict reading) and the plain-run store of generations 17 and 18 (the fight won). Per 100 arrivals.

| first Act 3 boss | human runs | humans past (95% interval) | ours, judged arms | ours, plain-run store |
|---|---|---|---|---|
| **Test Subject** | 1,001 | **70.4** (67.5 to 73.2) | **1.8** (18 of 989) | **2.8** (87 of 3,077) |
| Queen | 983 | 74.1 (71.2 to 76.7) | 26.9 (287 of 1,068) | 25.4 (799 of 3,142) |
| Aeonglass | 1,030 | 72.1 (69.3 to 74.8) | 20.5 (219 of 1,067) | 18.0 (534 of 2,962) |

Second boss (won the run): humans Test Subject 63.2 (761 runs), Queen 65.9 (687), Aeonglass 58.5 (723); ours (store) Test Subject 3 of 688 (0.4), Queen 30 of 323 (9.3), Aeonglass 26 of 409 (6.4). A cross-check on the newer corpus copy (14,725 runs) gives 69.7, 73.0 and 70.5 for the three first bosses. No human cell is under 20 runs.

Read it: people find the three bosses equally hard (70 to 74 in 100 get past); we pass the Queen and Aeonglass at 18 to 27 and the Test Subject at 2 to 3. It is one boss, not a hard act.

## 2. Why the fight kills us (task 2; from the records and our fork's code)

- **We arrive in much the same shape.** Health going in: ours 82% of max (90), humans 86% (87). Deck size 33 for both. Differences: potions held 1.0 against about 2.1, relics 14 against 18, and the deck's mix: ours 19.3 attacks, 9.7 skills, 2.4 powers; humans' 13.1, 14.3, 3.8 (`act3_starts.py decks`).
- **The 87 of ours that won the fight** (plain-run store) against the 2,990 that lost: health going in 92% against 82%, potions 1.23 against 1.00, relics 15.0 against 13.9, the same deck mix (skills 9.0 and 9.7, attacks 19.6 and 19.2). Humans who passed against those who died at it: 88.6% against 80.0% health, 2.26 against 1.87 potions, 12.6 against 14.1 attacks, 4.0 against 3.4 powers. So the ones who get past arrive about ten points healthier with a potion in hand; the human winners also hold fewer attacks and more powers, ours do not differ in deck.
- **The boss (the copy's code, Ascension 10).** Three forms of 111, 212 and 313 health (636 in all): it stands up again when a form falls, and the revive turn is a free turn for us. It gains 3 Strength, kept through every form, for each Skill we play. Form one alternates Bite 22 and Skull Bash 16 (with Vulnerable); form two is Multi-Claw, 11 a hit, one more hit each turn (3, 4, 5, ...); form three cycles Lacerate (11 three times), Big Pounce 45 and Burning Growl (Burns into our discard, 3 more Strength), and it is untouchable on every other turn of our play. Damage per turn therefore climbs fast: with 10 Strength a claw is 21, so the second form's first turn costs 63 and its third 105 before block.
- **We die early.** Fight wall seconds in the store (the same search budget a decision, so about proportional to length): Test Subject fights we lose last 15.6 s on average, Queen fights we lose 52.7 s; the ones we win at the Test Subject 27.3 s. Lane 1's replayed fight fell in form one after seven decisions and died at 64 of 212 in form two.
- **Most common cause of death** (a 30-second probe of the exam player, 5 Test Subject games, four human positions and one of ours; anecdote, not a result): all five lost in form two, within 4 to 6 turns, to Multi-Claw (11 times 3 or 4), the boss already at 8 to 12 Strength, 56 to 65% of that form's health left.
- **One line:** a three-bar boss whose hits grow every turn; we arrive as healthy as the humans do with fewer potions and attack-heavy decks, and the fight brain, which has never practised an Act 3 start, is gone in the second form after a few turns where humans lose it in 3 of 10. Not verified: whether anything it was trained on held this fight (the practice did not).

## 3. What was built (tasks 3, 4; all on fork main)

- `rl/act3_starts.py` (new): one corpus pass (`scan`, 90 s to 3 min, the exam fifth excluded before anything is read) gives the human bar and 4,325 Act 3 boss openings rebuilt from each human's own record, with the human's result (the second boss is survived only by winning the run); `human` deals them on the copy (old engine, 4 processes, about a minute, none refused); `own` builds our arrivals from the stores (10,600 in four minutes, one process); `table` and `decks` print the aggregates. A human run's id never reaches a file: the start's run is a salted hash. `human_starts.rebuild_run` takes `acts` and `kinds` (Acts 1 and 2 as before).
- `fight_exam.py add-act3`: the exam's Act 3 cells as a third file (`starts-act3.*`, `act3-meta.json`); quota weighted to where our runs die (Test Subject cells 80 + 40 human, 60 + 30 ours; Queen and Aeonglass 32 and 20 human, 30 and 20 ours; 414 starts), clean runs first, one start a run, the AI exam's and the Acts 1 and 2 human stratum's files checked unchanged, the runs added to `exclude_runs.json`. Staged in `test-subject/exam-act3/`: all 224 human starts are clean, and 158 of them (70.5%) went past, matching the bar. `play`, `compare` and `report` of `fight_exam.py` do not play it (`--stratum all` is as before).
- `rl/act3_exam.py`: plays the cells with the champion's fight network at its own boss budget (`a3-v1@h1e4b16`), old engine, CPU prior, four draws a start; report: kills by side and cell with intervals, the champion against the human on the same starts (paired, bootstrap over starts), and the Test Subject's forms from per-decision traces (turns, health lost a turn, the boss's Strength, what killed).
- **Practice stratum, off by default** (`practice_mix.py`): `mix.json` `{"act3": {"share": 0.1, "human_share": 0.5, "own_encounters": [80]}}`; with share 0 nothing is read and draws are the same to the byte (tested). Human pool after the exam's runs are dropped: 3,915 starts; ours: 3,660 Test Subject arrivals. One line in `gym_loop.py` (`MEAN_X16_S` has `act3-boss: 120`, a guess).
- Tests: `tests/python/test_act3_starts.py`, 45, on synthetic runs and a fixture; the real copy deals a Test Subject opening (111 of 111) in one of them.

## 4. The full exam run and the flips

`TEST-SUBJECT-exam.sh` (this folder): builds what is missing (the staged files are there), then plays every cell, four draws, 12 processes, BelowNormal, wall limit 3 h, QUIET line `act3-exam` with the Windows PID, refuses under another's line, the night, PAUSE, HALT or main.lock, resumable, report at the end (`test-subject/exam-act3/report.txt`). 414 starts times 4 draws is 1,656 games; the six probe games took 7 to 24 s each, so about 7 core-hours, under an hour on 12 processes (estimate, unmeasured at that scale). The smoke is the same script with `PROCS=4 DRAWS=2 TAKE=act3-boss1-80=40,act3-boss1-78=20,act3-boss1-73=20 WALL_HOURS=0.45` (a subset of the full run; it needs a tree with a current `out/`: the default `wt-test-subject` has one, the main checkout's is stale).
To put the cells in the live exam and switch the practice on (orchestrator; rehearsed on a copy of the live exam's files: same picks): `python rl/fight_exam.py add-act3 --exam-dir D:/spireline/referee/gym-loop/exam --starts-dir D:/spireline/referee/backlog/act3-week/test-subject`; copy `human-starts-act3.*`, `human-outcomes-act3.json`, `own-starts-act3.*` into `gym-loop/starts/`; then `starts/mix.json` `act3.share`. Do the first two before the third.

## 5. Not done, not verified

Smoke (above). The champion's kill rate on any Act 3 cell. Fidelity of the rebuilt openings (no relic counters or in-fight card bonuses; potions an event gave are missing; the full run's own-position kill rate against the store's 2.8 is the test). Old engine only. `loop_played` is frozen at the scan (03:16Z). One of the gate's first runs failed `test_practice_mix`'s segment test, whose draws are seeded by the clock; it fails the same at that second on main before this change.

## 6. Repeat

`D:/spireline/src/sts2/.venv/Scripts/python.exe -I rl/act3_starts.py scan|table|decks --out D:/spireline/referee/backlog/act3-week/test-subject` (from the fork tree); tests: `STS2_REQUIRE_AOT=1 D:/spireline/src/sts2/.venv/Scripts/python.exe -I -m unittest discover -s tests/python -p test_act3_starts.py`; gate: `test-subject/lane5-gate.sh`.
