# The strategy, rethought: a teacher for each half of the player (2026-11-05)

Opus design worker on D55, written from 08:24Z (`date -u`). Sources are named where used; nothing was played. Three
single-process scripts read the human corpus and three nights, aggregates only, and stay in
`referee/backlog/scratch-strategy/` (`count_corpus.py` writing `counts.json`, `shop_check.py`, `night_by_act.py`). Every
figure is measured (file named), arithmetic on measured figures, or marked *estimate* or *unverified*. Human data: the Spire
Codex public run export for v0.107.1 (spire-codex.com), aggregates only, no cell under 20 runs (D13, D38, D55).

## For the owner

**What is wrong.** The player has stopped getting better. Each new version this past week added about one floor, the last
two were worse, and in about 76,000 games it has never won. It beats the first boss about as often as human players at
this level, but the second boss in 5 runs of 100, where humans do in 29. Both halves learn from teachers no better than
themselves: the fighting half has caught up with the slow search it copies, like a pupil who knows all their tutor knows,
and the deck-building half learns only from its own games, which rarely pass the second boss.

**What changes.** The deck-building half first learns from 12,000 recorded human runs (1,364 of them wins), then improves by
playing. The fighting half thinks longer in boss fights and practises the second act. Progress is judged by second-boss wins.

**In two weeks** we expect the second boss beaten in 8 to 12 runs of 100, and card picks matching a human's about half the
time, not a third. A 2,000-game head-to-head and the nightly real-game runs will tell. If the deck changes bring nothing,
the effort moves to the fighting.

## 1. Where the player stands

### 1.1 The ledger (`referee/agent/promotions.tsv`; each line a paired block of fresh seeds)

| generation, date | what changed | paired floors, candidate minus base |
|---|---|---|
| 1, 2, 3 (10-23, 10-24) | fight prior from self-play | +0.41, +0.31, +0.29 |
| 4 | | refused twice |
| 5 (10-25) | the run judgement (`V_run`) chooses cards, paths, rests, shops | **+5.00** |
| 6, 7, 8, 9 (10-26 to 10-29) | fight prior and run judgement refit together | +1.72, +0.75, +2.04, +1.04 |
| 10 | | refused twice |
| 11 (11-02) | the gym's fight player v2; generation 9's run judgement kept | +1.07 |
| 12 (11-02, 11-05) | run judgement refit on generation 11's own runs | refused twice: -5.91 (2,000 seeds), -1.29 (200-seed smoke) |

Generation 11 on its block (`agent/gen11/candidate/promotion.json`): mean floor 23.13 (95% 22.77 to 23.48); the Act 1 boss
reached in 90 of 100 runs and beaten in 57 of 100 of those; 14 in 100 card rewards skipped. **No block has held a win:** 16
blocks of 2,000 seeds and one of 200 (64,400 runs, both arms), plus 11,540 real-game runs over ten nights.

**Both learners have stalled.** The gym's player v2 (checkpoint c0019) was promoted 10-31 14:30Z; about 145 checkpoints have
come since (to c0164, gated 08:19Z today) and none was promoted (`gym-loop/loop.log`). On the 200-start Act 1 boss board v2
wins 47.05 in 100 and its teacher, the sixteen-times search, 46.3: it has caught its teacher. The run judgement in play is
generation 9's (sha256 `f0a199fb…`, fitted 10-29). Every floor since generation 9 came from the fight player.

### 1.2 Stage by stage against the humans

AI: generation 11, real game, night of 11-05, 499 runs (`backlog/mr-2026-11-05/`). Humans: the four training fifths, 11,961
finished vanilla runs (`counts.json`; the exam fifth agrees within 1.5 points on every rate). Door figures: `docs/SUBPROBLEMS.md`.

| stage | AI | humans |
|---|---|---|
| reach the Act 1 boss, of runs | 90 in 100 | 74 |
| beat it, of those who reach it | 56 | 74 |
| reach the Act 2 boss, of those who beat Act 1 | 52 | 70 |
| beat it, of those who reach it | **19** | **76** |
| win, of those who beat the Act 2 boss | 0 of 25; Act 3 bosses 3 of 20 over nine nights | 40 |
| Act 2 boss beaten, of all runs | **5.0** | **28.9** |
| fights survived, Act 1 hallway / elite / boss | 99.4 / 90.7 / 56.7 | 98.7 / 89.1 / 73.8 |
| fights survived, Act 2 hallway / elite / boss | 93.9 / 66.5 / 18.9 | 97.2 / 88.4 / 75.7 |
| at the Act 1 boss door: potions / relics / elites fought / HP share | 0.8 / 4.2 / 0.46 / 78% | 1.6 / 6.0 / 1.95 / 67% |
| mean floor; wins | 23.35; 0 | 27.05 (exam fifth); 11.4 in 100 |

## 2. Why it stopped: the causes, ranked by their share of the gap

### 2.1 Where the gap is

Through Act 2 the gap is a factor of 5.8 (28.9 against 5.0). On a log scale (arithmetic on 1.2):

| stage | AI | humans | share of the gap |
|---|---|---|---|
| reach the Act 1 boss | 0.904 | 0.739 | -11% (the AI is better) |
| beat the Act 1 boss | 0.565 | 0.738 | 15% |
| reach the Act 2 boss after Act 1 | 0.523 | 0.698 | 16% |
| beat the Act 2 boss | 0.188 | 0.757 | **80%** |

Act 3 adds an unmeasured gap on top (humans win 40 in 100 runs that clear Act 2). The 11-02 boss-entry fits put 27 to 44
points of the Act 2 boss gap on play and 22 to 39 on the hand brought to it (HP, potions, relics, deck), and 17 to 23 of the
Act 1 boss gap on play against 0 to 5 on the hand (`SUBPROBLEMS.md` pieces 1, 2; associations in fitted models, not tests).

### 2.2 The causes

1. **The fight player loses the big fights and its teacher can teach it no more** (largest: about half the Act 2 boss gap,
   most of the Act 1 boss gap). v2 has caught the search it imitates. Practice gives the Act 2 boss 10 of 134 starts a
   segment against about 40 for the Act 1 boss (`loop.log`, segment 168). At test time it thinks 30 simulations a move in
   every fight, bosses included (`a3-v1`, `rl/search_configs.py`); the sixteen-times search without a learned prior beat the
   Act 1 boss 46.3 against 36.8 times in 100 (M2 in D37, 1,999 pairs); with v2's prior the gain is **unmeasured**. The deeper
   teacher (`docs/design/2026-11-04-training-design.md` §1, "the training design" below) has not been run. Nor has the direct test of play against deck, our player on the humans' own boss
   starts, though they exist (8,216 Act 1 and 3,948 Act 2, `docs/rl/HUMAN_STARTS.md`).
2. **The deck-building half has no teacher past the first boss** (the hand's share: card picks worth 2 to 10 points at the Act
   2 boss, relics 4 to 9, potions 5 to 9, by the fits). Its own runs cannot teach Act 2 choices: under generation 11's player
   96.5 of 100 Act 2 continuations die before the act ends, so Act 2 options look alike (`2026-11-05-hindsight-sizing.md` §4,
   "the sizing memo" below). It takes the human's
   card in 31 of 100 rewards (a coin over three cards and skip: 25), skips 7 in 100 in Act 2 against the humans' 32, takes
   Battle Trance 7 times in 100 against 61 and Anger 71 against 15 (`SUBPROBLEMS.md` piece 4). Both refits from self-play lost.
3. **It spends what humans keep.** The fight's currency counts a potion as 10 HP and a death as -100 (training design §0
   item 3), so the player drinks in 60 of 100 Act 1 hallway fights it wins holding one (humans 23) and reaches the boss with
   half their potions; its boss kill is 41, 56 and 71 in 100 holding 0, 1, and 2 or more. It fights a quarter of their elites
   and brings 1.8 fewer relics. A hold rule is cheap to test; the one-currency fix is designed, not built.
4. **The scoreboard rewards Act 1.** A run that beats the Act 2 boss goes about 8 floors further (1,331 Act 3 floors over 169
   runs, `docs/diagnostics/2026-11-04-act2-act3-fidelity.md`). Doubling Act 2 boss kills from 5 to 10 in 100 moves the mean
   floor about 0.4 (arithmetic), the paired gate's resolution at 2,000 seeds (generation 11's lower bound sat 0.40 under its
   mean). The measure is blind where 80% of the gap is.
5. **Cadence.** A run-judgement candidate waits for about 8,000 fresh runs of its own fighter (three days for generation 12
   attempt 2), then a fit, a smoke block and up to 30 core-hours of block: one candidate in two to three days. Pretraining on
   human runs needs no new games.
6. **The copy's remaining errors: not binding, watched closer.** Night of 11-05 (`night_by_act.py`, the fidelity diagnostic's
   method): state disagreements 0.66 per 1,000 decisions in Act 1, **4.4 in Act 2** (6.5 and 6.6 the two nights before),
   10.7 in Act 3 (25 runs); **24 in 100 runs entering Act 2 meet one there** (34 before). Whole runs agree within noise: copy
   24.32 floors against the game's 23.53 on the same 200 seeds (gap +0.8, 95% -0.4 to +2.0); Act 2 boss fights won 23 in 100
   on the copy (56) against 19 in the game (132). The judgement will learn from Act 2 on the copy, so this is checked nightly.
7. **The value fit's instability** is a symptom of 2 and of D33's keep test, which checks the Act 1 forecast, not the choices:
   attempt 1 passed it, rested 2.1 times against 3.1 before the boss and lost 5.9 floors; attempt 2 cut skips from 17 to 7 in
   100 and lost 1.3. Deeper targets and a test of choices cure it; another knob (beta) does not.

The gate's statistics are sound; what it measures (4) and how often it can be fed (5) are the problem.

### 2.3 The orchestrator's two causes

- **(a) "An 18-class Act-1 head": rejected as stated.** The judgement in play has 53 floor classes fitted on whole-run final
  floors, and has since generation 5 (`value/floor_head` is 53 x 256 in the `run_value.npz` of generations 5, 9, 11, 12-a2;
  `run_train/train.py` targets the final floor). Act-1 only are the keep test (`run_train/keep.py`, floors 1 to 16), DESIGN
  §5.1's rule and, decisively, the data: its own runs say almost nothing past floor 17. Lifting F3 changes the paperwork; a
  teacher past floor 17 changes the judgement.
- **(b) "It learns from scratch while human runs sit unused": confirmed, with a ceiling.** Human runs are the only teacher for
  the deck half past the first boss and cost no games. They can close at most the hand's share (cause 2, part of 3); they do
  not fix the fights, and the record holds no route or event choices as decisions (3.1).

## 3. The new recipe

D6 (no end-to-end RL) and D7 (no LLM) stand: this is imitation and expert iteration around search and learned judgements.

### 3.1 What a human record can teach (`counts.json`, `shop_check.py`)

Ironclad, Ascension 10, solo, standard, no modifiers: 14,974 finished runs, 6,222 abandoned (left out; D38's 14,811 used a
slightly different filter, not traced). Vanilla runs by fifth (exam = the ids file united with the D38 hash bucket, the rule
`rl/human_starts.py` applies): training 2,999 / 2,994 / 3,065 / 2,903 runs with 343 / 348 / 349 / 324 wins; exam 2,959 runs,
345 wins. Of the 11,961 training runs 8,842 reach the Act 1 boss, 4,559 the Act 2 boss, 3,452 Act 3. One build (v0.107.1);
no player identity, so skill shows only in outcomes.

| decision | what the record holds | training count | a prior now? |
|---|---|---|---|
| card reward | the offers (three in 93 of 100 screens), the one taken; skip = none | 151,499 (Act 1 90,204; Act 2 41,974; Act 3 19,321); skip 15 / 32 / 47 in 100 | **yes**; 6 in 100 points list more than three offers (merged screens: split or drop) |
| ancient (act start) | 3 options, the one chosen | 21,886 | **yes**, once titles map to options for 9 in 10 |
| rest site | the choice (smith 31,931, heal 23,922, other 1,511); the smith's target | 55,796 | **yes**; options from relics |
| shop | offers (about 6 cards, 3 relics, 3 potions); relic and potion buys flagged, card buys via cards gained; removals; gold spent | 19,383 visits | **partly**: prices not recorded (rebuild from the copy's rules, check against gold spent) |
| potion reward | offers, the one taken | about 78,000 | later |
| event | the chosen option's title only | 66,577 visits | **no** |
| route | each floor's room type; no map | none | **no** |

Of D55's five macro priors, card reward and rest (with ancients) are learnable now, shop partly, route and event not as
per-decision priors. The human route (1.95 elites before the Act 1 boss) stays a reported target: in the AI's runs 0, 1 and
2 elites give the same boss kill (52, 51, 51 in 100), so elites pay only once the fights are won.

### 3.2 (a) The human prior for the deck half

- **Model.** `π_h` is an afterstate scorer on the run judgement's trunk: the 1,851-wide input (deck, relics, potions, HP, gold,
  act, floor, map-ahead block, FightNet's fight block H), `RunValueNet`'s embeddings, one logit. Each human decision's offered
  options become afterstates through `apply_option` on the state rebuilt from the record (the rebuild `tools/boss_entry_exam.py`
  does for the exam); the loss is a softmax over those options against the human's choice. Same inputs, same afterstates, so it
  drops into the existing chooser. Smith targets are a second softmax over upgradable cards; a shop is one buy-or-leave per offer.
- **The missing map.** Each decision gets a donor map (the AI's own state on the same floor and region, as the exam does),
  redrawn every epoch; at play the true map. Routes are not imitated.
- **Split.** Fifths 1 to 3 train; **fifth 4 is the validation set** for early stopping, weights, λ and every other choice; no
  builder reads the exam fifth (`assert_no_exam`); `boss_entry_exam.py agreement`, extended to ancients, smith targets and
  shops, scores it once per frozen candidate. A variant weighting winners' decisions 2x is kept if validation favours it.
- **Size.** About 240,000 decisions and 270,000 parameters: minutes on the card (*estimate*).
- **Bar.** Validation top-1 agreement of 45 in 100 on card rewards (coin 25, today 31). Under 40 means the rebuild or the
  features are wrong, and nothing goes to a block.

### 3.3 How the prior enters the choice

The chooser takes `argmax_o [ V(o) + λ · log π_h(o) ]`, `V` in expected final floors. λ = ∞ is pure imitation, λ = 0 today's
chooser; the judgement overrules the prior only when its advantage beats λ times the log-odds gap (at λ = 0.5: 0.55 floors
against a 3-to-1 preference, 1.15 against 10-to-1). λ in {0, 0.25, 0.5, 1, ∞} is chosen on the hindsight labels (each λ's picks
against generation 11's, paired, held-out) and on fifth 4; the best one or two go to the smoke block. Guard: an option the prior
gives under 2 in 100 is taken only if the judgement prefers it by more than a floor (attempt 1's "never rest"). Map choices use
λ = 0; fights are unchanged.

### 3.4 (b) The whole-run judgement and its keep test

- **Heads and targets.** Keep the 53-class final-floor head (expected floors, W = 53 for a win) and add three binary heads:
  clears Act 1, clears Act 2, wins. Pure Monte Carlo targets from the run's end (beta 0; the 11-02 recipe diagnosis showed the
  bootstrap inherits the playing head's lag).
- **Rows and a source input.** Self-play afterstates from whole runs on the copy plus the human chosen-option afterstates of
  fifths 1 to 3; two inputs say human or self, "self" at play. Human rows teach which decks, relics and HP carry a run
  through Acts 2 and 3 (3,452 training runs reach Act 3; the self-play window holds a few hundred, *estimate*); the source input
  absorbs the level difference (76 against 19 in 100 at the Act 2 boss). H stays an input and is FightNet on our player's
  fights, so an elite's danger is read for our player.
- **Weights.** Human rows at 0.25, 1 or 4 times self rows, three seeds each, chosen on held-out self-play runs (5 folds by seed
  hash: log-loss of the two clears heads) and the labels' ranking leg; the kept fit averages its three seeds.
- **Keep test (replaces D33's Act 1 rule).** Kept when (1) out of fold on self-play runs the Brier skill against the base rate
  has its 95% interval above zero for clears Act 1 (rows on floors 1 to 16) **and** clears Act 2 (floors 18 to 32); (2) the
  ranking check passes with the sizing memo's skip guard (a fall over 5 points in card skips fails unless the label leg favours
  the candidate) and the same guard on rest heals; (3) on held-out labelled decisions its picks are worth no less than the
  incumbent's (paired lower bound above -0.1 floors a decision). Reported only: win skill, calibration, exam agreement. Then
  the funnel as now.

### 3.5 (c) The improvement loop from that start

1. **Start:** generation 11's fighter, `π_h`, the whole-run judgement, the chooser of 3.3.
2. **Play:** the lab's filler plays the current agent exploring (tau 0.1, eps 0.02 on the blended score), whole runs on the copy.
3. **Deck half, expert iteration:** refit the judgement on human plus new self-play rows; label 1,200 of the agent's decisions a
   round (cards, shops, ancients first, K 4); refit `π_h` on human decisions plus the agent's blended choices plus the labels'
   clear winners (gap over 2 SE), with a KL anchor to the previous prior, so it moves from "what a human picks" to "what works
   for our player" in steps the tests can see.
4. **Fight half:** (a) if x4 or x16 at bosses and elites gains 3 points or more on human boss starts and the fight exam, the
   agent gets a stakes schedule; (b) practice: Act 2 boss starts from 7.5 to 25 in 100, Act 2 elites up, human starts kept; the
   loop's gate moves from the 200-start Act 1 board to the fight exam's cells; (c) the deeper-teacher board (judge leaves,
   training design §1); (d) the potion hold rule now, the one currency after.
5. **Judge:** the promotion rule unchanged (paired floors, fresh 2,000 seeds), with Act 2 boss kills a not-worse guard until both
   arms reach 10 in 100, then co-primary (D24's pattern); the night on 500 seeds; the exam once per frozen candidate.

**The hindsight labels now:** not a target for a blended self-play refit (that line stops) but the arbiter between the human
prior and the judgement under our own player (λ, the label leg), and expert-iteration targets from round 1.

### 3.6 (d) Pitfalls

| pitfall | handling | check |
|---|---|---|
| human choices assume human fight skill (cards our player cannot use; elites look safe) | source input; H from our fights; λ and the label leg decided under our player; the gym practises human decks | label leg; elites and elite deaths per block |
| choices depend on the options seen | softmax over the recorded offers only; rests from relics; merged screens split or dropped; events and routes not imitated | builder tests against `counts.json` |
| human decks unlike ours | donor maps; agreement by act and deck size; labels on our states; KL-anchored steps | label leg by kind and act |
| the copy's Act 2 and 3 errors | human rows are real-game outcomes; the nightly per-act line; if copy and game Act 2 boss rates differ by over 2 SE two nights running, self-play rows past floor 17 are down-weighted until fixed | nightly |
| leakage into the exam fifth | union rule and assert in every builder; tuning on fifth 4 only; one logged read per frozen candidate | builder test; the read log |
| fit instability | deep human targets, Monte Carlo targets, three-seed average, a test of choices, the prior bounding the judgement | keep test |
| abandoned runs left out (29 in 100) | self-play calibration decides | keep test (1) |
| the average human's ceiling (11 wins in 100) | expert iteration moves past it; not a two-week issue | |

## 4. Keep, stop, start

| activity | verdict | reason |
|---|---|---|
| simulator fidelity lane | **change**: only Act 2 and 3 groups that change outcomes, by agent weight (D19), one worker | Act 1 at 0.66 per 1,000 decisions; Act 2 at 4.4 now feeds the judgement; whole runs agree within noise |
| nightly real-game check | **keep**; add the per-act accuracy line, lead with Act 2 boss kills | the judge of transfer |
| lab filler self-play | **keep**, playing generation 11 exploring until the first new agent passes its smoke, then that agent | the judgement's self-play rows |
| presorts, aimed bugs, probes | **keep** at once per tree (D54 item E), no growth | no yield change since 11-03 |
| fight gym loop | **change**: Act 2 weighting, gate on the fight exam's cells, the deeper-teacher board first | about 145 checkpoints without a promotion |
| hindsight label run | **keep** to the 1,200 read, on to 2,400 unless the sizing memo's stop rule fires; new use above | 490 of 2,400 at 08:40Z, about 150 an hour, so the read is due today (*estimate*) |
| generation-12 line (self-play refit, beta, blended fit) | **stop** | refused twice; replaced by 3.4 |
| `a3-v1` in every fight | **change** at bosses and elites if milestone 1 shows the gain | 30 simulations a move at the Act 2 boss |
| morning report | **keep**; section 7's headline, per-act accuracy, exam agreement when scored | |
| paper | **keep** one edition a day (D39); a section on the rethink and its go or no-go | |

**Compute.** 16 logical (8 physical) cores and a card 17 in 100 busy (compute diagnostic); the CPU was half used over 11-01 to
11-03. The new work is light on the card (fits take minutes) and heavy on blocks and fights: milestone 1 about 30 core-hours,
a smoke block 3, a 2,000-seed block about 30. Week 1 fits on the PC beside the loop and the nights; **nothing is rented in
week 1**. In week 2, rent only if decided blocks wait more than a day: the copy alone (our binary; its Linux build is
untested and needs a one-block identity check, about a unit) on 16-vCPU machines at about $0.45 to $0.51 an hour (DESIGN
§3.4, *unverified*), for paired blocks and exploring self-play: a 2,000-seed block is about two hours on one, about $1. The game,
its files and the nightly check never leave the PC. A rented card is not worth it.

## 5. Two weeks

### 5.1 Milestones (Sonnet builds and measures, Opus designs and decides, Haiku checks each landing)

| # | dates (Z) | milestone | who, units | what decides it |
|---|---|---|---|---|
| 0 | 11-05 | decisions recorded; the generation-12 line closed | orchestrator | |
| 1 | 11-06 | **Play or deck?** Generation 11's player on 300 human Act 2 and 300 Act 1 boss starts from fifth 4, two draws, at `a3-v1`, x4 and x16 at the boss; the potion hold rule on a 200-seed smoke | Sonnet 0.5; about 30 core-hours, QUIET line, by 15:45Z | win rate against the humans' 74 and 76 on the same starts; the paired gain of thinking time |
| 2 | 11-06 to 11-07 | the human decision set (card, ancient, rest and smith, shop with rebuilt prices), exam asserted out | Sonnet 1.5 | counts match `counts.json`; prices within 10 gold of gold spent in 9 of 10 visits, else shops wait |
| 3 | 11-07 to 11-08 | `π_h` on the card | Sonnet 1 | 45 in 100 on fifth 4's card rewards |
| 4 | 11-08 to 11-09 | the imitation agent (generation 11's player, `π_h` choosing, λ = ∞; routes by today's judgement): smoke, then the paired funnel against generation 11 | Sonnet 0.5; the lab | paired floors and Act 2 boss kills; label leg |
| 5 | 11-07 to 11-10 | the whole-run judgement: design, then fit and keep test | Opus 0.5, Sonnet 1.5 | 3.4's keep test |
| 6 | 11-10 to 11-12 | the blend (3.3) against the better of generation 11 and milestone 4 | Sonnet 0.5 | the 2,000-seed block; a pass is generation 12 of the new line |
| 7 | 11-06 to 11-12 | fight half: stakes schedule if milestone 1 shows 3 points; Act 2 weighting and the exam-cell gate; the deeper-teacher board | Sonnet 1.5 | fight exam per cell; the block |
| 8 | 11-11 | week-one review | Opus 0.3 | |
| 9 | 11-12 to 11-17 | expert iteration round 1 (3.5 step 3) | Sonnet 2 | keep test; the funnel |
| 10 | 11-18 | the best candidate against generation 11, fresh 2,000-seed paired block; the night on 500 seeds | the lab, the night | 5.2 |
| 11 | 11-19 | go or no-go | Opus 0.5 | 5.2 |

About 11 worker units, five or six points with checks (*estimate*). Milestone 1 orders the rest: if our player wins the humans'
Act 2 boss starts near their 76 in 100, the deck dominates and milestones 2 to 6 go first; near its own 19, the play dominates
and milestone 7 takes the first slot after milestone 2.

### 5.2 Go or no-go on 2026-11-19

**Go** when all hold: (1) a new-recipe candidate is promoted under the unchanged rule; (2) on that block the Act 2 boss is
beaten in at least 8 runs of 100 (generation 11: 5 in the game, 6.5 on the copy) with the paired difference's 95% lower bound
above zero, and the night agrees; (3) the frozen candidate takes the human's card in at least 45 of 100 exam-fifth rewards.

**No-go, the rethink was wrong about the deck,** when the imitation agent and the blend both fail to beat generation 11 (paired
lower bound at or below zero) **and** the label leg finds the human prior's picks worth no more than the judgement's under our
player. Then the deck is not where the gap is: two weeks go to the fight half and human runs stay as judgement rows only. A
partial result (agreement up, floors flat, Act 2 boss up less than 3 points) keeps the human judgement and moves the effort
to fights.

## 6. Risks, and the owner's questions

- **Our player cannot use human decks** and imitation loses floors: milestone 1 and the label leg show it within days.
- **The rebuilt human state is wrong in places** (potions least certain, growing enchantments low, merged screens): a noisy
  prior; the validation bar and the builder's counts catch gross errors.
- **Gains on the copy the game does not show** in Act 2: the nightly per-act line and the two arms' Act 2 boss rates.
- **More experiments than cores:** milestone 1 first, one block at a time, the funnel's early stops, rent only on the trigger.

Questions only the owner can answer:

1. **Money:** may we rent cores in week 2 if decided test blocks wait more than a day (the copy only, never the game;
   under $50 for the fortnight, *estimate*)?
2. **On a no-go:** should the fight-first fallback start at once, or after a review with you?

## 7. The headline measures

| measure | now | humans | why |
|---|---|---|---|
| **Act 2 boss beaten, per 100 runs** (night and paired blocks): **the headline** | 5.0 (copy 6.5) | 28.9 | 80% of the measured gap; about 100 events per 2,000 seeds |
| **wins per 2,000 runs** | 0 | about 228 | the goal; decisive later |
| runs reaching Act 3, per 100 | 5 | 29 | the road to the end game |
| Act 1 boss beaten, of runs reaching it | 56.5 | 74 | the fight half's first test |
| mean floor | 23.35 | 27.05 | stays the promotion measure, no longer the headline |
| exam-fifth agreement, card / rest | 31 / 61 | | the deck half's scoreboard, once per frozen candidate |
| fight exam, per cell | v2: halves 62.9 / 59.0 | | the fight half's ruler |
| the copy's Act 2 accuracy | 4.4 per 1,000 decisions; 24 in 100 runs | | the copy's trust line |

## Not verified

The gain of thinking time with v2's prior; how much of the Act 2 boss gap is play (the fits are associations); the agreement a
human prior reaches (45 in 100 is a sanity bar, not a forecast); every two-week effect size (*estimates*); shop prices rebuilt
from the copy's rules; the copy's Linux build; rental prices; when the label run finishes; why D38's 14,811 differs from this
count's 14,974 (filters not traced; builders use the union rule).
