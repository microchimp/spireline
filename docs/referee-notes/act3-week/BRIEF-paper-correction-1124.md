# Brief: the paper's real-game figures corrected after lane 23 (2026-11-24)

Written 2026-11-24 04:50Z by the orchestrator. Writing lane, Sonnet. Read `COMMON.md` first. You edit exactly one file, `D:/spireline/spireline/docs/paper/spireline-paper.html` (edition 47, published 03:12Z today). Do not commit or publish; the orchestrator checks, commits and publishes. No CPU work: every figure is given here or in the addendum.

## Why

Lane 23 landed a corrected reader (Spireline `7cfd47e`): a boss fight our player played itself is credited even when the referee lost its place earlier (and recovered) or later (at the second boss). The old reader wrote the run off from its first loss. Source of every corrected figure: `D:/spireline/referee/backlog/act3-week/REAL-ROWS-LOST.md`, section "Addendum 2026-11-24 (lane 23)", table "The two blocks read again". Use its counts exactly, as "N of M".

## The corrected figures

11-20 block (generation 20, 2,000 real runs): first Act 3 boss passed on **68 of 348 arrivals = 19.5 per 100** (page says 61 of 348 = 17.5); on the fights our player finished itself **68 of 260 = 26.2 per 100** (page says 24.1, 253); lost-track arrivals **88 of 348** (page says 95; 21 of the 88 went past under the stand-in and are not credited); Aeonglass **25 of 117** (page 23), the Queen **27 of 120** (page 24), the Test Subject **16 of 111 = 14.4 per 100** (page 14 of 111 = 12.6). Wins 2 of 2,000 unchanged. Act 1 boss beaten 1,417 of 2,000 (was 1,413), Act 2 boss 572 (was 541), if the page quotes them for 11-20.

11-19 block (generation 19): **37 of 292 = 12.7 per 100** (page says 32 of 292 = 11 in 100); player-finished **37 of 191 = 19.4**; lost-track **101 of 292**; the Test Subject **2 of 96**, lost-track at it **69 of 96** (the page's "81 of those 96 fights" was the old reading of the form-change loss; replace with the addendum's 69 of 96 lost-track arrivals, worded as such); Aeonglass 19 of 104, the Queen 16 of 92. The Act 2 boss figure for 11-19 on the Progress bar (447 of 1,997) is left as it is unless the addendum gives a corrected 11-19 Act 2 count (it does not); say nothing about it.

## The odds behind the 2 December mark (a consequence to state, not to decide)

The mark (at least 23.0 passes per 100 arrivals on one real block) was set with an odds table computed on a baseline of 17.5: a player that has not moved reads 23 or more in 0.3 of 100 blocks. On the corrected baseline of 19.5 that figure is **about 5 in 100** (one block of about 350 arrivals; a normal approximation, 2 SE about plus or minus 4.2). The other rows stand (true rate 23: 50 in 100; 25: 81; 20: 8). Where the page quotes the odds table (the At a glance board on the mark, the Decisions entry "The 2 December pass mark stays at 23", the plan item), keep the owner's decision text as it was said and add one sentence of correction: the baseline reading is 19.5 after the reader fix, so a player that has not moved passes the mark in about 5 of 100 blocks, not 0.3; the owner has not been asked again.

## Where (every occurrence; grep the page for 17.5, 24.1, "61 of 348", "95 of", "of 348", "253", "11 in 100", "2 of 96", "81 of those 96", "14 of 111", "23 of 117", "24 of 120", "12.6")

The At a glance boards (the mark board, the two-day board, the review board's "95 of the 348 arrivals ... 30 at the Test Subject, 34 and 31": the corrected lost-track per boss are Aeonglass 32, the Queen 28, the Test Subject 28 of 348 total 88); the timeline entries of 11-19, 11-20 and 11-21 (historical entries get the corrected figure with "(read again 11-24: ...)" rather than silent replacement); the scoreboard row "Gets past the first Act 3 boss" and its note; the Progress section ("Act 3 and the win", "No real-game reading of generation 21 yet"); the Risks rows that quote 17.5 or 24.1; the plan item on the real block; the Decisions entries (as above); the change log entries of editions 46 and 47 are history: leave them, and add new change-log lines (see below). The review board that quotes "the referee lost its place in 95 of 348 ... a stand-in finished those fights without ever passing" becomes: lost its place in 88 of 348; the stand-in got 21 of them past but they are not credited; the player passed 26.2 in 100 of the 260 fights it finished; tracked and played at that rate the block would read about 26 per 100 arrivals.

## New change-log lines (at the top of the change log, stamped 2026-11-24 05:00Z)

1. The reader correction (lane 23, Spireline `7cfd47e`): what changed, the corrected figures for both blocks, the odds consequence, and that the mark is unchanged.
2. Lane 21 (fork `13ca1f45`, `f98caf6c`): the 95 lost arrivals explained (78 inside the fight, of which 63 copy differences and 10 the referee's unasked end turns; 10 before the boss, 9 of them the deck past 64 cards, fixed; 7 the reader's); per-boss-fight record fields; the prediction for the 11-27 block (lost-track per 100: 24.7 with this, 22.7 with the reader, about 20 with fix c, 3 to 8 with fix d); lane 22 building fixes c and d.
3. Lane 19 (fork `663ed6d7`): the boss-door exam's ruler grows with every block the champion defends; its positions leave the practice automatically; a fresh champion's unplayed exam is named in the ledger.

Also update the "At a glance" heading's stamp to 2026-11-24 05:00Z and add to it "; the last real block re-read: 19.5 per 100 arrivals, not 17.5 (a reader correction, not the player)". Update the page stamp and `updated:` field to the same time; the edition number stays 47 (a correction, not an edition).

## Report

At most five lines: the places changed (count), any occurrence you could not place or that conflicts with the addendum (quote both), anything left as it was.
