# Hindsight labels: what they are for, the first label run, and the run head's next signal (2026-11-05)

Opus design worker, written from 03:36Z (`date -u`), after the hindsight pilot (D53 item 2a) and generation 12's second refusal.
Read: `referee/hindsight/pilot-2026-11-05/` (report, labels, tasks, manifest), the fork's `rl/hindsight.py`, `rl/gen_loop.py` and
`rl/run_train/train.py`, attempt 2's `promotion.json` and `vrun_fit.json`, the train job record `LAB/runs/20261105T0306-train`,
and the run shards of three exploring jobs (297 runs, for decisions per run). Nothing was played. Every number is **measured**
(read from those files), **arithmetic** on measured parts, or marked **estimate**.

## Recommendation

1. **The labels are a training target first.** The same run supplies the grader in a narrow role: the fit's held-out check and a
   by-kind diagnostic. Not an exam figure beside the nightly and not a screen before the smoke block: reading a run chooser's
   floors as precisely as the smoke block does (SE 0.68 floors a run) takes about 160 core-hours of labels at attempt 2's
   disagreement rates; the smoke block takes 3.
2. **First label run: 2,400 decisions at K 4, three quarters in Act 1, cards and shops first** (section 2): 140 core-hours, no
   GPU, about 23 hours on 6 processes or 14 on 10, outside the night. Read it at 1,200 decisions.
3. **No beta trial.** The run head's next candidate is one blended fit: attempt 2's floor fit plus the labels' centred-value term
   (training design 2.5), with beta and the term's weight both chosen on held-out labels (no games), and one candidate to the
   smoke block. Beta can only pull a fit back toward the incumbent; it adds nothing about the options themselves.
4. **The pilot moves the plan in four places** (section 4): Act 2's share down, rests and routes down, a skip-rate guard in the
   ranking check, pooled noise in the fit's weights.

## 1. What a label's noise means for each use

| kind (decisions) | chance | head agrees | perfect head at K 8 | head's pick, floors over the average option | best option (estimate) |
|---|---|---|---|---|---|
| card (27) | 25% | 37% | 58% | +0.54 ± 0.38 | about 1.34 |
| shop (30) | 19% | 33% | 36% | +0.14 ± 0.19 | about 0.84 |
| rest (28) | 17% | 61% | 53% | +1.24 ± 0.33 | about 1.40 |
| route (25) | 46% | 76% | 77% | +0.71 ± 0.27 | about 0.86 |

Chance is one over the options played; the perfect head and the best option come from a normal model with each kind's measured
spread and noise; the head's pick value is unbiased (the head never sees the label's draws).

- **One label cannot rank its own options.** At K 8 a centred value is 37 to 44% signal (split-half reliability 0.37 after the
  Spearman-Brown step; the variance model 0.92² / (0.92² + 2.97²/8) gives 0.44); at K 4, 22 to 28%. The two 4-draw halves of one
  decision name the same best option 53% of the time (chance 26%). Choosing by a 4-draw label instead of by the head changes a
  decision's value by -0.03 ± 0.17 floors (pick on one half, score on the other): one decision at a time, the head is as good.
- **Where the room is:** cards (the head's pick +0.54 against about 1.34 for the best; agreement 21 points under its ceiling) and
  shops (+0.14 against about 0.84; agreement sits at its ceiling only because shop labels are noisy). Rests and routes leave
  about 0.15 floors a decision.
- **As a training target** the noise is averaged out by the fit across decisions and adds no bias: every option meets the same
  draws, and nothing is conditioned on the run's own luck. At K 4 an effect shared by m labelled decisions is resolved to about
  √(3.05/m) floors: 0.25 for a card offered in 50 labelled screens.
- **As a grader** the figure that matters is per run, and it is weak. A head's floor gain is the sum, over the decisions it makes,
  of the label value of its pick minus that of the incumbent's pick (the performance-difference identity, on the incumbent's
  states). A run makes about 24.5 multi-option decisions of these kinds in Acts 1 and 2 (card 8.85, route 8.63, rest 3.86, shop
  3.17). At attempt 2's disagreement with the incumbent (cards 40%, rests 45%, routes 6% on the ranking set; shops assumed 40%)
  the per-run SE is 1.7 floors from a held-out fifth of 2,400 decisions, 0.77 from all 2,400, and 0.68 only at about 160
  core-hours. Attempt 1 (-5.91) would show on a fifth (about 3.5 SE); attempt 2 (-1.29) would not. The 02:27Z reading "1,500
  labels grade a chooser to a twentieth of a floor" holds for one option class's mean value a decision, not for floors a run.
- Grade with paired differences (candidate's pick minus incumbent's) or a pick's centred value, never "best label minus pick":
  the best of several noisy values is biased upward.

## 2. The first run: K, size and mix

**K.** A decision costs 27.4 process-seconds of replay (3,010 s over the pilot's 110 decisions) plus 44.1 per draw of all its
options (4.56 options × 9.67 s). Variance × cost of a class's mean centred value, relative: K 1 690, K 2 607, K 3 605, K 4 622,
K 8 742 (for option differences 1,708, 1,507, 1,504, 1,551, 1,861). The best K is about 2.5 for both. **Spend on decisions, at
K 4:** 3% over the optimum, and it keeps two 2-draw halves for the reliability check and three degrees of freedom per decision;
K 8 costs 19% more than K 4 for the same precision. Noise over spread is the same in both acts (10.3 and 10.1), so one K serves.
The runner's `k_with_tau` (7.5) mixes the noise of an option difference with the spread of a centred value; consistent pairs give
K 3.0 (a class's mean centred value) and 13.9 (a mean difference of two options) for 0.05 floors over 1,500 decisions.

| cell | decisions | seconds each at K 4 | core-hours | SE of a class mean, floors |
|---|---|---|---|---|
| card/a1 | 750 | 214 | 44.7 | 0.08 |
| shop/a1 | 500 | 258 | 35.9 | 0.10 |
| rest/a1 | 300 | 230 | 19.1 | 0.13 |
| route/a1 | 250 | 124 | 8.6 | 0.14 |
| card/a2 | 250 | 208 | 14.5 | 0.06 |
| shop/a2 | 100 | 263 | 7.3 | 0.10 |
| route/a2 | 150 | 111 | 4.6 | 0.08 |
| rest/a2 | 100 | 194 | 5.4 | 0.10 |
| **total** | **2,400** | **210** | **140** | |

Why: every cell reads its own figures (the head's pick, skip, leave, heal) to about ±0.1 floor; cards and shops get most because
the head is furthest from the best option there; Act 1 gets three quarters (77% of a run's decisions, and an option spread of
1.17 floors against Act 2's 0.52); card/a2 keeps 250 to settle the skip question (humans skip 34% in Act 2, the AI 7%; skip's label
value is +0.10 ± 0.24 floors today, about ±0.06 in Act 2 after). Source: the 8,804 exploring runs of generation 11's fighter, two
decisions a run (about 1,200 runs; Act 2 cells need the 43% that reach Act 2), replayed on the build they were played with. A fifth
of the runs, by seed hash, is held out of both terms of the fit. **At 1,200 decisions (70 core-hours):** stop if the head's pick in
card/a1 and shop/a1 is within 0.2 floors of the estimated best option (nothing to teach); otherwise finish. A day-long run should
not hold a QUIET.lock line (it would stop the lab's filler for a day); the filler's slot is the place (the orchestrator's call).

## 3. Beta: no further trial

`bootstrap_targets` sets a row's target to (1 - beta) × the run's final floor + beta × the floor forecast the playing head stored
at the next decision. On exploring runs the playing head is the incumbent, so beta blends the incumbent's view into the fit: less
target noise, more of the lag the recipe removed (recipe doc, finding 1). It adds no information about the options. The exploring
runs do try other options (19% of multi-option decisions in Acts 1 and 2; card rewards 21% in Act 1, 44% in Act 2), but mostly
where the head already sees a near tie, and each such try is scored by one run's final floor and that run's luck, while a label
scores every option on the same draws.

Attempt 2's signature is option ranking, not target noise. On the ranking set it skips 6.6% of card rewards against the
incumbent's 16.9% (SE 0.7 points; heal +5.6 points; elites 2.9% against 1.3%). In the smoke block it reached the Act 1 boss as
often (181 against 179) and killed it less (96 against 107), taking 8.46 cards a run against 8.02 (skip 6.3% against 14.2%). That
the loss comes from card taste is an inference. Beta moves such a fit part way back toward the incumbent, so its expected place is
between attempt 2 and the incumbent, and the funnel cannot tell "about equal" from a small gain without the full block.

Cost, from the records (the brief's figures are off): the fit 23 min wall and 41 CPU-minutes on four threads (`device: cpu`), so
0.7 core-hours and no GPU; the ranking check 14 min (841 s); the smoke block 11.4 min on 16 processes, 3.0 core-hours (683 s wall,
2.3 CPU-hours). 1.7 hours is the order of the full 2,000-seed block (about 30 core-hours), paid only after a smoke pass. A beta
trial costs about 4 core-hours to its smoke verdict, so cost is not the reason. The reasons: its best case is the incumbent; D47's
two attempts are spent and the guard refuses a third generation 12 candidate before a seed, a cap worth keeping for a knob that
brings no new information; inside the blended fit beta is chosen on held-out labels for free.

**Recommendation: the blend.** The floor term on attempt 2's window keeps the level matched to generation 11's fighter (its keep
test passed, Brier skill 0.18); the labels' centred-value term sets the option ranking; beta in {0, 0.3} and the term's weight on
a three-point grid are chosen on the held-out fifth; one candidate goes to the ranking check and the smoke block. Whether it counts
as generation 12's third attempt or opens a new line is the orchestrator's call.

## 4. What the tables change

- **Act 2 cards and shops are flat under this fighter:** true spread 0.30 and 0.20 floors, reliability at K 8 0.15 and 0.10
  (0.37 overall); 96.5% of Act 2 continuations die before the act ends (Act 1: 45%). The training design's 40% share for Act 2
  card rewards (2.4, human labels) drops to about 10%: the Act 2 lever is the fighter at the boss, not the run head's card taste.
  Route/a2 and rest/a2 kept signal (0.91 and 0.60, on 12 and 13 decisions).
- **Shops' low agreement is mostly label noise** (33% against a 36% ceiling), but the head's shop picks are worth little, so shops
  stay second in the mix. **Cards are the real gap.** **Rests:** the head beats a 4-draw label pick by 0.39 ± 0.22 floors; rest
  labels are a check (heal rate, attempt 1's failure), not a teacher. **Routes** are at the ceiling.
- The head squeezes option differences: its centred values spread 0.48 floors against the labels' true 0.92 (Act 2: 0.29 against
  0.52), the recipe doc's "near ties" seen from outside.
- Rest and shop screens are cut to six options (9.3 and 12.5 exist on average; 27 of 28 and 25 of 30 pilot decisions were cut): a
  candidate's pick outside the six cannot be graded, so the held-out leg reports its coverage.
- The ranking check measures skip rate but does not gate on it; attempt 2's 10-point fall (about 15 SE) passed. Add a guard: a fall
  of more than 5 points against the incumbent fails unless the held-out label leg says the candidate's card picks are worth more.
- In the fit's weights w_d, use each cell's pooled noise, not the decision's own 3-degree-of-freedom estimate (±82% scatter; noisy
  weights favour decisions whose draws happened to agree).
- Pace: a continuation 9.67 s (the design estimated 14), a K 4 decision about 210 s (design 190).

## Costs and order of steps

| step | what | core-hours | GPU-min | wall |
|---|---|---|---|---|
| 0 | orchestrator: record "no beta trial" and how the blended head is counted; place the label run | 0 | 0 | |
| 1 | the label run, read at 1,200 decisions | 140 (70 at the read) | 0 | 23 h on 6, 14 h on 10 |
| 2 | build training design 2c on these labels, with the beta knob, the skip guard and pooled weights (Sonnet) | small | 0 | |
| 3 | six fits (3 weights × 2 betas), the held-out leg, one ranking check | 4.4 | 0 on record | about 2.5 h on 4 threads |
| 4 | the smoke block, then the funnel's looks if it passes | 3.0 (up to about 30) | 0 | 11 min (up to about 2 h) |
| 5 | human labels (2b) with this memo's mix, only if step 4 shows the term helps | | | |

About 150 core-hours to a smoke verdict, about 175 if the candidate runs the full block. No GPU work on record (the attempt 2
fit's record says `device: cpu`; the pilot's continuations used 8.24 CPU-seconds of their 9.67).

**Not verified:** the per-run grader figures use attempt 2's disagreement rates on the generation 9 ranking set and assume shops at
40%; the best-option values use a normal model on spreads from 25 to 30 decisions a kind (cells 12 to 16); core-hours are measured
at 6 processes and may rise at 10 to 16 (8 physical cores); that a label's ordinal equals its source shard's decision index (needed
to grade a new head from stored states) is untested; the card-taste reading of attempt 2 is an inference; a new fighter promoted
before step 4 would leave the labels belonging to the old one (design 2.3).
