# How a fight-brain promotion should reach the champion (judge-design lane, 2026-11-22 01:58Z)

This memo uses only file reads and arithmetic; no games were played. Terms:
- **deep_f**: runs per 100 that get past the first Act 3 boss (a win counts). It is the run judge's measure.
- **pair**: the candidate and the champion playing the same seed.
- **route A**: keep rule v3's only route to promotion: a gain of at least +0.5, with the one-sided 0.005 lower bound above 0.
- **fight-only swap**: the champion with only its fight network replaced, as the wiring builds it.

"±" is one standard error (SE) unless marked 2 SE.

## Recommendation

Keep route A for every candidate. For fight-only swaps, add **route S**, which judges the fight brain where it acts, on the stop rule's own measure. It has two parts:

- **S1, the arrival exam.** The candidate's fight network plays against the champion's from the champion's own positions on arriving at the first Act 3 boss. There are 1,127 such positions, rebuilt from the champion's judged base arms, which the trainer never read. Each is played with 6 fresh paired draws. S1 holds when the gain is at least +1.0 passes per 100 arrivals and its 0.005 lower bound is above 0. Its SE is about 0.4. One point per arrival is worth 0.22 per 100 runs.
- **S2, the breakage check.** Play 2,000 whole-run pairs. deep_f must not be down at a one-sided 95% bound (99% at the interim looks). v3's collapse, crash and wins guards still apply.

A candidate is promoted when both S1 and S2 hold.

| | no gain | true +0.5 at the boss | true +1.0 at the boss |
|---|---|---|---|
| route S | 0.5 in 100 | 98 | 99.8 |
| v3 today | 0.9 in 100 | 9.5 | 42 |

Small steps add up by themselves, because S1 always compares against the champion's fight network. A candidate costs 1.7 h when S1 refuses it and 3.8 to 5.9 h when it is promoted; under v3 each costs 4.2 to 6.6 h. Route S can promote without a whole-run Act 3 gain, so it is **a D66 change and needs the owner's approval**. It also reverses D68 addendum 5 decision 6.

## 1. Why route A cannot see a fight step

**The judge's noise.** The deep_f difference within one pair has a spread of 27 per 100 runs (26.2, 27.2 and 28.9 on the three stored blocks). The SE is therefore 0.60 at 2,000 pairs and 0.42 at 4,000. To see a gain 80 times in 100 at the 0.005 bound takes:
- 34,000 pairs (72 h) for +0.5;
- 8,500 pairs (18 h) for +1.0;
- 2,100 pairs for +2.0.

**Fight points earned in Acts 1-2 do not show up in deep_f.**
- v3→v4 was +1.94 ± 0.63 fight points and read +0.48 ± 0.42.
- v3→v5 was about +3.0 ± 0.8 points and read -1.27 ± 0.87. That run was halted early by the futility stop, which biases it low.
- Fitted together, that is 0.00 ± 0.17 deep_f per 100 runs per fight point.
- Floors do respond: +0.27 ± 0.08 a run per point.

So no threshold on the gate's Acts 1-2 score can be justified from data. Option (a)'s threshold has to be measured at Act 3, and that measurement is S1.

**What v5's loss is made of.** deep_f is arrivals times the pass rate per arrival. The champion's fresh 5,100 runs arrive 22.1 times per 100 runs and pass 25.0 times per 100 arrivals. Against that, v5:
- reached the boss more often: +2.1 ± 1.3 per 100 runs;
- passed it less often: 22.1 ± 2.6 against 29.2 ± 2.9 per 100 arrivals.

Whole runs cannot tell a worse fight from worse arrivals; S1 can.

**What limits the 12-02 mark.** The gym's measured Act 3 step is +0.6 ± 0.8 per 100 arrivals (0.0 ± 1.0 on the gate's starts from our own arrivals). The mark needs +5.5 in the real game, about +7 on the copy. The size of the Act 3 step limits the mark, not the judge.

## 2. The options compared (`judge_power.py`, `judge_power_s.py`)

Each cell gives how many of 100 candidates are promoted at a given true deep_f gain per 100 runs. Method:
- Normal approximation, with the rule's SEs taken as known.
- 200,000 simulated candidates per cell, so each figure is ±0.2.
- Measured inputs: per-pair spread 27, arrivals spread 44, correlation 0.29.
- S1's SE taken as 0.45, which is conservative.
- Hours on 16 processes: 1,000 pairs take 2.1 h; one Act 3 fight costs 5.3 process-seconds.

| design | 0 | +0.5 | +1.0 | +2.0 | true -1.0 | hours |
|---|---|---|---|---|---|---|
| v3 as in force | 0.9 | 9.5 | 42 | 98 | 0.0 | 4.2-6.6 |
| (a) S1 filters, then v3 | 0.0 | 9 | 42 | 98 | 0.0 | 1.7 + v3's |
| (b) a second extension | 1.1 | 14 | 59 | 99 | 0.0 | 4.6-8.0 |
| (c) no-harm check only | 94 | 99 | 100 | 100 | 47 | 4.1 |
| **S, gain at the boss** | **0.5** | **98** | **99.8** | **100** | 0 at the boss; 47 through arrivals | 1.7 + 2.1-4.2 |
| S, gain from Acts 1-2 | 0.5 | 0.5 | 0.5 | 0.5 | 0.0 | 1.7 (route A by hand) |

**(b)** Extending from +0.5 is already in force: `--min-gain 0.5` sets it, and v4 was extended at +0.70. A third block of seeds brings the SE to 0.35 at 6,000 pairs. Pooling v4 and v5 (5,100 pairs) reads +0.10 ± 0.38, but it mixes two brains and so tests neither.

**(c)** At 1,100 pairs, v5's -1.27 ± 0.87 would have played on (z -1.46). At 2,000 pairs a true -1.27 is refused 70 times in 100. The owner's worry is a step that gains in Acts 1-2 at Act 3's cost: +2 points in Acts 1-2 and -4 per arrival at Act 3, about -0.5 deep_f.
- (c) passes such a step 76 times in 100.
- The gym's own guard lets 11 in 100 through, so about 8 in 100 would reach the champion.
- S1 refuses all of them.

**(d) is S.** S1 does not see two things:
- arrivals that change with the fight brain: potions spent earlier, HP at the door, weaker runs now reaching Act 3;
- Act 3's ordinary and elite fights, where 12.6 real runs in 100 die.

Only S2 sees these. A whole-run loss of that kind passes S2 77 times in 100 at -0.5, 47 at -1.0 and 4.5 at -2.0. This is the one risk S adds, and it falls on the stop rule's copy half, which reads +2.6 ± 0.44 against +2.0 needed.

**(e) Later, for every candidate.** Replay each judged run's first-Act-3-boss arrival 8 times from its saved position and score the run by the mean. That adds about 15% to run time. The pair variance is projected to fall from 0.071 to 0.038, so route A would need about half the pairs. It needs a change to the arm runner; not this week.

**Per week**, at about one gym promotion a day:
- v3: 30-45 h, with the fight loop paused throughout.
- S: about 12 h of S1, plus 2-8 h of S2 for each step that holds, plus 1.8 h for each new champion's ruler.

## 3. The rule change

Route S applies when `agent.json` reads `built.swap: fight` and nothing else changed. Its ledger route is `S`, or `AS` when route A also holds.

**S1's ruler** (the set of positions S1 plays):
- The champion's first-Act-3-boss arrivals in its base arms, from blocks it was not selected on. For generation 20 those are E21, E21-r1 and E21-r2: 437 + 450 + 240 = 1,127.
- Rebuilt to the boss door by the gym's replay step, keeping only replays that match their row.
- Second-boss arrivals are played for the record.
- Every run used is excluded from practice.
- Rebuilt for each champion, about 1.8 h.
- Not taken from the gen-20 plain-run store, because the trainer reads that store.

**S1's play:**
- Config `a3-v1` on the CPU prior, 6 draws per start; test k uses draws 6k to 6k+5.
- The statistic is the per-start mean of the survival difference (candidate minus champion), averaged unweighted over the arrivals, with the SE taken over starts.
- S1 holds when the mean is at least +1.0 and the mean minus 2.576 SE is above 0.
- A 95% upper bound below 0 counts as a reversal for the gate.
- Cost: about 13,500 fights, 1.7 h on 12 processes. It runs as the first stage of the lab's train job, so the gym daemon is not touched.

**S2:**
- The D51 looks over 2,000 pairs.
- From 500 pairs on, a look refuses when deep_f's 99% upper bound is below 0 or the floors collapse.
- At the end it refuses when the 95% upper bound is below 0, and otherwise promotes if the crash and wins guards hold.
- No futility stop on route A's gain, no early promotion and no extension.
- It may reuse the champion's stored arm on a block the candidate never played, after 20 of its seeds replay identically. That cuts the time from 4.2 h to 2.1 h.

**Order of work and files:**
1. **Margins, no rule change:** `tools/lab/keep_v2.py` (`margins`, `summary`), `rl/gym_gate.py` (`strat_read`: margins and the boss-cell flag), `rl/gym_loop.py`; tests `test_keep_v3.py`, `test_gym_gate_v5.py`.
2. **Ruler and exam, run as a measurement only:** `rl/act3_starts.py`, `rl/gym_gate.py` (`arrival_exam`); new test `test_arrival_exam.py`.
3. **S1 on v5**, run by hand.
4. **The owner's decision.**
5. **Route S itself:** `keep_v2.py` (`route_s`, `judge_v3(s1=)`, `seq_call_v3(route_s=True)`, `ledger_cells`), `rl/gen_loop.py` (the funnel under S, base-arm reuse), `rl/gen0.py` (`--route-s auto|off`), `docs/rl/KEEP_TEST_V3.md`.
   - New test `test_keep_v3_route_s.py` covers: no S1 means v3 unchanged; S1 and S2 holding promotes by S; a failed S2 bound refuses; collapse, crash and wins still block; the harm stop at a look; the base-arm identity check.
   - Additions to `test_funnel.py` and `test_gym_wiring.py`.
   - Landing needs the Python-only gate.
6. **The orchestrator** adds `--route-s auto` to the train job in `jobs.json`.

## 4. What the verdict and the ledger print (D68 addendum 6 decision 1, judge half)

**`promotion.json`** gains these fields:
- `keep_v2.margins`: for B1, B2, B3a, wins, deep_f, floors and arrivals, the counts, the paired difference per 100 runs, its SE and ±2 SE, and the discordant pairs;
- `per_arrival`: each arm's rate per 100 arrivals with its SE;
- `s1`: the reading with its SE, starts, draws and the ruler's hash;
- `state_shift`: the whole-run per-arrival difference minus S1's, with its SE.

**The ledger** shows ±2 SE beside every figure. v5's line would read:

`deep -1.27 ±1.74 | B3a 58/70 -1.09 ±1.69 | wins 1/3 -0.18 ±0.26 | arrivals 263/240 +2.09 ±2.66 | per arrival 22.1/29.2 -7.1 ±7.8 | B1 +2.82 ±2.81 | B2 +2.27 ±3.08 | floor +0.90 ±0.74`

**The gate's verdict** shows ±2 SE for each cell and flags any boss cell at -3 or worse in the stage line. Nothing would be flagged for c0390. Two cells would be for c0384: the first Act 3 boss at -4.0 ±3.7 and the second at -3.8 ±5.2.

## 5. The first candidate: gen21/candidate-fight-v5

**S1:** v5 against v3 on the 1,127 arrivals. Building the ruler takes 1.8 h and playing it takes 1.7 h.

**S2, if S1 holds:**
- Reuse the 1,100 E21-r2 pairs. They come from the same pre-registered block, and the early stop biases them toward refusal, never toward promotion.
- Add 2,000 candidate runs on E21-r1 against the champion's stored arm: 3,100 pairs in total, SE 0.49, 2.1 h.
- Pass rates: a true 0 passes 82 times in 100, a true -1.27 12, a true +0.5 96.
- Alternatively, completing E21-r2 to 2,000 pairs takes 1.9 h and passes 81, 30 and 93.

**Other points:**
- The r2 pairs cannot serve S1, because their rows hold no fight positions.
- If S1 reads v5 as worse at the boss, gate v5's reversal tally reaches 2 of 2 and the gate is reviewed.
- Steps 1-3 need no owner decision.

**Not verified:**
- that the judge's arms load into the gym's replay step;
- S1's SE, which is projected from the gate's paired Act 3 games, where 4 to 16 draws in 100 disagree. Its false-promote rate is fixed by the bound; only its power depends on the SE.

**To repeat:** run `D:/spireline/venv-gpu/Scripts/python.exe -I judge_power.py` in this folder; then `judge_power_s.py`, `judge_facts.py` and `a3_spread.py` the same way.
