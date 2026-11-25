# Analyst A: the learning system (2026-11-19)

Paths are under `D:/spireline/`; `scripts/` is `referee/backlog/analysis-2026-11-18/scripts/` (my read-only scripts, the source of every figure not quoted from a file). "Copy": our re-implementation of the game. "Champion": the current best AI; a "generation" is a promoted champion. "Run brain": the network that scores positions by the floor a run should reach; "fight brain": the one that plays fights; "judge": the promotion test on "pairs" (one seed played by both AIs). At Ascension 10 Act 3 ends with two bosses back to back, the "first" and "second Act 3 boss". Human figures: Spire Codex public run export for v0.107.1, the four training fifths of Ironclad A10 (14,725 runs), aggregates only.

**Short answer.** As built, this loop will not reach the best humans and shows no sign of reaching even the average human: it wins 1 run in 1,000, its win rate has not moved since 11-05, its learning target counts a win as worth four floors, and about nine tenths of the gap to the average human sits in the two Act 3 boss fights, which no part of the loop is aimed at and which the judge (it turns out) over-counts threefold. Whether a loop re-aimed at those two fights could close the gap is untested; the tests that would tell take about a week.

## What went right

**1. The loop produced lasting gains, and the copy matched the real game wherever it was checked (to generation 13).** The champion went from 11.5 to 30.3 floors on the copy in 26 days. Per promotion (paired floors gain, with pairs; boss kills per 100 runs, candidate against base on the same seeds; real floors where a real block ran):

| Gen | Date | What changed | Floors gain (pairs) | Boss kills per 100, cand vs base | Real / copy floors |
|---|---|---|---|---|---|
| 1-3 | 10-23/24 | fight brain learns from its own searches | +0.41, +0.31, +0.29 (2,000 each) | Act 1: 2.0/1.4 → 3.5/2.4 | gen 3: 12.7 / 12.8 |
| 5 | 10-25 | run brain chooses routes, cards, rests | **+5.00** (2,000) | Act 1: 13.5 vs 3.4 | 18.4 / 17.7 (same seeds) |
| 6-9 | 10-26/29 | both brains refit on own runs | +1.72, +0.75, +2.04, +1.04 | Act 1: 27 → 46 | gen 7: 19.1 / 19.3; gen 9: 22.1-23.1 / 22.4 |
| 11 | 11-02 | fight brain from the fight gym (v2) | +1.07 (2,000) | Act 1: 51.3 vs 43.1 | 23.5 (3,479 runs) / 23.1 |
| 12 | 11-05 | human prior blended into run choices | -0.31 (2,000) | Act 2: 5.4 vs 2.5 | |
| 13 | 11-05 | 4x search at elites, 16x at bosses | +1.85 (500) | Act 2: 9.2 vs 5.8 | 24.2, Act 2 boss 7.8 / 24.5, 9.3 |
| 14-15 | 11-12/13 | "student" network copies a slower search | +0.87, +0.98 (1,400 each) | Act 2: 10.9 vs 9.3; 11.0 vs 8.9 | |
| 16 | 11-14 | run brain refit on gen 15's 13,142 runs | +0.88 (1,700) | Act 2: 14.3 vs 10.7 | |
| 17 | 11-15 | run brain refit on gens 15+16 (26,564 runs) | +1.83 (800) | Act 2: 21.8 vs 16.4 | |
| 18 | 11-18 | fight gym's v3 in the run player | +0.70 (2,000) | Act 1: 76.5 vs 72.8; Act 2: 24.5 vs 23.6 | |

[referee/agent/promotions.tsv; each candidate's agent.json and arms/*/runs.jsonl; scripts/A-gens.py; real figures from spireline/docs/paper/spireline-paper.html "Every generation", "Humans against the AI" and the scoreboard]

By mechanism, of the 19.4 floors of promoted gains: the run brain switched on (gen 5) 5.0; refits on own runs (gens 1-3 the fight brain, 6-9 both brains) 6.6; the run brain's two catch-up refits (16-17) 2.7; the gym's fight brains (11, 18) 1.8; more boss search (13) 1.9, at about three times the run cost (149 against 42 wall-seconds a run on its block); the student (14-15) 1.9; the human prior (12) -0.3 floors but Act 2 boss kills doubled. The gains held: they sum to 19.4 against a measured change of 18.8, and each champion's level on later blocks stayed within 0.8 floors of its promotion block [scripts/A-gens.py, A-drift.py]. Copy and real agreed within 0.7 floors for every generation checked (0.4 or less from generation 7 to 13). The brief's "24.2 real against 29.7 copy" compares generation 13's real block with generation 17's copy runs; it is not a measured copy-real gap.

**2. On Acts 1 and 2 the copy's champion now matches or beats the average human.** Generation 18 kills the Act 1 boss 76.5 in 100 (n=2,000) against the humans' 54.9 (n=14,725), the Act 2 boss 24.5 against 28.7 [scripts/A-drift.py, A-human.py]. The data step plays the champion faithfully: generation 17's plain runs kill these bosses 73.3 and 22.8 in 100, its judged runs 73.4 and 22.9 [scripts/A-act3.py].

## What went wrong

**1. The judge's Act 3 boss figure is about three times too high.** The judge reads a boss as killed when the record says its health bar was emptied [fork tools/lab/keep_v2.py `bosses_beaten`]. That agrees exactly with "the run went past the boss" in Acts 1 and 2, but at the first Act 3 boss two runs in three that "empty" it still die on that floor (perhaps a boss with more than one life; not verified). Generation 18: read 7.9, actually past it 2.6 in 100 (n=2,000); generation 17: 7.0 against 2.3 (n=9,299) [scripts/A-killread.py]. The plain runs' explicit flag agrees with the second reading: 2.29 in 100 beat the first Act 3 boss, exactly the runs that reach the second (n=52,824) [scripts/A-variety.py]. Re-read honestly, the refused refit `cheap-v3d` beat the first Act 3 boss 132 times against 96 over its 4,000 pairs, +0.90 in 100 (95% interval +0.23 to +1.57), and the refused round-3 fit 66 against 44 on 2,000, +1.10 [+0.12, +2.08]; generation 18's promotion is level, 52 against 47 [scripts/A-true3.py]. The owner's D66 rule now decides on this misread figure.

**2. Where the gap really is: the two Act 3 boss fights.** Wins per 100 decompose stage by stage:

| Stage | Ours (gen 17 plain runs, n=52,824) | Humans (n=14,725) |
|---|---|---|
| Kill the Act 2 boss | 22.8 in 100 runs | 28.7 |
| Of those, reach the first Act 3 boss | 65 in 100 | 87 |
| Kill it, per door | 15.5 in 100 (n=7,797) | 71 (n=3,667) |
| Then win (second boss) | 4.5 in 100 (n=1,208) | 62 (n=2,606) |
| Wins | 0.10 in 100 | 10.9 |

[scripts/A-variety.py, A-human.py, A-bosses.py]. Over the last two rows our rate is 0.016 of the humans', over the first two 0.59, so about nine tenths of the gap (on a log scale) is in those two fights. Humans kill each of the three first-Act-3 bosses about equally (70, 71, 73 in 100, cells over 1,190); ours kills them 22, 18 and 1.5 in 100 (n=159, 131, 137 fights in a 2,935-run sample). Both sides enter at about the same health (ours 0.83 of maximum, humans 0.86); when ours wins it loses 0.58 to 0.66 of its maximum health (n=35 and 24), humans 0.32, so it meets the second boss at 0.31 (humans 0.54) and almost always dies [scripts/A-bosses.py, A-variety.py].

**3. No part of the learning system aims at Act 3 or the win.**
- The run brain learns to predict the final floor; a won run counts as floor 53, death at the second Act 3 boss 49, at the first 48 [fork rl/run_train/models.py, evaluate.py]. So a win is worth 4 floors over losing the last fight, and the first Act 3 boss 1 floor. On our numbers, playing both Act 3 fights as well as the average human (wins 0.1 → about 6.5 in 100) is worth about +0.34 floors a run to the brain, as much as two more Act 1 boss kills in 100 (each worth about 18 floors). The floor rules of the judge (v1, v2) shared this blindness; D66 changed the judge, not what the brain learns.
- The fight brain's exam (65 against the humans' 80 in 100) holds Act 1 and 2 fights only: 185 Act 1 bosses, 91 Act 2 bosses, the rest elites and hallways [referee/gym-loop/exam/human-meta.json]. The 24,393 human Act 3 positions were never built into practice starts [fork docs/rl/HUMAN_STARTS.md, "act 3 or later: not built"]. Since 11-17 the fight trainer also reads the boss fights of plain runs, so Act 3 bosses reach it only as the 15 in 100 runs that get there. On the humans' own positions it trails at bosses, by 9 points in Act 1 and 28 in Act 2, while hallways and elites are level [referee/backlog/human-bar/diagnosis.md; practice player, regret-drawn starts].
- The boss-door judge forecasts 7 deaths in 100 at Act 3 doors where 86 die, worse than a constant [referee/run-cheap/17/calibration.json].
- Data at the goal is thin: of the 52,824 plain runs, 1,208 beat the first Act 3 boss and 54 won; the win is learned from 54 examples.

**4. The own-runs signal: exhausted for Acts 1 and 2 under this target, not at Act 3.** The run brain was not refit from generation 9 (fit on generations 6 to 8, 10,014 runs) to generation 15: the same network, f0a199fb, while the fight brain, the prior, the boss search and the student all changed [referee/agent/gen9..gen15 promoted candidates' agent.json, `vrun_fit`]. On this evidence the refits of generations 16 and 17 caught up a stale brain, a one-time harvest. After that, 3.5 times more of the champion's own runs (12,980 → 45,986) improved held-out prediction by 1.7 in 100 (log-loss 2.180 → 2.142) [referee/run-cheap/17/fits/*/vrun_fit.json], and fits on the champion's own runs alone made it die earlier (13,000 runs: -2.79 floors; 46,000: -1.95 and -2.16; the Act 1 boss 61 to 63 against 73 to 75 in 100), as the orchestrator found, by learning to heal less (heal rate 0.43 against 0.55) [DECISIONS D63 addendum 2, D65 addendum 1]; the window pooled over three champions did not collapse (+0.55, level). But the larger windows did learn something about Act 3, where data is scarce: the honest Act 3 gains in item 1 come from exactly these refused fits. The judge refused them on floors.

**5. Variety: the roads vary; the choices never do.** One figure: in a sample of 2,935 plain runs (every 18th record), all 149,944 real choices were played greedily, with probability 1 (no randomness in the data step), although the brain rated the runner-up within half a floor of the best in 58 in 100 of them and within a quarter floor in 39 [scripts/A-variety.py]. The brain only ever sees the result of the option it takes. Measured against the humans at the same depth:
- Routes are as varied as the humans': two random runs share their first six Act 1 rooms 0.65 in 100 of the time (humans 0.81); 5,133 distinct first-ten-room sequences in 11,011 runs (humans 6,022 in 12,580). "The same roads every run" is not literally true; the maps differ by seed.
- Card picks repeat about as rarely (two runs share their first three picks 0.01 in 100, humans 0.02), and positions are almost all new: by the fourth card reward 2 in 100 of decks occur in another sampled run, by the sixth none.
- What is narrow is the style: 0.51 elites in Act 1 (humans 1.79); two or more Act 1 elites in 6 runs in 100 (humans 60); card skips 18.6 in 100 screens (humans 32.4); the ten most-taken cards are 44.6 in 100 of picks (humans 31.6); 32 cards make up 80 in 100 of picks (humans 47). So the brain never sees decks or roads built the humans' way and cannot learn whether they win. (A forced-elite probe on 200 pairs hurt Act 1, D60 addendum 4, so the narrow style may suit this fight brain.)

**6. Wins have not moved in two weeks, and the fight loop is stuck.** Wins per 100 on the copy: 0.04 (gen 12, n=2,500), 0.12 (gen 16, n=2,500), 0.06 (gen 17, n=9,300), 0.10 (gen 18, n=2,000) [scripts/A-drift.py]. The first Act 3 boss, honestly read, went 0.23 (gen 13) → 1.5 (16) → 2.3 (17) → 2.6 (18) in 100, mostly by more runs arriving there. The fight loop judged 49 students since 11-09 with no promotion [paper, Tuesday review].

**7. Promotions were tried until one passed.** Seven of 16 promotions followed a refusal in the same generation (gens 3, 7, 12, 14, 15, 16, 18; gen 18 after five), five were early stops at 500 to 1,700 pairs, and two passed only on the timing of a rule change (gen 12 under v2 hours after v1 refused it; gen 18 under v2 two minutes before v3, which refuses it) [promotions.tsv]. Because levels held on later blocks, this inflated single verdicts more than the trend.

## What the evidence cannot tell us

- **Whether the Act 3 wall is real or the copy's.** No real block has measured Act 3 at scale (the last, gen 13 on 11-06, reached it in a few runs in 100). The odd kill reading, and one boss beaten 1.5 in 100 against the humans' 71, are also what a copy fault would look like.
- **How the Act 3 loss splits between deck and play.** No exam plays our fight brain on human Act 3 positions.
- **What more search buys at Act 3 bosses.** A run costs about 52 CPU-seconds, 73 in 100 of it in boss fights [DECISIONS D63 addendum 2]; boss search paid in Acts 1 and 2 (gen 13); Act 3 is unmeasured.
- **Whether a target that counts the win can learn from 54 wins**, or needs per-boss survival steps chained together.
- **Whether exploration helps.** Never tried; the pooled window not collapsing is weak indirect evidence.
- **The best humans' number.** The export has no player key on solo runs [fork rl/strong_sets.py], and almost no runs above A10 (17). Published estimates: "a 60+% win-rate at A10" for high-level players (an unsourced blog, https://buttondown.com/bayjinger/archive/slay-the-spire-2/); about 95 in 100 for the top player, from a 53-win A10 streak (Epoch AI, 2026-10-14, https://epoch.ai/publications/ai-systems-are-improving-rapidly-at-slay-the-spire-and-its-sequel). So the goal is 60 to 95 wins in 100; we are at 0.1, 600 to 950 times below.

## What we should do

Costs: a "lane" is one worker session, 2 to 4 hours; a judged block of 2,000 pairs holds the machine about 3 hours (about 30 core-hours); a run-brain fit is 2 to 3.5 card-hours. Gains are in honestly-read first-Act-3-boss kills (now 2.6 in 100) and wins (now 0.1 in 100); my uncertainty on every gain is wide.

| Option | Cost | Expected gain (Act 3 boss / wins per 100) | Risk | Known within a week? |
|---|---|---|---|---|
| 0. Read Act 3 kills as "went past the boss" in the judge; re-score the ledger | 1 lane, no machine | none by itself; changes verdicts (cheap-v3d becomes +0.90 [+0.23, +1.57]) | none | yes, in a day |
| d. A target that counts the goal: refit the run brain on the ~84,000 plain runs on disk with per-boss survival heads chained into a win chance (or "bosses beaten from Act 2 on") | 1-2 lanes; 1 fit; 1-2 judged blocks | +0.5 to +2 / 0 to +0.3 | trades Act 1 survival for Act 3 (the refused fits did); the last head has 54 wins | yes |
| b. More search at Act 3 bosses: replay a few hundred saved Act 3 boss positions (the fight loop already builds starts from run fights) at 1x, 4x and 16x today's boss budget | 1-2 lanes; under half a machine-day | unknown; each +10 points per door is about +1.5 per 100 runs | the copy's Act 3 may be wrong | yes |
| c. Act 3 into the fight brain: the 24,393 human Act 3 positions as practice starts, Act 3 boss cells in the exam | 2-3 lanes; the fight loop's card time | unknown; the loop's record is one promotion in three weeks | slow; human decks differ from ours | the exam cell yes, the gain no |
| a. Variety: explore where the brain's top two are within half a floor, fork runs at hard choices, weighted to Acts 2-3 | 2-3 lanes; 1-2 machine-days; 1 judgement | 0 to +1 / about 0 | off-policy labels; machine time taken from the fight rows | partly |
| e. Relax D6 (end-to-end reinforcement learning) | weeks of build; compute likely far beyond one PC | unknown; the reward is 1 win in 1,000 runs | cost, opacity | no |
| e'. Relax D7 (no language models) | owner's decision; API cost | an LLM agent with screen control won 6 of 15 Ironclad A10 runs (Epoch AI, above) | changes the project | a 15-run probe, partly |
| f. Narrow to "from Act 3 entry" as the next goal, or stop | | | | |

On (e): the run loop already is outcome-based improvement with search, which D6 allows (D6 came from the design document, not the owner, D60). What it lacks against published systems is exploration and a target aimed at the outcome, not the "end-to-end" label. Mahjong's Suphx reached the top 0.01 in 100 of ranked players by learning from human play first, then large-scale self-play (https://arxiv.org/abs/2003.13590); in NetHack, a long random roguelike, hand-written bots beat neural agents about three times on median score and nothing came near winning (https://arxiv.org/abs/2203.11889). The only published AI wins at Slay the Spire 2 A10 are language-model agents, which D7 forbids.

**Recommended order.** Option 0 first (a day). Then d and b in the same week: both use data and positions on disk, and both answer the decisive question cheaply. Then c, sized by what b shows. Then a, only aimed at Acts 2-3. Set a stop rule now: if by 12-02 the honestly-read first Act 3 boss kill per door has not moved from 15.5 toward 30 in 100 and wins have not reached about 0.5 in 100, stop this method or reopen D7.

**The one real bet:** aim the whole loop at the two Act 3 boss fights: what the run brain learns (the win, not floors), what the fight brain practises and is examined on (Act 3 bosses), and where the search spends (Act 3 doors). About nine tenths of the gap to the average human is there, and today nothing is aimed there. Everything else polishes Acts 1 and 2, where the copy's champion is already at or above the average human.

## What would change this conclusion

The most informative test within a week: **one real-game block of generation 18 (2,000 runs, about 300 Act 3 boss doors if the copy is right), read with "went past the boss".** If the real per-door kill of the first Act 3 boss is far above the copy's 15.5 in 100 (say over 35), the wall is the copy's and the bet becomes Act 3 fidelity, not learning; if it matches, the bet stands. Second, option b's replay: if four times the search lifts the per-door kill by 10 points or more, the ceiling is compute, not method. Third, option d: if a win-aligned refit on existing runs gains at least +1.5 in 100 on the first Act 3 boss over 4,000 pairs without a collapse, the answer moves from "no" to "maybe, slowly". If none of the three moves, this method stops near today's level.
