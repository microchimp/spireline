# How enemies choose moves

A quick static classification of the 111 enemies the emulator models, from the move-selection code in r33hab/sts2 at `b7452170ce1df91de29d3c94acb11d87c7efc708` (`src/Sts2Emulator/Core/EnemyAI.cs`, the `SelectIntent` switch). The emulator is ported from the decompiled game, so this mirrors the game's own `MonsterMoveStateMachine` logic, to the extent the port is faithful.

**Method.** For each `case KE.<Enemy>:` block in `SelectIntent`, and any helper it calls with the AI random stream, check for a random draw (`PickBranch`, `rng.Next`, `rng.NextFloat`, `rng.NextDouble`). Blocks with no draw are fixed patterns (cycles, turn-indexed scripts, or conditions on state). This covers move **choice** only: some fixed-pattern moves still have random targets or effects when they execute.

## Result

| | Enemies |
|---|---|
| Fixed move pattern | 93 |
| Random move choice | 18 |

The 18 with random move choice: DecimillipedeSegment, Exoskeleton, Fabricator, FakeMerchant, FlailKnight, Fogmog, FossilStalker, HunterKiller, Inklet, LeafSlimeS, Mawler, ScrollOfBiting, SlitheringStrangler, SludgeSpinner, SoulNexus, SpectralKnight, TheObscura, TwigSlimeM.

They use the game's weighted-random branch rule, usually with "can't repeat the last move" (`CannotRepeat`) or per-branch repeat caps. The roll happens before the weights are read, so even a forced branch consumes a value from the AI random stream; this matters for bit-exact replay.

**Every act boss found by name uses a fixed pattern:** Ceremonial Beast, The Kin, Vantom (Overgrowth); Lagavulin Matriarch, Soul Fysh, Waterfall Giant (Underdocks); Knowledge Demon, The Insatiable (Hive); Aeonglass, Queen, Test Subject (Glory). Kaiser Crab's parts are named differently in the code and weren't confirmed.

## What it means for search

- In most fights the hidden randomness is the player's own draw order, plus random targets and effects of a few cards and moves.
- For the 18 random-choice enemies, the belief over the next move is a small categorical distribution under the move table's rules. Leak test L7/L8 in the design checks it.
- "Unknown" and other non-attack intents hide what a move does, not necessarily which move comes next. For a fixed-pattern enemy, the next move is known to anyone who knows the pattern, which the design counts as fair rules knowledge.

This is a quick scan, not a proof. Verify against the game before relying on any single enemy's classification.
