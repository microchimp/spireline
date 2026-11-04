# Enemy health: why the game's and the copy's enemy HP part (diagnosis and fixes, 2026-11-05)

Written 2026-11-05 (fidelity lane, mechanism diagnosis; Opus). Read: the last three nights' lockstep records and rows
(`LAB/nightly/2026-11-05/g11`, `2026-11-04/g11`, `2026-11-03/g11`), the real game's stdout logs the lane copies each night
(`D:/spireline/logs/w5-night-2026110{3,4,5}-stdout`, split per run at the driver's `run <seed> ended` line), the fork at main
`a8d972b5`, and the decompile for the game's rules (read, not quoted). The game was not run; every reproduction is on the copy.
Scripts and tables: `D:/spireline/logs/enemy-health/` (`eh_classify.py`, `eh_weights.py`, `eh_furcoat.py`, `eh_pennib.py`,
`cls-<night>.txt`). Weights are the ranking's own formula (`tools/lab/rank.weigh`) over every record whose first differing
field is the enemies' HP.

## 0. In plain words

The pile is the records where, at some decision in a fight, the game and the copy show different HP on the enemies. The
comparison looks only at the hand and at enemy HP inside a fight, so anything hidden (an enemy's block, a power, a relic's
counter) only shows when it finally moves an HP number. That is why the pile looks like a crowd of unrelated small numbers.

It is mostly four separate mistakes, none of them a damage formula:

1. **A card the Stone of All Time event enchanted hits 7 short.** The event's "Push" option gives one Attack +8 damage on its
   first play each fight. The copy gave it +1. Like a voucher printed with the wrong amount: every fight, the first use of
   that card pays 7 less.
2. **Fur Coat bites the wrong rooms.** This Act 3 relic picks seven fights at random and sets every enemy in them to 1 HP. The
   copy rolled its seven picks from a differently-seeded dice, so it bit other rooms (game 1 HP, copy full, or the reverse).
3. **The Ovicopter's eggs stand in a different order.** The game gives each new egg a numbered place and lists them by place;
   after an egg dies, the next egg fills the gap in the middle. The copy put every new egg at the front. Same HPs, different
   order, and from then on the same target number hits a different egg on each side.
4. **The Scythe forgets its growth between fights.** Each play makes The Scythe 4 stronger for the rest of the run; the copy
   only remembered that inside the fight.

These four are fixed on the fork (section 6). Two more are understood but are not one-line rules (section 7), and about a
quarter of last night's weight is a long tail still unexplained (section 8).

## 1. The pile

| night | records | weight | of which: value | same numbers, other order | turn one, 1 HP on one side |
| --- | --- | --- | --- | --- | --- |
| 2026-11-05 | 29 | 592 | 24 | 3 | 2 |
| 2026-11-04 | 38 | 1,024 | 27 | 3 | 8 |
| 2026-11-03 | 133 | 3,355 | 125 | 3 | 5 (1 Fur Coat, 4 Toy Box) |

(The ranking's group for last night, rank 1, weight 559, is the same pile less the records it files elsewhere.)

## 2. By mechanism, with weight

| mechanism | 11-05 records / weight | 11-04 | 11-03 | status |
| --- | --- | --- | --- | --- |
| A. Stone of All Time's Vigorous at 1, not 8 | 7 / 181 (31%) | 5 / 140 (14%) | 38 / 907 (27%) | fixed |
| B. Ovicopter egg order | 3 / 90 (15%) | 3 / 95 (9%) | 3 / 164 (5%) | fixed |
| C. Fur Coat marks other rooms | 2 / 4 (1%) | 8 / 15 (1%) | 1 / 2 | fixed |
| D. The Scythe's growth not kept between fights | 1 / 13 (2%) | 2 / 49 (5%) | 4 / 96 (3%) | fixed |
| E. The played card goes to its pile before its after-play effects | 1 / 39 (7%) | (not counted) | (not counted) | scenario, options |
| F. Toy Box's wax relics (the lists part, and melted relics come back alive after a re-anchor) | 4 / 67 (11%) | 3 / 73 (7%) | 17 / 406 (12%) | options |
| G. Not an HP error: the two sides are on different turns (hand, player HP and energy differ too) | 2 / 33 (6%) | 3 / 79 (8%) | 26 / 693 (21%) | other family |
| unexplained | 9 / 164 (28%) | 14 / 573 (56%) | 44 / 1,088 (32%) | section 8 |

Fixed A to D: **49% of last night's weight**, 38% and 38% of the two nights before. Outcome-changing records among them, last
night: 7 of the 13.

## 3. Kind (a): small value differences

The record is the first decision whose view differs; the step before it (`acted`) is the play that moved the number, or the
enemy turn when the turn advanced. For each record the game's log gives the run's choices: relics, events with the option
taken, cards chosen on every screen, and every card played with its target.

**A. Vigorous.** In every one of the 50 records the card just played is the card the run chose at the Stone of All Time's
"Push" (the log's `chose cards [X]` on that event): last night Thunderclap 3 times, Unrelenting, Bludgeon, Anger, Cinder. The
numbers are the signature: the game's enemy is 7 lower on a plain hit (Hunter-Killer 111 against 118, Louse Progenitor 73
against 80, Bowlbugs 23 against 30 and 36 against 43), 11 lower on a Vulnerable enemy (Mytes 38 against 49, 24 against 35:
(base + 8) x 1.5 against (base + 1) x 1.5, rounded down). Game rule: the event enchants the chosen Attack with Vigorous at the
event's own amount, 8, and Vigorous adds its amount to that card's first attack in a fight. Copy rule: the event opened its
deck selection without an amount and the selection's default of 1 applied (`RunEngine.cs`, the Stone of All Time case). Every
other enchanting event and relic was checked against the game's amounts and matches (Self-Help Book 2, Beautiful Bracelet 3,
Pael's Growth 4, Gnarled Hammer, Kifuda, Punch Dagger, Fresnel Lens, Wing Charm and the 1s).

**D. The Scythe.** Every record right after a Scythe has the game's enemy 4 to 6 lower (Devoted Sculptor 36 against 42; 29
against 33; 35 against 40). Game rule: each play adds 4 (5 upgraded) to the card for good, and the play grows the deck's card
too, so the next fight starts with it. The copy grew only the card in the fight; its own comment said the run half was owed.
The game's other card that grows its deck version, Genetic Algorithm (block), had the same gap and is fixed with it.

**E. The played card's pile before its after-play effects (1 record last night).** Louse Progenitor, game 123, copy 120, run
DYYNTREEES: Neow's Fury hit it, the screen it opened was answered, the card exhausted under Charon's Ashes (3 to every enemy).
Game rule: a card's after-play listeners all run before the card moves to its result pile; the Progenitor's Curl Up pays its
block (18 at A10) at after-play, so Charon's 3 land on that block. Copy rule: `CombatEngine` places the played card (exhaust,
so Charon's Ashes, Feel No Pain, Dark Embrace) before the after-play powers (Curl Up, Rupture, Serpent Form and the rest), so
the 3 reach HP and the block comes after.

**F. Toy Box.** The Ancient relic lends four "wax" relics that melt one by one every third fight. In 24 records over the three
nights the run had already shown a relic-list difference at or after the Toy Box: at the pick the game lists the four lent
relics and the copy does not yet; later the game keeps a melted relic in its list (inactive) while the copy drops it. Each
relic-list difference re-anchors the copy from the game's list, which brings a melted relic back alive in the copy. Last
night's ZNK98WEMJE is the likeliest clean case: the two lists had already parted over which lent relics were still held,
and after a skill on turn one both of the Kaiser Crab's parts are 5 lower in the copy (210, 200 against 205, 195), which is
Letter Opener's 5 to every enemy firing on one side only. The other three (two Perfected Strike records in D2PKZAG58R, a
Chomper in T9NZ337KHZ) sit in runs with the same relic-list history; their exact step was not traced.

**G. Different turns, not damage (2 records last night, 26 on 11-03).** The record also differs in hand, player HP and energy:
the copy is already a turn further (full energy, a new hand). These belong to the turn-flow family, not to enemy health.

## 4. Kind (b): the Ovicopter's children in another order (3 a night)

Game: the Ovicopter encounter has six named places, egg1 to egg5 and the Ovicopter's own last. Each laid egg takes the last
place no creature in the fight holds, and adding a creature with a place sorts the enemy list by place. A dead egg leaves the
fight, so its place is free again. Copy: every new egg was put in front of the first egg (or into a kept corpse's position).
That agrees while no egg has died. With survivors in egg3 and egg4, the game's next clutch fills egg5, egg2, egg1 and lists
[egg1, egg2, egg3, egg4, egg5, Ovicopter]; the copy listed the three new eggs first. Every one of the nine records over three
nights fits this exactly. 2026-11-05 J86VUJQJHU: one egg left, at 2 HP in egg4; the game's clutch fills egg5, egg3, egg2 and
lists [19, 17, 2, 18, Ovicopter 88], the copy lists the three new eggs first, [19, 17, 18, 2, 88]. SXUWEGR77T: one egg left,
at 9 HP in egg3; the game's clutch fills egg5, egg4, egg2: [17, 9, 15, 16, 41] against the copy's [17, 15, 16, 9, 41]. The
11-04 record AKHCZ3C7DY (eggs left in egg3 and egg4, the clutch filling egg5, egg2, egg1) is the same rule with two survivors.
The copy already placed the Fabricator's bots and the Two-Tailed Rats by place; the Ovicopter now does too. Other summoners
checked: Fogmog's and the Obscura's single illusion place and the Wrigglers' and Gremlins' fixed places already come out in
the game's order; Living Fog's bombs take the FIRST free place in the game and are appended in the copy (no record in three
nights; noted, not changed).

## 5. Kind (c): the two turn-one records

Neither is a read before or after a phase change. Both are Fur Coat (run XH5XRL65FK took it at the Act 3 Ancient): the
Devoted Sculptor on floor 36 (map place col 6, row 2) was one of the game's seven bitten rooms and not the copy's (game 1,
copy 172); the Mecha Knight on floor 44 (col 3, row 10) was one of the copy's and not the game's (game 320, copy 1). Game rule:
the coat's rooms are a shuffle of the act's Monster and Elite places with the relic's own dice, seeded from the run seed plus
a hash of the relic's entry name, FUR_COAT. Copy rule: the same shuffle seeded with the class name, FurCoat. 11 records over
three nights (2 + 8 + 1), all at a fight's first decision, all "1 on one side". The other turn-one records of 11-03 (±9 on
every enemy) are Toy Box's Festive Popper alive on one side only (F).

## 6. Fixed (fork main `9240438c`, landed 2026-11-04 23:08Z)

| commit | what | test (fails before, passes after) |
| --- | --- | --- |
| `0d929724` | Stone of All Time: Push enchants with Vigorous 8 | `PotionRewardEventTests.PushingCostsSixHpAndEnchantsAnAttackWithVigorous` (amount 1 against 8) |
| `ef4b0e2e` | Fur Coat: rooms from the stream seeded with FUR_COAT | `FurCoatMarkedRoomsTests` (6 rooms from 3 recorded runs, bitten or not as the game showed: all 6 wrong before) |
| `5fef283e` | Ovicopter: eggs take the encounter's places, list in place order | `OvicopterEggSlotTests` (4) |
| `0e00ea65` | The Scythe and Genetic Algorithm keep their growth for the run | `PlayGrowthReachesTheDeckTests` (5, Rampage as the control that must not carry) |
| `9de0686f` | kernel sites and solver scans regenerated | every `--check` and `gen_key.py --check` |

Plus `9240438c`, the section 7 scenario. Full gate (`tools/build_and_test.sh`) on the same engine tree: C# 7,725 passed, 0 failed
(7 skipped); EmuDump 341 of 341; corpus check 0 regressed fights, 76 improved of 11,317 compared; Python 4,354 ran, no new
failure against the baseline once the scenario's encounter index was corrected (narrow rerun of the scenario and lockstep
tests on the landed tip: 105, OK); site and solver scans all pass. Evidence: `D:/spireline/logs/fork-tests/9240438c.txt`.

## 7. Reproductions for what is left

- **E (pile before after-play).** `tests/scenarios/play-order/curl-up-blocks-charons-ashes-after-the-card.json` on the fork,
  an expected failure on both engines (landed, `9240438c`): Feed into a Louse Progenitor at 100 HP under Charon's Ashes; the
  game's order gives 90 HP and 15 block, both engines give 87 and 18. Options: (1) move `PlacePlayedCard` after the after-play listeners in the old engine's
  play tail (it then has to carry everything placement feeds: the exhaust hooks, Right Hand Hand's discard read, the empty-hand
  check); a whole-play ordering change, so the full gate and the corpus decide; (2) leave the old engine and migrate the play
  tail with the F08/F10 kernel work, where the game's order is the design. Recommendation: (2) if the play-tail migration is
  scheduled within a week; the record weight is 7% last night.
- **F (Toy Box).** No copy-only reproduction captures it: the error is between the game's relic list, which keeps melted
  relics, and the copy's, which drops them, plus the re-anchor that copies the game's list. Options: (1) the driver reports a
  melted relic as melted (or leaves it out of the list), and the anchor sets it melted on the copy; (2) the copy keeps melted
  relics in its list with a flag and every relic effect skips them, as the game does (a run-state field: byte proof and the
  state-hash regeneration). Either needs a decision; (1) is the smaller change and touches the driver, which the night runs.
  The pick itself (the copy's list lacking the four lent relics at the Toy Box decision) is a reward-mirroring question for
  the lockstep and was not traced here.
- **Lab setups.** The lab already holds E, traced against the game: group `Gcf4d2ad05d` (first seen 2026-10-19; setup Charon's
  Ashes, Dramatic Entrance+, the Louse Progenitor fight) shows the game's Progenitor at 123 HP and 15 block against the copy's
  120 and 18, the same numbers as last night's DYYNTREEES. None of the lab's shrunk setups names the Stone of All Time, Fur
  Coat, the Ovicopter's second clutch (its two Ovicopter groups are about the first intent's kind) or The Scythe across
  fights; A, C and D need a run (an event, a map, a second fight), which the fight-only setups cannot express, so the C#
  tests above are their reproductions.

## 8. Not settled

- **Pen Nib (2 records last night, 9284XXYSUF and LQE4PERZ5E).** The copy doubled an attack the game did not: counting the
  game's logged Attacks since the pickup, the doubled plays were the 56th and the 22nd, neither a tenth. The copy's counter is
  run state carried between fights and counts in the play path; the step where the two counts part was not found from the
  log. Next step: a lockstep readout of the Pen Nib counter on both sides at each fight start (one probe field), then a copy
  replay of the fight where they first differ.
- **The rest of last night's long tail (7 records, 1 to 15 HP; signs are the copy's HP minus the game's):** Knowledge Demon after Thrash (+12), Mawler after an Osty card
  from another character (-15), Lagavulin Matriarch after an enemy turn with Corrosive Wave in play (-6), Kaiser Crab after
  Thunderclap (+4, +3), Bowlbug Nectar after Fiend Fire and an enemy turn (+3), Ceremonial Beast after Spite (+3), a Bowlbug
  pair after Fight Me (-1). No two share a card, relic or power. The same holds on the two nights before.
- **Why the pile looks like one group.** The comparison sees the hand and enemy HP only. An enemy's block, its powers, the
  player's Strength or a relic counter can differ for several decisions and surface later as HP, which is what makes the long
  tail hard to read. Adding enemy block and powers to the comparison (as a second, unranked check) would name the step where
  most of these part; that is a lockstep change for its owner.
