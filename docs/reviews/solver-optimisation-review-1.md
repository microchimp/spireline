# Fight solver, optimisation round: design review 1

2026-10-28. Independent, read-only review (no build, test, benchmark or game process was run). Subject: the kernel
lane's plan for the solver's optimisation rounds after S4 and the S6 baseline: (a) the engine step in a solver mode,
(b) the macro draw, (c) dominance and bounds with a non-monotone registry and the irrelevant-play case, (d) dead
end-turn fields if the profile shows lost merges; each before/after on the same positions, harness at zero differences.
Read: `docs/rebuild/FIGHT_SOLVER.md` sections 1-7, 10, 11, 14; the S3 code as landed (fork main `6cd01889`) under
`src/Sts2Emulator/Solver/` with its tests, `tools/solver/harness.py`, `order_readers.json`, `key_fields.json`; the
engine's step path (`CombatEngine.Step`, `StepCore`, `EndTurn`, `ValidActions`, `StateCloning.CopyTo`,
`KernelState.CopyTo`, `KernelGate.Step`, `CardEffects.DrawCards`, `ShuffleDiscardIntoDraw`, `StableShuffle`); the
kernel lane's handoff entries.

## 1. Soundness

**Landed prunings.** Transposition merging is sound on the bisimulation key; a non-exact entry is rightly reused only
at equal turns left. The table holds values only: once branch and bound lands, a cut subtree's value is a bound, and
an entry needs a bound kind or a reused bound is read as a value (a precondition for (c), nothing to fix today).
Multiset hands and potions: sound, off wherever a hand-position reader is present. Draw by value with the steered
layout: sound for draws off the top; the `draw-tie` refusal closes the sorted-pick hole. One mechanism breaks it in the
native build: `SolverChance.FromDiscardShuffle` and `FromStableShuffle` recognise their call site through
`StackTrace.GetFrames()` and `GetMethod()`, which returns null under NativeAOT (`PublishAot` is on in the csproj).
Then a reshuffle inside a step is not steered (every Fisher-Yates call becomes a chance node: n! leaves, each a full
replay, and a later `DrawPending` carries pre-shuffle branches) and the tie check never fires (the 1/4-3/4 odds come
back silently). The C# test host runs under the JIT and cannot see it. Interchangeable enemies is a no-op
(`enemy_order` is `always`), rightly: Back Attack Left/Right, Surrounded, Ravenous (the ally dying first is eaten) and
slot acting order make mirror positions unequal; leave it off. The fixed shown intent is sound: Shriek and Plow
(Terror Eel, Ceremonial Beast) replace the intent with a stun when an unblocked hit crosses a threshold, but that is
state the engine computes, not chance. Subtree reuse and the exactness rule in `NodeValue.Max` are sound.

**Macro draw.** The hypergeometric argument holds only when nothing acts per drawn card in an order-dependent way, the
hand is a multiset, and the count drawn does not depend on the order. The engine's draw loop names the observers:
Hellraiser (auto-plays a drawn Strike inside the draw), Iteration and Pagestorm (extra draws inside the draw: the
prefix's length depends on where they land), Stratagem (a screen inside a reshuffle inside the draw), Speedster when
its per-draw damage can end the fight (fewer cards are then drawn), and, once F11 is on, any `AfterCardDrawn` or
`AfterCardDrawnEarly` listener in the kernel's tables. Safe: Void's energy loss, Automation's count, Corrosive Wave,
Kingly Kick and Punch (per-copy growth), the hand cap, a reshuffle at a fixed count, and the Confused and Slither cost
rolls (chance calls between draws over a fixed sub-multiset, i.i.d. per card). A hand-position reader turns it off; the
hand's flow into the discard is already in the key's `implies`.

**Dominance.** The rule names the ordered quantities but not the equality set, which must be: every key field equal
except player HP, block, energy, the potion multiset (a superset dominates) and each enemy's HP; buffs, relic
counters, every counter and flag equal. Non-monotone readers in the emulator's content: Red Skull (Strength at or
below half HP: lower HP can be better); Orichalcum (block at turn end only when block is 0: block 0 beats block 1);
enemy-HP thresholds that change behaviour discontinuously: Shriek (Vulnerable 99 queued when wounded), Plow, the
half-HP beetle-charge branch in the knight's move table, Doom; Ice Cream makes end-of-turn energy live. Lizard Tail,
Parrying Shield, Body Slam, Fortifier and block keepers are monotone.

**Bounds.** "Block covers every shown intent" is not sound without running the enemy turn: Strength an ally grants
earlier in the turn, multi-hit moves, Frail or Vulnerable applied by the first mover, Constrict-type end-of-turn
damage, unblockable HP loss. The one cheap sound bound is on the utility: when no heal, max-HP gain or potion gain is
reachable in the combat (`HealPlayer` sites: three in CardEffects, four in RelicEffects, one potion; two `PlayerMaxHp`
gain sites; one potion-gain site; plus end-of-combat heals such as Burning Blood as a constant if the winning step
applies them before the terminal is scored), a node's value is at most L0(HP + end heal, potions). The bound is tight:
an exact move reaching it (a kill with no HP lost) closes the node, so "lethal-first termination" becomes lossless.

**Irrelevant plays and dead end-turn fields** are one rule. "Defend, end turn" and "end turn" differ after the next
turn's start only in fields nothing reads (per-combat counters: `CardsPlayedThisCombat` is read by one card and Gold
Axe, `CardsDrawnThisCombat` and `CardsGeneratedThisCombat` by one each), and before it in block (dead when no damage
comes this enemy turn and no Orichalcum, Parrying Shield, Juggernaut-type reader or keeper is present), energy (dead
without Ice Cream) and per-turn counters (reset at turn start). The exactness condition is the same for both: the
masked field has no reader in this combat.

**What the 400 recipes exercise.** The 50 corpus fixtures are Strike, Defend, Bash, Ascender's Bane decks with Burning
Blood; the rest is the twelve-card MIX list, seven screen cards and the two owner's fights. Draw piles are cut to 0-4
cards, enemies to 2-14 HP, horizon 0 or 1. Covered: commuting plays, multiset hands, draws by value over a small
middle, five screen kinds, enemy rolls, Shriek (one fixture). Not covered: any on-draw observer, a five-card draw over
six or more values, a reshuffle inside a draw, any relic but Burning Blood, potions in play, Plow, the beetle charge,
act 2-3 decks. A wrong macro draw, dominance or dead-field rule passes this gate.

## 2. The registries by scan

`scan_order_reads.py` already does the hard part: holder attribution by case label and a call graph over the six
engine files, a source sha, a test that fails on an unclassed read. The non-monotone and dead-field registries are the
same scan with another needle: every read of `PlayerHp`, `PlayerMaxHp`, `PlayerBlock`, `Energy`, `PotionSlots`,
`enemy.Hp`, `enemy.MaxHp` and of each `*ThisTurn` and `*ThisCombat` field, classed by shape: a comparison against a
threshold is a non-monotone candidate (hand-classed with a why, as `free` reads are today), an additive use is
monotone, a counter read names a reader for the dead-field rule. A quantity whose non-monotone holders are absent from
the combat is monotone there; a field with no holder present is dead there (the `Readers.On` logic). A scan misses:
(1) Core2's handlers and the OldState views, which read the same quantities under other names outside the six files,
so the scan must cover Core2/Models and the adapters or the registry is wrong for every family switched on;
(2) holders chosen by a string switch on the card's name rather than a case label (`GrowKinglyCardOnDraw` is one);
(3) end-of-combat effects, which belong in the bound's constant, not a reader list; (4) monotonicity is a property
of the use, which no regex judges: the human class with a why stays, per site.

## 3. The engine step

Where the microseconds go, from reading, not measuring:

- *Two full clones per run.* `CombatEngine.Step` snapshots `Before = state.Clone()` and `RngBefore` for the
  stopped-step replay on every step whose stream is a `CountingRandom`; `Successors.Expand` has already cloned the
  parent and laid out its pile. Each clone copies about 110 scalars, 15 lists, every enemy, and under core2 the
  kernel's hook-action list, stops, waits, command log, progress and sequence dictionary, all excluded from the key as
  unread sequencing. Estimate 5-15 microseconds per clone on old, 10-30 under core2.
- *The step body.* The end-turn step (enemy turn plus next turn's start) is the dear one; a play step is a fraction of
  it. `Baseline` allocates a roster array per step; `StepInProgress` carries four lists; the trace hooks are null
  checks; `ValidActions` is not recomputed inside the step.
- *The solver's own per-run cost*, of a clone's order: `DrawSteer.Layout` encodes every middle card through a fresh
  `KeyWriter` and sorts; `CheckRest` walks the pile and `CheckTie` builds a dictionary on every `Next(0, n >= 2)` call
  on any stream, enemy rolls included; a reshuffle takes a `StackTrace`.
- *Per node*: the key is encoded and SHA-256-hashed twice per child (to group outcomes, then on entry to `Node`);
  `Readers.OrderedPiles` (every category over every card) runs three times per node; `Rational` is BigInteger-backed
  with a GCD per operation, five operations per outcome.
- *Is copy-plus-replay larger than the engine?* Per run, no: clones and layout are perhaps a third of a run. Per node,
  yes, and structurally: a chance tree of depth L is replayed from the step's start once per internal node and once
  per leaf, so the enemy turn is re-run once per draw outcome, and the sequential draw makes L the number of cards
  drawn. On the harness's trimmed piles that is the measured 2.6 runs per node; on a real deck an end-turn move drawing
  five from a middle of six to ten values is 10^3 to 10^5 runs (d^k ordered sequences, times d/(d-1) for the internal
  replays), each a full enemy turn. The engine step is the ceiling per run; the run count is the lever.

A solver mode can safely skip: the engine's pre-step snapshot (made lazy: run without a record; if a screen is raised,
drop the copy and re-run that one run with the record on, which is the replay-from-start the solver already does); the
kernel's sequencing lists in solver copies; the tie check on streams other than Shuffle and CardSelection; the
stack-walk site detection. It must not skip `OnDrawPileTake`, hook ordering, or anything the byte proof covers; the
gate is the corpus byte identity with the mode off, as for the chance hook, plus the harness.

## 4. Order and expected multipliers

- *Macro draw*: 10-100x fewer engine runs per end-turn move on real decks (d^k ordered sequences against C(d+k-1, k)
  sub-multisets, plus the internal replays), nothing on play moves. The sizing figures (58%, 72%, 33%) were computed
  with multiset hands, so they already assume it; without it a horizon-1 solve on an act-2 deck costs seconds. First
  lever; it earns a second round (the reshuffle inside the draw, the F11 listener check).
- *Engine step*: 1.5-2.5x per run from the second clone, the kernel copies under core2 and the allocations; the
  kernel's dispatch overhead (core2 steps -24%, sims -31%) is a separate project. The solver's per-node costs (double
  keying, SHA-256, `OrderedPiles`, `Rational`) belong in the same round: one profile, one before/after.
- *Dead end-turn fields with the irrelevant play*: collapses the ordering and count of filler plays; 2-5x on nodes in
  turns with slack energy and no attack, and, as a pre-step key on the end-turn move, it also removes duplicated
  end-turn expansions, the dear ones. Third, once the merge audit (change 2) says how many merges are lost.
- *Dominance and bounds*: the tight utility bound with lethal closure is cheap, sound and cuts every node where a kill
  at no HP loss exists (the last turn of most won fights). Generic dominance is smaller, needs a registry per quantity,
  and must stay below the root (root move values are the policy label and the harness compares every one). Fourth: the
  bound first, dominance only if the audit shows siblings differing only in the ordered quantities.
- The orchestrator's order is right in spirit (the profile decides) and wrong in its default: the profile must be
  taken on real decisions (the S6 sample), not on the harness, whose piles hide the draw explosion. It should report
  runs per move by kind (play, potion, end turn, screen), chance levels per run, leaves per end-turn move, and a
  sampling split between `StepCore`, clones, key, `Rational` and the chance hook's checks.

## 5. What the plan misses

- *Lethal and full-retention closure* as a lossless bound (section 1). Risk: a missed heal source makes a closed node
  wrong; gate with the harness and a scan assertion that every `HealPlayer` and max-HP site is classed.
- *The end-turn seam.* The draw's chance tree branches after the enemy turn. If the engine can stop at the turn
  boundary (a held turn-start phase already exists for relic screens), the enemy turn runs once per intent-roll leaf
  and the turn start once per draw outcome, independently of the macro draw. Risk: a seam differing from the single
  step by a byte; gate on the byte proof. Price it after the macro draw lands.
- *Wide rolls as horizon leaves* instead of refusals (14 of 400 harness positions; more on real decisions with card
  generation): exact_mass accounting, no exactness risk. *Expansion caching* for the potion curve (the design's shared
  expansion is not built): cache `Successors.Expand` by (key, move), at least for end-turn moves.
- *Parallel root splitting*: feasible (the shuffle scratch and the running-step slot are thread-static) with a table
  per thread; no exactness risk; low priority while the lab parallelises by process.
- *Energy dominance* is subsumed by the dead-field rule, *intent-aware pruning* by the shown-intent state plus the
  bound, *phase-aware keys* by Turn, PlayerTurn and the table's turns-left. None needs a rule of its own.

## 6. Verdict: CHANGES

1. **Fix the call-site detection before S4's exports are trusted.** Replace `FromDiscardShuffle` and
   `FromStableShuffle` with an explicit site: a thread-static marker set and cleared by `ShuffleDiscardIntoDraw` and
   `StableShuffle`, or `ChanceCall.Site` filled at those two call sites. Add a test that solves a reshuffling harness
   position and a draw-tie position through the published native library; S4's "native equals EmuDump" gate must run
   EmuDump under the JIT, or it compares two wrong answers.
2. **Baseline on real positions with counters, before any round.** On the S6 sample: runs per move by kind, chance
   levels per run, leaves per end-turn move, the sampling split of section 4, and a merge audit: a second hash per
   end-turn node with the candidate dead fields masked (block, energy, per-turn counters, unread per-combat counters),
   reporting distinct masked keys against distinct full keys. The audit decides (d); the counters decide the order.
3. **Macro draw first, wired as a k-prefix layout in `DrawSteer`.** `DrawPending` reports how many rest cards the run
   took; branch over the sub-multisets of that size (hypergeometric, canonical order within the prefix), keeping the
   reshuffle epoch; off when the hand is ordered or an observer is present (Hellraiser, Iteration, Pagestorm,
   Stratagem, Speedster able to kill, any F11 `AfterCardDrawn` listener), the observer list a scanned registry with a
   why per entry. Harness: recipes with a five-card draw over six or more values and one per observer, both engines;
   `ChanceModelTests` positions on the macro path (the only test that can see a wrong hypergeometric; the reference
   shares `Expand`); a pruned-against-pruned comparison (macro on and off) for positions past the reference cap.
4. **Engine round scope.** The lazy pre-step record; no kernel sequencing copies in solver copies; the tie check only
   on the Shuffle and CardSelection streams; the key passed into `Node` (one encode per child); a non-cryptographic
   128-bit hash in place of SHA-256 with the debug full-bytes compare kept; `OrderedPiles` cached per card-id set;
   `Rational` profiled and, if above a tenth of a node, production values in double compared at 1e-12 while
   `Reference` keeps `Rational`. Gate: the corpus byte proof with the mode off, the harness, before/after on the S6
   sample.
5. **Bounds before dominance, both below the root.** The tight utility bound from a scanned heal, max-HP and
   potion-gain registry plus end-of-combat heal constants; lethal closure at max nodes; branch and bound and dominance
   only at depth 1 and below; table entries carry a bound kind before any bound is stored.
6. **One dead-field mechanism.** A pre-step end-turn key with the dead fields masked (block with no incoming damage and
   no block reader or keeper, energy without Ice Cream, per-turn counters, per-combat counters without a reader in this
   combat), used as a move-level transposition on the end-turn expansion. The irrelevant-play case falls out of it.
7. **Registries by scan.** Extend `scan_order_reads.py` to quantity and counter reads with shape classes, covering
   Core2/Models and the OldState adapters; a test that fails on an unclassed read, as today; dominance's equality set
   written down as "every key field except the ordered ones".
8. **Harness coverage for the rules.** Recipes holding Red Skull, Orichalcum, Ice Cream, Parrying Shield, Shriek, Plow,
   the half-HP charge, Doom and a potion in play, each at horizon 1 on both engines, before (c) or (d) is enabled.
9. **Wide rolls become horizon leaves** in S4 or S6.
