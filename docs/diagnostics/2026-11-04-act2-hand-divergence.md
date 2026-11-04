# Act 2 hands: why the game holds the copy's whole hand plus cards (diagnosis, 2026-11-04)

Written 2026-11-04 11:50Z (fidelity lane, diagnosis; Opus). No code changed. Read: the last three nights' lockstep records and rows
(`LAB/nightly/2026-11-02/g9`, `2026-11-03/g11`, `2026-11-04/g11`), the real game's stdout logs the lane copies each night
(`D:/spireline/logs/w5-night-2026110{2,3,4}-stdout`, split per run at the driver's `run <seed> ended` line), the fork at main
`5bef4fd6` (no `src/` change since the nights' tree `e22346e1`), and the decompile for the game's rules (read, not quoted). Run: seven
single-seed copy runs, one process each, with the nights' engine library (`wt-lab/out`, copied to a scratch folder first so the lab's
build is never held open). The game was not run. Line numbers are at fork main `5bef4fd6`.

Group under study: `F-handcount` of `docs/diagnostics/2026-11-04-act2-act3-fidelity.md` (one side's hand holds the other's whole hand
plus one or more cards). Re-extracted here from `divergences.jsonl` (first differing field `.combat.hand`, sizes differ, one side's
multiset contains the other's): **348 records on the last three nights, 342 of them in Acts 2 and 3 (182 runs), 6 in Act 1**; the
fidelity note counts 340 in Acts 2 and 3 by its own group rules.

## 0. In plain words

The copy plays a fight's **first turn** through a separate, hand-written start; every later turn goes through the turn-start code.
The game has no such split: turn one runs the same turn start as turn ten. Anything the copy put only in the later-turn code is
missing on turn one. **Pollinous Core** (a relic from the Colossal Flower, an event that exists only in Act 2) counts the player's
turns and gives two extra cards on every fourth one, counting across fights. The copy's turn one neither counts the turn nor pays
the two cards, so the copy's count falls one turn behind at every fight and its two cards come one turn late, or, when the fourth turn
is a fight's first, not at all. The game's hand is then two cards bigger. That is **259 to 268 of the 342 records (76-78%)**.

Like a pedometer that misses the first step of every walk: over a day it is behind by one step per walk, and the "every fourth step"
chime rings late.

Three smaller mechanisms make most of the rest: **Booming Conch** never fires in Act 2 or Act 3 elite fights because the copy decides
"is this an elite fight" from a list of Act 1 elites only (40 records, 12%); **Brightest Flame+** draws 3 in the game and 2 in the copy
(19 records, 6%); **Stoke** deletes the cards Dark Embrace drew while it exhausted the hand (3 records, plus 1 in Act 1). About 12
records (3.5%) are left unexplained (section 9).

The re-anchor failure "no emulator id" for the Decimillipede (section 8): the lockstep's fight loader looks enemies up by the game's
class name, and the game names the three segments `DECIMILLIPEDE_SEGMENT_FRONT`, `_MIDDLE` and `_BACK` while the copy has one
`DecimillipedeSegment`. The live layer already has the table that maps them (`sts2_gym/live/ids.py` `MONSTER_SUBCLASSES`); the anchor
tables do not use it. One line in `src/sts2_gym/native.py` `run_set_anchor_tables`, confirmed on the copy.

## 1. What the records say

Each record carries the decision index, floor, encounter (the roster the fight began with), turn, whether the turn advanced since the
decision before, the step before (`acted`), the two hands, and whether a fight-start re-anchor was tried and held. It carries no relics
or powers: those were read off the game's log of the same run (the event option the game took, the Ancient's pick, relic rewards).

| | records (Acts 2+3) | runs | side holding more | size difference | turn of the record | encounters (top) |
| --- | --- | --- | --- | --- | --- | --- |
| Pollinous Core held (turn start) | 254 | 125 | game 249, copy 5 | 2 | 4: 92, 1: 87, 2: 45, 3: 30 | Louse Progenitor 20, Infested Prism 16, 4 Exoskeletons 16, Mytes 15, The Insatiable 15, Entomancer 15, Chompers 14, Kaiser Crab 14 (32 encounters) |
| ... same, hand at the 10-card cap | 5 | 5 | game | 1 (10 against 9) | 2-4 | mixed |
| ... other sizes or mid-turn, core held | 9 | 5 | mixed | 1-4 | 1-3 | mixed |
| Booming Conch held, Act 2/3 elite, turn 1 | 40 | 34 | game 40 | 2 | 1: 40 | Entomancer 15, Decimillipede 13, Infested Prism 11, Soul Nexus 1 |
| right after playing Brightest Flame+ | 19 | 10 | game 19 | 1 | any | 13 encounters |
| right after playing Stoke (Dark Embrace held) | 3 | 3 | game 3 | 1-3 | 1, 6, 7 | Knowledge Demon, Kaiser Crab, Decimillipede |
| unexplained | 10 | 8 | game 6, copy 4 | 1-6 | mostly 1-2 | mixed |
| no game log for the run | 2 | 1 | game | 2 | 2, 4 | |
| **all** | **342** | **182** | **game 328, copy 14** | | | |

- **Which side, and does it flip.** The game holds the superset in 328 of 342. Of the 182 runs, 171 show only the game ahead, 4 only the
  copy, 7 both: the copy is ahead when its late Pollinous payment lands on a turn the game did not pay (replay A below shows one).
- **When it shows.** 128 at a fight's first decision (the step before was a map, reward, rest, event, shop or treasure choice), about
  180 at the first decision of a later turn (the step before an End Turn, or a card play after which the referee ended the turn because
  nothing was playable), about 30 inside a turn (22 of them the Brightest Flame and Stoke ones).
- **The extra cards are not special.** They are whatever lies on top of the draw pile: Strike 120, Defend 78, Anger 27, Ascender's Bane
  22, Bash 16, then the deck's own cards. Nothing about the cards; everything about how many are drawn.
- **Why Acts 2 and 3.** Pollinous Core comes from the Colossal Flower, which is in the Hive's (Act 2's) event list only; the relic stays
  for Act 3 (24 of the 254 are on floors 34+). Booming Conch is a Neow pick held from floor 1, but the copy reads Act 1 elites correctly,
  so it only fails from Act 2 on. Brightest Flame comes from the Storybook, an Act 2 Ancient option. In Act 1 the same records are 6 in
  three nights.
- **Re-anchors.** A record at a fight's first decision re-anchors at once, and the fight-start anchor puts the game's hand and relic
  counters on the copy, so the run goes on being compared; the mistake then repeats at the next fight (up to 6 records a run). 13 of the
  40 Booming Conch records failed to re-anchor: all 13 are Decimillipede fights (section 8).

## 2. Mechanism 1: turn one skips Pollinous Core

**The game's rule** (`PollinousCore`, `CombatManager.StartCombatInternal`, `StartTurn`, `SetupPlayerTurn`). The relic keeps a saved
turn count (`TurnsSeen`) that no fight resets. At every player-side turn start, turn one included, the side-turn-start hook adds one to
it; then the hand draw asks every relic how many cards to draw, and Pollinous Core adds two when the count stands at four, after which
the count goes back to zero. Turn one of a fight is not special: combat start runs the same turn start every later turn runs.

**The copy's rule.**

- `src/Sts2Emulator/Core/CombatEngine.cs` `EndTurn` (the next turn's start, about line 2499) calls `RelicEffects.TickPollinousCore`. That
  is the only call. Turn one never reaches it: it runs `CombatFactory.Reset` -> `RelicEffects.ApplyBeforeOpeningHand` (its "phase 4,
  the side's `BeforeSideTurnStart`", `RelicEffects.cs` about line 709, lists only the five relics whose hook is guarded to turn one) ->
  `CombatEngine.StartFirstTurn` / `ContinueFirstTurn` (about line 3126) -> `CombatFactory.DrawOpeningHand`.
- `src/Sts2Emulator/Core/Effects/RelicEffects.cs` keeps **two** hand-draw lists: `ExtraOpeningHandDraw` (turn one, about line 1147) and
  `ExtraHandDraw` (turns two on, about line 934). Pollinous Core's two cards are in the second only.
- `TickPollinousCore` (about line 1105) sets the count to 1 when it stood at 4 or more, else adds one; it does not reset to zero when the
  relic has paid, so after a fight that ended on a paying turn the copy carries 4 where the game carries 0 (the next tick gives 1 on both,
  so it is invisible to play, but the counter a re-anchor or a feature reads differs).
- The count does survive between fights (`RelicEffects.RunCounterRelics` / `CarryRunCountersBack`, about line 2195, and
  `CombatFactory.Reset`'s `runRelics`), so the copy is behind by exactly one turn per fight since the relic was taken or since the last fight-start anchor
  wrote the game's count.

**Why D11F1 and D11F2 did not remove it.** D11C (2026-10-27) saw this shape in Act 1 and traced it to the relic counters a re-anchor did
not carry; D11F2 made the fight-start anchor write the game's counters. That fixed the anchor, not the copy's own rule: in lockstep (no
record, so no anchor) the copy still loses one turn a fight, and the anchor only runs after a record has already been written. Pendulum,
the other relic D11C named, is not affected: its tick is in `ApplyAfterPlayerTurnStart`, which turn one does call.

**Evidence 1: the game's logs predict the records.** For every run of the three nights whose log shows the Colossal Flower's Pollinous
Core option, the player turns of each later fight were counted from the log (a new turn at each enemy move block) and both rules were
simulated from a count of zero: the game's (every turn counts, pay at four on any turn) and the copy's (turn one does not count and
never pays). The first turn where one pays and the other does not is the predicted record.

| runs with the core taken at the event | 152 |
| --- | --- |
| first record after the pickup is a hand record on the predicted floor and turn | **113** |
| hand record on another floor or turn (the log's turn count is approximate: an enemy that does nothing logs no move) | 12 |
| first record is something else (enemy HP 4, relics 1, floor 1, phase 1, HP 1) | 8 |
| a divergence predicted, no record (run ended or the turn was never asked) | 8 |
| no divergence predicted, and none recorded | 11 |

**Evidence 2: two copy replays to the record's turn.** The record's seed on the copy, Neow's first option, straight to Act 2
(`run_debug_enter_next_act`), then the game's own map coordinates from its log, so the copy meets the same rooms; fights before the
record's fight resolved (`run_debug_resolve_combat`) after the number of turns the game played, End Turn only; Pollinous Core added with
`run_debug_set_player` (count 0) at the point the game took it; then the record's fight, turn by turn. Hand size and the core's count
are read on a combat fork. Same rooms and the same encounters as the game; the deck is the starting deck (the size of the draw is what
is tested, not which cards).

*Replay A: 11-04 seed R6J25H4ECA, record decision 167, floor 22, Chompers, turn 1 (game 7 cards, copy 5).* Game log: core taken on
floor 20, Bowlbugs (Weak) on floor 21 lasted three turns, Chompers on floor 22.

| fight (copy encounter) | turn | copy hand | copy count | game hand | game count |
| --- | --- | --- | --- | --- | --- |
| Bowlbugs Weak (Bowlbug Rock + Nectar) | 1 / 2 / 3 | 5 / 5 / 5 | 0 / 1 / 2 | 5 / 5 / 5 | 1 / 2 / 3 |
| Chompers (2 Chompers), the record's fight | 1 | **5** | 2 | **7** | 4, paid, 0 |
| | 2 | 5 | 3 | 5 | 1 |
| | 3 | **7** | 4 (paid) | 5 | 2 |

The game's column follows its rule from the log's turn counts. The record is turn 1 (game 7, copy 5), and the copy's late payment on turn
3 is the copy-ahead shape the 14 copy-side records show when no anchor intervened.

*Replay B: 11-03 seed J7CPAG3V4S, record decision 163, floor 22, Bowlbug Rock + Bowlbug Silk + Slumbering Beetle, turn 4 (game 7,
copy 5).* Game log: Tunneler (floor 19), Exoskeletons (floor 20), Colossal Flower (floor 21: core taken), then this fight. The copy met
Tunneler, three Exoskeletons, an event, then exactly the record's roster.

| turn | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| copy count / hand | 0 / 5 | 1 / 5 | 2 / 5 | 3 / **5** | 4 / 7 |
| game count / hand | 1 / 5 | 2 / 5 | 3 / 5 | 4, paid, 0 / **7** | 1 / 5 |

Both replays show the copy's turn one adding nothing to the count and the payment landing one turn late, on two seeds, two encounters,
one record at a fight's first turn and one at turn 4. (A third seed, H43T988Q62, could not be walked: its record's room is an unknown
node that the game rolled as a fight and the copy, with a different run history, as an event.)

**Every other place the same split is used.** The mechanism is the copy keeping turn one as a second, hand-maintained copy of the turn
start. What was checked against the decompile:

| game hook (every player turn, turn one included) | copy, turns 2+ | copy, turn 1 | verdict |
| --- | --- | --- | --- |
| hand-draw modifiers, relics: Snecko Eye +2 every turn | `ExtraHandDraw` | `ExtraOpeningHandDraw` | ok |
| Pael's Blood +1 every turn | both | both | ok |
| Fiddle +2 every turn (late) | both | both | ok |
| Ring of the Drake +2 on turns 1-3 | turns 2-3 | turn 1 | ok |
| Bag of Preparation, Ring of the Snake +2 turn 1 only; Big Mushroom -2 turn 1 only | - | turn 1 | ok |
| Booming Conch +2 turn 1 only, elite room only | - | turn 1, but the elite test is wrong (section 3) | wrong elsewhere |
| Pocketwatch +3 from turn 2 | turns 2+ | - | ok |
| **Pollinous Core +2 whenever the count is 4, any turn** | `ExtraHandDraw` | **missing** | **wrong** |
| side-turn-start relics: Pollinous Core's count (saved, never reset) | `EndTurn` | **missing** | **wrong** |
| Kunai, Shuriken, Ornamental Fan, Rainbow Ring, Velvet Choker, Brilliant Scarf, Beating Remnant, Demon Tongue, Mini Regent, Music Box, Orichalcum (+ fake), Pocketwatch's last-turn tally, Pael's Flesh, Ripple Basin: reset a per-turn tally or a display | turn start | fresh at combat start | equivalent (nothing carries in from the last fight) |
| Bag of Marbles, Red Mask, Cracked Core, Twisted Funnel, Power Cell (turn-one-guarded) | - | `ApplyBeforeOpeningHand` phase 4 | ok |
| Pendulum (after-player-turn-start, every turn) | `ApplyAfterPlayerTurnStart` | same function with turn 1 | ok |

Not checked: the hand-draw powers (Clarity, Demesne, Draw Cards Next Turn, Machine Learning, Mind Rot, Pale Blue Dot, Tools of the
Trade, Tyranny) and the side-turn-start powers (Aggression, Hardened Shell, Plating, Sloth, Void Form) on turn one. A power is on the
player at turn one's draw only if something applied it before the draw (a combat-start relic or an enemy's room-entry move), which is
rare; Plating on an ENEMY grants its block at the start of the player's first turn only (round 1), which the copy's turn one should be
checked for. The fix below makes the question disappear for relics; the powers are an audit item for the worker, not a known error.

## 3. Mechanism 2: the copy decides "elite" from an Act 1 list

**The game's rule.** Booming Conch (+2 cards on turn one, +1 energy at turn one's start) and Sling of Courage (+2 Strength on entering
the room) ask whether the current ROOM is an elite room. War Hammer, Black Star, White Star and Sword of Stone ask the same of the room.

**The copy's rule.**

- `src/Sts2Emulator/Core/CombatFactory.cs` line 402: `IsEliteCombat = IsEliteEncounter(encounter)`, with `EliteEncounters` (about line
  1130) listing the six Act 1 elites. Its own remark says Act 2's elites were left out on purpose because the emulator then modelled
  Act 1 only. Booming Conch reads `IsEliteCombat` (`RelicEffects.cs` about lines 805 and 1154), so it never fires in an Act 2 or Act 3
  elite (Entomancer, Infested Prisms, Decimillipede, and Act 3's).
- `src/Sts2Emulator/Core/Run/RunEngine.cs` line 311 sets `combat.IsEliteRoom` from the room the run resolved, which is the game's
  question, but it does so after `CombatFactory.Reset` (line 291) has already run the combat-start relics and the opening draw. Sling of
  Courage reads `IsEliteRoom` (`RelicEffects.cs` about line 632) inside that reset, so it never fires in any run elite, Act 1 included.
- The run layer's War Hammer, Sword of Stone and White Star use `LastResolvedRoomType` directly and are right.

**Confirmed on the copy** (11-03 seed ZJPP63YBW7, record decision 179, floor 25, Entomancer, turn 1, game 7 cards, copy 5): walked to
the same elite node by the game's coordinates with Booming Conch and Sling of Courage held. At turn one the copy has `is_elite_combat
false`, `is_elite_room true` (set after the hooks ran), hand 5 (game 7), energy 3 (game 4), no Strength (game 2). The lockstep does not
compare energy or powers, so the energy and Strength halves are invisible in the records but change play.

## 4. Mechanism 3: Brightest Flame+ draws one card too few

The game's Brightest Flame gives 2 energy and draws 2, and its upgrade raises BOTH by one (3 energy, 3 cards). The copy
(`CardEffects.cs` about line 9008) gives 3 energy upgraded but always draws 2; its comment says the draw does not upgrade, and the test
`BrightestFlameTests.EnergyUpgradesButTheDrawDoesNot` (`src/Sts2Emulator.Tests/Cards/Colorless/EventSkillCardTests.cs`) pins the wrong
rule. All 19 records follow a Brightest Flame play whose energy rose by 3 (the upgraded card): the game holds exactly one card more.

Other cards: 48 game cards raise a card count on upgrade. Spot-checked in the copy and right: Battle Trance, Burning Pact, Offering,
Pommel Strike, Fuel, Relax, Expertise. The other 40 are a script sweep (section 7, step 6), not a known error.

## 5. Mechanism 4: clearing the hand after exhausting it deletes drawn cards

The game's Stoke exhausts each card of a snapshot of the hand, one at a time; a card drawn meanwhile (Dark Embrace draws one per
exhaust) stays in the hand, and the generated cards are added after. The copy (`CardEffects.cs` lines 628-647, `IC.Stoke`) exhausts
the snapshot and then calls `state.Hand.Clear()`, which removes the Dark Embrace draws from the fight altogether (they are in no pile).
Same code in `PotionEffects.cs` lines 346-354 (Glowwater Potion). The same bug was found and fixed for Pael's Eye's end-of-turn exhaust
(`CombatEngine.cs` about line 1607, whose comment describes it); Fiend Fire removes each card as it goes and is right. Confirmed by
reading and by one run's log (11-03 CTYCWAU49Q: Dark Embrace played in the run, game 3 cards ahead after Stoke); the other two Stoke
records have Feel No Pain or Burning Pact in the run and no Dark Embrace play logged, so they are not explained by this.

## 6. The failing tests to write first

All C#, in `src/Sts2Emulator.Tests`, each red on main today:

1. **`TurnOneStartTests`: Pollinous Core pays on turn one.** `CombatFactory.Reset` with a 12-card deck, relic ids `[PollinousCore]` and
   `runRelics: [new RelicInstance(PollinousCore, 3)]` (the shape `TeaOfDiscourtesysDazedCanOpenTheHand` uses). Expect hand 7 and the
   core's counter 0 (today: 5 and 3).
2. **`TurnOneStartTests`: Pollinous Core counts turn one.** Same with the count at 0: expect counter 1 after the reset (today 0); then End
   Turn three times: expect hand 5, 5, 7 at turns 2, 3, 4 and 5 again at turn 5 (today 5, 5, 5 and 7 at turn 5).
3. **Run-level: the count carries across two fights.** On a `RunEngine` (or the run session), the core at 0, a fight of three turns
   resolved, the next fight's opening hand: expect 7 (today 5). This is replay A as a unit test.
4. **`EliteAndUpgradeRelicTests`: Booming Conch and Sling of Courage in a run elite of every act.** With the run's room set to elite
   before the combat starts, for an Act 2 elite (Entomancer, encounter 63) and an Act 1 elite: expect hand +2, energy +1, Strength +2
   against the same fight without the relics (today: nothing for Entomancer; Sling nothing in both). `BoomingConchFiresInEveryActOneElite`
   asserts `IsEliteCombat` directly and will change with the fix.
5. **`BrightestFlameTests`: the upgraded card draws 3.** Replace `EnergyUpgradesButTheDrawDoesNot` with the game's numbers (2/2 and
   3/3).
6. **Stoke and Glowwater with Dark Embrace.** Hand of Stoke + 3 cards, Dark Embrace 1, a known draw pile: after Stoke the hand holds the
   3 cards Dark Embrace drew plus 3 generated (today 3); Glowwater the same idea (the Dark Embrace draws stay, then 10 are drawn up to
   the cap).

## 7. Fix brief for a Sonnet worker (engine change: full gate)

Worktree `wt-act2-hands` from fork main. Files: `src/Sts2Emulator/Core/Effects/RelicEffects.cs`, `src/Sts2Emulator/Core/CombatEngine.cs`,
`src/Sts2Emulator/Core/CombatFactory.cs`, `src/Sts2Emulator/Core/Run/RunEngine.cs`, `src/Sts2Emulator/Core/Effects/CardEffects.cs`,
`src/Sts2Emulator/Core/Effects/PotionEffects.cs`, the tests above, and the regenerated hash-pinned files.

1. **One hand-draw list.** Replace `ExtraOpeningHandDraw` and `ExtraHandDraw` with one function of the turn number the draw is for, each
   relic carrying its own game guard (the table in section 2; Booming Conch reads the room). `DrawOpeningHand` and the later-turn draw
   both call it. Pollinous Core is then counted on turn one by construction. Keep the order and the `ApplyTurnOneDrawPileReorder` input
   as they are (the opening count goes into the reorder).
2. **One side-turn-start tick.** Move `TickPollinousCore` to a function both turn starts call: turn one's in `ApplyBeforeOpeningHand`
   phase 4 (before the draw, as in the game), later turns where it is now. Make it reset to 0 after paying (the game's
   `AfterModifyingHandDraw`), not at the next tick, so the copy's counter equals the game's `TurnsSeen` at every point (refset's
   `COUNTER_MAP` writes `TurnsSeen` into it unchanged).
3. **Elite from the room.** Set the combat's elite-room flag before `CombatFactory.Reset` runs (pass it in, or set it on the `CombatState`
   the run builds at `RunEngine.cs` line 207, from `LastResolvedRoomType == NodeElite`), make Booming Conch read it, and retire
   `IsEliteCombat` (the direct combat environment without a run sets the room flag from the encounter, with the Act 2 and Act 3 elites
   added from `RunConstants.HiveEliteEncounters` and the Act 3 list; `CombatSnapshot` keeps reading `is_elite_room`).
4. **Brightest Flame+** draws `upgraded ? 3 : 2`; fix its comment and test.
5. **Stoke and Glowwater Potion** remove each card from the hand as it is exhausted (the Pael's Eye loop) and drop the `Hand.Clear()`.
6. **Sweep** (script, report only, no fix unless a mismatch shows): for the 48 game cards whose upgrade raises `CardsVar`, check the
   copy's case passes an upgrade-dependent count; list mismatches in the landing note.
7. **Regenerate the hash-pinned files before the gate** (the engine-edit checklist): re-record the split hash in `tools/kernel/sites.py`
   if `CombatEngine.cs` changes (first confirm the edit is outside `DoomThePlayerAtTurnEnd`), `tools/kernel/sites.py build`, then
   `tools/solver/scan_order_reads.py`, `scan_draw_observers.py`, `scan_utility_gains.py` in write mode and each with `--check`, plus
   `gen_key.py --check`. Without them the gate shows three new failures: `OrderReadTests.TheScanIsAsFreshAsTheEngineSources`,
   `test_kernel_sites`, `test_utility_gains`.

**Done looks like:** the six tests green; the full gate at the last engine landing's counts (Pillage, 2026-11-03: C# 7,700 passed, 0
failed, 7 skipped, plus the new tests; EmuDump 341/0; corpus 0 regressed of 11,317; Python 3,972 ran with 6 failures and 12 errors,
nothing above the known baseline); a byte proof against main in which every differing fight-mode pair holds Pollinous Core, Booming
Conch or Sling of Courage in an elite, an upgraded Brightest Flame, or Stoke or Glowwater with Dark Embrace, and every other pair is
identical; the next night's `F-handcount` in Acts 2 and 3 at or under about 0.5 per 1,000 decisions (from 2.2). Size: about 2 units.

## 8. The re-anchor: Decimillipede segment names

**Where it fails.** The fight-start anchor (`EmuLock._anchor_fight` -> `native.run_reanchor_fight` -> `FightAnchor.Anchor`) looks every
enemy of the game's record up by name in `FightAnchor.Tables.Enemies` (`src/Sts2Emulator/Core/FightAnchor.cs` line 294,
`PatchEnemies`). The tables are built once per process from `data/id_map.json` by `src/sts2_gym/native.py` `run_set_anchor_tables`
(line 1936). The copy has one enemy, `DecimillipedeSegment` (id 22, key `DECIMILLIPEDE_SEGMENT`); the game's record names its three
subclasses, so the lookup throws and `Anchor` returns "no emulator id for The given key 'DECIMILLIPEDE_SEGMENT_FRONT' ...". Across all
nine nights' records the only game enemy names the table lacks are those three and `MYSTERIOUS_KNIGHT` (a Flail Knight subclass,
1 record). The live layer already maps exactly these four (`src/sts2_gym/live/ids.py` `MONSTER_SUBCLASSES`).

**The one-line fix** (Python only, Python-only gate), in `run_set_anchor_tables` after `id_map` is loaded:

    from sts2_gym.live.ids import MONSTER_SUBCLASSES  # noqa: PLC0415 -- the game's subclass names the emulator keeps under their base
    id_map = {**id_map, "enemies": {**id_map["enemies"], **{sub: id_map["enemies"][base] for sub, base in MONSTER_SUBCLASSES.items()}}}

**Confirmed on the copy:** a run session at seed FTD5K97LDS put into the Decimillipede fight (encounter 69, three segments of id 22), a
record built from its own piles with the game's three names: today status -4 with the message above; with the tables merged as above,
status 3 (patched). Test to add: `tests/python/test_native_reanchor.py`, a Decimillipede fight re-anchored from a record naming
`DECIMILLIPEDE_SEGMENT_FRONT/MIDDLE/BACK` holds. Pairing is by kind in roster order, so the game's FRONT, MIDDLE, BACK pair with the
copy's three segments in its order; the worker should check on one night record that the copy's roster order is the game's (the
`F-ehp-deci` fix of 10-30 settled the HP order). Expected: the night's largest re-anchor failure gone (23 of 42 failures on
11-03, 12 of 14 on 11-04; 207 of 439 over nine nights), and the 13 Booming Conch records of section 1 that did not re-anchor would
have. Size: under half a unit.

## 9. What could not be confirmed

- **The game side was not run.** The game's columns in the replay tables follow its rule (read in the decompile) from the turn counts
  in its own logs; the copy's columns are measured. The records themselves are the game's measurement.
- **The replays use the starting deck** and Neow's first option, and resolve earlier fights instead of playing them; they test the count
  and the size of the draw, not the cards drawn. Seed H43T988Q62 could not be walked (an unknown room rolled differently).
- **Unexplained, 12 records:** DRBAPZWFP4 (2 records, game 5-6 cards ahead at turn 2 with Runic Pyramid held, probably the retained
  hand), 79T9SQY5RL (2), FS6ERMD5DC, N2TF7NSXN4, AHJ8JCNCHD, DB9YA7P246, FT9SUZK2WP, BXHMHTDYP8 (one each), and the run without a
  game log (2). Inside the Pollinous Core runs, not explained by the late payment alone: 8XLKVJY8W6 (copy 3 cards ahead,
  four times), 9H36WKW336 (copy 1 ahead at a fight start), and four records with the game 2 or 4 ahead after an End Turn or a potion in
  the same round (DUUNCL8T3X twice, AT26K4GVJU, DXXC3P2N9K), possibly the core paying on an extra turn; nor are the two Stoke records
  without Dark Embrace. The six Act 1 records were not studied.
- **Turn-one powers** (section 2's last paragraph) and the other 40 upgrade-count cards (section 4) are audits, not findings.
- **The fight-reward and enemy-HP groups** of the fidelity note are not touched here, though Booming Conch's missing energy and Sling of
  Courage's missing Strength in elites will also have moved enemy HP and player HP records there.

## Appendix: the copy replay

Run from any folder with the emulator interpreter, `-I -B`, one process: `python -I -B pc_replay.py <lib dir> '<spec json>'`, where the
library directory holds a copy of the night's `Sts2Emulator.dll`. Spec for replay A:
`{"seed":"R6J25H4ECA","path":[[3,0],[4,1],[4,2],[3,3],[3,4]],"fights":{"1":1,"3":3,"4":"record"},"core_before":3,"core_counter":0,"record_turns":4}`;
replay B: `{"seed":"J7CPAG3V4S","path":[[3,0],[4,1],[5,2],[6,3],[5,4]],"fights":{"1":1,"2":1,"4":"record"},"core_before":4,"core_counter":0,"record_turns":5}`.
`path` is the game's Act 2 map coordinates from its log; `fights` maps a path index to the turns to play before resolving it, or
`"record"`.

```python
import os, sys, json
ROOT = 'D:/spireline/fork/sts2'
os.environ.update(STS2_LIB_PATH=sys.argv[1], STS2_ENGINE='core2', STS2_ALLOW_STALE_NATIVE='1')
sys.dont_write_bytecode = True
for p in (ROOT + '/rl', ROOT + '/src', ROOT):
    sys.path.insert(0, p)
from sts2_gym import procutil, native
procutil.lower_priority()
from run_train import engine

CORE = 200
spec = json.loads(sys.argv[2])
s = engine.RunSession(spec['seed'], 10, engine.CombatBudget(1, 1))
env, obs = s.env, s.env._run_obs_buf

def fight_state():
    child = s.combat(fork_combat=True).combat_fork(None)
    try:
        return len(native.get_pile(child.handle, native.PILE_HAND)), dict(native.get_relics(child.handle))
    finally:
        native.destroy(child.handle)

d = s.decision(); s.apply(d.options[0])            # Neow: first option
native.run_debug_enter_next_act(s.handle, obs)     # straight to Act 2
path = [tuple(x) for x in spec['path']]
pi = 0
while pi < len(path):
    d = s.decision()
    if d.type != 'map':
        o = next((o for o in d.options if any(w in o.kind for w in ('skip', 'proceed', 'leave'))), d.options[0])
        s.apply(o); continue
    opts = {(o.node[0], o.node[1]): o for o in d.options}
    if pi == spec['core_before']:
        native.run_debug_set_player(s.handle, obs, hp=999, max_hp=999, relics=list(s.view().relics) + [CORE],
                                    relic_counters=[(CORE, spec['core_counter'])])
    s.apply(opts[path[pi]])
    if s.phase == engine.rc.PHASE_COMBAT:
        plan = spec['fights'].get(str(pi))
        turns = plan if isinstance(plan, int) else spec['record_turns']
        for t in range(1, turns + 1):
            n, rel = fight_state()
            print(path[pi], 'encounter', native.run_encounter_id(s.handle), 'turn', t, 'hand', n, 'core', rel.get(CORE))
            if t < turns:                          # End Turn is the action after the hand
                native.run_step(s.handle, n, -1, obs, env._run_rew_buf, env._run_terminal_buf, env._run_truncated_buf)
        if not isinstance(plan, int):
            break
        native.run_debug_resolve_combat(s.handle, obs)
    pi += 1
s.close()
```
