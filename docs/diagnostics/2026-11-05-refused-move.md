# "The engine refused action N in phase 5": the refused move, 2026-11-05

On the nightly real-game arm about one run in 530 ended as a crash row with `RuntimeError: the engine refused action N in
phase 5` (12 rows in 6,404 runs on the nights of 2026-10-30 to 11-05). This note says who refused what, why, how to make it
happen on the copy alone, and what was changed. Times are Z. Nothing here ran the game; the evidence is the nights' own rows,
their game-log copies and the copy (the emulator).

## What happens

- **Who refuses: our copy, not the game.** The message is raised by the fork's `RunSession._step`
  (`rl/run_train/engine.py`), the copy's run engine, when its native step returns non-zero. The lockstep
  (`referee/lockstep.py`, `EmuLock`) steps the copy so it stands where the game stands; one of those steps was not legal on the
  copy's screen, and the exception left the run (the copy's `sync` is not guarded the way its `apply` is), so the worker wrote a
  crash row (`where: agent`) and restarted the game.
- **Phase 5 is the copy's rewards screen** (`PHASE_RELIC_REWARD`: the gold, potion, relic, card and special items after a fight).
- **The moment, in all 12:** a won fight against the Thieving Hopper (THIEVING_HOPPER_WEAK, an early Act 2 fight). The Hopper
  steals a card on its first move; killing it gives the card back as an extra "special card" item on the rewards screen. The
  game's driver takes the gold and the returned card without asking and then asks about the card reward. At that question the
  copy claims its own gold and returned card too, to hold the same deck, and the returned-card step is the one it refused.
- **The action numbers are potion ids.** The step was computed as "potion + relic + card items", where the potion and the
  relic are the item's id (not 1 for "present"). Every refused number is a potion id plus one card item (no relic in a normal
  fight).

## The 12 rows

| night folder | seed | worker | Z | refused | copy's potion (id) | card the Hopper returned | earlier divergence |
|---|---|---|---|---|---|---|---|
| 2026-10-30 | B47PPNUNC7 | 10 | 10-30 05:13 | 62 | Touch of Insanity (61) | Spite | none |
| 2026-10-30 | VP5AA8R94P | 0 | 10-30 05:31 | 11 | Colorless Potion (10) | Bully | floor 19, re-anchored |
| 2026-10-30 | KAE3YPER3K | 5 | 10-30 06:28 | 41 | Orobic Acid (40) | Bludgeon+ | none |
| 2026-11-01 | NNB7U6ZZWJ | 11 | 11-01 02:31 | 25 | Flex Potion (24) | Stone Armor | floor 19, re-anchored |
| 2026-11-02 | 2VZVEM4TKS | 9 | 11-01 23:29 | 40 | Mazaleth's Gift (39) | Fight Me+ | none |
| 2026-11-03 | WG5SPJ2T83 | 10 | 11-02 22:00 | 24 | Fire Potion (23) | Inferno | floor 19, re-anchored |
| 2026-11-03 | SAZ8CYFPRA | 1 | 11-02 22:22 | 64 | Weak Potion (63) | Stone Armor | none |
| 2026-11-03 | JFTP58MYAB | 7 | 11-02 23:45 | 6 | Block Potion (5) | Dominate+ | none |
| 2026-11-03 | 92PKPZQDYR | 7 | 11-03 00:05 | 7 | Blood Potion (6) | Volley | none |
| 2026-11-04 | XQL535FL5N | 6 | 11-03 21:29 | 6 | Block Potion (5) | Charge | none |
| 2026-11-04 | Q7CHDAAVNN | 9 | 11-03 21:47 | 57 | Speed Potion (56) | Hemokinesis | floor 19, re-anchored |
| 2026-11-05 | EKFPQ4U8GW | 11 | 11-04 19:12 | 18 | Duplicator (17) | Fight Me+ | none |

The potion is the refused number minus one card item, named from `data/id_map.json`. The returned card and the moment are read
from each worker's game-log copy (`logs/w5-night-<date>-stdout/p<worker>r<restart>.log`): every one ends with the Hopper's gold,
then "special_card", then the game waiting on the card question.

**One mechanism, all 12.** Four rows also carry a divergence record from earlier in the run (a floor-19 reward where the game's
deck holds an upgraded Strike the copy lacks, and the gold differs); each was re-anchored at a later map and the lockstep was
back in step when the Hopper fight came. Those records are a separate lead, not this crash.

## The mechanism

The copy's rewards screen is read through native list 6: **(gold amount, potion id, relic id, number of card items, number of
special rows)**. An item's action is its position on the screen: gold, potion, relic, card items, special rows, counting each
present gold, potion or relic as one. The copy's own screen reader (`engine._rewards`) counts that way. The lockstep's claim of
the returned card, added on 2026-10-28 (fork commit 6f20e9e6, "the lockstep claims a returned special card before the card
ask"), added the raw values instead: `potion + relic + cards`.

- With no potion on the copy's screen that sum is 0 + 0 + 1 = 1, the right position, so the claim worked in most Hopper fights.
- With a potion still on the copy's screen the sum is the potion's id plus one: a number past the end of the screen, refused.
- The test for that claim used a stand-in screen that gave 1 for "a potion is there", so it could not see the difference.

**When a potion is still on the copy's screen at the card question.** The game asks about a potion before the card; when the
agent takes it, the copy takes its own too and the potion is gone by the card question. It stays when the game took none:

1. The game's belt was full (two slots at A10). The driver skips a potion without asking when there is no slot, so the game
   leaves it on the screen and so does the copy. Example: EKFPQ4U8GW held a Swift Potion and a Power Potion.
2. The game rolled no potion and the copy did. In VP5AA8R94P the game's belt was empty at the Hopper (its one potion drunk
   during that fight) and it was asked nothing, so it had no potion; the copy had a Colorless Potion. That run had
   diverged at its floor-19 reward and was re-anchored at the map into the Hopper's room. Whether the copy's potion chance is off after a room-entry re-anchor is not
   settled here (an open lead; with the fix it no longer crashes, the copy leaves its potion on the screen).

Size of the window: across the nights' game-log copies there are 1,664 Hopper screens with a returned card; the game took a
potion at 777 of them. The crash needs the copy to hold a potion the game did not take, which happened 12 times.

## Reproduction on the copy

`tests/python/test_lockstep.py`, `HopperReturnedCardNativeTests` in the fork: a copy run is put straight into the Thieving
Hopper fight (`run_start_combat`, encounter 35, a 12-card attack deck, a full belt of two Block Potions), turn one is passed so
the Hopper steals, then the Hopper is killed. Seeds RFSD000000 upward are tried until the screen holds a potion and the returned
card (RFSD000006: gold 8, potion id 54, one card item, one special row, deck 11). The lockstep's `sync` at the card question
then claims the returned card. On the old code it raised `RuntimeError: the engine refused action 55 in phase 5`, the nights'
message; with the fix the deck is back to 12, the gold and the special row are claimed, the potion stays. A stand-in version of
the same screen (`MappingTests`, with the potion's id 17 as list 6 gives it) steps the row at 2, not 18.

## The fix

Python only, in the fork (`referee/lockstep.py` and its tests). `reward_items()` turns list 6 into the screen's item order
(gold, potion and relic counted by presence, then the card items and the special rows), and the copy's gold, its returned card
and the game's answers are all stepped at their position in that one list. The other readers of list 6 (the copy's own screen
reader, the replay and probe scripts, `play.py`, `commands.py`) were checked and already count by presence.

Landed on the fork main as 6c42702d (85a5eb7e put on a8d972b5), pushed 2026-11-04 21:12Z. Python-only gate on the change: 4,337 tests, 19 failures, none new from it (60 on the baseline list; the 3 outside it are the two known tests fixed on main before the landing and the AOT site test, which needs a build output Python-only worktrees do not have); test_lockstep 94 OK on the landed tree.

## Not done, and options

- **A refusal inside `sync` still ends the run.** The lockstep already turns a refused `apply` into a "the copy lost step"
  record and plays on with the fallback until the next re-anchor; a refused step inside `sync` (the comparison before each
  decision) is not caught. Making it the same kind of record would turn any future crash of this kind into a short unranked
  span of a played run instead of a crash row. That is a policy choice for the orchestrator, not built here.
- **The potion the copy had and the game did not** (VP5AA8R94P), and the four floor-19 records (upgraded Strike and gold), are
  fidelity leads of their own.
