# Play or deck? Generation 11's fight player on the humans' own boss starts (2026-11-05)

Written 2026-11-05 by the Sonnet worker for milestone 1 of the strategy memo (`docs/design/2026-11-05-strategy-rethink.md`, section 5.1 and cause 1 of section 2.2). Games were played on the copy (not the game) from 09:00Z to 14:53Z. Human data: Spire Codex public run export for v0.107.1 (spire-codex.com), aggregates only, no cell under 20 runs, no run is named. Every figure is measured (file named in section 7) or arithmetic on measured figures; what is not verified is in section 6.

## 0. The answer

**It is the play at the first boss and half and half at the second.** Generation 11's fight player (the gym champion v2 at the normal search, `a3-v1`) played 300 Act 1 and 300 Act 2 boss starts from the human fifth 4, twice each, and the humans' real outcomes are the comparison on the same starts.

1. **Act 1 boss, play.** The player wins **52.5 in 100** (95% interval 47.8 to 57.2) of the humans' starts; the humans won **73.7** (68.7 to 78.3) of the same fights, so the player is 21.2 points (16.0 to 26.2) below them with their own deck, relics, HP and potions. On its own boss starts (generation 11's real runs of 11-03 to 11-05 replayed on the copy, same engine and draws) it wins 57.2 (52.8 to 61.8): the humans' hands are **not** better for it (the hand effect is -4.7 points, -11.2 to +2.0). The whole Act 1 boss gap is the play.
2. **Act 2 boss, play and hand in equal parts.** The player wins **44.4** (39.7 to 49.3) of the humans' starts against their **74.3** (69.6 to 79.4): a play effect of 29.9 points (24.3 to 35.3). On its own starts it wins **14.7** (10.3 to 19.5): the hand effect is 29.8 points (23.2 to 36.2). Midway between its 14.7 and their 74.3 is 44.5; it wins 44.4. At the door the humans' hands differ from the player's in potions held (1.68 against 0.48), relics (11.6 against 8.2) and HP (72% against 62% of max), not in the number of cards (26.1 against 27.3).
3. **Thinking time** (same starts and draws, paired): four times the simulations (x4) adds **+4.2** (+1.7 to +6.7) at the Act 1 boss and **+6.2** (+3.0 to +9.5) at the Act 2 boss; sixteen times (x16) adds **+10.6** (+6.6 to +14.8) and **+10.7** (+6.6 to +14.6) on the 227 and 219 starts it reached. At x16 the player wins 64.3 and 54.1, still 11.5 and 18.5 points under the humans on the same starts: more thinking time closes about a half (Act 1) and a third (Act 2) of the play gap.
4. **For the milestone order:** neither extreme of the memo's rule. Act 1 is play only; Act 2 is half play and half hand. So milestone 7 (the fight half) should not wait behind the deck milestones 3 to 6: it takes its slot after milestone 2, as the rule's play branch says, and the deck milestones stay because at the Act 2 boss they are worth as much (section 4). The memo's 3-point test for a stakes schedule is met on human boss starts at x4 in both acts by the point estimate.
5. **Biggest caveat:** the human starts are rebuilt on the copy and the copy is not the game (section 5); the play gap is the figure that carries both. The same player's own-start rates on the copy (57.2 and 14.7) sit next to the game's nightly 57 and 19, which is some comfort.

**For the owner.** We put the fighting program into real players' boss fights, with the decks, health and potions those players had, and let it play each fight twice. At the first boss it wins about 52 fights in 100 where the humans won 74, so the fighting itself is behind and its own decks are no worse than theirs. At the second boss it wins 44 where they won 74, but on its own decks it wins 15, so the fighting and the preparation (potions, health, relics) each account for half of the gap. Thinking sixteen times as long adds about 10 wins in 100 at either boss: it helps, it does not close the gap.

## 1. The question

The memo says the second boss is beaten in 19 fights of 100 that reach it by the player and 76 by humans, and the 11-02 fits put the gap partly on the play and partly on the hand brought to the door (deck, relics, HP, potions). Those were associations in fitted models. This note is the direct test the memo asked for: put generation 11's fight player into the humans' own boss fights and compare its win rate with theirs on the same starts. If the player wins near the humans' 74 and 76, the hand explains the gap and the deck comes first. If it wins near its own, the play explains it. A third reading is added: what more thinking time buys at the boss.

## 2. Method

**Starts.** `rl/human_starts.py` rebuilds on the copy the opening of each human boss fight: the deck, relics, potions, HP and max HP the human walked in with, the same boss, floor 17 or 33 (8,216 Act 1 and 3,948 Act 2 boss records over the four training fifths; `docs/rl/HUMAN_STARTS.md`). The set is the `human-starts` stem of `rl/practice_mix.py` `FILES` (`referee/gym-loop/starts/human-starts.jsonl`, with its index and list).

**Fifth rule.** A run's fifth is `human_starts.exam_bucket(run id)`: the first 32 bits of sha256 of `spireline-d38-exam-fifth|` plus the id, modulo 5. Bucket 0 and the ids file are the exam fifth (`is_exam`, the union): never read, and the sampler asserts that none of its runs is in the sample. `counts.json` (`referee/backlog/scratch-strategy/`) labels the training fifths `train<bucket>`, so **fifth 4 is bucket 4**: 2,903 finished vanilla runs, 324 wins. It holds 1,996 rebuilt Act 1 boss starts (by boss 354, 290, 302, 361, 373, 316) and 982 Act 2 boss starts (332, 313, 337).

**Sample.** Seed 20261105; within each boss the starts are ordered by sha256 of the seed and the start id and the first 50 (Act 1, six bosses) or 100 (Act 2, three bosses) are taken: **300 Act 1 and 300 Act 2 boss starts**, equal allocation by boss (`sample.json`).

**The player.** "Generation 11's fight player" is the combat prior of the gym's champion `v2` (checkpoint c0019), the very weights and net that `agent/gen11/candidate` holds (policy sha256 `64d057e1…`, net `9007e005…`, same search settings: c_puct 0.2, prior_min_visits 3), searched live. The search arms are the fight gym's (`rl/fight_gym.py arm_settings`, the arms D37's M2 used): **a3-v1** (`rl/search_configs.py`: 30 simulations a move, 120 where a target or a choice screen is asked, c 0.2), **x4** (every simulation count and the safety clock times 4: 120 a move, 480 at a target or choice screen) and **x16** (times 16: 480 and 1,920). `search_configs.py` itself holds no scaled config. v2 was promoted on 10-31, before the human starts entered the practice (2026-11-04), so it has never trained on a human start; later checkpoints have, which is why the player in play is v2, not the loop's newest.

**Draws and pairing.** Two draws a start (j = 0, 1). A game loads the start's snapshot and forks it with fresh hidden information (draw order and streams) from seeds derived from (start id, j, a namespace, the decision index) and never from the arm, so the three arms see the same shuffles and the same per-decision search seeds. The play path is the fight exam's (`rl/fight_exam.py`, `fight_gym.play_steps` in the lockstep processes with the batched prior server); a game past three times the gym's deadline (ten times the arm's mean) or 400 decisions would be capped and lost (none was).

**The run.** One driver (`pod_run.py`, `referee/backlog/play-or-deck/`; nothing in the repos was edited): 10 lockstep worker processes holding 8 games each, BelowNormal in a Job Object, one emulator each, a spawn pool, the prior server on the card under its own `GPU_OK` tag, a `play-or-deck` QUIET.lock line held while games ran (dropped during the pauses below and for 14 s at the hand-over to the reference arm). A pilot of 20 starts a config and act (draw 0) timed the arms (own seconds a game, Act 1 / Act 2: a3-v1 5.3 / 9.0, x4 20.6 / 43.5, x16 78.5 / 144.5); the whole design (a3-v1 and x4 on all 600 starts, x16 on all 600) fitted the 21,600 s left at 0.9 efficiency by that timing (estimate 179,000 process-seconds against 194,000). The tasks ran in the order a3-v1, x4, then x16 in start-rank order interleaved across the acts, so that any prefix of x16 is stratified and paired. x16 was stopped on purpose at 14:45Z to leave room for the reference arm and this note, so it holds 884 of its 1,200 games: the first 227 Act 1 and 219 Act 2 starts of the stratified order (some with one draw only; every x16 comparison is on the (start, draw) games both arms played). The run was paused four times by `main.lock` (11:09, 13:15, 13:19 and 13:51Z; it resumed within a minute or two each time under its own guard, but the games in flight at each stop, up to 80 of them, were played again from their start), and eight times a worker died or was killed after 300 s with no step (section 3.6). A first launch at 09:00Z lost all its rows to a bug of mine in a row field, raised after each game was played (about 15 minutes of the ten processes; the rows are kept as `rows-aborted-typeerror.jsonl` and not used); the second launch at 09:16Z played the pilot again, and its timings are the ones above. The library is a copy of the fork's published native library (`wt-lockstep-hidden/out`, sha256 `bfa2aefe…`, engine tag `bfa2aefeb34b`, API 39, engine `core2`) with the code of fork main `5b365a02` in a private worktree; the shared checkout's own `out/` is from 10-15 and fails the freshness and API checks.

**The humans on the same starts.** A pass over the corpus (`human_outcomes.py`, one process, 153 s) read the outcome of each sampled start's run with the rule of `count_corpus.py`: the boss was beaten when the run goes on to the next act (or wins, in Act 3). On the 600 starts this gives 73.7% of 300 (Act 1) and 74.7% of 300 (Act 2; 74.3% of the 296 that stay after the crash reading below); over every rebuilt fifth-4 boss fight the rates are 74.2 (1,579 of 2,127, Act 1) and 74.5 (805 of 1,081, Act 2), and `counts.json` has 74.2 and 74.7 for all train4 boss fights. So the sample is typical. HP left is the HP recorded after the boss floor.

**Intervals.** Percentile bootstrap over starts, resampled within boss (3,000 resamples; 1,500 on the sensitivity reading and 750 in the per-boss cells; seed 20261105); a start's two draws are averaged first. A paired difference is, per start, the mean over the draws both arms played of one arm's win minus the other's. The gap to the humans is the mean over starts of (our two-draw rate minus the human's 0 or 1). A difference between two sets of starts (below) resamples each set within boss separately.

**Crashes.** The copy raised an exception or hung on a few Act 2 starts (section 3.6). Primary reading: a start with a crash in any arm is dropped from every arm and from the humans, so every rate is on the same starts. Sensitivity reading: the crashed game counts as lost and the start stays. A game that hit the time or decision cap would be lost in both.

**Reference arm.** To read the hand's effect on one engine and one play path, the same player at a3-v1 also played generation 11's own boss starts: the real-game runs of the nights of 11-03, 11-04 and 11-05 (agent g11) replayed on the copy and held in the gym's start set; Act 1 50 starts a boss, Act 2 every such start; draws 0 and 1, the same namespace (`pod_own.py`). All 948 games (474 starts: 300 Act 1, 174 Act 2) have rows, none capped or crashed; the arm ran from 14:45Z to 14:53Z. The fight exam (v2, a3-v1, four draws on its clean starts from all nights, engine `1b3d1f01c90b` of 11-04) gives a second own-start figure on an older engine.

## 3. Results

### 3.1 Win rate per act

Humans: the same 300 starts' real outcomes. Gen 11: the fight player at three search budgets, two draws a start. The x16 rows are the starts it reached (a prefix of the stratified order), see section 2.

**Primary reading.**

| act | who | win rate % (95% interval) | starts | games |
|---|---|---|---|---|
| 1 | humans, same starts | 73.7 (68.7 to 78.3) | 300 | 300 |
| 1 | gen 11 at a3-v1 (30 sims) | 52.5 (47.8 to 57.2) | 300 | 600 |
| 1 | gen 11 at x4 (120 sims) | 56.7 (51.8 to 61.5) | 300 | 600 |
| 1 | gen 11 at x16 (480 sims) | 64.3 (59.3 to 69.4) | 227 | 448 |
| 2 | humans, same starts | 74.3 (69.6 to 79.4) | 296 | 296 |
| 2 | gen 11 at a3-v1 (30 sims) | 44.4 (39.7 to 49.3) | 296 | 592 |
| 2 | gen 11 at x4 (120 sims) | 50.7 (45.9 to 55.6) | 296 | 592 |
| 2 | gen 11 at x16 (480 sims) | 54.1 (48.2 to 59.6) | 219 | 430 |

**Sensitivity reading.**

| act | who | win rate % (95% interval) | starts | games |
|---|---|---|---|---|
| 1 | humans, same starts | 73.7 (68.7 to 78.3) | 300 | 300 |
| 1 | gen 11 at a3-v1 (30 sims) | 52.5 (47.7 to 57.3) | 300 | 600 |
| 1 | gen 11 at x4 (120 sims) | 56.7 (52.0 to 61.7) | 300 | 600 |
| 1 | gen 11 at x16 (480 sims) | 64.3 (59.3 to 69.5) | 227 | 448 |
| 2 | humans, same starts | 74.7 (69.7 to 79.3) | 300 | 300 |
| 2 | gen 11 at a3-v1 (30 sims) | 44.0 (39.2 to 48.7) | 300 | 600 |
| 2 | gen 11 at x4 (120 sims) | 50.3 (45.5 to 54.8) | 300 | 600 |
| 2 | gen 11 at x16 (480 sims) | 53.6 (48.0 to 59.2) | 222 | 436 |

### 3.2 What more thinking time buys (paired, same starts and draws)

Differences in points of win rate; the rates beside them are on the starts both arms played.

**Primary reading.**

| act | comparison | difference (95% interval) | starts | rates on those starts (first, second) | games where only the first won / only the second won |
|---|---|---|---|---|---|
| 1 | x4 minus a3-v1 | +4.2 (+1.7 to +6.7) | 300 | 56.7 / 52.5 | 46 / 21 |
| 1 | x16 minus a3-v1 | +10.6 (+6.6 to +14.8) | 227 | 64.3 / 53.7 | 63 / 18 |
| 1 | x16 minus x4 | +5.7 (+2.2 to +9.5) | 227 | 64.3 / 58.6 | 44 / 19 |
| 2 | x4 minus a3-v1 | +6.2 (+3.0 to +9.5) | 296 | 50.7 / 44.4 | 67 / 30 |
| 2 | x16 minus a3-v1 | +10.7 (+6.6 to +14.6) | 219 | 54.1 / 43.4 | 65 / 20 |
| 2 | x16 minus x4 | +5.9 (+2.1 to +9.8) | 219 | 54.1 / 48.2 | 52 / 27 |

**Sensitivity reading.**

| act | comparison | difference (95% interval) | starts | rates on those starts (first, second) | games where only the first won / only the second won |
|---|---|---|---|---|---|
| 1 | x4 minus a3-v1 | +4.2 (+1.5 to +6.8) | 300 | 56.7 / 52.5 | 46 / 21 |
| 1 | x16 minus a3-v1 | +10.6 (+6.5 to +14.3) | 227 | 64.3 / 53.7 | 63 / 18 |
| 1 | x16 minus x4 | +5.7 (+2.2 to +9.7) | 227 | 64.3 / 58.6 | 44 / 19 |
| 2 | x4 minus a3-v1 | +6.3 (+3.0 to +9.5) | 300 | 50.3 / 44.0 | 69 / 31 |
| 2 | x16 minus a3-v1 | +10.6 (+6.5 to +14.6) | 222 | 53.6 / 43.0 | 66 / 21 |
| 2 | x16 minus x4 | +5.9 (+2.0 to +9.9) | 222 | 53.6 / 47.7 | 52 / 27 |

### 3.3 Gen 11 against the humans on the same starts

Gen 11 minus the humans on the same starts, in points of win rate (primary reading); negative means below the humans.

| act | arm | difference (95% interval) | starts |
|---|---|---|---|
| 1 | a3-v1 | -21.2 (-26.2 to -16.0) | 300 |
| 1 | x4 | -17.0 (-22.0 to -12.2) | 300 |
| 1 | x16 | -11.5 (-17.2 to -5.7) | 227 |
| 2 | a3-v1 | -29.9 (-35.3 to -24.3) | 296 |
| 2 | x4 | -23.6 (-29.2 to -18.1) | 296 |
| 2 | x16 | -18.5 (-24.9 to -12.1) | 219 |

### 3.4 Where the gap sits: play against hand

Play effect: how far the player is below the humans on the identical starts. Hand effect: how far the same player is above itself when it walks in with the humans' hands instead of its own (two sets of starts, resampled separately). Whole gap: their sum.

**Primary reading.**

| act | humans, human starts | gen 11 on human starts | gen 11 on its own starts (g11 nights) | play effect: humans minus gen 11, same human starts | hand effect: gen 11 on human starts minus on its own starts | whole gap: humans minus gen 11 on its own starts |
|---|---|---|---|---|---|---|
| 1 | 73.7 (68.7 to 78.3) | 52.5 (47.8 to 57.2) | 57.2 (52.8 to 61.8); 300 starts | +21.2 (+16.0 to +26.2) | -4.7 (-11.2 to +2.0) | +16.5 (+9.8 to +23.3) |
| 2 | 74.3 (69.6 to 79.4) | 44.4 (39.7 to 49.3) | 14.7 (10.3 to 19.5); 174 starts | +29.9 (+24.3 to +35.3) | +29.8 (+23.2 to +36.2) | +59.7 (+53.0 to +66.2) |

**Sensitivity reading.**

| act | humans, human starts | gen 11 on human starts | gen 11 on its own starts (g11 nights) | play effect: humans minus gen 11, same human starts | hand effect: gen 11 on human starts minus on its own starts | whole gap: humans minus gen 11 on its own starts |
|---|---|---|---|---|---|---|
| 1 | 73.7 (68.7 to 78.3) | 52.5 (47.7 to 57.3) | 57.2 (52.3 to 61.8); 300 starts | +21.2 (+16.3 to +26.2) | -4.7 (-11.3 to +1.5) | +16.5 (+9.7 to +23.4) |
| 2 | 74.7 (69.7 to 79.3) | 44.0 (39.2 to 48.7) | 14.7 (10.6 to 19.0); 174 starts | +30.7 (+25.0 to +36.2) | +29.3 (+23.0 to +35.9) | +60.0 (+53.2 to +66.6) |

### 3.5 By boss

Win rate %, 95% interval, starts in the cell (primary reading). Intervals are wide: a cell holds 50 (Act 1) or 100 (Act 2) starts.

| act | boss | humans | a3-v1 | x4 | x16 |
|---|---|---|---|---|---|
| 1 | Ceremonial Beast | 86 (76 to 94); 50 | 71 (60 to 81); 50 | 76 (66 to 86); 50 | 83 (73 to 92); 39 |
| 1 | Lagavulin Matriarch | 76 (64 to 88); 50 | 58 (45 to 70); 50 | 58 (45 to 70); 50 | 68 (55 to 81); 39 |
| 1 | Soul Fysh | 74 (61 to 86); 50 | 55 (45 to 65); 50 | 63 (53 to 73); 50 | 69 (55 to 82); 39 |
| 1 | The Kin | 62 (48 to 76); 50 | 45 (33 to 58); 50 | 50 (38 to 63); 50 | 61 (47 to 76); 35 |
| 1 | Vantom | 74 (62 to 86); 50 | 48 (36 to 59); 50 | 54 (43 to 66); 50 | 55 (42 to 67); 38 |
| 1 | Waterfall Giant | 70 (58 to 82); 50 | 38 (27 to 49); 50 | 39 (26 to 53); 50 | 47 (34 to 62); 37 |
| 2 | Kaiser Crab | 68 (59 to 77); 100 | 29 (22 to 37); 100 | 36 (28 to 44); 100 | 35 (26 to 44); 71 |
| 2 | Knowledge Demon | 68 (58 to 77); 96 | 50 (41 to 58); 96 | 56 (48 to 65); 96 | 58 (47 to 67); 72 |
| 2 | The Insatiable | 87 (80 to 93); 100 | 55 (46 to 62); 100 | 60 (53 to 69); 100 | 68 (60 to 77); 76 |

### 3.6 Caps and crashes

| arm and act | games | engine crashes | capped by time or decisions |
|---|---|---|---|
| a3-v1, act1 | 600 | 0 | 0 |
| a3-v1, act2 | 600 | 2 | 0 |
| x4, act1 | 600 | 0 | 0 |
| x4, act2 | 600 | 2 | 0 |
| x16, act1 | 448 | 0 | 0 |
| x16, act2 | 436 | 4 | 0 |

Starts with a crash in any arm: none of the 300 Act 1 starts, 4 of the 300 Act 2 starts (the primary reading drops them).

### 3.7 By the hand brought in, and by the rebuild's flags

Win rate % by the hand the start walks in with (primary reading; cells under 20 starts not shown). The hand matters for both, and the humans lead in every cell.

| act | hand | starts | humans | a3-v1 | x4 |
|---|---|---|---|---|---|
| 1 | HP share: under 50% | 52 | 53.8 | 23.1 | 23.1 |
| 1 | HP share: 50 to 75% | 141 | 73.0 | 49.3 | 54.6 |
| 1 | HP share: 75% and over | 107 | 84.1 | 71.0 | 75.7 |
| 1 | potions held: 0 | 25 | 60.0 | 38.0 | 48.0 |
| 1 | potions held: 1 | 120 | 66.7 | 46.2 | 49.2 |
| 1 | potions held: 2 or more | 155 | 81.3 | 59.7 | 63.9 |
| 2 | HP share: under 50% | 43 | 62.8 | 27.9 | 32.6 |
| 2 | HP share: 50 to 75% | 120 | 75.0 | 36.2 | 45.0 |
| 2 | HP share: 75% and over | 133 | 77.4 | 57.1 | 61.7 |
| 2 | potions held: 0 | 33 | 57.6 | 37.9 | 37.9 |
| 2 | potions held: 1 | 83 | 65.1 | 36.1 | 39.2 |
| 2 | potions held: 2 or more | 180 | 81.7 | 49.4 | 58.3 |

Win rate % by the rebuild's approximation flags (primary reading; a flagged start is one whose enchantment growth the record cannot give). A flagged start is no harder for our player.

| act | flag | starts | a3-v1 % | humans % |
|---|---|---|---|---|
| 1 | enchanted=True | 114 | 51.8 | 75.4 |
| 1 | enchanted=False | 186 | 53.0 | 72.6 |
| 1 | upgrade_level_above_1=False | 300 | 52.5 | 73.7 |
| 2 | enchanted=True | 189 | 45.8 | 76.7 |
| 2 | enchanted=False | 107 | 42.1 | 70.1 |
| 2 | upgrade_level_above_1=False | 296 | 44.4 | 74.3 |

### 3.8 HP left, potions, turns

Primary reading. The humans' figure is the HP the corpus records after the boss floor (whether before or after the boss reward is not checked); ours is the HP when the fight ends.

| act | who | wins | HP left, mean | % of max HP | potions used a game | turns a game |
|---|---|---|---|---|---|---|
| 1 | humans (HP after the boss floor, as recorded) | 221 | 29.6 | 36.4 | n/a | n/a |
| 1 | a3-v1 | 315 | 19.3 | 23.8 | 1.45 | 8.3 |
| 1 | x4 | 340 | 22.2 | 27.3 | 1.44 | 8.2 |
| 1 | x16 | 288 | 22.3 | 27.2 | 1.44 | 8.3 |
| 2 | humans (HP after the boss floor, as recorded) | 220 | 32.8 | 38.9 | n/a | n/a |
| 2 | a3-v1 | 263 | 24.0 | 28.2 | 1.61 | 6.9 |
| 2 | x4 | 300 | 24.1 | 28.4 | 1.63 | 6.9 |
| 2 | x16 | 233 | 25.0 | 29.5 | 1.63 | 6.7 |

The reference arm, a3-v1 on generation 11's own boss starts (this run's engine), with the hand those starts bring:

| act | starts | games | win rate % | HP left after a win | % of max | potions used a game | start HP share | potions | relics | deck cards |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 300 | 600 | 57.2 (52.8 to 61.8) | 20.0 | 24.0 | 0.83 | 78.9% | 0.85 | 4.3 | 18.7 |
| 2 | 174 | 348 | 14.7 (10.3 to 19.5) | 13.7 | 15.8 | 0.45 | 61.7% | 0.48 | 8.2 | 27.3 |

### 3.9 The hands, and the fight exam's own-start reading

The hand at the boss door (means): the human sample against the fight exam's own starts (clean starts of all nights, 4 draws; the generation 11 own starts of the reference arm are in 3.8).

| act | who | starts | HP share | potions | relics | deck cards |
|---|---|---|---|---|---|---|
| 1 | human sample | 300 | 67.8% | 1.47 | 6.0 | 19.5 |
| 1 | gen 11's own starts (exam) | 590 | 77.1% | 0.77 | 4.2 | 18.8 |
| 2 | human sample | 296 | 71.5% | 1.68 | 11.6 | 26.1 |
| 2 | gen 11's own starts (exam) | 103 | 63.3% | 0.61 | 8.2 | 26.6 |

The same player on its own boss starts in the fight exam (v2 at a3-v1, four draws, engine `1b3d1f01c90b` of 11-04, 590 Act 1 and 103 Act 2 starts of all nights): a second own-start figure on an older engine, in line with the reference arm.

| act | win rate % (95% interval) | starts | games | HP left after a win | % of max |
|---|---|---|---|---|---|
| 1 | 52.3 (49.1 to 55.5) | 590 | 2360 | 20.5 | 24.6 |
| 2 | 13.6 (8.5 to 18.7) | 103 | 412 | 14.2 | 17.3 |

### 3.10 The x16 starts

- Act 1: 227 starts; x16 64.3%, a3-v1 53.7%, humans 75.8%
- Act 2: 219 starts; x16 54.1%, a3-v1 43.4%, humans 72.6%

Humans on every rebuilt fifth-4 boss fight (not only the sample): Act 1 74.2% (1,579 of 2,127; Wilson interval 72.3 to 76.0), Act 2 74.5% (805 of 1,081; 71.8 to 77.0).


## 4. What it means for the milestone order

The memo's rule (section 5.1): if the player wins the humans' Act 2 boss starts near their 76 in 100, the deck dominates and milestones 2 to 6 go first; near its own 19, play dominates and milestone 7 takes the first slot after milestone 2.

| boss | gen 11 on its own starts | gen 11 on the humans' starts | the humans on those starts | where it falls |
|---|---|---|---|---|
| Act 1 | 57.2 | 52.5 | 73.7 | at its own: play |
| Act 2 | 14.7 | 44.4 | 74.3 | midway: both |

- **Act 1 boss: play first.** The humans' hands buy the player nothing (-4.7 points, interval -11.2 to +2.0), and the player is 21 points under them on the identical hand. This agrees with the 11-02 fits (17 to 23 points on play, 0 to 5 on the hand).
- **Act 2 boss: both, equally.** 29.9 points of play (24.3 to 35.3) and 29.8 of hand (23.2 to 36.2); the 11-02 fits had 27 to 44 on play and 22 to 39 on the hand, and these sit inside both ranges. Neither half alone reaches the humans: with their hands the player stops at 44, and by simple addition (the two effects need not add) their play on its own hands would also leave it near 45.
- **So the order.** Milestone 7 takes the first slot after milestone 2 (the play branch), because it is the whole of the Act 1 boss gap and half of the Act 2 one, and the deck milestones 3 to 6 are kept, because the hand is worth as much at the Act 2 boss. They use different resources (the deck half's fits are light, the fight half's blocks and fights heavy), so neither has to wait for the other. The hand's difference is in potions, relics and HP at the door, not in the deck's size, and those come from the rest, shop, potion and route decisions as well as the card picks (the human prior covers cards, rests and in part shops, not routes or events, memo section 3.1), so the potion hold rule (memo cause 3) belongs with the deck half's work.
- **Thinking time is the cheapest fight-half lever measured.** At x4 the gain is +4.2 and +6.2 points (the memo's 3-point test for a stakes schedule, on human boss starts, passes at the point estimate in both acts, the Act 1 interval starting at +1.7); at x16 it is about +10.6 in both acts, a half of the Act 1 play gap and a third of the Act 2 one. The cost is about 4 to 5 times (x4) and 15 to 16 times (x16) the own time of a boss game. The other half of the memo's test (the fight exam) and elites were not measured here, and the rest of the gap (11.5 and 18.5 points at x16) would need more than this search time: a better prior (the deeper-teacher board's aim) or a longer search than x16, which was not measured.
- **What does not change.** The go or no-go of section 5.2 of the memo, and the headline measure (Act 2 boss beaten per 100 runs). The ceiling for the hand alone is the 30 points of the hand effect, and only a part of it is reachable by choosing cards, since the hands also come from the fights before.

## 5. Caveats

1. **The rebuilt starts are not exact.** The record does not hold the growth of in-play enchantments, relic counters or potions an event gave (`docs/rl/HUMAN_STARTS.md`). If anything this costs our player: the human's real fight had them, the rebuilt one does not, so the play gap below may be a little overstated and the hand effect understated. The flagged approximation that can be checked does not drive the gap: starts with an enchanted card (114 of 300 in Act 1, 189 of 296 in Act 2) are won no less often by our player than the others (section 3.7). Counters the record cannot flag are not checkable.
2. **Copy against game.** Our rates are on the copy, the humans' are the game's. The copy's Act 2 state disagreements run 4.4 per 1,000 decisions in Act 2 and 0.66 in Act 1 (memo, section 2.2 cause 6), and its Act 2 boss was won 23 in 100 against the game's 19 for generation 11 (memo). So the play gap (humans minus our player on the same starts) includes whatever the copy's bosses add or take away; the hand effect (our player on two sets of starts, both on the copy) does not.
3. **Selection.** Both sets of starts are the fights of runs that reached the boss, so the hands are those of survivors, and good and poor players arrive with different hands. The hand effect is what the hands are worth to this player as they come, not what a deck policy could change at will.
4. **One player, one prior.** The player is v2 at three search budgets. Later gym checkpoints practised on human starts and would flatter themselves on these (so they were not used); a different prior could move every number.
5. **Thinking time is search only** (more simulations with the same prior). It costs about 4 to 5 times (x4) and 15 to 16 times (x16) the own time of a game (own seconds a game, Act 1 / Act 2: 5.3 / 9.0, 20.6 / 43.5, 78.5 / 144.5); whether the real game's bridge can afford x16 at a boss is not examined.
6. **Draws.** Two draws a start; the start is the unit of the intervals, so the human's single 0 or 1 and our two draws are both inside them. A boss cell holds 50 (Act 1) or 100 (Act 2) starts, so a per-boss rate is good to about 7 to 14 points either way.
7. **Crashes and hangs on the copy.** Eight games on four Act 2 starts (4 of 300, 1.3%) did not finish. On one start the copy raised an exception inside its approximation of a generated Defect card (a list changed while it was read) and killed the worker (three games: x4 once and x16 twice); on three starts a native step never returned and the worker was killed after 300 s with no step (five games; one game of one start hung in all three arms). Under the primary reading these four starts leave the sample (296 Act 2 starts); no game hit the time or decision cap. The copy's defect is real and unfixed here.
8. **The x16 arm** is a stratified prefix of the starts, not all of them (section 2), and what the stops cost is in section 2.

## 6. Not verified

- Whether the same holds in the real game: no real-game fight was played; the memo's 19 in 100 at the Act 2 boss is the nightly's.
- Whether the gym's play path (`fight_gym.play_steps` with the batched prior) matches the player the real-game bridge runs move for move; the fight exam and the gym loop's gate use the same path.
- The other half of the memo's stakes-schedule condition (a gain of 3 points or more on the fight exam as well as on human boss starts): only the boss-start half was measured here. Elites were not played.
- Whether a deck policy could reach the human hands: the hand effect is what the hands are worth to this player, an upper bound on what imitating the humans' decks can give through the hand.
- Why the copy hangs or raises on the starts of section 3.6; they were counted, not diagnosed.

## 7. Sources

All under `referee/backlog/play-or-deck/` unless a path says otherwise; per-run inputs stay there, uncommitted. The scripts are `build_sample.py` (the sample), `human_outcomes.py` (the corpus pass), `pod_run.py` and `pod_steps.py` (the games), `pod_own.py` (the reference arm), `analyze.py` and `make_tables.py` (the figures); `after_main2.sh` chained the reference arm after the main run.

| figure | file |
|---|---|
| every game of the three arms (win, HP left, potions, turns, own seconds, caps) | `rows.jsonl` |
| every game of the reference arm | `rows-own.jsonl`, `own-sample.json` |
| the 600 starts, their pools, ranks and hands | `sample.json`, `sample/starts.lite.json` |
| all rates, intervals, differences and tables of section 3 | `results.json`, `results.txt` (from `analyze.py --boot 4000`) |
| the pilot's timings and the plan | `plan.json`, `logs/play-or-deck/run.log` (under the working root) |
| library, commit, processes | `run-meta.json` |
| the first launch's discarded rows (a row-building bug of mine; the games were played, the timings are the pilot's) | `rows-aborted-typeerror.jsonl`, `plan-aborted.json` |
| the humans' rates on all fifth-4 boss fights | `referee/backlog/scratch-strategy/counts.json` (train4) and `results.json` `human_fifth4_all_bosses` |
| the humans on the 600 starts, HP after the boss floor | `human_outcomes.jsonl` (per run, local) through `results.json` |
| the fight exam's own-start reading (v2, a3-v1, four draws) | `referee/gym-loop/exam/games-v2.jsonl`, `starts.lite.json` |
| the memo's real-game figures (19 in 100, 4.4 per 1,000) | `docs/design/2026-11-05-strategy-rethink.md` sections 1.2 and 2.2 |
