# The training design: a deeper teacher, hindsight labels, one currency, the machine and the yardstick (2026-11-04)

Design round (Opus), the item D53 queued behind the compute measurement. Written 2026-11-04 from 11:15Z (`date -u`). It decides
four questions with today's numbers and gives a worker brief for each piece. Paths are relative to `D:/spireline/`; fork paths
are relative to the fork's root. Nothing was run for it: every number is read from a file, combined by arithmetic, or marked as
an estimate. Words: **measured** (a record or a timed run says so), **arithmetic** (measured parts combined, not played),
**estimate** (reasoned, not run). The decisions are the design round's, for the orchestrator to record; none of them touches the
promotion rule (`PROMOTION_RULE`, D43), the night's player config, or the exam fifth of the human corpus.

Read for it: the memo `docs/research/2026-11-04-train-and-test-ideas.md`; `docs/diagnostics/2026-11-04-compute-allocation.md`,
`2026-11-04-nightly-power.md`, `2026-11-04-gen12-attempt2.md`; `docs/SUBPROBLEMS.md`; DECISIONS D35, D37 to D39, D43, D47 to
D49, D52, D53 and its addendum. In the fork: `rl/ARCHITECTURE.md`, `rl/combat_mcts.py`, `rl/live_search.py`,
`rl/search_configs.py`, `rl/fight_gym.py`, `rl/gym_loop.py`, `rl/gym_loop_train.py`, `rl/judge.py`, `rl/judge_client.py`,
`rl/prior_server.py`, `rl/gen0.py`, `rl/gen_loop.py`, `rl/run_fields.py`, `rl/run_train/` (models, features, engine),
`src/sts2_gym/run_env.py`. The lab's `LAB/yield.tsv` and `LAB/mix.json` (read-only).

It builds on what lands today (branches read, not merged): the fight exam (`rl/fight_exam.py`, branch `fight-exam`: about
2,000 stratified starts, four paired draws, a judge baseline with a regression adjustment, halves A and B); human practice
starts and the regret-weighted sampler (`rl/human_starts.py`, `rl/practice_mix.py`, `rl/gym_loop.py`, branch
`practice-human-starts`; the loop is relaunched onto it after tonight's block); the speed lane (`--emu-runs` for the copy arm,
the root kill check `a3-v1-k`); and the generation 12 plumbing (the run-layer lane: candidate identity, placement, flush on stop,
exploring filler; 8,000 exploring runs expected 2026-11-05 evening to 11-06).

## 0. The four decisions

| # | Question | Decision | The numbers it rests on |
|---|---|---|---|
| 1 | The deeper teacher | **Judge leaves first** (the teacher's simulation schedule with the fight judge at the leaves instead of rollouts), then playout-cap randomization on top of it, then a Gumbel root only for the cheap decisions; **reanalysis not built** (in this design it is CPU work, not card work). Beside them: the trainer's pass cap tested at 4, 8 and 16 with last-layer resets on the stored buffer, and a confidence fast path for the exam agent as a gated config. | x16 costs 17 to 23 times a3-v1 a fight; a judged simulation 1.7 CPU-ms against 5.1 rolled out; judge-v0 at a fifth of x16's simulations already scores 44.1 on the board against x16's 46.3; the student (47.05) has caught x16; the trainer uses about 40 s of card a day and waits 87% of its time for rows |
| 2 | Hindsight labels | **The value of an option is an n-step return in floors**: K continuations from the rebuilt state with the option applied, played by the fixed exam agent to the end of the current act (its boss included), valued by the death floor or by the frozen run head at the next act. K 4 with common random numbers across options; many decisions, few draws. The run head learns **centred option values (advantages) by weighted regression** beside its existing floor fit; the human's pick and the human run's outcome never enter a label. Pilot on the AI's own runs first (exact states), then human card rewards, rest sites and potion holds. | The copy plays a run in 25.9 process-seconds (1.1 a floor); about 190 process-seconds a decision; a whole machine-day buys about 7,200 decisions, six daytime processes about 1,600 |
| 3 | One currency | A fight's terminal value becomes **the frozen run head's expected final floor of the post-fight state** (death: the fight's floor), mapped per fight onto today's search scale so the exploration constant keeps its meaning; one module serves the live search, the judge leaf and the old label generator. Order: freeze the head (generation 11's), audit its marginals, play (`a3-v1-r`), then teach (the teacher and the value target in the currency). | Today a potion is 10 HP everywhere and a death -100; the AI drinks in 60% of the Act 1 hallway fights it wins holding a potion (humans 23%) and reaches the Act 1 boss with 0.8 potions (humans 1.6), where its kill rate is 41, 56 and 71% with 0, 1, and 2 or more held |
| 4 | Compute and the yardstick | **aimed-bugs to one job a day** (it used more CPU than the loop's practice and its ledger shows no new group since 11-03 02Z, to be confirmed); the freed cores to the loop's practice (6 to 8 processes) and the exam; the card's work is the judge at the leaves; **no rented cores now** (a trigger is set); the yardstick gets **AIVAT-style chance terms**: per draw in the fight exam, and at run-level chance events then fight draws for the night block (estimate: 30 to 50 in 100 of the night's floor variance; one floor would need about 610 runs instead of 1,015). | The lab's daytime jobs 53.2% of the CPU used against the loop's 35.3%; the 16 logical cores are 8 physical; the card 17% busy; the copy-arm control variate buys nothing at today's cost ratio |

## 1. The deeper teacher at training time

### 1.1 What limits the student now

- **The teacher, not the rows.** On the fight board (200 Act 1 boss starts, ten draws) the student v2 wins 47.05%; the x16
  teacher scored 46.3% in M2 (1,999 pairs); the student's top-1 agreement with the teacher is 0.755 and gained 0.4 points over the
  last ten checkpoints (memo section 0, measured). More rows from the same teacher buy less each day. The lever is a stronger
  teacher per CPU-second.
- **What a row costs** (compute doc sections 1 and 2, measured). A practice fight is 54 own seconds (45 CPU-s) and 19.9 rows; the
  loop took 84,000 rows a day; Act 1 boss fights are 36% of the fights and 53% of the seconds. The loop's practice used 550,881
  CPU-s over 11-01 to 11-03, about 2.1 cores on average, and its gates 0.7 cores.
- **The card is free.** 17% busy over three days; the judge server costs 0.082 ms of card a leaf at 15.8 leaves a batch (gates),
  0.023 ms at 41 (judge board) and 0.6 ms at 4.5 (two processes); the trainer used 179 s of card in 110 hours and waits for rows
  87% of its time because of the four-pass cap. The only way to put the card to work at scale is to move leaf work onto it.

### 1.2 The four levers, priced

Own seconds a fight by kind, today's x16 against two judge-leaf teachers (arithmetic: each kind's x16 simulation count times
1.87 own-ms a judged simulation, the gates' figure for judge-v0 on Act 1 boss starts; the exact solver's grading per decision is
not scaled and comes on top). `j480` is x16's simulation schedule (480 a plain play, 1,920 at a target or a choice) with the judge
at the leaves; `j960` is twice that.

| kind (share of practice fights) | x16 (measured) | sims a fight | x16 ms a sim | j480 | j960 |
|---|---|---|---|---|---|
| Act 1 hallway (25.3%) | 20.4 | 8,524 | 2.39 | 15.9 | 31.9 |
| Act 1 elite (12.0%) | 42.9 | 11,413 | 3.76 | 21.3 | 42.7 |
| Act 1 boss (36.3%) | 79.6 | 14,736 | 5.40 | 27.6 | 55.1 |
| Act 2 hallway (13.7%) | 46.4 | 11,827 | 3.92 | 22.1 | 44.2 |
| Act 2 elite (5.9%) | 52.3 | 11,360 | 4.60 | 21.2 | 42.5 |
| Act 2 boss (6.8%) | 79.8 | 17,434 | 4.58 | 32.6 | 65.2 |
| practice mix | 54.0 | 12,352 | | 23.1 (0.43) | 46.2 (0.86) |

**(a) The judge at the teacher's leaves.**
- *Cost a fight:* 0.43 of today's at j480, 0.86 at j960 (arithmetic; the hallway saving is smallest because a hallway rollout is
  short). Rows a fight are unchanged, so j480 gives about 2.3 times the rows a CPU-second.
- *Expected gain (estimate):* at least x16's strength at j480 and above it at j960. Judge-v0, at 90 simulations a plain play (a
  fifth of x16's 480), is 2.2 points behind x16 on the board (44.1 against 46.3), while the rollout search went from 36.9 to 46.3
  for 16 times the simulations. A teacher above the student's 47 raises the student's ceiling; at j480 it also more than doubles
  the rows.
- *Fast test:* (1) the judge's calibration per fight kind on the buffer's held-out rows (card minutes; the judge reads the same
  tokens the trainer stores); (2) the board's 200 starts, 400 paired games each (two draw indices the incumbent was not selected
  on) for x16, j480 and j960 with v2 as the prior: about 3.5 hours of six processes, most of it x16.
- *Risk:* the judge's errors become the teacher's, with no rollout to correct them. Judge-v0 was trained once on a3-v1-era fights
  (D41); its calibration on Act 2 and human decks has not been measured (D37's seam rule asks for it). In practice its batches
  would be small (K 2 a process gives about 5 leaves a batch: 0.6 ms of card and a 1 ms wait a leaf), so practice K must rise to 8
  or more (a stop then loses 8 short fights, about what 2 x16 fights lose now: 8 times 27.6 own seconds against 2 times 79.6).
- *Card at j480 on today's CPU (arithmetic):* about 9,800 fights a day times 12,352 leaves, 121 million leaves: 2,800 s of card at
  41 leaves a batch, 9,900 s at 16 (3 to 11% of a day).
- *Slow test:* the fight exam's half A, a student trained two to three days on the new teacher against the champion, once the
  exam has read three gates (so its spread is known).

**(b) Playout-cap randomization** (most decisions cheap, a quarter deep).
- *Cost a fight:* per decision, deep with probability 0.25 (a policy target) or cheap at judge-v0's schedule (no policy target;
  the move is played and the fight's outcome is still the value label): 0.25 + 0.75/16 = 0.30 of a deep fight.
- *Gain:* policy rows per CPU-second are unchanged (5 deep rows a fight at 0.30 of the cost); fights, value labels and starts
  covered rise 3.4 times. KataGo measured 1.37 times for the whole loop; here the gain comes only through value data and start
  coverage, which matter once the human starts bring tens of thousands of starts and once the judge is retrained on the loop's
  fights. It does not raise the teacher.
- *Fast test:* the trainer's held-out policy cross-entropy at equal CPU; the judge's held-out calibration when retrained on 3.4
  times the fights.
- *Risk:* value labels from mixed-strength play describe a slightly weaker player (acceptable: the exam agent plays the cheap
  config).
- *Slow test:* the exam's half A.

**(c) Gumbel root selection with sequential halving.**
- *Cost:* no extra CPU at the same simulations; the code is in `live_search`'s root (2,288 lines, with the per-move statistics and
  the confirmation built around UCT).
- *Gain:* concentrated at 2 to 16 simulations (Gumbel MuZero); at the teacher's 480 to 1,920 it is small. Its uses here are
  turning (b)'s cheap decisions into usable policy targets, and the player's own 30-simulation search.
- *Fast test:* a Gumbel root at a3-v1's 30 simulations against a3-v1 on the board's 400 paired games; and on stored positions,
  how often the completed-Q target's top move equals x16's, against the 30-simulation visit target's.
- *Risk:* the completed-Q target assumes a trustworthy Q; ours is determinized and noisy at one to four visits a move, so the
  softmax over sigma(Q) moves mass to lucky moves. The root's common-random-number sweep (every move on the same imagined worlds)
  is the natural mitigation and must be kept.
- *Slow test:* the exam's half A on a student trained with the Gumbel targets.

**(d) Reanalysis of stored positions on the idle card.**
- *Cost:* in this design the search runs the copy on the CPU (each simulation forks the engine and steps it); the card holds only
  the prior and the judge. A re-searched old position costs about what a new one costs (2.3 CPU-s a row), brings no new start, and
  must first be replayed from its fight's start (the buffer stores tokens, not engine states). MuZero's reanalysis is cheap because
  its search runs on a learned model on the card; we have no learned dynamics model and this design does not propose one.
- *Gain:* fresher targets for old positions, which new positions also give.
- *Decision:* not built. The card-only variant (re-scoring stored rows' value targets with the newest judge, or with the search's
  root value) belongs to the auxiliary-target item (memo 3.4) and is not urgent while nothing at play time reads the student's
  value head.

### 1.3 Decision and order

**(a) first**: it is the only lever that raises the teacher's strength and cuts its cost at once, and the only one that puts the
idle card to work at scale. Adoption rule, on the 400 paired board games: **j960** if it beats x16 by 3 points or more
(one-sided McNemar p under 0.05): a stronger teacher at about today's cost; else **j480** if its 95% lower bound against x16 is
above -2 points: the same teacher at 0.43 of the cost and 2.3 times the rows; else keep x16, retrain the judge on the buffer's
fights (`judge.py train` on the loop's outcomes) and try once more. **(b)** on the adopted teacher once it has run a day; **(c)**
only for (b)'s cheap decisions, after (b) is read; **(d)** not built. Later, after item 3's value target lands (3b): the student's
own value head in the run currency at the leaves, so that one network call answers prior and value and the leaf is trained
continuously on the loop's fights, as in AlphaZero; the separate judge then retires.

### 1.4 The trainer's passes per row, with resets

Each 30-minute checkpoint trains about 38 steps of 256 rows in 1.0 to 1.3 s of card; four passes over a day's rows cost about
40 s of card (measured). More passes cost nothing scarce; the question is overfitting the teacher's noisy visit counts.
Primacy-bias resets pay above a replay ratio of about 4 (Nikishin 2022), which is ours. **Decision:** test on the stored buffer,
not live. Replay the newest 300,000 rows in arrival order through six arms from the same base checkpoint: cap 4 (two seeds, for
the run-to-run spread), 8, 16, 8 with the heads' last layers reset every 24 checkpoints (12 hours of arrival), 16 with the same
resets. Read the held-out policy cross-entropy (the pre-filter's own figure, D49), top-1 agreement and value loss at matched
arrival points. Adopt the arm with the lowest held-out cross-entropy at the end if it beats cap 4 by more than the two cap-4
seeds differ; resets only if they beat the same cap without them. About 10 minutes of card an arm and one core. Its value grows
after a teacher switch, when a new ceiling has to be climbed from fewer rows.

### 1.5 The confidence fast path

Play the student's top move without a search when its probability is above a threshold. **Price:** the night's AI search is 47
minutes a 500-run block (87,700 decisions at 31 a second, D53 addendum, measured). If a share q of decisions is above the
threshold and those are mostly plain plays (30 simulations, against 120 at a target or a choice), the saving is about 0.6 q of the
search time (estimate): at q 0.4, about a quarter of the hour. The same config cheapens the copy arm, the hindsight continuations
(item 2) and practice. **Never fast:** a decision where a potion is legal and the student's top move is a potion (board piece 5), a
choice screen, a decision where the kill check (`a3-v1-k`) finds a lethal, HP under 30% of max. **Threshold:** from the buffer's
held-out rows, the lowest threshold at which the student's top move equals the teacher's most visited move in at least 97 of 100
rows above it. **Gated like any player change:** 2,000 paired board games against a3-v1 with the 95% lower bound of the
difference above -2 points, the fight exam's half A not worse, then the orchestrator's call on the night's config.

### 1.6 Alternatives rejected, and the risks

- More hours of the x16 teacher (today's path): the student has caught it.
- A cheaper rollout teacher (x4, 3.4 times a3-v1's CPU): weaker than the student, so it teaches nothing. A deeper one (x64): four
  times today's cost for an unmeasured gain, where judge leaves reach the same simulation counts at about a third.
- Gumbel or reanalysis first: priced above.
- Risks across item 1: the judge's drift on decks it has not seen (the calibration table before adoption, per kind; a kind where
  it is off keeps rollouts, since a config can name the leaf per fight kind); the practice K change (stop losses; memory, six
  processes stay under `MEM_LIMIT_GB` 3 each); more passes overfitting (the held-out figure decides); the fast path skipping the
  search exactly where the student is confidently wrong (the exclusions and the board).

### Briefs for item 1

**1a. The teacher with judge leaves.** Sonnet, 2 units (one day). Fork files: `rl/fight_gym.py` (arms `j480` and `j960`: a3-v1's
schedule times 16 and 32 with `leaf="judge"`, built like `arm_settings`), `rl/gym_loop.py` (a judge-leaf teacher in practice: the
judge server started beside the prior server as for gates; `--practice-k`), tests. Steps: (1) the judge's calibration per kind on
the buffer's held-out rows (win Brier and log loss, HP error if won), a table; (2) the arms and the practice path; (3) the board,
400 paired games each for x16, j480 and j960 with v2's prior, under a QUIET.lock line `teacher-board` with the Windows PID,
BelowNormal, outside the night and the half hour before it, split over two days if the window is short; (4) if a kind's judge is
off, the judge retrained on the buffer and step 3's judge arms replayed. Done: the strength and seconds-a-fight table, the
adoption by section 1.3's rule, and the relaunch arguments for the orchestrator (the worker does not relaunch the loop). The test
that fails before and passes after: `arm_settings("j480")` returns a config with leaf "judge" and x16's simulation schedule
(KeyError today), and a judge-leaf teacher task in `gen_game_steps` asks a stub judge for leaves. Must not move: the Python-only
gate's new failures (0 against the baseline of the tip it rebases on; at e22346e1, 4,092 tests and 18 failures: 16 baseline,
`engine.py:760` and the niceness test that passes alone; lab modules all OK); `arm_settings` for a3-v1, x4, x16 and judge-v0;
the moves of a3-v1's board games (`moves_sha` on a 20-game sample).

**1b. Passes per row and resets, on the stored buffer.** Sonnet, 1 unit. Fork files: `rl/gym_loop_train.py` (`--reset-every N`
for the heads' last layers; a `replay` subcommand that trains arms offline on the shards in arrival order and scores them at
matched points), tests. Runs on the card under the loop's GPU_OK rules (the live trainer keeps priority) and one core; no QUIET.lock
line (it plays nothing). Done: section 1.4's table and the recommended flags (the orchestrator sets them at a relaunch). Fails
before and passes after: after `reset_every` checkpoints the heads' last linear layers are re-initialised and the encoder is not;
the budget accepts `--max-epochs 16`. Must not move: the gate; the default flags train exactly as today (a seed-fixed chunk gives
the same loss).

**1c. The confidence fast path.** Sonnet, 2 units, after `a3-v1-k` lands (same file). Fork files: `rl/search_configs.py`
(`a3-v1-f`: the threshold and section 1.5's exclusions, combined with the kill check), `rl/fight_gym.py` (`play_steps` plays a
fast decision with no search and counts it in the row), a measuring script on the buffer's held-out rows, tests. Steps: the
curve (share above the threshold and agreement there, for thresholds 0.6 to 0.99); the threshold; the board's 2,000 paired games
(about 30 minutes of six processes, QUIET.lock line `fast-path`); the exam's half A when its champion has played. Done: the
numbers, seconds a fight and decisions searched; the night's config unchanged. Fails before and passes after: `a3-v1-f` answers
"fast" for a confident plain play and "search" for a potion, a choice screen and low HP; a fast decision runs no simulation. Must
not move: the gate; a3-v1's games (`moves_sha` sample).

**1d. Playout-cap randomization.** Sonnet, 2 units, after 1a's teacher has run a day. Fork files: `rl/gym_loop.py`
(`gen_game_steps`: each decision deep with probability p from a seeded draw on start, game and decision, else the cheap config;
cheap rows carry no policy target), `rl/gym_loop_train.py` (reads it), tests. Done: a day of practice at p 0.25: fights and rows a
day, starts covered, the trainer's held-out cross-entropy at equal CPU. Fails before and passes after: a cheap decision's row is
never a policy sample in `batch_tensors`. Must not move: the gate; p 1 reproduces today's practice.

## 2. Hindsight labels for the run layer

### 2.1 What the value of an option is

For a decision d at state s with options o_1 to o_n, the copy rebuilds s, applies each option as a transform of the state (the
card added or not; the heal or the upgrade; the potion kept for later or not), and plays K continuations from it. Each
continuation's return G is **the floor where the run died, if it died before the end of the current act; otherwise the frozen run
head's expected final floor at the first decision of the next act**. The label Q(d, o) is the mean of G over the K continuations.
The unit is floors, the run head's own unit, so the label is both: floors reached inside the horizon and the head's value beyond
it (an n-step return). The human's choice is one option among the others, not the target, and the human run's own outcome never
enters a label.

Decisions and options:
- **Card reward:** the offered cards and skip (four options; more where a relic adds one).
- **Rest site:** heal, the human's upgrade, and the frozen head's best upgrade (two or three after duplicates).
- **Potion hold:** at a hallway fight the human entered holding a potion, the fight played with potions allowed against potions
  locked, then the rest of the act as usual (two options). This is the run-level price of keeping a potion (board piece 5); the
  in-fight potion move stays the fight player's (item 3).
- **Route and shop** cannot be rebuilt from the human record (it holds the rooms visited, not the map, and the purchases, not the
  prices on offer; SUBPROBLEMS pieces 3 and 6). They come from the AI's own exploring runs, where the copy holds the exact state
  and the options on screen; that is also the pilot's source (2a), which needs no rebuild.

### 2.2 How far forward, and how many draws

- **Horizon: the end of the current act, its boss included.** The boss decides Act 1 (56.5% killed once there), and a card's
  effect needs several fights to show. The run's end would triple the cost of Act 1 decisions, add the late-run spread (the final
  floor's SD is about 8) and lean on Act 3, whose copy fidelity is barely verified. A zero horizon is the head grading itself.
- **Draws: K 4 an option, common random numbers across options.** Continuation k of every option uses resample seed k, so the
  options meet the same map, encounters and reward rolls for as long as their decks allow. More decisions beat more draws: the
  head generalizes across decisions, so a card's average advantage over 1,500 offers at K 4 has a standard error of about 0.05
  floors if the paired SD is 4 floors (estimate). The pilot measures the paired SD and the correlation between options and sets K
  at 4 or 8 by that arithmetic.
- **Recorded beside each continuation:** the state at the boss door and the judge's estimate of the boss fight there, so that a
  multi-fidelity label (the judge at the door for every continuation, the boss played for some) can be computed afterwards with no
  replay.

### 2.3 How the player in the replay is fixed

Fixed, and written into every label file's manifest: the exam agent at the time of the label run (the fight player's checkpoint
sha with the a3-v1 config, or `a3-v1-f` if 1c has been adopted by then), the frozen run head of generation 11 (the weights
generation 9 trained, sha256 `f0a199fb...`) for the continuations' run choices, argmax, no exploration; seeds in a namespace of
their own from (run id, floor, decision kind, k). The labels are values under that policy, and a head trained on them is one step
of policy improvement. A label set is regenerated when the exam agent changes generation; old and new labels are not mixed in one
fit.

### 2.4 What a machine-day buys

The copy plays a run in 25.9 process-seconds: 3,781 exploring runs in 1.7 hours at 16 processes on 2026-11-02 (gen12 doc,
measured), 1.1 process-seconds a floor at generation 11's 23.4 floors. Planning figure 1.4 a floor (later floors and bosses cost
more). A continuation to the act's end is about 9 floors with its boss: about 14 process-seconds (estimate). A decision is 3.4
options on average times K 4 = 13.6 continuations, about 190 process-seconds with the rebuild. **A whole machine-day (16
processes) buys about 7,200 decisions; six processes for 14 daytime hours about 1,600** (arithmetic). The memo's 20,000 a
machine-day counted one continuation an option.

The four training fifths hold about 11,800 runs; Acts 1 and 2 give roughly 140,000 card rewards, 60,000 rest sites and 35,000
potion-hold fights (estimate from counts a run). So the labels are a sample: **10,000 decisions** (about 1.4 machine-days),
stratified 40 in 100 Act 2 card rewards (the skip gap: 7% against the humans' 34%), 25 Act 1 card rewards, 20 rest sites, 15
potion holds.

### 2.5 How the run head learns from them, without the luck bias

**Decision: advantage regression, added to the existing Monte Carlo floor fit.** For decision d, the label's centred value is
A(d, o) = Q(d, o) minus the mean of Q over d's options; the head's own centred value comes from its afterstate encoding (the path
the run macro already uses, `features.encode_afterstate`): V(after(s, o)) minus the mean over the options. The loss is the existing
floor loss on self-play runs plus lambda times the sum, over labelled decisions and options, of w_d times the squared gap between
the two centred values, with w_d = 1 / (s_d^2 / K + tau^2), s_d the decision's own measured spread (shrinkage, so a noisy decision
weighs less). Lambda starts where the hindsight term's gradient is about the floor term's, then is set by the ranking check's
hindsight leg on a tuning fifth.

- **Why centred values:** the luck of the rebuilt state (a strong or weak deck) moves every option together and cancels; the floor
  fit keeps the head's level.
- **Why no luck bias:** each label is an expectation over fresh futures from a fixed state under a fixed policy, and every option
  is played on the same futures. Return-conditioned methods fail on luck (ESPER; Kumar 2022) because they condition on the realized
  return; nothing here does. The states are the ones humans reached: a shift in which states are labelled (toward states the agent
  should learn to reach), not a bias in the labels.
- **Rejected:** regressing V(after) on the raw Q (levels), which fights the floor fit over the rebuilt states' luck; a preference
  target (which option won), which throws away the size of the gap and overweights near ties; imitating the human's pick (33 in
  100 agreement, and agreement barely tracks strength).
- **D6 holds:** this is Monte Carlo evaluation of a fixed policy and a supervised fit, the family of the floor fit already in use,
  not reinforcement learning through the run. **D7:** no language model anywhere in it.

### 2.6 Data rules

D38: only the four training fifths. The exam fifth is out by id and by the fixed hash rule (the union, as `human_starts.is_exam`),
and a written label record that belongs to an exam run stops the build. A fifth of the labelled runs (by run id, under a second
fixed hash) is the hindsight leg's held-out set, never fitted. Reports carry aggregates only; a cell under 20 runs is not shown
(D13).

### 2.7 Tests

- **Fast:** the ranking check (D47, D49) gains a third leg, hindsight. On the held-out labelled decisions: the rank correlation of
  the head's centred option values with the labels', and the share of decisions whose top option is the label's (weighted by the
  label's centred value over its spread). A candidate head passes the leg when it beats the incumbent's on both by more than their
  paired standard error. Plus the per-decision exam on the exam fifth (`boss_entry_exam.py agreement`, 8 minutes), read for the
  Act 2 skip share (7% against 34%) and the named cards (Battle Trance, Shrug It Off, Bloodletting).
- **Slow:** the funnel (the 200-seed smoke block, the paired looks) and the 2,000-seed night block.

### 2.8 Risks

- **The rebuild differs from the human's state** (relic counters, enchantments that grow, potions found in events; `human_starts`
  lists them): the rebuild is checked against the record at that floor and refused by reason.
- **More noise than estimated:** the pilot reads it before any label run.
- **The continuation policy's own errors:** the run head that plays the continuations may undervalue HP, as generation 12's refused
  fit did (D47), which biases rest labels; rest labels are read against the human heal rate before they are used.
- **Flat Act 2 labels:** the agent kills the Act 2 boss 13 times in 100, so most continuations die there whatever the option; the
  pilot reads the per-act spread of the centred values, and Act 2 labels whose spread is mostly noise are dropped, not fitted.

### Briefs for item 2

**2a. The hindsight runner, and a pilot on the AI's own runs.** Sonnet, 3 units. Fork files: `rl/hindsight.py` (new): replay a
recorded generation 11 exploring run on the copy to a decision, clone the run there (`Sts2RunEnv.clone(resample_hidden=True,
seed=k)`), step each option, continue with section 2.3's fixed policy to the end of the act, the boss included, and value the end
as in 2.1; a manifest with the policy shas and seeds; tests. Pilot: 100 decisions of each kind (card reward, rest, route, shop
where present) at K 8, under a QUIET.lock line `hindsight` (about 1.7 hours of six processes, BelowNormal, outside the night).
Done: the paired SD of option differences and the correlation between options by kind and act; the cost of a continuation; the K
that gives 0.05 floors over 1,500 decisions (arithmetic); the share of decisions whose options all die at the boss. Fails before
and passes after: on a fixture run, two options from one state with the same seed k meet the same first encounter and map, and G
is the death floor on a forced death and the head's value at the next act otherwise. Must not move: the Python-only gate (new 0);
self-play, the loop and the night are untouched.

**2b. Human decision states rebuilt on the copy, and the label run.** Sonnet, 3 units, after `practice-human-starts` lands and 2a
has set K. Fork files: `rl/hindsight_human.py` (new), reusing `human_starts`' replay of a human record and its exam rule. The
rebuild: a copy run on a fresh seed, advanced to the human's act and floor with fights resolved by `debug_resolve_combat` and rule
choices elsewhere, then `debug_set_player` (HP, max HP, gold, cards, relics, potions, slots) at the decision; checked against the
record at that floor (deck, relics, HP, gold) and refused by reason. Options as section 2.1's transforms. The label run: 10,000
decisions stratified as in 2.4, in the filler's slot after generation 12's exploring runs are done, BelowNormal, stopped by the
night, resumable. Done: the label file and manifest, the aggregate report (counts by kind, act and refusal reason; cells under 20
runs suppressed), `assert_no_exam` on every written record. Fails before and passes after: a run id of the exam fifth in the input
stops the build; a rebuilt state equals its record on a fixture run. Must not move: the gate; the human starts' own outputs.

**2c. The run head learns from the labels.** Sonnet, 3 units, after 2b and after generation 12's attempt 2 is judged (both change
the V_run fit). Fork files: `rl/run_train/train.py` (the advantage term and lambda), `rl/run_train/ranking.py` (the hindsight
leg), `rl/gen0.py` (`vrun-fit --hindsight LABELS`), tests. Steps: the fit with lambda set on the tuning fifth; the D33 keep test,
the ranking check with its three legs and the per-decision exam; a candidate is built only if all pass; the funnel and the block
are the orchestrator's. Done: the keep document with the hindsight leg against the incumbent. Fails before and passes after: on a
synthetic set where one option is always a floor better, the head's centred value for it rises with lambda above 0 and not at 0;
the leg refuses a head whose option ranking is reversed. Must not move: the gate; a fit with no labels gives today's fit
(`vrun_fit.json` and the head's sha on a fixture).

## 3. One currency for fights

### 3.1 Today's currency

The search's value is HP: a win is end HP plus 10 for each potion held, a death -100 (`live_search._outcome`, `DEATH_VALUE`,
`fight_gym.POTION_VALUE`); the tree divides by max HP, the scale its exploration constant was tuned on. The judge's leaf is mapped
into the same units (`judge_client.estimate`); the board's L0 uses the same 10-HP potion; the trainer's value target is the end-HP
bucket with death first (`gym_loop.compact`'s label, `gym_loop_train.losses`); the old label generator's
`combat_mcts.terminal_value` is the HP fraction with death 0. ARCHITECTURE's "one currency" (a terminal is V_run of the exact
post-fight state) was never built.

What that costs (SUBPROBLEMS piece 5, measured on the self-play shards): the AI drinks in 60% of the Act 1 hallway fights it wins
holding a potion (humans 23%), wins 99.5% of them anyway, and arrives at the Act 1 boss with 0.8 potions (humans 1.6), where its
kill rate is 41, 56 and 71% with 0, 1, and 2 or more held. Under the HP currency a potion is worth 10 HP in a hallway and at a
boss alike; the run head will say what it is worth in each (the boss figures are an association, not a price).

### 3.2 The run currency

- **Terminal value of a fight:** T = the frozen run head's expected final floor of the post-fight state if won; the fight's own
  floor if lost (the run ends there, exactly).
- **The search's units, per fight start:** v = DEATH + (T - T_lost) / (T_full - T_lost) x (max HP at the start - DEATH), with
  T_full the head's value with full HP and every starting potion held. Within one fight this is an affine function of the expected
  final floor, so the search maximizes expected final floor; the spread from a death to a full-HP win is today's (-100 to max HP),
  so the exploration constant, the confirmation's arithmetic and the board's statistics keep their measured meaning.
- **A judge leaf:** v = P(win) x v(T(HP if won, potions if won)) + P(death) x DEATH. Composing a mean through V is Jensen's error;
  a judge trained on the currency directly (3b) removes it.
- **The post-fight state:** the fight start's run view with HP, max HP, the potions still held (by identity) and gold replaced by
  their end values; deck and relics as at the start. Persisting in-fight changes the observation shows (a max-HP gain) are carried;
  the others are listed as not carried.

### 3.3 What the run head must expose

A module `rl/run_currency.py` (numpy only; it loads the head's numpy export through `run_train.models.load_numpy`):
- `FightCurrency(start view, head, floor)`: T_lost, T_full, and `value(hp, max_hp, potions, gold)`, memoized by key and evaluated
  in batches of the distinct keys a search has asked for. One numpy forward of the head's MLP (454 to 256 to 256 to 53 floor
  classes) over a few hundred rows is well under a millisecond (estimate), so the search's hot path is a dictionary lookup.
- `audit(head)`: the head's marginal table: floors for 10 more HP at 30, 60 and 90% HP, for each potion held by kind, for 50
  gold, by act and floor band; and the HP-to-potion ratio against today's 10 HP.
- **The start records carry the run view.** Night starts: from the run engine at the fight's start during the start builder's
  replay. Human starts: from the record, with the map-ahead block set to the act-and-floor mean of the self-play shards. The map is
  the same before and after a fight, so its error moves T_lost and T_full together and touches only the head's second-order terms.

### 3.4 The order: freeze, audit, play, then teach

1. **Freeze.** Generation 11's head is the currency. A refit head (generation 12's attempt 2 or later) becomes the currency at
   most once a week, only after it passes the ranking check and the audit, and only after the fight exam on the new currency is
   not worse.
2. **Audit.** Stop if a potion is worth under 3 or over 40 HP-equivalent in an Act 1 hallway fight, or if V is not increasing in
   HP in some act and floor band. Generation 12's refused fit undervalued HP (D47); the audit keeps that from being taught to the
   fight player.
3. **Play.** A config `a3-v1-r` (a3-v1 with the run currency), read on the fast tests.
4. **Teach.** The teacher plays with the currency (`x16-r`, or the adopted judge teacher with `-r`), so the student imitates
   run-currency play; the value target becomes the normalized currency u = (T - T_lost) / (T_full - T_lost), in [0, 1] with death
   0, and the end-HP buckets stay as an auxiliary head (memo 3.4); the judge is retrained on u.

**Two heads trained against each other** is the risk the order is built for: the fight player learns against a frozen run head;
the run head is refit on the new fighter's runs (the fighter-matched recipe) only after that fighter is promoted, and becomes the
currency only through the audit and the exam. They alternate; they never move together.

### 3.5 Tests

- **Fast:** (i) the audit, in seconds; (ii) the board, `a3-v1-r` against a3-v1, 400 then 2,000 paired games, the 95% lower bound
  above -2 points (a boss fight values potions under both currencies, so little should move: a guard); (iii) the fight exam's
  Act 1 hallway and elite cells (100 starts each, four draws): the share of won hallway fights that began with a potion in which
  one was drunk (60% today) down, the hallway win rate not under 99%, HP lost a hallway fight reported; (iv) a 200-run copy batch
  with `a3-v1-r` as the fight config: **potions held at the Act 1 boss door** (0.8 today, humans 1.6) up, **relics held at the
  door** (4.2) not down, the copy's Act 1 boss kill not down beyond its standard error.
- **Slow:** the night block of a promoted agent (2,000 seeds): floors and the Act 1 boss kill. Potions at the doors on the real
  arm wait for the per-fight record in `rl/run_fields.py` (the nightly power doc's lead).

### 3.6 Alternatives rejected, and the risks

- A better constant (a potion is 20 HP): one number cannot be right in a hallway and at a boss, and potion kinds differ.
- The judge predicting the post-fight state for the run layer to compose: ARCHITECTURE's argument holds; potions spent are a
  choice the tree prices, not an outcome to forecast.
- P(win) as the currency: no HP or potion gradient at all.
- Training the fight player and the run head together: two moving targets.
- Risks: a mispricing head (the audit and the freeze); Jensen's error at judge leaves (3b); the post-fight state's approximations
  (gold, persisting deck changes); the map block of human starts; the scale map keeping the exploration constant's meaning only
  approximately (the board is the guard).

### Briefs for item 3

**3a. The run currency at play time.** Sonnet, 4 units, after `practice-human-starts` lands (the start records) and after 1c (the
same config file). Fork files: `rl/run_currency.py` (new, section 3.3); `rl/live_search.py` (`_outcome` takes an optional
terminal function, default unchanged); `rl/judge_client.py` (`estimate` composes through it when given); `rl/combat_mcts.py`
(`terminal_value` reads the same module when given one, so the old label generator and the live search cannot drift);
`rl/search_configs.py` (`a3-v1-r`); `rl/gym_loop.py` and `rl/human_starts.py` (the run view in the start records); tests. Steps:
the audit (stop on its rule); section 3.5's fast tests (ii) to (iv): the board (about 35 minutes of six processes for 2,000), the
exam's two cells (800 games, about 20 minutes), the copy batch (about 25 minutes of six), under a QUIET.lock line `currency`.
Done: the audit table, the three readings with their standard errors, the config; nothing switched. Fails before and passes
after: on a fixture head, T rises with HP and with each potion held, a death returns the fight's floor, and the map sends a death
to -100 and a full-HP win holding every potion to max HP; with the currency, a potion drunk in a hallway costs the head's
marginal, not 10. Must not move: the gate; a3-v1's games (`moves_sha` sample); the board's figures for the existing arms.

**3b. The currency in practice and in the value target.** Sonnet, 3 units, after 3a passes and the exam has read it. Fork files:
`rl/fight_gym.py` (teacher arms with `-r`), `rl/gym_loop.py` (the label u beside end HP), `rl/gym_loop_train.py` (the value head
on u, the HP buckets as an auxiliary head), `rl/judge.py` (a judge trained on u), tests. Done: a day of practice on the `-r`
teacher; the trainer's held-out value error on u; the judge's calibration on u; the student gated as usual; the exam's hallway
potion reading on the next promoted version. Fails before and passes after: a won fight's u is in [0, 1] and a lost fight's 0;
the value loss reads u; the HP head still trains. Must not move: the gate; the end-HP label is still written.

## 4. Compute and the exam's yardstick

### 4.1 The lab's daytime cores

Measured (compute doc table 2b, 11-01 to 11-03): the job ledgers used 49.9% of 16 logical cores; of what was used, the lab's
daytime jobs took 53.2% (aimed-bugs 592,890 CPU-s, the lab's own selfplay 157,386, its train job 154,404, presort 91,350,
score-real 41,730, bench-env 27,936), the loop 35.3% (practice 550,881, gates 180,774), the nights 11.5%. **The 16 logical cores
are 8 physical cores with two threads each**, so half the logical capacity is not half the machine idle: the second thread of a
busy core adds a fraction (estimate: a fifth to a third). Moving cores between jobs is the lever, not adding jobs.

**Which sweeps still pay under D39.** aimed-bugs alone used more CPU than the loop's practice. Its ledger (`LAB/yield.tsv`) shows
87 fix-ready items in 15 jobs from 11-01 to 11-03 01:41Z, then 24 jobs since 11-03 02Z (7,321 CPU-minutes, 1,710 mismatches)
with 0 new groups and 0 fix-ready in its columns. Either the known groups are saturated or the report step no longer writes those
columns; the orchestrator checks which in the runner's reports before acting. **Decision:** aimed-bugs to one job a day (about
330 CPU-minutes), more only when the fix lane asks for a group's repro; retest stays; presort stays (its skips landed today); the
exploring filler stays until generation 12's 8,000 runs, then its slot runs the hindsight labels (2b); the lab's train job stays
(generation 12); bench-env on demand only. The freed CPU (about two cores on the three-day average) goes, in order, to the loop's
practice (6 to 8 processes by day: rows are what the trainer waits for), the fight exam's readings, and the hindsight runs. The
night keeps the whole machine.

### 4.2 The card

Its free capacity is large (17% busy; the trainer about 40 s a day). Its work, in order: the judge at the teacher's leaves (1a; 3
to 11% of a day at j480's rate if batches reach 16 to 41 leaves); more passes per row (1b; minutes); the exam's chance terms (4b;
seconds). Reanalysis is CPU work in this design (1.2 d), so the card needs no job of its own.

### 4.3 Rented Linux cores

**Not now.** Porting would take the copy's native library built and tested for Linux (the fork's .NET build and its C# suite), a
practice worker without the Windows process controls (Job Objects, priority classes; the prior protocol already has a socket path
off Windows), the prior on the worker's CPU or a rented card: about 3 to 4 units. The data path is small: the newest checkpoint
(megabytes) pulled every 30 minutes, the shards pushed back (the loop's 84,000 rows a day), the start set (about 28 MB a night)
shipped once a night. The owner's call comes first: the copy carries the game's rules, and its engine leaving the PC is his
decision (D9; the cloud credit stopped on 2026-10-25, D30). **The trigger to price it:** after 1a and 4a, when the loop's practice
is CPU-bound with the cheaper teacher (the trainer's fresh-row wait under 30% of its time) and the exam shows the student still
gaining by the day. Until then the PC's freed cores and the judge's 2.3 times are cheaper than any rental.

### 4.4 The yardstick

**The fight exam.** It adjusts each start by regression on the judge's opening value (its own docstring says: not AIVAT). The
stronger and cheap form: at each draw of an exam game the copy can take the expectation over the chance outcome. A luck term is
the judge's value after the draw minus the mean judge value over M resampled draws from the position before it (the copy forks
the pre-draw position with a resample seed). Summed over a game, the luck terms have mean zero for any player (AIVAT's property:
exact chance probabilities, any value function), so the corrected score stays unbiased with the draw luck taken out. Cost: M 8
times about 8 turns, 64 judge leaves and forks a game, about 10 ms of CPU against a game's 5 s (estimate). Expected: 20 to 40 in
100 of the paired-difference variance removed on top of common draws (estimate: the draws are shared until the two players' first
different move, and the luck terms carry the gain after it; the poker figure, 85 in 100 of the SD, is a ceiling, not a forecast).

**The night block.** The run head's value per floor, used as a covariate as it stands, would subtract skill as well as luck (a
better agent raises its own value per floor), so the difference between two agents would shrink toward zero. Only chance terms
qualify: at each chance event with known odds (the act's boss drawn; an elite or hallway encounter drawn after the agent chose
the room; a card offer; a potion or relic drop; and in fights each draw and enemy roll), the value after the event minus its
expectation over the odds, valued by a function fixed before the night (the frozen run head, the judge, or a per-encounter table
from earlier nights). **Stage 1**, the run-level events the game-log copies hold (the encounter id of every combat room, the boss
included; the rewards): estimate 5 to 15 in 100 of the floor variance (the Act 1 boss kill rate alone runs from 27% to 73% by
boss). **Stage 2**, the draws in the real arm's fights: the real arm already loads a copy snapshot at every decision for its
search, so the luck terms can be computed there; estimate a further 25 to 40 in 100. **Together, estimate 30 to 50 in 100**: at
40, a one-floor change needs about 610 runs a night instead of 1,015, and half a floor about 2,430 instead of 4,057.

**Measuring it on the nine nights.** Stage 1 on the seven nights with game-log copies (10-29 to 11-04), in the nightly power doc's
table (raw SE, corrected SE, 1 - rho^2), with the mean of the correction checked near zero on each night's copy arm, where the odds
are exact. Stage 2 cannot be read on past nights (no per-decision states were kept): it is measured first on a fresh 500-run
copy-arm batch, where every state is at hand, then on the real arm after the driver change.

### Briefs for item 4

**4a. The lab's daytime cores.** The orchestrator's change, 1 unit with a Haiku read. Steps: confirm in the runner's reports that
aimed-bugs' zero groups and zero fix-ready are real; then `LAB/mix.json` (aimed-bugs' weight) or a once-a-day cap in
`LAB/jobs.json`, with a dated backup and `_note`, outside a night; the loop's `--procs` 8 by day at its next relaunch, after a
night, at a verdict line. Done: two days later the compute doc's tables 2b and 3 re-read for the new window (the loop's CPU share,
rows a day, the trainer's fresh-wait share), and the fix lane's repro requests answered. No code test; the read compares the
windows.

**4b. AIVAT in the fight exam.** Sonnet, 2 units, after the exam lands and the champion's calibration games are played. Fork
files: `rl/fight_exam.py` (the observer records at each draw the judge's value of the position and the mean over M resampled forks
of the pre-draw position; the luck sum a game; `report` and `compare` print the corrected scores beside the regression-adjusted
ones), tests. Measure on the champion's calibration games replayed with the luck recorder (their seeds reproduce them), and on the
first candidate's `compare`: within-start variance raw, regression-adjusted and corrected; the luck sum's mean (near 0). Done: the
table and a note on whether the exam's gate reading should use the corrected score (the rule itself unchanged until the
orchestrator decides). Fails before and passes after: on a fixture where the draw is the only randomness, the corrected score
varies less across draws with the same mean within its standard error; the luck sum averages 0 over many seeds. Must not move:
the exam's existing readings; the gate.

**4c. The night block's covariate, stage 1.** Sonnet, 2 units, Spireline repo: `tools/morning_report.py` and a test file. Chance
terms: the act's boss drawn, and each elite and hallway encounter drawn given the room, valued by a table of the previous
generation's outcomes by encounter and act (fixed before the night, written beside the report), minus the expectation over the
pool's odds (the copy's pools where the report can read them, else the encounter frequencies over earlier nights' copy arms;
either way the correction's mean is checked near zero). Read on the seven nights with game-log copies. Done: the table like the
nightly power doc's, and the go or no-go for stage 2 (a fork change in the night driver, briefed after this reading). Fails before
and passes after: on a synthetic night where the boss alone decides the floor, the corrected SE is near zero; a night with no game
logs reads "not measured". Must not move: every existing figure of the report (`--check`: 0 mismatches on the nine nights); the
suite (213 tests at 9ac39d4, all passing).

## 5. Order of execution, dependencies and the week's budget

One unit is about half a day of one worker. Heavy runs take a QUIET.lock line with their Windows PID, run BelowNormal, stay out of
the night and the half hour before it, and stop when another line stands.

| order | brief | model | units | starts after | machine |
|---|---|---|---|---|---|
| 1 | 1b passes per row and resets | Sonnet | 1 | now (no file shared with today's landings) | card minutes, one core |
| 1 | 4c night covariate, stage 1 | Sonnet | 2 | now (Spireline `tools/`) | minutes |
| 1 | 4a the lab's daytime cores | orchestrator, Haiku read | 1 | tonight's block ends; after the run-layer lane's `jobs.json` edit | none |
| 2 | 1a judge-leaf teacher | Sonnet | 2 | any day outside the night (files `fight_gym.py`, `gym_loop.py`; rebase on `practice-human-starts`) | about 3.5 hours of six processes |
| 2 | 2a hindsight runner and pilot | Sonnet | 3 | now (generation 11's 3,781 exploring runs exist) | about 1.7 hours of six processes |
| 3 | 1c confidence fast path | Sonnet | 2 | `a3-v1-k` lands (same file) | 30 minutes of six processes, then the exam |
| 3 | 4b AIVAT in the exam | Sonnet | 2 | the exam lands and its champion has played | replays of calibration games |
| 4 | 3a run currency at play | Sonnet | 4 | `practice-human-starts` lands; 1c | about 1.5 hours of six processes |
| 4 | 2b human states and the label run | Sonnet | 3 | `practice-human-starts` lands; 2a sets K | about 1.4 machine-days in the filler's slot, over several days |
| 5 | 1d playout-cap randomization | Sonnet | 2 | 1a's teacher has run a day | practice only |
| 6 | 2c the run head on the labels | Sonnet | 3 | 2b; generation 12's attempt 2 judged | a fit, about an hour |
| 6 | 3b currency in practice and the value target | Sonnet | 3 | 3a passed and read by the exam | practice only |

**Dependencies on today's landings.** The fight exam (D53 item 1): 4b, 3a's exam cells, and every slow test in items 1 and 3.
Human practice starts and the regret sampler: 3a (the start records carry the run view; `gym_loop.py` and `human_starts.py` are
that branch's files) and 2b (its record replay and exam rule). The speed lane's `a3-v1-k`: 1c (the fast path never skips a found
lethal; same file). The generation 12 plumbing and attempt 2: 2c waits for its judgement; the frozen currency head stays generation
11's either way; 2a reads the exploring runs that lane produces. The loop's relaunch onto the regret sampler after tonight's block:
1a's teacher switch, 1b's flags, 4a's processes and 3b's teacher are relaunches of the same kind, each after a night at a verdict
line, done by the orchestrator.

**The week's budget** (to the reset, 2026-11-10 21:00Z; ceiling 65 in 100, about 9 used at the start of this round). The twelve
briefs are 28 units. At about 0.4 points a Sonnet unit (estimate from D49 to D53's items, 0.5 to 1.5 points for items of one to
three half-days), they are about 11 points. This week, orders 1 to 4 (1a, 1b, 1c, 4a, 4b, 4c, 2a, 3a and 2b's build) are about 20
units, about 8 points, plus about 1.5 for landing checks and the orchestrator's reading: the week would read about 18 or 19 of 65.
Next week, 1d, 2c and 3b (8 units), about 3 points. That leaves room for D53's queued auxiliary targets (memo 3.4), the run-layer
lane's generation 12 work and the fidelity lanes.

## Sources

Inside: the files listed at the top; numbers from the compute doc's tables 1, 2a, 2b, 3 and 4 and its benchmark; the nightly power
doc's tables 2 to 4; the generation 12 doc's count and pace; SUBPROBLEMS pieces 1 to 6; the memo's sections 0, 1, 3 and 6;
`LAB/yield.tsv` (aimed-bugs rows from 11-01); the branches `fight-exam` and `practice-human-starts` read at their tips. Outside (as
cited in the memo): KataGo (Wu 2019), Gumbel MuZero (Danihelka 2022), MuZero Reanalyse (Schrittwieser 2021), primacy bias
(Nikishin 2022), AIVAT (Burch 2018), CUPED (Deng 2013), multifidelity Monte Carlo (Peherstorfer 2016), ESPER (Paster 2022), Kumar
2022, SpireBench (2610.12596).
