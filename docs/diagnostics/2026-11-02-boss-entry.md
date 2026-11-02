# Boss entry, 2026-11-02: what the AI brings to the Act 1 and Act 2 bosses, against humans

Step B of the reset order (D44, started early by D45). The 2026-11-01 diagnostic found that the AI reaches the Act 1 boss more often
than humans (92% of runs against 74%) and kills it less often (52% of visits against 74%), then dies in Act 2, and that nothing measured
what it brings to those fights. This file is that measure: the instrument, the human comparison on the held-out fifth, the per-decision
exam, and a reading. Everything here was computed from files on this PC; no game and no emulator ran. Times are Z.

Tools (in this repo): `tools/boss_entry.py` (readers and aggregates), `tools/boss_entry_report.py` (the tables below),
`tools/boss_entry_exam.py` (the per-decision exam), tests in `tests/test_boss_entry.py`. How to rerun everything is at the end.

## The answer

**The AI does not arrive at the Act 1 boss weak. It arrives healthier than a human and poorer in what fighting more would have given
it, and it still loses to the boss far more often.** At the Act 1 boss the AI has 65.5 of 82.8 HP (79%); a human has 54.6 of 81.2
(67%). Upgrades (2.8 against 2.9) and deck size (18.8 against 19.6 cards) are level. The AI holds 4.2 relics against 6.0, 0.7 potions
against 1.6, 99 gold against 150, and a deck of 11.1 attacks and 5.2 skills against 9.5 and 7.6. Its route had 0.45 elite fights; the
humans' had 1.95. Yet it kills the boss in 51.5% of visits (18,401 visits, plus or minus 0.7) against 74.8% for humans (2,155 visits,
plus or minus 1.8).

At the Act 2 boss the AI is worse off in most things: 52.2 of 85.4 HP (61%) against 60.6 of 84.3 (72%), 5.7 upgrades against 6.9,
8.1 relics against 11.5, 0.6 potions against 1.9, and a deck of 15.8 attacks and 7.6 skills against 11.4 and 11.1. It kills the boss in
8.8% of visits (4,408, plus or minus 0.8) against 75.7% (1,142, plus or minus 2.5). It also dies before that boss far more often:
53% of the runs that enter Act 2, against 29% of the humans'.

**Most of the boss gap is not in what the run brings; it is in how the boss fight is played with it.** Two small models of the boss
kill (a logistic fit on nine things the run brought, optionally plus the copies of each of the 60 commonest cards) say:

| Boss | AI actual | Humans actual | Human-fitted model on the AI's entry states | AI-fitted model on the humans' entry states |
|---|---|---|---|---|
| Act 1 | 51.5% | 74.8% | 68.8% (74.6% with the cards) | 56.4% (44.3% with the cards) |
| Act 2 | 8.8% | 75.7% | 35.9% (35.3% with the cards) | 31.3% (34.7% with the cards) |

Read the Act 1 row as: a human holding the AI's hand would kill the boss about 69 to 75 times in 100, so of the 23-point gap only
0 to 5 points are the hand and 17 to 23 points are the play (the AI-fitted model with cards even rates the humans' hands 7 points below
the AI's own: the AI plays its own style of deck best). The Act 2 row: the AI's hand is worth about 36 in 100 in human hands and the AI
plays it to 9, so of the 67-point gap 22 to 39 points are the hand and 27 to 44 points are the play. The raw cuts agree: an AI
run with 85% or more of its HP at the Act 1 boss kills it 64% of the time, a human run with under 50% kills it 57%; at the Act 2 boss
the same two groups are 18% and 64% (table 13). So the loop's fight player (step A) is the larger lever at both bosses; the run-level
choices are second at Act 1 and a close second at Act 2.

## Which run-level choices differ from humans, ranked by what they could buy

"Could buy" is the change in the boss kill share, in points, when that one thing moves from the AI's average to the humans' average with
the rest held, under the AI-fitted model and under the human-fitted model (table 9). It is an association inside a model, not a test:
potions held, for instance, also mark a run that is going well. Where the two models disagree the range is given.

| # | Choice and what differs | Act 1 boss (gap 23.3) | Act 2 boss (gap 66.9) |
|---|---|---|---|
| 1 | **Route: fights and elites, hence potions and relics.** The AI takes 0.45 elites before the Act 1 boss (humans 1.95) and takes an elite in 18% of the map choices that offer one (31% in Act 2). It fights 5.4 times (humans 6.7) and so is offered 3.1 potions (humans 4.3); it picks them up at the same rate (84% against 82%) and spends about the same number, so it holds 0.7 at the boss against 1.6. Relics 4.2 against 6.0 (Act 2: 8.1 against 11.5) | potions +9 to +10, relics +3 to +8; but fighting those elites costs HP (the AI's 12-point lead in HP share is worth 7 to 10 points), so net of that the route is worth about 0 to +6 | potions +5 to +9, relics +4 to +9; HP share +3 to +5 |
| 2 | **Deck shape: card rewards.** The AI almost never takes defence and draw skills when offered: Shrug It Off 0% of 11,654 offers (humans 43%), Bloodletting 1% (40%), Battle Trance 2% (61%), Flame Barrier 1% (55%), Burning Pact 0% (33%); it takes Anger 82% (humans 20%), Twin Strike 70% (18%), Unrelenting 94% (34%), Fight Me 97% (40%), Bully 87% (31%). In Act 2 it skips 8% of rewards, humans 34%. At the Act 2 boss: 15.8 attacks and 7.6 skills against 11.4 and 11.1 | about 0 to +2 (more skills, +4, are offset by fewer attacks: net 0 in the AI model, +2 in the human model) | +2 to +10 (the human-fitted model charges 8.5 points to the extra attacks) |
| 3 | **Rest sites: heal against upgrade.** Totals before the Act 1 boss are level (1.9 upgrades and 1.4 heals either way), but by HP on arrival the AI heals where humans upgrade: at 40 to 60% HP it upgrades 29% of the time (humans 55%), at 60 to 80% HP 43% (83%). In Act 2 it upgrades 1.3 times before the boss (humans 1.7) and arrives with 5.7 upgrades (6.9) | about +0.5 (an upgraded card is worth 5 to 6 points at the Act 1 boss in both models, but the totals are level) | +1 to +2 |
| 4 | **Shops.** The AI visits more (1.6 against 0.9 before the Act 1 boss) and buys cards (1.2 against 1.0) but fewer relics (0.11 against 0.28) and removes fewer cards (0.13 against 0.21); it carries 99 gold to the boss, humans 150 | about 0 (gold has no effect in either model) | about 0, but relics bought in Act 2 are 0.41 against 0.60 |

Everything in the table together: **+6 points at the Act 1 boss** (AI model +5.9, human model +5.4) and **+22 to +39 at the Act 2 boss**
(AI model +22.4, human model +38.6; the second is large because the models extrapolate beyond the AI's range). The cards themselves
matter less than the counts: in the human-fitted model with cards the largest effects per copy at the Act 1 boss are Fight Me +0.62,
Dominate +0.60, Battle Trance +0.36, Ashen Strike +0.36, Unrelenting +0.35 and Anger +0.26 (log-odds, table 14); the AI already takes
Fight Me, Dominate, Unrelenting and Anger nearly every time they are offered. Of the cards it passes on, only Battle Trance and Ashen
Strike show a clear positive effect; Shrug It Off and Bloodletting are near zero (+0.10 and -0.05 in a 90-card version of the fit).
Adding the cards to the model moves its fit only a little (area under the curve 0.723 to 0.747 at Act 1, 0.712 to 0.746 at Act 2).

Two readings follow from the AI's own results. First, inside its own runs the number of Act 1 elites it fights does not change its boss
kill share (52%, 51%, 51% for 0, 1, 2 elites, table 12): each elite costs about seven points of HP share and brings about 0.9 relics,
and the two cancel for this fighter; humans who fought 3 elites kill 81% against 61% for none, but that mixes route with player strength. So the
route is not a free gain for the AI; it pays only if the fight player gets better at keeping HP. Second, the V_run recipe made the AI
better mostly by raising its HP at the boss, not by improving its deck: from generation 5 to 9 the kill share at the Act 1 boss went
19% to 52% while HP at entry went 44.5 to 65.5 and the deck, upgrades, relics, potions and elites barely moved (table 11).

## The per-decision exam (item 3 of the brief): built, on card rewards and rest sites

On the held-out fifth (2,924 runs, Acts 1 and 2) the AI's own run-level chooser (the generation 9 value head, the same weights and
the same lookahead rule as the nightly) was asked what it would do at the humans' card rewards (29,172 decisions) and rest sites
(11,421), from the state the human was in. A human record becomes the chooser's state by rebuilding HP, gold, deck, relics and
potions from the rooms up to the decision; the one thing the corpus lacks is the act map, so each state is valued under four maps taken
from the AI's own states on the same floor of the same act and the values are averaged. That choice agrees with the chooser using the
true map in 97.2% of 1,381 card decisions and 97.9% of 606 rest decisions on the AI's own states, against 80.8% and 89.8% with no map.
Map choices, shop choices and events are not examined (a map choice needs the map, a shop choice the prices, an event the event ids).

| | Act 1 | Act 2 |
|---|---|---|
| Card rewards: the AI picks what the human picked | 33% (a coin over the offered cards and skip: 25%) | 26% |
| The human's pick is the AI's first or second choice | 56% | 50% |
| Human skips / the AI would skip | 14% / 14% | 34% / 7% |
| Floors the AI's own value says the human's pick loses | 0.37 | 0.15 |

When a human took a card, the AI would take the same card 35% of the time and skip 12%; when a human skipped, the AI would skip 13%.
The cards it would pass on or grab, from the same states, are the same as in its own games (table 15): it passes on Battle Trance
(7% against 61% of humans), Bloodletting (1%, 40%), Flame Barrier (13%, 49%), Burning Pact (1%, 36%), Shrug It Off (14%, 41%); it takes
Anger (71%, 15%), Twin Strike (65%, 16%), Unrelenting (90%, 29%), Fight Me (81%, 35%), Bully (81%, 30%). So its card taste belongs
to the value head, not to the states it happens to reach. At rest sites it would upgrade 46% of the time against the humans' 56%, and
agrees on 61%; by HP on arrival (Act 1) it upgrades 36% against 55% at 40 to 60% HP and 48% against 83% at 60 to 80%. When both
upgrade, the AI's value says the human's choice of card loses 0.57 floors against its own.

What the exam does not say: whether the humans' choices are better. The link from a choice to boss survival is only the association
in tables 9 and 14; the exam shows where the chooser parts company with the humans, and by how much.

## What this means for the next recipe (a reading, not a decision)

- A new V_run target cannot buy more than about 6 points at the Act 1 boss; the fight player is worth up to 17 to 23. At Act 2 the
  run-level ceiling is larger (22 to 39 points) and the levers are the same set: potions, relics, a less attack-heavy deck, HP.
- The value head under-values the things that come from fighting (elites, potions, relics) and over-values attacks that win quickly.
  Its target (floor reached) rewards HP kept now over relics that pay at a boss, and it has almost no Act 2 clears to learn from.
- Any new recipe can be tested for these on two cheap checks that this step leaves behind: the per-decision exam (about 12 minutes,
  one process, no game) and the entry table on self-play shards (about 3 minutes).

## What each source holds, and what it lacks

| Source | Holds | Lacks |
|---|---|---|
| Nightly real arm, `referee/LAB/nightly/<date>/g9/runs.jsonl` | seed, floor, boss damage by act, card picks and skips by floor, rest choices by floor, map letters | HP, max HP, gold, deck, relics and potions at any floor; the map letters only where the agent had a choice (a forced step is not asked), so its elite, chest and fight counts undercount (elites 0.07 against the emulator arm's 0.45); shop buys, events, potion use. The game's per-fight logs are deleted at block end |
| Nightly emulator arm, `.../g9-emu/runs.jsonl` | the same fields, with every map step | the same state fields |
| The loop's start set, `referee/gym-loop/starts/` | full fight-entry states (HP, deck, relics, potions) for 50 runs a night on four nights (10-26 gen 5, 10-27 and 10-29 gen 7, 10-30 gen 9): 168 Act 1 boss starts, 18 Act 2 | the three newest nights, the real arm, picks and path; small. Used as a cross-check (table 16) |
| The lab's self-play shards, `referee/LAB/runs/*selfplay*/shards/r*.jsonl.gz` | every run's full state at every decision and fight, emulator, the nightly agent's own macro and prior: 20,049 generation 9 runs (33,242 for generations 5 to 9) | the real arm; the nightly seeds. Used as the AI table: its headline matches the nightly emulator arm (mean floor 22.60 against 22.5, 22.2, 22.6, 22.7; Act 1 boss kill 51.5% against 51.0, 50.6, 50.0, 51.3) |
| The human corpus, `data/spire-codex/runs-v0.107.1.jsonl.gz` | per room HP, max HP, gold, cards gained, removed, transformed and upgraded, relics, potions, rest choices, card offers with the pick | the act map and position; the order of events inside a room; whether an offered card was upgraded |

The AI's real-arm boss-entry state is therefore not measured: every number about HP, deck and relics at a boss is from the emulator
(self-play, and 4 x 50 saved nightly runs). The two arms agree to within one or two points on everything the real arm does record: Act 1
boss reach, kill rate, cards taken a run (8.2 against 8.0 on 11-02), skip rate (14% against 13%), rests upgraded (55% against 55%)
and the pre-boss picks and rests in table 10; so the emulator is a fair stand-in for run-level choices, but "fair" is not "checked run
by run" (only about half the paired seeds end on the same floor, per the diagnostic). Proposed fields that would close this are at the end.

## Notes and limits

- The human line is the **held-out fifth** of D38 (2,924 vanilla Ironclad A10 runs of 14,745, by a fixed hash of the run id,
  `boss_entry.exam_bucket`). No split file existed (the diagnostic could not find one), so this step created it: the rule is the hash,
  and the id list is `referee/backlog/boss-entry/human-exam-fifth-ids.txt` (run ids only) for the owner to place next to the corpus.
  The other four fifths were used only to fit the human-side models (a training use the decision allows). The human cells are
  aggregates; any cell under 20 is suppressed in the tables (tests check it). The all-runs row of table 1 reproduces the paper's line
  (27.0 floors against 27.1; Act 1 boss killed in 73.9% of visits against 74%; Act 2 boss cleared in 28.9% of runs against 29.1%;
  wins 11.3%; 9.5 cards a run against 9.2; 57% of rests upgrading against 55%).
- A human deck at boss entry is rebuilt by replaying the rooms. Against the final deck it gets the card list exactly in 99.7% of
  3,000 runs and the number of upgrades exactly in 97.7% (`boss_entry.py check`). Potions held are rebuilt the same way (picked and
  bought, less used and discarded) and are not checked; the human potion figures are the least certain in the tables.
- "Killed the boss" for a human means the next act exists in the record; for the AI the boss fight was won. A human run the corpus
  ends without a death or a win (none were seen in the first 3,000) would be left out of the kill rates.
- The kill models are logistic, fitted by Newton steps with a small ridge penalty; they describe the AI's and the humans' data, not the
  game. The Act 2 human-fitted model is applied to AI states with about 4 more attacks than a human holds on average.
- The exam's run count printed in table 15 (2,968) counts exam-fifth runs read before the vanilla filter; the 40,593 decisions come
  from the 2,924 vanilla runs (fixed in the code, not rerun).
- The self-play shards of generations 5 to 8 are played by earlier agents; only generation 9 is the nightly agent. Table 11 is the
  trend; the other tables use generation 9 only.

## Tables

All human rows are the exam fifth unless a row says otherwise. "Cleared Act 1 (of runs)" is the share of all runs that killed the Act 1
boss; "Kill it (of reached)" is the share of the runs that reached it. Self-play rows are the emulator; the night rows are the nightly
blocks (crash rows excluded). A dot is "no data or not applicable".

### 1. The run in one line, by source

| Group | Runs | Mean floor | Reach Act 1 boss | Kill it (of reached) | Cleared Act 1 (of runs) | Reach Act 2 boss | Kill it (of reached) | Cleared Act 2 (of runs) | Won | Cards taken a run | Skip rate | Rests upgraded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Humans, exam fifth | 2,924 | 27.2 | 73.7% | 74.8% | 55.1% | 39.1% | 75.7% | 29.6% | 11.4% | 9.6 | 23% | 56% |
| Humans, all runs | 14,745 | 27.0 | 73.8% | 73.9% | 54.5% | 38.2% | 75.6% | 28.9% | 11.3% | 9.5 | 23% | 57% |
| AI gen 9 self-play (emulator) | 20,049 | 22.6 | 91.8% | 51.5% | 47.3% | 22.0% | 8.8% | 1.9% | 0.0% | 7.9 | 14% | 54% |
| AI gen 9 night 2026-10-30, real game | 1,409 | 22.1 | 91.2% | 51.3% | 46.8% | 19.2% | 5.9% | 1.1% | 0.0% | 7.7 | 15% | 53% |
| AI gen 9 night 2026-10-30, emulator | 2,000 | 22.5 | 91.1% | 51.0% | 46.5% | 22.5% | 9.3% | 2.1% | 0.0% | 7.8 | 15% | 53% |
| AI gen 9 night 2026-10-31, real game | 472 | 22.5 | 91.7% | 54.0% | 49.6% | 20.1% | 10.5% | 2.1% | 0.0% | 7.8 | 15% | 53% |
| AI gen 9 night 2026-10-31, emulator | 500 | 22.2 | 89.8% | 50.6% | 45.4% | 20.2% | 10.9% | 2.2% | 0.0% | 7.7 | 15% | 54% |
| AI gen 9 night 2026-11-01, real game | 493 | 22.7 | 92.3% | 52.3% | 48.3% | 20.7% | 10.8% | 2.2% | 0.0% | 8.0 | 14% | 55% |
| AI gen 9 night 2026-11-01, emulator | 500 | 22.6 | 93.2% | 50.0% | 46.6% | 21.2% | 10.4% | 2.2% | 0.0% | 7.9 | 14% | 53% |
| AI gen 9 night 2026-11-02, real game | 498 | 23.1 | 91.8% | 56.9% | 52.2% | 23.5% | 10.3% | 2.4% | 0.0% | 8.2 | 14% | 55% |
| AI gen 9 night 2026-11-02, emulator | 500 | 22.7 | 92.0% | 51.3% | 47.2% | 22.2% | 9.9% | 2.2% | 0.0% | 8.0 | 13% | 55% |

### 2. What each group brings to the Act 1 boss

| Group | Runs | HP / max | HP share | Cards | Upgraded | Attack / skill / power / other | Strikes + Defends | Relics | Potions | Gold |
|---|---|---|---|---|---|---|---|---|---|---|
| Humans (exam fifth), reached the boss | 2,155 | 54.6 / 81.2 | 67% | 19.6 | 2.9 | 9.5 / 7.6 / 1.1 / 1.5 | 8.5 | 6.0 | 1.6 | 150 |
| Humans (exam fifth), killed the boss | 1,611 | 56.6 / 81.3 | 70% | 19.7 | 3.0 | 9.5 / 7.7 / 1.1 / 1.4 | 8.4 | 6.0 | 1.7 | 148 |
| Humans (exam fifth), died at the boss | 544 | 48.7 / 80.7 | 60% | 19.5 | 2.5 | 9.5 / 7.5 / 1.0 / 1.5 | 8.5 | 6.0 | 1.3 | 154 |
| Humans (exam fifth), died before the boss | 769 | 33.9 / 80.1 | 43% | 16.7 | 1.1 | 8.1 / 6.3 / 0.9 / 1.5 | 8.6 | 3.9 | 1.0 | 143 |
| AI gen 9 self-play, reached the boss | 18,401 | 65.5 / 82.8 | 79% | 18.8 | 2.8 | 11.1 / 5.2 / 1.2 / 1.3 | 8.8 | 4.2 | 0.7 | 99 |
| AI gen 9 self-play, killed the boss | 9,474 | 71.8 / 83.2 | 86% | 18.9 | 3.0 | 11.2 / 5.1 / 1.2 / 1.3 | 8.8 | 4.3 | 0.9 | 89 |
| AI gen 9 self-play, died at the boss | 8,927 | 58.8 / 82.4 | 71% | 18.6 | 2.5 | 11.1 / 5.2 / 1.1 / 1.3 | 8.7 | 4.1 | 0.6 | 109 |
| AI gen 9 self-play, died before the boss | 1,648 | 26.8 / 81.9 | 33% | 16.8 | 1.0 | 9.9 / 5.0 / 0.7 / 1.2 | 8.9 | 3.2 | 0.5 | 125 |

### 3. What each group brings to the Act 2 boss

| Group | Runs | HP / max | HP share | Cards | Upgraded | Attack / skill / power / other | Strikes + Defends | Relics | Potions | Gold |
|---|---|---|---|---|---|---|---|---|---|---|
| Humans (exam fifth), reached the boss | 1,142 | 60.6 / 84.3 | 72% | 26.3 | 6.9 | 11.4 / 11.1 / 2.5 / 1.4 | 7.4 | 11.5 | 1.9 | 186 |
| Humans (exam fifth), killed the boss | 865 | 62.1 / 84.2 | 74% | 26.2 | 7.2 | 11.2 / 11.1 / 2.5 / 1.4 | 7.4 | 11.7 | 2.0 | 189 |
| Humans (exam fifth), died at the boss | 277 | 55.8 / 84.8 | 66% | 26.7 | 6.3 | 11.9 / 10.9 / 2.5 / 1.4 | 7.6 | 10.9 | 1.5 | 177 |
| Humans (exam fifth), died before the boss | 469 | 34.5 / 82.7 | 42% | 24.1 | 4.5 | 10.7 / 9.7 / 2.2 / 1.5 | 7.8 | 8.5 | 1.4 | 178 |
| AI gen 9 self-play, reached the boss | 4,408 | 52.2 / 85.4 | 61% | 27.0 | 5.7 | 15.8 / 7.6 / 2.1 / 1.4 | 8.2 | 8.1 | 0.6 | 100 |
| AI gen 9 self-play, killed the boss | 388 | 66.3 / 85.9 | 77% | 26.9 | 6.3 | 15.8 / 7.6 / 2.1 / 1.4 | 8.2 | 8.4 | 0.8 | 92 |
| AI gen 9 self-play, died at the boss | 4,020 | 50.8 / 85.4 | 60% | 27.0 | 5.7 | 15.8 / 7.6 / 2.2 / 1.4 | 8.2 | 8.1 | 0.6 | 101 |
| AI gen 9 self-play, died before the boss | 5,066 | 32.0 / 83.8 | 38% | 24.4 | 4.0 | 14.0 / 6.9 / 2.1 / 1.4 | 8.3 | 6.5 | 0.5 | 114 |

### 4. The path and the choices before the boss

| Group | Runs | Fights | Elites | Rests | Shops | Chests | ? rooms | Upgrades / heals | Cards taken (skip rate) | Shop visits / cards / relics / removals |
|---|---|---|---|---|---|---|---|---|---|---|
| Act 1, humans (exam fifth), reached the boss | 2,155 | 4.7 | 1.95 | 3.26 | 0.92 | 1.00 | 3.22 | 1.87 / 1.37 | 6.42 (15%) | 0.92 / 0.99 / 0.28 / 0.21 |
| Act 1, humans (exam fifth), died before the boss | 769 | 3.7 | 0.56 | 0.95 | 0.54 | 0.46 | 2.01 | 0.56 / 0.39 | 4.03 (14%) | 0.54 / 0.61 / 0.11 / 0.12 |
| Act 1, AI gen 9 self-play, reached the boss | 18,401 | 5.0 | 0.45 | 3.31 | 1.32 | 1.00 | 3.96 | 1.92 / 1.38 | 5.30 (18%) | 1.56 / 1.18 / 0.11 / 0.13 |
| Act 1, AI gen 9 self-play, died before the boss | 1,648 | 4.4 | 0.65 | 1.10 | 0.79 | 0.60 | 2.72 | 0.54 / 0.56 | 4.30 (17%) | 0.89 / 0.67 / 0.05 / 0.06 |

| Group | Runs | Fights | Elites | Rests | Shops | Chests | ? rooms | Upgrades / heals | Cards taken (skip rate) | Shop visits / cards / relics / removals |
|---|---|---|---|---|---|---|---|---|---|---|
| Act 2, humans (exam fifth), reached the boss | 1,142 | 4.0 | 1.75 | 3.11 | 1.08 | 1.01 | 3.04 | 1.68 / 1.50 | 4.42 (34%) | 1.08 / 1.02 / 0.60 / 0.36 |
| Act 2, humans (exam fifth), died before the boss | 469 | 3.0 | 0.34 | 0.78 | 0.60 | 0.46 | 1.90 | 0.33 / 0.43 | 2.59 (33%) | 0.60 / 0.55 / 0.27 / 0.15 |
| Act 2, AI gen 9 self-play, reached the boss | 4,408 | 4.0 | 0.71 | 3.07 | 1.34 | 1.01 | 3.84 | 1.27 / 1.80 | 5.48 (8%) | 1.62 / 1.20 / 0.41 / 0.15 |
| Act 2, AI gen 9 self-play, died before the boss | 5,066 | 3.3 | 0.62 | 0.82 | 0.78 | 0.50 | 2.34 | 0.26 / 0.56 | 3.57 (8%) | 0.92 / 0.67 / 0.27 / 0.07 |

### 5. Rest sites: the share spent on an upgrade, by HP on arrival

Act 1

| HP on arrival | AI sites | AI upgrade share | Human sites | Human upgrade share |
|---|---|---|---|---|
| <40% | 7,529 | 19% | 2,214 | 17% |
| 40-60% | 11,515 | 29% | 2,300 | 55% |
| 60-80% | 18,744 | 43% | 2,095 | 83% |
| >=80% | 24,899 | 94% | 1,097 | 97% |

Act 2

| HP on arrival | AI sites | AI upgrade share | Human sites | Human upgrade share |
|---|---|---|---|---|
| <40% | 6,045 | 16% | 1,165 | 15% |
| 40-60% | 4,435 | 29% | 1,182 | 46% |
| 60-80% | 3,953 | 46% | 1,032 | 78% |
| >=80% | 3,249 | 87% | 609 | 91% |

### 6. Cards in the deck at the boss: share of runs holding each

Act 1 boss

| Card | AI gen 9 | Humans (exam fifth) |
|---|---|---|
| Anger | 49% | 17% |
| Twin Strike | 43% | 14% |
| Molten Fist | 43% | 21% |
| Perfected Strike | 38% | 20% |
| Thunderclap | 23% | 13% |
| Fight Me | 23% | 12% |
| Stampede | 22% | 10% |
| Dominate | 21% | 19% |
| Pommel Strike | 14% | 35% |
| Bloodletting | 3% | 34% |
| Shrug It Off | 0% | 34% |
| Tremble | 11% | 32% |
| Breakthrough | 16% | 22% |
| Armaments | 17% | 21% |
| Blood Wall | 1% | 20% |

Act 2 boss

| Card | AI gen 9 | Humans (exam fifth) |
|---|---|---|
| Anger | 64% | 21% |
| Perfected Strike | 63% | 23% |
| Twin Strike | 58% | 18% |
| Molten Fist | 56% | 31% |
| Pommel Strike | 43% | 50% |
| Thunderclap | 39% | 18% |
| Unrelenting | 37% | 14% |
| Breakthrough | 35% | 26% |
| Bloodletting | 7% | 57% |
| Shrug It Off | 35% | 52% |
| Tremble | 23% | 48% |
| Battle Trance | 7% | 36% |
| Dominate | 29% | 36% |
| Blood Wall | 16% | 30% |

### 7. Card rewards: pick rate when offered (cards before the boss; largest gaps)

Act 1

| Card | AI offers | AI pick rate | Human offers | Human pick rate | Gap (points) |
|---|---|---|---|---|---|
| Battle Trance | 3,922 | 2% | 605 | 61% | -59 |
| Flame Barrier | 3,855 | 1% | 616 | 55% | -54 |
| Shrug It Off | 11,654 | 0% | 1,816 | 43% | -43 |
| Bloodletting | 11,522 | 1% | 1,877 | 40% | -39 |
| Whirlwind | 3,846 | 2% | 629 | 39% | -37 |
| Burning Pact | 4,006 | 0% | 671 | 33% | -33 |
| Ashen Strike | 3,805 | 2% | 624 | 31% | -30 |
| Pommel Strike | 11,682 | 21% | 1,856 | 50% | -29 |
| Stone Armor | 3,885 | 74% | 648 | 32% | +42 |
| Stomp | 3,938 | 85% | 648 | 37% | +48 |
| Stampede | 3,854 | 81% | 695 | 30% | +51 |
| Twin Strike | 11,706 | 70% | 1,792 | 18% | +52 |
| Bully | 3,948 | 87% | 608 | 31% | +56 |
| Fight Me | 3,830 | 97% | 615 | 40% | +57 |
| Unrelenting | 3,798 | 94% | 601 | 34% | +60 |
| Anger | 11,573 | 82% | 1,800 | 20% | +62 |

Act 2

| Card | AI offers | AI pick rate | Human offers | Human pick rate | Gap (points) |
|---|---|---|---|---|---|
| Dominate | 1,342 | 27% | 313 | 68% | -41 |
| Battle Trance | 1,292 | 20% | 312 | 60% | -40 |
| Bloodletting | 3,892 | 1% | 864 | 39% | -38 |
| Burning Pact | 1,269 | 6% | 279 | 42% | -36 |
| Feel No Pain | 1,332 | 12% | 334 | 34% | -22 |
| Vicious | 1,284 | 12% | 339 | 32% | -20 |
| Drum Of Battle | 1,294 | 4% | 333 | 22% | -18 |
| Expect A Fight | 1,275 | 8% | 337 | 25% | -17 |
| Breakthrough | 3,836 | 47% | 870 | 10% | +37 |
| Twin Strike | 3,754 | 50% | 895 | 10% | +40 |
| Bully | 1,263 | 71% | 273 | 27% | +44 |
| Stone Armor | 1,316 | 76% | 328 | 23% | +53 |
| Stomp | 1,318 | 72% | 306 | 16% | +55 |
| Hemokinesis | 1,263 | 66% | 301 | 7% | +59 |
| Perfected Strike | 3,932 | 76% | 886 | 16% | +60 |
| Unrelenting | 1,383 | 86% | 270 | 17% | +69 |

### 8. Each boss

Act 1

| Boss | AI visits | AI kill rate | AI HP share | Human visits | Human kill rate | Human HP share |
|---|---|---|---|---|---|---|
| Lagavulin Matriarch | 3,178 | 56% | 79% | 325 | 74% | 65% |
| Ceremonial Beast | 3,116 | 73% | 79% | 355 | 82% | 67% |
| Vantom | 3,091 | 43% | 80% | 360 | 74% | 70% |
| The Kin | 3,011 | 41% | 79% | 376 | 72% | 69% |
| Waterfall Giant | 3,004 | 27% | 78% | 353 | 63% | 68% |
| Soul Fysh | 3,001 | 68% | 79% | 382 | 82% | 67% |

Act 2

| Boss | AI visits | AI kill rate | AI HP share | Human visits | Human kill rate | Human HP share |
|---|---|---|---|---|---|---|
| Kaiser Crab | 1,582 | 3% | 70% | 387 | 65% | 73% |
| Knowledge Demon | 1,417 | 10% | 57% | 367 | 80% | 72% |
| The Insatiable | 1,409 | 14% | 56% | 388 | 82% | 71% |

### 9. Who would win from whose hand

Act 1 boss (18,401 AI visits, 8,725 human visits for the model, 2,155 exam-fifth visits)

| Kill share | AI's entry states | Humans' entry states |
|---|---|---|
| Actual kill share | 51.5% | 74.8% |
| Human-trained model on that group's entry states | 68.8% | 74.0% |
| AI-trained model on that group's entry states | 51.5% | 56.4% |

| Moving the AI's average to the human exam average | AI now | Human | AI model: change in the AI's kill share (points) | Human model: change in the humans' kill share if their average moved to the AI's (points) |
|---|---|---|---|---|
| HP share at entry | 79% | 67% | -10.1 | +7.2 |
| Max HP | 82.8 | 81.2 | -1.4 | +0.4 |
| Upgraded cards | 2.8 | 2.9 | +0.5 | -0.4 |
| Relics | 4.2 | 6.0 | +7.6 | -3.1 |
| Potions | 0.7 | 1.6 | +10.4 | -9.0 |
| Attack cards | 11.1 | 9.5 | -4.5 | +1.8 |
| Skill cards | 5.2 | 7.6 | +4.7 | -4.1 |
| Power cards | 1.2 | 1.1 | -0.6 | +0.4 |
| Gold | 99 | 150 | -1.1 | -0.0 |
| All of these together |  |  | +5.9 | -5.4 |

Act 2 boss (4,408 AI visits, 4,486 human visits for the model, 1,142 exam-fifth visits)

| Kill share | AI's entry states | Humans' entry states |
|---|---|---|
| Actual kill share | 8.8% | 75.7% |
| Human-trained model on that group's entry states | 35.9% | 74.8% |
| AI-trained model on that group's entry states | 8.8% | 31.3% |

| Moving the AI's average to the human exam average | AI now | Human | AI model: change in the AI's kill share (points) | Human model: change in the humans' kill share if their average moved to the AI's (points) |
|---|---|---|---|---|
| HP share at entry | 61% | 72% | +3.2 | -4.9 |
| Max HP | 85.4 | 84.3 | -0.2 | +0.3 |
| Upgraded cards | 5.7 | 6.9 | +1.4 | -2.2 |
| Relics | 8.1 | 11.5 | +3.8 | -8.8 |
| Potions | 0.6 | 1.9 | +4.8 | -9.0 |
| Attack cards | 15.8 | 11.4 | +0.8 | -8.5 |
| Skill cards | 7.6 | 11.1 | +1.3 | -1.0 |
| Power cards | 2.1 | 2.5 | +0.1 | +0.0 |
| Gold | 100 | 186 | -0.3 | -0.0 |
| All of these together |  |  | +22.4 | -38.6 |

### 10. The same figures by night (path and choices before the Act 1 boss)

| Night | Arm | Agent | Visits to the boss | Cards taken | Skip rate | Upgrades | Heals | Fights / elites / shops / ? rooms |
|---|---|---|---|---|---|---|---|---|
| 2026-10-26 | emulator | g5 | 1,597 | 6.30 | 11% | 2.37 | 0.60 | 5.3 / 0.57 / 0.99 / 4.1 |
| 2026-10-27 | real game | g7 | 1,350 | 5.60 | 14% | 1.59 | 1.78 | (logged only where a choice existed) |
| 2026-10-27 | emulator | g7 | 1,664 | 5.59 | 14% | 1.56 | 1.79 | 4.8 / 0.55 / 1.29 / 4.0 |
| 2026-10-29 | real game | g7 | 1,554 | 5.64 | 15% | 1.51 | 1.78 | (logged only where a choice existed) |
| 2026-10-29 | emulator | g7 | 1,651 | 5.66 | 14% | 1.51 | 1.76 | 4.9 / 0.59 / 1.30 / 3.9 |
| 2026-10-30 | real game | g9 | 1,285 | 5.26 | 19% | 1.90 | 1.43 | (logged only where a choice existed) |
| 2026-10-30 | emulator | g9 | 1,822 | 5.28 | 18% | 1.91 | 1.42 | 5.0 / 0.45 / 1.32 / 3.9 |
| 2026-10-31 | real game | g9 | 433 | 5.18 | 19% | 1.90 | 1.43 | (logged only where a choice existed) |
| 2026-10-31 | emulator | g9 | 449 | 5.23 | 18% | 1.92 | 1.41 | 4.9 / 0.46 / 1.31 / 4.0 |
| 2026-11-01 | real game | g9 | 455 | 5.30 | 17% | 1.94 | 1.37 | (logged only where a choice existed) |
| 2026-11-01 | emulator | g9 | 466 | 5.32 | 18% | 1.91 | 1.41 | 4.9 / 0.51 / 1.32 / 4.0 |
| 2026-11-02 | real game | g9 | 457 | 5.30 | 17% | 2.05 | 1.33 | (logged only where a choice existed) |
| 2026-11-02 | emulator | g9 | 460 | 5.32 | 17% | 2.00 | 1.37 | 4.9 / 0.45 / 1.33 / 3.9 |

### 11. Self-play by generation (reached the Act 1 boss)

| Agent | Runs | Mean floor | Kill Act 1 boss | HP / max | Cards | Upgraded | Relics | Potions | Elites | Cards taken |
|---|---|---|---|---|---|---|---|---|---|---|
| gen 5 | 3,179 | 17.5 | 19.2% | 44.5 / 81.1 | 19.8 | 3.2 | 4.2 | 0.8 | 0.55 | 6.37 |
| gen 6 | 4,064 | 19.2 | 31.8% | 57.9 / 80.6 | 18.5 | 3.0 | 4.0 | 0.8 | 0.49 | 5.57 |
| gen 7 | 3,012 | 19.5 | 36.5% | 64.4 / 83.2 | 18.8 | 2.5 | 4.2 | 0.7 | 0.56 | 5.60 |
| gen 8 | 2,938 | 21.9 | 48.5% | 68.0 / 83.3 | 18.3 | 2.6 | 4.0 | 0.7 | 0.50 | 5.28 |
| gen 9 | 20,049 | 22.6 | 51.5% | 65.5 / 82.8 | 18.8 | 2.8 | 4.2 | 0.7 | 0.45 | 5.30 |

### 12. Potions and elites before the boss

| Act | Group | Visits | Potion rewards taken | Potion rewards left | Elites fought | Elite taken when on offer | Map choices with an elite on offer |
|---|---|---|---|---|---|---|---|
| Act 1 | AI gen 9 | 18,401 | 2.60 | 0.50 | 0.45 | 18% | 2.5 |
| Act 1 | Humans (exam fifth) | 2,155 | 3.55 | 0.77 | 1.95 | . | . |
| Act 2 | AI gen 9 | 4,408 | 2.15 | 0.78 | 0.71 | 31% | 2.3 |
| Act 2 | Humans (exam fifth) | 1,142 | 3.41 | 0.99 | 1.75 | . | . |

Act 1 boss visits by the elites fought before it

| Elites fought | AI visits | AI kill share | AI HP share | AI relics | Human visits | Human kill share | Human HP share | Human relics |
|---|---|---|---|---|---|---|---|---|
| 0 | 11,174 | 52% | 82% | 3.8 | 176 | 61% | 73% | 4.3 |
| 1 | 6,281 | 51% | 75% | 4.6 | 507 | 72% | 71% | 5.2 |
| 2 | 910 | 51% | 70% | 5.5 | 806 | 74% | 66% | 6.1 |
| 3 or more | 36 | 67% | 64% | 6.2 | 666 | 81% | 64% | 6.9 |

Act 2 boss visits by the elites fought before it

| Elites fought | AI visits | AI kill share | AI HP share | AI relics | Human visits | Human kill share | Human HP share | Human relics |
|---|---|---|---|---|---|---|---|---|
| 0 | 1,918 | 9% | 70% | 7.5 | 122 | 71% | 77% | 9.0 |
| 1 | 1,875 | 9% | 57% | 8.4 | 306 | 71% | 74% | 10.5 |
| 2 | 570 | 9% | 47% | 9.4 | 473 | 75% | 71% | 11.9 |
| 3 or more | 45 | 13% | 37% | 10.3 | 241 | 85% | 69% | 13.3 |

### 13. Boss kill share by what the run brought

Act 1 boss

| Factor | Level | AI visits | AI kill share | Human visits | Human kill share |
|---|---|---|---|---|---|
| HP share on entry | under 50% | 1,933 | 9% | 375 | 57% |
|  | 50-70% | 3,095 | 35% | 816 | 72% |
|  | 70-85% | 4,253 | 56% | 539 | 82% |
|  | 85% or more | 9,120 | 64% | 425 | 87% |
| Potions held | 0 | 8,003 | 41% | 221 | 53% |
|  | 1 | 7,800 | 56% | 718 | 71% |
|  | 2 or more | 2,598 | 71% | 1,216 | 81% |
| Relics held | under 4 | 5,465 | 47% | 74 | 73% |
|  | 4-5 | 10,802 | 52% | 775 | 74% |
|  | 6-7 | 2,004 | 58% | 979 | 76% |
|  | 8 or more | 130 | 58% | 327 | 74% |
| Upgraded cards | 0-1 | 3,812 | 38% | 490 | 66% |
|  | 2-3 | 9,233 | 51% | 968 | 74% |
|  | 4-5 | 4,413 | 61% | 520 | 80% |
|  | 6 or more | 943 | 64% | 177 | 85% |
| Skill cards | under 5 | 5,973 | 51% | 55 | 69% |
|  | 5-7 | 11,630 | 52% | 1,005 | 73% |
|  | 8-10 | 786 | 49% | 983 | 77% |
|  | 11 or more | 12 | . | 112 | 78% |

Act 2 boss

| Factor | Level | AI visits | AI kill share | Human visits | Human kill share |
|---|---|---|---|---|---|
| HP share on entry | under 50% | 1,552 | 3% | 130 | 64% |
|  | 50-70% | 1,186 | 7% | 398 | 69% |
|  | 70-85% | 728 | 13% | 299 | 78% |
|  | 85% or more | 942 | 18% | 315 | 87% |
| Potions held | 0 | 2,250 | 7% | 103 | 54% |
|  | 1 | 1,693 | 10% | 270 | 69% |
|  | 2 or more | 465 | 16% | 769 | 81% |
| Relics held | under 4 | 0 | . | suppressed | . |
|  | 4-5 | 184 | 9% | suppressed | . |
|  | 6-7 | 1,526 | 8% | 41 | 66% |
|  | 8 or more | 2,698 | 9% | 1,096 | 76% |
| Upgraded cards | 0-1 | 55 | 13% | 20 | 60% |
|  | 2-3 | 651 | 6% | 128 | 72% |
|  | 4-5 | 1,478 | 7% | 242 | 69% |
|  | 6 or more | 2,224 | 11% | 752 | 79% |
| Skill cards | under 5 | 204 | 5% | suppressed | . |
|  | 5-7 | 2,038 | 9% | 84 | 69% |
|  | 8-10 | 1,797 | 8% | 389 | 77% |
|  | 11 or more | 369 | 10% | 659 | 76% |

### 14. The same, with the cards in the deck

Act 1 boss

| Model | AUC | Kill share on the AI's entry states | Kill share on the exam fifth's |
|---|---|---|---|
| Human model, nine entry features: AUC on exam fifth | 0.723 | 68.8% | 74.0% |
| Human model, with cards: AUC on exam fifth | 0.747 | 74.6% | 73.8% |
| AI model, nine entry features: AUC on held-out AI visits | 0.769 | 51.5% | 57.0% |
| AI model, with cards: AUC on held-out AI visits | 0.804 | 51.5% | 44.3% |

| Card (human model) | Effect per copy (log-odds) | Held at the boss by humans (other fifths) | AI picks it when offered | Humans pick it when offered |
|---|---|---|---|---|
| Spoils Map | -0.54 | 12% | . | . |
| Stone Armor | -0.38 | 10% | 74% | 32% |
| Feel No Pain | -0.36 | 8% | 0% | 27% |
| Injury | -0.34 | 6% | . | . |
| Body Slam | -0.19 | 7% | 0% | 10% |
| Inflame | -0.17 | 12% | 71% | 36% |
| Anger | +0.26 | 17% | 82% | 20% |
| Unrelenting | +0.35 | 10% | 94% | 34% |
| Battle Trance | +0.36 | 18% | 2% | 61% |
| Ashen Strike | +0.36 | 8% | 2% | 31% |
| Dominate | +0.60 | 20% | 92% | 73% |
| Fight Me | +0.62 | 12% | 97% | 40% |

Act 2 boss

| Model | AUC | Kill share on the AI's entry states | Kill share on the exam fifth's |
|---|---|---|---|
| Human model, nine entry features: AUC on exam fifth | 0.712 | 35.9% | 74.8% |
| Human model, with cards: AUC on exam fifth | 0.746 | 35.3% | 74.7% |
| AI model, nine entry features: AUC on held-out AI visits | 0.716 | 8.6% | 28.1% |
| AI model, with cards: AUC on held-out AI visits | 0.755 | 8.6% | 34.7% |

| Card (human model) | Effect per copy (log-odds) | Held at the boss by humans (other fifths) | AI picks it when offered | Humans pick it when offered |
|---|---|---|---|---|
| Stampede | -0.41 | 18% | 21% | 25% |
| Inferno | -0.29 | 19% | 38% | 19% |
| Whirlwind | -0.28 | 14% | 35% | 17% |
| Rage | -0.26 | 16% | 23% | 28% |
| Ultimate Strike | -0.21 | 7% | . | . |
| True Grit | -0.21 | 30% | 3% | 19% |
| Bully | +0.26 | 14% | 71% | 27% |
| Battle Trance | +0.26 | 35% | 20% | 60% |
| Crimson Mantle | +0.33 | 12% | . | . |
| Exterminate | +0.34 | 5% | . | . |
| Fight Me | +0.35 | 18% | 35% | 23% |
| Dominate | +0.36 | 36% | 27% | 68% |

### 15. The per-decision exam: the AI's chooser on the humans' states (held-out fifth)

2,968 exam-fifth runs, 40,593 decisions scored in Acts 1 and 2 (4 without donor maps).

Card rewards

| Act | Decisions | AI picks what the human picked | Human's pick is the AI's first or second | Human skips | AI would skip | Same take-or-skip | Floors the AI thinks the human's pick loses |
|---|---|---|---|---|---|---|---|
| Act 1 | 19,733 | 33% | 56% | 14% | 14% | 76% | 0.37 |
| Act 2 | 9,439 | 26% | 50% | 34% | 7% | 64% | 0.15 |
| Both | 29,172 | 31% | 54% | 21% | 12% | 73% | 0.30 |

Cards the AI's chooser would take far less or far more often than the humans did, from the same states (cards offered 150 times or more)

| Card | Offered | Human took it | AI would take it | Gap (points) |
|---|---|---|---|---|
| Battle Trance | 914 | 61% | 7% | -54 |
| Bloodletting | 2,732 | 40% | 1% | -39 |
| Flame Barrier | 932 | 49% | 13% | -36 |
| Burning Pact | 950 | 36% | 1% | -34 |
| Feel No Pain | 967 | 30% | 2% | -27 |
| Shrug It Off | 2,685 | 41% | 14% | -27 |
| Whirlwind | 932 | 32% | 7% | -24 |
| Ashen Strike | 909 | 31% | 7% | -24 |
| Stone Armor | 973 | 29% | 70% | +41 |
| Perfected Strike | 2,673 | 25% | 68% | +44 |
| Fight Me | 913 | 35% | 81% | +46 |
| Twin Strike | 2,675 | 16% | 65% | +49 |
| Stomp | 952 | 30% | 82% | +52 |
| Bully | 880 | 30% | 81% | +52 |
| Anger | 2,597 | 15% | 71% | +56 |
| Unrelenting | 869 | 29% | 90% | +61 |

Rest sites: the share spent on an upgrade, by HP on arrival

| Act | HP on arrival | Decisions | Human upgrades | AI would upgrade | Same choice |
|---|---|---|---|---|---|
| Act 1 | <40% | 2,195 | 17% | 21% | 70% |
| Act 1 | 40-60% | 2,287 | 55% | 36% | 46% |
| Act 1 | 60-80% | 2,064 | 83% | 48% | 49% |
| Act 1 | >=80% | 1,079 | 97% | 96% | 93% |
| Act 2 | <40% | 1,114 | 12% | 28% | 67% |
| Act 2 | 40-60% | 1,139 | 45% | 43% | 50% |
| Act 2 | 60-80% | 980 | 79% | 59% | 53% |
| Act 2 | >=80% | 563 | 95% | 95% | 91% |

### 16. The loop's saved fight starts (nightly emulator arms, 50 runs a night)

| Night | Boss | Starts | HP / max | HP share | Cards | Relics | Potions |
|---|---|---|---|---|---|---|---|
| 2026-10-26/g5 | Act 1 | 41 | 42.1 / 81.2 | 52% | 20.2 | 4.5 | 0.8 |
| 2026-10-27/g7 | Act 1 | 40 | 64.5 / 82.8 | 78% | 18.9 | 4.5 | 0.8 |
| 2026-10-29/g7 | Act 1 | 41 | 59.8 / 83.5 | 72% | 19.3 | 4.3 | 0.9 |
| 2026-10-30/g9 | Act 1 | 46 | 64.0 / 82.2 | 78% | 18.5 | 4.2 | 0.7 |

## Proposed night logging (a unified diff, not applied)

What the nightly cannot tell us today is the real arm's state at a boss (and at the fight that killed a run before it): its rows keep
`cards`, `nodes` and `rests` only, and the real arm's map letters skip forced steps. The fields below close that for both arms with the
same keys, so a night's `runs.jsonl` can feed `tools/boss_entry.py` directly:

- `fight_starts`: `[[floor, "M|E|B|?", hp, max_hp, gold, cards, upgraded cards, relics, potions], ...]`, one compact row per fight as it
  opens. The last row of a run that died before a boss is the fight that killed it (the "died before the boss" cohort).
- `boss_entries`: `[{"act", "floor", "hp", "max_hp", "gold", "deck", "relics", "potions"}, ...]`, the full holdings (deck as `NAME` or
  `NAME+`, relics and potions by name) as each act's boss opens.

Where they come from: the real arm's referee observation (`obs.hp`, `max_hp`, `gold`, `deck`, `relics`, `potions`, `act`, `floor`)
at the first decision of each fight, which `referee/lockstep.py` `_track` already sees (`msg["obs"]`); the emulator arm's run session
view (`s.view()`, the same call `RunRecorder.open_fight` makes) at the moment `rl/gen0.py` `play_emu_run` opens a fight. Both go through
`RunFields` in `rl/run_fields.py`, whose `row()` is what `gen0.py` (line 301) and `referee/envproto.py` (line 588) write into the row;
`RUN_FIELD_KEYS` in `gen0.py` lets an envproto end event carry the two keys. Cost: one `view()` per fight on the emulator arm and a few
hundred bytes a fight. The real arm's forced map steps (and so its chest, shop and rest counts) stay unlogged: the referee's `obs` as read
here carries no room type, so that would need a driver field. The diff is against the fork's HEAD at the time (58f8c307) because worker A
is editing `rl/`; it applies cleanly there (`git apply --check`), the three files compile, and the new `RunFields` methods were run on a
sample observation (`fight_starts` and one `boss_entries` row per act). It has no test yet in the fork: the first edit should add one
beside `tests` for `run_fields`.

```diff
diff --git a/referee/lockstep.py b/referee/lockstep.py
index 7b6db85..cbdd4bf 100644
--- a/referee/lockstep.py
+++ b/referee/lockstep.py
@@ -401,6 +401,7 @@ class Lockstep:
             if self.prev_kind not in COMBAT_KINDS or (rnd is not None and self.round is not None and rnd < self.round):
                 names = sorted(str(e.get("name")) for e in c.get("enemies") or [] if isinstance(e, dict))
                 self.roster = "+".join(names) or None  # a new fight: the enemies it began with
+                self._fields("real_fight_start", msg.get("obs") or {}, self.room_type)  # the run's holdings as the fight opens
             advanced = rnd is not None and before is not None and rnd > before
             self.round = rnd
         self.ctx = {"acted": self.prev_act, "turn": self.round, "turn_advanced": advanced, "encounter": self.roster,
diff --git a/rl/gen0.py b/rl/gen0.py
index ea5c229..6307bbe 100644
--- a/rl/gen0.py
+++ b/rl/gen0.py
@@ -144,7 +144,7 @@ def result_json(runs: list[dict], wall_s: float, generation: int = 0) -> dict:
             "crashes": t["crashes"]}
 
 
-RUN_FIELD_KEYS = ("boss_damage", "boss_damage_acts", "cards", "nodes", "rests")  # rl/run_fields.py: what an envproto end event adds to its row
+RUN_FIELD_KEYS = ("boss_damage", "boss_damage_acts", "cards", "nodes", "rests", "fight_starts", "boss_entries")  # rl/run_fields.py: what an envproto end event adds to its row
 
 
 def real_runs(runs_jsonl: str | Path) -> list[dict]:
@@ -263,6 +263,7 @@ def play_emu_run(seed: str, ix: int, sims: int | str, ascension: int = 10, agent
                 continue
             if fight_boss is None:
                 fight_boss = s.info["node_type"] == engine.vocab.NODE_BOSS
+                fields.emu_fight_start(s.view(), s.info["node_type"])  # the run's holdings as this fight opens
             if fight_boss:  # the combat observation opens the run observation: the boss's HP at this decision
                 fields.boss_enemies(s.act_index, run_fields.obs_enemies(env._run_obs_buf, native.OBS_ENEMY_OFFSET,
                                                                        native.OBS_ENEMY_SLOT_SIZE, native.MAX_ENEMIES))
diff --git a/rl/run_fields.py b/rl/run_fields.py
index 3d428b2..b538b98 100644
--- a/rl/run_fields.py
+++ b/rl/run_fields.py
@@ -11,6 +11,10 @@
   nodes             the map node types taken in order, one letter each: M monster, E elite, R rest, S shop, T treasure, B boss,
                     ? unknown, A ancient (x: a type this table lacks).
   rests             [[floor, "heal" | "smith" | ...], ...]: each rest site choice (leaving is not recorded).
+  fight_starts      [[floor, "M" | "E" | "B" | "?", hp, max_hp, gold, cards, upgraded cards, relics, potions], ...]: the run's state as each
+                    fight opens (the last row of a run that died before a boss is the fight that killed it).
+  boss_entries      [{"act", "floor", "hp", "max_hp", "gold", "deck", "relics", "potions"}, ...]: the full holdings as an act's boss opens
+                    (deck as "NAME" / "NAME+", relics and potions by name). Both arms write the same keys (tools/boss_entry.py reads them).
 Shop buys are not recorded: the referee's shop label carries a slot and a price, not the item, so a buy needs new plumbing.
 
 A row without these keys is an older row: absent means unknown, never 0 (the guard stays inert on such rows).
@@ -41,15 +45,19 @@ LEAVE_LABELS = ("leave", "proceed")
 EMU_NODE_CODES = {1: "M", 2: "E", 3: "R", 4: "S", 5: "T", 6: "B", 7: "?", 8: "A"}
 
 
-@functools.lru_cache(maxsize=1)
-def card_slugs() -> dict[int, str]:
-    """Emulator card id -> the referee's card name (the lockstep's slug), so both sides write one id scheme."""
+@functools.lru_cache(maxsize=4)
+def id_slugs(section: str = "cards") -> dict[int, str]:
+    """Emulator id -> the referee's name (the lockstep's slug) for "cards", "relics" or "potions", so both sides write one id scheme."""
     from run_train import vocab  # noqa: PLC0415
 
-    ids = json.loads((ROOT / "data" / "id_map.json").read_text(encoding="utf-8"))["cards"]
+    ids = json.loads((ROOT / "data" / "id_map.json").read_text(encoding="utf-8"))[section]
     return {v: vocab.game_slug(n) for n, v in ids.items()}
 
 
+def card_slugs() -> dict[int, str]:
+    return id_slugs("cards")
+
+
 def obs_enemies(obs: Sequence[int], offset: int, slot_size: int, slots: int) -> list[tuple[int, int, int]]:
     """(slot, hp, max_hp) of every enemy slot of a combat observation (a dead enemy keeps its slot at 0 HP; an empty slot has no max)."""
     out = []
@@ -94,6 +102,8 @@ class RunFields:
         self.cards: list[list] = []  # [floor, card name | name+ (upgraded) | "skip"] per card reward decided
         self.nodes: list[str] = []  # the map node types taken, one letter each, in order
         self.rests: list[list] = []  # [floor, "heal" | "smith" | ...] per rest site choice
+        self.starts: list[list] = []  # one compact row per fight opened (see the module docstring)
+        self.entries: list[dict] = []  # the full holdings as each act's boss opens
 
     @property
     def in_boss_fight(self) -> bool:
@@ -157,12 +167,37 @@ class RunFields:
             # label this table lacks is recorded as its own text, never as a heal.
             self.rests.append([floor, label.lower()])
 
+    def fight_start(self, act: int, floor: int, kind: str, hp: int, max_hp: int, gold: int, deck: Sequence[str], relics: Sequence[str],
+                    potions: Sequence[str]) -> None:
+        """A fight opens: the run's holdings now. `deck` is "NAME" / "NAME+" per card. The first boss fight of an act also keeps the
+        full holdings (the sorted deck, relics and potions)."""
+        self.starts.append([int(floor), kind, int(hp), int(max_hp), int(gold), len(deck), sum(1 for c in deck if str(c).endswith("+")),
+                            len(relics), len(potions)])
+        if kind == "B" and not any(e["act"] == int(act) for e in self.entries):
+            self.entries.append({"act": int(act), "floor": int(floor), "hp": int(hp), "max_hp": int(max_hp), "gold": int(gold),
+                                 "deck": sorted(map(str, deck)), "relics": sorted(map(str, relics)), "potions": sorted(map(str, potions))})
+
+    def emu_fight_start(self, view: Any, node_type: int) -> None:
+        """The emulator side: `view` is the run session's RunView as the fight opens, `node_type` the room's (EMU_NODE_CODES)."""
+        cards, relics, potions = id_slugs("cards"), id_slugs("relics"), id_slugs("potions")
+        self.fight_start(view.act_index, view.floor, EMU_NODE_CODES.get(node_type, "x"), view.hp, view.max_hp,
+                         view.gold, [cards.get(c.card_id, f"?{c.card_id}") + ("+" if c.upgraded else "") for c in view.deck],
+                         [relics.get(r, f"?{r}") for r in view.relics], [potions.get(p, f"?{p}") for p in view.potions])
+
+    def real_fight_start(self, obs: dict, room_type: Any) -> None:
+        """The real-game side: the referee's `obs` as a fight opens and the last map label's room type (stale at a boss: the floor names it)."""
+        kind = "B" if is_boss_floor(obs.get("act"), obs.get("floor")) else NODE_CODES.get(str(room_type), "?")
+        deck = [str(c[0]) + ("+" if len(c) > 1 and c[1] else "") for c in obs.get("deck") or []]
+        self.fight_start(obs.get("act") or 0, obs.get("floor") or -1, kind, obs.get("hp") or 0, obs.get("max_hp") or 0, obs.get("gold") or 0,
+                         deck, [str(r) for r in obs.get("relics") or []], [str(p) for p in obs.get("potions") or [] if p])
+
     def row(self) -> dict:
         """The keys for the run's row (an open boss fight is closed as lost: the run stopped in it)."""
         self.boss_over(won=False)
         first = next((frac for act, frac in self.bosses if act == 0), 0.0)
         return {"boss_damage": first, "boss_damage_acts": [list(b) for b in self.bosses],
-                "cards": [list(c) for c in self.cards], "nodes": "".join(self.nodes), "rests": [list(r) for r in self.rests]}
+                "cards": [list(c) for c in self.cards], "nodes": "".join(self.nodes), "rests": [list(r) for r in self.rests],
+                "fight_starts": [list(s) for s in self.starts], "boss_entries": [dict(e) for e in self.entries]}
 
 
 def aggregate(rows: Iterable[dict]) -> dict:
```

## Rerunning it

With the GPU venv's Python (`-I`), single process, BelowNormal (the tools set it themselves), nothing starts the game or the emulator.
Caches live in `referee/backlog/boss-entry/` (not committed; the human cache holds one reduced line per run, so it stays out of the repo).

```
python -I tools/boss_entry.py human    --out human.jsonl.gz --exam-ids human-exam-fifth-ids.txt     # about 2 minutes
python -I tools/boss_entry.py selfplay --gens 5-9 --out selfplay.jsonl.gz                           # about 2 minutes
python -I tools/boss_entry.py nights   --out nights.jsonl.gz                                        # seconds
python -I tools/boss_entry.py check    --limit 3000                                                 # the deck replay check
python -I tools/boss_entry_exam.py validate --n-runs 150 --donor-runs 600                           # the map-donor check
python -I tools/boss_entry_exam.py exam --out exam-rows.json                                        # about 11 minutes
python -I tools/boss_entry_report.py --human human.jsonl.gz --selfplay selfplay.jsonl.gz --nights nights.jsonl.gz --exam exam-rows.json --out tables.md
```

The exam needs the fork's `rl/run_train` on disk (read only), the generation 9 `run_value.npz` and the self-play shards for the donor
maps. A later generation: change `--gen` and the weights path in `tools/boss_entry_exam.py`.
