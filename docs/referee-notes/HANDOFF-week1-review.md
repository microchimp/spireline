# Week 1 (P0) review, as it stood in HANDOFF.md section 0 before the week-2 review replaced it

## 0. Week 1 (P0) review, 2026-10-23

P0 rounds 1-9 of `PLAN.md` section 11 ran and landed. Fork main is `97b03d1e`, pushed. Every landing kept the corpus at 3,138 of 4,037 identical with 0 regressed. Round notes and reports are in the P0 side-session notes.

**Headline metric (measured, generation 0, 500 paired seeds `E0-2026-10-23`, A10 Ironclad).** Generation 0 is IS-MCTS combat search with resampling and the rules policy outside combat.

| engine | search | wins | win rate (Wilson 95%) | mean floor |
|---|---|---|---|---|
| real game (referee, lockstep) | 60 sims | 0 / 500 | 0% (0-0.8%) | 10.82 |
| emulator | 60 sims | 0 / 500 | 0% (0-0.8%) | 11.47 |
| emulator | 120 sims | 0 / 500 | 0% (0-0.8%) | 11.93 |

- **Transfer gap:** G = 0 (no wins). The paired mean-floor gap, emulator minus real, is +0.64 (95% CI 0.20 to 1.08).
- **Divergence:** 0.99% of lockstep decisions diverge (509 of 51,429). 84% of decisions are ranked; the rest are scored only.
- **Crashes:** 0. The 500 real runs took 604 s at 12 processes.
- **A3 settings (`a3-v1`):** 30 sims for a plain play, 120 for a target or a choice screen, c 0.2. Against gen-0 60 sims on 200 seeds, mean floor is +0.10 (-0.50 to +0.69) at 1-8% less wall time. Not significant; it is adopted for its cost.

**Lane spend against ceiling (estimated, Sonnet-equivalent rounds; Opus counted 1.7x).**

| lane | P0 estimate | spent | rounds |
|---|---|---|---|
| A agent | 6-8 | ~18 | A0a, A0b x2 + review, A1 (Sonnet), 2 Opus amends, events, 2 Opus reviews, 2 fix rounds, integration, A2 + review, A3 (Opus) + review |
| B fidelity | 1-2 | ~2 | B0 x2, review, fix |
| C referee env | 2-3 | 1 | C0 |
| D scheduler | 2-3 | ~1.2 | D0, review |
| E / H6 | 0 | 0.4 | patch list |
| orchestration and review | 2 | ~3 | this session |
| **total** | **13-18** | **~26 (~5-6% of a week)** | |

Lane A is more than 25% over its estimate. The cause is A1: the bridge needed two Opus amends (re-anchoring, mapping, the resample leaks L2/L3) and their fix rounds. If week 2 is also more than 25% over, the lane stops and the owner is told (section 10).

**G0 check (section 8.4).**
- **Measurement table: met (measured).** In `readiness.json` `bench.emu`, at 1 / 8 / 16 processes: 3,889 / 25,554 / 39,344 steps/s; 10,410 / 67,171 / 98,046 clones/s (resampled); 441 / 3,011 / 4,614 sims/s. In `bench.env`, sustained at 8 / 12 / 16 processes: 101 / 118 / 141 decisions/s.
- **PLAY agent plays whole A10 runs on both engines: met.**
- **First agent-ranked list: met.** `D:/spireline/referee/agent/gen0/rank/top20.md` has 218 groups. Architectural groups hold 72.9% of agent weight. 350 runs are outcome-changing (confirmed), but 57% of paired runs end differently anyway, so that count is weak.
- **Lab runs the new job kinds for 48 h: in progress.** The owner allowed the restart; the runner restarted on fork main 97b03d1e at 2026-10-23T09:44:12Z, so the 48 h window ends 2026-10-25T09:44Z. The history before the restart: The runner has run since 17 Oct on pre-D0 code and does not read `LAB/jobs.json`. Restarting the scheduled task was refused by the permission check, so the owner must restart "Spireline fix lab". The 48 h clock starts then. `jobs.json` is ready: selfplay at share 0.5 and score-real, both with `a3-v1` from `wt-a3`; nightly bench-emu and bench-env; train disabled.

**Findings that need a decision or an owner action.**
1. **Section 8.1 bar crossed (measured).** The agent side with `a3-v1` makes 21.4 decisions/s per core and 242 at 16 processes. That is above 80% of the env's sustained 118/s at 12 processes, so by the plan's rule a faster real-game host is indicated.
   - Against it: the real game is not a bottleneck today, because a 500-run scoring block takes 10 minutes and training runs on the emulator.
   - Recommendation: no host build. Re-test the bar if real-game training (D18, V_run fine-tuning) enters P2. Owner decision.
2. **Owner: restart the lab task** (see G0).
3. **Owner: H6 approval line** in `SECURITY_REVIEW_ADDENDUM_1.md`. The H2 and H3 status is recorded there.
4. **GPU training: done 2026-10-23.** The owner made `D:/spireline/venv-gpu` (torch 2.14.1+cu132, RTX 3080 visible, matmul checked), separate from the emulator venv; `train` should use it. History: The emulator venv's torch is 2.12.0+cpu, so `train` runs on CPU. A CUDA torch needs a network install, by the owner. The lab runner is sequential, so `train` cannot overlap `selfplay`.
5. **The ten-minute env cliff recurred at minute 13.9 (measured, C0).** All 12 games waited at once while CPU fell from about 40% to 3%. Memory and commit were flat. The cause is not named. Unchecked suspects: the single Python bench parent, paging and standby-list pressure. This goes to C1.

**Rebuild lane (D23, Tier 1 kernel stage), 2026-10-23.** Started; fork branch `rebuild/tier1-kernel` (worktree `fork/wt-rebuild`), cap 25 reviewed rounds a week (Opus 1.7x). Rounds spent: 0 landed, 3 in flight (R1 manifest, R2 `IEngine` with `Fight` on it, K0 kernel design review). Design: `fork/wt-rebuild/docs/rebuild/TIER1_KERNEL.md`. **For the P1 session (A1b):** the rebuild lane moves `tools/emudump/Reanchor.cs` onto `IEngine` (round R3, next after R2) and lands it first; start A1b's native Reanchor export on top of that landing, or say so here if A1b must go first. The Codex-stop census is deferred to G1 (a Tier 2 input). Local tables and the `L` patch are in this lane since 2026-10-23 (API-credit lane on hold); the `L` patch adds one trace-mode-only patch file under `referee/driver` (the P1 session's area) and a spec key, nothing else there, and is posted here before it starts.
- *2026-10-23, late.* R1 manifest, K1 descriptor/generator, R2 (`IEngine` + `Fight`) and R3 (`Reanchor` on `IEngine`; the old engine's state loader is one file-free class, `tools/emudump/Engines/Old/OldAnchor.cs`, that A1b can move into the DLL behind a native export) are reviewed and in the full gate for landing on fork main now. R4 (`Setup`, `NetState`) and K2b (a per-combat card uid on `CardInstance`, invisible to every output) are reviewed or in review; R5 (`HookProbe`, `Trace`, `RngLog`, `StateWalk`) runs. **`L` patch starts next:** one new file `referee/driver/ListenerTrace.cs` (postfix on the two `IterateHookListeners`, `L` records, spec key `trace_listeners`, off unless asked) plus one line in `Trace.cs` widening the hook-name filter to Modify*/Should*/Try*; smoke recordings on `referee/game-trace` only. **For Lane B:** the uid audit found the old engine's Bolas return adding a second Bolas no pile gave up (3 corpus fights).
- *2026-10-23 13:00Z.* **Landed and pushed: fork main `ccb04363`** (R1 manifest, K1 descriptor/generator, R2 `IEngine` + `Fight`, R3 `Reanchor` on `IEngine` with `OldAnchor`, `tools/fidelity/byte_proof.py`). Gate: C# 6,673 (0 failed), EmuDump 216, corpus 0 regressed, Python 0 new failures except `test_live_search ... test_a_parallel_search_on_a_loaded_snapshot_beats_one_worker`, a throughput assertion that failed once under load and passes 2 of 3 alone (it passed in the previous gate; the engine is byte-identical). Corpus baseline for `ccb04363` waits for `QUIET.lock`. **A1b can start on main now.** Every EmuDump output is byte-identical to main `97b03d1e` (9 modes x 4,043 corpus fights); `byte_proof.py` and the rng-log readers run EmuDump with `rng_diff.NO_INLINING`, because `RngLog`'s stack-derived caller labels vary with tiered JIT (one build against itself differed in 5-213 fights). **For Lane B (second finding):** after a snapshot-loaded selection, `CombatState.HeldPlayedCard` stays set once the card is filed (cleared only by `ReleaseHeldPlayedCard`, a no-op while a screen is open; the snapshot reader never restores it), so the next step can file the card again: an extra Hidden Daggers in document-loaded searches. Not reproduced yet; suggested test: step once more after both answers, expect one Hidden Daggers and `HeldPlayedCard` null.
- *2026-10-24 (UTC 2026-10-23 ~15:00Z).* **Landed and pushed: fork main `0cd771d1`** (R4 `Setup`/`NetState`, R5 `HookProbe`/`Trace`/`RngLog`/`StateWalk` onto `IEngine` (allowlist 21 -> 13); K2b per-combat card uid, also on A1b's native fight-start path; K2 listener order over the old state (`Core2/OldState.cs`, `Listeners.cs`, `NotModelled.cs`; agrees with `game_order_key` on 118,738 scenario pairs); the trace-mode `L` patch (`referee/driver/ListenerTrace.cs`, spec key `trace_listeners`; on 10 game fights, 50,073 dispatches all in `game_order_key`'s order). Gate: C# 6,716 (0 failed), EmuDump 226, Python 0 new failures, corpus 0 regressed; byte proof 9 modes x 4,055 fights identical to main `da713391`; **Codex walk identical run for run** (20,294 runs, 15,092 complete) and refset v2 0 worse/0 better between `ccb04363` and the candidate. H6 row updated (Spireline `3d65f01`). Corpus baseline for `0cd771d1` waits for `QUIET.lock`. **Calibration after the first ten rounds:** 13.25 reviewed rounds spent (Opus 1.7x; amends ran ~1 extra worker run per round against the plan's 0.36); kernel stage re-estimated at ~36 rounds (30-45), family migrations ~39 (25-55), **Tier 1 central ~75 (55-100)**, under the 120 stop line, so the lane continues. **For Lane B (third finding):** `power_aliases.json` lacks ShivDamage -> AccuracyPower (K2's mapping keeps it in code; adding it to the file changes `fight_compare` and reanchor's judging, so it is Lane B's call).

**API-credit lane, 2026-10-23 (orchestrator).** On hold: the owner is holding the credit back, so no API-key session starts and `API_CREDIT_PLAN.md` does not run until the owner says so. Effects: B1 belongs to the P1 session from now (not from day 4), at 3-5 rounds a week while the rebuild lane runs: the by-family report first, then minimal repros through the lab, then the top single-site kits. The `L` patch and the local tables go to the rebuild lane (the 2026-10-26 hand-back above is void). The K0 review stands in for the batch-priced Tier 1 review. The credit expires in early November; if it is started later, its plan runs as written.

**Next briefs (P1 week 2, in order).**
1. **C1 (Sonnet):** cliff instrument and rerun (typeperf page faults, standby list, disk queue, parent-process CPU and pipe waits); recycle at about 60 runs if memory pressure is the cause; the env action-space gaps (choose 0, card-reward alternatives, potions outside fights); the `character` key. A new game copy is an owner action (firewall rules are per path), so reuse the existing copies.
2. **B1 (Sonnet, fixers):** the three grade-C kits in `agent/gen0/kits/` first need minimal repros (lab `runs` repro). Then fix through bug process v2, one reviewer each. Architectural groups wait for G1. Report divergence by hook family (`agent/gen0/rank/by_family.md`: agent weight and architectural share per family, cumulative curve) before and after the cycle; G1 now chooses between two rebuild tiers on it (`PLAN.md` section 8.3, D23). While the API credit is held back, B1 is the P1 session's from the start, capped at 3-5 rounds a week with the by-family report first.
3. **A2b (Sonnet):** the generation loop. Selfplay on `a3-v1`, `train` on CPU (Gumbel ExIt prior plus V_run DMC, ONNX-exportable modules), promotion on a fresh 2,000-seed emulator E-block, with `LAB/train/ready-<gen>` and `LAB/score/pending` markers. Score-real's paired emulator reference must be re-run with `a3-v1` (`jobs.json` still points `--emu-dir` at the 60-sims run).
4. **A1b (Sonnet):** re-anchor at fight start through a native Reanchor export (33 of 35 remaining re-anchor failures), to lift the ranked share from 84%.
5. **Leaks follow-ups (Sonnet):** the L8 table scan, or a synthetic-table test, per the reworded DESIGN.md 7.6; `MapChoices` exposes the next encounter id (L4: the firewall must drop it); an L3 shop test.
6. **D1 (Haiku):** the weekly mix re-weighting rule from `yield.tsv`, once the lab has run the new kinds.
7. **Weekly review (Opus):** G1 needs two fix cycles. The architectural share (72.9%) already exceeds G1's 50% trigger, so the week-4 decision leans to the rebuild unless fixes move it.

