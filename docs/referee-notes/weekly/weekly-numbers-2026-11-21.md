# The five weekly numbers (2026-11-21T10:30:45Z)

Champion: generation 20. Rates are per 100 with a 95% interval in brackets and the counts; humans: Spire Codex public run export for v0.107.1; Ironclad, Ascension 10; finished runs (14,811); aggregates.

| # | number | now | n | humans | read from |
|---|---|---|---|---|---|
| 1 | wins per 100, real game | 0.10 [0.03, 0.36] | 2000 | 11.3 (8.0 counting quits) | 2026-11-20T1904, 0.6 days old (referee/LAB/nightly/2026-11-20T1904/g20) |
| 2 | first Act 3 boss passed | real, all runs: 3.05 [2.38, 3.90]; per 100 arrivals: 17.5 [13.9, 21.9]<br>copy, same seeds: 5.80 [4.07, 8.21]; per 100 arrivals: 26.4 [19.0, 35.3]<br>real, same seeds: 3.40 [2.13, 5.38]; per 100 arrivals: 20.0 [12.9, 29.7] | 2000 real (348 arrivals), 500 pairs (copy 110 arrivals, real 85) | 18.2 per 100 runs, 72.7 per 100 arrivals | 2026-11-20T1904 g20 |
| 3 | copy honesty (copy minus real) | both arms end in the same act: 54.8 [50.4, 59.1] in 100<br>real ended in Act 1 (128 runs): copy in the same act 52.3 in 100, floors +8.85<br>real ended in Act 2 (227 runs): copy in the same act 55.1 in 100, floors +0.40<br>real ended in Act 3 (145 runs): copy in the same act 56.6 in 100, floors -7.76<br>all: floors +0.20 (se 0.58)<br>alarm: YES, Act 1 same-act share moved -6.6 points (within its 95% noise of 11.9); Act 2 same-act share moved -12.3 points (beyond its 95% noise of 8.7) | 500 pairs | - | 2026-11-20T1904 g20 vs 2026-11-19T1103 g19 |
| 4 | distance to winning humans | 22.0 floors behind on seeds a human won [20.8, 23.3]; won 0 of 200 of those seeds (0 of 400 draws) (generation 14, not the champion: no exam of generation 20 exists; the newest is of generation 14) | 200 seeds | the human won all of them | referee/seed-exam/2026-11-12-gen14, 9.1 days old |
| 5 | gen20/candidate-chain against gen19/candidate-cheapv3-fightv3 | the selection block only, not fresh: passed 5.91 vs 3.09; wins 0.27 vs 0.09; difference in passed 2.82 per 100 (se 0.76) | 1100 pairs | - | agent arms, promotions.tsv |

## The stop rule (by 2026-12-02)

First Act 3 boss passed per 100 arrivals: 25.4 now (the selection block (not fresh); 1100 pairs), started at 16, target 30; wins 0.27 per 100 (target 0.5). Fresh pairs so far 0 of 4000; a real block of the champion: yes; days left 11.6.

Strict means a run won or its floor is above 48; an arrival is floor 48 reached, a win, or a boss-damage entry for Act 3. A crashed real run counts as a loss. Copy-honesty rows by act are conditioned on where the real arm ended (a real run that ended early was a low draw, so the copy tends to read higher there and lower in Act 3): only the all-runs floor difference is a plain bias; compare the per-act rows between blocks of the same player, and read the two-point alarm beside its noise (a few hundred pairs move several points by chance).
