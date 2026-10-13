# Efficiency ideas (unverified)

This file lists ideas for making Spireline cheaper, faster or more trustworthy. Seven independent research lenses produced them in October 2026: online resources, local game files, fidelity verification, search, learning, compute and process. The raw list had 59 ideas. Here, near-duplicates are merged (52 remain), each idea gets a rough priority, and ideas are grouped by the pipeline stage they act on.

**Written before D15 and D16 (2026-10-13).** Ideas that assume Defect first, the sts2-cli fork as referee, or patches offered to an upstream dependency are superseded: the simulator is now our own fork, refereed by the game's own `sts2.dll` run headless, Ironclad first. [SIMULATOR.md](../SIMULATOR.md) says which simulator ideas the plan takes up.

**Every idea here is UNVERIFIED.** Nobody has checked the claims, the line references or the gain estimates. Before building anything, answer the idea's **Check first** question, record the answer in `LOG.md`, and only then decide. If the answer changes a decision, add a dated entry to `docs/DECISIONS.md`.

**How to read an entry**

- Gains are the idea authors' estimates unless a measurement is cited. Treat them as hypotheses.
- `file:line` references point into third-party repos as read in October 2026, and lines may have moved. Plain paths (`FINDINGS.md`, `HANDOFF.md`, `rl/combat_mcts.py`, `CardEffects.cs`, ...) are in r33hab/sts2. `RunSimulator.cs`, `Program.cs` and `HeadlessCombatHooks.cs` are in sts2-cli: the copy vendored in mingxuan-he/sts2-agent unless the entry says wuhao21/sts2-cli. `McpMod*.cs` is r33hab/STS2MCP. "DESIGN §x" and `DESIGN.md:n` refer to [docs/DESIGN.md](../DESIGN.md).
- Priority (high / medium / low) is a rough call on leverage, the cost of the first check, and how soon Spireline needs it. Phase 1 is combat labels at A10, and the learned components wait for ledger signals (D5), so most learning ideas rank lower for now.
- IDs (`data-1`, `fid-3`, ...) are local to this file.

**Constraints every idea must respect**

- No LLM components in the system (D7, D14). Claude Code as the development agent is tooling, not part of the system (see the end of this file).
- Hardware: an always-on Windows PC running native Windows, no WSL ([pc-setup/WINDOWS.md](../../pc-setup/WINDOWS.md)); a Mac; cheap cloud CPU for bounded bursts only (D9). Claude Code's sandbox does not exist on native Windows.
- Review before building or running any third-party code (D3). Repos without a licence are read-only: re-derive, never copy.
- The Spire Codex run export is a test corpus. Nothing is trained or tuned on it (D13). Ideas that would train on it are flagged and need a new decision first.
- Everything is played at A10 (D11). No bots on Daily runs or leaderboards.
- No game code, decompiled source or raw human logs, saves or run files in this repo (`CONTRIBUTING.md`).

## Index

| ID | Priority | Idea |
|---|---|---|
| data-1 | high | Passive flight recorder for the game's own logs, saves and replays |
| data-2 | medium | Real A10 Defect fight starts rebuilt from human runs, as the training fight distribution |
| data-3 | low | Pretrain V_run and FightNet on human run outcomes, then fine-tune |
| data-4 | medium | Columnar data layer: Parquet, cached features, positions as replay keys |
| sim-1 | high | Make the sts2-cli referee run at logic speed |
| sim-2 | medium | Profile the NativeAOT step; compiler/runtime matrix |
| fid-1 | high | The game's own desync checksum as the per-action comparator |
| fid-2 | high | Check the referee with the game's built-in replay verifier |
| fid-3 | high | Inventory and taint sts2-cli's TestMode, stub and patch paths |
| fid-4 | high | Free test oracle from displayed previews, orb values and playability |
| fid-5 | medium | Event ledger from the real engine, diffed against the emulator |
| fid-6 | high | Game DLL and emulator in one process, compared function by function |
| fid-7 | high | Real game headless and decoupled from real time |
| fid-8 | medium | The built-in AutoSlayer as a full-run fuzz driver |
| fid-9 | low | Custom-mode modifiers as coverage amplifiers |
| fid-10 | medium | Exhaustive small-scope tests of Defect orbs and Focus |
| fid-11 | medium | Measure unverified emulator code the oracle uses; gate gold on it |
| fid-12 | medium | Swarm configurations for the differential fuzzer |
| fid-13 | medium | Known-defect registry for the referee, from the fork network |
| fid-14 | medium | Cross-port bug transfer from sibling StS2 ports |
| fid-15 | medium | Bug-for-bug corpus from later patch notes and fix mods |
| orc-1 | medium | Replace the tempo rollout: native playout, weights fitted by simulation balancing |
| orc-2 | medium | Event-keyed randomness to keep CRN coupled |
| orc-3 | low | Maximally coupled draw orders across candidate decks |
| orc-4 | low | Multifidelity control-variate estimator for label gaps |
| orc-5 | high | Simulation-based calibration of the hidden-state sampler |
| orc-6 | medium | π_ref as a pure function of the info state, memoised |
| orc-7 | medium | Race end-state classes with first-action sets; merge twin enemies |
| orc-8 | medium | Sound pruning: Pareto dominance and HP ceilings |
| orc-9 | medium | One scheduler across label positions, with futility stopping |
| orc-10 | medium | Selective relabelling after emulator fixes |
| lrn-1 | high | Give the combat net Defect's orbs; keep the end-turn probe until then |
| lrn-2 | medium | KataGo's self-play data recipe for combat ExIt |
| lrn-3 | low | Auxiliary soft-policy and short-horizon value heads |
| lrn-4 | medium | Order-invariant line targets (partial-label loss) |
| lrn-5 | low | Compositional encounter inputs and era inputs for data transfer |
| lrn-6 | low | Luck-corrected V_run training targets |
| lrn-7 | low | Exact human states as self-play start points |
| lrn-8 | medium | Adopt a sibling project's measured results as priors; replicate three |
| eval-1 | medium | Prediction-powered SpireBench aggregates |
| eval-2 | medium | Human-par fight benchmark from Spire Codex data |
| cmp-1 | medium | Parallel headless real-game fleet on the PC |
| cmp-2 | low | Tokenize in C# into the batch buffer |
| cmp-3 | medium | Preemptible work units on cheap ARM cloud |
| proc-1 | medium | Fast regression guard for the fix loop |
| proc-2 | medium | Build-vs-build trajectory diff, changed trajectories to the referee |
| proc-3 | low | Overnight agent harness that never stops for a prompt |
| proc-4 | medium | Per-mismatch context packs and a usage budget per fix |
| proc-5 | low | Two-way decision inbox and a fortnightly hands-on session |
| proc-6 | medium | Watchtower: heartbeats, dead-man's switch, build-hash tripwire |
| proc-7 | medium | Patch blast radius, worked out before the patch lands |
| proc-8 | low | Our A10 Defect fixtures in upstream's CI |

## Data

### data-1 · Passive flight recorder: archive the game's own logs, saves and replays on both machines

**Priority: high.** Cheap, needs no machine time, and the logs it would keep are being deleted now. *Merges two raw ideas.*

Without any mod, the game writes a near-complete record of every session and then throws it away. `godot.log` (Godot keeps only 5 files) logs every card play with its target, every potion use, in-combat "chose cards" selections, map votes, encounter creation, every enemy move as it runs, and each reward rarity roll with its raw value and pity offset. `current_run.save` is rewritten at every room entry and after each combat, and deleted at run end. It is plain JSON holding the counters of all 12 RNG streams, per-player odds state, relic grab bags, the pre-rolled encounter queues per act and `unlock_state`. `replays/latest.mcr` is overwritten every combat, and Steam Cloud keeps only 100 `history/*.run` files. A small watcher (launchd or fswatch on the Mac; a FileSystemWatcher scheduled task on the PC that also covers the modded save folder) copies each closed log, each save version and each `.mcr` into a content-addressed archive keyed by run seed, and merges `.run` files from both machines. An offline parser joins log, saves and `.run` into one action record per run. The checker loads each room-entry save into the emulator (and into sts2-cli, whose `LoadSave` already takes SerializableRun JSON, `RunSimulator.cs:547-559`), replays the logged plays, and requires the next save's RNG counters, HP, potions, gold and deck to match. Logged enemy moves check the AI turn by turn, and each logged "Rolled x" float is a bit-exact check of reward RNG and pity logic.

- **Expected gain:** Every game played on either machine becomes a mod-free lockstep test, with no extra play time and about 1–8 MB per run. Achievements stay on. The per-stream counters are a strong checksum: one extra `combat_orbs` or `combat_targets` roll shows up even when HP happens to match, and a divergence is pinned to one stream in one room. It keeps working when the mod breaks on patch day. It also feeds fid-1, fid-2 and lrn-7.
- **Effort:** 3–4 h for the watchers and archive on both machines; 1–3 days for the parser and replay checker (extending `scripts/replay_real_run.py` and `fidelity_replay.py`).
- **Precedent:** r33hab treats `current_run.save` as ground truth for run generation (`PLAN.md:699`), compares live RNG stream positions per turn through the mod (`scripts/combat_sweep.py:1128`), and used one rarity-roll log line to settle a rarity question (`HANDOFF.md:694-699`). ytcs/sts2-solver traces carry a history log plus all RNG streams per action (`docs/simulator.md`). No precedent known for harvesting save snapshots.
- **Risks:** Log lines don't distinguish duplicate cards that differ by upgrade, enchantment or cost modifier, so replay must branch (the counters settle it). End of turn is only implied by monster-move lines, and random effects such as orb-evoke targets are not logged. Some saves are mid-room (`pre_finished_room`). The copier must not lock a file the game is writing (copy after close, retry). Log verbosity can change in a patch. Profile-dependent generation (`PLAN.md:705`) breaks fixed-profile generation checks on a partly unlocked profile, but room-level combat checks still work because each save carries its own `unlock_state`. Useful only while play stays on v0.107.1. The archive is personal data and stays out of the repo.
- **Check first:** Does `godot.log` record every in-combat decision (card and target, potion, "chose cards") completely enough that replaying a Defect combat from its room-entry save reproduces the next save's `rng.counters` exactly?

### data-2 · Real A10 Defect fight starts rebuilt from human runs, as the training fight distribution

**Priority: medium.** Could give the learned components real Act 2–3 fights, but RL is gated (D5) and the Spire Codex part conflicts with D13. *Merges two raw ideas. Shares the rebuild pipeline with eval-2.*

Human `.run` records (schema_version 9 in both local files and the Spire Codex v0.107.1 export) hold enough to rebuild each fight's starting state. Per floor they have `rooms[].model_id` (the encounter), `monster_ids`, `damage_taken`, `current_hp`/`max_hp`, `turns_taken`, card choices, upgrades, removals, transforms, enchants, relic and potion choices and use, and the final deck carries `floor_added_to_deck`. Walk each run forward to rebuild deck (with upgrades and enchantments), relics, potions, HP and floor at each A10 Defect fight, and drop runs whose rebuilt final deck doesn't match `players[0].deck`. Deal each start with `native.reset_arena`, which already takes the deck (negative ids for upgrades), enchantments, relics, potions, HP, max HP, ascension and floor (`src/sts2_gym/native.py:983-1021`). Stratify by act and room type, and mix the bank with the existing synthetic generator as the fight set for combat ExIt and FightNet. Labels still come from our own searcher, so no human play enters them. Start with local run history. Training on the Codex export needs a new decision that replaces D13's "nothing is trained or tuned on it".

- **Expected gain:** Self-play barely reaches the fights that decide runs. r33hab's generation 0 died in Act 1 95.4% of the time and never reached Act 3 (`rl/run_train/FULL_RUNS.md:111`). The default generator deals Overgrowth hallway fights with starter plus random cards (`train_combat.py:69`, `real_fights.py:3-8`), "a position no real run is ever in" (`FINDINGS.md:91-92`). The Codex export holds about 302k A10 Defect v0.107.1 fights (Spire Codex aggregate) at realistic Act 2–3 deck strength, for zero self-play cost. ytcs found its synthetic generator dealt core cards far below expert rates (Noxious Fumes 16.7% vs 76.9% of expert decks) and left 29 power and 50 card embeddings untrained (evidence E46, E51). Combat learning stops depending on run-policy quality.
- **Effort:** 1.5–2 days for parser, rebuild validator, ID mapping (`CARD.X` ↔ entry names in `Generated/Cards.g.cs`) and dealing; 1–2 more days for the bank and the mixing.
- **Precedent:** r33hab's own move from synthetic to "real fights" (`rl/prior_loop/real_fights.py`). ytcs/sts2-solver evidence E46/E51 (https://github.com/ytcs/sts2-solver/blob/main/docs/research/evidence.md). AlphaGo, AlphaStar and KataGo seeded learning from human positions.
- **Risks:** D13 as written forbids training on the Codex export, and its licence is NOASSERTION (`DESIGN.md:121`), so even with a new decision use it for start states only, never as ground truth. Rebuilds go wrong around Ancients, transforms and enchant edge cases (drop runs that fail the deck check). Filter out modded characters and abandoned runs. Uploaders are self-selected, and human decks reflect human drafting habits, so mix rather than replace. Never read the banned `draw_order`/`rng_state` fields (`DESIGN.md:176`); resample RNG at fight start.
- **Check first:** For what fraction of A10 Defect v0.107.1 runs does forward rebuilding from `map_point_history` exactly reproduce the final `players[0].deck`, upgrades and enchantments included? And how far are r33hab's generated card and relic frequencies from human decks at the same floor (top-20 card rates or KL)?

### data-3 · Pretrain V_run and FightNet on human run outcomes, with a policy-source token, then fine-tune on self-play

**Priority: low.** Needs a new decision against D13, and RL-2 is gated and Phase 2.

Reuse data-2's parsed rows as supervised data about outcomes. FightNet rows map (deck, relics, potions, HP, encounter, ascension) to the 22-class HP-lost/death label and `turns_taken`, with source = human. V_run rows map the afterstate at every floor to the final floor or a win. Train across characters and ascensions with character, ascension and source inputs. Then fine-tune on emulator self-play with source = π_ref, and query only with source = π_ref. Hold out by run, as r33hab already requires.

- **Expected gain:** V_run's core problem is that there are no wins to learn from: r33hab's generation 0 won 0 of 1,999 runs (`FULL_RUNS.md`), and DESIGN §5.5 expects V_run to start "with almost no wins". Human A10 data contains wins and real Act 2–3 trajectories, so V_run could rank decks, relics and HP across all three acts before self-play gets there, and pass the Brier-skill-vs-V0 gate several generations earlier. FightNet would get millions of human fight records, against a 400k-fight emulator cap. Guess: worth several nights of self-play.
- **Effort:** 1–2 days on top of data-2's parser.
- **Precedent:** A dev.to series on StS1 run-win models trained on per-floor decks labelled by eventual win (https://dev.to/doronsinger/part-3-good-models-finish-last-2n6a). A Hearthstone deck win-rate network (FedCSIS 2018, https://annals-csis.org/proceedings/2018/drp/pdf/365.pdf). AlphaGo and AlphaStar supervised pretraining before RL.
- **Risks:** Humans play combat differently from π_ref. The source token absorbs a level offset, not every interaction, hence the gate on emulator held-out Brier. Uploader selection bias; abandoned runs (treat as censored, or drop). Licence terms. Newer versions (v0.108–v0.111, about 1M more runs) have different rules, so never pool them without a version token and a separate check.
- **Check first:** At equal self-play data (say 2k and 8k runs), does a human-pretrained, fine-tuned V_run beat a from-scratch V_run on held-out emulator runs' Brier skill, and on per-decision ranking agreement with Tier B silver labels?

### data-4 · Columnar data layer: Spire Codex to Parquet, cached encoded features, positions as replay keys

**Priority: medium.** About a day, and every later use of the Codex corpus and of self-play shards gets cheaper.

(1) Pass over the v0.107.1 Codex export once. It decompresses about 11x, to roughly 23 GB of JSON, so stream it: `gzip -dc | filter A10 Defect and the needed fields | Parquet via DuckDB`. Later queries then take seconds instead of a full reparse. D13 records the file as already downloaded, so the Parquet step matters more than the streaming. (2) r33hab self-play shards are gzipped JSON RunViews, re-read and re-encoded on every fit (`rl/run_train/shards.py:1-14`, `train.py:345-393`). Add an Arrow or npy memmap feature cache keyed by (shard sha256, FEATURE_VERSION, encoder code hash), so each generation encodes only new shards and the GPU trains straight from mmap. (3) Store positions as (seed, action prefix, root-state hash) replay keys of about 0.5 KB, and keep zstd-dictionary snapshots only for positions imported from the live game. Replay keys also serve orc-10.

- **Expected gain:** One 15–30 min pass instead of a 23 GB parse per experiment that touches community data. V_run and FightNet fits stop paying to decode all data as JSON (about 1 core-hour or more per generation at tens of millions of afterstates). Position storage shrinks about 10–50x.
- **Effort:** About 1 day.
- **Precedent:** DuckDB reads gzipped JSON lines natively (https://duckdb.org/docs/stable/data/json/overview). zstd dictionaries for small records (https://github.com/facebook/zstd#the-case-for-small-data-compression).
- **Risks:** Schema drift between Codex `schema_version` values. The filter must keep the fields replay verification needs (seed, per-floor choices). A wrongly keyed cache serves stale features. Treat downloaded data as untrusted: parse it in its own directory with `python -I`. Parquet files stay under the gitignored `data/`.
- **Check first:** Is the v0.107.1 export a single gzip stream with exactly one run per line all the way through, so a one-pass streaming filter works?

## Simulator

### sim-1 · Make the sts2-cli referee run at logic speed: measure, then remove sleep-polling and add batch and replay modes

**Priority: high.** A 1–2 h measurement decides a possible 10x on the main verification bottleneck. *Merges three raw ideas.*

sts2-cli manages about 20 decisions/s (about 49 ms each on Windows), which looks like waiting, not game logic. The mingxuan-he copy already runs game continuations on a queue-based `HeadlessFrameSynchronizationContext` (`RunSimulator.cs:40-56`). But `PumpUntil` loops `Pump(); if done break; Thread.Sleep(1)` (`:1136-1154`), `Cmd.Wait` resumes on the next pumped frame, and other paths have fixed sleeps: Sleep(100) "between phases" (`:1099`, probably hit at every end turn), Sleep(200) after rest options (`:1576`), and Sleep(5) or Sleep(10) polls (`:1277`, `:1343`, `:1551`, `:1607`, `:1887`, `:2910`). It also makes 21 `Task.Run` hops and exchanges one JSON line per action (`Program.cs:79`, `:241`). On Windows' default timer Sleep(1) costs about 15.6 ms, so 49 ms per step fits three timer ticks. Steps: (1) measure process CPU time vs wall time, plus a stopwatch histogram over 1,000 combat actions, on Windows and on macOS. (2) Cheapest fix: `timeBeginPeriod(1)` at startup, with an opt-out from power throttling. (3) Proper fix: an event-driven drain. `Post()` signals an event, `PumpUntil` loops without sleeping while work is queued and waits on the event only when the queue is empty, and each fixed sleep becomes a wait on the specific task or phase change. (4) Add `replay` (seed and action list in, per-step state digests out) and `batch` (scenario files in, traces out) commands, so Python stops paying a round trip per action. (5) Run old and new paths side by side for a week and require byte-identical traces, then run one process per core.

- **Expected gain:** If logic is about 1–3 ms per action, 10–25x per process. At 8–12 processes that is about 2,000–5,000 real-engine actions/s, against about 200 now. ytcs reports about 10 ms per fight in batch mode and a 661-action whole-run replay in about 2.5 s on the same game code. That makes lockstep testing, mismatch shrinking and "referee on every gold label" (instead of a 2% spot check) affordable. If the process turns out CPU-bound, the gain is near zero, and the measurement points at profiling instead.
- **Effort:** 1–2 h to measure; half a day for the timer fix plus a trace-equality check; 1–3 days for the drain and the two commands; one overnight equivalence run.
- **Precedent:** Zaaacqwq/SlayTheSpireRL found that a Sleep(1) spin loop in sts2-cli costs about 15.6 ms per iteration on Windows, and reported 20.48/73/123/140 steps/s at 1/4/8/16 workers (https://github.com/Zaaacqwq/SlayTheSpireRL/blob/main/plan/timeline.md). Windows timer resolution rules since Windows 10 2004 (https://randomascii.wordpress.com/2020/10/04/windows-timer-resolution-the-great-rule-change/). ytcs/sts2-solver's single-thread drain (`oracle/combat/Pump.cs`) and `batch` command (https://github.com/ytcs/sts2-solver; no licence, so reimplement the generic pattern). Controlled single-threaded scheduling of async code for deterministic tests: Microsoft Coyote (https://github.com/microsoft/coyote).
- **Risks:** Some sleeps may hide real races, and new pump timing can reorder thread-pool continuations, so traces must stay identical and be checked against the live game. Some handlers deliberately run on the thread pool so that card-selection prompts can block (`:1277`, `:1343`, `:1551`, `:1607`). Draining on one thread could deadlock there, so those prompts need an explicit "pending selection" exit. Windows 11 may ignore timer requests from background processes unless they opt out of power throttling. It is a local patch to third-party code, carried forward on every upstream update and reviewed under D3. TestMode is on (`:3059`), and ytcs documents two TestMode quirks: Rolling Boulder damage batching and the bundle-choice screen.
- **Check first:** Over 1,000 scripted combat actions, how does sts2-cli's CPU time compare with its wall time, and what share goes to sleeps, polls and per-action JSON I/O? If waiting is above about 80%, the 10x is real.

### sim-2 · Profile the NativeAOT step natively and run a compiler/runtime matrix

**Priority: medium.** Every downstream number scales with step cost, but the gain is a guess until a profile exists.

The emulator step takes about 56 µs (median) and allocates 4 KB, and the remaining cost "has not been located yet" (`docs/agent-interface.md:385-386`). End of turn costs 12x a card play (`:349`). Profile a fixed benchmark with samply, which runs on Windows and macOS: 2,000 seeded tempo-rollout fights over 5 A10 Defect encounters from Acts 1–3. Likely hot spots are visible in the source. `HasRelic` is `state.Relics.Any(relic => relic.DefId == relicId)`, a capturing lambda plus an interface enumerator on every call (`RelicEffects.cs:1773-1774`). It has 154 call sites, about 22 of them inside `ApplyStartOfPlayerTurn` (`:969-1199`), the same pattern upstream already fixed in `BuffSystem.Get`. Defect card dispatch switches on strings (`switch (def.Name)`, `CardEffects.cs:5569`). About 200 LINQ calls sit across CombatEngine, CardEffects, RelicEffects and EnemyAI. Run a matrix: net9 NativeAOT (current, no OptimizationPreference), net10 NativeAOT with `OptimizationPreference=Speed`, and CoreCLR JIT with Dynamic PGO, measured with the existing StepCostProbe. Then fix the top hot spots, for example with a per-combat relic bitset and int-keyed dispatch.

- **Expected gain:** Plausibly 1.3–2x on combat step throughput, which scales sims/s, label core-hours and self-play. If JIT with Dynamic PGO beats AOT by more than 20%, host the planned C# search loop as a JIT app.
- **Effort:** 1 day to profile and run the matrix; 1–3 days of targeted fixes.
- **Precedent:** Upstream's StepCostProbe allocation work (`agent-interface.md:358-386`). .NET 10 escape analysis and stack allocation for delegates and small arrays (https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime). `OptimizationPreference=Speed` for Native AOT (https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/optimizing). samply (https://github.com/mstange/samply).
- **Risks:** Refactors can change behaviour; the 32 committed run traces and about 3,650 tests are the guard. Damage maths uses float (`BuffSystem.cs:239-280`), so traces must be identical across runtimes and builds. The profile could be flat. Fixes are patches to a third-party dependency, so offer them upstream.
- **Check first:** In a samply profile of the fixed rollout benchmark, do 10 or fewer functions account for at least 30% of combat-step time?

## Fidelity

### fid-1 · Use the game's own desync checksum (NetFullCombatState → XxHash32) as the per-action comparator

**Priority: high.** The check is a read of the decompile, and a yes turns lockstep comparison into one integer per action.

sts2.dll v0.107.1 contains a checksum system for lockstep multiplayer. Its strings include ChecksumTracker, GenerateChecksum, SendPostActionChecksum, NetFullCombatState, XxHash32, NetChecksumData, ReplayChecksumData and "State divergence detected! … LOCAL STATE DUMP / REMOTE STATE DUMP". The single-player replay writer also records checksums into `latest.mcr`, whose header carries the version, the commit and a model-ID hash that matches the one in `godot.log`. Plan: (1) in sts2-cli, subscribe to ChecksumTracker's event, or call GenerateChecksum after each action, so the real engine emits a 32-bit digest per action. (2) Port NetFullCombatState's serializer, the packet writer and XxHash32 into the emulator once; the console's `dump` command writes the ModelId database for ID mapping. Lockstep tests then compare one uint32 per action and dump full state only on a mismatch, with the game's own "REPLAY STATE DUMP" format as the diff target. The same port checks the emulator offline against the checksums in archived human `.mcr` files (data-1), with no real engine running.

- **Expected gain:** Upstream calls canonical state serialization "the hard part" of per-step replay verification (`docs/replay-verification.md:93,108`). The developer has already decided which state matters for lockstep, so hand-kept field-skip lists and false-divergence triage go away. Divergences are pinned to the exact action, the digest is a free key for deduplicating mismatches, and every archived `.mcr` becomes an offline exact test.
- **Effort:** 0.5 day for the sts2-cli hook; 2–5 days to port the serializer (reading a local decompile that is never committed).
- **Precedent:** Deterministic-lockstep games use per-turn sync hashes with state dumps on mismatch: Age of Empires (https://www.gamedeveloper.com/programming/1500-archers-on-a-28-8-network-programming-in-age-of-empires-and-beyond) and Factorio's desync reports (https://wiki.factorio.com/Desynchronization). StS2's own multiplayer divergence detector is the direct precedent.
- **Risks:** NetFullCombatState may leave out state the emulator needs (hidden draw order, RNG positions), so pair it with the RNG counters. Net IDs and card-instance IDs must be assigned the same way, or normalised. The serializer can change in a patch, so pin it to the model-ID hash. A port from decompiled code needs the usual care, and no decompiled source goes in this repo.
- **Check first:** Does GenerateChecksum run after every action in single-player combat, and does NetFullCombatState cover pile order and RNG state, so that equal checksums imply equal gameplay state?

### fid-2 · Check the referee: replay human `.mcr` files through sts2-cli with the game's built-in replay verifier

**Priority: high.** The only free test of sts2-cli against combats recorded by the real GUI engine.

sts2-cli is the planned referee for Act 2–3 parity and for spot checks of gold labels. But it stubs Godot, and it has known stub bugs: the Gardener runaway and a Kaiser Crab false win (`DESIGN.md:424`). The release DLL ships a combat replay runner: NetReplayGameService, LoadReplay, LoadReplayChecksums, CheckAgainstReplayChecksum, a "Choose Replay" picker in the debug multiplayer test scene (console `multiplayer test`, which needs `full_console` in settings.save), and a "Replay state divergence! … REPLAY STATE DUMP" message. Wire NetReplayGameService into sts2-cli in place of the NetSingleplayerGameService it uses now (`RunSimulator.cs:274-276`), then replay every archived human `latest.mcr` from data-1. The real engine recorded those, so any checksum divergence is a sts2-cli stub or harness bug, found before it can certify wrong emulator behaviour. Confirm the path once by loading one `.mcr` in the GUI test scene.

- **Expected gain:** Without it, every lockstep mismatch against sts2-cli has an unknown chance of being sts2-cli's fault, and every match could certify a bug both share. This turns trust in sts2-cli into a measured pass rate over real fights, and catches stub bugs like the Kaiser Crab false win automatically.
- **Effort:** 1–2 days for the replay mode and batch runner; 1 h for the manual GUI check.
- **Precedent:** The game's own debug replay button and divergence dump. Emulator projects routinely test the reference before trusting it (for example, Dolphin's FIFO player regression runs).
- **Risks:** The replay runner lives under `Nodes.Debug.Multiplayer.NMultiplayerTest` and may need the scene tree or extra stubs. A `.mcr` covers combat only, so map, shop and event logic stay untested. The model-ID-hash check rejects replays from other builds, which is correct but limits the corpus to v0.107.1.
- **Check first:** Can sts2-cli run NetReplayGameService on a recorded `latest.mcr` headlessly, or does the replay path need the NMultiplayerTest scene tree?

### fid-3 · Check the referee before trusting it: inventory sts2-cli's TestMode, Godot-stub and Harmony-patch paths, and taint any step that uses them

**Priority: high.** Today nothing checks the referee, and a silent referee artifact would poison every label after it.

sts2-cli is sts2.dll running under three kinds of non-game behaviour, and each can be listed and checked. (a) TestMode. Both forks set `TestMode.IsOn = true` (wuhao21/sts2-cli `RunSimulator.cs:3075`; mingxuan-he copy `:3059`), and game code branches on it: it skips the "force undiscovered act" branch of `ActModel.GetRandomList`, auto-accepts rewards, and takes a different `MoveToMapCoordAction` path. Grep the decompile for every `TestMode.IsOn` read outside `MegaCrit.Sts2.Core.Nodes` and UI, and classify each as cosmetic or rules-affecting. (b) Godot stubs. The real GodotSharp.dll ships with the game and Mathf is plain managed code, so fuzz each stub member the rules code uses against the real one (about 10^6 inputs each, in a separate .NET process). Two differences are visible by reading: the stub's `Snapped` uses banker's rounding where Godot uses `Floor(x/step + 0.5)`, and the stub's `IsEqualApprox` uses an absolute 1e-6 tolerance where Godot's is relative (`GodotStubs/Math.cs:150-151` vs Godot 4.4 `Mathf.cs`). (c) Harmony replacements. `Neutralize.OnPlay` is rewritten as `CreatureCmd.Damage` plus `PowerCmd.Apply`, which bypasses `DamageCmd.Attack` and its attack hooks; `Cmd.Wait` becomes a no-op; `Task.Yield` is replaced by the frame pump. (d) Runtime taint. Harmony postfixes on the TestMode getter, on every value-returning stub member, on each patched method and on `TaskHelper.RunSafely` tag any step that touches them from rules code as `referee_tainted`, and that step's verdict goes to the live game. `RunSafely` swallows exceptions, so a stub NullRef can silently cut an effect short. (e) Schedule perturbation. Re-run each referee case with 0 vs k extra idle pump frames at each await. A trajectory that changes is order-sensitive and gets confirmed live.

- **Expected gain:** Known failures so far: the Gardener runaway (a missing `Mathf.Log` stub plus a patched wait produced an unbounded enemy phase that invalidated 3 of 44 recorded defeats) and Kaiser Crab false wins. The expensive failure is a silent agreement with a referee artifact: the fix loop "fixes" the emulator toward it, the fix passes the guard, and every later label is wrong. The inventory turns "sts2-cli is the real engine" into a short list of quarantined paths, and the taint makes each verdict self-certifying.
- **Effort:** 1.5–2 agent-days (classification 0.5, stub fuzzer 0.5, taint and perturbation 0.5); the maintainer spends about 1 h running it on the PC and reviewing the list.
- **Precedent:** mingxuan-he/sts2-agent `docs/BUG_gardener_runaway_phase.md`, where a stub plus an IL patch produced a wrong game result (https://github.com/mingxuan-he/sts2-agent/blob/main/docs/BUG_gardener_runaway_phase.md). StS2Sim's README lists its own Harmony redirects, including replacing `CardPileCmd.Shuffle` with a synchronous Fisher-Yates (https://next.tangled.org/cee.wtf/sts2-sim). Godot's Mathf source (https://github.com/godotengine/godot/blob/4.4/modules/mono/glue/GodotSharp/GodotSharp/Core/Mathf.cs). Schedule perturbation follows CHESS systematic concurrency testing (OSDI 2008).
- **Risks:** The grep may misclassify a TestMode read (for example, one used only for logging) and over-taint, so use a reviewed allow-list. The real GodotSharp.dll may need the native host in a static constructor; the fallback is checking stub semantics by reading the Godot source. The live game runs `RunSafely` too, so a genuine game bug that throws is ground truth the emulator must copy, not a taint. Log `RunSafely` exceptions in the live mod as well.
- **Check first:** How many `TestMode.IsOn` reads and Godot member references sit in rules (non-Nodes) code in the v0.107.1 sts2.dll? Does the real GodotSharp.dll's Mathf load and run in a plain .NET 9 process?

### fid-4 · A free test oracle from what the game already displays: card previews, orb values and playability

**Priority: high.** The first pass needs no new captures, and it checks exactly the modifier arithmetic that Defect labels depend on.

Every real-engine state carries numbers the game computed without taking an action. Hand-card descriptions have resolved values (`GetDescriptionForPile(Hand)`, `McpMod.Helpers.cs:50-57`). The game's `UpdateDynamicVarPreview` gives per-target damage and block previews (`vs_targets`, `McpMod.StateBuilder.cs` around 2020-2075). Each orb has `passive_val` and `evoke_val` after Focus (`:1771-1800`). Each card has `can_play`, and intents are displayed. Today the live one-step check compares post-action state only. It compares orbs by type and position, never by value (`src/sts2_gym/live/ids.py:211-214`), and never compares previews. Add an emulator export, `Sts2_DerivedObservables(handle)`, that returns for each hand card the resolved damage and block (untargeted and per target), `can_play`, and orb values. It computes them by playing the card on a no-resample clone and reading damage before block, so no preview code has to be ported. Assert at every state of every capture, live decision and sts2-cli lockstep step. It also works on old data: the 32 committed run traces (`tests/fixtures/run_trace`) store resolved hand text and `can_play` at every step, with 133 distinct card/text pairs and 30 cards that show more than one value (Headbutt 6/9/11, for example).

- **Expected gain:** About 10–40 assertions per state for no extra game time, against about one per action from one-step prediction, so 10–30x more checks per minute of live play. It checks Focus on orbs (negative Focus included), Strength, Weak, Vulnerable and relic multipliers in the combinations real A10 runs reach. A preview mismatch on a converted live state also exposes a power or enchantment lost in `convert` before it becomes a wrong label.
- **Effort:** 1–2 agent-days: emulator export, a text-number parser for the old traces, and wiring into the comparators. The maintainer needs nothing beyond normal play.
- **Precedent:** Pseudo-oracles ("Pseudo-oracles for non-testable programs", ACM 1981). r33hab's card-capture tests already compare orb EvokeValue/PassiveValue, but only in the 88 single-card capture states (`scripts/generate_card_capture_tests.py:95`). Using UI previews across all states: none known.
- **Risks:** Some previews deliberately differ from resolution (random, conditional or X effects; hand text that ignores target powers), so build a whitelist after the first triage. Parsing description text is brittle, so use `vs_targets` numbers wherever the mod provides them. The firewall drops `vs_targets[].values` (D10), which is right for search, so this check must read the raw payload in fidelity test code, never through the search path. Random-target cards need seeded RNG on the clone, or exclusion.
- **Check first:** For every Defect card and orb, can the emulator compute the same numbers the game shows in hand text and `vs_targets`? For example, does hand text apply Strength and Weak but not Vulnerable, with the same rounding order as the emulator's damage path?

### fid-5 · An event ledger from the real engine (RNG, hooks, commands), diffed against the emulator (the NES `nestest.log` method)

**Priority: medium.** A strong diagnosis tool, but it speeds up fixing more than finding. Build it once lockstep tests produce mismatches. *Merges two raw ideas.*

sts2-cli already patches sts2.dll with Harmony (`HeadlessCombatHooks.cs:25-50`), the game ships Harmony 2.4, and STS2MCP uses HarmonyLib. Add probes at three levels. First, every `Rng.Next*` and shuffle call: stream, counter before and after, value and call site, using one patch per call site or the outer NextInt/NextDouble wrappers rather than a stack walk. Second, hook dispatch: hook name, listener model id and order index. Third, the command layer: `DamageCmd` and `CreatureCmd.Damage`, Block, `PowerCmd.Apply`, `CardPileCmd` moves, orb channel and evoke. Each action writes compact, versioned JSONL (to a ring buffer flushed on request in the live game). The emulator emits the same schema behind a compile-time `TRACE_EVENTS` flag, so release builds pay nothing. A Myers diff over event tuples reports the first divergent event plus the 20 before it, for example `combat_targets roll #251 consumed by Lightning.Evoke in emulator vs Thunder power in game`. The RNG and command levels are the contract; add hook-level events only where the port mirrors the game, because the emulator implements Defect cards by name. A zero-code first step: launch the game with its release `-log <LogType> <LogLevel>` option (for example VeryDebug for ActionQueue or GameSync), or use the `log` console command, and see how much the game's own logger already says.

- **Expected gain:** Diagnosis goes from "state differs at step N" to "the 3rd AfterDamage listener is missing". The divergence catalogue records multi-hour hunts where the cause sat floors earlier (`docs/divergence-catalog.md:133`). It catches bugs that reach the same state by a different path, which state comparison can't see: folded multi-hits that under-trigger per-instance hooks (`HANDOFF.md:1623`), or RNG drawn by the wrong consumer. It also removes snapshot-timing races (`divergence-catalog.md:647`). Estimate: roughly halves the cost of each mismatch fix, and shrinking needs fewer iterations.
- **Effort:** 1 h to try the `-log` flags; 2–4 agent-days for the probes (1), emulator emission (1–2) and the diff report (0.5). The maintainer installs the rebuilt mod once.
- **Precedent:** The NES `nestest.log` golden CPU trace that emulator authors diff against instruction by instruction (https://www.qmtpro.com/~nes/misc/nestest.log; https://www.nesdev.org/wiki/Emulator_tests). FCEUX and BizHawk trace loggers for TAS desync hunting. sts2-cli's existing Harmony patches.
- **Risks:** The JIT may inline small Rng methods and defeat a prefix. Probe overhead in the live game at 3x speed. Hook order may differ for legitimate reasons (batching) and need normalising. The schema can drift between the two sides, so version it (like `emu-snapshot/1`).
- **Check first:** Do Harmony prefixes on sts2.dll's Rng and hook-dispatch methods fire under sts2-cli (not inlined) with acceptable slowdown? Does the emulator draw from each stream at points that map one-to-one onto the game's Rng calls?

### fid-6 · Test function by function: load the game DLL and the emulator in one .NET process

**Priority: high.** If the two load side by side, run-layer and A10-value checks for Acts 2–3 become nearly free.

Build one .NET 9 FsCheck/xUnit project that references sts2.dll, initialised the way sts2-cli and StS2Sim do it (Godot stubs, `ModelDb.Init`, Harmony shims), and the Sts2Emulator assembly as managed code (its test project already builds it that way). Write property tests over matched function pairs:

- every Rng method, over random (seed, counter);
- UnstableShuffle;
- act selection plus room and map generation for 10^5 seeds per act at A10, which would flag the known 17-row vs 16/15-row map difference (`HANDOFF.md:2023`);
- encounter, event, relic, potion and card-reward rolls from a given stream state;
- every monster's A10 HP and move values;
- the damage and block modifier pipeline over random power stacks;
- the orb value functions.

Then run whole-combat lockstep in the same process, comparing objects directly with no JSON round trip.

- **Expected gain:** StS2Sim reports about 1,000 multi-turn trials/s single-threaded with the real sts2.dll in-process, against about 20 actions/s for sts2-cli. Pure generators run at microseconds per call: 10^5–10^6 checks per subsystem per hour on the PC, against about 30 run-generation captures today. The fix loop gets sub-second reproductions.
- **Effort:** 2–3 agent-days: host bring-up 1 day (much of it from sts2-cli's `EnsureModelDbInitialized`), then about 15 function pairs at about 1 h each. The maintainer spends about 1 h on the PC.
- **Precedent:** Translation validation (TACAS 1998; PLDI 2000), done here empirically per function rather than by proof. QuickCheck-style model-vs-implementation testing (ICFP 2000). StS2Sim shows in-process execution of the real DLL works (https://next.tangled.org/cee.wtf/sts2-sim).
- **Risks:** `CombatManager.Instance` allows one combat per process, so parallelise with processes. TestMode branches change some generators, so route them through fid-3's inventory. A hand-built RunState may skip lobby steps the real game performs; validate the host against about 30 existing live captures first. The project loads game DLLs, so it runs only on machines with a game install, never in public CI.
- **Check first:** Can map generation and the reward rollers be called on a hand-built RunState without the lobby, the way sts2-cli's StartRun does it? Do sts2.dll and the managed emulator load side by side without assembly conflicts?

### fid-7 · Run the real game headless and decoupled from real time (`--headless --fixed-fps`) under STS2MCP

**Priority: high.** A 2–4 h test could make the only tier with zero Godot stubs 5–20x faster.

StS2 is a Godot 4 .NET game. Godot documents `--headless` (no display, dummy audio driver) and `--fixed-fps N` (disables real-time synchronisation) as available in release export templates. Launch `SlayTheSpire2.exe --headless --fixed-fps 30` with STS2MCP loaded, and keep the mod's `set_time_scale` and hit-stop keeper (`McpMod.TimeScale.cs`). Animations, tweens and SceneTree timers then advance by a fixed game-time step per frame, and frames run as fast as the CPU allows. Move unattended live card captures, live parity runs and live-play prediction checks to this mode. No GPU or window is needed, so it can run while the PC is in use.

- **Expected gain:** The live game runs at about 1 action/s today, mostly waiting on animations. With no rendering and no time sync a frame is probably 1–3 ms of CPU, so a 1 s animation costs about 30–90 ms: plausibly 5–20x per instance, and more with several instances (cmp-1). It may also avoid the 13.3 GB working-set growth (DESIGN §3.4) if that comes from render or VFX resources.
- **Effort:** 2–4 h to test the flags on one scripted combat; 1–2 days to harden it (relaunch watchdog, instance pool).
- **Precedent:** The Godot CLI docs mark `--headless`, `--fixed-fps` and `--time-scale` as available in release builds (https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html). Unity ML-Agents trains with `--no-graphics` and `--time-scale 20` for the same reason (https://unity-technologies.github.io/ml-agents/Training-ML-Agents/). r33hab verified a headless boot on macOS (`HANDOFF.md:2665-2700`).
- **Risks:** The developer may ship a modified engine that ignores CLI flags. Code that reads viewport textures or shaders (run-history screenshots, VFX) may throw on the dummy renderer. Logic that awaits a wall-clock `Task.Delay` rather than a SceneTree timer won't speed up, and could race fixed-fps time. Steam or the game may enforce a single instance. Cross-check headless captures against windowed captures on a small set before trusting them.
- **Check first:** Does the shipped v0.107.1 `SlayTheSpire2.exe` honour `--headless --fixed-fps` with STS2MCP loaded, and does the mod's HTTP API drive a full combat to completion in that mode?

### fid-8 · The game's built-in AutoSlayer as a full-run fuzz driver, started from harvested mid-run saves

**Priority: medium.** Free coverage of event, shop and reward code, but it may be locked to non-release builds.

The release DLL contains the developer's internal soak bot, `MegaCrit.Sts2.Core.AutoSlay`. It has an AutoSlayer with `RunAsync`, `PlayRunAsync` and `HandleRoomAsync`, handlers for every room and screen, AutoSlayCardSelector, AutoSlayConfig, a watchdog, and `autoslay` and `autoslay.seed` arguments with "Run completed successfully with seed=" and exit codes. A community mod (STS2AutoSlayMod) shows it works in v0.10x builds. Add a mod action in our STS2MCP fork that starts AutoSlayer with a seed on a headless instance, either at Neow or from a harvested mid-run save (Act 2–3 states from data-1), and let the flight recorder capture logs, saves and `.mcr` as usual. The emulator then replays AutoSlayer's logged actions and checks the counters and checksums.

- **Expected gain:** The "random / fuzz agent — bizarre card+relic combos humans avoid" corpus that `docs/replay-verification.md` asks for, without writing or maintaining a screen-by-screen driver; the developer keeps it working across every screen. Several unattended full runs per instance-hour, reaching event, shop and reward code that human A10 play rarely visits. Starting from saves avoids the early deaths of a weak policy at A10.
- **Effort:** 1–2 days (mod action, config, seed control, recorder integration).
- **Precedent:** STS2AutoSlayMod, which "unlocks and extends the built-in AutoSlay runner" (https://sts2.gg/mods/mod-216, https://www.nexusmods.com/slaythespire2/mods/216).
- **Risks:** It may be hard-gated to non-release builds (the mod's author mentions setting the game to non-release). Its policy may be close to random. Known softlocks exist (the Punch Constructs event, exhausting the whole deck). AutoSlayConfig may not expose character or ascension. Keep bot runs out of the developer's metrics with `upload_data=false` or by running modded. Never on Daily runs or leaderboards.
- **Check first:** Can a mod start AutoSlayer on release v0.107.1 for Defect at A10 with a chosen seed, and from a loaded mid-run save?

### fid-9 · Custom-mode modifiers as coverage amplifiers for real-engine captures

**Priority: low.** Cheap, but the states are off-distribution, and A10 may not combine with custom mode.

The game's own modifiers build unusual but legal states inside the real engine. INSANITY deals a random 30-card deck. SPECIALIZED gives 5 copies of one card, which stresses stacking such as orb or Focus scaling. ALL_STAR adds 5 colorless cards. VINTAGE makes normal fights drop relics. BIG_GAME_HUNTER brings elite swarms with rare rewards. FLIGHT lets a run route to target rooms. DRAFT and SEALED_DECK steer deck building. The design already captures tapes in custom mode (`DESIGN.md:457`). Add a modifiers parameter to the capture harness and to sts2-cli's RunState creation (`RunSimulator.cs:267`, `CreateForTest`), run real-engine or flight-recorded runs with them, and verify at room level from `current_run.save`. Most of these change only setup or rewards, so combats need no new emulator rules.

- **Expected gain:** An INSANITY combat exercises about 30 distinct Defect cards instead of the 3–8 in an early deck. BIG_GAME_HUNTER and VINTAGE raise elite and relic exposure per hour several times. Card × relic × enemy coverage per real-engine hour plausibly rises 5–10x with no hand-built scenario code.
- **Effort:** 0.5–1 day (harness flag plus sts2-cli parameter); emulator support only if full-run generation replay is wanted for those modes.
- **Precedent:** None known for verification. The modifiers are the developer's own, and StS1 had the same family.
- **Risks:** These states are off-policy, so use them for verification only, never for labels or benchmarks. Modifiers that change combat rules (MURDEROUS, TERMINAL) need emulator support or exclusion. Custom mode may cap ascension, which would clash with D11 for anything beyond pure verification.
- **Check first:** Can custom mode (and sts2-cli run creation) combine Ascension 10 with modifiers like INSANITY and BIG_GAME_HUNTER on v0.107.1?

### fid-10 · Exhaustive small-scope tests of Defect orbs and Focus against the real engine

**Priority: medium.** Defect labels lean on orb arithmetic, and even zero bugs found gives a certificate the oracle can cite, but the card pool is already 88/88 captured.

Enumerate a small scope completely instead of sampling it:

- ring capacity 1–5, full ring included;
- every sequence of up to 4 orbs over Lightning, Frost, Dark, Plasma and Glass (780 sequences);
- Focus from −3 to +3 (the emulator's 19 hand-written orb tests use no negative Focus);
- a few Dark-accumulation and Glass-decay states;
- three enemy setups: one enemy; three enemies with one at 1 HP, which tests Lightning retargeting when the target dies; one enemy with block or Artifact.

For each case, apply one probe: channel each orb type, evoke the leftmost orb, multi-evoke, end turn (passive order and Lightning target rolls), gain or lose Focus mid-turn, or gain or lose a slot. Build states only with first-party commands. In the live game that means STS2MCP's `debug_add_power` (`PowerCmd.Apply`, `McpMod.Debug.cs:501-559`) and `debug_add_card`, then playing channel cards; add the same commands to sts2-cli. Compare full state, plus fid-5's event log if it exists, with the emulator.

- **Expected gain:** Certainty over the scope, instead of whatever random play happened to hit. Likely finds are the edge rules where port bugs hide: clamping under negative Focus, evoke order when channelling into a full ring, Lightning targets when enemies are dead or dying, Glass decay with Focus, and passive triggers vs relic hooks. Each such bug biases thousands of labels.
- **Effort:** 1–2 agent-days (enumerator, sts2-cli setup commands, comparator), then one overnight run on the PC: roughly 10^4–10^5 cases at about 700k actions/h across about 10 processes, faster after sim-1.
- **Precedent:** The small-scope hypothesis behind Alloy. Korat bounded-exhaustive testing (ISSTA 2002). "Evaluating the Small Scope Hypothesis" (MIT tech report, 2003).
- **Risks:** Building states by card plays adds prefix actions, and some ring states may be unreachable without reflection. Avoid reflection, because sts2-cli's SetPlayer adds relics without their OnObtain hooks (`RunSimulator.cs:332-420`). Yield may be low (88/88 captured, with three divergences). Trust in the results depends on fid-3.
- **Check first:** Can any in-scope ring state plus a Focus value be reached in the real engine with at most about 10 setup actions, using first-party commands (PowerCmd.Apply, channel cards, set_draw_order)?

### fid-11 · Measure how much of the emulator code the oracle uses was never checked against the game, and gate gold labels on it

**Priority: medium.** About a day, and it turns "fidelity where the agent goes" into a number and a worklist.

Instrument the managed emulator build with branch coverage (coverlet, for example) in two passes. Pass A replays every real-engine comparison that passed (committed traces, card captures, combat sweeps, live checks, lockstep runs). The branches it exercises form V, the verified set. Pass B runs the oracle's actual workload (search on the SpireBench positions plus a self-play sample) and counts visits S_b per branch. Report the unverified mass U = Σ_{b∉V} S_b / Σ S_b, and list the top 50 unverified branches mapped to card, power, monster or relic. Record per-label coverage provenance (the branches its search touched), and let a label become gold only if its unverified share is below a threshold. The worklist feeds fid-10-style tests and capture choices.

- **Expected gain:** Replaces "the catalogue says Open: None, but the count is a bad proxy" with a number to drive down and a ranked worklist. Stops gold labels resting on code that no ground truth has run, such as Act 2–3 move tables written from source or rare cards never played live. Test effort goes where the oracle spends its simulations.
- **Effort:** About 1 agent-day: coverage runs plus a branch-to-entity mapping from file and method names.
- **Precedent:** Structural-coverage gating in safety-critical certification (DO-178C). "Code Coverage at Google" (ESEC/FSE 2019). `docs/replay-verification.md` argues "fidelity where the agent goes is what matters" but measures nothing.
- **Risks:** Branch coverage is not state coverage: a branch exercised once can still be wrong in other states, so treat it as necessary, not sufficient. The managed and NativeAOT builds must come from the same source. Instrumentation slows pass B, so sample it.
- **Check first:** Can the comparisons that passed (Python replays driving the native library) be re-run against a managed, instrumented build, so V is measured on the same code paths?

### fid-12 · Swarm configurations for the differential fuzzer: leave random features out of each episode

**Priority: medium.** A few hours once a fuzzer exists. The gain is unproven for game simulators.

Before each lockstep fuzz episode (in sts2-cli or the fid-6 host), draw a random "swarm" mask:

- each Defect card allowed in rewards and deck building with probability 0.2–0.5;
- a relic subset of 0–6 from the Defect and shared pools;
- potions on or off;
- policy biases: play orb cards first, hoard energy, end the turn early with probability p, focus one target;
- a deck-size bias;
- an A10 encounter from Acts 1–3.

The mask limits what the fuzz policy can choose. Log it with each mismatch, so features common to failing runs point at the culprit.

- **Expected gain:** Uniform random agents rarely build the deep concentrations where interaction bugs live: 4+ orb generators with Focus stacking, 0-cost loops, many copies of one power. In the original study, a week of swarm Csmith found 104 distinct compiler crash bugs against 73 for the default configuration (about 42% more).
- **Effort:** 2–4 agent-hours on top of the fuzzer.
- **Precedent:** "Swarm Testing" (ISSTA 2012, https://www.cefns.nau.edu/~adg326/issta12.pdf). "Better Random Testing by Leaving Features Out" (https://blog.regehr.org/archives/591).
- **Risks:** Masks can produce unwinnable or degenerate runs that waste referee time. Cap episode length and reject masks with fewer than about 8 playable cards.
- **Check first:** Does the fuzz driver control deck and reward choices at run level (set_player/enter_room or reward selection), so a mask can actually restrict what the engines see?

### fid-13 · A known-defect registry for the referee, mined from the fork network

**Priority: medium.** Minutes a week of reading, and it could save 10–40 h of triaging referee bugs as if they were emulator bugs.

A weekly read-only `gh api` script lists the forks of wuhao21/sts2-cli (65), Gennadiyev/STS2MCP (102), r33hab/sts2 and evangambit/sts2. It compares each active fork with its parent (ahead_by, commit messages) and fetches any bug tracker it finds. The agent reads the diffs and never builds or runs them. Each relevant item goes into our mismatch registry either as a "referee known defect", with a signature the differential tester uses to annotate or suppress mismatches, or as a candidate patch for a port we write and review ourselves. A first scan found three useful forks. morefreeze/sts2-cli is 470 commits ahead and keeps a 51-entry tracker of headless-engine faults (`agent/bug.md`). Examples: BUG-037, a NullRef in Vantom's DismemberMove under headless (2–3% boss crash rate); BUG-014, a Cmd.Wait deadlock; BUG-035, card_select picking the worst cards; BUG-050, return-to-hand cards reported as unplayed. KevinMeiAI/sts2-cli has a `compat/v0.107.1` branch with "Fix Defect state metadata and validate a manual A10 run" and "Fix Jungle Maze headless audio crash". aizatrosli/sts2-cli is 37 commits ahead with "fixes from live captures". Post our own referee findings back to those trackers.

- **Expected gain:** Otherwise every headless-only fault shows up as a false mismatch, costing a triage iteration or, worse, an emulator "fix" toward a referee bug. If 10–20 of the roughly 50 known faults apply to the mingxuan-he copy at its pinned commit, that is about 10–40 h of triage avoided.
- **Effort:** 3–5 h for the script; about 1 h a week of agent triage; about 15 min a week of maintainer review.
- **Precedent:** useful-forks for finding active forks (https://useful-forks.github.io/). The GitHub compare API. The format of morefreeze/sts2-cli's `agent/bug.md`.
- **Risks:** Forks diverge (the mingxuan-he copy replaced the IL patches with a frame pump), so some bugs won't apply. Fork code is untrusted: read-only, no builds (D3). Check each licence before porting code; using bug reports and ideas is fine. The registry needs expiry, so a suppressed signature can't hide a real emulator bug after the referee is fixed.
- **Check first:** How many of morefreeze's BUG-001..051 reproduce in the mingxuan-he/sts2-agent build at commit `f9047e4`? Reading the code paths each entry references answers this.

### fid-14 · Cross-port bug transfer: turn sibling StS2 ports' published divergences and hidden-state lists into tests

**Priority: medium.** About 40 cheap, high-prior tests now, but the ports target v0.111.0.

Four independent ports have published what they got wrong against the real game. (1) iRyougi/sts2-sim (C#, MIT, v0.111.0) files divergences as labelled issues (label 保真差异, "fidelity difference"), about 20 so far. Examples: iRyougi/sts2-sim#19, transforms and random card generation draw from the Niche stream differently; iRyougi/sts2-sim#17, candidate order when choosing from a pile; iRyougi/sts2-sim#15, cards generated after combat end consume extra Shuffle draws; iRyougi/sts2-sim#14, hooks still fire inside the combat-end window; iRyougi/sts2-sim#11, AfterCurrentHpChanged is not fired when a secondary enemy dies with the primary; iRyougi/sts2-sim#10, AfterCardGeneratedForCombat is missing on in-combat transforms. (2) ytcs/sts2-solver keeps `docs/game-bugs.md`, a file:line-cited `docs/research/game_code.md` (one run-wide MonsterAi stream that is never reset per combat; a .NET introsort reshuffle; C# decimal arithmetic) and named regression scenarios such as `defect_missing_base_orb_slots`. (3) yizhang-dream/sts2-simulator ships an `install_engine_fixes` layer. (4) Yummn/sts2-turn-rewind, which has a PC v0.107.1 build, lists in its changelog each hidden field it had to restore to rebuild a combat exactly: monster state-machine cursor and first-turn fields, relic `[SavedProperty]` counters, power internal counters, full combat history for Echo Form, card cost-modifier chains, and orbs. Each item becomes a targeted lockstep scenario against sts2-cli, plus a state-completeness assertion: the field must exist in emulator state and be compared in lockstep. Spire Codex's per-patch changelog plus a decompile diff decides which items apply to v0.107.1. A weekly `gh api` job lists new issues and commits with fidelity keywords in these repos.

- **Expected gain:** Ports of the same decompile tend to fail at the same tricky spots (hook dispatch windows, choice of RNG stream, ordering), so each external finding is a cheap, high-probability test. The hidden-field checklist closes the main blind spot of lockstep testing, which compares only the state it serialises.
- **Effort:** 2–3 evenings for the first harvest and tests; about 1 h to set up the weekly watcher.
- **Precedent:** Differential and N-version testing across independent implementations (Csmith-style). iRyougi's workflow of replaying recorded client games and filing each divergence as an issue (https://github.com/iRyougi/sts2-sim/issues). https://github.com/ytcs/sts2-solver/tree/main/docs. https://github.com/Yummn/sts2-turn-rewind.
- **Risks:** These ports target v0.111.0, so some findings are version-specific. ytcs, turn-rewind and yizhang-dream have no licence: read them only, re-derive each test from the v0.107.1 decompile, and never build or run their code. Most iRyougi issues are written in Chinese.
- **Check first:** Of the roughly 20 iRyougi divergences and the ytcs regression scenarios, how many touch classes that are byte-identical between the v0.107.1 and v0.111.0 decompiles?

### fid-15 · A bug-for-bug corpus from later patch notes and community fix mods

**Priority: medium.** 15–25 high-prior tests for rare item-by-card interactions that random fuzzing reaches only after millions of states.

Each gameplay "Fixed …" line in a patch after v0.107.1 describes behaviour v0.107.1 actually has, and a port written to the intended behaviour will likely get it wrong. Pull the full notes as JSON from the public Steam News API (https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2868840&count=60&maxlength=0) for v0.108.0 to v0.111.0, and keep fixes that Defect can reach (checked against the pools on spire-codex.com/api). Examples: Bone Tea failing to upgrade the hand when Toolbox is also held; Unceasing Top not firing after an auto-played start-of-turn hand; Pollinous Core counting past 4; Gold Plated Cables (a Defect relic) flashing when the orb passive doesn't fire; Vigor applying to only the first of Mad Science's 3 hits; Entropy turning curses into Ascender's Bane; History Course copies; and "many instances of weird RNG behaviour", which means v0.107.1 keeps some stream correlations. Check the other direction too. The emulator's Zamiell base predates v0.107.1 (`PLAN.md:267`), so the v0.107.1 patch notes are the checklist of changes the port had to absorb: Shatter evokes all orbs twice at 7(11) damage; Tesla Coil+ does 4 damage with two Lightning triggers; Hyperbeam is 28(36); Infused Core gives +1 Lightning damage; Beckon no longer damages the player when Lightning orbs end combat; Scrape no longer discards 0-energy cards that have a Star cost; Perfect Fit works with Reboot. Add community fix mods that state a root cause, such as gnidiad/sts2-Foregone-Conclusion-Fix: a paused SetupPlayerTurn lets AfterSideTurnStart remove DrawCardsNextTurnPower early. That one is Regent-only, but it documents a general turn-start ordering hazard. Each item becomes a small scenario that asserts v0.107.1 behaviour in sts2-cli first, then in the emulator.

- **Expected gain:** Every failure is a real fidelity bug in a class that biases labels (hook order, auto-play, generated cards, orb timing). The suite also guards against "fixed" behaviour leaking in if v0.111-era code is ever merged.
- **Effort:** 1 evening to pull and triage the notes; 2–4 evenings to write the scenarios.
- **Precedent:** One regression test per bug fix is standard practice. ytcs/sts2-solver `docs/game-bugs.md` lists real-game bugs its simulator must reproduce or guard against.
- **Risks:** The notes are terse, and many items are UI-only, multiplayer-only or for other characters. Some bugs may have been introduced in a beta after v0.107.1, so reproduce each on v0.107.1 before asserting it.
- **Check first:** Does each candidate bug reproduce in sts2-cli on v0.107.1, so the test asserts real v0.107.1 behaviour rather than a beta-only regression?

## Oracle (search and labels)

**Read this before trusting any variance-reduction gain in this section** (orc-2, orc-3, orc-4). The open issue in `LOG.md` ("time-uniform CSs cost far more worlds than §4.3 assumes") measured that, under the time-uniform confidence sequences, the number of worlds needed depends only weakly on σ, because the range term dominates. The betting CS at h = 1 needs 750 worlds at σ = 3 and 852 at σ = 8. So a variance cut buys much less than the estimates below assume, until that issue is settled (for example with fixed-n or asymptotic certification). Re-run `scripts/cs_width_probe.py` at the reduced σ before claiming a gain. Ideas that cut work per world or stop work early (orc-6 to orc-9) don't depend on this.

### orc-1 · Replace the hand-set tempo rollout: a native playout with weights fitted by simulation balancing

**Priority: medium.** The rollout is the biggest measured lever in r33hab, and its Ironclad-tuned weights are probably wrong for Defect, but the first check needs reference values. *Merges two raw ideas.*

The tempo rollout (`rl/combat_mcts.py:414-457`) uses fixed weights: Attack 4, Skill 3 if threatened and 0.4 otherwise, Power 2, End Turn 0.6. End Turn's weight never applies because of an index bug (`FINDINGS.md:421-425`). For Defect, Zap, Dualcast and Coolheaded are Skills, so the main damage cards score 0.4 whenever nothing is incoming. Each playout is also 13–16 Python steps over ctypes (`legal()`, dict lookups, `rng.choice`, `step`; `:422-497`). Two changes. (a) One export, `Sts2_Rollout(handle, weights*, seed, max_steps) -> (value, steps)`, runs the whole playout in C#. (b) The policy becomes a softmax-linear function of cheap per-action features: the damage, block, draw, energy and scaling tags in `rl/card_tags.py`, cost vs energy left, incoming damage minus block, orb type channelled or evoked and free slots, an end-turn flag, and optionally card id crossed with context buckets. Fit the weights by simulation balancing, not by move-matching: minimise the squared error between the rollout's mean return Q_roll(s,a) and a deep reference Q_ref(s,a) over root actions on about 500 Defect positions, with CMA-ES or SPSA and CRN worlds shared across weight candidates. Q_ref comes from 1500-sim plain MCTS or from gold labels, never from search that uses this rollout. Refit per character and per generation. Labels record the rollout version, because Q^tempo changes meaning.

- **Expected gain:** Hand tempo weights were a ~25x budget multiplier over uniform and +3.8 HP at equal budget (`FINDINGS.md:18, 40-44`). The rollout runs at the leaf, in Stage-1 screening, in the QUICK continuation, for bronze labels and in the search half of the λ = 0.3 value target. FINDINGS says that target is 8.6 HP pessimistic because rollouts play worse than search (`FINDINGS.md:268-275, 488-491`). Guess: a further 2–5x budget multiplier on Defect, and a higher bronze-vs-silver Kendall τ, which may let bronze labels pass the ≥ 0.6 keep rule. Native execution adds roughly 1.3–1.7x sims/s.
- **Effort:** 2–3 days of code (export and features 1 day; fitting and paired evaluation 1–2 days), plus 1–2 nights of compute for reference values and fitting.
- **Precedent:** "Monte-Carlo Simulation Balancing" (ICML 2009). "Monte-Carlo Simulation Balancing in Practice" (CG 2010, https://www.remi-coulom.fr/CG2010-Simulation-Balancing/): the Go program Erica's win rate against Fuego rose from 69% to 78% when balanced weights replaced move-matching ones. AlphaGo's fast rollout policy, a linear softmax at about 2 µs per move (Nature 2016). "Combining Online and Offline Knowledge in UCT" (ICML 2007) showed that a stronger rollout can make MCTS worse.
- **Risks:** A stronger rollout is not automatically a better estimator, hence the balance objective, and acceptance only on paired regret at matched wall-clock time. Weights can overfit the reference set, so hold out positions. The reference is circular if it comes from search that uses this rollout. Near-deterministic rollouts lose diversity, so fit the softmax temperature too. Feature code must read only displayed information.
- **Check first:** On about 200 Defect positions, how far is the current tempo rollout's Q from PLAY@300 or 1500-sim plain MCTS, in mean bias and in rank correlation across root actions? Large systematic error means weights can fix it; mostly noise means they can't.

### orc-2 · Event-keyed randomness so common random numbers stay coupled after candidate lines diverge

**Priority: medium.** Possibly 1.5–3x lower paired variance on the hardest A10 fights, but see the note above. The first check is a cheap logging pass. *Merges two raw ideas.*

This is for search clones only (`resample_hidden=True` worlds). Faithful clones and fidelity tests keep the game's sequential streams. Three shared, sequentially consumed combat streams desync paired candidates. (a) Reshuffles run Fisher-Yates on one ShuffleRng (`CardEffects.cs:3559, 3592-3598`), so piles that differ by one card get unrelated orders. Give each card a permanent key u = H(world_seed, shuffle_ordinal, DefId, upgraded, enchant, canonical copy ordinal) and sort the pile by key. The law stays uniform, but shared cards keep their relative order across candidates. (b) Enemy AI uses one AiRng iterated over living enemies (`EnemyAI.cs:16`; the game has one run-wide MonsterAi stream), so a kill in one line shifts every later roll of the survivors. Give each enemy its own substream, H(world_seed, slot, spawn_ordinal). (c) Lightning passive and evoke and random multi-hits draw CombatTargets per hit (`divergence-catalog.md:324, 339`). Key them by (turn, orb slot or hit index). A simpler variant reseeds every stream at each player-turn start from H(world_seed, stream, turn). `Clone(rngSeed)` (`StateCloning.cs:209-234`) sets a "keyed" flag, and CallCount still increments, so bookkeeping doesn't change.

- **Expected gain:** Root CRN measured a 4.6x variance reduction (`FINDINGS.md:300-305`), but only while candidates consume RNG identically, and in Defect fights that stops quickly. Any end turn with a different number of Lightning orbs or living enemies shifts CombatTargets, any kill shifts AiRng, and Act 1 decks reshuffle every 2 turns or so. Expect 1.5–3x lower paired-gap variance on multi-enemy, elite and boss fights (about 1x on short single-enemy hallway fights), and tighter CRN within a Gumbel round in PLAY search.
- **Effort:** 2–4 agent-days in C# behind a flag (shuffle helper, ChooseIntents, about 10 CombatTargets sites), plus a test that faithful clones stay bit-identical; one overnight variance A/B on 200 positions; about 3 h of maintainer review.
- **Precedent:** iRyougi/sts2-sim's keyed mode (`RunState.CreateKeyedForLabels`, which derives draws by purpose rather than by sequence "so two branches of the same game remain comparable"; https://github.com/iRyougi/sts2-sim). Synchronising random numbers per event type as the condition for CRN to work (Management Science 38(6), 1992, https://doi.org/10.1287/mnsc.38.6.884). Counter-based keyed RNG: "Parallel Random Numbers: As Easy as 1, 2, 3" (SC'11, https://www.thesalmons.org/john/random123/). Fixed-scenario policy comparison: PEGASUS (UAI 2000).
- **Risks:** Keying on anything the candidate line changed silently correlates worlds and breaks CS coverage. CardInstance has no instance id (`Card.cs:302`), so per-copy state (BonusDamage, CostBump) needs a canonical copy ordinal. The other ~140 RNG call sites stay sequential, so the gain is partial. The keyed path must never reach the F1/F5 fidelity tests. It removes the real game's cross-stream correlations; that fits the F9 nominal-distribution convention, but record it, and check that marginal draw distributions match sequential mode.
- **Check first:** In A10 Defect dev positions, at which turn do paired candidate worlds first diverge in AiRng, CombatTargets or Shuffle call counts (logged per turn with `Sts2_RngCallCount`)?

### orc-3 · Maximally coupled draw orders across candidate decks for card-reward, removal, upgrade and shop labels

**Priority: low.** Tier B is Phase 2, it needs orc-2's keyed shuffle first, and the note above applies.

`deckfights.py` gives every candidate afterstate the same fight seed (`:79-84`). But decks of different size or content still get unrelated Fisher-Yates orders, so only the enemy rolls are shared. Reuse orc-2's keyed shuffle at deck level. Shared cards carry identical keys in every shuffle. For "Take A" vs "Take B", the new card takes the same key slot, so A and B sit in the same draw position in every world and every reshuffle. "Skip" simply lacks that card, "Remove c" deletes c's key, and "Upgrade" keeps it. Use the same coupling for Tier B PLAY-lite act rollouts, map and shop top-2 verification, and QUICK macro's 72 deck fights. Each candidate's marginal is still a uniform permutation.

- **Expected gain:** Tier B is the most expensive tier (about 320 core-h for 80 gold positions, plus about 20 for silver). If coupling raises the per-fight correlation of post-fight HP between candidates from about 0.2–0.4 to 0.7–0.85, paired variance falls 2.5–4x. That could save 100–200 core-h per Tier B gold campaign, and sharpen QUICK macro answers within the same 30 s.
- **Effort:** About 1 agent-day after orc-2; about 2 h to measure the correlation before and after on `rl/run_train/deck_benchmark.json`.
- **Precedent:** Permanent random numbers for coordinated samples in official statistics ("Coordination of samples using permanent random numbers", in *Business Survey Methods*, Wiley 1995). The paired deck fights in an Edinburgh UG4 deck-building project and in r33hab's `deckfights.py` use CRN without permutation coupling.
- **Risks:** Coupling decays once play diverges (A gets played or exhausted, B doesn't), so the gain shrinks over long act rollouts. Random card generation and transforms need their own keys. Asymmetric coupling (the new card always on top, say) would bias the comparison, so it must stay a uniform-key interleave.
- **Check first:** On the `deck_benchmark.json` candidate pairs, what is the current per-fight correlation of post-fight HP between candidate decks on the same fight seed? If it is already above 0.8, this buys little.

### orc-4 · Multifidelity control-variate (two-phase) estimator for silver and gold gaps

**Priority: low.** Under the current time-uniform CSs, the control variate's wider range can cancel its variance gain. Revisit if certification moves to fixed-n intervals.

In each CRN world j, compute the paired gap at two fidelities on the same world, with the same continuation RNG. d_hi uses the label's continuation (PLAY@300 for gold, PLAY@60 for silver). d_lo uses PLAY@16, a tempo rollout, or FightNet at the next turn boundary. Estimate mean_n(d_hi − β·d_lo) + β·mean_m(d_lo), with m ≫ n. Fix β and m/n per tier from a dev pilot; the multifidelity optimum is m/n = sqrt(c_hi·ρ² / (c_lo·(1−ρ²))). For validity, use a time-uniform empirical-Bernstein CS on Y_j = d_hi − β·d_lo (range 2(1+β)) at α/2, plus a CS on mean(d_lo) at α/2, so it still holds under optional stopping. Stage-1 screening worlds can double as the cheap sample only if their CSs hold simultaneously over all 16 candidates. Optionally, send the expensive continuation preferentially to worlds with large |d_lo_j| (Neyman two-phase sampling with Horvitz-Thompson weights).

- **Expected gain:** Under variance-proportional sizing, expensive continuations fall by about 1/(1−ρ²) for the same half-width: about 1.9x at ρ = 0.7 and 4.5x at ρ = 0.9. Gold (about 150 core-h per 200 positions) and silver (about 135 core-h) dominate Tier A, and both are redone at every π_ref promotion, so a 2x cut saves about 140 core-h per relabel cycle. The same estimator applies to Tier B gold, with deck fights as the cheap level.
- **Effort:** 1–2 agent-days for `stats.py` and for running two continuations per world with shared seeds; one overnight pilot on about 50 dev positions to estimate ρ and β.
- **Precedent:** "Optimal Model Management for Multifidelity Monte Carlo Estimation" (SIAM J. Sci. Comput. 2016, https://dspace.mit.edu/handle/1721.1/108618). Multilevel Monte Carlo (Operations Research 2008). Double sampling (JASA 1938). This differs from AIVAT-style luck correction (lrn-6), which uses a value function rather than a cheaper simulation of the same world.
- **Risks:** Estimating β on the same data adds a small bias, so fix it from dev. Tempo rollouts are 8.6 HP pessimistic and may rank lines differently, so ρ could be low; PLAY@16 is the safer cheap level. Y's range is 2(1+β), wider than [−1, 1], which hurts range-dominated CSs; two-phase weights widen it further. The cheap level must use exactly the same world and continuation RNG.
- **Check first:** On about 50 dev positions with shared CRN worlds, what is the per-world correlation of the PLAY@300 paired gap with the PLAY@16 gap, and with the tempo-rollout gap? Then rerun `scripts/cs_width_probe.py` with the implied σ and range.

### orc-5 · Check that resampled hidden state has the right distribution, not only that it varies (simulation-based calibration)

**Priority: high.** Honest search rests on the hidden-state sampler, nothing else would detect a bias in it, and the test is Python-only and runs in minutes.

Honest determinized search samples hidden state from b(I): the draw-pile permutation, fresh streams, likelihood-weighted AI particles and redrawn unseen content. The current leak suite checks variety and consistency: L1–L3 and L8 ask whether there is more than one value, and L7 checks analytic posteriors on hand-picked tables (DESIGN §7.6). StateCloningTests check invariants only. Simulation-based calibration (SBC) tests the whole sampler with one statistic:

1. From the emulator's own generative process (random seeds, a fixed policy, A10 Defect, random stop points), draw N ≈ 2,000 pairs of (I, true hidden h*).
2. For each pair, rebuild the position from I only, through the `from_info_state`/convert path, and draw L = 99 samples h′ ~ b(I).
3. Rank f(h*) among the f(h′) for several statistics: each card's position in the draw pile, next turn's first draw, each enemy's next intent, the Act 2–3 encounter behind the next node, and the next card-reward rarity.

The ranks must be uniform (chi-square test or an ECDF band). Repeat at small N with sts2-cli as the generator, so the modelled move weights are checked against the real engine.

- **Expected gain:** A biased b(I) shifts every Q the oracle produces, and lockstep fidelity can't see it. Examples: a particle filter that mis-weights probabilistic moves, known-top cards forgotten after a shuffle, an encounter redraw that ignores encounters already seen. SBC catches all of these in one automated test at emulator speed, across every hidden component jointly and on realistic states.
- **Effort:** 0.5–1 agent-day, Python only, using the existing clone and export APIs; it runs in minutes on the Mac.
- **Precedent:** "Validating Bayesian Inference Algorithms with Simulation-Based Calibration" (2018, https://arxiv.org/abs/1804.06788). "Validation of Software for Bayesian Models Using Posterior Quantiles" (JCGS 2006).
- **Risks:** If b(I) is sampled by cloning the true state rather than rebuilding it from I, the test is circular, so it must go through the import path. Discrete statistics need randomised ranks for ties. Positions flagged `ai_state_assumed` must be excluded or reported separately.
- **Check first:** Can a test build export the true hidden state (ordered piles, AI fields, stream positions) alongside the observation I? Is there an import path that rebuilds a position from I alone, so samples come from b(I) and not from a clone of the truth?

### orc-6 · Make π_ref a pure function of the information state and memoise its decisions

**Priority: medium.** Labels become reproducible either way. The speed-up depends on a hit rate that is cheap to measure once a combat info-state hash exists.

Today the PLAY continuation seeds its determinizations as move·sims + k (`combat_mcts.py:770, 773`) and shares a numpy Generator, so π_ref's choice depends on the move index and on generator history. Instead, derive every internal determinization and rollout seed from blake2b(info_state_hash, π_ref_version, ordinal within the deterministic segment), using a canonical hash like the one in `spireline/infoset/schema.py` (`info_state_hash`, `det_seed`). π_ref is then a deterministic function of the info state. Store each decision, or the whole plan for a deterministic turn segment with subtree reuse, in an LRU or SQLite table keyed by (π_ref_version, info_state_hash). Share the table across worlds, root candidates, positions in the same fight, label jobs and self-play. Continuations from different worlds and candidates often reach the same info state at the next turn start (same visible state after the enemy phase, same hand multiset, same displayed intent). On a hit, skip the search and step the stored action.

- **Expected gain:** Continuation decisions cost 60–300 sims each (about 26–130 ms plus the prior) and dominate Tier A label cost. An Act 1 deck of 10–12 cards gives only about 10–20 distinct next-turn hand multisets per candidate across 100–300 worlds, so the first continuation turn (about 40% of the remaining decisions) could hit 80–95% of the time. Later turns and 25–30-card Act 3 decks hit far less. Net guess: 1.2–1.8x on silver and gold Tier A, largest in Act 1. Labels become reproducible and continuation noise drops.
- **Effort:** About 1 agent-day once the hash covers combat state; about 1 h to measure the hit rate on a pilot.
- **Precedent:** CFR-family solvers look up the strategy per information set by construction. Subtree reuse is standard MCTS practice. For Slay the Spire: none known.
- **Risks:** The key must contain everything the policy reads (AI move history and particles, relic counters, orbs, per-copy card state, potions) and nothing hidden. Too coarse a key silently changes π_ref and could leak information; too fine a key gives no hits. Invalidate on π_ref promotion, and cap self-play memory.
- **Check first:** In a silver Tier A pilot job, what fraction of π_ref continuation decisions repeat a canonical info-state hash seen earlier? Report Act 1 and Act 3 positions separately.

### orc-7 · Race end-state classes and label sets of first actions; merge identical twin enemies

**Priority: medium.** Cheaper Tier A, and a correctness fix to SpireBench regret. Shares bookkeeping with lrn-4.

The candidate DFS already deduplicates lines by end-state hash (`DESIGN.md:568`), but the answer is the line's first atomic action (`DESIGN.md:231, 588`). For each end-state class c, also record F(c), the set of first actions that can start a line reaching c. Canonicalise end states under permutation of enemies that are identical in visible and AI state; the old search graded identical twin Cubex Constructs 17.7 HP and 36 HP apart (`live_search.py:57, 578`). Racing still runs over classes, but it stops as soon as every class the CS hasn't eliminated shares a common first action, which is then DECISIVE as a first move. The ε-best atomic set is the union of F(c) over the ε-best classes, and SpireBench regret for an atomic action a is max_c Q(c) minus the best Q over classes reachable from a.

- **Expected gain:** Some positions have top classes that differ only after the first card (a later order, the last target, which twin was hit). These currently race to ε precision for no decision value, and would stop after screening. Guess: 20–40% of hallway positions, so 1.2–1.5x on Tier A cost. Merging twins removes duplicate candidates in multi-enemy fights. SpireBench also stops charging regret when a player's first card starts a different ordering of the same best end state.
- **Effort:** About 1 agent-day for the DFS bookkeeping and stopping rule; about half a day for twin canonicalisation, with a per-encounter check that plays both twins in one world and compares (as `live_search.py` already collapses identical card copies).
- **Precedent:** "Transpositions and Move Groups in Monte Carlo Tree Search" (IEEE CIG 2008). Bottled AI's end-state dedupe (xaved88/bottled_ai, cited in the design). `live_search.py`'s collapse of identical card copies.
- **Risks:** Twins can differ in slot-dependent mechanics or hidden AI state, so merge only on a full-state hash match after permutation. The first-action label must match what SpireBench scores. Recording F(c) must not inflate the 5,000-line cap.
- **Check first:** On the 200 dev positions, how often do the top two end-state classes after Stage 1 share a first atomic action?

### orc-8 · Sound pruning before rollouts: Pareto dominance of lines and HP-ceiling bounds

**Priority: medium.** Helps QUICK's live budget and bronze labels. Little effect on silver and gold.

(a) Pareto pruning. Drop a DFS line if its end state is weakly worse than another line's in every component of a verified-monotone order and equal everywhere else: player HP, block, Strength and Focus; enemy HP and block; enemy debuffs. A per-monster whitelist excludes HP-threshold mechanics such as splits, curl-up and enrage-on-death, found by grepping `Core/EnemyAI.cs`. Many of the up to 5,000 lines are prefixes of a line that plays one more pure-improvement card, and the hand is discarded at end of turn anyway. (b) HP ceiling. Under L0 (0 if dead, else 0.5 + 0.5·min(1, (HP_end + 10·potions)/maxHP)), the HP after a line's deterministic enemy phase, plus the largest heal available from inventory, bounds u from above in every world. Prune a candidate when that ceiling falls below the leader's lower confidence bound. (c) Where the next draw is enumerated exactly, apply Star1/Star2 at those chance nodes, with the same ceilings and a one-line probe as the lower bound.

- **Expected gain:** Pre-scoring runs 4 tempo rollouts per line, up to about 16 core-s per position, and pruning dominated lines could cut that 3–10x. The main beneficiaries are QUICK's 10 s p90 live budget and the 100k bronze tier (about 28 core-h). Freeing the 16 candidate slots for distinct plans also helps candidate recall. Ceilings matter mostly in the last 1–2 turns of a fight.
- **Effort:** 1–2 agent-days, plus a dev check that pruning never removes the 64-candidate argmax.
- **Precedent:** "Simulation-Based Admissible Dominance Pruning" (IJCAI 2015, https://www.ijcai.org/Abstract/15/241). *-minimax (1983). "Rediscovering *-Minimax Search" (CG 2004). "Monte Carlo *-Minimax Search" (2013, https://arxiv.org/abs/1304.6057).
- **Risks:** Non-monotone mechanics make dominance unsound: block-scaling cards, low-HP triggers, HP thresholds, Defect orb-slot evoke order. Restrict pruning to fields proven monotone, and re-measure candidate recall against the 98% bar. Heal allowances must cover every in-combat healing source, or the ceilings aren't bounds.
- **Check first:** On dev positions, what share of DFS lines is dominated under a whitelist-safe order, and what share of QUICK wall time is pre-scoring today?

### orc-9 · One scheduler across all label positions, with futility stopping

**Priority: medium.** Recovers budget burnt on positions that end UNCERTAIN, and doesn't depend on variance reduction.

Treat a whole label campaign as one multi-bandit best-arm-identification problem, instead of racing each position to its own cap. A scheduler gives the next block of CRN worlds to the position most likely to reach a verdict per core-second, using a GapE-V-style index on the current gap, its variance, the ε band and the remaining cap. A position stops for futility when the conditional probability of reaching DECISIVE or CLOSE within its cap falls below a pre-registered threshold, and is marked UNCERTAIN_FUTILE. Quotas by decision type, act and room keep the label mix fixed. Spire Codex v0.107.1 frequencies could weight strata toward decisions that actually occur; that is an evaluation-side use, but check it against D13.

- **Expected gain:** Per-position cost spans 2.5–22 core-min for silver and 14–98 for gold, and positions that end UNCERTAIN burn their whole cap. If they are 20–30% of positions at about 3x the median cost, they use about half the budget. Futility stopping recovers most of that: about 1.5–2x more resolved labels per core-hour, and overnight jobs finish predictably.
- **Effort:** 1–2 agent-days for the scheduler and the rule; one overnight dev run to calibrate the threshold (count futility-stopped positions that would have resolved with the full cap).
- **Precedent:** "Multi-Bandit Best Arm Identification" (NIPS 2011, https://proceedings.nips.cc/paper_files/paper/2011/file/c4851e8e264415c4094e4e85b0baa7cc-Paper.pdf). Futility stopping by conditional power in group-sequential trials (Statistics in Medicine 24:2747, 2005). Hyperband (JMLR 2017).
- **Risks:** The resolved set tilts toward large gaps, so reports must count UNCERTAIN_FUTILE, and test-split membership must be fixed in advance. A miscalibrated threshold drops positions that would have become DECISIVE. The scheduler must not reuse worlds across positions in a way that breaks the independence each per-position CS assumes.
- **Check first:** In the week-3 pilot, what fraction of Tier A core-hours went to positions that ended UNCERTAIN?

### orc-10 · Relabel selectively after each emulator fix, using content-coverage bitsets and CRN fingerprints

**Priority: medium.** Needed once a persistent label bank meets nightly fixes, not before.

Records carry one lock hash (DESIGN §3.5), so with a nightly fix loop every fix would mark the whole label bank stale. Instead, in three parts. (1) Add a per-handle `ulong[]` touched-content bitset to the emulator (about 1,400 ids across cards, relics, powers, monsters and potions). It is set at the central dispatch points: CardEffects `switch (def.Id)` and `switch (def.Name)` (`CardEffects.cs:33, :5569`), true results of `RelicEffects.HasRelic`, `BuffSystem.Get` hits, and EnemyAI move execution. Export it as `Sts2_GetTouched`. (2) Each label stores the union of the bitsets over its simulations, plus 8 fingerprint worlds (world seed, a fixed-seed tempo-rollout continuation, the exact outcome vector). (3) On each emulator commit, take the changed content ids from the fix's mismatch signature; a shared-engine change counts as touching everything. Re-check only labels whose bitset intersects, by replaying their 8 fingerprint worlds (about 1 ms each). An exact match carries the label forward, tagged with the commit. Any difference queues a relabel.

- **Expected gain:** Silver Track D costs about 135 core-h and gold about 150 (DESIGN §4.5). A single-card or single-monster fix touches a few percent of positions, so a fix costs minutes of fingerprint checks plus a few core-h of relabelling instead of a full regeneration: about 20–50x less label compute per fix. It doesn't help on π_ref promotion, which still regenerates everything (`DESIGN.md:665`).
- **Effort:** 2–3 days (instrumentation and export 0.5; label-store fields and checker 1–2).
- **Precedent:** Ekstazi regression test selection from dynamic dependencies (ISSTA 2015, http://ekstazi.org/). Bazel's content-addressed action cache. Salsa incremental recomputation (https://github.com/salsa-rs/salsa).
- **Risks:** Indirect effects through shared paths (the damage pipeline, turn start) can be missed, and those changes must fall back to fingerprinting every label. Fingerprints must use the deterministic tempo continuation, because batched net inference is not bit-reproducible (`FINDINGS.md:566-570`: one of eight fights differed by 1 HP because of padding). Measure the cost of writing the bitset (about 1 ns per hook).
- **Check first:** Is a stored CRN world bit-reproducible across emulator rebuilds? Does the same seed and tempo continuation give the identical outcome when no touched content changed?

## Learning

RL-1 and RL-2 start only when ledger signals call for them (D5), so most ideas here rank lower for now. lrn-1 is the exception, because it is a correctness check.

### lrn-1 · Give the combat net Defect's orb ring (it can't see orbs today), and keep the end-turn probe until it can

**Priority: high.** A silent correctness bug for any use of r33hab's learned prior on Defect, checked in about an hour.

r33hab's `rl/combat_tokens.py` `encode()` (line 313 on) builds tokens from the hand, piles, player buffs, enemies, secondary intents and potions. It never reads `OBS_ORB_CAPACITY_OFFSET` or `OBS_ORB_OFFSET`, even though the observation publishes them: `src/sts2_gym/native.py:673-683` gives (type+1, passive, evoke) per slot with Focus applied, and `CombatObservation.cs:56` has MaxOrbs = 10. Every r33hab measurement used `--character Ironclad` (`train_combat.py:545`). The fix: add a TYPE_ORB token per filled slot, with an embedded orb-type id, passive and evoke magnitudes in F_MAGNITUDE-style channels and an explicit slot-ordinal channel, plus an orb-capacity channel on the global token. The slot ordinal matters because the encoder has no positional encoding, and evoke order (front orb first) is what makes Zap→Dualcast differ from Dualcast→Zap. Second, and just as important: don't apply FINDINGS' planned `--ablate-endturn` speed-up (`FINDINGS.md:592-593`, `combat_tokens.py:321-323`) to Defect until the orb tokens exist. The end-turn probe forks the position and ends the turn, so today it is the only way Lightning passive damage and Frost passive block reach the net. The ablation that found the probe "unused" (`FINDINGS.md:367-382`) ran on Ironclad, which has no orbs. Write a `show_sample`-style check that decodes a Defect position and confirms the orbs appear.

- **Expected gain:** Not quantified. It is the kind of change FINDINGS found pays off, fixing a broken observation (like the player/enemy buff mix-up found by reading one position, `FINDINGS.md:649-653`), unlike enriching a working one, which did nothing four times. Without orbs, the value head can't tell 3 Frost orbs from an empty ring, and the prior can't learn when to channel and evoke, which caps the whole ExIt loop. Once orbs are encoded, the probe can be dropped for Defect too (the ~2x on the prior call that FINDINGS expects; see cmp-2). Measure it as outcome NLL against the per-encounter marginal, and as policy-window capture on Defect positions.
- **Effort:** 3–5 h of code plus a test (mirror `src/Sts2Emulator.Tests/Cards/Defect/OrbObservationTests.cs` on the Python side), plus one night to regenerate the dataset, because the token layout changes.
- **Precedent:** In the same repo, the buff-ownership fix and the compositional card embeddings (`FINDINGS.md:199-214, 649-653`). More generally, AlphaZero-style nets fail silently when a state feature is missing, while the loss curve looks fine (FINDINGS' own warning).
- **Risks:** Orb values already include Focus, so Focus as a buff token is redundant but harmless. Lightning's random targeting means end states aren't fully deterministic. Datasets made before the change can't be reused (bump the feature/token version). Check that clones and resampled worlds populate the orb block.
- **Check first:** In a cloned, resampled Defect combat, is the 10-slot orb block populated in evoke order, with correct passive and evoke values after Focus changes? Does one decoded position match the live game's orb display via STS2MCP?

### lrn-2 · KataGo's self-play data recipe for combat ExIt: skip forced moves, randomise the playout cap, weight by policy surprise

**Priority: medium.** About 2–2.5x more fights per core-hour for the value and FightNet heads, once RL-1 starts.

`play_fight` (`rl/combat_mcts.py:874-886`) runs the full search on every move, including moves with one legal action, and generation records every position at one budget (6,400 fights × 300 sims). The recipe has four parts. (a) If the SemAction-collapsed legal set has one member, step without searching and record nothing. (b) Play every move at the PLAY budget (60–120 in hallways, 300–500 for elites), so fight outcomes come from exactly the π_ref that FightNet and the leaf value must predict. (c) Run a deep 300–600-sim Gumbel search only on a random p ≈ 0.25 of positions, plus any position where KL(prior ‖ a 16-sim Gumbel result) exceeds a threshold, and record only those as policy targets. (d) At merge (`prior_loop/loop.py`), weight recorded positions half uniformly and half by KL(raw prior → target). Keep value and outcome labels for every position.

- **Expected gain:** Per-fight cost falls from 300 sims per move to about 0.25·300 + 0.75·90 ≈ 140, and further after the forced-move skip: about 2–2.5x more fights per core-hour. Fights are what limits the value and FightNet heads (val loss bottoms at epoch 2 with train 0.95 vs val 2.33, `FINDINGS.md:481-486`; 8x data took NLL from 1.94 to 1.46, `:173-174`). The policy head gets fewer but sharper targets where its thin window is (it captures only 26–41%, `:473-474`). KataGo found playout cap randomisation beat every fixed cap at equal compute, and calls surprise weighting one of the larger improvements of its g170 run.
- **Effort:** 4–8 h, plus one matched-wall-clock paired A/B night on `rl/prior_loop/real_fight_set.json`.
- **Precedent:** "Accelerating Self-Play Learning in Go" (https://arxiv.org/abs/1902.10565), playout cap randomisation and Fig. 5. KataGoMethods.md, "Policy Surprise Weighting" (https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md).
- **Risks:** Dirichlet root noise inflates KL, so compute KL against the raw prior. Surprise weighting biases the prior toward rare moves; KataGo argues that is harmless for a search prior, but here the pointer net's calibration is reused as a Gumbel logit. With fewer policy rows, the policy head may need more epochs. Pre-register p and the KL threshold.
- **Check first:** In existing `generated.npz` data, what fraction of positions has exactly one distinct SemAction, and how concentrated is KL(prior → target)? Does the top quartile of positions carry most of it?

### lrn-3 · Auxiliary heads that are free signal: KataGo's soft-policy target and short-horizon value targets

**Priority: low.** Cheap, but a similar auxiliary idea already came to nothing in r33hab, and RL-1 is gated.

Add two heads to `rl/combat_net.py`, neither needing extra simulation. (1) A soft-policy head trained on the search target raised to 1/T and renormalised. KataGo uses T = 4 at about 8x loss weight. Under Gumbel completed-Q every legal action has a value, so the low-mass tail carries information, not noise. (2) Short-horizon value heads predicting (1−λ)·Σ_{t′≥t} λ^{t′−t}·Q_root(t′) over the rest of the fight, with mean horizons of about one and about three player turns, plus a direct "HP lost by the end of this enemy turn" target. The main head keeps its λ = 0.3 search/outcome blend.

- **Expected gain:** The fight-outcome target has std 0.00 within a fight (`FINDINGS.md:236-239`), so adjacent positions give no contrastive signal. Short-horizon targets vary step to step, and they carry less of the rollout pessimism that limits the main value head. KataGo reports the soft-policy target "greatly improves the speed of learning of the policy". A plausible result is +5–10 points of window capture and better top-1 agreement at equal data.
- **Effort:** 3–5 h, plus a 3-seed sweep over T ∈ {2, 4} and the loss weight (one night).
- **Precedent:** KataGoMethods.md, "Auxiliary Soft Policy Target" (T = 4, weight 8, adopted in v1.12) and "Short-term Value and Score Targets" (https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md).
- **Risks:** FINDINGS already found one auxiliary-as-regulariser idea worthless (the policy head didn't help the value head, +0.006 nats, `FINDINGS.md:607-608`), and these could come to nothing too. Use per-head checkpoints, so an aux head can't pick the stopping epoch.
- **Check first:** On `target_info.py`'s fixed positions, over 3 seeds at equal epochs, does adding the soft-policy head raise the held-out share of the policy-target window that the main policy head captures?

### lrn-4 · Order-invariant line targets: train the atomic pointer with a partial-label loss over end-state classes

**Priority: medium.** Possibly 1.3–2x more usable policy signal on most Defect turns. Shares bookkeeping, and the exact-hash prerequisite, with orc-7.

Spireline's PLAY root is over information-boundary lines deduplicated by end-state hash (DESIGN §4.1, `DESIGN.md:558, 568`). The learned prior, though, is a masked pointer over atomic first actions (`DESIGN.md:692`), and the design doesn't say how a line-level target becomes an atomic one. If the first action of the representative ordering gets all the credit, the mass for one plan splits arbitrarily: Defend, Strike, Strike and Strike, Strike, Defend are the same turn (`FINDINGS.md:413-414`). The candidate DFS enumerates orderings before deduplicating, so it can record, at no extra cost, the set F(L) of first actions that begin some ordering reaching each end-state class L. Train with the partial-label likelihood −Σ_L t(L)·log Σ_{a∈F(L)} p(a). Build Gumbel's line logits the same way (from the class mass, not the representative ordering's path probability), and break ties at play time with a fixed canonical order.

- **Expected gain:** An unmeasured estimate: much of the measured target entropy (a floor of 0.9–1.4 nats against ceilings of about 1.2–1.4) is indifference between orderings, not real uncertainty. Today the head is trained to reproduce that arbitrary split, and PUCT spends simulations on transposed branches. Orderings that do matter, such as Bash before Strike or the evoke order of orbs, reach different end states and are preserved.
- **Effort:** About 1 day (DFS bookkeeping, the loss, the `target_info.py` measurement).
- **Precedent:** "Transpositions and Move Groups in Monte Carlo Tree Search" (IEEE CIG 2008). Partial-label learning ("Learning with Multiple Labels", NIPS 2002; "Learning from Partial Labels", JMLR 2011). Bottled AI's end-state deduplication (cited in the design).
- **Risks:** It needs an exact end-state hash. A hash that misses hidden fields (orb order, a Dark orb's banked value, per-card cost-this-turn) would merge orderings that differ. "Same end state" in one determinization must hold in all of them; check that on a sample.
- **Check first:** Does the emulator expose, or can the clone support, an exact combat-state hash? On what fraction of PLAY roots does the chosen line's class have |F(L)| ≥ 2?

### lrn-5 · Make data transfer across ascension, act and budget: compositional encounter descriptors plus era inputs

**Priority: low.** Helps the most data-starved FightNet parameters, but RL-2 is Phase 2.

(a) FightNet reads an 88-way encounter one-hot (`rl/run_train/DESIGN.md:1471`), and the combat global token embeds a bare encounter id. Replace both with an EmbeddingBag over the roster's monster ids, plus numeric HP at the current ascension from `Generated/Enemies.g.cs` (MinHp/MaxHp and the `...BelowToughEnemies` variants), enemy count, act, room type and the weak flag. This is the same recipe as the compositional cards, which won by 0.073 nats once initialised at 1/√K (`FINDINGS.md:199-214`). Add A10 move damage from the Spire Codex monster data or the emulator's AI tables, since the Moves in `Enemies.g.cs` are empty. (b) Make ascension, combat budget and policy source or generation into network inputs, and stop discarding data at era boundaries. Today "changing either starts a new era", and buffers keep only the current budget, ascension and version (`DESIGN.md:1574-1584` in r33hab). Train on the pooled data and query at the current era. Character can be an input too, so Ironclad data can warm-start shared card and monster embeddings.

- **Expected gain:** Bosses and elites appear once per act per run, and Act 2–3 encounters are almost unseen in self-play, so per-encounter parameters are the most data-starved part of FightNet. Sharing through monster identity and HP turns hundreds of separate estimates into one model. Era pooling stops dropping up to 400k fights at each budget, ascension or feature change, and lets r33hab's A9 data (standing in for A10) feed the A10 target. (The raw idea also counted Track D's A0 data; D11 and D12 moved Track D to A10.)
- **Effort:** About 1 day.
- **Precedent:** KataGo trains one net across board sizes, komi and rules through input features and masking (KataGoMethods.md, "Training on Multiple Board Sizes via Masking"). The compositional card embeddings in r33hab.
- **Risks:** Era variables are confounded with deck quality, since later generations build better decks; validate on a held-out era (train on A9, test on an A10 slice, for example). Monster HP alone misses mechanics such as Artifact, minions and enrage, so keep a per-monster identity row as the residual term, as the card composition does.
- **Check first:** With one Act 1 boss (or one Act 2 elite) held out entirely, does the compositional FightNet predict its fights better than the smoothed per-encounter marginal, at 0 and at 100 training samples?

### lrn-6 · Luck-corrected V_run training targets at chance nodes the emulator can resample exactly

**Priority: low.** Could need 1.4–2x fewer runs for the same Brier skill, but RL-2 is Phase 2 and exact redraws are unproven.

This applies AIVAT's construction to training targets. During run self-play, at chance events with known distributions (card-reward offers per `CardPools.g.cs`, relic and potion drops, "?" room outcomes, the encounter draw, shop stock), clone just before the event, redraw the outcome K ≈ 8 times with reseeded streams, and score each resulting decision state with V_run. Each score is the max, or the policy-weighted value, over afterstates, which takes microseconds in numpy. The correction c_t = V(realised) − mean_k V(redraw_k) has zero mean under the true chance distribution whatever V is. So the target y_t = z − Σ_{t′>t} c_{t′}, combined with the existing β = 0.3 bootstrap, stays unbiased, and removes the luck of offers and encounters from every earlier decision's label. Optionally add a down-weighted correction for fight luck based on FightNet; that one is biased, so blend it and validate.

- **Expected gain:** Per-run final-floor SD is 3.6–4.5 floors (r33hab `DESIGN.md` §5.6), and V_run regresses through that noise. If the nodes that can be resampled explain 30–50% of outcome variance, label variance drops by that much. The cost is about K clones (17–70 µs each) per chance node, negligible next to a 20–120 s run. These are training targets, so the confidence-sequence note in the oracle section doesn't apply.
- **Effort:** 1–2 days.
- **Precedent:** AIVAT (https://arxiv.org/abs/1612.06915). "Variance Reduction for Reinforcement Learning in Input-Driven Environments" (ICLR 2019, https://arxiv.org/abs/1807.02264). "Variance Reduction in Monte-Carlo Tree Search" (NIPS 2011).
- **Risks:** Unbiasedness needs the redraw to come from the true conditional distribution. Pity timers, GrabBag tag rejection (`EncounterTags.g.cs` notes it moves later draws) and the cross-stream coupling flagged in the design's F9 all get in the way, and a redraw that shifts other streams changes the future. Corrections also add V's noise, so measure the variance actually removed before relying on it.
- **Check first:** Can the run engine clone just before a card-reward or encounter roll and redraw only that outcome from its true distribution, leaving other streams untouched? In generation-0 data, what share of final-floor variance do those nodes explain?

### lrn-7 · Exact human states as self-play and Deep Monte Carlo start points (a demonstration-state curriculum)

**Priority: low.** Gives real Act 2–3 states, but the sample is small and reflects one player's style. Depends on data-1 and a save loader.

Each archived `current_run.save` (data-1) is an exact, loadable game state at a decision point a human actually reached at A10: deck, relics, potions, HP, gold, map position, RNG counters, grab bags and encounter queues. Build a loader from save to emulator state. Then start a fixed share (50%, say) of Gumbel ExIt episodes and V_run Deep Monte Carlo rollouts from these states, re-determinizing hidden state from the information set rather than using the saved RNG. Run the rest from Neow. Weight start states toward Acts 2–3 and elites. Extend later with AutoSlayer states (fid-8) and data-2's rebuilt fight starts.

- **Expected gain:** A weak early policy at A10 rarely reaches Act 3, so Act 3 learning gets almost no samples. Starting from Act 2–3 states skips about 2/3 of a run's steps per Act 3 sample, which gives about 3x or more Act 3 samples per CPU-hour. Training mass also lands on the realistic states that SpireBench and live parity are scored on.
- **Effort:** 1–3 days for the loader (depends on how close the emulator's state model is to SerializableRun); 0.5 day for the sampler.
- **Precedent:** "Learning Montezuma's Revenge from a Single Demonstration" (2018, https://arxiv.org/abs/1812.03381). Backplay (https://arxiv.org/abs/1807.06919). Go-Explore's restore-then-explore (https://arxiv.org/abs/1901.10995).
- **Risks:** Bias toward one player's deck-building style, so mix with Neow starts. A leak is possible if saved RNG or hidden queues are used instead of re-determinized ones, so enforce information-set resampling at load. The supply of start states grows only with play time.
- **Check first:** How much converter work does it take to load a SerializableRun `current_run.save` as an emulator run state at room entry?

### lrn-8 · Adopt a sibling project's measured results as priors, and replicate the three that would change Spireline's plan

**Priority: medium.** An evening of reading and a few overnight runs could avoid multi-week dead ends before RL-1 or RL-2 start.

ytcs/sts2-solver (a bit-exact Rust simulator with a real-game oracle, ExIt, A10, v0.111.0) publishes about 50 measured claims with paired standard errors in `docs/research/evidence.md`. Several bear directly on Spireline's learning plans:

- E8: much larger search (8×64, 3-turn, 3.5x the time) was no better than 5×32, 2-turn, on 200 tail fights.
- E22/E23: no policy target closed the gap between network and search (search agrees with the reference 0.90–0.95, networks 0.65–0.71), so "the stack must not depend on policy quality".
- E25/E26: 48% of near-miss losses are unwinnable even with perfect information, the avoidable share is 2–19%, and the errors are spread across setup turns, so a sharper value judge helps more than depth.
- E30: P(win run) from rollouts is about 0 from A10 starts; they replaced it with a floored per-act gate array.
- E21: a near-miss bench (replay close losses and wins from fight start with the same fight seed and a new search seed) gives a paired SE of about 0.009.
- E36: exact current-turn search gives +0.011.
- E20: an observation audit found calculated card numbers hidden in 23.8% of states.

Record these as explicit priors. Before committing compute to deeper search, to ExIt by policy distillation alone, or to DMC V_run trained on P(win), replicate E8, E22 and E30 on Defect v0.107.1 with r33hab (a few hundred fights each). Adopt the near-miss bench for combat-policy A/B tests.

- **Expected gain:** Avoids multi-week dead ends for the price of a few overnight runs. The near-miss bench concentrates evaluation on fights where the policy can matter (1,230 losses plus 1,500 close wins gave an SE of about 0.009), several times cheaper than full-run seed batteries of 312–1,096 seeds.
- **Effort:** 1 evening of reading; 2–3 evenings plus overnight runs per replication.
- **Precedent:** https://github.com/ytcs/sts2-solver/blob/main/docs/research/evidence.md. r33hab `rl/FINDINGS.md` (CRN and prior results).
- **Risks:** A different build (v0.111.0), different main characters (Ironclad and Silent), and a different search and network, so findings may not transfer to Defect's orb-heavy, multi-turn play. The claims are not peer-reviewed. No licence, so read only.
- **Check first:** Does E8's plateau (no gain from 3.5x more search) replicate on 200 Defect A10 near-miss fights in r33hab at two search budgets?

## Evaluation

### eval-1 · Prediction-powered SpireBench aggregates: silver labels everywhere, gold on a random subset

**Priority: medium.** Half a day, reuses labels that will exist anyway, and could save 60–100 core-h of gold labelling per π_ref promotion.

Some metrics are aggregates over positions: mean regret, top-1 agreement, ε-best rate, and the promotion gates. For these, label every test position at silver (or at bronze, for silver-level metrics), and only a uniformly random subset at gold. Estimate each gold-level aggregate as the mean over the gold subset of (gold − silver) plus the mean over all positions of silver, with a valid CI from PPI++ with a power-tuned λ. Per-position gold verdicts stay wherever a per-position claim is made. Optionally, choose gold positions by silver uncertainty (active inference) with inverse-probability weights.

- **Expected gain:** For the same CI on an aggregate, the number of gold-labelled positions falls by about 1/(1−ρ²), where ρ is the per-position silver-gold correlation: about 2.8x at ρ = 0.8. Gold costs about 150 core-h per 200 positions and is redone at every π_ref promotion. It stacks with AIVAT-style luck correction, which targets per-game luck rather than label fidelity.
- **Effort:** About half a day. The estimator is a few lines; add it to `spireline/eval/stats.py` rather than installing `ppi_py`.
- **Precedent:** "Prediction-powered inference" (Science 2023, https://arxiv.org/abs/2301.09633). PPI++ (https://arxiv.org/abs/2311.01453). "Active Statistical Inference" (2024, https://arxiv.org/abs/2403.03208).
- **Risks:** Valid only for aggregates over a truly random gold subset, never for per-position claims. If silver is selected or tuned on the gold subset, validity breaks. Low silver-gold correlation on decisive positions shrinks the gain, though the estimate stays valid. Fix the gold subset in the pre-registration.
- **Check first:** What is the per-position correlation between silver and gold regret on the first pilot gold positions (about 50)?

### eval-2 · Human-par fight benchmark from Spire Codex A10 v0.107.1 data

**Priority: medium.** An external yardstick in honest units. The aggregate version takes a handful of API calls, and it is a test use that D13 allows.

Spire Codex's public endpoint (https://spire-codex.com/api/runs/encounter-stats?bracket=a10&build_id=v0.107.1; `bracket=wr75` for top-quartile players; free community use at 60 requests/min under its API terms) returns, per encounter and character, the number of fights, the fatal count, the average damage taken and the average turns. For A10 Defect on v0.107.1 there are about 302k fights across 87 encounters. Act 1 elite examples (Spire Codex aggregates): Bygone Effigy 6,365 fights, 25.1 average damage, 491 fatal; Phrog Parasite 6,303 / 27.1 / 496; Byrdonis 6,246 / 30.8 / 402. For a paired version, rebuild each fight's starting state from `map_point_history` as in data-2, and check it against `players[0].deck`. Then run Spireline's combat policy on each start over K resampled worlds, and report HP saved against the human per encounter, with wr75 players as the bar. Local run history can be a first slice that needs no download.

- **Expected gain:** HP lost per fight compared with A10 humans and top players, with no live play and thousands of samples for every encounter. Per-encounter gaps show where to spend learning effort. Encounters where the agent does much worse than humans with similar decks point at emulator monster bugs, which complements a "too good to be true" audit from the other side.
- **Effort:** 1 evening for the aggregate comparison; 3–5 evenings for the paired rebuild (from the downloaded v0.107.1 export, or a paged `version=v0.107.1&limit=` pull).
- **Precedent:** ytcs/sts2-solver evidence E43 (a "whole-run combat swap": each of an expert's 25 fights restored and played by their agent, then compared with the human's real end HP) and E39 (expert-divergence counts), https://github.com/ytcs/sts2-solver/blob/main/docs/research/evidence.md.
- **Risks:** Selection bias: humans choose paths, abandon runs and save potions, so the agent must get the same potions. Each human fight is a single realisation, so only aggregates mean anything, never per-fight verdicts. Rebuild errors come from event transforms and enchantments. Average damage is truncated at HP for fatal fights. Publish only aggregates, with attribution (D13).
- **Check first:** Can a fight's starting state (deck with upgrades and enchantments, relics, potions, HP) be rebuilt from `map_point_history` well enough that the rebuilt final deck matches `players[0].deck` in at least 95% of A10 Defect runs?

## Compute

### cmp-1 · Parallel headless real-game fleet on the always-on PC

**Priority: medium.** 8–12x on the only tier with real Godot timing, if Steam allows several instances.

r33hab measured a headless real-game instance at about 148 MB RSS, a few % CPU and about 6 s to boot (`HANDOFF.md:2686`, on macOS). STS2MCP reads its port from `STS2_MCP.conf` next to the mod DLL (`McpMod.Config.cs:18,37`), so give each instance its own copy of the install with its own port, and its own Godot user dir by overriding `%APPDATA%` per process. Keep Steam Cloud off for the game (D1) so instances don't share remote saves; upstream warns that Steam Cloud restores deleted saves (`HANDOFF.md:533`). Run 8–12 instances with Instant mode and time scale (already in the mod, plus fid-7 if it works), each fed from a queue of capture jobs: live parity runs, card captures, AutoSlayer seeds. The game's `fastmp host|load|join` launch argument on 127.0.0.1 suggests the developer runs several instances on one machine.

- **Expected gain:** About 8–12x throughput on the GUI-engine tier. Overnight live parity batteries and card-capture sweeps that take days on one instance finish in hours.
- **Effort:** About 1 day (install copies, launcher script, job queue, health checks).
- **Precedent:** Upstream's verified headless boot (`HANDOFF.md:2665-2700`). The game's own `fastmp` multi-instance argument.
- **Risks:** Steamworks may refuse a second concurrent process for the same app and account. Each copy needs a few GB of disk (the .pck alone is 1.9 GB). Steam auto-updates could break version pinning, so launch the copies from outside `steamapps` and use proc-6's hash tripwire. Unmodded instances would upload metrics, so keep them modded or set `upload_data=false`.
- **Check first:** Can 8 or more headless instances from separate install copies, each with its own `%APPDATA%` and mod port, run at once under one Steam login without Steamworks init failures or save clobbering?

### cmp-2 · Tokenize in C#, writing zero-copy into the inference batch buffer; drop the end-turn probe only after lrn-1

**Priority: low.** Matters only once a learned prior and a GPU inference server exist.

Add `Sts2_WriteTokens(handle, int32* ids, float* feats, cap)`, a C# port of `combat_tokens.encode` (`rl/combat_tokens.py:313`). It writes one row of a preallocated numpy array per state, so `torch.from_numpy` wraps the whole batch with no copy. Remove `end_turn_outlook` (`combat_tokens.py:270`: five forks and five end turns per position), but for Defect only after lrn-1 lands, because the ablation showing the net ignores those channels (`FINDINGS.md:589-593`) ran on Ironclad. Keep the Python encoder as the reference, with an equality test on 10k random positions in CI, and port the §4.4 hidden-information tests so the C# encoder reads only fields the game displays.

- **Expected gain:** After batching, encode (0.55 ms) is the floor of a prior call (about 0.9 ms in total on one thread, `FINDINGS.md:572-580`). A C# encoder should take about 5–20 µs, which cuts the CPU prior call to about 0.4 ms (2–2.5x) and PUCT@60 from about 1.28 to 0.9–1.0 s per fight. With the planned GPU server (7.5 µs per state at batch 128, `FINDINGS.md:617`), Python encoding would be about 98% of the prior's cost, so without this change the GPU buys almost nothing.
- **Effort:** 1–2 days.
- **Precedent:** Upstream's own profile names encode as the next factor of about 2 (`FINDINGS.md:589-593`). Leela Chess Zero and KataGo build input planes in C++ next to the engine for the same reason.
- **Risks:** Two tokenizers can drift; the CI equality test covers it, and FEATURE_VERSION must be bumped on both sides together. Leaking hidden state is easier in C#, where all state is reachable, so the allow-list tests are mandatory. Dropping the probe needs a retrain with `--ablate-endturn`.
- **Check first:** Does a net retrained with `--ablate-endturn` match the current net on the 64-fight paired benchmark (mean HP within paired SE), on Defect positions with orb tokens present?

### cmp-3 · Fishtest-style preemptible work units on cheap ARM cloud, with anytime-valid merging

**Priority: medium.** Its first check (bit-identical results across builds) matters even with no cloud, because the Mac and the PC already differ.

Build a linux-arm64 NativeAOT emulator (r33hab's `build.sh` targets linux-x64, and arm64 is close to the M1). Split every label or battery job into small idempotent units: (position id, candidate set, CRN world index range [k, k+64), continuation version, emulator commit). Workers pull units from a small SQLite or HTTP queue on the PC, and write each result as a small JSONL or Parquet object to object storage (Cloudflare R2 has no egress fees). A preempted unit is simply re-issued. Because racing uses time-uniform confidence sequences over i.i.d. CRN worlds, finished units can be merged in any order without invalidating the verdict. Burst target: Hetzner CAX41 (16 Ampere cores at $0.0777/h, about 0.49 c/core-h as of June 2026). The same scheduler can use idle Mac and PC cores interchangeably.

- **Expected gain:** About 2–6x cheaper than the assumed 1–3 c/core-h. Tier B gold (about 320 core-h) would cost about $1.6 instead of $3–10, and a full silver plus gold Tier A (about 285 core-h) about $1.4. Ampere vCPUs are full cores with no SMT, which suits branchy single-threaded simulation.
- **Effort:** 1–2 days.
- **Precedent:** Stockfish Fishtest, a distributed queue of small game batches merged into SPRT (https://github.com/official-stockfish/fishtest). Leela Chess Zero's distributed clients. Hetzner's price table (https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/). Oracle Always Free terms (https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm) and the reported cut (https://infoq.com/news/2026/07/oracle-cloud-free-tier-limits/). R2 pricing (https://developers.cloudflare.com/r2/pricing/).
- **Risks:** Cross-architecture determinism: damage maths uses float (`BuffSystem.cs:239-280`), and CRN pairing across win-x64 (the PC) and arm64 (the Mac, the cloud) needs bit-identical outcomes. Hetzner reportedly listed CAX as limited or unavailable in mid-2026. The raw idea also proposed an Oracle Always Free VM (2 OCPU, 12 GB) as an always-on trickle worker; that goes beyond D9's bounded bursts, and Oracle reclaims instances idle below 20% CPU p95 over 7 days. Each new vendor adds an account and a data path. Only our own binaries go to rented machines, never game DLLs or the decompile (D9).
- **Check first:** Do the 32 committed run traces and a 1,000-fight CRN battery replay bit-identically on linux-arm64, osx-arm64 and win-x64 builds?

## Process

### proc-1 · Make the fix loop's regression guard fast: parallel sweeps, test-impact selection, JIT inner loop

**Priority: medium.** 3–5x more fix attempts per night, once the fix loop exists.

Each automated fix candidate pays for the C# suite (about 3,650 tests, about 2 min), a serial trace sweep (about 8 min, `HANDOFF.md:964-978`), Act 1 sweeps (about 20 min, `HANDOFF.md:2489`) and a NativeAOT publish. Three changes. (a) Shard trace replays and per-encounter sweeps over cores with a process pool; the scripts currently run serially. (b) Build a per-test coverage map nightly (dotnet-coverage or coverlet per test, plus orc-10's touched-content bitsets). For a candidate, run only the tests and fixtures that cover the changed methods or DefIds, plus a 5% random sample. (c) Validate candidates on the JIT build (`dotnet test`) and publish NativeAOT only for the accepted fix. A full guard still runs nightly before the morning summary.

- **Expected gain:** A candidate's guard drops from about 10–30 min to 1–3 min. That is roughly 3–5x more fix attempts per night, and agent sessions stop waiting on the guard.
- **Effort:** About 1 day.
- **Precedent:** Predictive test selection at Meta (https://arxiv.org/abs/1810.05286). Ekstazi regression test selection. Google TAP selective testing.
- **Risks:** Selection can miss a regression through shared code; the nightly full guard and the 5% random sample catch it within a day. JIT and AOT behaviour can differ (float, trimming), so the AOT trace check stays mandatory before acceptance.
- **Check first:** Of a typical fix candidate's guard wall time, what share is the serial trace and encounter sweep, and how much of it does a single-content fix actually need to touch?

### proc-2 · Compare each emulator build with the previous one on a fixed corpus, and send every changed trajectory to the referee (like Dolphin's FifoCI)

**Priority: medium.** Every fix generates its own high-yield referee tests for free, once a referee and a fix loop exist.

Keep a frozen bank of about 20k emulator trajectories: seeded A10 Defect fights across Act 1–3 encounters, a mix of deck sizes and archetypes, a fixed rules policy, and CRN seeds. On every emulator commit, including each automated fix, replay the bank on the old and new builds and hash each trajectory. At about 70 µs per step that is well under a minute on 8 cores. Group changed trajectories by first divergent event (fid-5) or by the (card, power, monster) they touch. A fix should change only trajectories that touch the mechanic it fixed. For each group, rebuild the divergence state in the referee (an sts2-cli room save, `set_draw_order` and a prefix replay, or the live game) and decide which build is right. Unexpected groups block the merge.

- **Expected gain:** A blast-radius check that the real-trace regression set can't give: that set covers 32 runs, while the bank covers what the search visits. Every changed trajectory is, by construction, a state where at least one build is wrong, which makes it the cheapest high-yield referee test available: no fuzzing and no search. Most collateral damage from fixes is caught at commit time rather than weeks later in label audits.
- **Effort:** About 1 agent-day (bank generator, hash diff, grouping, hand-off to the referee).
- **Precedent:** Dolphin's FifoCI replays a corpus of recorded GPU FIFO logs on every build and flags rendering changes for review (https://github.com/dolphin-emu/fifoci). Csmith cross-checked compiler versions differentially (PLDI 2011).
- **Risks:** A fix to a common mechanic (draw, block rounding) changes most trajectories, so adjudicate one representative per first-divergent-event group. Version the bank with the lock hash, or it drifts.
- **Check first:** Can the referee be put into the exact state at a trajectory's divergence point (deck, relics, HP, draw order, enemy state) using sts2-cli's `set_player`, `enter_room` and `set_draw_order` plus a prefix replay?

### proc-3 · An overnight agent harness that never stops for a prompt

**Priority: low.** The raw design rests on Claude Code's sandbox in WSL2, and the PC runs native Windows, where that sandbox doesn't exist.

As proposed: run Claude Code in WSL2 with the Bash sandbox in auto-allow mode (bubblewrap; writes limited to the work item's git worktree; a short `network.allowedDomains` list; `allowUnsandboxedCommands=false` and `failIfUnavailable=true`). A PreToolUse or PermissionRequest hook allows Edit and Write inside the worktree and denies them elsewhere, so nothing waits on a human. The agent never launches the game. Instead, a small Windows-side capture service, started by Task Scheduler at logon, owns the headless game processes and exposes a job API on 127.0.0.1 (`POST /capture {seed, ascension, character, action_script}` returns a fixture JSON). The agent can submit jobs and read fixtures, but can't touch the install, the mods folder or Steam. Each work item is one `claude -p --max-turns N --output-format json` run in its own worktree, and its output is a branch. Hooks on the Notification matchers (`permission_prompt`, `idle_prompt`, `quota_auto_resume_*`) and on StopFailure with `error=rate_limit` log an event and requeue the item for after the limit resets. Remote Control lets the maintainer unblock a session from the Claude app. On native Windows, the parts that survive are the capture service, one worktree per item and hook-based requeue. Zero-prompt Bash there would run unsandboxed, which `pc-setup/WINDOWS.md` advises against. A sandboxed host (the Mac, or a Linux box) could run the agent instead, if it can reach the capture service safely.

- **Expected gain:** Upstream's loop gets its autonomy by running `claude --dangerously-skip-permissions` with no sandbox (`scripts/ralph/ralph.sh:139-140`). This harness would get the same zero-prompt behaviour with limits the OS enforces. Estimate: from about 1 productive agent-hour per night to 4–6, capped by usage limits (see proc-4). A confused agent also can't damage the game install or Steam.
- **Effort:** 5–8 agent-hours; about 2 h of maintainer setup.
- **Precedent:** Upstream's Ralph loop (`scripts/ralph/ralph.sh:139-140`, `scripts/ralph/COPILOT.md`). Claude Code sandbox docs (https://code.claude.com/docs/en/sandboxing). The hooks reference (https://code.claude.com/docs/en/hooks). Remote Control (https://code.claude.com/docs/en/remote-control). The Desktop "Auto-continue when limits reset" option (https://code.claude.com/docs/en/whats-new/2026-w33). The headless game boot the capture service would use (`HANDOFF.md:2666-2700`: about 6 s to drivable and about 148 MB RSS, verified on macOS only).
- **Risks:** No sandbox on native Windows (above). Auto-allow widens what Bash can do inside the worktree, so keep secrets and tokens out of reach. Headless launch with `steam_appid.txt` is verified only on macOS. Remote Control is a research preview. Requeue logic must be idempotent: one worktree and one branch per item.
- **Check first:** Adapted from the raw question, which asked whether a WSL2-sandboxed command can reach a service on Windows' 127.0.0.1. Without WSL, which host can run the agent sandboxed and still reach the PC's capture service over a narrow, authenticated channel? Or must the loop stay ask-first on native Windows?

### proc-4 · Per-mismatch context packs and a usage budget for each fix

**Priority: medium.** If packs cut tokens per fix 3–5x, everything the fix loop does is multiplied by that. The check reuses closed catalogue entries.

For a hobby project, agent usage is the binding constraint, and upstream is expensive to explore: `HANDOFF.md` is 203 KB (about 50k tokens), `docs/divergence-catalog.md` is 486 KB (about 120k), `AGENTS.md` is 43 KB, and the C# emulator is 6.2 MB across 504 files. Write a deterministic generator that turns a shrunk mismatch (signature, seed, step) into one pack of at most about 15k tokens. The pack holds:

- the first diverging step of both traces;
- the full, unstripped decompiled method(s) for the entity;
- the emulator code for it, found by a `relic_pair.py`-style whole-tree grep for the id constant and printed with its enclosing function;
- the existing tests that touch the entity;
- the 3 nearest closed catalogue entries by signature;
- the exact command that must go green.

The agent prompt says to read only the pack and a STATE.md of at most 2k tokens, never `HANDOFF.md` or the catalogue. Route work by type: mechanical items (fixture re-capture plus `generate_capture_tests.py`, test-count updates, rebases) run as scripts or on a smaller model, and rule-port fixes get the strongest model. Record usage per item from `--output-format json`, so the morning summary shows tokens per fix and fixes per usage window.

- **Expected gain:** If an exploratory fix costs about 150–300k tokens and a pack-driven one 30–60k, that is 3–5x more fixes per usage window and per weekly cap, and each fix is easier to review because one file explains it. Upstream saw the same effect when reading cards: `card_pair.py` is "the only way the rate is bearable" (`HANDOFF.md:2773`).
- **Effort:** 5–8 h for the generator, using upstream's `card_pair.py` and `relic_pair.py` as references rather than as code; 1–2 h to measure.
- **Precedent:** Upstream's `scripts/card_pair.py` and `scripts/relic_pair.py` (see their docstrings). The Ralph `progress.txt` "Codebase Patterns" convention (`scripts/ralph/COPILOT.md`). SWE-agent, which found that a narrowed agent-computer interface raises solve rates (https://arxiv.org/abs/2405.15793).
- **Risks:** A pack can miss where a mechanic actually lives, which leads to a duplicate implementation. HANDOFF documents two such cases: Howl from Beyond's effect sits in `CombatEngine.EndTurn`, and Equilibrium gets its block through `ApplyGeneratedCardApproximation`. Mitigations: the whole-tree grep, the existing-tests section, and a rule that the agent may widen its context once if the pack's command still fails. Packs must never strip source; upstream warns that stripped source produces confident wrong readings. Packs contain decompiled code, so they stay local and never enter this repo.
- **Check first:** Take 5 already-closed catalogue entries and redo each fix from a reverted branch, once with a pack and once without. What are the tokens-to-green and the success rate in each case?

### proc-5 · A two-way decision inbox with one-tap answers, plus a fortnightly hands-on session

**Priority: low.** Only worth it if the loop produces more than a few human-only decisions a week.

Anything the loop can't decide alone becomes a GitHub issue in a private ops repo, made from a fixed template. Each issue has 2–4 labelled choices (for example `decide:model-as-game`, `decide:game-bug-ignore`, `decide:park`, `approve:mechanism-test-change`, `gate:G2-passed-start-RL1`), a one-paragraph context, a link to the context pack (proc-4), the default action and the cost of waiting. A nightly plain script (`gh`, no LLM) reads the labels and acts. An item left untouched for 7 days takes its pre-declared safe default, which is park, never merge. The pre-registered gates in `eval/prereg/*.yaml` are evaluated nightly by script, and an inbox item opens only when a gate flips. Items that need the maintainer's hands get a `needs-hands` label: Steam Guard re-login on the PC, re-enabling the mod in the in-game Mods screen after a rebuild, a reboot, live A10 parity sessions. These are batched into one checklist for a 60–90 min session every two weeks. The phone (GitHub mobile) is the interface. GitHub is already in use, so no new vendor is added.

- **Expected gain:** A judgement call waits under 24 h and costs about a minute, instead of waiting days for the next desk session. A 26-week project might see 100–200 such calls, so most of the time the loop sits idle waiting goes away, and it keeps working on unblocked items meanwhile. Hands-only steps become one planned slot instead of scattered interruptions.
- **Effort:** 3–5 h.
- **Precedent:** Kubernetes Prow's label-driven `/approve` and `/lgtm` automation (https://docs.prow.k8s.io/docs/components/plugins/approve/approvers/). Dependabot comment commands.
- **Risks:** Inbox inflation if the agent asks too often: cap the open items, and require each to state its default and its cost of delay. Defaults must be the safe action (park or skip). Gate evaluation must read the frozen pre-registration, not editable thresholds.
- **Check first:** Does the loop produce enough human-only decisions to justify an inbox (more than about 3 a week)? Count them in the first two weeks of loop logs.

### proc-6 · Watchtower: progress heartbeats, an outside dead-man's switch, and a build-hash tripwire on the loop's ground truth

**Priority: medium.** Near-zero running cost. Build the tripwire as soon as any unattended job runs, because it blocks the worst failure an automated fix loop can have.

(a) Every unattended process (capture service, emulator batteries, training, each agent item) writes heartbeat rows with a progress counter (steps, fights, tests) to a local SQLite database. A supervisor tells "alive but no progress for 30 min" (a game hang, an endless fight, an agent waiting on something) apart from "dead", and kills or requeues according to job type. (b) The PC can't report its own death, so it pushes an hourly heartbeat commit to a private GitHub repo. A scheduled GitHub Actions workflow there opens an issue, which notifies by email, when the last heartbeat is more than 6 h old. (The raw idea used a scheduled Claude routine for this check; a plain scheduled job does the same with no LLM.) (c) Once a day the PC polls change feeds: Steam branch build ids from api.steamcmd.net (public = 23811903, last updated 2026-06-19; public-beta = 24724944, last updated 2026-08-14), Spire Codex `/api/beta/version` (v0.111.0 at the time of writing), and new commits on r33hab/sts2, STS2MCP and the watched forks. (d) Tripwire: the capture service hashes `sts2.dll` before every job and refuses to run if the hash differs from `versions.lock`, and the fix loop refuses any fixture that lacks that hash. A silent Steam update can then never push the loop into "fixing" the emulator toward v0.111 behaviour.

- **Expected gain:** A stalled night is caught within hours instead of at the next weekly look. Rewriting correct emulator code to match a different game build is ruled out by construction.
- **Effort:** 3–6 h.
- **Precedent:** The healthchecks.io dead-man's-switch pattern (https://healthchecks.io/docs/; open source and self-hostable). Upstream's `SEED_TIMEOUT` for endless fights (`scripts/night_train.sh:31`). The STUCK detector in morefreeze/sts2-cli (`agent/bug.md`, BUG-051). api.steamcmd.net (https://api.steamcmd.net/v1/info/2868840).
- **Risks:** api.steamcmd.net is a third party; the fallback is the `buildid` in Steam's own `appmanifest_2868840.acf` on the PC, which `pc-setup/spec-check.ps1` already reads. Long legitimate jobs could raise false alarms, which is why heartbeats track progress counters, not wall time.
- **Check first:** Steam starts at boot on the PC, and the game is set to update only on launch. Can a game update still change files in the directory the capture service runs from, without anyone launching the game through Steam?

### proc-7 · Patch blast radius, worked out before the patch lands

**Priority: medium.** The forecast costs an hour or two today, and archiving the v0.107.1 replays is time-sensitive.

Three layers. (1) Free, today: Spire Codex's `/api/beta/diff` (8 KB of JSON) lists every entity that changes between v0.107.1 and the v0.111.0 beta. That is 78 cards changed and 19 added, including 13 of the 88 Defect cards (Biased Cognition, Helix Drill, Hyperbeam, Ignition, Momentum Strike, Null, Refract, Rocket Punch, Shatter, Sunder, Synchronize, Thunder, Trash to Treasure), plus 15 monsters, 21 relics and 9 powers (and 2 powers removed). Mapped onto `/api/encounters`, 16 of the 80 act encounters are touched: 8 of 42 in Act 1, 3 of 20 in Act 2, 5 of 18 in Act 3. (2) Fingerprints: tag every fixture, mismatch fix and oracle label with the entity ids it can touch (deck, relics, potions, encounter monsters, powers seen), plus each entity's behavioural digest. Upstream already computes such a digest for cards, ignoring UI-only lines (`scripts/audit_cards.py:92`), and for monster move machines (`audit_enemy_moves.py`). Add a "mechanism epoch" taken from the MECHANISM_TESTS outcomes (`scripts/patch_refresh.py:51`). On patch day, recompute the digests and invalidate only the items that intersect a change; a change in any mechanism test invalidates everything. This reuses orc-10's touched-content sets. (3) Optional rehearsal: install the public beta into a separate folder on the PC (SteamCMD `force_install_dir`; the maintainer logs in) and run upstream's `patch_refresh.py` report-only each week. Spire Codex uploads have moved to the beta (at least 125 Defect A10 replays on v0.107.1 against at least 687 on v0.111.0), so archive the v0.107.1 replays now.

- **Expected gain:** The content-level forecast: about 80% of encounter-level fixtures and fights survive. Patch-day re-capture, which uses the scarcest resource (live game time), shrinks to the roughly 20% of touched encounters plus fixtures that hold changed cards. Relabelling shrinks to the intersecting positions; an honest range is 20–60% of labels surviving, because a late-act Defect deck often holds one of the 13 changed cards. The STS2MCP recovery for v0.107.1 took about 40 days (`DESIGN.md:500`), and a worklist known in advance shortens ours.
- **Effort:** 1–2 h for today's forecast; 6–10 h for fingerprints in the ledger and fixture metadata; 3–4 h for the beta rehearsal, plus about 30 min of the maintainer's time for the SteamCMD login.
- **Precedent:** Spire Codex `/api/beta/diff` (https://spire-codex.com/api/beta/diff) and `/api/history/{entity_type}/{entity_id}`. Upstream's patch playbook and digest audits (`HANDOFF.md:2701` on, `scripts/patch_refresh.py`, `scripts/audit_cards.py`). Content-addressed selective invalidation in Bazel and Nix build caches.
- **Risks:** Entity-level diffs miss changes to shared code (RNG streams, shuffle, hook order); the mechanism epoch and the decompile rehearsal exist to catch those. The static touched set over-invalidates, which is the safe direction. The beta is not the final patch, so the forecast is only directional. Decompiling the beta has the same terms-of-service position as decompiling v0.107.1: one's own install, never published.
- **Check first:** What fraction of the current SpireBench positions and committed Defect A10 fixtures contains none of the entity ids the v0.111 beta changes? This can be computed today from `/api/beta/diff`.

### proc-8 · Get our A10 Defect fixtures into upstream's CI, not just our bug reports

**Priority: low.** We have no fixtures yet, and upstream has never taken an external PR. The crater-style fallback is the useful part.

Contribute game-sourced A10 Defect fixtures (combat sweeps for Act 1–3 encounters, run traces, card captures) to r33hab/sts2 as small PRs in upstream's format. Generate the assertions with upstream's `scripts/generate_capture_tests.py`, so only the game side moves (`HANDOFF.md:2883`). Upstream CI already runs `bash lint-and-test.sh` on GitHub-hosted windows-latest runners for every push and PR (`.github/workflows/ci.yml:11,34`), and it builds without game files because the generated data is committed (`src/Sts2Emulator/Generated`). Once our fixtures are merged, every upstream commit, including those from its own agent loop, is checked against our configuration for free. Today upstream's suite barely covers that configuration: `tests/fixtures/combat` has 2 A10 fixtures and no Defect combat fixtures, and `run_trace` has 1 Defect trace out of 33. Start with one small PR and an issue proposing the fixture convention, then send batches. If upstream declines, run the same fixtures nightly in our own CI against upstream HEAD, crater-style.

- **Expected gain:** A10 Defect regressions are caught before they reach us, and our patch queue tends toward zero. Across a year that includes patch days, this removes most of the rebase-and-re-verify hours.
- **Effort:** 2–4 h per PR batch; about 1 h of maintainer time for correspondence.
- **Precedent:** Rust's crater, which runs downstream crates' tests against compiler changes (https://github.com/rust-lang/crater). The "upstream first" practice. Upstream already treats game-sourced fixtures as regression truth (`tests/fixtures` is 85 MB).
- **Risks:** Upstream has one maintainer and had never had an external issue or PR (last push 2026-10-05), so it may not respond; the crater-style fallback still catches regressions within a day. The suite was cut to 1m40s (`HANDOFF.md:964`), so keep fixtures small and offer a slow tier. Fixtures embed game-derived values, so stay within upstream's existing convention, and check `CONTRIBUTING.md`'s no-game-content rule before committing any fixture to this repo.
- **Check first:** Will r33hab review and merge an external PR at all? Send one 2-fixture PR and see whether it gets a response within 2 weeks.

## Top 10 to check first

These are the ten high-priority ideas, ordered so that the cheapest and most time-sensitive checks come first.

1. **data-1 · Flight recorder.** Install the watchers now, because the game keeps only 5 logs. Then check: does a logged Defect combat replay from its room-entry save to the next save's RNG counters exactly?
2. **sim-1 · sts2-cli at logic speed.** Measure CPU time vs wall time over 1,000 actions on the PC (1–2 h).
3. **fid-7 · Headless, fixed-fps real game.** Does `--headless --fixed-fps` work on the shipped exe with STS2MCP and finish a combat (2–4 h)?
4. **fid-3 · Referee inventory.** Count the `TestMode.IsOn` reads and Godot references in rules code, and test whether the real GodotSharp Mathf runs in plain .NET 9.
5. **fid-1 · Desync checksum.** Does GenerateChecksum run after every single-player action, and does it cover piles and RNG? (A read of the decompile.)
6. **fid-2 · Built-in replay verifier.** Can NetReplayGameService replay a `.mcr` headlessly? Check it in the same reading session as fid-1.
7. **fid-4 · Displayed-preview oracle.** Can the emulator reproduce the game's hand-text and `vs_targets` numbers for every Defect card and orb? Start on the committed traces; no capture needed.
8. **fid-6 · In-process function tests.** Do sts2.dll and the managed emulator load side by side, and do the generators run on a hand-built RunState?
9. **orc-5 · Calibration of the hidden-state sampler.** Is there an import path that rebuilds a position from I alone, plus a test-build export of the true hidden state?
10. **lrn-1 · Orb tokens.** Decode one cloned, resampled Defect position: is the orb block populated correctly, and does the encoder read it (about 1 h)?

## Excluded, merged and adjusted

### Excluded by the no-LLM rule

None. No raw idea puts an LLM inside Spireline's system (search, labels, priors, values or explanations), so none was excluded by the no-LLM rule. Close calls that were kept:

- proc-3 and proc-4 are about Claude Code as the development agent (its harness and its usage). That is development tooling, like the agent reading this file, not a system component.
- fid-13 has the agent read fork diffs. Its output is a registry that scripts and people use, not labels.
- proc-6's outside watchdog was a scheduled Claude routine in the raw version. It is replaced here by a plain scheduled GitHub Actions job.
- proc-5 already specified a plain script with no LLM.

### Merged near-duplicates (59 raw ideas → 52)

- **data-1** ← "Passive flight recorder: archive every godot.log, current_run.save write and latest.mcr on both machines" + "Passive flight recorder: archive the game's own godot.log and every current_run.save write on both machines"
- **data-2** ← "Deal real A10 Defect fight starts reconstructed from human runs as the ExIt and FightNet fight distribution" + "Train on the decks humans actually bring: a bank of ~300k A10 Defect fight starts from v0.107.1 runs"
- **sim-1** ← "Remove sleep-polling from sts2-cli so the referee runs at logic speed, not wait speed" + "Remove the sts2-cli sleep-polling bottleneck (Windows 15.6 ms timer tick)" + "Make the real-engine referee 10x+ faster: event-driven drain plus batch/replay modes in the sts2-cli fork"
- **fid-5** ← "Harmony-instrumented RNG and hook event ledger from the real engine, diffed against the emulator" + "Record a step-by-step event log from the game and diff it against the emulator's (the NES 'nestest.log' method)"
- **orc-1** ← "Fit the rollout policy by simulation balancing, per character, instead of hand-picked tempo weights" + "Distil a learned fast rollout policy (AlphaGo-style linear softmax) and run the whole playout natively"
- **orc-2** ← "Event-keyed randomness so common random numbers stay in sync after candidate lines diverge" + "Reseed search-world RNG per turn and per monster to keep common random numbers coupled"

### Adjusted to fit current decisions

- **sim-1:** the raw "run the referee under WSL2" option was dropped (native Windows PC). The Windows timer fix and the event-driven drain remain.
- **proc-3:** the WSL2 sandbox premise doesn't hold on native Windows; the entry says what survives.
- **data-2, data-3:** training on the Spire Codex export conflicts with D13 and needs a new decision. Local run history isn't covered by D13.
- **lrn-5:** "Track D's A0 data" no longer exists after D11 and D12.
- **cmp-3:** the always-on free-tier cloud worker goes beyond D9's bounded bursts.
- **cmp-2:** dropping the end-turn probe now waits for lrn-1 (the two raw ideas conflicted).
- **proc-6:** the LLM routine was replaced with a plain scheduled job.
- **orc-2, orc-3, orc-4:** variance-reduction gains are qualified by the confidence-sequence width issue open in `LOG.md`.
