# Training and testing the fight player: the ideas, the evidence, a ranking

Written 2026-11-04 (orchestrator), for the owner's questions of the same day: "is there a smarter way to train", "why can't we
build the best fight player on realistic decks with a realistic test averaged over draws", "what other part of the process is
worth a deep dive", and "what happened to the exact search". Three literature searches (Sonnet workers) fed it; every outside
number below is theirs and is cited; every inside number was read from files on this PC today (paths relative to
`D:/spireline/`). The learning curves it refers to are at https://claude.ai/artifact/ADKnva6WCu8ntt1uPVvx2x.

## 0. The short answer

The test the owner describes can be built, and most of its parts exist. What stands between us and the best fight player is
not a missing idea; it is three measured facts:

1. **The teacher's depth sets the student's ceiling.** The sixteen-times search kills the Act 1 boss in 46.3 of 100 paired
   replays against 36.8 for the shallow search (M2, 1,999 pairs). The student, version 2, scores 47.05 on the same board. It has
   caught its teacher, matches the teacher's first choice 75.5 times in 100, and that curve gained 0.4 points over the last ten
   checkpoints. More hours with this teacher buy less each day.
2. **The practice rarely contains the fights we lose.** Practice starts come only from the AI's own nightly runs (250 a night,
   nine nights). Act 2 boss starts are 7.6 in 100 of practice because the AI reaches that boss in 24 of 100 runs; it wins that
   fight 13 times in 100 against the humans' 76. The human corpus's four training fifths (about 11,800 runs with the deck, relics,
   HP and enemy at every floor) were approved as practice starts on 2026-10-30 (D38) and have not been built.
3. **The ruler is short.** The promotion gate's board is 200 Act 1 boss starts from the 2026-10-29 headroom test, ten draws each.
   53 of the starts are always won and 61 never won, so 86 starts carry the signal; a one-point difference needs about 39,000
   independent games unpaired, and ten replays of one start are not independent. Candidates have gained about a point in four
   days and the bar is 1.3 points, so the gate cannot see the progress that is probably there.

Ranked by what they would buy here (details in section 3):

| # | Item | What it buys here (estimate) | Cost |
|---|---|---|---|
| 1 | **The fight exam**: starts from human runs and recent nights, stratified by act, kind and boss; paired draw orders; value-baseline scoring (AIVAT); a held-out half; per-boss readings | The gate's noise from about ±1.6 points to roughly ±0.5 at the same games; a ruler the loop cannot overfit; the six-piece board read per fight kind every gate | 1.5 units, about 10 machine-hours |
| 2 | **Practise what we lose**: human Act 2 and boss starts; starts weighted by regret (value loss), not by frequency; archived pre-loss states as starts | The Act 2 boss (13 against 76) finally in the practice at scale; prioritized replay gave +28 to +76 in 100 on Procgen | 1.5 units |
| 3 | **A deeper teacher at training time only**, paid for by cheap games: playout-cap randomization, Gumbel root selection, the judge's value at the leaves on the GPU, reanalysis of stored positions on the idle GPU | The M2 jump (+9.5 points from 16×) says depth pays; ten times the training search bought fifteen times the play-time search in Hex; the GPU sits idle between gates | 1 unit design + 1 unit build |
| 4 | **Trainer data efficiency**: auxiliary targets (HP lost, turns, enemy HP left), the search's root value as the value target, periodic last-layer resets with a higher replay ratio | KataGo: auxiliary targets 1.65×, playout caps 1.37×; resets pay only above replay ratio 4 (ours is about 4) | 1 unit |
| 5 | **The nightly exam's power**: the copy arm as a control variate (seed correlation about 0.5, so 25 in 100 fewer real runs for the same precision), a value baseline on run outcomes, a composite metric | A 500-run night that can see a half-floor change instead of one floor | 0.5 unit |

The run layer has its own list in section 6; its first item (hindsight labels for human run decisions, replayed on the copy) is
the one idea here that is new to this project rather than borrowed.

## 1. Where we are (read today)

- **The fight player.** A student network (`rl/combat_net.py`) imitates a searching teacher: single-observer information-set
  MCTS, each simulation re-shuffling the draw pile (determinization, `rl/combat_mcts.py` lines 9 to 14), leaves valued by rollout
  or by the judge network, about 30 simulations a decision for play (`a3-v1`) and sixteen times that for the teacher. The exact
  solver (D35, S3 expectimax) sits inside: it settles the decisions whose remaining tree is small and its move overrides the
  teacher's where the teacher's was worse (`rl/gym_loop_train.py` lines 12 to 14). In the newest buffer shard 4.9 in 100
  decisions carry an exact value.
- **The teacher's headroom.** M2 (DECISIONS line 925): the sixteen-times search 46.3 against 36.8 on 1,999 paired Act 1 boss
  replays. The judge-leaf search at 30 simulations scores 44.1 on the board; the shallow rollout search 36.9; version 1 45.7;
  version 2 47.05.
- **The gate** (`PROMOTION_RULE`, `rl/gym_loop.py` lines 108 to 124): 200 starts, stage 1 on a rotating pair of draw indices
  (400 games, +1.0 point to go on), stage 2 on all ten (2,000 games, one-sided McNemar p under 0.05 and mean L0 not worse). 111
  checkpoints gated in 4.4 days, two promotions on the first day, eight rematches since, all short; the best (c0109) +1.1 points at
  p 0.052. Stage-1 candidates went from 1 to 3 points behind the champion to level.
- **The trainer** (`rl/gym_loop_train.py`): the newest 300,000 rows, at most four passes per row, AdamW, a checkpoint every 30
  minutes; 1.45 million samples over 144 checkpoints; held-out top-1 agreement with the teacher 0.607 to 0.755; value error 4.58
  to 1.70.
- **The practice mix** (`gym-loop/starts/weights.json`): Act 1 boss 34, Act 1 hallway 26, Act 1 elite 10, Act 2 hallway 15,
  Act 2 boss 7.6, Act 2 elite 7.3 (in 100); sources: the nights' AI runs only, 250 a night (`starts/meta.json`); no human
  starts.
- **Compute.** Fights are CPU-bound at about 50 a minute (400 games in 8 minutes); the GPU is about 30 in 100 busy during a gate
  and idle between gates.
- **The nightly exam.** 500 runs give a standard error of 0.36 floors (2,000: 0.18). The copy arm's floors correlate with the
  real arm's on the same seed at about 0.5 (paired SD 8.03 against 8.04 and 8.27), although the copy agrees on 99.75 in 100
  decisions: one early divergence changes the whole run.
- **The gaps** (`docs/SUBPROBLEMS.md`, 2026-11-03): first boss once there 56.5 against 74.8; Act 2 hallway 92 against 97,
  elite 66 against 89, boss 13 against 76; elites fought before the Act 1 boss 0.46 against 1.95; potions held at the boss door
  0.8 against 1.6; relics 4.2 against 6.0; card-reward agreement with the human 33 in 100 (a coin: 25).

## 2. The owner's questions

**"Why can't we build the best fight player, on realistic decks, with a realistic composite test averaged over draws?"**
We can; the loop is five days old and its ruler was fixed before its first checkpoint on purpose (so that nothing tuned on the
gate's own games). What is missing is listed in section 0. Two cautions from outside. A hobby project that distilled a fight
search into a network failed six times because its teacher saw the future draw order (imitation accuracy stuck at 0.44, cloned
play at floor 12 against the teacher's 23); our teacher does not see the draws, which is why our student does copy it. And
averaging the test over draws removes only half the noise: the other half is which fights are in the set. With 86 informative
starts, more starts beat more replays; a never-won start measures nothing however often it is replayed.

**"If the agent dies, let it go back and make different decisions."** This is Go-Explore's archive (restore a saved state, explore
from there; Nature 2021), Go-Exploit (AlphaZero self-play started from archived states: 0.59 to 0.67 head-to-head against plain
AlphaZero at the same checkpoint on Connect Four and 9×9 Go), and the reverse curriculum from demonstration states (Salimans and
Chen 2018, Backplay). The copy saves and restores any state, so all three apply. The fight gym already does the fight-level
version on 200 boss starts; it does not yet start from the states just before the AI's own losses, and it does not start from
human states at all. For run-level choices nobody here or in the literature has done it in this game; section 6 says how.

**"Replay fights several times and average."** Two places. In the test, yes (section 4): paired draw orders are already used, and
the value baseline (AIVAT: standard deviation down 85 in 100 in a poker match, 44 times fewer games) is the stronger form of the
same idea. In the teacher, it is already done inside the search (every simulation is a fresh shuffle), and one outside attempt to
average four sampled futures on top of the search did not help (Singer 2026). In the value target, the search's root value is
already an average over shuffles; if the trainer's value target is the single played outcome, switching to a mix of root value
and outcome is item 4.

## 3. The ideas, ranked

Each: what it is; the evidence; what it buys here; cost and risk; verdict. "Unit" is one Sonnet worker's typical item (about
0.5 of the weekly allowance).

### 3.1 The fight exam (testing) — do now

A fixed, held-out, stratified set of fight starts with paired draws and baseline-corrected scores; the gate's ruler and the
six-piece board's instrument. Design in section 4.
- Evidence: Fishtest's paired openings (21 in 100 fewer games for the same decision); AIVAT (value-function control variates,
  standard deviation down 85 in 100 in heads-up poker, 69 in Leduc with one known strategy); the one-point arithmetic (39,000
  unpaired games, 39,000 × (1 − ρ) paired); SpireBench's finding that fight-quality measures (damage taken per hallway fight,
  damage per energy, wasted block) separate strong agents from weak ones (rank correlation −0.87) while agreement with human card
  picks barely does (0.16); the reusable-holdout result (Dwork 2015) that a test set answered too often is overfitted.
- Buys here: gate noise from about ±1.6 points (2,000 games, ρ near 0.8) to roughly ±0.5 at the same games if the judge explains
  half the draw luck (the poker figure is the upper bound); the loop's progress becomes visible; per-boss and per-kind readings
  at every gate, so the board's "which boss" question answers itself.
- Cost: 1.5 units, about 10 machine-hours to play the champion on the new set. Risk: the baseline needs a decent value estimate;
  ours is the judge, whose board score (44.1 at 30 simulations) says it is one.
- Verdict: first. It also unblocks items 2 and 3, which need a ruler that can see one point.

### 3.2 Practise what we lose (training) — do now

Human Act 2 and boss starts (D38's four fifths, rebuilt on the copy: deck, relics, HP, enemy, fresh draws); starts weighted by
regret (the gap between the teacher's root value and the played outcome, or the student's value loss), not by how often the AI
meets them; the states a few decisions before the AI's own losses added as starts.
- Evidence: prioritized level replay (+28 in 100 test return on Procgen easy, +35 hard, +76 with augmentation; scoring by value
  loss alone or staleness alone did worse than uniform, so both terms are needed); Go-Exploit above; Procgen's 200-level finding
  (a set that small is memorized; the practice needs thousands of distinct starts).
- Buys here: the Act 2 boss and elites at scale (today 15 in 100 of practice, almost all from the AI's thin Act 2 decks);
  a practice distribution that follows the gap instead of the AI's own path.
- Cost: 1.5 units (the human-start builder is specified in D38; the weighting is a sampler change). Risk: human decks the AI
  would never build; mitigated by the exam's human-start stratum, which measures exactly that.
- Verdict: second, in parallel with 3.1 (disjoint files: the exam is tooling, this is the gym's start sampler).

### 3.3 A deeper teacher at training time, paid for by cheap games — design first

Four pieces, all from the AlphaZero efficiency literature: (a) playout-cap randomization: most fights played cheap (×4) for value
data, a quarter at ×64 for policy targets (KataGo: 1.37× for the cap trick alone); (b) Gumbel root selection with sequential
halving, so that few simulations still give a policy improvement (Gumbel MuZero learns 9×9 Go at 2 simulations where MuZero fails
below 16; 11× faster at 16); (c) the judge's value at the leaves, batched on the GPU, instead of CPU rollouts (the judge-leaf
search already beats the rollout search 44.1 to 36.9 on the board at equal simulations); (d) reanalysis: re-run the teacher on
stored positions with the newest network on the idle GPU (MuZero Reanalyse; EfficientZero reanalyses 99 in 100 policy targets).
- Evidence: above, plus Jones 2021 (each 10× of training compute removes about 15× of play-time compute, 9×9 Hex).
- Buys here: a teacher above the student's ceiling without more CPU; the trainer fed from the GPU's idle hours.
- Cost: 1 unit of design (Opus: which of the four first, with the loop's measured seconds per fight), 1 unit build. Risk: the
  determinized search's leaf values are noisy; Gumbel's completed-Q target assumes the value is trustworthy.
- Verdict: third; design after 3.1 lands so the gain can be read.

### 3.4 Trainer data efficiency — measure first

Auxiliary heads (HP lost in the fight, turns to the end, enemy HP left, potion used), the search's root value mixed into the
value target, periodic resets of the last layers with a higher replay ratio.
- Evidence: KataGo's ownership and score targets 1.65×, auxiliary policy target 1.30×; primacy-bias resets (Atari 100k 0.38 to
  0.48; the gain grows with replay ratio and is negative at ratio 1); BBF (replay ratio 8 with resets every 40k steps).
- Buys here: more strength per fight generated, which is the bottleneck. Our replay ratio is about 4 (four passes per row), the
  edge of where resets help.
- Cost: 1 unit. Risk: resets cost a few checkpoints each; the aux heads need the fight exporter to carry the targets.
- Verdict: fourth; the aux heads first, resets only with the replay ratio raised.

### 3.5 The nightly exam's power — do when the lab is quiet

The copy arm's floors as a control variate for the real arm's (correlation 0.5 gives 25 in 100 fewer runs for the same
precision; CUPED at Bing about 50 in 100 with a better covariate; Sim2Val up to 83 in 100 with a well-correlated simulator); a
value baseline on run outcomes (the run head's value at each floor, AIVAT-style); a composite metric with less variance than
floors (floor, HP at the boss doors, boss kills).
- Buys here: a 500-run night that can see half a floor. Cost: 0.5 unit in `tools/morning_report.py`. Risk: none to the game.
- Verdict: fifth; cheap, do it in the housekeeping lane.

### 3.6 Ideas considered and set aside

- **Imitating human card picks.** SpireBench: pick agreement barely tracks strength; Singer: the model most faithful to human
  picks (55.8 in 100) played worst over 50 seeds. Use the human picks as a feature and a sanity check (the ranking check does
  this), not as the target.
- **Return-conditioned policies on the human runs** (Decision Transformer, RvS). ESPER: return conditioning fails when outcomes
  depend on luck (Connect Four 0.80 against 0.99); Kumar 2022: filtering to the best runs scales worse than plain cloning. This
  game is luck-heavy. The hindsight-label idea in section 6 avoids it by replaying the state, not trusting the outcome.
- **Seed knowledge.** The copy knows the shuffle; a search that uses it plays a different game. The one simulator with a public
  bot (sts_lightspeed) assumes the RNG is known; its search without it is unimplemented. Not for us.
- **Stochastic MuZero's learned chance model.** We have the exact chance model (the copy). Afterstate values are still worth
  having inside the net (item 3.3's design question).
- **Language-model players.** D7. For calibration only: Epoch's October 2026 harness had its best model winning 40 in 100
  Ironclad runs at Ascension 10 in 15 single attempts (wide intervals), with expert humans near 95. The target is reachable and
  the gap is judgment, not reflexes.

## 4. The fight exam: design

- **Starts.** About 2,000: half from human runs (D38's four fifths; deck, relics, potions, HP and enemy at the fight, rebuilt on the
  copy), half from the last three real nights. Stratified by act (1, 2; 3 once the copy's Act 3 is verified) and kind (hallway,
  elite, boss), and within bosses by boss identity, so every cell has at least 100 starts. The board's 200 current starts and
  every run behind them stay out of training as today.
- **Draws.** Four paired draw orders per start (common random numbers: the same shuffles for champion and candidate). Four, not
  ten: once a start's outcome correlation across candidates is high, more starts beat more replays.
- **Scores.** Per game: win; HP lost; potions spent; turns. Per start: the mean over draws minus the judge's value of the start
  (the baseline), so a lucky draw set does not count as skill. The gate's statistic stays the paired McNemar on wins plus the L0
  rule, now on the baseline-corrected means with a bootstrap interval.
- **Held-out.** Two halves. The gate reads only half A; half B is read once a week by the orchestrator (the reusable-holdout
  rule). Rotate a quarter of half A every two weeks from the newest nights.
- **Calibration pass.** The champion plays the whole set once; starts always won or never won under both the champion and the
  sixteen-times teacher are kept but weighted zero in the gate (reported, not scored).
- **Readings.** Win rate per cell (the six-piece board's fight rows at every gate), the three SpireBench fight-quality measures
  (damage taken per hallway fight, damage per energy, wasted block), the per-boss table.
- **Cost.** The champion's 8,000 games once (about 2.7 machine-hours at 50 a minute); a stage-1 gate on 800 games; stage 2 on the
  4,000 of half A.

## 5. The practice: design

- Starts: the exam's source distribution (human four fifths plus nights), minus every exam start and its run, tens of thousands.
- Weights: a regret score per start (teacher root value minus played outcome, averaged over its last plays) times a staleness
  term, as in prioritized level replay; the AI's own pre-loss states (the position three decisions before a lost fight) enter the
  archive with the same score.
- Report: the mix per act and kind, and the regret distribution, in the loop's segment log.

## 6. Other parts worth a deep dive (ranked)

1. **Act 2, as a whole.** The widest gap (boss 13 against 76) and the thinnest practice. Beyond items 2 and 3.1: the route
   (0.46 elites before the first boss against 1.95; the humans' relics 6.0 against 4.2 come from those fights) is the run
   layer's piece; and the copy's fidelity in Act 2 and 3 is "barely verified" (D38 text). A deep dive would read the Act 2
   divergences in the nightly rows before anything trains there.
2. **The run layer's teacher: hindsight labels from human runs replayed on the copy.** For each human decision in the four
   fifths (card reward, rest, route, shop), rebuild the state on the copy, play each option forward with the fight player under
   fresh draws, and label the decision with the measured value of each option. The owner's "go back and choose differently",
   applied to 11,800 realistic runs instead of the AI's own. It sidesteps the luck problem that breaks return conditioning
   (ESPER) because it replays the state rather than trusting the logged outcome. Cost: the copy plays the rest of the run per
   option, about 3 copy-seconds a floor; a sample of 20,000 decisions is a machine-day. This is the one genuinely new idea in
   the memo and it needs an Opus design first (what "value of an option" means: floors, or the run head's own value).
3. **The nightly exam's metric and power** (item 3.5), plus the question the morning report cannot yet answer: survival by
   fight kind in the real arm, which needs the game-log copy.
4. **Compute allocation.** Fights are CPU-bound and the GPU idles between gates: the judge at the leaves, the prior server, and
   reanalysis all move work to the GPU. A measured plan (seconds per fight by config, GPU occupancy) before item 3.3's design.
5. **The potion and relic pieces** (board items 5 and 6). The fight player values HP at the fight's end, not the potion at the
   boss; the fix is the run head's value of the post-fight state as the fight's terminal value (`rl/ARCHITECTURE.md`, "one
   currency"), which is PLAN section 14's potion item. It is a design, not a training change.

## 7. What happened to the exact search

The fight solver (D35, 2026-10-26) landed as S3 on fork main `6cd01889` on 2026-10-27: exact expectimax over the copy's fight
rules with a transposition table, lossless prunings, a reference solver and the equal-value harness, exports with the
native-library fix. The shape review of 2026-10-29 (`docs/reviews/solver-shape-review-2026-10-29.md`) decided it should be one
part of the fight gym rather than a race for exact coverage: exact last-turn values, a lethal and forced-survival check at the
root, the one-turn enumerator. That is where it is today: inside the loop's teacher, it settles the decisions whose remaining
tree is small (4.9 in 100 of the newest shard's decisions; 16 in 100 within ten seconds in the measurement), and where it
finishes with a better move than the search's, the trainer learns the solver's move (`solver_override`). Its two measurement
rounds, M1 (oracle regret on the decisions it settles) and M2 (the headroom test), ran; M2's result, +9.5 points for the
sixteen-times search, is the number that set the fight gym's priority. The pruning rounds that would extend its reach (bounds,
dominance) were parked by the same review. Nothing about it is lost; it is a component, measured, and working at the share the
budget allows.

## 8. What I would start this week

Items 3.1 and 3.2 now, in parallel, on disjoint files (exam tooling under `tools/`; the gym's start sampler under `rl/`), 3 units
in all against a week at 6 in 100 used with a ceiling of 65; then the Opus design for 3.3 and for the run layer's hindsight
labels (section 6.2) once the exam can read a point. Item 3.5 in the housekeeping lane at the next quiet window.

## Sources

Outside (from the three searches, 2026-11-04): KataGo (Wu 2019, arXiv 1902.10565; methods notes); Gumbel MuZero (Danihelka
2022); MuZero Unplugged / Reanalyse (Schrittwieser 2021, 2104.06294); EfficientZero (Ye 2021, 2111.00210); primacy bias
(Nikishin 2022, 2205.07802); SR-SPR (D'Oro 2023); BBF (Schwarzer 2023, 2305.19452); train-time against play-time compute (Jones
2021, 2104.03113); Expert Iteration (Anthony 2017, 1705.08439); Stochastic MuZero (Antonoglou 2022); sampled chance nodes
(Lanctot 2013, 1304.6057); determinization and IS-MCTS (Long 2010; Cowling 2012); AIVAT (Burch 2018, 1612.06915); common random
numbers (Sharma 2025, 2512.24145); CUPED (Deng 2013); multifidelity Monte Carlo (Peherstorfer 2016); Sim2Val (2506.20553);
Fishtest pentanomial; reusable holdout (Dwork 2015, 1506.02629); Procgen (Cobbe 2019, 1912.01588); PLR (Jiang 2021,
2010.03934); ACCEL (2203.01302); Go-Explore (Ecoffet 2021, 2004.12919); Go-Exploit (Trudeau and Bowling 2023, 2302.12359);
single demonstration (Salimans and Chen 2018, 1812.03381); Backplay (Resnick 2018, 1807.06919); Decision Transformer
(2106.01345); RvS (2112.10751); ESPER (Paster 2022, 2205.15967); Kumar 2022 (2204.05618); SpireBench (2610.12596); Epoch
SpireClimb (October 2026); AgenticSTS (2607.02255); sts-rl-agent (Hugging Face, Jialeiv); Doron Singer's Silent series
(dev.to, 2026); sts_lightspeed; bottled_ai; AscensionAI (2026); Hearthstone MCTS with a value network (Swiechowski 2018,
1808.04794); Magic ensemble determinization (Cowling, Ward and Powley 2012).

Inside: `docs/DECISIONS.md` D35, D38, D43, D49 and the M2 addendum; `docs/SUBPROBLEMS.md`; `fork/sts2/rl/gym_loop.py`,
`gym_loop_train.py`, `combat_mcts.py`, `search_configs.py`, `ARCHITECTURE.md`; `referee/gym-loop/state.json`, `loop.log`,
`trainer/checkpoints.jsonl`, `starts/weights.json`, `starts/meta.json`, `buffer/shards`; the nine nights under
`referee/LAB/nightly` read with `tools/morning_report.py`.
