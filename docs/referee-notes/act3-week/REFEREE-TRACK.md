# Lane 21: why the referee loses its place at the Act 3 bosses

Written 2026-11-24 by lane 21 (Opus 5.5). Fork `main` `f98caf6c`. Words once: the *referee* plays the real game and our *copy* side by side; it *loses its place* when the copy stops matching the game (a *loss*: a divergence record that was not re-anchored), and a fixed *stand-in* then plays the real game until the next *re-anchor* (the copy put back on the game's record), which today happens only at a fight's first decision or a map choice. An *arrival* is a run that reached the first Act 3 boss (floor 48). Handed off at 300k tokens of context (COMMON rule): the two larger fixes below are specified, not built.

## The table (from the rows and divergence records; the game logs are gone)

Lost arrivals as the stop-rule reader counts them (`lost` set and not past the boss): **95 of 348** on 11-20 (generation 20, after lane 10), **106 of 292** on 11-19 (before). Each row is placed by the loss in force at the first Act 3 boss (each loss lasts to the end of its not-ranked span):

| group | what happened | 11-20 | 11-19 | whose fault |
|---|---|---|---|---|
| A | lost **inside the boss fight** | **78** (Aeonglass 28, Queen 28, Test Subject 22) | 98 | below |
| A1 | ordinary copy differences: enemy health 27, hand 26, hand and health 6, player health 4 | 63 | 34 | the copy (engine), mostly |
| A2 | the game's player had nothing left to play, the game ended the turn **without asking**; the copy still had a playable card and stayed a turn behind | 10 (Queen 6) | 46 (Test Subject 44) | **the referee**: it infers the game's unasked End Turns from the copy's own legal list |
| A3 | the copy refused the game's step (a cost after Snecko Oil, a generated card the copy has no label for) | 3 | 4 | copy / mapping gap |
| A4 | the copy's fight ended while the game's went on (`phase:5/6`) | 2 | 1 (and 2 others: relics, potions) | the copy |
| A5 | lane 10's potion at no target | 0 | 11 | fixed by `dbac8428` |
| B | lost **before** the boss and never recovered (the stand-in played the boss) | **10** | 3 | |
| B1 | the game's deck passed 64 cards (Reflections' Shatter doubles it); the copy's view reads 64, every later re-anchor failed on `.deck` | 9 | 2 | **the referee** (fixed) |
| C | **the player did play the first boss**; the loss came at the second boss, or was recovered before the first | **7** | 5 | **the reader**: a lost row is read by the *first* loss of the whole run |

The 253 tracked arrivals (11-20): 248 never lost at the boss and 5 lost rows the reader already credited; no row was lost in the first boss and recovered at the second.

**Lane 10's question.** Its two fixes worked: their signatures fell from 55 of 98 in-boss losses to 1 of 78. Its estimate missed because other mechanisms dominate: ordinary in-fight copy differences rose from 34 to 63 (12 to 18 in 100 arrivals), partly because Test Subject fights now go past the first form and meet them (Test Subject A1 10 of 96 to 17 of 111), partly a rise at the Queen and Aeonglass (in-boss losses 30 of 196 to 56 of 237, about 2 SE; the records do not say why: generation 20's decks, or chance). Lane 10's second fault was one case of A2, which goes on (Queen: Chains of Binding stops plays in the game, not in the copy). In the whole 11-20 block A2 is 251 of the 1,459 loss records, the most common single loss.

**The stand-in is not hopeless:** 18 of the 78 A rows and 3 of the 10 B rows went past the boss under it; the reader credits none of them (correctly: not our player).

**The honest 11-20 reading** (reader fixed for C, nothing else): passes 68 of 348 arrivals = **19.5 in 100** (was 17.5); tracked arrivals 260, of which our player passed 68 = 26.2 in 100 (was 61 of 253, 24.1).

## What landed (fork main `13ca1f45` and `f98caf6c`, Python only; full suite 6,625 tests, 0 new failures against the 60 known; base 6,614, 0 new)

1. **The copy's deck is compared whole** (`referee/lockstep.py` `EmuLock._deck_view`): at the observation's 64-card limit the deck is read from the run's state list 0 (when its length is the run's own deck count; a card a Thieving Hopper holds keeps the old reading). Covers B1: 9 of 95. Tests `test_lockstep_deck_view.py` (5, one on the native library with a 70-card deck).
2. **Record fields for the 11-26/27 block** (`Lockstep._boss_tally`, `_resume`): `stats.boss_fights` = per boss fight {act, floor, first decision, decisions, stand_in, first_stand_in}: a boss fight is our player's when `stand_in` is 0. A recovered loss record carries `resumed_at` {decision, floor, plan}. Tests `test_lockstep_track.py` (6).

## For the orchestrator (not done here)

- **The reader** (Spireline `tools/strict_rows.py`, not this lane's folder): credit a boss when `stats.boss_fights` has its fight with `stand_in` 0 (the floor rule as now); for older rows use the loss intervals (`classify.py` here), not `first_loss`. Covers C: 7 of 95.
- **Fix c, specified (driver + referee, about a day for a Sonnet or Opus lane):** the driver reports the lone actions it took without asking. `Env.Decide` with n == 1 in a fight kind appends [kind, label] to a list sent with the next asked decision (`"unasked"`) and the end message. `EmuLock._auto_combat` then steps the copy's End Turn exactly as often as the game took one, takes the copy's other lone actions as now, and never a lone End Turn the game did not take (the agent then answers from the copy's own list). Without the key (old driver) as now. Covers A2: 10 of 95 (and about 250 losses a block elsewhere). Tests: a pure helper in `driver.Tests`; `LoneEndTurnTests`-style fakes.
- **Fix d, specified (driver + referee, two days, Opus):** re-anchor **inside a fight**, at the very decision a difference is found (or the next fight decision after a refused step). The driver answers a new command `{"cmd":"anchor_state"}` with the open decision's hidden state (`AnchorStateOf`: draw order, streams, deck and relic holdings) without re-sending the decision (an old driver answers `bad_action` and re-sends: read and drop it). `play_run` hands `GameEnv.anchor_state` to the lockstep; the hidden state goes to `EmuLock.take_anchor_state` only (the firewall as now; the search resamples). Plan `mid_fight` = `_anchor_fight(obs)` with the hidden record (the native loader already writes a whole mid-fight snapshot: turn, energy, powers, all four piles, enemies, streams). **It counts only if** after it the views agree, the energy agrees, the second (unranked) comparison is empty and the copy's legal actions are the game's (deduped by card and potion slot); at most 8 a fight; `boss_fights` gains `reanchors`. **What could fool it:** what no snapshot carries stays the copy's (an enemy's move history beyond its next move, per-card changes such as a cost cut or a growing attack, a power's hidden number, this turn's counters); it shows as a later difference and another re-anchor. Covers A1, A2, A3: up to 76 of 95 if re-anchors hold (unverified). Test basis: `FightStartAnchorNativeTests` at round 2 with a perturbed record. `test_no_reanchor_mid_fight` in `test_lockstep.py` states today's rule and must change with it.
- **For the emulator lane** (copy faults seen here, records only): enemy health after attacks at Aeonglass (16) and the Queen (6); hands after draw and generate effects (26); Chains of Binding timing at the Queen (hidden powers a turn apart); Snecko Oil costs; the copy ending a fight the game continues (6 with C). The 2026-11-20 engine commit `d3daa7d8` made no aimed card legal with no enemy to hit; no engine branch from this lane.

## What the 11-26/27 block should show (generation 21, about 350 arrivals; one block reads to about plus or minus 4.5 in 100 at 2 SE)

| landed by the block | lost-track arrivals per 100 (11-20 basis 27.3) |
|---|---|
| this lane only (deck), reader unchanged | about **24.7** |
| this lane and the reader change | about **22.7** |
| and fix c | about **20** |
| and fix d, if its re-anchors hold | about **3 to 8** (only A4 and failed re-anchors left) |

Checks that need no estimate: no loss record whose `.deck` difference has the game's deck above 64 (11-20: 18 records); every arrival row carries `stats.boss_fights`; `reanchor_fail_reasons` without `diff:.deck` after a deck of 65 or more.

## Not verified

Nothing here ran against the real game (the weekly block is the test). The split of A1 into copy and referee faults rests on the records' fields; a hand difference right after a draw could also be a draw-order stream the re-anchor set wrongly. The Queen and Aeonglass rise is not explained. Fix d's coverage is an upper bound.

## Repeat

```
cd D:/spireline/fork/wt-referee-track   # any fork tree with a published out/
STS2_LIB_PATH=<tree>/out D:/spireline/src/sts2/.venv/Scripts/python.exe -I D:/spireline/referee/backlog/act3-week/referee-track/lost_rows.py D:/spireline/referee/LAB/nightly/2026-11-20T1904/g20 <out>/g20-arrivals.jsonl
D:/spireline/venv-gpu/Scripts/python.exe -I .../referee-track/classify.py <block> <out>/g20-arrivals.jsonl <out>/g20-class.jsonl
D:/spireline/venv-gpu/Scripts/python.exe -I .../referee-track/table.py <block> <out>/g20-class.jsonl     # the table
D:/spireline/venv-gpu/Scripts/python.exe -I .../referee-track/xtab.py <out>/g20-class.jsonl               # passes by group
D:/spireline/venv-gpu/Scripts/python.exe -I .../referee-track/behind2.py <block> <out>/g20-class.jsonl    # A2 in the whole block
D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p "test_lockstep_*.py"
```

# Lane 22: the referee keeps its place inside a boss fight (fixes c and d)

Written 2026-11-24 05:30Z by lane 22 (Opus 5.5). Both fixes landed on fork main and are pushed: **fix c `09cea0a1`**, **fix d `6eeab4bd`** (driver and referee code, Python and the driver's C#; no engine change, no engine branch). Words once: the *driver* is our program inside the real game; it asks the referee only when two or more actions are legal and takes a lone one itself (*unasked*). The *second comparison* is the unranked check of block and powers that runs beside the ranked one.

## What landed

**Fix c (group A2: 10 of the 95 lost arrivals; about 250 loss records a block elsewhere).** The driver now tells the referee which fight actions it took without asking: every fight question carries `unasked`, a list of [kind, action] (empty when nothing was taken), and so does the run's end message. The copy then takes its End Turn exactly as often as the game took one, also when the copy still had a card it could play (the A2 case: the game's player had nothing playable, the copy did, and the copy fell a turn behind). The copy never takes a lone End Turn the game did not take; its other lone actions (one card on a fight card screen) are taken as before. A driver without the key leaves everything as it was. The record keeps the game's list (`ref_unasked`); a row's `stats.unasked` counts the game's unasked End Turns (`game_end_turns`), the copy's steps for them (`stepped`), those taken while the copy had a choice (`stepped_with_choice`: the A2 cases now followed) and the copy's lone End Turns held back (`held_lone_end`).

**Fix d (groups A1, A2, A3: up to 76 of 95).** The referee re-anchors the copy *inside* a fight (plan `mid_fight`): at the very fight decision where a difference is found, or, while lost, at the next fight decision when the loss began in this fight (a refused step). The driver answers a new command, `anchor_state`, with the open decision's hidden state (the draw pile in order, the random streams' counters, the deck's and relics' holdings) without sending the decision again; it answers only in a run whose reset asked for the hidden state, and a driver that does not know the command answers `bad_action` and re-sends the decision, which the referee reads and drops (and stops asking that process). The hidden state goes to the copy's re-anchor only, never to a record, the stand-in or the search (the search re-rolls hidden things from its own copy, as before). The copy is re-anchored only in its own fight on the game's floor with no card screen open; the record of the decision (hand, piles, energy, block, powers, enemies, the round) and the potion belt are written over it by the native loader that fight starts already use.

**A mid-fight re-anchor counts only if, right after it:** (1) the views agree (the same comparison as everywhere); (2) the copy's energy is the game's; (3) the second comparison finds nothing (block and powers of the player and every enemy); (4) the copy's legal actions are the game's, one key per card, End Turn, one per potion (hand positions, targets and slots folded together). At most 8 tries a fight, held or not. A difference in the deck, the relics or the floor is not tried (a fight's record cannot put it right) and a loss from before the fight waits for the next fight start or room entry, as before. A failed try leaves the row as a loss is recorded today (`reanchored` false, the stand-in plays on); the record adds `reanchor_plan: "mid_fight"` and `reanchor` {try, ok, why, with, moves}, and a recovered loss lists its tries in `mid_fight_tries`. `stats.boss_fights` entries gain `reanchors` (held) and `reanchor_failed`; the row's stats gain `mid_fight_hidden` (tries that had the game's hidden state) and `mid_fight_capped`. `SPIRELINE_MID_FIGHT=0` turns fix d off without a code change.

Tests: driver 25 (21 before fix d: `UnaskedTests` 6, `ReplyTests` 4 new); Python `test_lockstep_unasked.py` 11, `test_lockstep_mid_fight.py` 25 (3 on the native library: a copy at round 2 of its own fight, the game's record perturbed, the draw pile in another order; held, the state is the record's, and a legal list the copy lacks is refused). `test_no_reanchor_mid_fight` was rewritten as the new rule; every firewall test is unchanged and passes. Full Python suite: base `f98caf6c` 6,682 tests, fix c 6,693, fix d 6,718; 0 new failures against the 60 known each time (one flake that passes alone). `dotnet build` of the driver: 0 warnings, 0 errors.

## What could fool fix d, and how the block shows it

The loader writes what the record shows; what no snapshot carries stays the copy's own: an enemy's move history beyond its next move (where its AI is not a fixed cycle the loader cannot set the next move: the try's `moves` reads `unknown`), per-card changes (a cost cut, Snecko Oil's costs, a growing attack: the copy keeps its own copy of each card it still holds), a power's hidden second number, this turn's counters (cards and attacks played this turn). None of these is in the four conditions, so a re-anchor can hold and the copy part again a step or a turn later; that shows as another `mid_fight` record in the same fight, with `acted` and `turn` saying where. Read the block by: `reanchor_by_plan` `mid_fight:ok` against `mid_fight:failed`; `reanchor_fail_reasons` `mid_fight:<why>` (energy, hidden:<field>, legal:+/-<key>, diff:<field>, not_in_fight, floor, selection_open, anchor:<loader message>); the count of `mid_fight` records per boss fight with `moves` and `with`; `stats.boss_fights[].reanchors`.

Checks that need no estimate: every row carries `stats.unasked` (if not, the block ran an old driver and fix c did nothing); rows with mid-fight tries have `mid_fight_hidden` above 0 (if 0, the game's driver did not know the command and every re-anchor used the observation alone); A2's signature (a loss right after an unasked End Turn with the copy still holding a playable card) falls toward 0.

## What the 11-26/27 block should show (lane 21's table, restated)

Lost-track arrivals at the first Act 3 boss per 100 (11-20 basis 27.3): the deck fix only about 24.7; with the reader change about 22.7; with fix c about 20; with fix d, if its re-anchors hold, about 3 to 8 (A4, the copy's fight ending first, and failed re-anchors left). One block reads to about 4.5 in 100 at 2 SE. Fix d's figure is an upper bound: it assumes the four conditions hold after most tries.

## For the orchestrator

- Nothing in `LAB/jobs.json` needs changing: the lab's presort builds the driver from the tree (`build-driver`) and the real arm installs it. Check before 11-27 19:00Z that the lab tree is at `6eeab4bd` or later and its driver build is fresh.
- Expect more divergence records per block: a held mid-fight re-anchor lets later differences in the same fight be recorded, where before the fight was dark after the first. `reanchor_failed` also grows (up to 8 tries a fight); the morning report's "re-anchors (failed)" line changes meaning accordingly.
- The reader: a boss fight re-anchored at the very decision of its difference has `stand_in` 0 and is our player's; one recovered after a refused step has `stand_in` above 0 (the stand-in answered between) and is not, by the strict rule.
- Not done: the two Act 3 bosses have no question between them, so the second boss's first decision is not a fight start; fix d covers it only when the copy already stands on that floor. Treating a floor change between two fight decisions as a fight start is a small follow-up for a later lane.

## Not verified

Nothing ran against the real game (the weekly block is the test). The share of mid-fight tries that hold is unknown: the native tests hold on the copy's own record, perturbed; the game's records carry powers and cards the loader may treat differently. The coverage figures are lane 21's estimates.

## Repeat

```
cd D:/spireline/fork/wt-referee-fix-cd     # or any fork tree at 6eeab4bd or later with a built out/
dotnet build referee/driver/SpirelineReferee.csproj -c Release
dotnet test referee/driver.Tests
D:/spireline/src/sts2/.venv/Scripts/python.exe -m unittest discover -s tests/python -p "test_lockstep_*.py"
TAG=<tag> WTN=<tree folder> FULL=1 bash D:/spireline/logs/gym-loop/bin/gate-py.sh    # the full suite against the 60 known failures
```
