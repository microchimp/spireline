# Order audit: game vs emulator (static, 2026-10-16)

Read-only audit of every place where the ORDER in which the game handles things can differ from the
emulator's. Game = referee/decompiled (class and method names only, no game code quoted). Emulator =
the fork at 885f56ba (paths below are relative to the fork root). Hook dispatch order is NOT redone:
tools/fidelity/hook_open.txt holds 94 open `order` rows and 109 `missing` rows, which stay the owner of
that class.

Verdicts: match (both sides read, same list order / key / tie rule), MISMATCH (a difference shown by
reading both sides), unsure (cannot be settled by reading; the test says how to settle it), n/a (display
only, infrastructure, or an engine that selects by deck index so no list order exists).
"Depth": R = both sides read; F = game side read, emulator confirmed by the shared helper, its comments
or a test name only.

Counts (sites, approximate where a row groups many): about 257 checked: 196 match, 5 MISMATCH (4
findings: M1 Vakuu draw-pile order, M2 Power Cell and Aggression hand order, M3 Goopy write-back, M4 Summon
Forth), 13 unsure (Claws batch order; 12 map HashSet sites), 43 n/a (display, infrastructure, hook
dispatch cross-reference).

## 1. Method (the logic)

An outcome depends on order in only four ways, so each site was put in exactly one class:
1. a sort with ties (List.Sort / Array.Sort are introsort, unstable above 3 elements for the network and
   above 16 for partitions; LINQ OrderBy is stable);
2. a random pick or shuffle over a list (the index drawn is only as good as the list's order);
3. a selection screen (a selector, the referee's included, takes the FIRST n of the list the command
   built, so list order is the pick);
4. iteration of an unordered collection, or a batch whose items are inserted in an order of its own.
For each class the game's rule was compared with the emulator's rule, then the list-building step.

## 2. Table of sites

### 2.1 Explicit orderings in the game (grep: Sort, OrderBy, OrderByDescending, ThenBy, sortingOrder, Comparer, Comparison, IComparable)

| # | Game class / method | Emulator | Verdict | Depth | Reason |
|---|---|---|---|---|---|
| A1 | ListExtensions.StableShuffle (List.Sort() then Fisher-Yates) | CardEffects.StableShuffle :3854, ShuffleDiscardIntoDraw :3741, RunNonCombatEffects.StableShuffleDeck :284, GameRng.StableShuffle (Core/Rng/GameRng.cs:178) | match | R | Same runtime introsort (Array.Sort on keys+items, List.Sort with a comparison, both the same partitioning), eligible list handed in pile/deck order, n-1 draws. |
| A2 | AbstractModel.CompareTo, CardModel.CompareTo, ModelId.CompareTo (category, entry ordinal, then upgrade level) | CardEffects.EntryRank :3680, ShuffleSortKey :3867; StableShuffleDeck :286 | match | R | Entry compared ordinal, then Upgraded. All 38 MaxUpgradeLevel overrides are 0 (default 1), so a bool is the whole level. |
| A3 | DeterministicModelComparer (listener order) | hook tables | n/a | F | Owned by tools/fidelity/hook_table.py, hook_order.py, hook_open.txt (94 order rows open). Not redone. |
| A4 | CardSelectCmd.FromDeckGeneric with sortingOrder, FromDeckForRemoval (curses first, then deck index, stable OrderBy) | none: RunNonCombatEffects.CanSelectCard picks by deck index; the referee mirror reads the game's record (91a985f4) | match (n/a) | R | The engine has no list, so no list order to get wrong; the mirror takes the cards at the game's positions. |
| A5 | CardSelectCmd.FromDeckForEnchantment(cards) (OrderBy deck index) | RoyalStamp :1164 replays the Niche shuffle draws, picks by deck index | match | R | Shuffle only spends n-1 Niche draws; the screen re-sorts to deck order. |
| A6 | CardSelectCmd.FromCombatPile, draw pile branch (orderby Rarity, ModelId) | CardEffects.OpenDrawPileSelection :4697, :4640 (candidates in pile-index order) | MISMATCH (Vakuu) / match (other callers) | R | See M1. Only a selector that takes the first candidate (VakuuCardSelector, Whispering Earring) sees the sort. |
| A7 | CombatState.SortEnemiesBySlotName (List.Sort on slot index) | CombatFactory slots (:1651, :1932), FabricatorOwnSlot | match | R | Slot index is the key; unique slots, and the unslotted case has ties but fewer than 17 items (insertion sort keeps them). |
| A8 | CardCmd.Transform(batch) PileIndexSort | RunNonCombatEffects.TransformInDeck :3698 (appends in pick order) | unsure | R | See U1: the batch overload appends in ascending index order, the emulator in pick order. Only Claws uses the batch overload. |
| A9 | RewardsSet.GenerateWithoutOffering (sort by RewardsSetIndex; Gold 1, Potion 2, Relic 3, SpecialCard 4, Card 5, Removal 7) | RunRewardGenerator comments :240, :311, :669; EliteRewardOrderTests | match | F | Populate runs in set order, the sort only moves the display; <= 16 items so ties keep order. |
| A10 | DollRoom.DollChoice.CompareTo (relic ModelId) | RunNonCombatEffects.DollRoomOffer :2880 | match | R | Entries sorted ordinal (BING_BONG, DAUGHTER_OF_THE_WIND, MR_STRUGGLES) before the shuffle; Take(2) and Take(3) both shuffle all three. |
| A11 | Map: StandardActMap (4 StableShuffle/UnstableShuffle), SpoilsActMap (3), MapPathPruning (SortedDictionary ordinal, 2 shuffles), MapPoint/MapCoord/MapLocation/RunLocation IComparable (12 sites) | RunMapGenerator OrderBy Col/Row (:710, :777, :885, :1489, :1513, :1737), StableShuffle(Comparer<int>) :1865, :1906, :1225 | unsure | F | See U2: HashSet<MapPoint> Children/parents/start sets are enumerated after Remove, which reuses slots. Outcome-checked only (ActMapShapeTests, MapSegmentSearchTests, real-run replays). |
| A12 | UI-only sorts (n=25): NCardGrid x2, NCardPileScreen, NBestiary, NCardLibraryGrid, NSimpleCardSelectScreen x2 (prefs.Comparison), NGameOverScreen, MapSplitVoteAnimation, NPotionLabCategory, NRelicCollectionCategory x2, NTimelineScreen, NUnlockTimelineScreen, NTreasureRoomRelicCollection, NHellraiserVfx x2, NCrystalSphereScreen, EpochModel x3, ArtConsoleCmd, GetLogsConsoleCmd x3, AchievementConsoleCmd | none | n/a | F | Display only. FromSimpleGrid hands the selector the caller's list unsorted (prefs.Comparison is applied by the screen). |
| A13 | Infrastructure sorts (n=16): ModHelper x2, NetTypeCache, ModelIdSerializationCache, JsonSerializationUtility, SavedPropertiesTypeCache, CloudSaveStore x2, ProgressState, EpochComparer, SemanticVersion, LocString, NullLeaderboardStrategy, BackgroundAssets, HandLayoutHelper, ModelDb.Distinct chains | none | n/a | F | No effect on a run's outcome. |
| A14 | CardSelectCmd list builders: FromDeckForUpgrade (deck order, IsUpgradable), FromDeckForTransformation (deck order, not Quest, IsTransformable), FromHand/FromHandForDiscard/FromHandForUpgrade (hand order), FromSimpleGrid/FromChooseACardScreen/FromChooseABundleScreen (caller's list) | engine picks by deck/hand index in the same order; DrawPileToHand candidates in pile order | match | R | Same candidate set and order; the draw-pile screen is the one sorted list (A6). |

Emulator sort sites (37) mapped: CardEffects :3431 (M2), :3697, :3780, :3861, :4645, :10883 (M2), :3697; RunNonCombatEffects :286, :767, :2388, :2496, :2884 (all Entry-ordinal on unique entries: match); RunEngine :1976, :1988 (M3); RunRewardGenerator :624 (match: pool ids sorted by character name, same as ModelId of the pool); RunMapGenerator (U2); CombatSnapshot :1863, RunNativeExports :301-318, UnlockState :167, HookChoiceReplay :452 (output / tooling only: n/a); GameRng :180 (match).

### 2.2 Order of the source list before a random pick or shuffle

| # | Game site(s) | Emulator | Verdict | Depth | Reason |
|---|---|---|---|---|---|
| B1 | Deck-upgrade StableShuffle, n=7: Whetstone, WarPaint, WarHammer, SandCastle, FragrantMushroom, BattlewornDummy, DoorsOfLightAndDark | UpgradeRandomDeckCards :301, UpgradeRandomCards :3547, ApplyWarHammerOnVictory :3540, UpgradeRandomDeckCardsForEvent :258, callers :3555, :3682 | match | R | Positions in deck order, sorted by Entry then Upgraded with List.Sort, Fisher-Yates on Niche or the event's stream; candidate = !Upgraded && def.Upgradable; type filter (Attack / Skill / none) matches. |
| B2 | NextItem over a deck list, n=14: ImprovementPower, Reflections x2 (with removal), TabletOfTruth, EndlessConveyor x2, WelcomeToWongos, SlipperyBridge, RanwidTheElder x2, TrashHeap x2, StoneOfAllTime, TheFutureOfPotions | ApplyImprovementUpgrades :90, Reflections :3575, UpgradeRandomCard :2840, DowngradeRandomUpgradedCard :2823, SlipperyBridge :2714, EventRng :3123 | match | R | Index lists built in deck order; the event's stream is one stream per event (counter carries); candidates filtered the same. |
| B3 | Combat pile shuffles/picks, n=14: StoneCracker, PowerCell, BeatDown x2, Uproar x2, Catastrophe x2, SeekerStrike, Anointed, DrainPower, AggressionPower, Cinder, HiddenGem | StableShuffle :3854 (Stone Cracker, Uproar, Catastrophe, BeatDown, SeekerStrike), DrawRareCards :2504 (Anointed, correct order), UpgradeDiscardCards :10025, GrantReplayToADrawPileCard (HiddenGem: same two-tier filter) | match except PowerCell and Aggression (M2) | R | Pick order inside the shuffled list is used; the hand receives the cards in shuffled order in Anointed, not in PowerCell/Aggression. |
| B4 | CombatTargets.NextItem(HittableEnemies), n=14: ForgottenSoul, Kusarigama, ParryingShield, Tingsha, CountdownPower, HauntPower, JuggernautPower, SerpentFormPower, BeatDown, BouncingFlask, LightningOrb, CardCmd x2, WhisperingEarring (AnyAlly) | CardEffects.RandomLivingEnemy :4986, RelicEffects :1372, :2539, CardEffects :1406, :1959, :5619 | match | R | Enemy order = roster order; list = alive or steam-eruption-dying; reviving enemies hold Hp 0 so the game's ShouldAllowHitting rule (Adaptable, Illusion, Reattach while reviving) gives the same set. Two helpers (RandomLivingEnemy and EnemyAI.IsTargetable :5333) state the rule differently; they agree only while Reviving implies Hp 0. |
| B5 | CombatCardSelection.NextItem(pile), n=12: Bookmark, JeweledMask, MummifiedHand x4, Thrash, TrueGrit, StampedePower (Shuffle stream), CardPileCmd.Add Random (draw pile NextItem :948), WhisperingEarring | RelicEffects.ApplyAfterFlush :2332, :1128, :1467; CardEffects :9356, :9378, CombatEngine :5485 | match | R (Bookmark, TrueGrit, Stampede), F (rest) | Hand/pile order as indexed lists; Bookmark list = retained cards in hand order with !CostsX and cost > 0. |
| B6 | Pile placement/shuffle: CardPileCmd.Shuffle (discard then draw, HashSet only used as a set), CardPileCmd.Add position Random (Shuffle stream NextInt(Count+1)), CardPile.RandomizeOrderInternal (opening UnstableShuffle in deck order), AfflictionModel.PickRandomTargets (no caller) | ShuffleDiscardIntoDraw :3741, AddCardToDrawPileRandomly :4135, AddCardToDiscardPileRandomly :4118, CombatFactory :423-426 | match | R | Same stream, same draw count, same pre-shuffle order (the opening shuffle has no sort, so deck order is the input: see 2.4). |
| B7 | Event/ancient option pools, n=45: Neow x4, Orobas x4, Pael x3, Tezcatara x3, Vakuu x3, Nonupeipe, Tanx, Darv, DollRoom x3, RelicTrader, FakeMerchant, NeowsBones x2, Kaleidoscope, SereTalon, CursedRun, DustyTome, FishingRod, WingCharm, ScrollBoxes x2, PaelsTooth, TinkerTime x2, potion picks on the Rewards stream (BattlewornDummy, EndlessConveyor, PotionCourier, TheLegendsWereTrue, Wellspring) | RunEngine :1696-1735 (Neow: curse list, positive list with MassiveScroll dropped before the shuffle, pairs appended Lava/Capsule, Oyster/Humidifier, Talisman/Pomander), GenerateAncientOptions :3148, RollRelicTraderStock :2384, RollGeneratableCurse :2490, SereTalon :767, OtherCharacterPools (RunRewardGenerator :619), UnlockState.Characters :100 | match | R (Neow, DollRoom, RelicTrader, Kaleidoscope, SereTalon, Orobas character list), F (rest) | Neow curse and positive lists verified id by id against the game's declaration order; AllCharacters order Ironclad, Silent, Regent, Necrobinder, Defect matches the enum; ModelId sort for card pools alphabetical by character. |
| B8 | Act and room generation, n=11: ActModel.GenerateRooms (events shuffle over AllEvents + AllSharedEvents minus epoch-locked events; weak/regular/elite grab bags; boss, ancient), ActModel.GetRandomList, RunManager shared ancients and second boss, RelicGrabBag.Populate x2 | RunMapGenerator.GenerateEventSequence :383ff, UnlockedEvents :293, PopulateRelicGrabBags :24, RelicGrabBag.Populate (Core/Run/RelicGrabBag.cs:63ff) | match | R | All four act event lists and the 18 shared events compared name by name in declaration order; epoch-locked events removed before the shuffle (one event per epoch); RelicGrabBag shuffles buckets in first-seen rarity order (Dictionary insertion order), the emulator keeps _shuffleOrder for that. |
| B9 | Factories, n=10: CardFactory (shop, reward, combat, transform x3, rarity roll), PotionFactory.GetPotionOptions, OrbModel.GetRandomOrb, Creature.SetUniqueMonsterHpValue | CardEffects.ShuffleTake :3045, RunRewardGenerator.TransformOptionsFor :57, generated pools (CardPools.g.cs, PotionPools.g.cs, RelicPools.g.cs "in pool order"), CombatFactory :1868-1905, EnemyAI.RollSummonedHp :5600 | match | R (HP, transform, ShuffleTake), F (pools) | Pool lists are extracted in the game's declaration order; TakeRandom = full Fisher-Yates then Take; unique HP uses the same HashSet<int> (ascending after ExceptWith) and ElementAt. |
| B10 | Monsters and encounters, n=14 gameplay (+8 skin picks on Rng.Chaotic, n/a): Fabricator (HashSet declaration order, last-spawned exclusion), ThievingHopper, SlimesWeak x3, BowlbugsNormal/Weak, RubyRaidersNormal, FlyconidNormal, SlitheringStranglerNormal x4, ToughEgg | EnemyAI.PickBot :5011, CombatFactory :1105-1260, :1644 | match (Hopper: known open) | R (Fabricator, Flyconid, rats), F (rest) | Hopper's stolen-card removal by value is already ledger line (2026-10-14, C5-R01). |

### 2.3 Iteration over unordered collections (HashSet, Dictionary, ToHashSet, GroupBy, Distinct)

| # | Game site | Emulator | Verdict | Depth | Reason |
|---|---|---|---|---|---|
| C1 | UnknownMapPointOdds.Roll (Dictionary iterated in insertion order Monster, Elite, Treasure, Shop; ToHashSet of keys + Event; first-by-order fallback) | RunEngine.RollUnknownMapPointNodeType :360 | match | R | Float running total in the same order; fallback unreachable (Event is always in the set). |
| C2 | RunManager.BuildRoomTypeBlacklist (Shop after a shop or when all children are shops) | RunEngine.IsUnknownShopBlacklisted :423 | match | R | Same two conditions. |
| C3 | Creature.SetUniqueMonsterHpValue (HashSet<int> from a range, ExceptWith, NextItem) | CombatFactory :1883-1895 | match | R | Same collection type and operations. Note the exclusion set differs (see B9) but not its order. |
| C4 | PainfulStabsPower (Dictionary<Creature, ...> Keys loop; players only) | BuffSystem / CombatEngine (single-player: one key) | match | F | One player key in a single-player run. |
| C5 | CardPileCmd.Shuffle HashSet<CardModel> of the draw pile (used as insertion-ordered list) | ShuffleDiscardIntoDraw :3741 | match | R | HashSet enumerates in insertion order with no removals; sorted afterwards anyway. |
| C6 | RelicGrabBag._deques Dictionary iteration | RelicGrabBag._shuffleOrder | match | R | See B8. |
| C7 | SlipperyBridge.SkippedRemovals, Hoarder, BingBong _cardsToSkip, Dampen casters, Hellraiser autoPlayingCards, ScrollBoxes.usedCardIds, CardFactory allowedRarities, Merchant blacklists x3 (membership only) | n/a | match | F | Used as sets, never enumerated into an outcome. |
| C8 | ModelDb.All* Distinct/Concat chains (cards, relics, potions, events, encounters) | generated pool arrays | match | F | Distinct keeps first occurrence; the arrays are extracted in that order. |
| C9 | Map HashSet<MapPoint> parents / Children / startMapPoints, MapPostProcessing HashSet<int> | RunMapGenerator | unsure | F | U2. |
| C10 | RunEngine.CarryGoopyGrowthToTheDeck (emulator-only GroupBy + ToDictionary of queues) | RunEngine :1967-1996 | MISMATCH | R | M3. |

### 2.4 Other order-shaped behaviour

| # | Game | Emulator | Verdict | Depth | Reason |
|---|---|---|---|---|---|
| D1 | Deck order: card rewards, curses, duplicates append; CardCmd.Transform removes and APPENDS the replacement; upgrade/enchant in place; remove by index | AddCardToDeck, TransformInDeck :3698, TransformCardAt :3704 | match | R | The opening shuffle has no sort, so deck order decides every opening draw. |
| D2 | CardPileCmd.Add(batch) appends in the enumerable's order (Anointed, PowerCell, Aggression, Summon Forth) | Anointed in order (:2504); PowerCell :3431 and Aggression :10883 descending pile index; PullSovereignBladesToHand :3524 reverse index per pile | MISMATCH | R | M2, M4. |
| D3 | AnswerSelectionsAsVakuu: VakuuCardSelector takes Take(maxSelect) of the list the command built | CombatEngine.AnswerSelectionsAsVakuu :6492 (candidate 0 of the emulator's list) | MISMATCH for draw-pile screens | R | M1. Hand screens (hand order), discard screens (pile order) and generated-card screens (generation order) agree. |
| D4 | Hook dispatch order | hook tables | n/a | F | 94 open order rows in hook_open.txt. |

## 3. MISMATCH and unsure items

### M1. Whispering Earring (Vakuu) takes the wrong card on a draw-pile screen

- Severity: LOW. Only runs holding Whispering Earring that auto-play a draw-pile fetch card on turn 1
  (Secret Weapon, Secret Technique, Seeker Strike; all Colorless, so an Ironclad can hold them).
  Well under 1% of Ironclad A10 runs; every such fight with at least two eligible cards where the top
  one is not the lowest (rarity, id) diverges at once (hand, draw pile, then every later draw).
- Evidence. Game: CardSelectCmd.FromCombatPile, when a selector is set and the pile is the draw pile,
  sorts the eligible cards by rarity then ModelId before the selector sees them; VakuuCardSelector
  returns the first maxSelect of that list. Emulator: OpenDrawPileSelection (CardEffects :4697) and the
  Seeker Strike path (:4640-4650, sorted by pile index) list candidates in pile order, and
  AnswerSelectionsAsVakuu (CombatEngine :6492) answers candidate 0, the topmost draw-pile card.
  Basic cards (the Strikes) sort first in the game, so the game nearly always takes a Strike.
- Real-game test (setup fight, coverage mode, 60 fights): `"setup": [{"cmd":"relic","id":"WHISPERING_EARRING"},
  {"cmd":"card","id":"SECRET_WEAPON"} x4, {"cmd":"card","id":"BLUDGEON"}, {"cmd":"card","id":"CARNAGE"},
  {"cmd":"fight","id":"<any weak encounter>"}]` (cards before `fight` join the deck; Earring plays on turn 1
  before any item after `fight` could run). Fights where Secret Weapon is in the opening hand and the
  draw pile holds a Rare or Uncommon attack above a Strike are the informative ones. Field that should
  differ: `hand` (which attack arrived) and `draw_pile` after the turn-1 step, first at the step the
  Earring plays Secret Weapon.

### M2. Hand order after a batch move from the draw or discard pile (Power Cell, Aggression)

- Severity: LOW-MEDIUM. Power Cell with at least two zero-cost cards in the draw pile on turn 1
  (Anger, Bloodletting, Offering, Clash all qualify), roughly 0.2% of runs; Aggression shows it only
  when its Amount is 2 or more (the power played twice), rarer. The swapped hand order feeds every later random pick
  from the hand (True Grit, Bookmark, Thrash), FromHand lists, the Earring's first-playable walk, and
  the discard order that the next unstable sort ties on.
- Evidence. Game: PowerCell does StableShuffle(...).Take(n) and then CardPileCmd.Add(cards, Hand), which
  appends in the enumerable's (shuffled) order. AggressionPower does UnstableShuffle(...).Take(Amount)
  and adds each card to the hand in that order. Emulator: MoveZeroCostDrawCardsToHandForPowerCell
  (:3431) and MoveDiscardedAttacksToHandForAggression (:10883) first take n from the shuffle, then
  re-sort the picks by DESCENDING pile index "so removal does not shift", and add to the hand in that
  order. When the shuffle puts the lower pile index first, the two hand slots are swapped. (Anointed,
  :2504, does it right: it adjusts the index instead of re-sorting.)
- Real-game test (setup fight, 60 fights): `"setup": [{"cmd":"relic","id":"POWER_CELL"},
  {"cmd":"card","id":"ANGER"} x3, {"cmd":"card","id":"BLOODLETTING"} x3, {"cmd":"fight","id":"<any weak encounter>"}]`.
  Two DIFFERENT zero-cost ids make the swap visible. Field: `hand` order at turn 1 (the first two entries).
  Aggression: after `fight`, `{"cmd":"power","id":"AGGRESSION_POWER","amount":2,"target":"player"}` and
  discard pile `{"cmd":"card","id":"BLUDGEON","pile":"Discard"}`, `CARNAGE`, `ANGER`; then END_TURN; field:
  `hand` order at turn 2 (check the spec accepts target "player"; otherwise play the Aggression card).

### M3. Goopy growth is written back to the wrong deck copy

- Severity: LOW. Paels Claw (or Pael's Growth) enchants Defends with Goopy; each played copy grows by 1.
  Roughly 1-2% of runs reach Act 2 and pick it; the damage is later Block on specific deck positions.
- Evidence. Game: Goopy.AfterCardPlayed increments the played card's own Amount and its DeckVersion's.
  Emulator: CarryGoopyGrowthToTheDeck (RunEngine :1967-1996) has no card identity, so it groups combat
  copies by (def, upgraded), sorts the amounts DESCENDING, and hands them to the Goopy deck cards in
  descending deck-amount order (ties by deck index). With four Goopy Defends all at 1 and the last two
  played, the first two deck positions receive the 2s although they never grew.
- Real-game test: run-level (not a setup fight; needs the deck after a fight). Relic PAELS_CLAW picked up
  with at least four Defends, fight 1, play Defends so that the played ones are not the first deck
  copies, then compare `deck[i].enchantment.amount` per deck index after the fight. A setup fight with
  `{"cmd":"relic","id":"PAELS_CLAW"}, {"cmd":"fight",...}` followed by the deck snapshot at fight end
  is enough if the driver records the deck there.
- Fix shape (mechanism, not symptom): carry a stable deck index on CardInstance for run-deck cards and
  write back by index.

### M4. Summon Forth pulls Sovereign Blades in reverse pile order (Regent)

- Severity: LOW (Regent only; blades are interchangeable unless forged or upgraded differently).
- Evidence. Game: SummonForth adds PlayerCombatState.AllCards.OfType<SovereignBlade>() not in hand;
  AllCards walks Hand, Draw, Discard, Exhaust, Play in forward pile order. Emulator:
  PullSovereignBladesToHand (CardEffects :3524) walks Draw, Discard, Exhaust but each pile from the END
  to the front, so equal blades reach the hand in reverse.
- Real-game test (setup fight, character Regent, flagged cross_character): after `fight`, SOVEREIGN_BLADE
  into Draw (top), Discard, and Exhaust-adjacent if the spec allows, one of them `"upgraded": true`,
  SUMMON_FORTH into Hand, then play it. Field: `hand` order and the forge damage of each blade.

### U1. Claws: batch transform appends in ascending index order (unsure, low)

- Game: CardCmd.Transform(list) removes each original, then re-adds the replacements sorted by
  (pile type, index at removal time), so in the deck they are appended in ascending deck order whatever
  order the player clicked. Astrolabe, NewLeaf, Trial, MorphicGrove and Symbiote transform one card at a
  time (pick order), which the emulator matches. Emulator: DeckSelection.TransformToCarrying appends in
  pick order. Differs only when a player picks Claws' cards out of ascending order, and only changes deck
  order (so later unstable-sort ties and opening draws), not card identities.
- Test: not reachable with the referee's first-n selector (it picks ascending). Needs a scripted
  selector that returns the 5th then the 2nd deck card for Claws (`{"cmd":"relic","id":"CLAWS"}`); field:
  deck order after the pickup.

### U2. Map generation: HashSet<MapPoint> enumeration after removals (unsure, low)

- Game: MapPoint.Children, parents and ActMap.startMapPoints are HashSet<MapPoint>; MapPathPruning
  removes points, and a HashSet that has had a removal reuses the freed slot for the next add, so
  enumeration order can stop being insertion order. The emulator orders by (Col, Row) explicitly.
  Nothing in the code shows an order-dependent enumeration after a removal, and real-run replays
  reproduce maps, but no direct per-seed grid comparison was found in the tests.
- Test (no fight needed): generate the three act maps for 300 seeds in the game and via
  RunNativeExports; compare the node-type grid and the edge sets. A single differing seed is the proof.

### K. Known, not new

- Thieving Hopper stolen-card removal by value (ledger, 2026-10-14, C5-R01): same class (identity).
- The 94 open `order` rows of hook_open.txt (hook dispatch).

## 4. Where the 1,260 "different card upgraded" Codex stops are NOT coming from (negative result)

Every random-upgrade source in the game was compared with the emulator: Whetstone, War Paint, War Hammer,
Sand Castle, Fragrant Mushroom (StableShuffle on the deck), Battleworn Dummy, Doors of Light and Dark,
Reflections, Tablet of Truth, Endless Conveyor, Improvement (NextItem over deck-order lists), Welcome to
Wongos (downgrade). All build the candidate list in deck order and use the game's tie rule
(RunNonCombatEffects.StableShuffleDeck). So the listed sources are not the cause by list order. Two
remaining ordering-adjacent suspects for the walker (tools/emudump/Codex/Walker.cs): the EMULATOR-class
stops may be a deck whose ORDER already differs before the upgrade (a transform appended, a Neow's Bones
curse landing at another position, or a Hopper return), and the FIGHT-DEPENDENT stops are streams a
resolved fight left behind (Niche, CombatCardSelection), which is the walker not playing fights. To
settle it: classify each of the 1,260 stops by the floor's room, relic and event (the ledger's own
suggested check) and compare the deck ORDER, not only the multiset, at the floor before the stop.

Test for the family (setup fight, 60 fights, dense decks): `{"cmd":"card","id":"STRIKE_IRONCLAD"} x6`,
`DEFEND_IRONCLAD x6`, `BASH`, then `{"cmd":"relic","id":"WHETSTONE"}` (and again for WAR_PAINT, SAND_CASTLE,
FRAGRANT_MUSHROOM) BEFORE `fight`, so the pickup's random upgrades happen on the map. Field: the deck's
upgraded flags by position (more than 16 cards exercises the introsort partition tie case).

## 5. What this audit did not or could not check

- Emulator side of the ~25 "F" rows was confirmed by shared helpers, comments and test names, not line by
  line (Cinder, Catastrophe, Uproar, BeatDown, SlimesWeak, BowlbugsNormal, RubyRaiders, SlitheringStrangler,
  Orobas/Pael/Tezcatara pools, ScrollBoxes, FishingRod, WingCharm).
- Map generation was not simulated (U2).
- Pool epoch filters (GetUnlockedCards / FilterThroughEpochs) for transform and reward pools are profile
  dependent and not modelled per the walker's own note; a locked card changes the list the index is
  drawn from.
- Hook dispatch order was cross-referenced only.
- No game, lab or test was run (static audit).
