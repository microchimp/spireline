# Spireline: final report (2026-11-25)

Spireline set out to build an AI that beats the best human players of Slay the Spire 2 at Ascension 10, Ironclad first, using only what the player can know, with no language model in the player and no end-to-end reinforcement learning. It ran from early October 2026 (the first decisions are dated 2026-10-10) to 2026-11-25, when the owner stopped the Claude spend because the measured pace did not justify it. The machine keeps running unattended; this report says what was built, what was measured, why it fell short, and what a continuer would do first. Every figure carries its margin (two standard errors) where one exists.

Plain summary: the player is as good as or better than the average human for the first two of the game's three acts, and a hundred times worse at the end. It wins 2 runs in 2,000 on the real game; an average human wins about 110. It gets past the first Act 3 boss in about 20 of 100 arrivals (26 of 100 fights it finished itself); humans about 70. Six and a half weeks of learning moved that number by about one point per fighter promoted, and the real win count did not move at all.

## 1. What was built

**The simulator** (`microchimp/spireline-sim`, public since 2026-11-25, MIT). A fork of the r33hab/sts2 C# emulator of the game (itself from evangambit and Zamiell), extended for fidelity and coverage, with about 1,800 commits of ours since upstream `b745217`. Its distinctive part is the **referee**: the game's own code is run headless (its DLLs loaded by the C# driver in `referee/driver/`) beside the emulator on the same seeds, and the two are compared decision by decision (the lockstep comparer). Disagreements are ranked by the game's hook family and drive the fixes; nothing is fixed because a random run found it unless the AI meets it too. The emulator's dispatch was rebuilt in the game's own structure (the "kernel") rather than patched site by site. The game's files, assets and decompiled source are never in the repository; the referee needs the owner's own copy of the game.

**The lab** (`tools/lab/`). A Windows scheduled task runs `runner.py` always-on: it checks the tree out at the fork's main, builds, plays the configured jobs (practice runs, the whole-run judge, the weekly real-game block), and keeps its books (`status.txt`, `runner.log`, alerts). Locks (`QUIET.lock`, `main.lock`) coordinate it with hand-started jobs and landings.

**The learning machine** (`rl/`). Self-play on the simulator with search (configuration `a3-v1`, about 21 decisions a second a core). Two brains: a **fight brain** (`combat_net`, `fight_net`) trained in the fight gym, and a **run brain** (`run_value`, `run_student`, `boss_chain`) for the map, shops, rewards and events. The fight gym's **gate** (rule v5) scores a candidate fight brain on a ruler of human starting positions (500 Acts 1-2 starts from the corpus and 414 Act 3 boss starts), paired draws, three stages, a one-sided 95 per cent bound, and promotes it as the gym's incumbent (v3 to v8 between 2026-11-18 and 2026-11-25). A promoted fighter is wired into a **run candidate** (the champion's run brain with the new fight brain) and a marker queues the **whole-run judge**: 2,000 to 4,000 paired runs against the champion under **keep rule v3** (the first Act 3 boss passed per 100 runs at the 0.005 bound, with futility and extension looks), and for fight-only swaps **route S** (a boss-door exam S1 on about 1,100 of the champion's own arrivals, then a whole-run no-loss check S2), with a base block of 2,000 runs for a fresh champion. The rules are written in `docs/rl/KEEP_TEST_V3.md` in the fork.

**The real-game test.** Once a week (168 hours, from 2026-11-20 19:03Z) the referee plays 2,000 runs of the champion on the real game beside a copy arm on the same seeds, in about 6.6 hours. The **strict reader** (`tools/strict_rows.py`) credits a boss fight only when the player itself finished it; the morning report and the weekly numbers read the block.

**The human bar.** Aggregates of the Spire Codex public run export for game version 0.107.1 (aggregates and derived positions only, no cell under 20 runs, one fifth held out and never used for training or tuning; decision D13). Raw human runs never left the data folder and are not published.

**The books.** `docs/DECISIONS.md` (D1 to D70, every owner decision with its reason and undo), the paper (`docs/paper/spireline-paper.html`, 47 editions), the weekly sceptic reviews (`docs/review/`), the two-page state and the handoff log (`docs/referee-notes/`).

## 2. What was measured

The real game, generation 20 (the champion when the last block ran), block of 2026-11-20, 2,000 runs, against the average human from the corpus:

| Measure | Spireline | Average human |
|---|---|---|
| Mean floor reached | 30.1 | about 27 |
| Act 1 boss beaten, per 100 runs | 72 | 55 |
| Act 2 boss beaten, per 100 runs | 24 | 29 |
| First Act 3 boss passed, per 100 runs | 3.4 | 18 |
| First Act 3 boss passed, per 100 arrivals | 19.5 +-4.2 (68 of 348) | about 70 |
| ... per 100 fights the player finished itself | 26.2 +-5.4 (68 of 260) | about 70 |
| Wins, per 100 runs | 0.1 (2 of 2,000) | about 11 |

The copy game reads higher than the real one: the champion's fresh base arm on the simulator (4,000 runs) passes the first Act 3 boss 5.30 times per 100 runs, 23.8 per 100 arrivals, and wins 13. Copy-judged gains read at about 0.75 on the real game under today's referee, chiefly because the referee loses its place in a fight: in 88 of 348 real Act 3 arrivals (25 in 100) the copy stopped matching the game and a stand-in finished the fight, winning none. Two fixes to that (the driver reporting turns the game ended unasked; the copy re-anchored on the game's hidden state inside a fight, firewall kept) landed on 2026-11-25 and have not yet been tested by a real block; the prediction was lost-track down from 25 to between 3 and 20 per 100.

**The wall is one boss.** Within Act 3 the player gets past the Test Subject (three forms) in about 2 of 100 arrivals against 21 to 27 for the Queen and Aeonglass. From the humans' own positions our fighter kills the Test Subject 6.9 to 8.1 times in 100 against the humans' 72.5; Aeonglass 60.2 against 84.4; the Queen 59.4 against 65.6. Its second form kills us (586 of 798 losses: multi-hits of 11 x 3 and 11 x 4 at about 9 Strength). Thinking sixteen times longer at the boss buys +4.0 kills in 100 [1.6, 6.4] at the two beatable bosses and +1.1 at the wall: the fighter does not know what to do there, and more search does not find it.

**The learning pace.** Six fighters were promoted by the gate in a week (v3 to v8), each with a gate gain of about +1 to +2 points on the ruler. Pooled over the two measured fighters (1,590 starts), the boss-door exam reads **+1.12 +-0.70 passes per 100 arrivals per fighter**: real, small, and invisible in whole runs. Pooled over four fighters and 10,000 paired whole runs, the effect is **+0.11 +-0.49 per 100 runs** (the full carry-over of the door gain into whole runs would read about +0.24 +-0.15, which is not excluded). Four of four gate-promoted fighters read zero in their own whole-run judgement. The whole-run judge resolves a single step only from about +1.3 per 100 runs at 4,000 pairs; a fight-brain step is smaller, which is why route S was built. Generation steps that did show: generation 19 (+1.43 passes per 100 runs past the first Act 3 boss, lower bound +0.45, on 4,000 pairs) and generation 20 (the boss chain: 5.9 against 3.1 per 100 at 1,100 pairs, an early stop that reads high; about +1.0 fresh).

**Pace against the goal.** At about +1 per 100 arrivals per fighter and a fighter every one to two days, the average human's door rate (70) is two to three months away if the gains stack perfectly; the average human's win rate about a year; the best human beyond estimate. The real win count did not move in six and a half weeks (2 of 2,000 on both blocks).

**The machine.** 16 threads. The fight loop practises on 12 processes and gates on 12 every 120 minutes (one day: 7,881 fights, 18.0 hours played, 6.0 waited); a whole-run judgement takes 2.5 to 5 hours of 16 processes; the real block 6.6 hours a week. Disk grows about 14 GB a week.

## 3. Why it fell short

1. **The translation from fights to runs is unmeasured within noise.** Gains at the fight level are real but about one point each; whole-run judgements of 2,000 to 4,000 pairs cannot see them. Route S (the door exam) was built to judge fight-only swaps where they act, and had its first real-path run on 2026-11-25; the fresh-champion base block landed the same day. Neither has yet promoted anything.
2. **The practice set does not contain what kills us.** Act 3 hallway and elite fights take 12.6 of 100 real runs and are not in the ruler; the Test Subject's second form needs a different fight than Acts 1-2 teach.
3. **The referee's tracking loss discounts every real reading by a quarter.** The fixes exist but are untested.
4. **The cost per step.** Each fighter costs a gate (hours of the practice loop stopped) and a whole-run judgement (hours of the lab); the gate outspends practice.
5. **Early readings read high.** Three times a promising first look (an early stop, a one-sided 90 per cent bound, a hand-summed margin) was corrected downwards on fresh draws; the rule since is to confirm every rule set on fresh draws and to quote every figure with its margin.

## 4. The decision and the pause

D69 (2026-11-25): the owner's question whether to close. The sceptic review (`docs/review/sceptic-2026-11-25-continue.md`) recommended stopping the Claude spend and running the machine lights-out for four to six weeks. D70 (2026-11-25): the owner chose that, with a light check once a week, and asked that everything useful be published first.

**The reading rule for January** (D69): take the latest weekly real block and read the first Act 3 boss passed per 100 fights the player finished itself (the strict reader). **35 or more: a case to continue. Under 32: close and keep the code. Between: one more block.** The 2026-11-20 reading is 26.2 +-5.4.

**What runs unattended:** the fight loop (practice and gate), the whole-run judge when a marker exists, the weekly real block. A daily Claude-free health check writes `status/latest.md` in this repository and restarts the fight-loop daemon when it is down; a weekly cloud check reads it and reports in plain words. `docs/LIGHTS_OUT.md` says how it runs, how to read it and how to stop it.

## 5. What a continuer would do first

In the order the records give (D68 addendum 7; the 2026-11-24 and 11-25 reviews):

1. Exam precision: more draws per start at the boss door, so one fighter's door gain is resolved at the 0.005 bound.
2. Act 3 hallway and elite fights into the practice set and the ruler (own starts by dropping the boss filter in `rl/act3_replay.py`).
3. The gate's cost: practice should not stop while a gate plays.
4. The referee's stand-in: 27 in 100 of Act 3 boss fights in the real game were finished by the stand-in; read the 11-27 block as the test of fixes c and d.
5. Small items: the potion engine fault (`UsePotion` in an invalid state, 2 of 3,312 Act 3 games); `rl/gen0.py promote --help` crashes on a `%` in a help string; the seven residual unfinished-fight rows; the second Act 3 boss's first decision is not a fight start.

## 6. Where everything is

- Spireline (this repository, MIT): `docs/DECISIONS.md` (the decision log, wins over every other document), `docs/DESIGN.md` and `docs/SIMULATOR.md` (the design), `docs/SECURITY_REVIEW.md` and its addendum (the review that gated running the game's code), `docs/paper/spireline-paper.html` (the paper; its last edition is 47, published 2026-11-24, with its real-block figures corrected the same day), `docs/review/` (the weekly sceptic reviews), `docs/referee-notes/` (the two-page state, the handoff log, the briefs and memos of the last phase, scrubbed of user paths), `tools/` (the strict reader, the morning report, the weekly numbers, the pooled reading of fighters, the health check), `status/` (the daily status written by the unattended machine), `docs/LIGHTS_OUT.md`.
- The simulator fork (MIT): `FORK.md` (what the fork is and its rules), `referee/RUNBOOK.md` and `referee/FINDINGS.md` (the referee), `docs/rl/KEEP_TEST_V3.md` (the judge's rules), `rl/` (the machine), `tools/lab/` (the lab), `tests/` (6,744 Python tests at the pause plus the C# suites).
- The trained champion (generation 21: the generation-20 run brain with fight brain v5, promoted 2026-11-22) is published on the fork's Releases page with a `RUN.md`; it needs the simulator built locally.
- Not published, by rule: the game's files and decompiled source, the raw human runs, the referee's per-run logs and results folders.

## 7. What held up

The information firewall (the player sees only what a human could; every hidden field is dropped unless allow-listed, and the allow-lists stayed empty). The referee as the fidelity reference (the real game, not a test suite, says whether the copy is right). Aggregates-only human data with a held-out fifth. The books: a decision log with undo lines, a two-page state rewritten at every check, a weekly review that asks what a sceptic would say, and the rule that no figure is quoted without its margin.

## Credits and licence

r33hab/sts2 (and evangambit, Zamiell before it) for the emulator; Gennadiyev and r33hab for the STS2MCP mod whose payload the firewall reads; Spire Codex for the public run export; Mega Crit for the game. Spireline is an unofficial fan project, not affiliated with or endorsed by Mega Crit; it contains no game code or assets. Spireline and the fork are MIT.
