# The labels against the blocks: where the human prior's gain is, what a hindsight label can judge, round 1's weights, and x8 (2026-11-08)

Opus analysis worker on D55 addendum 11 (`DECISIONS.md:1369`; brief `referee/backlog/labels-question/BRIEF.md`), written from 11:06Z
(`date -u`). Every figure is read from the file named (`path:line` or a JSON key), counted from saved rows (read only), arithmetic on
those, or marked *est.* Probes: three read-only analyses of saved files (one process, seconds to 77 s) and one copy probe (six
BelowNormal processes, 11:42Z to 12:34Z, 5.0 core-hours of runs; section 3.2). Scripts and outputs:
`referee/backlog/labels-question/probes/`. No human run was read; nothing of the exam fifth is used; no fork code changed. Line numbers
are as of Spireline 192a709 and HANDOFF.md at 11:06Z.

## For the owner

- Two yardsticks seemed to disagree about the human-taste helper in the player's card, rest and relic choices. The big test (2,000
  games against the old player) says it beats the second boss about 3 more times in 100 games. The what-if grades (go back to a
  choice, play each option out a few times, compare) said it was no better.
- Both were right about what they looked at. Today's probe let the helper choose only from the second act on: that alone wins the
  whole gain (about 3 more second-boss wins in 100 games) and loses nothing at the first boss. The helper's first-act choices cost a few first-boss wins and gain
  nothing later. The what-if grades had graded first-act choices only (1,437 of 1,449), so they saw the costly half.
- Like timing a relay team by its first runner only: the stopwatch was right that the first leg got slower; the race was won on the
  second leg, which nobody timed.
- So: a player that uses the helper from the second act on should be better than both (judged by a big test, not by the grades); the
  grades do not choose the helper's weight; the next grades go where the helper changes the game, in the second act.
- Thinking half as long at bosses (x8) is fine for the what-if grades (they are mostly noise, and x8 makes about 1.7 times as many an
  hour); the practice games that teach the run judgement, and the player we keep, stay at x16.

## 1. The disagreement, exactly

Both sides compare generation 11 (`vrun`, run head `f0a199fb`) with generation 12 = generation 11 whose deck screens (card, ancient,
rest) are decided by `V + 0.5 log pi_h` (`candidate-imit-l05`, prior `pi_h-v0` `2ebfe6d7`; routes and shops by V in both;
`agent/gen12/candidate-imit-l05/agent.json`).

| | the labels (the label leg) | the blocks |
|---|---|---|
| source | `referee/human-prior/label-leg-v0-v1win.json` (HANDOFF.md:555 item 6; DECISIONS.md:1351) | `agent/gen12/candidate-imit-l05/promotion.json` (E12-2026-11-05-r3; DECISIONS.md:1337; keep-test-v2.md:27-33) |
| what is measured | 674 graded card and rest decisions (447 card, 227 rest; 1,071 labels read) from generation 11's exploring runs; each option played K = 4 times on the copy by generation 11 (a3-v1, argmax); the blend's pick minus the judgement's pick on the same continuation seeds | 2,000 paired seeds, whole runs |
| horizon | the end of the decision's act, its boss included (`referee/hindsight/labels-2026-11-05/manifest.json:61`) | the run's end |
| unit | floors a decision: the death floor, or the frozen generation 11 head's expected final floor at the next act (manifest.json:5) | deep kills (Act 2 boss + first Act 3 boss + wins) per 100 runs (route A); floors a run (route F) |
| reading | blend -0.004 ± 0.062; prior alone (lambda inf) -0.149 ± 0.092 | deep **+3.05 (SE 0.63)**, B2 107 against 49 (+2.90, SE 0.58); floors **-0.31 (SE 0.20)**; Act 1 boss 965 against 1,043 (-3.90, SE 1.21) |
| all labels to date (1,449; 893 graded: 603 card, 290 rest; `probes/label-leg2-v0.json`) | blend -0.022 ± 0.053; prior alone -0.176 ± 0.081 | |
| real game (DECISIONS.md:1357) | | Act 2 boss 5.52 per 100 against generation 11's pool 3.42 (+2.10, one-sided 95% lower bound +1.12); floor -0.63 |

The brief's "K 2" is round 1's plan (big-step.md:55); the labels behind the reading are K 4 (manifest.json:38). Of the 1,449 labels,
**1,437 are Act 1 decisions** (card 594, rest 290, shop 375, route 178) and 12 are Act 2: the run's two labels (`per_run` 2,
manifest.json:49) fill with Act 1 decisions first, so the card/a2 quota of 250 got 9.

Per run (the performance-difference sum over the decisions a run makes, hindsight-sizing.md:45-48; generation 11's arm meets 6.89
Act 1 card screens and 3.07 Act 1 rest sites a run, counted from its `runs.jsonl`): the labels put the lambda 0.5 blend's Act 1 choices
at **-0.26 ± 0.54 floors a run** and -0.9 ± 4.6 Act 1 survivals per 100 runs.

## 2. Candidate mechanisms

What the prior changes (both arms' rows, `probes/block_split.py`): Act 1 card skips 16.0 → 7.8 in 100; Act 2 card skips 8.2 → 33.8;
Act 1 rest heals 43.0 → 34.5 in 100. The blend overrides V's top option on 30.7% of Act 1 card screens, 39.2% of Act 1 rests, 27.0% of
Act 1 ancients, 57.3% of Act 2 card screens, 42.8% of Act 2 rests and 34.8% of Act 2 ancients (1.91 Act 2 overrides a run). In Act 1 it
takes more draw, energy and block (per 2,000 runs, generation 12 against 11: Bloodletting 585 against 22, Pommel Strike 688 against
267, Battle Trance 211 against 6, Shrug It Off 154 against 1) and fewer cheap attacks (Anger 588 against 986, Twin Strike 483 against
824, Thunderclap 206 against 419).

| mechanism | for | against | verdict |
|---|---|---|---|
| **1. Selection: which decisions are labelled** | the labels graded Act 1 only (1,437 of 1,449); the probe (3.2) puts the whole frontier gain in the Act 2 decisions (+3.38 ± 0.62 per 100 runs) and a cost in the Act 1 ones (Act 1 boss -3.94 ± 1.05, floors -0.63 ± 0.19, deep -0.65 ± 0.76); the labels' Act 1 reading (-0.26 ± 0.54 floors a run) agrees with the block's Act 1 part; ancients are never labelled (0.46 overrides a run) | none | **holds: the main cause** |
| **2. Unit.** Floors weigh an Act 1 boss kill (13.5 floors, keep-test-v2.md:35) and an Act 2 boss kill (12.9) alike | the recorded comparison (DECISIONS.md:1351) set a floor figure a decision against a deep-kill figure a run; in floors the block also reads the prior as worse (-0.31; real game -0.63) | alone it does not explain why the labels saw no gain: in floors the Act 2 part gains too (+0.28 ± 0.09 a run) | **holds: why the comparison looked like a contradiction** |
| **3. Horizon and the head's bootstrap.** An Act 1 label ends at the Act 1 boss; past it the label is the frozen generation 11 head, the judgement under test | 91% of the centred variance of Act 1 option means is surviving the act, 3% the head (`probes/label_noise.out`); the head's value among survivors has sd 1.75 floors against a 12.2-floor survive/die gap; the head term of blend minus judgement is +0.010 ± 0.012 a decision | the probe finds nothing past the horizon for the Act 1 part to miss (deep -0.65 ± 0.76) | **a real limit of Act 1 labels; not the cause here** |
| **4. Compounding through the deck.** A label prices one prior pick on a judgement-built deck | lambda inf: labels -1.84 ± 0.83 floors a run against the pure-imitation smoke's -3.14 ± 0.68 (`agent/gen12/candidate-imit/promotion.json`, 200 seeds; its ancients and Act 2 picks are unlabelled too) | the Act 2 prior on judgement-built Act 1 decks wins more than the whole prior (+3.38 against +3.05): the prior's Act 1 deck adds nothing at the Act 2 boss | **not supported at lambda 0.5** |
| **5. Noise** | the labels' per-run SE is 0.54 floors, 2.7 times the block's 0.20 | the deep gain is z 4.9 and the real game agrees; the labels' interval contains the block's Act 1 part | **not the cause** |
| **6. The labels' K** | K 4 here; at K 2 a label's best option agrees with the other two draws' 35 in 100 against chance 25 | K changes precision, not sign | **not the cause** |
| **7. The continuation player** | round 1's labels play the player's own schedule; these played a3-v1 | both arms of this question used generation 11's fighter at a3-v1 | **not the cause here** |

## 3. The test that separates them

### 3.1 From the files

- **A. The block split** (`probes/block_split.py`, saved arms, seconds): the overrides above; the first override's floor per seed; a
  determinism check (31 seeds where generation 12 never overrode V have identical Act 1 records, final floors and boss kills in both
  arms; 23 seeds whose first override is in Act 2 have identical Act 1 records). The saved block cannot split the gain by act: 1,946 of
  2,000 seeds first diverge in Act 1.
- **B. The label decomposition** (`probes/label_leg2.py` on all 1,449 labels, the label leg's rebuild of each screen from the shards,
  77 s on one process): each option's mean return split into a survival term ((H0 - D0) × the share surviving the act; H0 28.09, D0
  15.87 for Act 1), the head's term and the death-depth term, on a lambda grid:

| lambda | blend ≠ V, card / rest | Act 1 card skips (V 11.1) | blend - V, floors a decision | survival of the act, per 100 decisions | head term | first-order floors a run |
|---|---|---|---|---|---|---|
| 0.25 | 19 / 23% | 4.4 | +0.013 ± 0.045 | +0.03 ± 0.38 | +0.004 ± 0.010 | +0.13 ± 0.45 |
| 0.5 | 29 / 36% | 2.5 | -0.022 ± 0.053 | -0.14 ± 0.46 | +0.010 ± 0.012 | -0.26 ± 0.54 |
| 1 | 40 / 45% | 1.3 | -0.073 ± 0.065 | -0.22 ± 0.54 | +0.004 ± 0.013 | -0.77 ± 0.66 |
| 2 | 47 / 50% | 0.8 | -0.143 ± 0.072 | -0.64 ± 0.59 | -0.010 ± 0.014 | -1.51 ± 0.73 |
| inf | 57 / 57% | 0.7 | -0.176 ± 0.081 | -0.70 ± 0.66 | -0.023 ± 0.016 | -1.84 ± 0.83 |

- **C. What a K 2 label can teach** (`probes/label_noise.py`): the pooled sd of a one-draw option difference is 5.80 floors; at K 2 a
  clear winner (best beats next by 2 paired SEs, round 1's `clear_winner` rule) occurs in 2.8 of 100 decisions (41 of 1,449; cards 12
  of 603), and the other two draws name the same best option 59 times in 100 (chance 34).

### 3.2 The probe: the prior from Act 2 on only (run)

`probes/act2_switch.py` and `run_probe.sh` (log `run_probe.log`, rows `act2only.jsonl`, read by `act2_read.py` into `act2_read.out`):
generation 12's agent with lambda 0 on floors 1 to 17 and 0.5 from floor 18 (the Act 2 ancient), on E12-2026-11-05-r3's seeds and run
indices, a3-v1, the CPU prior path, from a fork worktree at origin/main `20dc5b35` with the library the labels were made on. With lambda
0 the chooser is exactly `vrun`, so its Act 1 is generation 11's: on the 957 seeds where generation 11 lost the Act 1 boss the arm equals
generation 11 and only generation 11's 1,043 Act 1 boss winners need play; the first 925 of them in a fixed hash order were played
(the 50-minute deadline stopped the rest).

- **Exactness.** Generation 11's agent replays its saved rows exactly on 6 of 6 boss-winner seeds (whole runs); generation 12's on 5 of 6,
  the sixth equal in every deck decision and differing in an Act 2 fight (floor 25), a prior-path difference in one search, not the
  chooser. The arm's Act 1 equals generation 11's saved Act 1 on 924 of 925 seeds.
- **Result, against generation 11's saved arm on the same 925 seeds:** Act 2 boss 100 against 44; deep 107 against 47, **+6.49 per 100
  of these seeds (SE 1.20; discordant 78 / 24), +3.38 per 100 runs of the block (SE 0.62)**; floors +0.54 (SE 0.17) on these seeds, +0.28
  a run; Act 2 card skips 32.0 against 8.3 in 100; the blend overrode V on 2,731 of 4,830 Act 2 card screens, 810 of 1,843 rests, 361 of
  1,024 ancients.
- **The Act 1 part** (generation 12 minus the arm: the prior's Act 1 choices with their interaction): Act 1 boss **-3.94 per 100 runs
  (SE 1.05)**, floors **-0.63 (SE 0.19)**, deep -0.65 (SE 0.76).
- **Reading.** The human prior's frontier gain is all in its Act 2 decisions; its Act 1 decisions cost Act 1 boss kills and floors and
  build nothing the Act 2 boss rewards. The labels, which graded Act 1 only, read that Act 1 part correctly (-0.26 ± 0.54 floors a run
  against -0.63 ± 0.19; survival -0.9 ± 4.6 per 100 against -3.94 ± 1.05). Against generation 12 over the whole block (the Act 1 part
  with its sign turned) the arm is ahead on every measure: Act 1 boss +3.94 (SE 1.05), floors +0.63 (SE 0.19), deep +0.65 (SE 0.76).

### 3.3 What is left, with its cost

- **The act gate under generation 13's fighter** (x4 elites, x16 bosses): the Act 1 cost was measured at a3-v1; the stakes fighter
  may pay it less. One block, generation 13 with lambda 0 in Act 1 against generation 13: about 150 core-hours at 2,000 seeds (133.8 s a
  run, HANDOFF.md:547); *est.* Act 1 boss +2 to +4 per 100, floors +0.3 to +0.6 (SE 0.20), deep +0.4 to +0.7 from the extra Act 2
  entrants (generation 13 turns 18.6% of its Act 1 boss wins into deep kills, E14 x16 arm 205 of 1,104): a route F candidate, not route A.
  It needs the gate as a recipe part (the probe's 20-line wrapper as `macro_recipe` syntax, e.g. a per-act lambda) and the builder's tests.
- **Which Act 2 screen carries the gain** (cards, rests or ancients): three Act-2-only arms with the blend on one screen kind each, on the
  same 925 seeds, about 5 core-hours each at a3-v1, SE about 0.62 per 100 runs each. It tells the labels and the prior's refit where to
  look; cheap, not run (over this task's hour).
- **The 118 unplayed boss winners** of the arm: about 0.6 core-hours; would move the SE from 0.62 to about 0.59.
- **A frontier-unit label leg is not affordable as an arbiter.** Grading a chooser on deep kills a run to the block's SE (0.63 per 100)
  with K 2 continuations to the run's end on only the decisions where the two choosers differ (3.1 a run in Act 1 at lambda 0.5; a deep
  kill's probability about 0.04 a draw; option correlation 0.385 from `report.json`): about 5,700 such decisions, about 800 core-hours at
  the own schedule, against about 166 for a 2,000-seed block (*est.*). For Act 2 decisions alone (2.2 overrides a run, +0.015 deep per
  override, *est.* p 0.08 a draw): about 2,000 Act 2 labels, about 320 core-hours. In floors the first label run already cost about 14
  times a block for the same precision (1,449 decisions at 231 s, 93 core-hours, for SE 0.54 a run, against the two arms' 49 core-hours
  of `run_wall_s` for SE 0.20).

## 4. Round 1: the refit's weights and lambda (memo 3.4)

The labels may not arbitrate lambda or a weight that moves the frontier: the blocks do. Act 1 labels measure the right thing for Act 1
choices (surviving the act; the probe found nothing past the horizon), but at round 1's size (1,200 K 2 labels, a held-out fifth of 240)
the paired SE of a chooser comparison is about 0.15 floors a decision (1.58 floors a decision at K 4 on 893 decisions, × √2 for K 2,
/ √240), about ±3 floors a run at 95%: too weak to choose anything. Act 2 labels (their horizon includes the Act 2 boss) could see the
frontier but cost about 320 core-hours to arbitrate it. Names are the round 1 draft's (`rl/round1_data.py` DEFAULTS in `wt-round1`,
uncommitted at 11:20Z); the builder may rename.

| parameter | draft | recommended | why |
|---|---|---|---|
| `prior.lambda` | 0.5 | **0.5 from Act 2 on; 0 in Act 1 once the act gate's block (3.3) holds** (a new per-act parameter, e.g. `prior.lambda_by_act` [0, 0.5, 0.5]; until then 0.5 everywhere) | the probe: Act 2 decisions +3.38 deep, Act 1 decisions -3.94 Act 1 boss and -0.63 floors |
| `prior.lambda_rule` | fixed | **fixed** | the label rule would read Act 1 survival on 240 held-out decisions; it cannot see the Act 2 gain and has ±3 floors a run of noise |
| `prior.lambda_grid` | 0, 0.25, 0.5, 1 | keep, report only | |
| `prior.weights.human` | 1.0 | **1.0** | the human rows are the signal that bought the gain |
| `prior.weights.agent` | 0.5 | **0** | the blend's own choices carry no outcome; fitting pi_h to them moves it toward V's argmax, so the next blend counts V twice and dilutes the human Act 2 taste that beat V by 3.4 per 100; nothing measures that it helps |
| `prior.weights.label` | 1.0 | **0** (immaterial at 1.0) | at K 2 about 34 clear winners in 1,200 decisions, about 4 in 10 of them noise (3.1 C), nearly all Act 1; it cannot move a fit on about 150,000 human decisions; 0 keeps the round attributable |
| `prior.kl_beta` | 1.0 | **1.0** | keep the refit near pi_h-v0, the prior that gained |
| `prior.label_gap_se` | 2.0 | 2.0 | as drafted, if the label term is kept |
| `judgement.human_weights` | 0.25, 1, 4 | **0.25, 1, 4, chosen on held-out clears-Act-2 log-loss** (clears Act 1 not worse) | V's Act 2 deck choices lost 3.4 per 100 to the human prior's: the human rows' worth is in Acts 2 and 3; the labels' ranking leg is Act 1 survival; report it, do not choose on it |
| keep test (2) skip guard and (3) label bound (strategy-rethink.md:194-197) | gating | **report only** under route A | (3)'s lower bound -0.1 a decision refuses a truly level candidate about 83 times in 100 at 240 held-out K 2 decisions (SE 0.145); the Act 1 skip guard would have refused generation 12 (Act 1 skips 16.0 → 7.8) |
| `label.quota` | Act 2 cells 120 of 1,200 | **Act 2 cells at least half: card/a2 and rest/a2 first, and ancients as a label kind** | the gain is in Act 2 deck screens; the sizing memo's "Act 2 options are flat" (hindsight-sizing.md:115) was a floors reading of 12 to 13 pilot decisions |
| `label.per_run` | 2 | **2 per act** (or Act 2 cells drawn from Act 2 decisions) | the first run's cap gave Act 2 cells 12 labels of a 600-decision quota |
| `label.k` | 2 | 2 | the cheapest precision (hindsight-sizing.md:59) |
| `label.own_schedule` | true | true, **with bosses at x8** (continuations by `gen14/candidate-stakes-b8`'s schedule, section 5) | |
| `play.config` | own schedule | **own schedule (x16 bosses)** | the judgement's self-play rows stay matched to the kept player (section 5) |

Expected effect: with the agent and label terms at 0 the prior refit is pi_h on the larger 11-06 human file with the anchor, a small
change (the same population, 14,537 runs against 11,961; HANDOFF.md:555); the round's deck gain comes from the judgement refit with
human rows and, if it holds under the stakes fighter, the act gate (route F, *est.* +0.3 to +0.6 floors). Row C's +0.5 to +1.5 a round
(big-step.md:111) assumed labels that teach the prior; at K 2 and this mix they do not yet.

## 5. x8 for the practice and label stages

The x8 block (`gen14/candidate-stakes-b8` against generation 13, E14-2026-11-07, 2,000 paired seeds; DECISIONS.md:1361, HANDOFF.md:547):
Act 2 boss 8.5 against 9.3 per 100 (-0.80, SE 0.52); deep -1.05 (SE 0.59); floor -0.11 (SE 0.10); Act 1 boss 1,079 against 1,104 of
1,800 reached in both (60.0 against 61.3 in 100); Act 2 boss of reached 31.1 against 34.8; wall 81.8 against 133.8 s a run (0.61).

- **Labels at x8: yes.** A label is mostly noise (K 2: best-option agreement 35 against chance 25 in 100). What x8 changes is the
  continuation's boss: for an Act 1 label the survival term shifts by about 12.2 floors × 1.3 points × the share reaching the boss, about
  0.14 floors for every option alike; only the option-dependent part biases a label, a fraction of that, against a label's noise of 4.1
  floors (an option difference at K 2) and a true option spread of about 0.92 (hindsight-sizing.md:35-37). For an Act 2 label the boss
  is the frontier and x8 costs 3.7 points of it (of those reaching it), again mostly alike for every option. An Act 1 continuation is
  mostly its boss fight at x16 (66.5 s of about 75 *est.*; board A, `referee/backlog/scratch-board-a/summary.md`), so x8 makes it about
  0.6 of the cost: about 1.7 times the labels for the same core-hours, SE × 0.77. Round 1's 112 core-hours of labels (big-step.md:55)
  become about 67 (*est.*).
- **Practice games (the round's exploring play) at x8: not for round 1.** They are the judgement refit's rows: a V fit on x8 outcomes
  learns a player 1.3 points weaker at the Act 1 boss and 3.7 at the Act 2 boss (of those reaching it), about a tenth of the clears-Act-2
  rate, in the head the round is meant to fix; generation 12's recipe fits V on the candidate's own fighter for this reason
  (HANDOFF.md:592). The saving would be about 32 core-hours a round (83 × 0.39). Revisit when compute binds: on the PC alone rounds to
  11-19 go from about 9.5 to about 10.8 with x8 labels, to about 12 with x8 play too (3,535 core-hours over 372, 327 and 295 a round;
  big-step.md:72-79).
- **The fight gym's teacher at x8: no.** The trainer is row-limited (idle for fresh rows 499,545 s against 249 s of GPU training,
  `referee/gym-loop/trainer/status.json`), but more rows have not moved the student (top-1 0.747 to 0.748 at c0175-c0176; about 150
  checkpoints without a promotion, big-step.md:112, 115); x8 would cut the teacher's margin over the student at the Act 2 boss by about
  3.7 of the 9.7 points it holds (big-step.md:112). A gym A/B would decide it; not worth a slot now.
- **What would decide it by measurement:** for labels, the option-by-schedule interaction (A at x8 minus A at x16 across one decision's
  options, common seeds); its expected size is far below the noise, so a measurement needs thousands of decisions and is not worth
  running. For play, the clears-Act-2 calibration of a V fit on x8 rows when scored on x16 runs (one refit and a held-out read, about 5
  core-hours, once round 1's x16 runs exist).

## 6. Decision draft (for the orchestrator)

**D55 addendum 12 (2026-11-08, orchestrator, on `docs/design/2026-11-08-labels-vs-blocks.md`).** (1) The labels and the blocks do not
disagree: the labels graded generation 11's Act 1 decisions only (1,437 of 1,449) and read the blend there at -0.26 ± 0.54 floors a run;
a probe that lets the blend decide only from Act 2 on (925 of generation 11's Act 1 boss winners on E12-2026-11-05-r3) puts the whole
frontier gain in the Act 2 decisions (deep +3.38 per 100 runs, SE 0.62; floors +0.28) and a cost in the Act 1 ones (Act 1 boss -3.94,
SE 1.05; floors -0.63, SE 0.19). (2) Hindsight labels do not arbitrate lambda or any weight that moves the frontier; blocks do; the
label leg, the skip guard and keep test (3)'s label bound are report-only under route A. (3) A per-act lambda becomes a recipe part;
generation 13 with lambda 0 in Act 1 is judged on a block against generation 13 (route F expected) and, if it holds, round 1's
candidate carries it. (4) Round 1's config: `prior.lambda` 0.5 (`lambda_rule` fixed); `prior.weights` human 1.0, agent 0, label 0;
`kl_beta` 1.0; `judgement.human_weights` chosen on held-out clears-Act-2 log-loss; at least half the labels in Act 2 (card, rest, and
ancients as a kind), two a run per act. (5) Labels play their continuations with bosses at x8 (`gen14/candidate-stakes-b8`'s
schedule), about 1.7 times the labels per core-hour; the round's exploring play, the kept player and the gym's teacher stay at x16.

## Not verified

- The probe played at a3-v1 with generation 11's fighter; the act gate's value under generation 13's stakes fighter is an estimate
  until its block. The arm covers 925 of the 1,043 boss winners (the first in a fixed hash order, so no selection by run length).
- The probe ran on the CPU prior path against arms saved on the server path; generation 11 replayed exactly on 6 of 6 seeds and the
  arm's Act 1 on 924 of 925, so the comparison is near exact, but a rare fight can differ.
- The per-run label conversion is first order (the performance-difference sum on generation 11's states) and uses Act 1 decision counts
  from generation 11's arm; rest sites outside the label's six-option cut are not graded (pick-in-played 0.87 for rests).
- The head term uses act constants (H0, D0), not per-decision ones.
- x8's label cost (0.6) is an estimate from board A's per-fight seconds, not a timed label run; the interaction bound is an argument,
  not a measurement. The frontier-unit and Act 2 label costs assume deep-kill probabilities of 0.04 and 0.08 a draw.
- The round 1 parameter names are a builder's uncommitted draft read at 11:20Z.
