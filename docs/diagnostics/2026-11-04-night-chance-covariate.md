# The night block's covariate, stage 1: the game's draws, read on the nights with game-log copies (2026-10-29 to 2026-11-04)

Written 2026-11-04 (housekeeping lane), brief 4c of `docs/design/2026-11-04-training-design.md` (section 4.4). Source: `tools/morning_report.py`
(the new `chance_covariate` block and `--chance-read`), run read-only on `LAB/nightly/<date>` for the nine dates and the game-log copies
`logs/w5-night-<date>-stdout` (present for 10-29 to 11-04); output to a scratch folder, nothing under `backlog/`. The tool's `--check`
second path recomputed every figure below that the tool prints (14 chance figures a night plus the older ones): 9 nights, 92 to 109
figures each, 0 mismatches. Counts are over ended real runs that the night's game-log copy holds (99.0% to 99.9% of them). No human data is used.

## 1. What was computed

A run's floor is skill plus the luck of the deal: which Act 1 the game rolled (it has two pools of encounters and bosses), which encounter each
hallway and elite room drew, which boss waited. The game deals these, not the agent, so for any agent the deal's effect has an expected value
that can be computed and subtracted. For each draw the term is **the value of what was drawn minus its expected value over the pool's odds**;
the sum over a run is the run's correction, and the corrected mean floor is `mean(floor) - beta x mean(correction)`. Only chance terms enter: the
run head's value of a state would subtract skill as well (design 4.4), and the table below is only ever asked "how did runs that met this draw
end", never "what did this agent do".

- **What counts as a draw.** Every combat room in the copy: boss, elite, hallway weak (the act's first rooms), hallway normal; an event's fight is
  a choice and is left out. The act is one plus the bosses passed. The act's variant is a draw too (the first room tells which pool the act
  uses); it is found from the runs themselves (encounters met together in one act are one variant), not listed by hand.
- **The value table (fixed before the night).** The mean final floor of the real runs of the **previous generation** (the highest generation below
  the night's own, its nights with a game-log copy) that met each draw; a draw met in under 20 of those runs takes its pool's mean. It is written
  beside the report (`chance_table.json`).
- **The odds.** The game deals each pool without replacement within an act (an encounter never came twice in an act's weak, normal or elite pool
  in about 60,500 draws, one repeat), so a draw's expectation is taken over the pool's encounters not yet drawn in that act, at their frequencies over **every
  earlier night with a copy**, whichever generation played it (the deal does not depend on the player). A run that died on a hard encounter has
  not drawn it again, and the conditional expectation knows that (against the plain pool average the difference was small on these nights).
- **The correction's own check.** It averages zero when the frequencies are the game's odds. Its SE counts the odds' sampling error
  (SD x sqrt(1/n + 1/odds runs)). The brief asked for the check on the copy arm, where the odds are exact; the copy arm's rows hold only the room-type
  string (`nodes`) and no encounter ids, so it is read on the real arm's own draws.
- **The corrected SE** is the residual SD of the floor on the correction over sqrt(n), plus the odds' sampling error in the double-sampling form of
  the control variate (`beta^2 SD(correction)^2 / odds runs`). The plain AIVAT form, floor minus correction with no fitted slope, is printed beside it.

## 2. The night-by-night table (the report's rule)

Table from the previous generation's nights; odds from every earlier night with a copy. The correction is in floors; the last column counts
draws the table never saw (left out of the sum).

| night | gen | table from | runs used (ended) | sd of floors | raw mean (SE) | corrected mean (SE) | corrected SE / raw SE | rho | 1 - rho^2 | mean of the correction (SE, z) | unknown draws |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10-26 | 5 | not measured: no game-log copy of the night |  |  |  |  |  |  |  |  |  |
| 10-27 | 7 | not measured: no game-log copy of the night |  |  |  |  |  |  |  |  |  |
| 10-29 | 7 | not measured: no earlier night with a game-log copy to build the table from |  |  |  |  |  |  |  |  |  |
| 10-30 | 9 | 10-29 (g7) | 1,407 (1,409) | 7.55 | 22.11 (0.201) | 21.95 (0.199) | 0.991 | 0.267 | 0.929 | +0.158 (0.068, z +2.3) | 6 of 13,384 |
| 10-31 | 9 | 10-29 (g7) | 469 (472) | 7.45 | 22.55 (0.344) | 22.58 (0.342) | 0.993 | 0.137 | 0.981 | -0.050 (0.095, z -0.5) | 0 of 4,502 |
| 11-01 | 9 | 10-29 (g7) | 491 (493) | 7.66 | 22.71 (0.346) | 22.62 (0.337) | 0.974 | 0.249 | 0.938 | +0.092 (0.094, z +1.0) | 1 of 4,757 |
| 11-02 | 9 | 10-29 (g7) | 497 (498) | 7.93 | 23.05 (0.356) | 23.07 (0.344) | 0.966 | 0.280 | 0.922 | -0.010 (0.097, z -0.1) | 0 of 4,907 |
| 11-03 | 11 | 10-30+10-31+11-01+11-02 (g9) | 1,990 (1,992) | 7.93 | 23.41 (0.178) | 23.32 (0.175) | 0.983 | 0.243 | 0.941 | +0.094 (0.056, z +1.7) | 0 of 19,945 |
| 11-04 | 11 | 10-30+10-31+11-01+11-02 (g9) | 484 (489) | 8.05 | 23.67 (0.366) | 23.56 (0.356) | 0.974 | 0.238 | 0.943 | +0.106 (0.095, z +1.1) | 0 of 4,885 |

- Pooled over the six nights (5,338 runs, Fisher z): rho 0.244, **1 - rho^2 = 0.941**: 5.9 in 100 of the floor variance removed,
  the corrected SE 0.966 to 0.993 of the raw SE (the odds' sampling error is in it).
- 10-26 and 10-27 have no copy. 10-29 has a copy but no earlier night with one, so the rule has no table to give it.
- The three nights that share the 10-29 table (10-30 to 11-02) and the two that share the g9 table (11-03, 11-04) are not independent readings of
  the correction's mean: the offsets they show are largely the one table's sampling error.

Sensitivity reading, not a rule: every other night with a copy (later ones too) gives both the values and the odds, so 10-29 is readable and the
odds are better known.

| night | gen | table from | runs used (ended) | sd of floors | raw mean (SE) | corrected mean (SE) | corrected SE / raw SE | rho | 1 - rho^2 | mean of the correction (SE, z) | unknown draws |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10-26 | 5 | not measured: no game-log copy of the night |  |  |  |  |  |  |  |  |  |
| 10-27 | 7 | not measured: no game-log copy of the night |  |  |  |  |  |  |  |  |  |
| 10-29 | 7 | 10-30+10-31+11-01+11-02+11-03+11-04 (g9) | 1,920 (1,921) | 6.71 | 19.08 (0.153) | 19.13 (0.151) | 0.986 | 0.213 | 0.955 | -0.073 (0.050, z -1.5) | 0 of 15,942 |
| 10-30 | 9 | 10-29+10-31+11-01+11-02+11-03+11-04 (g7) | 1,407 (1,409) | 7.55 | 22.11 (0.201) | 22.10 (0.196) | 0.974 | 0.263 | 0.931 | +0.010 (0.058, z +0.2) | 2 of 13,384 |
| 10-31 | 9 | 10-29+10-30+11-01+11-02+11-03+11-04 (g7) | 469 (472) | 7.45 | 22.55 (0.344) | 22.56 (0.341) | 0.991 | 0.148 | 0.978 | -0.015 (0.093, z -0.2) | 0 of 4,502 |
| 11-01 | 9 | 10-29+10-30+10-31+11-02+11-03+11-04 (g7) | 491 (493) | 7.66 | 22.71 (0.346) | 22.71 (0.337) | 0.974 | 0.241 | 0.942 | +0.001 (0.093, z +0.0) | 0 of 4,757 |
| 11-02 | 9 | 10-29+10-30+10-31+11-01+11-03+11-04 (g7) | 497 (498) | 7.93 | 23.05 (0.356) | 23.12 (0.343) | 0.964 | 0.281 | 0.921 | -0.057 (0.093, z -0.6) | 0 of 4,907 |
| 11-03 | 11 | 10-29+10-30+10-31+11-01+11-02+11-04 (g7) | 1,990 (1,992) | 7.93 | 23.41 (0.178) | 23.33 (0.174) | 0.981 | 0.246 | 0.939 | +0.086 (0.052, z +1.6) | 0 of 19,945 |
| 11-04 | 11 | 10-29+10-30+10-31+11-01+11-02+11-03 (g7) | 484 (489) | 8.05 | 23.67 (0.366) | 23.55 (0.356) | 0.974 | 0.239 | 0.943 | +0.120 (0.090, z +1.3) | 0 of 4,885 |

Pooled over the seven nights (7,258 runs): rho 0.236, 1 - rho^2 = 0.944. The two readings agree: about 5.9 in 100 of the variance.

## 3. What carries it

Share of the floor variance left after correcting with one kind of draw alone (1 - rho^2 of that kind's terms), rule nights:

| night | variant | hallway | elite | boss | all four |
|---|---|---|---|---|---|
| 10-30 | 0.9998 | 0.9985 | 0.9978 | 0.9251 | 0.9286 |
| 10-31 | 0.9994 | 1.0000 | 0.9990 | 0.9733 | 0.9813 |
| 11-01 | 0.9921 | 0.9939 | 0.9991 | 0.9322 | 0.9381 |
| 11-02 | 0.9996 | 0.9921 | 0.9940 | 0.9312 | 0.9217 |
| 11-03 | 0.9997 | 0.9946 | 0.9934 | 0.9508 | 0.9411 |
| 11-04 | 0.9999 | 0.9997 | 0.9978 | 0.9447 | 0.9434 |

The boss draw carries nearly all of it: 2.7 to 7.5 in 100 of the variance by itself (the 469-run night 10-31 is the 2.7). The variant, hallway and elite draws are each under 1
in 100 (0 to 0.8). The Act 1 boss values the 11-03 and 11-04 table used (mean final floor of the generation 9 runs that met each; one boss in
this table span 5.7 floors, 20.3 to 26.1; the Act 2 bosses differ by under one floor):

| act | variant (named by its smallest encounter id) | boss | draws in the table | mean final floor of the runs that met it |
|---|---|---|---|---|
| 1 | BYGONE_EFFIGY_ELITE | CEREMONIAL_BEAST_BOSS | 445 | 26.05 |
| 1 | BYGONE_EFFIGY_ELITE | THE_KIN_BOSS | 447 | 22.19 |
| 1 | BYGONE_EFFIGY_ELITE | VANTOM_BOSS | 444 | 22.51 |
| 1 | CORPSE_SLUGS_NORMAL | LAGAVULIN_MATRIARCH_BOSS | 429 | 24.74 |
| 1 | CORPSE_SLUGS_NORMAL | SOUL_FYSH_BOSS | 423 | 25.24 |
| 1 | CORPSE_SLUGS_NORMAL | WATERFALL_GIANT_BOSS | 434 | 20.32 |
| 2 | BOWLBUGS_NORMAL | KAISER_CRAB_BOSS | 204 | 33.16 |
| 2 | BOWLBUGS_NORMAL | KNOWLEDGE_DEMON_BOSS | 194 | 34.01 |
| 2 | BOWLBUGS_NORMAL | THE_INSATIABLE_BOSS | 186 | 33.70 |

## 4. What it buys in runs

Real runs a night needs to see a change (two nights of fresh seeds compared, 80% power, two-sided 5%, the nightly power doc's basis), the night's
own SD of floors:

| night | sd of floors | half floor: raw | half floor: corrected | one floor: raw | one floor: corrected | runs saved for a one-floor reading |
|---|---|---|---|---|---|---|
| 10-30 | 7.55 | 3,580 | 3,325 | 895 | 832 | 7.0% |
| 10-31 | 7.45 | 3,485 | 3,420 | 872 | 855 | 1.9% |
| 11-01 | 7.66 | 3,685 | 3,457 | 922 | 865 | 6.2% |
| 11-02 | 7.93 | 3,952 | 3,643 | 988 | 911 | 7.8% |
| 11-03 | 7.93 | 3,951 | 3,719 | 988 | 930 | 5.9% |
| 11-04 | 8.05 | 4,070 | 3,839 | 1,018 | 960 | 5.7% |

On the latest night (11-04, SD 8.05) a one-floor change needs 1,018 real runs raw and 960 corrected, a half-floor change 4,070 and 3,839: about 6
in 100 fewer runs for the same reading. For comparison the copy arm as run today buys under 1% (nightly power doc), and with the copy mean known
exactly it would buy 23 in 100 (rho 0.48).

## 5. The correction's mean (the odds check)

The correction averages between -0.05 and +0.16 floors on the rule nights; z (counting the odds' sampling error) is, for 10-30 to 11-04, +2.3, -0.5, +1.0, -0.1, +1.7, +1.1, the largest 2.3 in absolute value, inside
the 3 SE line on every night. The four largest offsets (10-30, 11-01, 11-03, 11-04: +0.16, +0.09, +0.09, +0.11 floors) are all positive and come mostly from the boss
term; with one night or four nights behind the table's frequencies that is what a sampling error looks like, and the sensitivity reading, with
five or six other nights behind the odds, puts the same nights at +0.01, +0.00, +0.09 and +0.12 (z 1.6 at most). The corrected mean sits 0.01 to 0.17 floors
from the raw mean. Nothing here shows a bias, nothing rules out a small one (one possible source: a better agent reaches deeper positions in the
pools, and the odds for a later position are not read separately); the check is printed every morning with its z so a drift shows.

## 6. Stage 2: go or no-go

The rule, written before the table was read: go when the pooled variance removed is at least 5 in 100 (the low end of the design's 5 to 15 for
stage 1) and the correction's mean sits within 3 SE on every night read; no-go under 3 in 100; between, marginal. Result: 5.9 in 100, largest |z|
2.3. **By the rule: go**, narrowly, and only for the first half of stage 2, which is the design's own order:

1. **Go: measure the in-fight luck terms on a fresh 500-run copy-arm batch** (design 4.4: every state is at hand there; no change to the night driver).
   Stage 1 shows the method holds on this data (the correction has mean zero, the corrected mean is unbiased in the synthetic repeats, the second path
   agrees) but says nothing about the fights' draws themselves, which are the whole prize: stage 1 is worth about 6 in 100 fewer runs, and the design's
   30 to 50 in 100 needs stage 2 to deliver 25 to 45 in 100 on its own.
2. **No-go for changing the real arm's driver until that batch has a number.** Gate suggestion: the copy batch's in-fight terms alone remove at least 25 in 100.

What stage 1 also shows, as arithmetic from the copy pairs (assumes the two arms play a seed alike on average, which their mean floors support):
the correlation of the real and copy floors on a seed is 0.48, so about 48 in 100 of the floor variance is a function of the seed's content, and
this reading used 5.9 of those 48. The rest is seed content the game-log copies hold only partly (their reward lines appear to list the card offers; the map
layout is not in them, nor, as far as the lines read, the shop and relic offers), so a **stage 1b on the card offers** is a cheaper next lever
than a driver change (no fork change). Not built, not measured here: whether the copies list every offer completely is unchecked.

## 7. What was not done

- The copy-arm check of the correction's mean (the copy rows hold no encounter ids); stage 2; the card, relic and potion offers; the map.
- Odds by position in a pool (the k-th normal draw is near uniform over the pool but not exactly: chi-square 118 on about 66 degrees of freedom for the
  Act 1 Overgrowth normals across draw positions 1 to 7). A model of the game's exclusion rules (a weak encounter and its normal namesake) would sharpen
  the expectation a little; the boss draw, which carries the gain, is uniform within noise.
- Fixed-slope form: the plain AIVAT form (floor minus correction, no fit) has SEs within 1% of the fitted one on every rule night (beta 0.53 to 1.09), so
  the report could use it without a fit; the report keeps the fitted slope, as the control variate does.

## 8. To reproduce

    python tools/morning_report.py LAB/nightly/2026-11-04 --chance-read --out <scratch folder>      # the two tables above (chance_reading.md / .json)
    python tools/morning_report.py LAB/nightly/2026-11-04 --winlog none --out <scratch folder>      # the night's report with chance_table.json
    python tools/morning_report.py LAB/nightly/2026-11-04 --check                                    # 0 mismatches on all nine nights

Tests: `tests/test_night_chance.py` (20): by-hand table and terms, the known fit, the synthetic night where the boss alone decides the floor (corrected
SE under a tenth of the raw SE) and the night where nothing does (no change), 300 repeated nights (unbiased and tighter), no game logs reads "not measured",
the table rules, the CLI with no paths in its output, `--check` with a wrong figure caught.
