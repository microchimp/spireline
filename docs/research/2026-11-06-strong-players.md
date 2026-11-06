# The strong-player set: the single-player runs carry no player key

Source: Spire Codex public run export for v0.107.1 (second download, 2026-11-06; see [SPIRE_CODEX.md](SPIRE_CODEX.md)). Aggregates only; no cell is under 20 runs; no player id appears here.

## What was asked

D55 addendum 7: rank the Ironclad Ascension 10 players of the new export by a shrunk win rate (players with at least 20 kept non-exam runs, a
beta prior centred on the pool's rate worth 20 runs), take the top quarter as the "strong set", and refit the human prior on that set's choices.
That needs a player key on each run.

## What the export holds

* `player_token` is **null in all 840,381 runs** (checked on the raw lines of the whole file), as in the October export.
* `players[0].id` is a 17-digit platform account id on multiplayer runs (16,220 distinct values across the file; 333,538 of the 333,616
  multiplayer runs carry one for every seat) and the placeholder **1 on single-player runs**: 506,762 of 506,765. The 3 exceptions are
  abandoned runs. In the 74,287 runs kept by the first filtering step, which is the single-player corpus every pipeline here reads, the
  id is 1 in every run. With the placeholder excluded, no single-player run has a key, so **the strong set of the single-player corpus is empty**
  (0 players with at least 20 runs, of 0).
* `_sts` (15,424 kept runs) names the uploading tool and `_spirecodex_damage` (3,272) is a per-fight damage block; neither names a player.
* `seed`, `start_time` and `run_time` do not identify a player, and nothing here tries to link runs to one another.

## What was built

`tools/spire_codex/strong_players.py` implements the rule as D55 addendum 7 states it (pool, eligibility, shrunk rank, top quarter, the
suppressed aggregates, the honest check that selects on fifths 1 to 3 and reads fifth 4, a tokenless corpus file for the prior's
pipeline) and `filter_a10.py --keep-player-token` keeps the token field in the working file. Both are tested on synthetic runs
(`tests/test_strong_players.py`); on this export's single-player corpus the tool reports 0 players. It keys on `player_token`; pointing it
at the account id of a multiplayer run is a small change (a key function), not made.

## The single-player pool, for the record

Ironclad Ascension 10, standard, single player, finished, unmodified, vanilla content; fifths by D38 addendum 1's hash rule; the exam
fifth (fifth 0) is left out of the pool and counted only as the exam.

| Group | Runs | Wins per 100 | Act 1 boss beaten per 100 | Act 2 boss beaten per 100 |
|---|---|---|---|---|
| Pool, fifths 1 to 4 | 14,537 | 10.77 | 54.67 | 28.57 |
| Fifth 1 | 3,625 | 11.01 | 53.68 | 28.08 |
| Fifth 2 | 3,605 | 11.15 | 56.64 | 30.01 |
| Fifth 3 | 3,736 | 10.39 | 53.99 | 27.60 |
| Fifth 4 (validation) | 3,571 | 10.53 | 54.41 | 28.62 |
| Exam (fifth 0, not used) | 3,588 | 10.81 | 54.71 | 29.38 |

## A feasibility probe on the multiplayer runs (not a strong set we can use)

The only runs with an account key are co-op runs. A probe with the stated rule (counts only, nothing written, the exam fifth by the same
hash on the run id left out, not vanilla-filtered, team outcomes): 66,987 Ascension 10 standard finished unmodified v0.107.1 runs with two or
more players (39,465 / 18,568 / 8,504 with 2 / 3 / 4 players, 450 with 5 to 9); 39,088 Ironclad seats in them, 7,924 in the exam fifth, 31 without
an account id, leaving 31,133 seats from 3,752 accounts (none appears on more than one platform type). 332 accounts have at least 20 such seats;
the top quarter by the shrunk win rate is 83 accounts.

| Group (multiplayer Ironclad seats, exam fifth out) | Accounts | Seats | Wins per 100 | Act 1 boss per 100 | Act 2 boss per 100 |
|---|---|---|---|---|---|
| Strong (top quarter of 332) | 83 | 2,940 | 55.3 | 90.7 | 77.0 |
| Other accounts with at least 20 seats | 249 | 9,703 | 7.1 | 69.8 | 34.7 |
| Accounts under 20 seats | 3,420 | 18,490 | 23.6 | 77.2 | 49.3 |
| All | 3,752 | 31,133 | 21.5 | | |

These figures are in-sample (the group is chosen on the same runs it is read on, so its rate is inflated), the win is the team's, and the
population is co-op: the copy plays single-player maps and fights, the record's per-seat stats sit beside the teammates', and
the pipeline reads `players[0]` and the first `player_stats` of each point everywhere. Using these runs for the human prior is a different job
from the one approved (it needs the seat's stats picked by account, a check that the copy regenerates a co-op map, and the owner's word that
co-op choices may teach a solo player); it was not started.
