# Lane 4: what more search buys at the Act 3 bosses (replay tool and smoke)

Read `COMMON.md` in this folder first, then option b in `referee/backlog/analysis-2026-11-18/A-learning.md`. Worktree `D:/spireline/fork/wt-act3-replay`, branch `feat/act3-replay`. Memo `ACT3-REPLAY.md` here. Sonnet lane. Heavy work in this lane: only the smoke (at most 4 processes, at most 30 minutes, BelowNormal, never while `LAB/nightly/active` exists). The full run is a script you write and the orchestrator launches after tonight's real-game block.

## The question

If the fight player thinks four or sixteen times longer at an Act 3 boss, how much more often does it win the fight? Each ten points more per arrival at the first Act 3 boss is worth about 1.5 wins-past-the-boss per 100 runs. If the gain is large, the ceiling is compute and we know its price; if small, the fight brain or the deck is the wall.

## Facts

- Today's champion is generation 18 (`referee/agent/current.json`); its search config is `a3-v1@h1e4b16`: base `a3-v1` with multipliers hall 1, elite 4, boss 16 (`agent.json` `search_schedule`; `gen_loop.Agent.search_config(sims)`; `rl/search_configs.py`; `rl/live_search.py` wall limits scale with the multiplier). "1x" in this lane means today's boss budget (16 times base); "4x" and "16x" mean 4 and 16 times that. Measure wall seconds per position at each budget in the smoke and size the full run from it (the full run must stay under about 100 core-hours and 8 hours wall on 12 processes).
- Saved positions: the fight exam (`rl/fight_exam.py`, `referee/gym-loop/exam/`, `human-meta.json`) already replays saved fight positions with the fight brain at a budget and counts outcomes: find how an exam cell is stored and played, and whether our own runs' Act 3 boss fights are saved in a replayable form (the plain-run store `referee/run-cheap/17|18/` rows carry `fight_rows` and `bosses`; the shards and `decisions.d/`; `rl/fight_rows.py`; `rl/human_starts.py` builds starts from human runs for Acts 1 and 2; `rl/practice_mix.py`; `rl/export_fight.py`). Positions must be fight starts at the first Act 3 boss (floor 48) and, where available, the second (floor 49), from generation 17's and 18's runs, each with the deck, relics, potions, HP and the boss's identity at the fight's start.
- Pairing: every position is played at all three budgets; report kills per budget with n and a 95% interval, the paired differences, and a split by boss identity and by whether the run that produced the position actually won the fight.

## Tasks

1. Build `rl/act3_replay.py` (or an exam cell set plus a budget flag in `fight_exam.py`, whichever is smaller): collect N Act 3 boss positions from the stores (deterministic sample, seeds recorded), play each at the three budgets with the champion's fight brain and the champion's search settings, write one JSONL row per (position, budget) with the kill, HP left, turns, wall seconds and sims, and a summary table. Tests on a tiny fixture.
2. Smoke: about 30 positions at the three budgets, at most 4 processes, BelowNormal. Put the table and the wall per position in the memo. If 16x is too slow for 30 positions in 30 minutes, run fewer at 16x and say so.
3. Write `ACT3-REPLAY-full.sh` here: the full run (a few hundred positions, all three budgets, 12 processes, BelowNormal, a wall limit of 8 hours, output under `D:/spireline/referee/backlog/act3-week/act3-replay-full/`), taking a `QUIET.lock` line it owns while it runs (tag `act3-replay`, the Windows PID via `$(cat /proc/$$/winpid)`) and removing it at the end. The orchestrator launches it.
4. Land on fork main (Python-only gate; before 10:30Z or after tonight's block). Report to the orchestrator the smoke table (kills per budget, n), the wall per position per budget, and the full run's expected hours.
