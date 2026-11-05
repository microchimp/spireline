# Can the copy regenerate a human run's hidden content from its seed? (probe, 2026-11-05)

Written 2026-11-05 (probe lane; Sonnet). Read: the fork at main `92197feb` (engine source under `src/Sts2Emulator/Core`, Python under
`src/sts2_gym`, `rl/`, `scripts/replay_real_run.py`), run with the copy's library built from the same engine source (native API 39,
the lockstep worktree's `out`; the fork's own `out` is older and is refused by `sts2_gym`). The game was not run, nothing under the
emulator checkout was read, and the decompile was not read or quoted. The human record is the Spire Codex export for v0.107.1
(`runs-v0.107.1.jsonl.gz`): Ironclad, Ascension 10, standard, one player, vanilla acts, **fifths 1 to 3 only** (the exam fifth is
dropped while reading, with the same `is_exam` rule as `rl/human_starts.py`; fifth 4 and fifth 0 are never kept; `assert_no_exam`
runs on the sample). Aggregates only; a cell over fewer than 20 runs is not shown (so the three acts are shown on the 400-run
extension, and the 40-run headline shows acts 2 and 3 together). The probe scripts are in `D:/spireline/referee/backlog/seed-replay/`
(not committed); the drawn runs stay in the data folder.

## 0. In plain words

A run's seed is like the recipe card a kitchen cooks a whole season from. Some dishes depend only on the card (the map of each act,
which monsters stand in which room, which events are waiting, what the "?" rooms turn into, the three first-room gifts). Some
depend on the card **and on how many earlier dishes of the same kind were cooked** (card offers after a fight, shop stock, shop
prices), because each kind has its own pile of numbers that is used up in order. And one pile, the one the fights shuffle and draw
from, is used up by *how the fights were played*.

The result for the questions asked:

* **The map is a function of the seed and the act number.** With nothing played, the copy draws all three acts' maps from the
  seed. The human's route is a path through it in **every** one of 400 runs once two things the record does not say are given to the
  copy (a Spoils Map card in the deck for Act 2; Winged Boots' three free jumps), and in 97 of 100 Act 1s with nothing given.
  Every route that reached the boss, in the runs with neither item, was the *only* matching path. Against another seed's map
  the same routes matched 0 times out of 545.
* **Card offers, shop shelves and shop prices do not depend on the fights, nor on which cards the human took.** They depend on the
  seed and on the earlier rooms' draws (rewards, shops, events), which the record does list. With fights resolved without being
  played, and given the human's route and event choices, the copy's three-card offers matched the record in 97.5 of 100 screens,
  shop shelves in 97.7 of 100 visits and shop prices to the gold in 99 of 100 visits (99.2 in the whole replay where the shelf
  matched). Four rare fight inputs aside (section 1). The 75-in-100 of today's rule-based rebuild is the rule's weakness, not the
  record's.
* **What stops a replay is mostly the human's event choices, not the seed**: the record names the option by a key the fork has no
  table for. With the choice found by trying the copy's options on exact clones and keeping the one that reproduces the record's
  gold, HP, deck, relics and upgrades, only 28 in 100 of 400 replays stay in step to the end of the run; 24 in 100 of events tie
  between options with the same measured effect, and the draws those would use are unknown. Where an event's numbers come from its
  own stream the copy's amount equals the record's to the gold (89 of 89 for three such events).
* About 5 in 100 players see a different first-room gift set than the copy (and about 1 in 100 a different early fight order or boss):
  the copy assumes a "fully unlocked" profile and a real player's unlocks change which pool a draw goes over (section 3.3).

## 1. What each thing depends on (the code, fork main `92197feb`)

Streams are `Core/Rng/RunRngSet.cs` (run-wide, from the seed) and `Core/Rng/PlayerRngSet.cs` (the player's, seed plus slot).
`Seed` is a hash of the canonical string seed (`RunRngSet.cs:26`); each named stream is the seed plus a hash of its name.

| thing | stream and state it reads | what it does **not** read | where |
| --- | --- | --- | --- |
| Map of an act | `act_<k>_map`, k the act **index** (`RunRngSet.cs:41`); the act model rolled at run start; Ascension (elite count); the Spoils Map card in the deck (Act 2 only, own stream `spoils_map` `RunRngSet.cs:48`); Golden Compass (replaces the act's map with one column) | fights, rewards, shops, events, the route so far. Winged Boots changes where the player may step, not the map | drawn when the act is entered, not at run start: `RunMapGenerator.cs:527` (`AdvanceToNextAct`) -> `:677` -> `:724`, stream `:740`, counts `:654`, elites `:2071` and `RunConstants.cs:179`, Spoils `:692` and `RunConstants.cs:1016`, compass `:619`, boots `:1697` |
| Which monsters, elites, boss, events, ancient each act holds | `up_front` at run start, in act order, over the profile's unlocked pools | everything the player does | `RunMapGenerator.cs:47` (`SelectActAndGenerateRooms`), `:172` (rooms), `:395` (event ring), `:235` (first boss the profile has never fought replaces the draw), `:134` and `:277` and `:286` (profile gates) |
| First-room gift (Neow) | `NEOW` stream (seed plus hash of the name); a refusal list that reads the profile (`Kaleidoscope` needs all characters unlocked) | the run | `RunEngine.cs:2043`, `RunNonCombatEffects.cs:1236`; later acts' ancients `RunNonCombatEffects.cs:3181` |
| What a "?" room turns into | `unknown_map_point`: the n-th "?" visited, plus the climbing odds the earlier "?" results left, whether the last room was a shop or all the node's children are shops (map-dependent), Juzu Bracelet and Golden Compass | fights, rewards | `RunEngine.cs:417` |
| Which event | the act's event ring (above), walked forward from the cursor past events the run may not be shown (gold, deck, HP, potion, floor and act gates) or has seen | any draw | `RunNonCombatEffects.cs:1419` (`EnterEvent`), `:1529` (gates) |
| An event's option values (gold, HP, costs) | the event's own stream, seed plus hash of the event's name, one per event (`:3156`), set up on entry (`:2119`) | the other streams | seed only; **exceptions**: Fake Merchant prices from `shops` (`:2183`); events that offer cards, relics, potions from `rewards` (e.g. `:588`, `:1116`, `:3119`); random transforms, upgrades, curses and combat HP from `niche` (`:311`, `:645`, `:771`, `:2848`, `:1398`) or `transformations` (`:3809`) |
| Card offer after a fight | `rewards` (player stream, `PlayerRngSet.cs:20`): potion roll, gold, then per card a rarity roll with the running pity offset, a pick over the character's pool (blacklist only inside the screen), an upgrade roll; the room type, the act index, relics that widen or upgrade offers | the deck, the cards taken earlier, the fight's play | `RunRewardGenerator.cs:245` (combat rewards), `:1281` (`PopulateCardReward`), `:2189` (rarity and offset), `:2224`, `:2270`; gold `:2053` |
| Shop stock | rarity rolls from `rewards` (5 cards, 2 colourless, 2 relic slots: `:1565`, `:1579`, `:1606`, `:1620`), picks from `shops`, relics from the shared relic bag (shuffled at run start from `up_front`, drained by every earlier relic pull) | the fight | `RunRewardGenerator.cs:1535` (`EnterShop`) |
| Shop prices | `shops` only (player stream, `PlayerRngSet.cs:21`): sale slot (`:1553`), one jitter draw per item, the sale card priced twice (`:1581`), potions after the picks; removal 100 plus 50 per earlier removal at A10 (`:1657`); Membership Card halves, Courier and Smiling Mask change prices | the fight, the floor, the Rewards position | `RunRewardGenerator.cs:2376` (card), `:2401` (relic), `:2421` and `:2439` (potion) |
| What the fights themselves draw | the run-spanning combat streams (shuffle, monster AI, targets, card generation, energy costs, orbs) are carried from fight to fight and written back at the end; `niche` is shared with the run (monster HP rolls, summons) | | `RunEngine.cs:195` to `:260`, `:2484` |

So, without replaying a single fight: the map, the act contents, "?" results, event identity, event values, the chest relic, card
offers, shop stock and shop prices are all functions of the seed plus the **non-fight** history (route, shop visits, reward
screens, event choices). The record lists every one of those, so a replay can follow them; it needs no fight. Four small ways a
fight does reach the run layer, none modelled by a history-only replay: a monster that escapes zeroes the gold draw (`:2107`);
The Hunt's kills, a Heist's and a Swipe's loot add reward rows (`RunRewardGenerator.cs:394`); Lava Lamp upgrades offers after
a fight that cost no HP; and `niche` moves with a fight's monster HP rolls, which shifts later random transforms and curses.

## 2. The probe

**Sample.** The corpus holds 9,058 usable runs in fifths 1 to 3 (after the exam fifth, fifth 4 and non-vanilla acts). The 400 with the
smallest `sha256("seed-replay|" + run id)` were drawn once; the first 40 of those are the headline, the 400 are a larger sample of the
same procedure. Each run starts on the copy with the record's seed (Ironclad, Ascension 10) with no other input.

**Maps (`probe_maps.py`).** The copy draws Act 1's map at start; Acts 2 and 3 by its own act transition (`debug_enter_next_act`,
no fight played). The record's route is the types of the points the human visited (monster, elite, rest, shop, treasure, "?", boss).
It matches when some path of the map from the act's first node has the same types in order (a route that ends early is a prefix).
Three readings: seed only; plus a Spoils Map card in the deck when Act 2 is drawn if the record gained one in Act 1; plus Winged
Boots' up to three free jumps after the floor it was picked up. Acts in which the Golden Compass had been picked up by the act's end
(3 in Act 2, 1 in Act 3) are set aside, not tested. Control:
every complete route against the next run's map of the same act.

**Run layer (`probe_replay.py`).** The fork's `HistoryReplayer` (`scripts/replay_real_run.py`) walks the copy through the record floor
by floor: the same gift, the node of the human's type, fights **resolved without being played**, the human's reward choices, shop
purchases, rest choices, event options; after each floor the gold, and away from a fight the HP, are compared and set to the record's.
Three changes for this format: card offers compared as a set (the record lists them in display order, the copy in rolled order);
a shop's shelf is the cards left plus the cards bought; the price test sums the copy's quoted price for every item bought (and the
removal) against the visit's `gold_spent` (visits that buy Membership Card, Courier or Smiling Mask are set aside, 7 in 400, since
the price falls while the visit goes on). The event option is found by trying every option of the page on an exact clone (up to the
pages the record shows) and keeping the one whose result equals the record's gold, max HP, HP, deck, relic count and upgrade count.
Each comparison is logged with whether the replay was **clean**: no screen the copy could not answer the human's way, no event
option that was ambiguous or did not reproduce the record, and no gold/HP difference after an earlier floor. A clean-path figure is
therefore a conditional one: given that everything before matched, the next screen matched this often.

## 3. Results

### 3.1 Maps

400 runs (Act 1: 400 runs; Act 2: 200 reached, 197 without the compass; Act 3: 116 reached, 115 without):

| reading | Act 1 | Act 2 | Act 3 |
| --- | --- | --- | --- |
| seed only: route is a path | 387 / 400 | 173 / 197 | 112 / 115 |
| plus the Spoils Map card (when the record gained one) | 387 / 400 | 194 / 197 | 112 / 115 |
| plus Winged Boots' jumps | **400 / 400** | **197 / 197** | **115 / 115** |
| complete routes with none of those items: a path / the only path | 290 / 290 / 290 | 135 / 135 / 135 | 95 / 95 / 95 |
| routes that ended early, none of those items: a path / the only path | 93 / 93 / 89 | 56 / 56 / 48 | 16 / 16 / 14 |
| act region equals the record's | 398 / 400 | 200 / 200 | 116 / 116 |
| boss (the first boss) equals the record's | 301 / 304 | 140 / 142 | 97 / 99 |
| control: the same complete routes against another seed's map | 0 / 304 | 0 / 142 | 0 / 99 |

The 13, 24 and 3 misses of the "seed only" row are all explained: every Act 1 and Act 3 miss held Winged Boots, and all but 3 of the
24 Act 2 misses were runs that gained a Spoils Map card in Act 1 (21; for the 19 first examined the record shows the *Nab the Map*
option of the event The Legends Were True), after which the engine draws a different, hourglass-shaped Act 2 map from its own stream
(`RunMapGenerator.cs:692`); the other 3 held Winged Boots. The copy models both items; the probe only had to tell it. The 40-run
headline: Act 1 38 / 40 seed only and 40 / 40 with the items; Acts 2 and 3 together (30 runs reached) 27 / 30 seed only and 30 / 30
with the items; complete routes 26 / 26 in Act 1 and 24 / 24 in Acts 2 and 3, each the only path; the control 0 / 53. All 400 runs'
maps take about 5 seconds on one core.

The two Act 1 region misses and the boss misses (3, 2 and 2 in the three acts) look like the profile (inferred, not shown): a player who
never entered Underdocks is sent to the other Act 1 without a draw, and a boss the profile has never fought replaces the drawn one
(`RunMapGenerator.cs:134`, `:235`).

### 3.2 What the run layer reproduces (400 runs, fights resolved not played)

| thing | whole replay | while the replay is clean (given all before matched) |
| --- | --- | --- |
| first-room gift set (Neow) | 379 / 400 | same (it comes first) |
| Act 2 and 3 ancients' gifts | 292 / 315 | 72 / 75 |
| the monster behind each fight room | 4,981 / 5,064 | 2,199 / 2,206 |
| what a "?" room turns into | 1,994 / 2,016 | 947 / 947 |
| which event | 1,393 / 1,471 | 719 / 733 |
| treasure chest relic | 674 / 692 | 235 / 235 |
| elite and other relic rewards | 851 / 1,106 | 362 / 371 |
| card offer (three cards, as a set) | 3,812 / 4,837 | **2,130 / 2,185** |
| card offer, also in the record's display order | 1,784 / 4,837 | 909 / 2,185 |
| gold after a fight's rewards are claimed | 3,898 / 4,678 | 2,069 / 2,095 |
| potion rewards | 3,948 / 4,717 | 2,054 / 2,095 |
| shop shelf (cards, relics, potions all equal) | 553 / 726 | **296 / 303** |
| shop price, visits with a purchase: to the gold | 569 / 646 | **259 / 262** |
| ... within 10 gold | 570 / 646 | 259 / 262 |
| ... to the gold where the shelf matched | 483 / 487 | 255 / 256 |
| ... to the gold where the shelf differed but the bought items were on the copy's shelf | 80 / 95 | fewer than 20 |

The 40-run headline reads the same where its cells are large enough: Neow 38 / 40; fight monsters 502 / 506; "?" rooms 180 / 184;
event identity 131 / 133; card offers 363 / 485 whole, 169 / 174 clean; shop shelves 55 / 79 whole, 24 / 26 clean; shop price to the
gold 60 / 71 whole, 20 / 21 clean, 49 / 49 where the shelf matched.

**Controls.** (a) With the copy's player taking **no card at all** in every reward (the human's picks replaced by skips), the card
offers matched 3,812 / 4,837 and the shelves 553 / 726, the same counts to the unit as with the human's picks: what is offered does
not depend on what was taken. (b) No fight was played in any of the replays, yet the offers match: fights are not an input.
(c) Wrong-seed maps: section 3.1.

**What the clean path costs.** 111 of 400 replays (28 in 100) stay clean to the last floor of the record (152, 38 in 100, if ties
between equal-effect event options are allowed); the median clean path ends at floor 7 of a median run of 18 (quartiles 5 and 15).
What ends it, of the 289 that do not run clean: 122 an ambiguous event option, 53 an event option that does not reproduce the
record (the copy's effect differs from the human's), 14 a different event than the record's, 71 a gold or HP difference after a
floor (28 after a shop, 16 after a "?", 14 a fight, 10 an elite, 3 other), 10 a gift the human took that the copy did not offer,
11 a rest or map step the copy could not take (Hatch, whose relic the record does not name, 7), 8 an event or deck screen it could
not answer. After the clean path is lost, 63 in 100 of card offers still match (1,682 of 2,652), because many ambiguous picks do
not move the stream; the whole-replay column above is not a rate of the engine.

**Events.** Of 1,435 events with a logged choice, the clone search found an option sequence that reproduces the record's measured
effects exactly and alone for 906 (63 in 100), a tie between options for 345 (24), an inexact best for 122 (9), and nothing to try for
62 (4). This is a statement about the copy's option sets as much as about the search: for 79 in 100 of events (1,134, ties
included) the copy has an option whose gold, HP, deck, relic and upgrade result is the human's. Where the numbers come from the
event's own stream the amounts equal the record's to the gold: Dense Vegetation (61 to 99 gold) 25 / 25, Sunken Statue (101 to 121)
44 / 44, Sunken Treasury 20 / 20.

### 3.3 What did not match, and what we think it is (partly unverified)

* **Profile.** 21 of 400 gift sets, 5 of 400 runs with their first Act 1 fights in a different order, 2 of 400 Act 1 regions and 7 of
  545 boss draws differ from the copy's: the copy assumes a fully unlocked profile; the game's refusal and discovery rules read
  the real player's unlocks. In 4 of the 21 gift misses the copy offered Kaleidoscope, which the engine refuses unless all
  characters are unlocked, and one refusal changes the whole shuffle; the rest of the 21 are consistent with that but not shown.
  Not testable without the profile.
* **Aubergine and extras.** The base replayer compares only the first gold pile of a fight; Amethyst Aubergine adds a separate 15
  (the "gold after rewards" row above is the fair test). Potion rewards beyond the room's own (a relic's) are not modelled by the
  replay; unverified which relic.
* **Shops.** The price misses (about 12 in 100 of purchase visits in the whole replay) are almost all after the clean path was
  lost; in the clean path 3 of 262. The price-changing relics (Membership Card, Courier, Smiling Mask) change prices mid-visit.
  A removal's price (100 plus 50 each) depends on how many earlier shop removals the replay saw.
* **Fights.** HP after a fight is the record's, not played; escaped monsters and The Hunt/Heist/Swipe extras (section 1) are not
  supplied, so the elite and monster gold or card rows they touch can differ.

## 4. What this means for the human decision set

Today's set (`rl/human_prior.py`, `docs/rl/HUMAN_PRIOR.md`) has no map (a donor's), rebuilds shop prices from the copy's rules (75.4 in
100 of purchase visits within 10 gold; shops left out of the fit), and has no routes or events.

| decision | becomes | because |
| --- | --- | --- |
| **route** (which node next) | teachable, with the true map | the map is exact from the seed and the act; the human's route is the only matching path in 98 in 100 acts (669 of 683 acts of the runs without boots or compass) and the other 2 can be skipped; about 38 in 100 steps have 2 or more children and 27 in 100 have children of different types (2,560 of 9,424 steps in 381 runs): about 6.7 real room-type choices a run. About 60,000 for the 9,058 runs of fifths 1 to 3 (an extrapolation). |
| **map block of every other decision** (card, rest, ancient, shop) | the true map ahead and the true distance to the boss, replacing the donor's | same |
| **shop buy or leave** | with exact prices | prices are a function of the Shops stream and the shelf; a replay quotes them to the gold in 88 in 100 of visits (99 in 100 while in step); the 9-in-10 within-10-gold gate that kept shops out of the fit is nearly met by the whole replay (88 in 100) and met in step (99 in 100) |
| **event choice** | teachable with its option set and each option's effect (from clones) | the copy gives every option of the page and its result; the human's pick is identified exactly for 63 in 100 of events, up to a tie for 24 in 100 more |
| card reward | unchanged: the record lists the offers; the replay adds a check that the three-card split of a merged screen is right | |
| fight starts | unchanged | |

Not made teachable by this: what the human saw of a hidden fight, a boss they never reached (a guess stays a guess), the profile.

## 5. The builder change this implies (not done here)

1. **Map block**: for each run, `Sts2RunEnv(seed, ascension=10)`; `map_graph()` for Act 1; the copy's act transition for Acts 2 and 3;
   put a Spoils Map card in the deck before Act 2 when the record gained one in Act 1; allow up to three jumps after Winged Boots.
   Find the human's path by type; flag acts with no path or more than one. Replaces the donor table (162 s, 67 keys) with
   about 12 ms a run.
2. **Route decisions** as a fifth kind: options are the children (the whole next row with boots), the chosen one is the next
   point; features are the afterstate of stepping there (the existing `apply_option` has no route kind).
3. **Shop prices**: take the quoted prices from the replay (or from the Shops stream directly: one jitter draw per item in slot
   order) instead of the rule band; keep the price-changing relic visits out.
4. **Events**: a one-off table of every event page's option keys in the order the game lists them (the fork has option **counts**,
   `Generated/EventOptions.g.cs`, and `replay_real_run.py` reads the keys from a decompile that is not in the fork). With it the
   63 and 24 in 100 above become nearly all; without it, use the clone search and keep the unique-and-exact picks only. The
   owner's step: extend `scripts/generate_event_options.py` to write keys, no text.
5. **A per-run identity check** that costs nothing: gift set, Act 1 region, first two fights, Act 1 boss against the copy's; drop or
   flag runs that disagree (about 5 to 7 in 100: the profile, inferred).
6. **Use the replay as the state rebuild** for the decisions it can follow (it reproduces gold and HP after each floor and flags where it
   cannot); a full pass over the 9,058 runs is about 15 minutes of one core (400 runs took 36 seconds).

## 6. Caveats and what is unverified

* 40 runs is the asked-for probe; the counts in sections 3.1 and 3.2 are the 400-run extension of the same procedure (first 40 inside it),
  from 400 of 9,058 eligible runs, a draw by a fixed hash. Runs differ in what they hold, so a rate is not a guarantee for a single run.
* The clean-path rates are conditional and read as "given everything before matched"; the unconditional rate of a late screen is
  the whole-replay column, lower because the event step of the replay is imperfect.
* Event options are found by effect, not by name; 24 in 100 are ties, 9 in 100 inexact. A wrong tie-break can move a later draw.
* Profile effects are inferred from where the copy and the record disagree, not shown: the profile is not in the record.
* Golden Compass maps (4 acts in 400 runs) were not tested; Winged Boots is allowed three jumps after its floor, which makes its runs' match
  easy, so their "only path" is not claimed.
* The copy's library is the lockstep worktree's build at the same engine source as fork main; fork main's own `out` is stale.
* Fights were never played; every HP after a fight is the record's. Nothing here says the copy plays a fight like the game.
* The extra potions in the record (a relic's) and the `Hatch` rest option are not modelled by the replay; their share is small
  and unmeasured.
* Not measured: whether the replay's prices stay exact in Acts 2 and 3 by act (the counts above are all acts together).
