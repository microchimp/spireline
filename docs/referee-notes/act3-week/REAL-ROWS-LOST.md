# Lane 8: reading real-game rows when the referee lost track of the game

Written 2026-11-20 by lane 8 (Sonnet 5.5). Spireline main, commit hash in the report line (tools only; the fork was not touched). Words once: the referee plays the real game and a copy of it side by side; when the copy stops matching the game it has "lost track" (the row's `lost` field), the agent can no longer be asked, and a fixed stand-in plays the rest of that run on the real game. "Beaten" is the strict count of lane 1: the run won or went past the boss's floor (17, 33, 48).

## What changed

The three readers disagreed. The morning report and `boss_entry` treated every `lost` row like a crash (it beats nothing); `weekly_numbers` applied no veto. The first came from the copy arm, where `lost` meant a worker that returned no data; in a real-game row the ending floor and the boss bars come from the game, but everything after the loss was played by the stand-in, not by the agent being measured. New shared rule, `tools/strict_rows.py`: a lost row beats the bosses whose floor is **below** the floor where tracking was lost (the `divergences` entry of `stats.first_loss.decision`, else the last entry before it) and nothing at or after it; no readable loss floor means the old reading (beats nothing), counted as `loss floor unknown` (none in this block). Crash rows and `fight_unfinished` rows as before (by floor). `morning_report.py`, `boss_entry.py` and `weekly_numbers.py` call it; the morning report's `--check` second path has its own copy of the rule. One more fault found on the way: the real game ends a won run with `end: "victory"`, which the morning report's win test did not know (it read 0 wins and failed its own cross-check "real wins = summary.wins", 0 against 2). Fixed in the same place.

Tests: `tests/test_strict_rows.py` (9: lost at 29 counts Act 1 only, lost at 10 nothing, crash nothing, clean above 48 all three, unknown floor, the loss-floor lookup, wins and deadline rows, the readers and the `--check` path agree row by row). Suite 305 passed.

## The block read again (generation 19, 2,000 seeds, 1,997 ended runs, 3 crash rows)

`--check` on the night: **114 figures, 0 mismatches** (was 28 of 100). I added Act 2, Act 3, wins and the lost-row counts to it.

| reading | Act 1 boss | Act 2 boss | first Act 3 boss |
|---|---|---|---|
| old (a lost row beats nothing) | 1,223 = 61.2 per 100 runs, 63.3 per 100 arrivals | 339 = 17.0, 33.0 | 30 = 1.50, 10.3 |
| **new (loss floor)** | **1,435 = 71.9, 74.3** (of 1,932) | **447 = 22.4, 43.5** (of 1,027) | **32 = 1.60, 11.0** (of 292) |
| plain (no veto at all; the first `weekly_numbers` figure) | 1,460 = 73.1, 75.6 | 499 = 25.0, 48.6 | 41 = 2.05, 14.0 |

Copy arm, same night (500 runs, unchanged by the fix): Act 1 369 = 73.8 per 100 runs (75.9 per 100 arrivals), Act 2 129 = 25.8 (48.5), first Act 3 boss 16 = 3.2 (17.0 of 94). Real arm: **wins 2 = 0.10 per 100**, mean floor 30.14 (copy 30.56). `weekly_numbers`: the first Act 3 boss per 100 arrivals goes from 14.0 [10.5, 18.5] to **11.0 [7.9, 15.1]** (41 to 32 of 292); the real arm on the 500 paired seeds from 16.1 to 14.5. Number 5's figure for generation 18's candidate moves 2.70 to 2.67 in 100 (two copy rows whose complete room string puts the boss above floor 48), the gain +1.45 to +1.48 (se 0.37).

**Lost rows: 272 of 1,997 (13.6%); 212 of them changed a boss figure** (they count at least one boss now, none before). Against the plain count 72 of them are credited less (25 fewer Act 1 kills, 52 Act 2, 9 first Act 3 boss): a row lost at floor 45 that the game then carried to floor 49 is not credited with the boss on 48. Loss floors: 60 rows at 17 or lower (nothing credited), 104 on floors 18 to 33, 106 on 34 to 48, 2 above 48.

## Why 19 runs end `fight_unfinished` (diagnosis, no fix here)

- **Rule.** The driver (`referee/driver/RunPlay.cs`, `FightLoop`) ends a fight after `max_actions` actions, default **400**; the nightly's run spec (`referee/envproto.py`, `reset_spec`) sets none (it sets 3,000 decisions for the whole run), and a fight still in progress then ends the run as `fight_unfinished`. A time deadline gives a crash row instead.
- **It does not cut real boss fights short.** 14 of the 19 (12 on floor 48, 2 on 49, all against the Test Subject, all lost rows) show the same answer to the same screen 376 to 394 times in a row (`streak`; none of the other 1,983 ended rows passes 49). The fight began about 400 actions before the run's last decision in each, and the not-ranked span of its divergence record runs to that last decision. A whole run takes about 380 decisions (death rows at floor 48 or above: median 378, maximum 548), so no genuine fight comes near 400.
- **Mechanism (read from the rows and the driver code; not confirmed in a game log, which the block's deletion removed).** When the Test Subject's first form falls no creature is alive until its next move, and the driver then offers enemy-target potions with target -1. In 13 of the 14 runs the move that lost track was exactly that: Vulnerable 5, Weak 4, Potion-Shaped Rock 3, Fire 1, all enemy-target potions; the game kept the potion and its energy, hand and turn did not change (`turn_advanced` false), while the copy spent it. After that the stand-in plays the first card, else the first non-end action; no card is offered without a target, so it picks the same potion every time, the game ignores it, the same decision comes back, and the cap ends the run. The 14th lost track on an End Turn (HP 66 against 69). Other rows whose lost move was a target -1 potion at a Test Subject were all self-target potions (Dexterity, Block, ...), which are fine.
- **Size.** On floor 48, 84 runs saw the first form fall: 72 went on and died in a later form, 12 stalled (2 more stalled against it as the second boss). At most 12 of 292 arrivals could have gone on; at the Test Subject's 2 to 3 passes in 100 that is well under one lost pass, and 14 x 390 wasted decisions are 1.2% of the block's 472,294. The 5 other `fight_unfinished` rows (floors 37 to 46, streaks 4 to 12, four of them not lost) are a different cause I cannot see from the rows.
- **Suggested, for the orchestrator (fork, engine gate):** do not offer an enemy-target potion when no enemy is alive (the `else` branch in `FightLoop`'s potion list); make the stand-in end the turn when its last action left the state unchanged; a `stuck` end reason after about 30 identical answers instead of 400.

## Not done, not verified

- Rows that lost track and then got it back (483 more, `lost` unset) are read plainly; the stand-in played the stretch between. A rule for them needs the span, which the divergence records hold.
- The loss floor rule is conservative by design (a boss on the loss floor itself was played partly by the stand-in); the plain count is above. The orchestrator decides whether the stop rule's baseline of 16 per 100 arrivals needs restating (11.0 on this block).
- The mechanism of the stall is not confirmed in a game log; a replay of one of the 14 seeds with the driver's log would show the refused potion.

## Repeat

```
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/morning_report.py D:/spireline/referee/LAB/nightly/2026-11-19T1103 --check --winlog none
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/weekly_numbers.py --no-write
D:/spireline/spireline/.venv/Scripts/python.exe -m pytest -q tests/test_strict_rows.py
```

## Addendum 2026-11-24 (lane 23, Sonnet 5.5): the reader credits a boss fight our player actually played

Spireline main `7cfd47e` (tools and tests only; the fork was not touched). Words once: *our player* is the agent being measured; the *stand-in* is the fixed player that plays on the real game while the referee has lost its place; an *arrival* is a run that reached the first Act 3 boss (a win, floor 48 or more, or an Act 3 boss bar, as the weekly table counts it); a *lost-track arrival* is an arrival whose boss fight the stand-in answered at least one decision of; a *finished* fight is one our player played to the end, whether it won or died in it.

### The fault and the rule now

Lane 8's reader read a lost row by the first loss of the whole run, so a loss that was recovered before the boss, or a loss at the second Act 3 boss, voided a fight our player had played itself (lane 21: 7 of the 95 lost arrivals of 11-20). A boss now counts as beaten by our player when the run went past it **and** no decision of its fight was answered by the stand-in. Where that is read from, in this order: (1) new rows (fork `f98caf6c`): `stats.boss_fights`, a fight is our player's when its `stand_in` is 0; (2) older rows: the loss intervals of the row's divergence records (the block's `divergences.jsonl` holds the same records; a row without them takes them from the file), each loss lasting to the end of its not-ranked span, and the last loss of a row that ended lost lasting to the run's end; a fight is our player's when no loss covers any of its decisions (a loss that opened inside it, or before it and was never recovered, covers it); (3) rows with neither: the first-loss rule as before, **counted and printed as a fallback** (none in either block: all 279 and 272 lost rows were read from their records). Wins, crash rows, the boss bar and the room-string rules are unchanged. One reader, `tools/strict_rows.py`, for `boss_entry`, `morning_report` and `weekly_numbers`; the morning report's `--check` second path is written again on its own and agrees on 130 figures (was 118), 0 mismatches, on both nights.

### The two blocks read again, first Act 3 boss (counts as "N of M")

| | 11-20 (generation 20, 2,000 seeds) | 11-19 (generation 19, 2,000 seeds) |
|---|---|---|
| passes on all arrivals | **68 of 348 = 19.5 per 100** (before: 61 of 348 = 17.5) | **37 of 292 = 12.7 per 100** (before: 32 of 292 = 11.0) |
| passes on the fights our player finished | **68 of 260 = 26.2 per 100** (before: 61 of 253 = 24.1) | **37 of 191 = 19.4 per 100** (before: 32 of 186 = 17.2) |
| lost-track arrivals | **88 of 348** (21 of them went past the boss under the stand-in and are not credited) | **101 of 292** (4 of them went past under the stand-in) |
| Aeonglass: passes / finished / lost-track | 25 of 117 / 25 of 85 / 32 of 117 | 19 of 104 / 19 of 87 / 17 of 104 |
| the Queen: passes / finished / lost-track | 27 of 120 / 27 of 92 / 28 of 120 | 16 of 92 / 16 of 77 / 15 of 92 |
| the Test Subject: passes / finished / lost-track | 16 of 111 / 16 of 83 / 28 of 111 | 2 of 96 / 2 of 27 / 69 of 96 |

"Before" is the lane 8 reader (first loss), "finished" before is the arrivals it did not count as lost. Per boss the three bosses add up to the totals in each column. Boss names come from lane 21's seed-to-boss table (`referee-track/boss_ids.json`). The row-by-row placement agrees with lane 21's own classification on both blocks (11-20: 78 in-boss and 10 earlier losses not credited, 12 later-loss rows and 248 never-lost rows played; 11-19: 98, 3, 7, 184). The morning report's own "Act 3 boss reached / killed" lines still count only rows that hold an Act 3 boss bar (11-20: 63 of 343; 11-19: 37 of 292); five rows of 11-20 went past floor 48 with no Act 3 bar and are arrivals and passes in the stop rule's reading above (the report now prints both).

### Rows changed

First Act 3 boss: **7 rows on 11-20 and 5 on 11-19**, every one credited now and none taken away: a loss recovered before the boss (lost earlier, put back on the game's record at a fight start or map choice) and the last loss at the second boss (floor 49, or 51 on a longer map). Same rule on the Act 1 and Act 2 bosses: 11-20 Act 1 1,413 to 1,417 (18 credited now, 14 no longer: 12 with a loss inside the boss's own fight that was recovered after it, 2 unclear), Act 2 541 to 572 (44 and 13: 10 and 3); 11-19 Act 1 1,435 to 1,438, Act 2 447 to 476. In all, 81 rows of 11-20 and 72 of 11-19 changed credit for some boss (74 and 67 of them for Acts 1 and 2 only). `--check` lists them with the reason.

### Not verified

- No row carrying `stats.boss_fights` exists yet (the fork writes it from the 11-26/27 block on): the new-row path ran on made-up rows only. First real check: every arrival row has the field, and `strict_rows.py --check` on that block reads its lost rows from `boss_fights`.
- Old rows, Acts 1 and 2: a loss that was recovered before the boss can only have run into the boss fight if it lasted at least as many decisions as there are floors between and the run had a failed re-anchor; where both hold the reading is "unclear" and counts as not our player's (11 readings on 11-20, 5 on 11-19, none at the first Act 3 boss). For the first Act 3 boss a recovered loss never covers it, because nothing re-anchors between the two Act 3 bosses (they have no question between them in the lockstep's record).
- Longer Act 3 maps (about 2 in 100 seeds): the first boss's floor is read from the records (a fight on 48 that is no boss's moves it one floor up); a row with no record on 48 reads the boss on 48, and the plain "floor above 48" rule counts a run that died at the real first boss one floor early, as before.
- The block's `divergences.jsonl` equals the rows' own records on 11-20 (same decisions for 1,994 of 1,994 rows), so the rows' own records are read first and the file only fills a row that has none.

### Repeat

```
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/strict_rows.py --check D:/spireline/referee/LAB/nightly/2026-11-20T1904/g20 --bosses D:/spireline/referee/backlog/act3-week/referee-track/boss_ids.json --list
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/strict_rows.py --check D:/spireline/referee/LAB/nightly/2026-11-19T1103/g19 --bosses D:/spireline/referee/backlog/act3-week/referee-track/boss_ids.json
D:/spireline/spireline/.venv/Scripts/python.exe -I tools/morning_report.py D:/spireline/referee/LAB/nightly/2026-11-20T1904 --check --winlog none
D:/spireline/spireline/.venv/Scripts/python.exe -m pytest -q    # 327 passed
```
