# B. Measurement and truth: do our numbers mean what we say they mean?

Analyst B, 2026-11-18 20:50Z. Read-only. Every figure below is printed by a script in `referee/backlog/analysis-2026-11-18/scripts/B-*.py` (named in brackets with its source files). Paths are under `D:/spireline/`.

Words used once and then plainly: **the copy** is our re-built version of the game that the AI learns and is judged on. **The real game** is the game itself, run without a window. A **real block** is about 2,000 runs of the champion in the real game. **The judge** decides whether a new brain (a **candidate**) replaces the **champion**: both play the same fresh seeds (**pairs**) and a **keep rule** decides (v1: floors; v2, from 11-05: the deepest boss the line reaches, or floors; v3, from 11-18: the first Act 3 boss and wins only). A **generation** is a promoted champion. "In 100" is per 100 runs unless it says "of arrivals" (per 100 runs that reached that boss).

## In short

- The judge's Act 3 number is misread. Two in three of the runs it counts as killing the first Act 3 boss died in that fight. Generation 18 gets past that boss in 2.6 in 100 runs, not 7.9; humans in 18.2. Rule v3 has decided on the wrong number since 11-18.
- For the same player, the copy and the real game agreed in Acts 1 and 2: generation 13 had 24.5 floors on the copy and 24.2 in the real game. The scoreboard's 30.3 against 24.2 compares two players twelve days apart. But the two part ways more often the deeper a run goes. When they part, the real-game harness plays a stand-in rule, and Act 3 has almost no real evidence (62 arrivals ever).
- No real block has run for 12 days, though the owner's own trigger for one was met on 11-15.
- Generation 18 is ahead of humans at Act 1 and near them at Act 2, but far behind at Act 3 and the win. "The best humans" cannot be measured from our corpus.

## What went right

1. **The copy gives the same number for the same player.** Generation 17 was judged on six separate seed sets (500 to 2,000 pairs each, 9,299 runs). It read 29.2 to 29.9 floors, and 19.6 to 23.6 in 100 at the Act 2 boss: within sampling noise [B-judge.py; `referee/agent/gen17/candidate-cheap-v2/arms/*/runs.jsonl`]. No seed was reused across the 36 judged blocks (56,700 seeds), and none was shared with a real night [B-judge.py].
2. **In Acts 1 and 2 the copy told the truth about the same player** (real nights to 11-06 against the copy's judged runs of the same generation) [B-nights.py; `referee/lab/nightly/*/g*/runs.jsonl`]:

| generation | real floors (runs) | copy floors (runs) | Act 2 boss, real | Act 2 boss, copy |
|---|---|---|---|---|
| 9 | 22.5 (2,872) | 22.4 (8,000) | 1.7 | 2.1 |
| 11 | 23.5 (3,479) | 23.1 (6,400) | 3.4 | 2.4 |
| 12 | 22.8 (1,992) | 22.9 (2,500) | 5.5 | 5.4 |
| 13 | 24.2 (1,995) | 24.5 (6,500) | 7.8 | 9.3 |

   On the 200 seeds both sides played in generation 13's night, the copy was 1.07 floors higher (standard error 0.65). Both sides ran Ascension 10 with the same search settings and agent files [`nightly/2026-11-06T0852/g13/compare.json`, `resume.json`]. The search is budgeted by simulations, not by the clock, so the real game's slowness costs time, not strength.
3. **The steps between champions held up in the real game.** Each real night's step pointed the same way as the copy's, at about two thirds to three quarters of the size. Generation 12 to 13: +1.3 floors real against +1.85 on the copy, and +2.3 against +3.4 in 100 at the Act 2 boss. Generation 11 to 12: +2.1 against +2.9 at the Act 2 boss [B-nights.py; `promotions.tsv`; DECISIONS D55 addendum 8].
4. **Most refusals were sound.** Of 19 refused candidates, 10 were worse by two standard errors or more, 8 were level, and 1 was a likely gain (below) [B-judge.py]. Rule v3's second look worked once: cheap-v3d's first-block Act 3 signal did not repeat on fresh seeds [`promotions.tsv`, 11-18 rows].
5. **The seed-matched human exam** (our player on the seeds of 400 human runs) separates the play from the deal [`referee/seed-exam/2026-11-12-gen14/table.md`].

## What went wrong

1. **The Act 3 boss kill is misread.** The judge counts a boss as beaten when the record shows its health bar fully emptied [fork `tools/lab/keep_v2.py` `bosses_beaten`]. At the Act 1 and Act 2 bosses that reading is exact: for generation 17, all 6,827 and 2,133 such readings went on to the next act. At the first Act 3 boss, 436 of 654 (67 in 100) died on that floor and never met the second boss. The real game shows the same (7 of 9) [B-killread.py]. The plain-run store keeps its own boss record, and it agrees with the floor, not with the judge: generation 17 beat that boss in 1,208 of 52,816 plain runs (2.3 in 100) [B-plainruns.py; `referee/run-cheap/17/runs.jsonl`]. The likely cause is a boss whose bar empties once before the fight is over; this is unchecked. What it does:
   - The scoreboard's Act 3 figure of 7.9 in 100 is really 2.6 (52 of 2,000). The human 18.2 uses the strict meaning.
   - About two thirds of v3's signal is "died in the fight after a full bar of damage".
   - Read strictly, several verdicts change [B-killread.py]:
     - generation 17 over 16 at Act 3: 0.0 in 100, not +1.4;
     - cheap-v3d on its 4,000 pooled pairs: +0.98 (z 2.7), not +0.75 (z 1.4), right at v3's +1.0 line;
     - generation 18 over 17: +0.35 (noise).
   - The frontier (the deepest boss the line beats in 1.5 of 100 runs) switched between Act 2 and Act 3 three times in four judgements, on loose readings of 1.67, 1.54, 1.13 and 2.44. Read strictly, generations 14 and 15 got past that boss 0.4 and 0.2 in 100 [`gen16/*/promotion.json` frontier records; B-killread.py].
2. **No real game for 12 days, though the owner's own trigger was met.** The record, in order:
   - 11-06: the last real block.
   - 11-06 to 11-09: the between-blocks real check failed eight times at its time cap, about 210 core-hours lost, and was switched off (D55 addendum 17).
   - 11-09: the owner set the next block to run when a promotion reads 15.3 or more in 100 at the Act 2 boss on the copy, else monthly (D55 addendum 16).
   - 11-15: generation 17 was promoted at 21.8. No block was written, and neither D63 nor the landing line mentions the trigger [HANDOFF 2026-11-15 17:59Z].
   - 11-18: the week's plan held a real night; D67 then paused it.

   Five promotions and a rule change rest on copy figures alone. Today's player reaches the Act 2 boss in 50 of 100 runs and the Act 3 boss in 16.5; generation 13 reached them in 27 and 1.1. The last real reading says almost nothing about where today's player wins and loses.
3. **"998 moves in 1,000" hides where the copy and the real game part ways.** It averages all decisions, and most decisions are in Act 1. In the real nights of generations 9 to 13 (10,338 runs), the two sides parted:
   - per 100 floors played: 0.7 times in Act 1, 4.7 in Act 2, 10.1 in Act 3;
   - per 100 visits to a boss floor: 3.0, 9.3 and 17.7 [B-divergence.py; `nightly/*/divergences.jsonl`].
4. **The real column measures the player plus a stand-in.** When the copy falls out of step, the real game is played by a fixed rule until the next fight or room. The rule plays the first card, else the first move that does not end the turn [fork `referee/lockstep.py` `referee_only_policy`, `play_run`]. That was 1.7 in 100 decisions in generations 9 to 13. Boss fights where it happened ended worse:
   - Act 1: 47 against 57 in 100 (253 such fights of 9,400);
   - Act 2: 12 against 18 (182 of 2,455);
   - Act 3: 0 of 11 against 2 of 51 [B-fallback.py].

   Out-of-step fights may also be harder fights, so this bounds the stand-in's cost; it does not measure it. Pooled over generations 9 to 13 and weighted to the same mix, the two sides beat the Act 2 boss equally often (17.6 against 17.5 in 100 arrivals). Generation 13 alone reads 28.9 real against 33.8 on the copy (p 0.02), and its in-step fights also read 28.9, so that gap is not the stand-in [B-acts.py, B-fallback.py].
5. **Act 3 has the least real evidence and the worst agreement.** There have been 62 real arrivals at the first Act 3 boss, ever. Read the same loose way on both sides, the real game converts 14.5 in 100 of them and the copy 36.6 (68 of 186; p 0.0006). Strictly, 2 of the 62 got past [B-acts.py, B-stats.py].
6. **The judge's target kept moving.**
   - The keep rule changed twice and its guards three more times (11-09, 11-16, 11-17).
   - Twice the rule changed hours after a refusal was read. v2 promoted generation 12 on the block v1 had refused that afternoon, and v3 followed cheap-v3d's refusal.
   - Generation 18 was promoted 3 minutes before v3, by the floors route that v3 abolished.
   - Five of the seven v2 promotions went by floors alone [`promotions.tsv`].

   The record no longer measures one thing across generations.
7. **The record, promotion by promotion** [B-judge.py; `promotions.tsv`; `promotion*.json`]:
   - All 16 promotions cleared their own rule (generations 1 to 11 on floors, 3 to 33 standard errors).
   - Since 11-05, Act 2-or-later gains were beyond two standard errors for generations 12 (+2.9 in 100 at the Act 2 boss, z 5.0), 13 (+3.4, z 2.7), 16 (+3.6, z 3.4) and 17 (+5.4, z 3.1). For generations 14 (z 1.8), 15 (z 2.2) and 18 (z 0.9) they were within noise; those gains were floors and Act 1.
   - Contradicted: none by a real night; generation 18 by the rule in force three minutes later; generation 17's Act 3 gain once read strictly.
   - The refused gain is round 3 (`gen18/candidate-cheap-v3`, 11-16): Act 2 boss 27.2 against 23.3 in 100 (z 3.5), Act 3 strictly +1.15 (z 2.1), floors +0.55. HANDOFF (11-16 21:33Z) and the paper called it "level", quoting Act 1 and floors. It was never replayed; v3 would have given it a second block.
8. **The judge cannot see the gains it now asks for.** At 2,000 pairs v3's measure has a standard error of 0.69 in 100. A true +1.0 then needs about 6,300 pairs for an even chance of promotion and 11,200 for 4 in 5: 12 to 22 hours of the whole machine. As built (2,000 pairs, then 2,000 more), v3 promotes a true +1.0 about 28 times in 100 and +2.0 90 times [B-stats.py]. The strict reading is less noisy (4 in 5 at about 4,900 pairs).
9. **The milestone check stopped.** The seed-matched human exam was to run after every promotion (D58 addendum 18); it last ran on generation 14 [`referee/seed-exam/`].
10. **The fight exam does not look where the runs die.** It is 400 human fight starts, Acts 1 and 2 only, in equal quotas per act and kind [fork `rl/fight_exam.py`]. Fight player v3's +2.6 on it (62.0 to 64.6) moved whole runs at the Act 1 boss (+3.7 in 100, p 0.0002) but not at the Act 2 boss (+0.9) or Act 3 (strictly +0.35) [`gen18/candidate-fight-v3/promotion.json`; B-killread.py]. Played from human positions, we lose more Act 1 boss fights than the humans did (64 against 73 in 100 in the 11-08 practice reading [`referee/backlog/human-bar/diagnosis.md`]). Yet in our own runs we beat that boss more often than humans do (80 against 74 of arrivals). The exam measures play with the humans' decks, not the fights our runs die in.
11. **Far from humans where it counts.** Humans: Spire Codex public run export for v0.107.1 [fork `docs/reference/codex-a10-ironclad.md`]. Generation 18: the copy, 2,000 runs, read strictly [B-acts.py, B-killread.py, B-lastboss.py]:

| per 100 | humans, finished runs (14,811) | humans, quits counted as losses | gen 18, copy | gen 13, real |
|---|---|---|---|---|
| floors (average) | 27.1 | 22.1 | 30.3 | 24.2 |
| Act 1 boss beaten | 54.6 | 43.7 | 76.5 | 56.6 |
| Act 2 boss beaten | 29.1 | 22.0 | 24.5 | 7.8 |
| first Act 3 boss got past | 18.2 | not read | 2.6 | 0 of 1,995 |
| wins | 11.3 | 8.0 | 0.1 | 0 |

   Per 100 arrivals at each of the four bosses, humans win 74, 76, 73 and 62 times. Generation 18 wins 80, 49, 16 and 4 (2 of 52 at the last boss; 54 of 1,208 in generation 17's plain runs). The walls are the first Act 3 boss and the last fight, then Act 2. The floors row flatters us: we die later in Act 1 and earlier at Act 3.
12. **The scoreboard misleads** [`spireline/docs/paper/spireline-paper.html`, At a glance]:
   - The real column (generation 13, 11-06) stands beside a different player on the copy (generation 18, 11-18).
   - The Act 3 row is the loose 7.9, with humans "not yet read", though their 18.2 has been in the reference since 10-28.
   - The human line leaves out 6,111 abandoned runs yet says "every Ironclad run"; the footnote describes generation 17, not 18.
   - No figure carries an interval.
   - "Judged by the real game" (the subtitle), "a fixed block of 500 real games" and "nightly real-game blocks" have been untrue since 11-06.

## What the evidence cannot tell us

- **The best humans.** The corpus's per-player key is blank on solo runs, so "best players" cannot be selected. Winning runs (about 1,600 at A10) mix luck and skill and give no player level (DECISIONS D55 addendum 22). The closest reading is the seed exam: on 200 seeds a human won, generation 14 died 22 floors earlier, and none of its 400 draws won. It has not been read since generation 14. The target "beat the best" has no number.
- **Whether generations 14 to 18 are as good in the real game.** History says Act 1 and 2 gains transfer at two thirds or more. On that basis generation 18 would beat the Act 2 boss about 17 to 22 times in 100 runs in the real game. That is a projection, not a measurement. At Act 3 the range is 0.3 to 2.6 in 100 and nothing narrows it.
- **How much of the Act 3 gap is the copy and how much is the stand-in.** 62 arrivals cannot split it.
- **Whether the copy's last boss is right.** We beat it in 4 of 100 arrivals, humans in 62, and no real run has fought it to the end.
- **The real nights' per-fight detail.** The logs were deleted at block end, so old divergences cannot be re-diagnosed.

## What we should do

| # | option | cost | expected gain | risk | known within a week by |
|---|---|---|---|---|---|
| 1 | Count a boss as beaten only when the run gets past it (as the plain-run store does) in the judge, frontier, ledger and scoreboard; re-judge v3's rows from the saved arms | 1 to 2 worker hours, no machine | v3 measures what D66 asked, with less noise | verdicts move (cheap-v3d sits on the line) | same day: judge and store agree at about 2.3 in 100 |
| 2 | Real block of generation 18 (2,000 runs; the copy replays 500 of its seeds; out-of-step fights reported apart). Cheaper: 500 real runs on seeds where the copy reached the Act 3 boss, reading only the copy-minus-real difference | about 12 machine hours (cheaper: 5 to 6) | first real reading of today's player; 200 to 330 Act 3 arrivals | a day without data or judging; reads low because of the stand-in | within 24 hours |
| 3 | Replace the stand-in: re-anchor at the next decision, or let the agent choose from the real state | a harness worker plus a 2-hour real check | the real column measures the player | mid-fight re-anchors can fail | out-of-step fights convert like in-step ones |
| 4 | Seed-matched human exam on generation 18, then after every promotion | about 10 core-hours | the only like-for-like human comparison | none | next day |
| 5 | Replay round 3 (cheap-v3) on fresh seeds under v3 with option 1 | about 4 machine hours | possibly +4 in 100 at the Act 2 boss | may come out level | same day |
| 6 | The five weekly numbers below replace the scoreboard | one paper edition | an honest board | none | next edition |
| 7 | Fight exam: add both Act 3 bosses; weight by where our runs die | a worker, 10 core-hours a reading | an exam that predicts run changes | Act 3 fidelity unknown | its next change against a run judgement |

**The five numbers each week**, with their noise at a cost we can afford:

1. **Wins per 100, real game**: the champion over 2,000 runs, with a 95% interval (upper bound about 0.2 to 0.4 today); humans 11.3, or 8.0 counting quits.
2. **First Act 3 boss got past, per 100 runs**: real and copy, same player and seeds, read strictly; standard error about 0.35 at 2,000 runs; humans 18.2.
3. **Copy honesty**: per act, copy minus real in bosses beaten per 100 arrivals (paired by seed), and out-of-step boss fights per 100 (now 3, 7, 18); an alarm past two standard errors.
4. **Distance to winning humans**: from the seed exam, our floor minus the human's on the 200 seeds the human won (generation 14: -22, give or take 1.2), and how many of those seeds we win (0 of 200).
5. **Net gain this week on the copy**: this week's champion against last week's on 2,000 fresh pairs (Act 3 passes plus wins, and the Act 2 boss, with intervals; about 4 machine hours). Unlike a chain of promotions, it is not inflated by picking the best of several candidates.

**Cadence of real blocks:** one 2,000-run block a week, by the calendar: about 12 hours, 7 in 100 of the machine's week. The trigger tied to copy gains failed the one time it fired. It also cannot see the drift it exists to catch: a copy that flatters itself also raises its own gains.

**Recommended order:**
1. Option 1, today.
2. Option 2, before v3 judges anything else.
3. Options 4 and 5, this week.
4. Option 3, before the next real block.
5. Option 6 as standing practice.
6. Option 7 once Act 3 has a real reading.

## What would change this conclusion

- **A real block of generation 18** would change it most.
  - If, with out-of-step fights set apart, the real game comes within about 3 in 100 of the copy at the Act 2 boss and about 1 in 100 at the first Act 3 boss, then the copy is honest where the judge looks. The 12 days would then have cost nothing, and the problem is how fast the AI learns, not what we measure.
  - If the real game gets past the first Act 3 boss close to never in 200 or more arrivals, then the copy's Act 3 is wrong and v3 is optimising a flaw in it. Every promotion since generation 13 would then need re-weighing.
- **Twenty hand-read copy runs** that "killed" the first Act 3 boss and died on its floor (minutes, no machine). If they show a second boss fought on the same floor and missed by the record, the Act 3 rate is about 7 in 100, and items 1 and 5 fall. The plain-run store's independent record (2.3 in 100) makes this unlikely.
