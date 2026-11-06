# The strong-player set: the v0.107.1 export names no player

Source: Spire Codex public run export for v0.107.1 (second download, 2026-11-06; see [SPIRE_CODEX.md](SPIRE_CODEX.md)). Aggregates only; no cell is under 20 runs.

## What was asked

D55 addendum 7: rank the Ironclad Ascension 10 players of the new export by a shrunk win rate (players with at least 20 kept runs, a beta
prior centred on the pool's rate worth 20 runs), take the top quarter as the "strong set", and refit the human prior on that set's choices.
The ranking needs a player id on each run: the export's `player_token`.

## What the export holds

* `player_token` is **null in all 840,381 runs** of the file (checked on the raw lines of the whole export, not only the kept subset).
* `players[0].id` is the seat number: 1 in all 74,287 runs kept by the first filtering step. `platform_type` is `steam` (74,245) or `none` (42).
* `_sts` (15,424 kept runs) names the uploading tool and `_spirecodex_damage` (3,272) is a per-fight damage block; neither names or links a player.
* `seed`, `start_time` and `run_time` do not identify a player, and nothing here tries to link runs to one another.

So no player-level rate can be computed, no player has "at least 20 runs", and a strong set cannot be formed from this export. The
first export (October) was the same: its `player_token` was empty (SPIRE_CODEX.md).

## What was built anyway

`tools/spire_codex/strong_players.py` implements the rule as D55 addendum 7 states it (pool, eligibility, shrunk rank, top quarter, the
suppressed aggregates, the honest check that selects on fifths 1 to 3 and reads fifth 4, a tokenless corpus file for the prior's
pipeline) and `filter_a10.py --keep-player-token` keeps the field in the working file. Both are tested on synthetic runs
(`tests/test_strong_players.py`); on this export the tool reports 0 players. They are ready for an export that carries tokens.

## The pool, for the record

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

The fifths agree with one another to within what 3,600 runs allow (the wins per 100 differ by under one point), so the larger file
can join the training fifths by the same rule without a shift in who is in them.

## Options that need the owner or the orchestrator

1. A different export that carries tokens (another build's file) cannot replay on the copy, which is built for v0.107.1; not tried, no
   download beyond the approved one was made.
2. A run-level stand-in for "strong" (runs that won, 1,565 in fifths 1 to 4; runs that beat the Act 2 boss, 4,153) selects on outcomes
   and luck as well as skill, and the win-conditioned prior `pi_h-v1-win` already conditions on the outcome; not built.
3. A refit on all players' choices over the larger file (14,537 runs in fifths 1 to 4, against about 11,960 in the v1 fit) is inside
   D13/D38/D55 item 1 and costs about half an hour of the copy's two-process replay and build plus minutes of fit; not built, since it is
   not the strong-player refit that was approved.
