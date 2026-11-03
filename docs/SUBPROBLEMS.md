# The sub-problem board: six pieces of the AI's game, each against the humans

Written 2026-11-03 22:10Z (D51 item 3, PLAN section 14 item 1). The gap to the humans is not one number; it is six pieces that can be worked one at a
time, each with a test that finishes in minutes on the copy of the game, and each guarded by the slow test that decides: the real-game block of
2,000 fresh seeds must not fall. **A piece lands when its number improves and that block does not fall.** Nothing here runs the game or the
emulator; every figure was read from files on this PC (paths relative to `D:/spireline/`). Times are Z.

Terms. "Block" is the nightly real-game run of the exam agent, 2,000 seeds when an agent has just been promoted, 500 otherwise.
"Door" is the moment a boss fight opens. "Humans" is the held-out fifth of the human corpus (2,924 vanilla Ironclad Ascension 10 runs of
14,745, D38), read only to score the AI; every human cell is an aggregate over at least 20 runs (D13). "Gen 11" is the exam agent since
2026-11-02: the trainer's fight player with generation 9's run-level head (the same weights, sha256 `f0a199fb...`, checked 2026-11-03), so the
11-02 per-decision exam of that head still describes gen 11's card, rest and map choices.

## The six pieces at a glance

The table is rendered by `python tools/subproblems.py refresh --out docs/subproblems.json --render docs/SUBPROBLEMS.md` (about 11 seconds) from
the newest finished night of at least 1,000 rows (a 2,000-seed block over a 500-seed check), the lab's self-play shards, the fight board, the exam rows and the human cache; do not edit it by hand. "Gap" is
the AI minus the humans in the unit of the row. "Could buy" is what the 2026-11-02 diagnostic's two fits say closing the gap is worth at the
Act 1 boss, in points of boss kill (an association inside the fits, not a test; Act 2 values are in each section).

<!-- subproblems:table:start -->
| Piece | Counted | AI now | Humans | Gap (AI minus humans) | Closing it could buy (points of boss kill, Act 1) | Fast test and run time |
|---|---|---|---|---|---|---|
| 1. First-boss fight | Act 1 boss killed, of runs that reach it | 56.5% (night 2026-11-03, 1,852 fights) | 74.8% (2,155 visits) | -18.3 | 17 to 23 (the play, not the hand) | fight board, 200 Act 1 boss starts x 10 replays: 400 games in about 8 minutes (the gate's stage 1), 2,000 in about 35 |
| 2. Act 2 fights by kind | Act 2 fights survived: hallway / elite / boss | 92.2% / 65.8% / 12.8% (night 2026-11-03, 475 boss fights) | 97.3% / 88.6% / 75.7% (1,142 boss visits) | -5.1 / -22.8 / -62.9 | 27 to 44 (the play); 22 to 39 is the hand | the gym's Act 2 start sets (hallway, elite, boss) in the loop's weights step: 100 games a kind, about 14 minutes for the three |
| 3. Route | Elites fought before the Act 1 boss, per run that reaches it | 0.46 (emulator arm, night 2026-11-03, 1,849 runs) | 1.95 (2,155 runs) | -1.49 elites | 0 to +6 net of the HP the fights cost | `subproblems.py refresh`: the emulator arm's rows and the shards, about 11 seconds; a fresh 200-run batch about 8 minutes |
| 4. Card picks and skips | Card rewards where the AI's chooser takes the human's pick, Act 1 / Act 2; Act 2 skip share | 33% / 26% (a coin: 25%); would skip 7%; fast-test baseline 30.6% cards / 60.7% rests (14,013 decisions) | skip 34% (9,439 Act 2 decisions) | -26.4 (skip share) | 0 to +2 (Act 2: +2 to +10) | `boss_entry_exam.py agreement` on a seeded 1,000 runs of the held-out fifth (14,013 decisions): 8 minutes for a candidate and the incumbent (the full exam: 11 minutes) |
| 5. Potions | Potions held at the Act 1 boss door; potions used a run before it, and where | 0.8 held (856 visits); 2.3 used a run before it, 2.0 in hallway fights | 1.6 held (2,155 visits); 2.0 used a run before it, 0.6 in hallway fights | -0.8 potions | +9 to +10 | `subproblems.py refresh`: the shards' potions at the doors and in fights, and the board's replays, about 11 seconds |
| 6. Shops and relics | Relics held at the Act 1 boss door, and bought in shops before it | 4.2 held, 0.11 bought (856 visits) | 6.0 held, 0.28 bought (2,155 visits) | -1.8 relics | +3 to +8 (relics); gold 0 | `subproblems.py refresh`: the shards' relics, gold and shop buys at the doors, about 11 seconds |

Rendered by `tools/subproblems.py` from `docs/subproblems.json` (2026-11-03T22:10:49Z; newest finished night 2026-11-03). Edit the numbers by rerunning the tool, not by hand.
<!-- subproblems:table:end -->

## 1. The first-boss fight

- **AI now.** The Act 1 boss is killed in **56.5%** of the runs that reach it (1,046 of 1,852; real game, folder `referee/LAB/nightly/2026-11-03`,
  generation 11, 2,000 seeds, plus or minus 2.3 at 95%; the emulator arm 56.7% of 1,849). Generation 9 over its four real nights: 52.9%.
  By boss, generation 9 on 18,401 emulator visits (diagnostic table 8): Ceremonial Beast 73%, Soul Fysh 68%, Lagavulin Matriarch 56%,
  Vantom 43%, The Kin 41%, Waterfall Giant 27%. The AI does not arrive weak: 77.6% of its HP against the humans' 67.4% (856 gen 11 self-play
  visits; `referee/LAB/runs/*selfplay*/shards`, no exploration). In Act 1 the AI survives the ordinary fights at least as often as the humans:
  hallway 99.5% of 11,175 real fights (humans 99.1% of 12,956), elite 94.2% of 939 (humans 88.5% of 5,238, but it fights far fewer: 0.46 a run
  against 1.95). The Act 1 gap is the boss alone.
- **Humans.** **74.8%** (1,611 of 2,155 visits, plus or minus 1.8; boss-entry diagnostic table 1, 2026-11-02, exam fifth), by boss 63 to 82%.
- **Gap.** -18.3 points (gen 9: -23.3). Of the gen 9 gap, the fits put 0 to 5 points on the hand the AI brings and 17 to 23 on how the fight is
  played; so this is the largest piece in Act 1.
- **Fast test.** The fight board: `referee/gym-loop/board/fp-v*.jsonl`, 200 saved Act 1 boss starts (real fights from earlier real nights),
  ten replays each, one fight player per file. Read by `tools/subproblems.py refresh` in seconds; replaying is the loop's gate: stage 1
  plays 400 games in about 8 minutes (11-03 18:40 to 18:48Z), stage 2 another 1,600 in about 27 (to 19:15Z). A pass is a paired win-rate gain
  over the incumbent at McNemar p under 0.05 on 2,000 pairs. Latest rows: v2 (`c0019`) wins **941 of 2,000 = 47.05%** (53 starts always won,
  61 never won); v1 45.7%; the search without a trained player (`judge-v0`) 44.1%; `a3-v1` 36.9% (`2026-11-01-facts.md` section 0). The board is a
  ruler for comparing fight players on a fixed set, not an estimate of the real kill rate (47.0 against 52 to 57%). The gym's own per-kind
  rate for the Act 1 boss, 100 games, is 54% (`starts/weights.json`, 2026-11-03 01:05Z).
- **Slow test.** The block's Act 1 boss kill of reached runs and of all runs (52.5%, 2.2 points either way at 2,000), and its mean floor 23.41
  (SE 0.18). The loop has promoted nothing since v2 (2026-10-31 14:30Z): since then c0084 (+0.5 points, p 0.21), c0109 (+1.1, p 0.052) and
  c0120 (+0.4, p 0.31) failed stage 2 (`referee/gym-loop/loop.log`).
- **Owner lane.** The trainer (the always-on loop), with the engine lane for speed.
- **First thing to try.** Build the human-run Act 1 boss starts (D38, PLAN item 5) and put the three weakest bosses' starts (Waterfall Giant,
  The Kin, Vantom) into the loop's practice, then read the board per boss.
- **Not measured.** The fight player against the humans on the same starts (no human fight start exists in the AI's form); the real arm's
  HP entering a boss (recorded nowhere in the rows; the diagnostic's proposed night logging would give it).

## 2. Act 2 fights by enemy kind

- **AI now.** Act 2 fights survived, real game, gen 11, folder `2026-11-03`: **hallway 92.2% (4,398 fights), elite 65.8% (661), boss 12.8%
  (475)**; emulator arm 93.4% (3,832), 65.0% (682), 11.7% (486). Only 24% of runs (478 of 1,992) reach the Act 2 boss, and the table counts
  fights, not runs. The gym's per-kind rates for v2 (the incumbent at the nightly's search settings on 100 games of training starts a kind,
  2026-11-03 01:05Z): hallway 94%, elite 62%, boss 9%, so the gym reads the same ordering as the block. By boss, generation 9 (diagnostic table 8):
  Kaiser Crab 3% of 1,582 visits, Knowledge Demon 10% of 1,417, The Insatiable 14% of 1,409. At the Act 2 boss gen 9 holds 52.2 of 85.4 HP (61%),
  0.6 potions, 8.1 relics, 15.8 attacks and 7.6 skills (diagnostic table 3).
- **Humans.** Act 2 boss **75.7%** (865 of 1,142 visits, plus or minus 2.5; Kaiser Crab 65%, Knowledge Demon 80%, The Insatiable 82%); they die
  before the Act 2 boss in 29% of the runs that enter Act 2, the AI in 53%. The per-fight survival of the humans (the exam fifth, one pass over
  the corpus on 2026-11-03, `tools/subproblems.py humans`, 84 seconds): **hallway 97.3% of 6,176 fights, elite 88.6% of 2,429, boss 75.7% of
  1,142**.
- **Gap.** Hallway -5.1, elite -22.8, boss -62.9 points (gen 9 boss: -66.9). So Act 2 is not the boss alone: the AI survives an Act 2
  elite 23 points less often than the humans, and fights only 0.66 of them a run (humans 1.75). The fits: 22 to 39 points of it are the hand (HP, potions, relics, a less attack-heavy deck:
  pieces 3 to 6), 27 to 44 the play.
- **Fast test.** The gym's Act 2 start sets in `referee/gym-loop/starts` (hallway 2,660, elite 475, boss 306 starts, 65 of the boss starts from
  the gen 11 night): the loop's weights step plays 100 games a kind; the whole six-kind step took 28 minutes (2026-11-03 00:37Z to
  01:05Z), so the three Act 2 kinds take about 14. There is no Act 2 fight board yet (the board is Act 1 boss only); the cheapest build is the
  same board file on the 306 `act2-boss` starts, ten replays each. A pass: the Act 2 kind rates rise on the same start sets with the Act 1 kinds not
  falling.
- **Slow test.** The block's per-fight survival table (`tools/morning_report.py`, the `fights` section; Act 2 boss 12.8% of 475 real fights, 63
  runs in 2,000 kill it) and its mean floor.
- **Owner lane.** The trainer for the play; the run planner for the hand.
- **First thing to try.** Weight the loop's practice toward Act 2 (its start mix, `starts/weights.json`, gives Act 2 boss starts 7.5% against
  33.8% for Act 1 boss starts, and Act 2 elites 7.2%) and start with Kaiser Crab, where the AI wins 3 in 100 and humans 65, and the Act 2 elites
  (66 against 89).
- **Not measured.** The real arm's Act 2 survival per enemy (the table is by kind; per enemy it exists for the emulator only, and for the
  humans not at all); an Act 2 fight board (below).

## 3. The route: elites, rests, paths

- **AI now.** **0.46 elites** fought before the Act 1 boss per run that reaches it (emulator arm of folder `2026-11-03`, 1,849 runs; every map
  step is logged there; gen 11 self-play 0.46 of 856; gen 9 0.45 of 18,401). Fights 5.4 (humans 6.6), rests 3.3, shops 1.4. It takes an elite in
  19% of the map choices that offer one (gen 11 self-play; Act 2: 35%). In Act 2: 0.66 elites (humans 1.75).
- **Humans.** **1.95 elites** before the Act 1 boss (2,155 runs), 1.75 in Act 2 (1,142), 6.6 fights, 3.3 rests, 0.9 shops (boss-entry cache, exam fifth).
- **Gap.** -1.49 elites. Worth, net of what the fights cost in HP: **0 to +6 points** at the Act 1 boss (diagnostic ranked table, row 1). Inside the
  AI's own runs the elite count does not move the boss kill (52%, 51%, 51% for 0, 1, 2 elites; each elite costs about 7 points of HP share and
  brings about 0.9 relics), so the route is not a free gain; it pays only if the fight player keeps its HP.
- **Fast test.** `tools/subproblems.py refresh` (the emulator arm's rows and the shards; 11 seconds) and `tools/boss_entry.py selfplay` + `report`
  (the entry table on self-play shards, about 3 minutes for 20,000 runs). A fresh 200-run emulator batch for a new planner takes about 8 minutes
  (the emulator arm ran 2,000 runs in 82 minutes on 11-03). A pass: elites per run up toward 1.95 and the HP share at the door not falling more
  than the seven points an elite costs. There is **no per-decision test for map choices**: the human corpus holds the rooms visited, not the
  map, so the exam cannot rebuild the choice (diagnostic, exam section).
- **Slow test.** The block's emulator arm path letters and its Act 1 boss kill; the real arm logs a map letter only where it had a choice, so
  its elite count undercounts (0.07 against 0.45).
- **Owner lane.** The run planner (PLAN item 4, the fighter-matched run-level head trained on exploring runs).
- **First thing to try.** Train the run-level head against the fight player that exists now, on exploring runs (PLAN item 4), and read elites
  per run and HP share at the door before any block.

## 4. Card picks and skips

- **AI now.** On the humans' own card rewards (held-out fifth, 29,172 decisions, 2026-11-02), the AI's chooser takes the card the human took in
  **33% (Act 1; 19,733 decisions) and 26% (Act 2; 9,439)**, against a coin over the offer and skip of 25%; the human's pick is its first or
  second choice in 56% and 50%. It would skip 14% (Act 1) and **7% (Act 2)**. In its own games (real block, runs that reach each boss) it skips
  18.1% in Act 1 and 7.0% in Act 2. Its taste: Battle Trance 7% (humans 61%), Bloodletting 1% (40%), Flame Barrier 13% (49%), Shrug It Off 14%
  (41%); Anger 71% (15%), Twin Strike 65% (16%), Unrelenting 90% (29%) (diagnostic table 15). Same head as gen 9 (sha256 checked), so the
  numbers stand for gen 11.
- **Humans.** Skip 14.5% in Act 1 and **33.8% in Act 2** (exam rows); in the humans' own runs 14.7% and 34.1% of rewards before the boss. There
  is no human ceiling for the agreement: how often two humans (or the other four fifths) pick the same card is not measured.
- **Gap.** Act 2 skip share -26.4 points; agreement 33% against a coin's 25% and an unmeasured ceiling. Worth **0 to +2 points** at the Act 1
  boss and +2 to +10 at the Act 2 boss (diagnostic row 2); the cards matter less than the counts (Battle Trance and Ashen Strike show a clear
  positive effect, Shrug It Off and Bloodletting about zero). The same exam reads rest sites (not one of the six): the AI upgrades 44% of
  the time against the humans' 58% in Act 1 and agrees on 60% (Act 2: 50% against 51%).
- **Fast test.** `tools/boss_entry_exam.py agreement`: the chooser's picks on a seeded 1,000 runs of the held-out fifth, candidate head against
  incumbent head, counts and rates only. Run on 2026-11-03 with generation 11's head against generation 9's (one file, so the difference is
  zero): **8 minutes for the pair, 14,013 decisions**; the head takes the human's choice in **30.6% of 10,072 card rewards and 60.7% of 3,941
  rest sites**, and would skip 11.8% of rewards and upgrade at 44.7% of rests. That is the baseline a candidate is compared with (paired
  difference and its standard error). The full exam took 11 minutes (`exam`). A pass for a new head: its share of decisions that
  match the human's rises with a paired standard error under the gain, and the Act 2 skip share moves toward 34%.
- **Slow test.** The block's rows keep every card pick and skip by floor (the real arm too), so the block reads picks per run and skip share.
- **Owner lane.** The run planner.
- **First thing to try.** The fighter-matched run-level head (PLAN item 4), read first on Battle Trance, Shrug It Off and Bloodletting pick
  rates and the Act 2 skip share, before any block.
- **Not measured.** The human agreement ceiling (needs the exam run on one human fifth against a model of the others); shop choices (below).

## 5. Potions

- **AI now.** **0.8 potions held at the Act 1 boss door** (856 gen 11 self-play visits; 0.7 for gen 9, 18,401), 0.6 at the Act 2 door (227).
  **Where they go, a record that exists:** the self-play shards keep the run's state at every decision, so the potions entering a fight against
  the potions in the first state after it say how many were drunk in it (a won fight only; a lost fight ends the run). Cross-check: of the
  2.37 potions a run loses between decisions before the Act 1 boss, 2.33 (98%) fall inside fights the method sees. Before the Act 1 boss
  a run uses **2.3 potions, 2.0 of them in hallway fights (84%) and 0.38 in elites**. It holds a potion at the start of 50% of its Act 1 hallway
  fights, and in 60% of the hallway fights it wins holding one it drinks (2,666 fights); it wins 99.5% of Act 1 hallway fights (11,175, real
  block). At elites 96% and at bosses 99% of the won fights holding a potion used one. The board's replays agree about bosses: of 1,190 replays
  that began with a potion, 90% used one. So the potions that reach the door are what is left after hallway fights it would have won anyway;
  a run gains 3.2 potions (rewards, shops, events), uses 2.3 and holds 0.8. **The humans spend them differently:** of the fights they survive
  holding a potion they drink in 23% of Act 1 hallway fights, 66% of elites and 73% of bosses (Act 2: 31%, 64%, 69%); the AI in 60%, 96% and 99%
  (Act 2: 82% at hallway fights and 98% at elites).
- **Humans.** **1.6 held at the Act 1 door** (2,155 visits; the least certain human figure: rebuilt from picks, buys, uses and discards),
  1.9 at the Act 2 door (1,142); 3.55 potion rewards taken before the Act 1 boss against the AI's 2.5. A human run uses **2.0 potions before the Act 1 boss, 0.64 in hallway
  fights (33%) and 1.33 in elites**, and holds 1.57 at the door; the AI uses 2.3, 84% of them in hallway fights. The humans' use figures rest on
  a rebuilt count of potions held (picked and bought, less used and discarded) and are the least certain in the tables.
- **Gap.** -0.8 potions at the Act 1 door. Worth **+9 to +10 points** at the Act 1 boss (AI-fitted model +10.4, human-fitted +9.0, one of the
  largest items; potions held also mark a run going well) and +5 to +9 at the Act 2 boss. In the AI's own boss visits the kill share rises with
  potions held: 41%, 56%, 71% for 0, 1, 2 or more (humans 53%, 71%, 81%).
- **Fast test.** `tools/subproblems.py refresh` (11 seconds): potions held at the doors, potions used by fight kind, and the board replays'
  `potions_used`. For a change to the fight player's potion rule, the board (above). A pass: potions held at the door up, the Act 1 boss
  kill not down on the board. The real arm's use is not in the rows (`runs.jsonl` keeps no potion field); only the workers' game logs
  hold it and the block deletes them at its end, so the shards (emulator) are the record, and whether the real arm drinks the same way
  was not checked.
- **Slow test.** The block's floor and boss kill; the block cannot read potions (no HP or potion field in its rows), so the check that a change
  moved potions is the shards, the check that it did no harm is the block.
- **Owner lane.** An instrument first (this tool, the human pass), then the trainer for the use rule and the run planner for picking up and
  buying.
- **First thing to try.** Hold potions for elites and bosses, as the humans do (23% of their Act 1 hallway fights against the AI's 60%): do not
  spend one in a hallway fight the AI wins 99.5% of the time (test it by forbidding a drink in a hallway fight above an HP share, then read potions
  at the door and the board).
- **Not measured.** Potion use on the real arm (the shards are the emulator).

## 6. Shops and relics

- **AI now.** **4.2 relics at the Act 1 door** (856 gen 11 self-play visits; gen 9 4.2), 8.1 at the Act 2 door. In the shops before the Act 1 boss:
  1.60 visits, 1.18 cards bought, **0.11 relics bought**, 0.14 removals; 100 gold carried to the boss.
- **Humans.** **6.0 relics** at the Act 1 door (2,155), 11.5 at the Act 2 door (1,142). Before the Act 1 boss: 0.92 shop visits, 0.99 cards, **0.28
  relics bought**, 0.21 removals; 150 gold at the boss.
- **Gap.** -1.8 relics at the Act 1 door. About 1.4 of that follows the elite gap (an elite brings about 0.9 relics, piece 3) and 0.2 the shop
  buys; gold has no effect in either fitted model. Worth **+3 to +8 points** (Act 2: +4 to +9). In Act 2 the AI buys 0.34 relics a run before its boss
  (humans 0.60).
- **Fast test.** `tools/subproblems.py refresh` (11 seconds) for relics and shop buys at the doors. A pass: relics at the door up toward 6.0 with the
  Act 1 boss kill not down. No per-decision exam for shop choices exists: the corpus has the purchases but the prices on offer are needed to say
  what a choice was.
- **Slow test.** The block's floor and boss kill.
- **Owner lane.** The run planner (shop choices are run-level); an instrument for the shop exam.
- **First thing to try.** Work piece 3 first (it carries most of the relic gap), then read relics at the door again before touching shop choices.
- **Not measured.** The shop choice against the humans per decision (needs the offered prices in the human record and in the shard states).

## The slow test, once

The nightly real-game block on fresh seeds. Folder `2026-11-03`, generation 11, 2,000 seeds (1,992 ended runs, 8 crash rows): mean floor **23.41**
(SD 7.93, SE 0.18), Act 1 boss killed in 52.5% of runs (56.5% of the 1,852 that reach it), Act 2 boss in 3.2%, no wins (humans: 27.05 floors; Act 1
boss killed in 54.6% of runs, Act 2 boss in 29.1%, 11.3% won). At 2,000 runs a rate has a margin of 2.2 points either way (95%); at 500 runs about 4.5, so a 500-seed night checks a fix and
does not measure an agent. The block takes about four hours of real time (emulator arm 82 minutes, real arm 169). The funnel (PLAN item 2) puts
the cheap tests ahead of it: the ranking check on held-out decisions, a 200-seed smoke block, a paired sequential block; the 2,000-seed block
stays the final gate. A 500-seed check ran the same evening (folder `2026-11-04`): Act 1 boss killed in 59.7% of the 452 runs that reached it,
Act 2 survival 92.4% / 62.1% / 13.0% (hallway, elite, boss; 115 boss fights), all inside that night's margin of the 2,000-seed figures.

## What is not measured, and what would measure it

| Number | Why not | The instrument |
|---|---|---|
| Anything per fight on the human side beyond Acts 1 and 2 by kind (per enemy, HP lost per fight) | the pass keeps survival and potion use by act and kind only | extend `human_fight_events` in `tools/subproblems.py` (the pass takes 84 seconds) |
| The fight player against the humans on the same starts | no human fight start in the AI's form | the D38 human-run starts (PLAN item 5) |
| The real arm's HP, potions and relics at a boss | the rows hold none | the night-logging diff in the 2026-11-02 diagnostic (`fight_starts`, `boss_entries`), not applied |
| The real arm's potion use | game logs deleted at block end | copy the logs during the night (the morning-report lane already does) and read potion events |
| The human agreement ceiling for card picks | not run | the exam on one human fifth against a model of the other four |
| Map choices and shop choices against the humans | the corpus has no map and no prices | a driver field for the offered map and prices on the AI side; none on the human side, so map and shop stay outcome-tested |
| An Act 2 fight board | built for Act 1 boss only | the board file on the 306 `act2-boss` starts |

## Rerun

```
python -I tools/subproblems.py humans  --out referee/backlog/boss-entry/humans.json     # about 1.5 minutes, one process, after a night, not during
python -I tools/boss_entry_exam.py agreement --candidate <run_value.npz> --incumbent <run_value.npz> --out referee/backlog/boss-entry/agreement.json   # 8 minutes
python -I tools/subproblems.py refresh --out docs/subproblems.json --render docs/SUBPROBLEMS.md
python -I tools/subproblems.py render  --json docs/subproblems.json --doc docs/SUBPROBLEMS.md   # table only, from the committed JSON
```

`refresh` takes `referee/backlog/boss-entry/humans.json` and `agreement.json` when they exist (or `--humans` and `--agreement`) and runs `tools/morning_report.py` on the newest finished night (Windows log skipped), reads that night's rows, the newest generation's
self-play shards that played without exploration, the fight board and `starts/weights.json`, the exam rows and the boss-entry human cache,
and writes `docs/subproblems.json` (aggregates only). Anything it cannot read becomes "not measured" with what would measure it. Tests:
`tests/test_subproblems.py`.

## Sources

`docs/diagnostics/2026-11-02-boss-entry.md` (tables 1 to 16 and the ranked table), `docs/diagnostics/2026-11-01-facts.md` (the board history),
`docs/PLAN.md` section 14, `tools/morning_report.py` on `referee/LAB/nightly/2026-11-03`, the self-play shards of generation 11, `referee/gym-loop`
(`board`, `starts/weights.json`, `loop.log`, `state.json`), `referee/backlog/boss-entry` (`exam-rows.json`, `human.jsonl.gz`).
