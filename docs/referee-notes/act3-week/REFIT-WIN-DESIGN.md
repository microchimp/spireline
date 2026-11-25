# The run brain aimed at winning: design (lane 3)

Written 2026-11-19T02:15Z by lane 3 (Opus 5.5). This is a design only: nothing was run beyond light reads. The build brief is `BRIEF-3b-refit-build.md`. Paths are under `D:/spireline/`. Figures marked [m] are my own counts over the plain-run store (method in section 7).

Words used:
- **Run brain:** the network that scores a position in the middle of a run (`run_value.npz`).
- **Plain runs:** the champion's own runs, which the lab plays as data (`referee/run-cheap/<gen>/`).
- **Door:** the last run choice before a boss.
- **Per arrival:** per run that reached that boss.
- **First Act 3 boss:** the first of the two bosses that end Act 3.
- **AUC:** how well a forecast tells winners from losers (0.5 is chance, 1 is perfect).

## Short answer

- **Today.** The run brain forecasts the floor a run will end on. A win counts as 53, a death at the last boss as 49 and a death at the first Act 3 boss as 48. Its forecast for that boss is nearly blind at the door: AUC 0.59 (n=1,320). Seven plain facts about the same positions reach 0.78 in a simple logistic fit [m].
- **Proposal: a small second network, the "boss chain".** It forecasts two chances: getting past the Act 2 boss, and getting past the first Act 3 boss once past the Act 2 boss. In Acts 2 and 3 the player adds 10 floors times the log of the chance of getting through to each option's value. Act 1 play stays byte for byte as it is, and the run brain is not refitted.
- **Cost.** Under an hour of the graphics card, about 45 minutes on 4 processes for the rows, one build lane, and two judged blocks (6 machine hours).
- **Expected gain.** The first Act 3 boss per arrival should go from 15.5 to about 19 in 100. Per 100 runs that is about +0.6 (range -0.3 to +1.3). Wins are not measurable at this size. The judge's minimum gain (+1.0) is above the central estimate.

## 1. What the run brain predicts today (question 1)

- **Target and loss.** A distribution over 53 outcomes: the run ends on floor 1 to 52, or wins (`rl/run_train/models.py`). Each row is the position after a choice. Its label is 0.7 times the run's actual end plus 0.3 times the playing network's own forecast one step later (`train.bootstrap_targets`; beta 0.3 in every recent fit, the champion's included). The loss is cross-entropy plus 0.25 times the squared error of end HP.
- **Inputs.** The state, deck, relics, potions, and **H**: 8 numbers in which a fight network forecasts HP lost and the chance of death against this act's fights and boss.
- **The four floors.** The player reads the forecast as the expected final floor, a win valued at 53 (`models.expected_floors`). The bosses stand on floors 17, 33, 48 and 49.
- **The "search."** At run level, a one-step look. The chooser takes the best of `V_W + lambda x log(student probability)`, plus the human prior on its screens (`imitation_chooser.BlendedPolicy`). A guard admits an option the student almost never picks only if `V_W` prefers it by more than 1 floor. The fight search values its leaves by playing the fight out and never reads the run brain.
- **The scale.** Lambdas, guard and bonuses are all in floors, so a new scalar must stay in floors. A raw probability would change the student's weight a hundredfold.
- **What it knows about Act 3** [m] (the champion's stored forecasts, held-out generation 18 plain runs):

| Where | n | Forecast | Actual | AUC |
|---|---|---|---|---|
| Act 3 start: past the first Act 3 boss | 2,002 runs | 8.3 in 100 | 10.2 | 0.72 |
| same, lowest to highest fifth of the forecast | 400 each | 6.5 to 10.0 | 2.2 to 22.2 | |
| Door, runs that reached that boss | 1,320 | 8.9 | 15.5 | 0.59 |
| Act 3 start: win | 2,002 | 0.44 | 0.25 (5 wins) | 0.49 |
| Logistic at the door on which boss, HP, max HP, deck size, relics, potions, gold (fitted on 3,000 gen 17 arrivals) | 1,336 | 14.7 | 15.6 | 0.78 |
| which boss alone | 1,336 | | | 0.69 |

A generation 17 sample of 4,000 agrees (0.73 and 0.57). The three first Act 3 bosses (ids 73, 78, 80) are beaten 17, 26 and 3.5 times in 100 per arrival (n=443, 442, 451), and the forecasts ignore even that. Probable causes, not proven: the 53-way head spends itself on floors within an act, and the 0.3 self-share passes the squeeze on. The win forecast carries no information.

## 2. The target and what the player reads (question 2)

**Heads.** These are chained chances:
- `q2`: past the Act 2 boss.
- `q3`: past the first Act 3 boss, given past the Act 2 boss.
- `q4`: win, given past the first Act 3 boss.

Their product is the chance of winning from here. Each head trains only on rows before its boss, of runs that met its condition. The label is the actual end, with no share of any forecast. There is no Act 1 head, since Act 1 is left alone.

`q4` is a constant: 68/1,683, or 4.0 in 100, Beta-smoothed over all stores. The run makes no choice between the two Act 3 bosses (the floor-48 map has one node [m]), and 67 wins cannot carry a state-dependent head.

**Scalar.** `U = V_W + kappa_act x log(chance of getting through)`:
- kappa is 0 in Act 1, and 10 floors per nat in Acts 2 and 3.
- In Act 2 the log term is `log q2 + log q3`; in Act 3, before floor 48, `log q3`. Chances are clipped below at 0.002.

**Why the log.** The win chance is a product of boss chances, so its log is a sum. Each boss then counts by how hard it is, which is what winning asks. "Expected bosses beaten" counts bosses alike and keeps the easy one ahead. How each readout trades a point of the hard thing for a point of the easy thing (from generation 17 rates):

| Trade | Winning (truth) | `V_W` now | `V_W` + 20 x bosses beaten | `V_W` + 10 x log chance |
|---|---|---|---|---|
| Act 3: per-arrival kill vs reaching the door | 4.2 | 0.11 | 1.4 | 2.9 |
| Act 2: first Act 3 boss (given Act 2 boss) vs Act 2 boss | 2.9 | 0.06 | 0.17 | 1.9 |

**Why kappa = 10.** Both trades land within about 1.5 times the truth, `V_W` still breaks near-ties where the chain is noise, and differences stay floor-sized. At the door, healing from 60 to 90 in 100 of max HP is about +0.9 nats (9 floors), a potion about 2, a card pick 0.1 to 0.5.

**Why Act 1 is off.** Every refused refit and both Act 2-aimed student fits lost by playing Act 1 worse (section 4), and Act 1 is where we already beat the average human (76.5 against 54.9 in 100). With kappa 0, Act 1 choices are byte-identical, and a test pins it.

**Why a separate head.** Reading the chain off the existing head needs no fit, but that head cannot tell door positions apart, so weighting it more would amplify noise. The chain is its own file (`boss_chain.npz`), used through the chooser's existing per-option bonus path. The run brain, student, prior and recorded `values` are unchanged.

## 3. Data for the last heads (question 3)

[m] as of 02:00Z (generation 18 adds about 800 runs an hour while the lab plays):

| Store | Runs | Past Act 1 boss | Past Act 2 boss | Reached first Act 3 boss | Past it | Wins |
|---|---|---|---|---|---|---|
| gen 15 | 13,142 | 8,522 | 1,377 | 567 | 58 | 1 |
| gen 16 | 13,423 | 8,886 | 2,076 | 1,274 | 188 | 7 |
| gen 17 | 52,824 | 38,723 | 12,048 | 7,797 | 1,227 | 54 |
| gen 18 | 8,220 | 6,225 | 2,021 | 1,333 | 208 | 5 |
| all | 87,609 | 62,356 | 17,522 | 10,971 | 1,681 | 67 |

- **Pooling.** All four stores, with one offset per generation per head; the player reads generation 18's, because the candidate plays its fight brain. 208 positives fix one offset to about 0.07 on the logit scale, not a whole head. This breaks the matched-window rule (`fit_run_value_matched`) on purpose: the champion's run brain is already unmatched, and the one refit window that did not cost Act 1 pooled three champions.
- **Shrinkage.** `q3` learns from 17,522 runs, 1,681 positive, on lane A's Act 2 chance recipe (`rl/act2_chance.py`): start from the champion's layers, a low rate, heavy dropout and decay, each run counted once per head, the best epoch on held-out runs. Eight numbers for the deck's forecast against Act 3's fights let Act 2 rows see Act 3.
- **Not used.** Judged arms hold outcomes, not positions, and their seeds are barred. No human data.

## 4. The risk: trading Act 1 for later (question 4)

Per 100 paired runs, Act 3 read strictly as "went past floor 48" [m, `agent/gen16..18/*/arms`]:

| Refit (window) | Pairs | Act 1 boss | Act 2 boss | First Act 3 boss | Floors |
|---|---|---|---|---|---|
| cheap-v3b/c (gen 17 own, 12,980) | 500 | -12.0 (se 2.5) | -1.0 | -1.4 (0.9) | -2.78 |
| cheap-v3d (gen 17 own, 45,986) | 2,000+2,000 | -10.7, -12.3 (1.3) | -0.9, -2.2 | +1.40, +0.40 (0.5) | -1.94, -2.16 |
| cheap-v3 (gens 15-17 pooled, 40,496) | 2,000 | -1.75 (1.1) | +3.95 (1.1) | +1.10 (0.50) | +0.55 |
| frontier, frontier-3 (student, A2 grade) | 500, 1,700 | -4.2, -3.1 | | | |

All were refused. The mechanism found: fits on one champion's runs learned to heal less (0.43 against 0.55; D63 addendum 2, D65 addendum 1).

What limits it here:
- Act 1 is untouched.
- The Act 2 boss keeps its own term in the same log chain, so Act 2 kills are traded only at winning's rate (2 to 3 for 1).
- The chain pushes toward more HP at the door: HP before the boss is the strongest door fact (+3.8 on the logit scale from empty to full).
- An offline flip check can veto the candidate.

v3's collapse guard (-5 floors) would not catch a -2 floors trade, and the design does not rely on it. Side finding: under v3 read strictly, `cheap-v3` is +1.15 in 100 on Act 3 kills plus wins, which reads "extend", and it was never played on a second block.

## 5. Recipe (question 5)

- **Venvs.** The rows need the emulator's Python (`D:/spireline/src/sts2/.venv/Scripts/python.exe`, with `STS2_LIB_PATH` set to the worktree's `out/`). The fit uses `D:/spireline/venv-gpu/Scripts/python.exe`.
- **Time.** Rows take about 45 minutes on 4 BelowNormal processes (A2 built 477,000 rows in 6). The fit is 3 seeds of 4 epochs, 15 to 30 card minutes.
- **Keep checks.** `vrun_keep_passed` (since D64, "the export exists") concerns `run_value.npz`, which stays the champion's along with its `vrun_fit` block. The chain has its own pre-registered checks (below and brief step 8).
- **Candidate.** `agent/gen19/candidate-chain`: a byte copy of `gen18/candidate-fight-v3`, with new `model.json`, `boss_chain.npz`, `boss_chain.json` and `train.json`, and its `agent.json` plus a `boss_chain` block (file, sha256, kappa [0, 10, 10]) and a recipe ending `+chain:<8 hex>@0/10/10`.
- **Marker.** The orchestrator writes `D:/spireline/referee/LAB/train/ready-18-g19-chain`, containing the UTC time as lane V's did. The lab judges under v3.
- **Smoke test, within an hour.** On the held-out fifth of generation 18 runs, `boss_chain.py report` gives calibration by decile and AUC for `q3` at Act 3 start and at the door among arrivals, and for `q2` at Act 2 start, beside the champion brain's own forecasts. Pass: door AUC at least 0.70, calibration slope 0.7 to 1.3, mean within 3 points. Otherwise there is no candidate.

## 6. Expected effect and the deciding test (question 6)

| Per 100 | Now (gen 18) | With the chain |
|---|---|---|
| First Act 3 boss, per arrival | 15.5 (n≈1,330) | about 19 (15.5 to 21) |
| Reaching that boss, per run | 16.2 | 15.5 to 17 |
| Past it, per run | 2.5 | 2.6 to 3.5 (central +0.6) |
| Wins | 0.06 to 0.10 | +0 to +0.05 |

Where the gain would come from [m]:
- 23 in 100 arrivals meet the boss below 70 in 100 of max HP.
- 35 in 100 hold no potion: 0.87 potions held of 2.44 slots, and a potion is worth +0.25 on the logit scale at the door.
- In Act 3 shops a potion is about 3 in 10 purchases when one is offered.

These are associations, and the judge measures.

**Test.** Two judged blocks of 2,000 fresh pairs, read strictly and decided on 4,000 by v3. The standard error at 4,000 is about 0.34 in 100 (`cheap-v3d` pooled), so a true +0.6 passes about 1 time in 8 and a true +1.0 half the time. **Pre-register both blocks.** At 2,000 pairs the rule extends only on a +1.0 point estimate, so a true +0.6 would most likely be refused after one block.

Read beside it:
- per-arrival kills (about 650 arrivals an arm, SE about 2 points);
- Act 2 boss kills;
- Act 1 kills, which should match pair by pair. Any difference is the judge's own noise.

## 7. Unknowns, and what would change this

- **Causality.** Whether the door facts are causal: HP and potions likely; relics and max HP partly stand in for deck strength.
- **The copy.** Whether the copy's Act 3 is right (tonight's real block).
- **The second boss.** Whether it can be moved by run choices at all; it is left to the fight brain (lane 5).
- **Stop signs:**
  - smoke AUC at the door under 0.65: stop, no judged block;
  - fewer than 3 in 100 Act 3 choices changed in the flip check: skip the judgement;
  - a pass: try Act 1 at a small kappa next.
- **Method of [m].** One Python process over `run-cheap/{15..18}/runs.jsonl` and `decisions.d/<seed>.record.json`. P(past the first Act 3 boss) sums the stored `p_floor` classes for floors 49 to 53, at the first decision on floor 34 or later and at the last before floor 48. `boss_chain.py report --champion` repeats it from the fork.
