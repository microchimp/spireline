# The nightly exam's power: the nine nights read (2026-10-26 to 2026-11-04)

Written 2026-11-04 (housekeeping lane), item 3.5 of `docs/research/2026-11-04-train-and-test-ideas.md`. Source: `tools/morning_report.py`
run read-only on `LAB/nightly/<date>` for the nine dates, `--winlog none`, output to a scratch folder (nothing under `backlog/`). The
tool's `--check` second path recomputed every figure below that the tool prints (the control variate, the progress score, the older
headline figures): 9 nights, 92 to 95 figures each, 0 mismatches in all.
Counts are over ended runs (crash rows left out) unless a line says otherwise. No human data is used.

## 1. What was computed

The real arm and the copy arm play the same seeds each night, so every seed that ended on both arms is a pair (real floor, copy
floor). The control-variate estimate of the real arm's mean floor is

    theta = mean_real(pairs) - beta x (mean_copy(pairs) - mean_copy(all copy runs that ended))
    SE(theta)^2 = s_e^2 / n + beta^2 s_x^2 / N

with beta the least-squares slope of the real floor on the copy floor over the n pairs, s_e the residual SD of that fit, s_x^2 the
variance of the N copy floors, rho the pairs' correlation. With the copy mean known exactly the SE is s_e / sqrt(n), the raw SE
times sqrt(1 - rho^2): 1 - rho^2 is the share of the variance the adjustment can remove. "Beyond the pairs" below counts the copy
runs on seeds where the real run did not end (a crash, or not played); they are the only copy runs the pairs do not already hold.

## 2. Raw and adjusted real mean floor, nine nights

| night | gen | pairs | copy runs | beyond the pairs | sd of floors | raw mean (SE) | adjusted mean (SE) | moved by | rho | slope | 1 - rho^2 | SE, copy mean known | adjusted SE / raw SE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10-26 | 5 | 1,996 | 2,000 | 4 | 6.01 | 18.68 (0.135) | 18.68 (0.135) | +0.002 | 0.385 | 0.468 | 0.852 | 0.124 | 1.000 |
| 10-27 | 7 | 1,771 | 2,000 | 229 | 6.88 | 18.61 (0.163) | 18.61 (0.161) | -0.002 | 0.465 | 0.468 | 0.784 | 0.145 | 0.987 |
| 10-29 | 7 | 1,921 | 2,000 | 79 | 6.71 | 19.08 (0.153) | 19.11 (0.153) | +0.028 | 0.523 | 0.519 | 0.727 | 0.131 | 0.998 |
| 10-30 | 9 | 1,409 | 2,000 | 591 | 7.55 | 22.12 (0.201) | 22.14 (0.193) | +0.018 | 0.507 | 0.478 | 0.743 | 0.173 | 0.961 |
| 10-31 | 9 | 472 | 500 | 28 | 7.44 | 22.53 (0.342) | 22.46 (0.341) | -0.072 | 0.471 | 0.446 | 0.778 | 0.302 | 0.997 |
| 11-01 | 9 | 493 | 500 | 7 | 7.65 | 22.70 (0.344) | 22.72 (0.347) | +0.025 | 0.538 | 0.536 | 0.710 | 0.291 | 1.007 |
| 11-02 | 9 | 498 | 500 | 2 | 7.94 | 23.07 (0.356) | 23.07 (0.356) | -0.004 | 0.518 | 0.519 | 0.732 | 0.305 | 1.000 |
| 11-03 | 11 | 1,992 | 2,000 | 8 | 7.93 | 23.41 (0.178) | 23.41 (0.178) | +0.002 | 0.486 | 0.486 | 0.764 | 0.155 | 0.999 |
| 11-04 | 11 | 489 | 500 | 11 | 8.04 | 23.69 (0.363) | 23.65 (0.363) | -0.036 | 0.515 | 0.500 | 0.735 | 0.312 | 0.998 |

Pooled over the nine nights (11,041 pairs, Fisher z): rho 0.479, range 0.385 to 0.538; 1 - rho^2 = 0.770.

## 3. What the adjustment buys

- **As run today it buys nothing.** The adjusted mean moves by at most 0.072 floors and the adjusted SE is 0.961 to 1.007 times the raw SE.
  Every night's copy arm plays the same seeds as its real arm (500 and 500, 2,000 and 2,000), so the copy mean over the pairs is the copy
  mean over all and the correction term is zero. The two nights with many copy runs beyond the pairs (10-27: 229, 10-30: 591, from real crash rows and
  unplayed seeds) gain 1.3% and 3.9% of the SE.
- **The gain is there only with more copy runs than real runs.** At rho 0.48 the best case (copy mean known exactly) leaves 77% of the
  variance: 23 in 100 fewer real runs for the same SE (the memo's 25 at rho 0.5), but not at one copy run per real run. Copy runs beyond the pairs, per real run:

| copy runs beyond each pair (k) | variance left | real runs saved | SE ratio | machine time per real run, real plus copy arms (a real run = 1, copy cost ratio 0.55) | total machine time for the same SE, against no adjustment |
|---|---|---|---|---|---|
| 0 | 1.000 | 0.0% | 1.000 | 1.55 | 1.00 |
| 0.5 | 0.923 | 7.7% | 0.961 | 1.83 | 1.09 |
| 1 | 0.885 | 11.5% | 0.941 | 2.10 | 1.20 |
| 3 | 0.828 | 17.2% | 0.910 | 3.20 | 1.71 |
| 9 | 0.793 | 20.7% | 0.891 | 6.50 | 3.33 |
| all (copy mean known) | 0.770 | 23.0% | 0.878 | n/a | n/a |

  Cost ratio 0.55 is 11-04's: the copy arm's mean seconds per run over the real arm's (10-31 to 11-04: 0.51 to 0.69; 10-26 to 10-30: 0.29 to 0.58).
  Extra copy seeds cut the real (game) runs and raise the machine time unless a copy run costs under 0.30 of a real run (rho^2 / (1 - rho^2) at rho 0.48), so at today's ratio there is no net saving in machine time at any k.
- **The adjusted mean estimates the mean over all seeds** (the real runs that crashed or were not played are filled in through their copy runs), not the mean over ended runs.
  The shift is at most 0.072 floors in the nine nights, so the two readings agree today.

## 4. Real runs a night needs to see a change (80% power, two-sided 5%)

Two nights of fresh seed blocks and equal size compared unpaired (SE of the difference sqrt(2) sd / sqrt(n)); n = 2 x (2.8016 x sd / change)^2 x (share of variance left).
"As run" uses each night's own pairs-to-copy-runs ratio (= raw today); "copy mean known" is the limit 1 - rho^2.

| night | sd of floors | half floor: raw | half floor: adjusted as run | half floor: copy mean known | one floor: raw | one floor: adjusted as run | one floor: copy mean known |
|---|---|---|---|---|---|---|---|
| 10-26 | 6.01 | 2,266 | 2,266 | 1,931 | 567 | 567 | 483 |
| 10-27 | 6.88 | 2,971 | 2,898 | 2,329 | 743 | 725 | 583 |
| 10-29 | 6.71 | 2,831 | 2,801 | 2,058 | 708 | 701 | 515 |
| 10-30 | 7.55 | 3,579 | 3,307 | 2,658 | 895 | 827 | 665 |
| 10-31 | 7.44 | 3,472 | 3,428 | 2,700 | 868 | 857 | 675 |
| 11-01 | 7.65 | 3,674 | 3,660 | 2,609 | 919 | 915 | 653 |
| 11-02 | 7.94 | 3,957 | 3,953 | 2,896 | 990 | 989 | 724 |
| 11-03 | 7.93 | 3,949 | 3,945 | 3,017 | 988 | 987 | 755 |
| 11-04 | 8.04 | 4,057 | 4,033 | 2,983 | 1,015 | 1,009 | 746 |

Smallest change a night of n runs can see, two nights compared (rows) and a night against a reference with no error (last column):

| runs per night | sd 6 (October nights) | sd 8 (recent nights) | sd 8, copy mean known | sd 8 against a fixed reference |
|---|---|---|---|---|
| 500 | 1.06 | 1.42 | 1.24 | 1.00 |
| 1,000 | 0.75 | 1.00 | 0.88 | 0.71 |
| 2,000 | 0.53 | 0.71 | 0.62 | 0.50 |
| 4,000 | 0.38 | 0.50 | 0.44 | 0.35 |

On the recent nights (sd 8.04) a one-floor change needs about 1,015 runs a night and a half-floor change about 4,057; the adjustment as run
changes that by under 1% on 11-01 to 11-04. A 500-run night compared with the previous night sees about 1.4 floors, not half a floor. Several nights of one generation pooled
are the practical route (g9's four nights, 2,872 runs, SE 0.14 on the mean floor).

## 5. The progress score (nine nights)

Six measures per night, each with its SE (sqrt(p(1-p)/n) for rates in percentage points, sd/sqrt(n) for the floor). Differences are unpaired (fresh seed blocks), SE
the square root of the two variances' sum, z = difference/SE. "Previous night" is the previous folder (there is no 10-28); "previous generation" is every night of the
highest generation below the night's own, pooled. Boss measures of 10-26 are n/a: its real rows past floor 17 (550 of 550) carry no Act 1 boss entry, so the
boss was not recorded that night and a difference against it would be a difference against a missing figure, not against zero. Wins are 0 on every night (z n/a).

Values, SE in brackets:

| measure | 10-26 | 10-27 | 10-29 | 10-30 | 10-31 | 11-01 | 11-02 | 11-03 | 11-04 |
|---|---|---|---|---|---|---|---|---|---|
| generation | 5 | 7 | 7 | 9 | 9 | 9 | 9 | 11 | 11 |
| ended runs | 1,996 | 1,771 | 1,921 | 1,409 | 472 | 493 | 498 | 1,992 | 489 |
| mean floor | 18.68 (0.13) | 18.61 (0.16) | 19.08 (0.15) | 22.12 (0.20) | 22.53 (0.34) | 22.70 (0.34) | 23.07 (0.36) | 23.41 (0.18) | 23.69 (0.36) |
| Act 1 boss reached (of runs, points) | n/a (n/a) | 76.2 (1.0) | 80.9 (0.9) | 91.2 (0.8) | 91.7 (1.3) | 92.3 (1.2) | 91.8 (1.2) | 93.0 (0.6) | 92.4 (1.2) |
| Act 1 boss killed (of those reached, points) | n/a (n/a) | 37.2 (1.3) | 36.0 (1.2) | 51.3 (1.4) | 54.0 (2.4) | 52.3 (2.3) | 56.9 (2.3) | 56.5 (1.2) | 59.7 (2.3) |
| Act 2 boss reached (of runs, points) | n/a (n/a) | 7.8 (0.6) | 7.8 (0.6) | 19.2 (1.1) | 20.1 (1.8) | 20.7 (1.8) | 23.5 (1.9) | 24.0 (1.0) | 24.1 (1.9) |
| Act 2 boss killed (of those reached, points) | n/a (n/a) | 10.8 (2.6) | 12.0 (2.7) | 5.9 (1.4) | 10.5 (3.1) | 10.8 (3.1) | 10.3 (2.8) | 13.2 (1.5) | 13.6 (3.2) |
| wins (of runs, points) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) | 0.0 (0.0) |

Differences against the previous night, SE in brackets:

| measure | 10-26 | 10-27 | 10-29 | 10-30 | 10-31 | 11-01 | 11-02 | 11-03 | 11-04 |
|---|---|---|---|---|---|---|---|---|---|
| base (nights, runs) | none | 10-26, 1,996 | 10-27, 1,771 | 10-29, 1,921 | 10-30, 1,409 | 10-31, 472 | 11-01, 493 | 11-02, 498 | 11-03, 1,992 |
| mean floor | none | -0.07 (0.21) z -0.3 | +0.47 (0.22) z +2.1 | +3.04 (0.25) z +12.0 | +0.41 (0.40) z +1.0 | +0.17 (0.49) z +0.3 | +0.37 (0.50) z +0.8 | +0.33 (0.40) z +0.8 | +0.28 (0.40) z +0.7 |
| Act 1 boss reached (of runs, points) | none | n/a | +4.7 (1.4) z +3.5 | +10.3 (1.2) z +8.8 | +0.5 (1.5) z +0.4 | +0.6 (1.7) z +0.3 | -0.5 (1.7) z -0.3 | +1.2 (1.4) z +0.9 | -0.5 (1.3) z -0.4 |
| Act 1 boss killed (of those reached, points) | none | n/a | -1.2 (1.8) z -0.7 | +15.3 (1.9) z +8.3 | +2.8 (2.8) z +1.0 | -1.7 (3.3) z -0.5 | +4.6 (3.3) z +1.4 | -0.4 (2.6) z -0.2 | +3.3 (2.6) z +1.3 |
| Act 2 boss reached (of runs, points) | none | n/a | -0.0 (0.9) z -0.0 | +11.4 (1.2) z +9.4 | +0.9 (2.1) z +0.4 | +0.6 (2.6) z +0.2 | +2.8 (2.6) z +1.1 | +0.5 (2.1) z +0.2 | +0.1 (2.2) z +0.1 |
| Act 2 boss killed (of those reached, points) | none | n/a | +1.2 (3.7) z +0.3 | -6.1 (3.0) z -2.0 | +4.6 (3.5) z +1.3 | +0.3 (4.4) z +0.1 | -0.5 (4.2) z -0.1 | +2.9 (3.2) z +0.9 | +0.4 (3.5) z +0.1 |
| wins (of runs, points) | none | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a |

Differences against the previous generation pooled:

| measure | 10-26 | 10-27 | 10-29 | 10-30 | 10-31 | 11-01 | 11-02 | 11-03 | 11-04 |
|---|---|---|---|---|---|---|---|---|---|
| base (nights, runs) | none | 10-26, 1,996 | 10-26, 1,996 | 10-27+10-29, 3,692 | 10-27+10-29, 3,692 | 10-27+10-29, 3,692 | 10-27+10-29, 3,692 | 10-30+10-31+11-01+11-02, 2,872 | 10-30+10-31+11-01+11-02, 2,872 |
| mean floor | none | -0.07 (0.21) z -0.3 | +0.40 (0.20) z +2.0 | +3.27 (0.23) z +14.2 | +3.67 (0.36) z +10.2 | +3.84 (0.36) z +10.6 | +4.22 (0.37) z +11.3 | +0.95 (0.23) z +4.2 | +1.24 (0.39) z +3.2 |
| Act 1 boss reached (of runs, points) | none | n/a | n/a | +12.5 (1.0) z +12.4 | +13.1 (1.4) z +9.1 | +13.6 (1.4) z +9.9 | +13.1 (1.4) z +9.3 | +1.4 (0.8) z +1.8 | +0.9 (1.3) z +0.7 |
| Act 1 boss killed (of those reached, points) | none | n/a | n/a | +14.7 (1.7) z +8.9 | +17.5 (2.6) z +6.8 | +15.8 (2.5) z +6.3 | +20.4 (2.5) z +8.2 | +3.6 (1.5) z +2.4 | +6.8 (2.5) z +2.7 |
| Act 2 boss reached (of runs, points) | none | n/a | n/a | +11.4 (1.1) z +10.0 | +12.3 (1.9) z +6.5 | +12.9 (1.9) z +6.9 | +15.7 (2.0) z +8.0 | +3.6 (1.2) z +3.0 | +3.8 (2.1) z +1.8 |
| Act 2 boss killed (of those reached, points) | none | n/a | n/a | -5.5 (2.4) z -2.3 | -0.9 (3.7) z -0.2 | -0.6 (3.6) z -0.2 | -1.2 (3.4) z -0.3 | +4.8 (1.9) z +2.5 | +5.2 (3.4) z +1.5 |
| wins (of runs, points) | none | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a | +0.0 (0.0) z n/a |

The nights compared back to back have an SE of the mean-floor difference of 0.21 to 0.50 floors (11-01 and 11-02, a 500-run night against a 500-run night: 0.49 and 0.50).

## 6. Fight-quality measures per fight kind in the real arm: not recorded

Checked the 2026-11-04 real-arm rows (`runs.jsonl`), the copy-arm rows, and the game-log copies (`logs/w5-night-<date>-stdout`, present for 10-29 to 11-04).
- Real-arm row fields: ev, w, seed, character, end, floor, asked, s, stats (decisions, ranked, diverged, gaps, re-anchor counters, first_loss, losses),
  lost, divergences, agent_seed, assumed, boss_damage, boss_damage_acts, cards, nodes, rests, t_end, restarts, boot_s, streak; crash rows add where and error.
  Copy-arm rows: seed, ix, win, floor, end, decisions, wall, ai_state_assumed, crash, combat_decisions, sims, config, generation, character, prior_path, prior_calls, boss_damage, boss_damage_acts, cards, nodes, rests.
  None holds the player's HP, energy, block or a fight's damage; `boss_damage` is the share of the boss's HP removed, not the player's HP.
- Game logs (24,640 lines in the first worker log of 11-04): card plays by name, enemy moves by name, kills, wins and the encounter id of each combat room, rewards, potion uses, run decisions.
  No HP, energy spent, block or damage number appears (the "block" and "energy" hits are potion and enemy-move names).
- Missing: HP at fight start and end (damage taken per hallway fight), energy spent per fight and damage dealt per fight (damage per energy), block gained and block lost at turn end (wasted block); also the fight kind per
  record (it can be taken from the encounter id's suffix as `morning_report.py` already does for the survival table).
- Where they come from: the referee's observation at every combat decision holds the player's hp, max_hp, block and energy, each hand card's cost, and the enemies' hp and block
  (`referee/driver/Combat.cs`; `referee/lockstep.py` reads it at each decision). `rl/run_fields.RunFields` keeps only the boss fight's enemy HP. A per-fight record added there
  (kind, HP at the first and last combat decision, energy spent = costs of the cards played, damage dealt = fall of the enemies' HP total, block left at each end of turn), written into the row
  by `envproto.py` beside the other run fields, gives all three measures; `gen0.play_emu_run` would write the same on the copy arm for a comparison. Both are fork changes (not made today).
- Crude proxies the game-log copy already gives without any change: cards played per fight and enemy moves per fight (a turn count), by encounter id. They are not the three measures.

## 7. Leads, and what was not done

- The control variate needs a covariate that is cheap and better correlated than the copy arm (rho 0.48, cost ratio 0.55): the run head's value at each floor (the memo's AIVAT-style baseline on run outcomes) is the next candidate. Not built.
- Extra copy seeds beyond the real arm's would raise the real-run saving to 17% at three per pair; not run, since the machine time rises (section 3).
- Pooling the nights of a generation is the cheap way to a half-floor reading: the tool prints the previous-generation comparison with SE and z every morning.
- Not done: the fight-quality fields (fork change), a composite metric (floor, HP at the boss doors, boss kills; HP at the boss doors is not recorded), the value baseline on run outcomes.
