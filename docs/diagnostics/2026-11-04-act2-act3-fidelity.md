# Act 2 and Act 3: how far the copy can be trusted, nine nights read (2026-10-26 to 2026-11-04)

Written 2026-11-04 11:22Z (Act 2 and 3 fidelity worker). Read-only: `LAB/nightly/<date>/<agent>` (`runs.jsonl`, `divergences.jsonl`, `summary.json`, `compare.json`) and the sibling `<agent>-emu` folder (the copy arm) for the nine dates, plus the fork's `git log` and the diagnosis notes named in section 8. No game or copy was run. Aggregates only; the seeds quoted are the nightly blocks' own seed strings. D38 (`docs/DECISIONS.md`) admitted Act 3 as "barely verified" and the fight exam and the practice are being extended into Act 2; this note puts numbers on both.

## 0. The numbers in five lines

1. **Rate.** The real game and the copy disagree on the state at 1.9, 9.3 and 15.5 in every 1,000 decisions in Act 1, Act 2 and Act 3 (nine nights pooled: 2,631, 3,478 and 175 records in about 1,369k, 375k and 11k decisions; Act 2 interval 8.8 to 9.7). On the last three nights, after the 10-30 fixes, it is 0.6, 6.5 and 15.3: Act 2 is 11 times Act 1, and between the first and the last night Act 1 fell 5.1-fold and Act 2 3.1-fold, with Act 2 flat from 10-31 on. Decisions per act are modelled (section 1); the record counts are exact.
2. **Reach.** 43% of the runs that enter Act 2 have at least one state disagreement in it (Act 1 18%, Act 3 57%; last three nights 7%, 34%, 60%). 8.1% of Act 2 decisions and 16.3% of Act 3 decisions were not compared at all because the copy was out of step and not yet reset (Act 1 1.3%).
3. **Whole runs.** On the same seeds the AI gets about as far on the copy as on the real game: last three nights, floor real minus copy +0.17 (SE 0.15, 2,979 pairs); reaches Act 2 52.9% against 51.4%; kills the Act 2 boss 12.8% (91 of 713) against 11.5% (82 of 715) of the fights that reach it. Nothing is outside noise, and the noise is about +-5 points on a boss kill, so this check cannot see a small Act 2 error; the lockstep can.
4. **Mechanisms.** Of 3,976 Act 2 and 3 records, three fixed mechanisms (the Ember enchantment's damage, the Decimillipede's HP, the Kaiser Crab's facing; fork commits of 10-30) account for 448 and went from 435 on the four earlier nights to 13 on the five later ones. The rest is open, and the biggest open groups are in the fight itself: a hand where one side holds the other's whole hand plus cards, the shape the D11C diagnosis of 10-27 traced to relic counters and enchantments (340 on the last three nights, 2.2 per 1,000 decisions in Acts 2 and 3 against 0.02 in Act 1), a long tail of enemy-HP differences (151), then the fight-reward screen (deck, relics: 167) and the Crystal Sphere event, which the lockstep cannot mirror at all (214 records, 1,916 decisions left unscored).
5. **Act 3 is measured, not verified.** 169 of 11,041 real runs (1.5%) reached it: 1,331 floors, about 11,258 decisions, 20 boss fights (3 won), no run won in nine nights. Its disagreement rate is the highest of the three acts and the sample is too small to give one number per enemy, event or relic.

## 1. What was read, and what is modelled

- **Two instruments.** (a) The lockstep: while the real game plays a run, the copy is stepped through the same choices and the two states (deck, relics, gold, HP, potions, in a fight the hand and the enemies' HP) are compared at every decision the game asks. A difference is a *record*; a record with `gap` set is a step or screen the copy cannot mirror, not a state difference. After a difference the lockstep tries to **re-anchor** (set the copy to the game's state) at the next fight start or map screen; until it holds, later decisions are **not compared** (that run of decisions is a *stretch* below). (b) The whole-run check: the copy arm plays the same seeds on its own, and the two arms' floors, Act 2 reach and boss kills are paired.
- **Acts by floor.** Act 1 is floors 1-17 (boss on 17), Act 2 floors 18-33 (boss on 33), Act 3 floors 34-49 (`rl/run_fields.py` ACT_BOSS_FLOORS 17, 33, 48; a win can record 49). A record's act is its `floor`.
- **Exact:** runs that reached each act (final floor), every record by floor and screen kind, re-anchor outcomes at a record, how many records begin a lost stretch and whether it was resumed (the sums over runs match the summary files: 11,041 ended runs, 1,755,994 decisions, 6,852 end-row records, 5,453 re-anchors held and 439 failed; the 63 crash rows and their 11 records are left out), card-reward and rest-site decisions by act (the rows keep `cards` and `rests` with floors).
- **Modelled:** decisions per act. The rows keep only a run's total decisions, not their floors. Fitting total decisions on the floors passed in each act over all 11,041 runs gives 7.65, 7.60 and 8.49 decisions per floor in Acts 1, 2 and 3 (residual SD 25 decisions a run), and each night's act figures are scaled to that night's exact total. Check on the data: runs that died on Act 1's boss floor (17) had played 128.3 decisions on average (5,195 runs), those that died on Act 2's boss floor (33) 248.6 (1,426 runs), those on floor 48 382.2 (21 runs): 7.5 decisions a floor across Act 2 and 8.9 across Act 3, against 7.6 and 8.5 fitted. The Act 3 coefficient is the least certain (169 runs). The decisions not compared are attributed to the act of the record that started the stretch (a stretch that runs to the run's end is split over the floors it covers). Intervals are 95% from resampling runs.
- **Not recorded at all** for the real arm: decisions by kind, by floor or by act. So a rate per kind is given only for card rewards and rest sites, whose decisions the rows do list; for fight moves, maps, shops, events and potions only counts are given (section 4).
- **Nights.** Nine folders, dated by the lab's local day (10-28 had no block). Agents: g5 (10-26), g7 (10-27, 10-29), g9 (10-30 to 11-02), g11 (11-03, 11-04); each generation reaches different content, and nothing here adjusts for that. Builds: the 10-26 and 10-27 blocks (played 10-25 and 10-28 UTC) predate the week-5 gate bundle (landed 10-28 11:13Z); 10-29 and 10-30 hold it; 10-31 to 11-04 also hold the three fix batches of 10-30 (batch A 11:46Z: Ember, Decimillipede, Matriarch, comparer HP bound; batch B 20:02Z: gold, rest site, map floor, event after death, Neow's Bones, Charge; batch C 23:31Z: Kaiser Crab facing, stuns). "Before" below means the first four nights, "after" the last five, "last three" 11-02, 11-03, 11-04.
- **Runs the driver stopped.** 151 runs on 10-26 and 10-27 ended at an empty treasure chest (`treasure_without_relic_picking`, fixed on 10-28 by `8a90b05d`) and 25 runs on 10-29, 10-30 and 11-03 ended as `fight_unfinished`; they are in the counts as ended runs and shorten the early nights' reach.
- **Records are not independent errors.** One unresolved difference can be re-detected at every later fight (50 runs carry 111 records of the Strike-and-gold group below), so the runs column is the more conservative count.

## 2. The nine nights

| night | agent | played (UTC) | runs / crash rows | reached Act 2 / Act 3 | decisions | state records A1 / A2 / A3 | gap records A1 / A2 / A3 | per 1,000 decisions A1 / A2 / A3 | Act 2 / Act 1 | re-anchors held / failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10-26 | g5 | 10-25 ~17:30-20:38 | 1,996 / 4 | 550 / 8 | 286,748 | 661 / 811 / 10 | 97 / 38 / 2 | 2.68 / 20.49 / 16.72 | 7.6 | 1,305 / 57 |
| 10-27 | g7 | 10-28 01:03-07:23 | 1,771 / 1 | 502 / 15 | 253,412 | 851 / 512 / 18 | 67 / 36 / 1 | 4.01 / 12.56 / 26.34 | 3.1 | 1,168 / 102 |
| 10-29 | g7 | 10-29 05:26-07:31 | 1,921 / 7 | 559 / 18 | 285,216 | 523 / 378 / 19 | 43 / 51 / 1 | 2.20 / 8.21 / 15.70 | 3.7 | 751 / 127 |
| 10-30 | g9 | 10-30 05:04-07:32 | 1,409 / 22 | 659 / 16 | 237,262 | 293 / 530 / 11 | 13 / 34 / 3 | 1.66 / 8.89 / 11.31 | 5.4 | 658 / 69 |
| 10-31 | g9 | 10-31 03:56-04:27 | 472 / 1 | 234 / 10 | 80,239 | 41 / 153 / 7 | 4 / 15 / 0 | 0.69 / 7.42 / 13.69 | 10.7 | 186 / 8 |
| 11-01 | g9 | 11-01 02:23-02:56 | 493 / 7 | 238 / 11 | 84,699 | 39 / 134 / 9 | 6 / 16 / 1 | 0.63 / 6.07 / 13.21 | 9.6 | 180 / 10 |
| 11-02 | g9 | 11-01 23:26-23:58 | 498 / 2 | 260 / 12 | 87,074 | 32 / 157 / 12 | 8 / 25 / 1 | 0.51 / 6.56 / 13.98 | 12.8 | 193 / 10 |
| 11-03 | g11 | 11-02 21:30 to 11-03 00:18 | 1,992 / 8 | 1,046 / 63 | 353,637 | 159 / 637 / 65 | 7 / 74 / 9 | 0.63 / 6.52 / 14.06 | 10.3 | 808 / 42 |
| 11-04 | g11 | 11-03 21:08-21:54 | 489 / 11 | 270 / 16 | 87,707 | 32 / 166 / 24 | 0 / 15 / 1 | 0.52 / 6.58 / 21.46 | 12.6 | 204 / 14 |
| **pooled** |  |  | 11,041 / 63 | 4,318 / 169 | 1,755,994 | 2,631 / 3,478 / 175 | 245 / 304 / 19 | 1.92 / 9.26 / 15.54 | 4.8 | 5,453 / 439 |
| **last three** |  |  | 2,979 | 1,576 / 91 | 528,418 | 223 / 960 / 101 | 15 / 114 / 11 | 0.59 / 6.54 / 15.30 | 11.0 | 1,205 / 66 |

Rates use the modelled decisions per act. The state records of each night sum to its `diverged_decisions` and the gap records to its `gaps` (checked on all nine). Act 1 fell from 2.68 to 0.52 per 1,000 between the first and last night and Act 2 from 20.5 to 6.6, but from 10-31 on Act 2 sits between 6.1 and 7.4 on every night (and Act 3 between 13 and 21 on tens of records a night), while Act 1 sits between 0.5 and 0.7.

## 3. By act: pooled and the last three nights

|  | Act 1 pooled | Act 2 pooled | Act 3 pooled | Act 1 last 3 | Act 2 last 3 | Act 3 last 3 |
| --- | --- | --- | --- | --- | --- | --- |
| runs that reached the act | 11,041 | 4,318 | 169 | 2,979 | 1,576 | 91 |
| decisions (modelled) | 1,369,251 | 375,486 | 11,258 | 374,999 | 146,818 | 6,601 |
| decisions not compared (share) | 18,047 (1.3%) | 30,532 (8.1%) | 1,837 (16.3%) | 1,317 (0.4%) | 7,793 (5.3%) | 853 (12.9%) |
| state records | 2,631 | 3,478 | 175 | 223 | 960 | 101 |
| gap records (step or screen the copy cannot mirror) | 245 | 304 | 19 | 15 | 114 | 11 |
| state records per 1,000 decisions | 1.92 | 9.26 | 15.54 | 0.59 | 6.54 | 15.30 |
| ... 95% interval (runs resampled) | 1.83 to 2.02 | 8.82 to 9.65 | 12.85 to 18.14 | 0.52 to 0.67 | 5.98 to 7.13 | 12.44 to 18.61 |
| state records per 1,000 decisions that were compared | 1.95 | 10.08 | 18.58 | 0.60 | 6.91 | 17.57 |
| runs with at least one state record in the act (share of runs that reached it) | 1,979 (17.9%) | 1,855 (43.0%) | 96 (56.8%) | 195 (6.5%) | 536 (34.0%) | 55 (60.4%) |
| re-anchor tried at the record: tried / held | 499 / 470 (94%) | 868 / 702 (81%) | 66 / 58 (88%) | 6 / 6 (100%) | 271 / 245 (90%) | 36 / 35 (97%) |
| not re-anchored at once: stretches begun | 2,406 | 3,080 | 136 | 232 | 829 | 77 |
| ... resumed later (share) | 1,875 (78%) | 2,253 (73%) | 95 (70%) | 212 (91%) | 644 (78%) | 63 (82%) |
| ... still not compared when the run ended | 531 | 827 | 41 | 20 | 185 | 14 |
| failed re-anchor attempts while waiting to resume (estimated by stretch) | 103 | 112 | 22 | 6 | 28 | 6 |
| re-anchors held / failed, all attempts (failed share) | 2,345 / 132 (5.3%) | 2,955 / 278 (8.6%) | 153 / 30 (16.2%) | 218 / 6 (2.5%) | 889 / 54 (5.7%) | 98 / 7 (6.3%) |

A re-anchor can be tried only at a fight start or a map screen, so a stretch begun elsewhere waits for the next one; every held re-anchor either followed a record at once ("held" in the tried row) or ended a stretch ("resumed"). The totals are exact (5,453 held, 1,230 at a record and 4,223 resumes; 439 failed, 203 at a record and 236 while waiting); only the split of the 236 waiting failures over the acts is estimated (by the act of the stretch they belong to; split pro rata where a run has stretches in two acts). The Act 3 re-anchor counts are small.

Why the 439 failed re-anchors failed (the summaries keep the reason per night, not per act):

| reason | pooled | 10-26 | 10-27 | 10-29 | 10-30 | 10-31 | 11-01 | 11-02 | 11-03 | 11-04 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no emulator id for the Decimillipede segment names (Act 2 fights) | 207 | 20 | 43 | 50 | 44 | 4 | 5 | 6 | 23 | 12 |
| state still differs after the anchor: gold | 90 | 2 | 35 | 49 | 4 | 0 | 0 | 0 | 0 | 0 |
| state still differs after the anchor: potions | 40 | 10 | 4 | 4 | 9 | 2 | 0 | 1 | 9 | 1 |
| state still differs after the anchor: deck | 34 | 2 | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| the walk to the map failed | 30 | 18 | 0 | 0 | 1 | 0 | 3 | 3 | 5 | 0 |
| state still differs after the anchor: relics | 18 | 3 | 3 | 2 | 2 | 1 | 1 | 0 | 5 | 1 |
| other (a named enemy the copy lacks, floor offset, mixed fields) | 20 | 2 | 1 | 6 | 9 | 1 | 1 | 0 | 0 | 0 |
| **all failed** | 439 | 57 | 102 | 127 | 69 | 8 | 10 | 10 | 42 | 14 |

The gold and deck failures went to zero after batch B (124 on the four earlier nights, 0 on the five later). The Decimillipede one is the single largest cause of a re-anchor failing (207 of 439, 47%): 22 per 1,000 runs on the four earlier nights, 13 on the five later (23 of 42 on 11-03, 12 of 14 on 11-04), and it occurs only on Decimillipede fights, which are Act 2 fights; the fight stays out of step after it. Batch A fixed that fight's HP rule, not its anchor. The `.potions` failures (40) are still there on 11-03.

## 4. By decision kind

A record's kind is the screen the game was asking about when the difference showed (`type`); the cause is often the step before it (a fight ends on a card play and the difference shows at the reward screen). Cells are state records / gap records. Fight move = `combat` and `select_cards_combat` (a card pick inside a fight). Event includes the Ancient's pick and the Crystal Sphere event; "fight reward screen" is the screen after a won fight (gold, relic, potion and card rewards); "deck pick" is the transform / remove / upgrade selection screens and the bundle screen.

| kind | Act 1 pooled | Act 2 pooled | Act 3 pooled | Act 1 last 3 | Act 2 last 3 | Act 3 last 3 |
| --- | --- | --- | --- | --- | --- | --- |
| fight move | 1,094 / 113 | 2,355 / 63 | 126 / 3 | 79 / 8 | 602 / 15 | 76 / 2 |
| card reward | 349 / 62 | 0 / 24 | 0 / 0 | 82 / 6 | 0 / 15 | 0 / 0 |
| map | 376 / 0 | 276 / 2 | 23 / 0 | 2 / 0 | 99 / 0 | 11 / 0 |
| rest site | 47 / 0 | 33 / 0 | 3 / 0 | 0 / 0 | 9 / 0 | 1 / 0 |
| shop | 16 / 4 | 37 / 3 | 2 / 0 | 3 / 0 | 11 / 1 | 2 / 0 |
| event | 116 / 0 | 109 / 210 | 3 / 16 | 2 / 0 | 22 / 83 | 1 / 9 |
| fight reward screen | 210 / 0 | 572 / 0 | 15 / 0 | 37 / 0 | 196 / 0 | 10 / 0 |
| deck pick | 351 / 66 | 52 / 2 | 3 / 0 | 4 / 1 | 5 / 0 | 0 / 0 |
| treasure | 72 / 0 | 44 / 0 | 0 / 0 | 14 / 0 | 16 / 0 | 0 / 0 |
| **all kinds** | 2,631 / 245 | 3,478 / 304 | 175 / 19 | 223 / 15 | 960 / 114 | 101 / 11 |
| memo: potion (last step a potion, or the first difference is `.potions`; overlaps the rows above) | 371 / 3 | 84 / 7 | 8 / 0 | 88 / 0 | 23 / 4 | 7 / 0 |

The kinds whose decisions the rows list, with exact denominators:

| kind |  | Act 1 pooled | Act 2 pooled | Act 3 pooled | Act 1 last 3 | Act 2 last 3 | Act 3 last 3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| card reward | decisions (taken + skipped) | 74,647 | 19,539 | 482 | 20,510 | 7,600 | 283 |
|  | state records per 1,000 | 4.68 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 |
| rest site | decisions (leaving not recorded) | 32,726 | 6,955 | 120 | 9,381 | 2,920 | 75 |
|  | state records per 1,000 | 1.44 | 4.74 | 25.00 | 0.00 | 3.08 | 13.33 |

Card rewards never differ in state in Acts 2 and 3 (the Act 1 records are the first-floor Neow potion, `.potions`: 81 of the 82 on the last three nights); the card-reward gap records in Act 2 are an option the copy lacks ("NOT_YET" on a reward screen). Rest sites differ 3.3 times as often per decision in Act 2 as in Act 1 pooled (4.7 against 1.4 per 1,000); the Act 3 figure rests on 3 records.

Per night, state plus gap records by kind, as Act 1 / Act 2 / Act 3:

| night | fight move | card reward | map | rest site | shop | event | fight reward screen | deck pick | treasure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10-26 | 329 / 532 / 5 | 161 / 1 / 0 | 84 / 54 / 1 | 1 / 3 / 2 | 3 / 2 / 0 | 33 / 52 / 3 | 47 / 196 / 1 | 90 / 7 / 0 | 10 / 2 / 0 |
| 10-27 | 389 / 381 / 9 | 35 / 2 / 0 | 78 / 30 / 4 | 22 / 10 / 0 | 4 / 3 / 0 | 30 / 53 / 1 | 62 / 21 / 2 | 290 / 40 / 3 | 8 / 8 / 0 |
| 10-29 | 216 / 306 / 17 | 46 / 1 / 0 | 144 / 22 / 2 | 24 / 6 / 0 | 6 / 9 / 0 | 37 / 55 / 1 | 39 / 22 / 0 | 31 / 1 / 0 | 23 / 7 / 0 |
| 10-30 | 153 / 382 / 9 | 43 / 2 / 0 | 67 / 48 / 2 | 0 / 4 / 0 | 1 / 5 / 0 | 13 / 28 / 3 | 17 / 89 / 0 | 1 / 1 / 0 | 11 / 5 / 0 |
| 10-31 | 17 / 109 / 5 | 17 / 1 / 0 | 1 / 14 / 1 | 0 / 1 / 0 | 3 / 6 / 0 | 0 / 8 / 0 | 6 / 25 / 1 | 0 / 0 / 0 | 1 / 4 / 0 |
| 11-01 | 16 / 91 / 6 | 21 / 2 / 0 | 0 / 11 / 2 | 0 / 0 / 0 | 0 / 3 / 0 | 1 / 18 / 1 | 2 / 23 / 1 | 0 / 0 / 0 | 5 / 2 / 0 |
| 11-02 | 17 / 95 / 10 | 15 / 1 / 0 | 1 / 15 / 1 | 0 / 2 / 0 | 2 / 1 / 0 | 0 / 26 / 2 | 3 / 39 / 0 | 0 / 1 / 0 | 2 / 2 / 0 |
| 11-03 | 57 / 422 / 46 | 60 / 12 / 0 | 1 / 64 / 8 | 0 / 5 / 1 | 1 / 7 / 2 | 2 / 64 / 7 | 30 / 122 / 10 | 4 / 3 / 0 | 11 / 12 / 0 |
| 11-04 | 13 / 100 / 22 | 13 / 2 / 0 | 0 / 20 / 2 | 0 / 2 / 0 | 0 / 4 / 0 | 0 / 15 / 1 | 4 / 35 / 0 | 1 / 1 / 0 | 1 / 2 / 0 |

## 5. Whole runs: the real game against the copy arm, same seeds

Floor gap is real minus copy (`compare.json` stores copy minus real, and counts a crashed real run as floor 0; here crash rows are left out of both). Reaching Act 2 means final floor 18 or more, the Act 2 boss floor 33, Act 3 floor 34 or more. "Either reached" pairs are those where the real or the copy run reached the act; restricting to the real run reaching it would add its selection effect to the gap (+3.8 floors pooled, by construction), so that figure is not used.

| night | pairs | mean floor real / copy | gap real - copy (SE) | reach Act 2 real / copy | Act 2 boss floor reached, of Act 2 entrants real / copy | Act 2 boss killed, of fights real / copy | gap, either reached Act 2 (n) | reach Act 3 real / copy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10-26 | 1,996 | 18.68 / 17.38 | +1.31 (0.14) | 27.6% / 13.3% | 22.7% / 27.3% | 0 of 0 / 1 of 73 | +3.83 (654) | 8 / 1 |
| 10-27 | 1,771 | 18.61 / 19.54 | -0.93 (0.17) | 28.3% / 31.1% | 27.7% / 32.2% | 15 of 139 / 21 of 198 | -1.46 (743) | 15 / 24 |
| 10-29 | 1,921 | 19.08 / 19.31 | -0.18 (0.15) | 29.1% / 29.1% | 26.8% / 30.3% | 18 of 150 / 23 of 175 | -0.29 (772) | 18 / 24 |
| 10-30 | 1,409 | 22.12 / 22.51 | -0.35 (0.21) | 46.8% / 46.5% | 41.1% / 48.4% | 16 of 271 / 42 of 450 | -0.69 (833) | 16 / 44 |
| 10-31 | 472 | 22.53 / 22.16 | +0.20 (0.36) | 49.6% / 45.4% | 40.6% / 44.5% | 10 of 95 / 11 of 101 | +0.33 (290) | 10 / 12 |
| 11-01 | 493 | 22.70 / 22.63 | +0.12 (0.33) | 48.3% / 46.6% | 42.9% / 45.5% | 11 of 102 / 11 of 106 | +0.22 (289) | 11 / 12 |
| 11-02 | 498 | 23.07 / 22.68 | +0.38 (0.35) | 52.2% / 47.2% | 45.0% / 47.0% | 12 of 117 / 11 of 111 | +0.66 (311) | 12 / 11 |
| 11-03 | 1,992 | 23.41 / 23.40 | +0.02 (0.18) | 52.5% / 52.5% | 45.7% / 46.5% | 63 of 478 / 57 of 486 | +0.00 (1,308) | 63 / 57 |
| 11-04 | 489 | 23.69 / 23.05 | +0.57 (0.36) | 55.2% / 51.4% | 43.7% / 45.9% | 16 of 118 / 14 of 118 | +0.78 (322) | 16 / 15 |
| **pooled** | 11,041 | 20.79 / 20.79 | +0.07 (0.07) | 39.1% / 36.7% | 36.9% / 41.4% | 161 of 1,470 / 191 of 1,818 | +0.23 (5,522) | 169 / 200 |
| **last three** | 2,979 | 23.40 / 23.22 | +0.17 (0.15) | 52.9% / 51.4% | 45.2% / 46.5% | 91 of 713 / 82 of 715 | +0.24 (1,941) | 91 / 83 |

The gap among pairs where either run reached Act 3 is -1.25 floors over 304 pairs pooled (SE 0.93) and +0.43 over 152 on the last three nights (SE 1.31). Among pairs where both runs reached Act 2 the gap is -0.35 (SE 0.09, 2,795 pairs) pooled and -0.11 (0.15, 1,167) on the last three nights; both reached Act 3: -0.70 (0.51, 44) and -0.29 (0.83, 21) (a selection that treats the two arms alike: if they were the same game the expected gap in it is zero). Floors past 17 summed over all pairs: pooled +0.14 (SE 0.06), last three +0.13 (0.14); past 33: -0.01 (0.01), +0.03 (0.04). The early nights are a different story (10-26: +1.31, with Act 2 reached by 27.6% of real runs and 13.3% of copy runs; 10-27: -0.93); from 10-31 every night's gap is between +0.02 and +0.57. At the sizes involved (about 700 Act 2 boss fights a side on the last three nights) a boss-kill difference under about 5 points is invisible here.

## 6. Is Act 3 verified?

|  | Act 2 | Act 3 |
| --- | --- | --- |
| real runs that reached the act (nine nights) | 4,318 | 169 |
| ... as a share of all real runs | 39.1% | 1.5% |
| floors played in the act (sum over runs) | 49,503 | 1,331 |
| decisions (modelled) | 375,486 | 11,258 |
| state records (rate per 1,000) | 3,478 (9.3) | 175 (15.5, 12.8 to 18.1) |
| runs with a state record | 43% | 57% |
| decisions not compared | 8.1% | 16.3% |
| boss fights reached / won (real arm) | 1,470 / 161 | 20 / 3 |
| boss fights reached / won (copy arm) | 1,818 / 191 | 28 / 10 |
| runs that won the game (real / copy) | 0 / 0 | 0 / 0 |

Act 3 runs end at floor 35 to 49 (median 40; 90 reached floor 40, 41 reached 45, 22 reached the boss floors 48-49), and the real arm fought the Act 3 boss floor 20 times (3 won). The 194 Act 3 records (105 runs) are mostly the Act 2 groups again: count-shaped hands 51, enemy HP long tail 48, Crystal Sphere 16, the Ancient's screen after a card pick 13, Fake Merchant phase 9; their fight records name 18 encounters, two of which (Devoted Sculptor 26, Living Shield + Turret Operator 24) hold 50 of the 117, and without per-encounter visit counts it cannot be said whether those two are error-prone or only common. The record rate is the highest of the three acts, over half the Act 3 runs have a disagreement, and one decision in six is not compared. **Answer: Act 3 is measured, not verified.** Its sample is about one twenty-sixth of Act 2's in runs and one thirty-seventh in floors, the winning path (the last floor, the victory screen) has no run at all, and the D38 wording stands. The larger Act 3 sample is the recorded human runs the Codex walker replays (section 8: 1,233 recorded runs that ended in Act 3), not the nightly blocks.

## 7. Mechanisms: the top fifteen groups in Acts 2 and 3

A group is the screen where the difference showed, the first differing field and the entity involved (enemy, card, relic or event), with a few signature rules: the Ember rule (a Strike's hit leaves one enemy 1 to 4 HP higher on the copy), the Decimillipede and Kaiser Crab (Crusher + Rocket) rosters, a Strike-and-gold shape at the reward screen. The record carries the first differing field and the two values, not the cause, so a group is a description. Status: **fixed** = a fork commit names the mechanism and the group fell by more than 90% on the later nights; **open** = anything else. 75 groups cover 3,976 records (Act 2 3,782, Act 3 194). Columns: records pooled, then split before (4 nights, 10-26 to 10-30) / after (5 nights, 10-31 to 11-04) / last three; runs = distinct runs; unscored = decisions not compared after the group's records; A1 last 3 = the same group's records in Act 1 on the last three nights (Act 1 had 2.55 times as many decisions there). Per-1,000 figures in the text use Acts 2 and 3 together as the denominator.

| # | group (what the record says) | records (A2 / A3) | before / after / last 3 | runs | unscored | A1 last 3 | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hand: one side holds the other's whole hand plus 1 or more cards (a count difference) (`F-handcount`) | 830 (779 / 51) | 404 / 426 / 340 | 463 | 7,202 | 6 | open (D11C shape; D11F1, D11F2 did not remove it) |
| 2 | enemy HP differs, other encounters (long tail) (`F-ehp-other`) | 536 (488 / 48) | 344 / 192 / 151 | 421 | 6,616 | 26 | open (long tail, no single mechanism) |
| 3 | fight reward screen: game's deck holds a card the copy lacks (not the Strike signature) (`R-deck-game-extra`) | 267 (267 / 0) | 203 / 64 / 51 | 226 | 973 | 0 | open |
| 4 | enemy HP: a Strike's hit leaves the copy's enemy 1-4 HP higher (signature of the Ember enchantment) (`F-ehp-ember`) | 254 (254 / 0) | 252 / 2 / 2 | 95 | 3,685 | 1 | **fixed** `5a6fcb3a` |
| 5 | Crystal Sphere screen has no mapping in the lockstep (gap) (`GAP-crystal`) | 214 (198 / 16) | 102 / 112 / 92 | 214 | 1,916 | 0 | open (screen unmapped) |
| 6 | player HP differs in a fight, other encounters (`F-hp-other`) | 163 (155 / 8) | 102 / 61 / 45 | 126 | 1,756 | 15 | open |
| 7 | hand: hand differs in which cards right after a card play (a swap) (`F-handswap-play`) | 158 (153 / 5) | 105 / 53 / 32 | 134 | 2,008 | 23 | open |
| 8 | enemy HP: Decimillipede segments hold different HP (`F-ehp-deci`) | 111 (111 / 0) | 103 / 8 / 8 | 111 | 1,522 | 0 | **fixed** `59c7050d` |
| 9 | fight reward screen: game's deck holds one more upgraded Strike and its gold is lower (`R-deck-strike`) | 111 (111 / 0) | 38 / 73 / 64 | 50 | 429 | 0 | open (new since 10-30) |
| 10 | map decision after an Act ancient's pick: game holds relics the copy lacks (`M-relics`) | 104 (101 / 3) | 41 / 63 / 47 | 103 | 0 | 0 | open |
| 11 | hand: opening hand differs in which cards (a swap) (`F-handswap-open`) | 96 (95 / 1) | 74 / 22 / 16 | 76 | 15 | 4 | open (fell 74 to 22) |
| 12 | fight begins while the copy is in the Fake Merchant phase (reason phase:13) (`S-phase13`) | 85 (76 / 9) | 40 / 45 / 29 | 85 | 81 | 0 | open |
| 13 | player HP: Kaiser Crab (Crusher+Rocket), after End Turn (`F-hp-crab`) | 83 (83 / 0) | 80 / 3 / 3 | 83 | 825 | 0 | **fixed** `742b465d`, `85651148` |
| 14 | fight reward screen: relics differ (`R-relics`) | 83 (81 / 2) | 19 / 64 / 52 | 73 | 406 | 0 | open (new since 10-30) |
| 15 | fight reward screen: player HP differs (after the fight) (`R-hp`) | 73 (65 / 8) | 42 / 31 / 23 | 63 | 256 | 22 | open (lead named, not fixed) |

The other 60 groups hold 808 records; none has more than 65. Counts per night for the top fifteen are in the appendix at the end.

Readings and one example each (`night seed, floor, decision` locates the record in that night's `divergences.jsonl`; "game only" and "copy only" are cards or relics held by one side):

1. **hand: one side holds the other's whole hand plus 1 or more cards (a count difference).** One side's hand holds the other's whole hand plus one or more cards; the game holds the extra in 739 of 830 (hand sizes game / copy: 7 / 5 473, 8 / 6 90, 9 / 7 56). Where it shows: 295 at the first hand of a fight, 131 at the draw after End Turn, 385 right after a card play, 19 after a potion or a screen. The D11C diagnosis (HANDOFF 2026-10-27, `W5-D11C-diagnosis.md`) traced this shape to the lockstep's state transfer, not to a draw rule: a card's enchantment lost at a re-anchor (a Power with Swift still draws in the game) and relic turn counters (Pendulum, Pollinous Core) that a re-anchor did not carry; D11F1 (10-27) and D11F2 (10-28) landed to carry both. Since then Act 1's rate fell from 0.114 per 1,000 decisions (10-26) to between 0.000 and 0.051 on the last five nights, while Acts 2 and 3 stayed between 1.59 and 2.81 on every night (2.07 over 10-29 to 11-04, against 0.020 in Act 1 over the same nights). The cause in Acts 2 and 3 is not diagnosed here; the per-night table follows the list. Example: 11-04 seed TR2E76YLQ9, floor 33, decision 190: game hand 10 cards, copy hand 9: game only: STAMPEDE+; after End Turn, CRUSHER+ROCKET, turn 2.

2. **enemy HP differs, other encounters (long tail).** Enemy HP differs after a hit or a power, on 36 different encounters. Share of the 536 records: OVICOPTER 14%, TUNNELER 7%, THIEVING_HOPPER 6%. After 10-31 (192 records): OVICOPTER 23, LOUSE_PROGENITOR 13, ENTOMANCER 13, HUNTER_KILLER 13, THIEVING_HOPPER 11. Cards played last (after 10-31): a screen choice 19, UNRELENTING 15, THUNDERCLAP 12, STRIKE_IRONCLAD 12, a potion 10. Example: 11-04 seed 5ZNLS7PA5U, floor 29, decision 217: ENTOMANCER: game [70] vs copy [69]; after playing POKE, turn 4.

3. **fight reward screen: game's deck holds a card the copy lacks (not the Strike signature).** At the screen after a won fight the game's deck holds a card or two the copy's lacks (most often STRIKE_IRONCLAD+ 19, UNRELENTING 17, STAMPEDE+ 13, INFERNO 12, FIGHT_ME 11, INFLAME 11; 79 different cards). 208 of 267 are on floors 19-21, the first Act 2 fights (113 on floor 19). 180 of the 267 are from the 10-26 night. Example: 11-04 seed BGDJ2U5MLX, floor 31, decision 201: game only: STRIKE_IRONCLAD+.

4. **enemy HP: a Strike's hit leaves the copy's enemy 1-4 HP higher (signature of the Ember enchantment).** Tezcatara's Ember (the Act 2 Ancient's Nutritious Soup puts it on the basic Strikes): the copy added the enchantment's amount to the card's damage where the game adds its own 3, so the copy's enemy kept 2 to 4 HP too many after each embered Strike. Named in the 10-30 diagnosis (M1). Matched here by its signature, not record by record. Example: 11-04 seed JAPN5JYBFA, floor 30, decision 185: game [4, 62] vs copy [4, 65]; THE_OBSCURA.

5. **Crystal Sphere screen has no mapping in the lockstep (gap).** The Crystal Sphere event ("payment plan" 193, "uncover the future" 21): the lockstep has no mapping for its screen, so the step is a gap and the run is not compared until the next fight start or map screen. Floors 20-23 hold 151 of the 214. Nothing in the fork log names it. Example: 11-04 seed Z44U7RLPBK, floor 21, decision 152: unmapped:crystal_sphere.

6. **player HP differs in a fight, other encounters.** Player HP differs after an enemy turn or a play, on many encounters. Act 1 shows 15 on the last three nights, Acts 2 and 3 45. After 10-31, by count: BOWLBUG_ROCK+BOWLBUG_SILK+SLUMBERING_BEETLE 8, DECIMILLIPEDE_SEGMENT_BACK+DECIMILLIPEDE_SEGMENT_FRONT+DECIMILLIPEDE_SEGMENT_MIDDLE 8, ENTOMANCER 5, OVICOPTER 4. Example: 11-04 seed QTXZJGUUDD, floor 30, decision 183: INFESTED_PRISM: game 24 vs copy 29; after End Turn, turn 3.

7. **hand: hand differs in which cards right after a card play (a swap).** Same screen, but the two hands hold different cards (both sides have cards the other lacks) right after a card play. Act 1 shows 23 on the last three nights against 32 in Acts 2 and 3 (per decision 3.4 times as many). Cards played last: STRIKE_IRONCLAD 28, DEFEND_IRONCLAD 17, ANGER 11, BASH 5, SPITE 5. Example: 11-04 seed 3YM4LQH3MA, floor 19, decision 102: game only: FIEND_FIRE+; copy only: INFERNO; after playing DEFEND_IRONCLAD, THIEVING_HOPPER, turn 2.

8. **enemy HP: Decimillipede segments hold different HP.** The three Decimillipede segments hold the same three HP values on different segments at the fight start; the copy settled them one at a time. Named in the 10-30 diagnosis (M3). The fight still cannot be re-anchored: 207 of all 439 failed re-anchors say `no emulator id` for the Decimillipede segment names (section 3). Example: 11-04 seed D9U96NVYGP, floor 28, decision 245: game [40, 34, 36] vs copy [47, 41, 43]; turn 1.

9. **fight reward screen: game's deck holds one more upgraded Strike and its gold is lower.** At the reward screen after a fight the game's deck holds one more upgraded Strike (sometimes two) and its gold is 1 to 7 lower. 32 of 50 runs first show it on floor 19, the first fight of Act 2; 111 records on 50 runs, none before the 10-30 night. Example: 11-04 seed SQR3YAYAK8, floor 22, decision 157: game deck +STRIKE_IRONCLAD+; gold game 12 vs copy 14.

10. **map decision after an Act ancient's pick: game holds relics the copy lacks.** At the map just after the Act 2 Ancient's pick the game holds 3 or 4 relics the copy lacks: Toy Box 57, Calling Bell 38 (floor 18 in 94 of the 104), Relic Trader 9. Re-anchored at once, so no decision goes unscored, but the copy does not grant those relics by itself. Example: 11-04 seed 8E5GDJHSG3, floor 18, decision 124: game only: ANCHOR, GIRYA, GREMLIN_HORN +1 more.

11. **hand: opening hand differs in which cards (a swap).** The first hand of a fight holds different cards on the two sides (a swap, the draw order differs). 74 on the four earlier nights, 22 on the five later; Act 1 shows 4 on the last three nights. Example: 11-04 seed 6EYDFSR9SD, floor 22, decision 160: game only: DOMINATE+; copy only: OMNISLICE; TUNNELER.

12. **fight begins while the copy is in the Fake Merchant phase (reason phase:13).** A fight begins in the game while the copy is in its Fake Merchant phase (13), on floors 21-23 in 63 of 85. 81 of the 85 were re-anchored at the fight start. Example: 11-04 seed T9F9PZ3SFX, floor 23, decision 147: phase:13.

13. **player HP: Kaiser Crab (Crusher+Rocket), after End Turn.** Kaiser Crab (Crusher + Rocket): the copy faced the wrong half, so the half at its back hit for half again. Named in the 10-30 diagnosis (M1, M2). 3 records on the five later nights. Example: 11-03 seed S69T7VA4QM, floor 33, decision 189: game 7 vs copy 11; after playing BODY_SLAM.

14. **fight reward screen: relics differ.** At the reward screen after a fight the game holds a relic the copy lacks (49 different relics, none above 5: RED_SKULL 5, BAG_OF_MARBLES 4, ANCHOR 3, POTION_BELT 3, RED_MASK 3). 78 of the 83 follow a card play; floors 21-25 hold 61. First seen 10-29 (2) and 10-30 (17), 52 on the last three nights. Example: 11-04 seed SDSWMFHT8F, floor 22, decision 139: game only: GORGET.

15. **fight reward screen: player HP differs (after the fight).** Player HP at the reward screen: the copy is 1 lower in 26 of 73 and 12 lower in 22, the rest 2 to 7 (a few the other way). The 10-30 note's lead: Crimson Mantle's turn-start cost the game never reaches, and an end-of-fight heal. Act 1 shows 22 on the last three nights, Acts 2 and 3 23. Example: 11-04 seed 5WP48UMYC3, floor 22, decision 191: game 58 vs copy 46.

**Fixed groups outside the top fifteen:**

- `M-floor` map: the copy stands one floor behind the game: 48 records, 48 before, 0 after; `89072b4f` (10-30 20:02Z, a lone map node and the room behind it walked to the game's map).
- `SC-gold` deck-pick screen: gold differs (41 of 45 on the 10-27 night): 45 records, 43 before, 2 after; `d5ed2524`, `a3569270` (10-28 12:08Z, gold lost at the pick).
- `S-screen-event-None!=event` event screen: the game asks after its player died: 30 records, 29 before, 1 after; `63e80311` (10-30 20:02Z, not compared once both ended).

**Same signature, not fixed.** `T-floor` (treasure room, 40) and `SH-floor` (shop, 24) show the copy one floor behind at a treasure or a shop; `M-floor` (the map variant) is gone since batch B, these are not (T-floor 21 before, 19 after; SH-floor 12 and 12). `S-screen-map-shop!=map` (38: 11 before, 27 after) and `S-screen-event-shop!=event` (28) are the copy standing in a shop where the game is at the map or an event.

**Top open groups on the last three nights, Act 2 and 3 (records, runs):**

- hand: one side holds the other's whole hand plus 1 or more cards (a count difference) (`F-handcount`): 340 records on the last three nights, 2.22 per 1,000 Act 2 and 3 decisions (Act 1: 0.02 per 1,000 Act 1 decisions).
- enemy HP differs, other encounters (long tail) (`F-ehp-other`): 151 records on the last three nights, 0.98 per 1,000 Act 2 and 3 decisions (Act 1: 0.07 per 1,000 Act 1 decisions).
- Crystal Sphere screen has no mapping in the lockstep (gap) (`GAP-crystal`): 92 records on the last three nights, 0.60 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).
- fight reward screen: game's deck holds one more upgraded Strike and its gold is lower (`R-deck-strike`): 64 records on the last three nights, 0.42 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).
- fight reward screen: relics differ (`R-relics`): 52 records on the last three nights, 0.34 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).
- fight reward screen: game's deck holds a card the copy lacks (not the Strike signature) (`R-deck-game-extra`): 51 records on the last three nights, 0.33 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).
- map decision after an Act ancient's pick: game holds relics the copy lacks (`M-relics`): 47 records on the last three nights, 0.31 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).
- player HP differs in a fight, other encounters (`F-hp-other`): 45 records on the last three nights, 0.29 per 1,000 Act 2 and 3 decisions (Act 1: 0.04 per 1,000 Act 1 decisions).
- hand: hand differs in which cards right after a card play (a swap) (`F-handswap-play`): 32 records on the last three nights, 0.21 per 1,000 Act 2 and 3 decisions (Act 1: 0.06 per 1,000 Act 1 decisions).
- fight begins while the copy is in the Fake Merchant phase (reason phase:13) (`S-phase13`): 29 records on the last three nights, 0.19 per 1,000 Act 2 and 3 decisions (Act 1: 0.00 per 1,000 Act 1 decisions).

**The largest open family, count-shaped hands (`F-handcount`), per night.** Records where one side's hand holds the other's, in Act 1 and in Acts 2 and 3, with the rate per 1,000 decisions of that act (D11F1 landed before the 10-27 night, D11F2 before the 10-29 night):

| night | Act 1 records (per 1,000) | Acts 2 + 3 records (per 1,000) | of those, game holds more / copy holds more | Acts 2 + 3 runs with one |
| --- | --- | --- | --- | --- |
| 10-26 | 28 (0.114) | 113 (2.81) | 78 / 35 | 54 |
| 10-27 | 13 (0.061) | 84 (2.03) | 59 / 25 | 50 |
| 10-29 | 7 (0.029) | 75 (1.59) | 72 / 3 | 49 |
| 10-30 | 1 (0.006) | 132 (2.18) | 119 / 13 | 75 |
| 10-31 | 3 (0.051) | 35 (1.66) | 35 / 0 | 21 |
| 11-01 | 1 (0.016) | 51 (2.24) | 50 / 1 | 33 |
| 11-02 | 0 (0.000) | 59 (2.38) | 54 / 5 | 28 |
| 11-03 | 6 (0.024) | 225 (2.20) | 218 / 7 | 123 |
| 11-04 | 0 (0.000) | 56 (2.12) | 54 / 2 | 30 |

## 8. Earlier work, and what changed since

- **No note before this one measures the copy's Act 2 or Act 3 fidelity across nights.** `docs/diagnostics/2026-11-01-facts.md`, `2026-11-01-process.md` and `2026-11-02-boss-entry.md` are about strength (where the AI dies, what it brings to the bosses); `2026-11-01-process.md` reads the AI's Act 2 rates from the copy's 2,000-seed block, which is exactly where this note finds the copy least checked. D38 gives no figure for "barely verified".
- **The 10-30 diagnosis notes** (`referee/rebuild/f08-enemy-hp-diagnosis-2026-10-30.md`, `f17-player-hp-diagnosis-2026-10-30.md`, `f16-gold-screens-diagnosis-2026-10-30.md`) explain the Act 2 enemy-HP, player-HP and screen groups of the nights 10-26 to 10-30 and predicted that those records go on the first build holding the fixes. Against the five later nights the records of the mechanisms they fixed fell: Ember 252 on the four earlier nights, 2 on the five later; Decimillipede HP 103 and 8; Kaiser Crab player HP 80 and 3; map floor 48 and 0; event after death 29 and 1; gold at the removal screen 43 and 2. What they left is still in the groups here: the reward-screen HP (`R-hp`, their "not taken" `Gc44f78e430`) and the player-HP long tail.
- **The Codex replay** (`readiness.json`, scored 2026-10-21 on fork `c3292672`, 20,294 recorded human runs replayed by the emulator to the end): the chance a run still replays identically is 88.5% at the end of Act 1, 62.6% at the end of Act 2 and 26.3% at the end of Act 3 (640 runs followed that far); 1,797, 1,971 and 1,434 of the 5,202 stopped runs stopped in Acts 1, 2 and 3. It is a different instrument (human decisions, whole run, strict identity) and the only one with a real Act 3 sample (1,233 of its runs ended in Act 3, against 169 real-arm runs reaching it here). It predates every fix above and has not been rerun, so it cannot be read against the nightly numbers; rerunning it on the current tree is the cheapest way to get an Act 3 figure.
- **What changed since the first of these nights:** 59 non-merge fork commits since 10-26 touch `src/` or `referee/lockstep.py` (the engine, the solver and the lockstep together); the ones that change what the copy does or what the lockstep compares are the week-5 bundle of 10-28, the gold-timing pair of 10-28, batches A to C of 10-30 and the Battleworn Dummy roster walk of 11-01 (section 1). `git log --since=2026-10-26` names no commit for: the Crystal Sphere screen, the Ancient's Toy Box and Calling Bell relics, the opening or next-turn draw, Brightest Flame, Crimson Mantle's turn-start cost, the Fake Merchant phase, or the fight-reward screen's deck, relic and gold differences. Those are the open groups above.

## 9. Not measured

- Decisions by kind (fight move, map, shop, event, potion) and by floor for the real arm: the lockstep stats keep a total only, so the per-kind rates exist for card rewards and rest sites alone and the per-act denominators are modelled.
- Whether a difference changes what the AI does or how far it gets; only the states are compared. The lab's weights (`ranked.json`) price that and were not recomputed here.
- Anything inside a stretch that was not compared (8.1% of Act 2, 16.3% of Act 3 decisions): the copy may be right or wrong there.
- The real arm's per-fight survival, HP at entry and per-encounter outcomes (the workers' game logs are deleted at the block's end and the rows keep seeds and outcomes), so no real against copy comparison by encounter.
- The cause of any open group: the records hold the first differing field and its two values, not the step trail, and no replay was run. Causes above are the 10-30 notes' or leads read off the shapes, flagged as such; the Ember rule is a signature match.
- Content coverage in Acts 2 and 3: how many of the enemies, events, relics and Ancient options the real arm has met (the rows list none of them for fights without a difference); Act 3 per enemy is certainly thin.
- The final floor, the second Act 3 boss and the victory path: 0 wins in 11,041 real runs, and 1 run that ended on floor 49.
- The 63 crash rows (0.6% of real-arm rows) and the 11 records on them: 24 game process deaths, 17 slow starts or silent games, 11 "the engine refused action" (the copy refusing an action the game offered: 3 on 10-30, 1 on 11-01, 1 on 11-02, 4 on 11-03, 2 on 11-04), 7 run deadlines, 4 worker exits. They are left out of every rate; the engine refusals are a fidelity signal of their own.
- Other characters and ascensions; only Ironclad A10 is in these nights. Agent effects: g5 to g11 reach different content and the pooled rates mix them.
- The build each night actually ran: taken from the morning reports' tree hashes and the library-build times they note, not re-derived.

## Appendix: records per night for the top fifteen groups (Acts 2 and 3)

| group | 10-26 | 10-27 | 10-29 | 10-30 | 10-31 | 11-01 | 11-02 | 11-03 | 11-04 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `F-handcount` | 113 | 84 | 75 | 132 | 35 | 51 | 59 | 225 | 56 |
| `F-ehp-other` | 170 | 70 | 49 | 55 | 27 | 14 | 19 | 102 | 30 |
| `R-deck-game-extra` | 180 | 1 | 1 | 21 | 5 | 8 | 13 | 30 | 8 |
| `F-ehp-ember` | 89 | 28 | 73 | 62 | 0 | 0 | 1 | 0 | 1 |
| `GAP-crystal` | 22 | 21 | 35 | 24 | 7 | 13 | 24 | 56 | 12 |
| `F-hp-other` | 21 | 59 | 7 | 15 | 13 | 3 | 8 | 27 | 10 |
| `F-handswap-play` | 44 | 30 | 12 | 19 | 10 | 11 | 3 | 21 | 8 |
| `F-ehp-deci` | 12 | 27 | 35 | 29 | 0 | 0 | 2 | 5 | 1 |
| `R-deck-strike` | 0 | 0 | 0 | 38 | 4 | 5 | 15 | 35 | 14 |
| `M-relics` | 19 | 6 | 4 | 12 | 9 | 7 | 7 | 31 | 9 |
| `F-handswap-open` | 33 | 27 | 9 | 5 | 2 | 4 | 2 | 12 | 2 |
| `S-phase13` | 8 | 5 | 11 | 16 | 8 | 8 | 6 | 22 | 1 |
| `F-hp-crab` | 11 | 24 | 19 | 26 | 0 | 0 | 1 | 2 | 0 |
| `R-relics` | 0 | 0 | 2 | 17 | 7 | 5 | 8 | 34 | 10 |
| `R-hp` | 6 | 14 | 13 | 9 | 4 | 4 | 2 | 20 | 1 |
| **all 75 groups** | 861 | 567 | 449 | 578 | 175 | 160 | 195 | 785 | 206 |

Acts 2 + 3 decisions per night for scale (modelled): 10-26 40,182, 10-27 41,435, 10-29 47,225, 10-30 60,587, 10-31 21,137, 11-01 22,758, 11-02 24,799, 11-03 102,262, 11-04 26,359.
