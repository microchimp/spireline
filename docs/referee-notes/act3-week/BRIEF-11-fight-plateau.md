# Lane 11: why the fight trainer's gate has promoted nothing since 11-09 (the gym-plateau alert; D57 addendum 2)

Read `D:/spireline/referee/backlog/act3-week/COMMON.md` first. This is a **read-only measuring lane**: no heavy runs (the machine is booked all day by an engine gate, the Test Subject exam, the Act 3 replay and a real-game block), no edits to the daemon, the lab, HANDOFF, STATE or any tree. Measure and explain; propose no fix and change no code.

## The alert

`D:/spireline/referee/LAB/alerts/gym-plateau.txt`, raised 2026-11-20T11:23Z: no promotion for 11.0 days and 55 gated candidates (incumbent v3 since 2026-11-09T12:00:58Z); the last ten verdicts are stage-2 rejects within -0.60 and +0.35 points of the incumbent on 2,000 pairs. D57 addendum 2 (in `D:/spireline/spireline/docs/DECISIONS.md`) calls this a failure to be reported the same day with a diagnosis lane. You are that lane.

## Sources

- `D:/spireline/referee/gym-loop/`: `state.json` (gated verdicts, prefilter figures, promotions, versions, wiring), `loop.log` (segment, gate, prefilter and daily lines), `gate/verdicts.jsonl`, `games/segments.jsonl`, `games/clock.jsonl`, `trainer/` (loss and checkpoint records), `exam/` (the live exam cells, Act 3 cells since 2026-11-20T00:49Z), `players/`.
- The daemon's tree `D:/spireline/fork/wt-gym-loop-run`: `rl/gym_loop.py`, `rl/fight_gym.py`, `rl/fight_exam.py`, `rl/gym_clock.py` (docstrings; read, never edit, never run).
- `D:/spireline/spireline/docs/DECISIONS.md`: D57 and its addenda, D65 addendum 5, D68 addendum 4. `D:/spireline/referee/backlog/act3-week/FIGHT-LOOP-ACT3.md` (lane 9's memo on the Act 3 stratum).

## Questions (each answered with a figure and the file it came from)

1. **Gate resolution.** For every verdict since 2026-11-09: candidate minus incumbent in points, its standard error, the stage, the verdict. How many stage-1 passes, how many stage-2 rejects. The smallest gain the gate can detect at its alpha on 2,000 pairs. Are the 55 candidates indistinguishable from v3 (centred on zero) or slightly worse (centred below)?
2. **The trainer.** Held-out loss per checkpoint since 11-09 (the prefilter lines in `loop.log` carry the policy CE against v3's on the same rows; `trainer/` may hold more). Is it still falling? If the imitation loss keeps falling while the gate's win rate does not move, say so plainly: that is the key fact.
3. **By cell.** For the last five stage-2 candidates, the win rate by cell (act1/act2 x boss/elite/hallway) against v3 on the gate's pairs, where the verdict records carry it. Does any cell gain while another loses?
4. **The prefilter.** How many candidates it skipped since 11-09 and under which rule (the gap against a rejected candidate's gap). Could it hold back candidates the gate would have passed? Compare the gaps of gated and skipped candidates.
5. **The human bar.** The 11-09 reading was survival 64.6 against the humans' 79.8 in 100 on 400 starts. Any later reading in `gym-loop/exam/`, `loop.log` or `state.json`? Has it moved?
6. **The Act 3 stratum** (live since 2026-11-20T00:49Z at share 0.3). Act 3 fights played so far (segment lines `act3-boss human a own b`), candidates gated since then, their verdicts. "Too early to judge" is a fine answer; say when it would not be.
7. **Your reading.** The two or three most likely mechanisms behind the standstill, each with the evidence for and against from the figures above, and the one measurement (not a fix) that would decide between them.

## Output

- Memo `D:/spireline/referee/backlog/act3-week/FIGHT-PLATEAU.md`: plain figures with their sources; no host names, user names or absolute user paths (`D:/spireline/...` is fine). Write nothing else anywhere; the orchestrator records in HANDOFF and STATE.
- Report to the orchestrator in at most five lines: the answer to question 2, the gate's resolution, the prefilter count, your top mechanism, and the memo path. Stay under about 150k tokens.
