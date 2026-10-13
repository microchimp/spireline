# Upstream map: the r33hab/sts2 emulator and its lineage

This is a map of what the upstream project already does, so that Spireline builds on it
instead of redoing it. It is written for the agent that is about to build and use the emulator
on the Windows PC.

It was compiled on 2026-10-13 from nine structured reader reports on the pinned commits.
Nothing in it was re-run by Spireline. The upstream state is as of 2026-10-05: that is the pin
date, and also the day all three r33hab repos were published to GitHub. A reader checked on
2026-10-10 that nothing had been pushed since then.

## About this document

**Pins**

| Repo | Commit | Default branch | Notes |
|---|---|---|---|
| r33hab/sts2 | `b7452170ce1df91de29d3c94acb11d87c7efc708` | `spire-coach` | The emulator, Python bindings, `rl/`, verification scripts. `main` mirrors evangambit/sts2 main. |
| r33hab/STS2MCP | `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4` | `spire-coach` | The live-game mod (payload schema 4). It is not a GitHub fork: it has no parent repo. |
| r33hab/spire-coach | `af2975f` (as read) | `dev` | The coach, grader, scoreboard, dashboard, fight lab and autopilot. It has no licence file. |
| evangambit/sts2 | main `37e4264` (2026-09-09) | `main` | r33hab's copy of this history has new SHAs with identical trees (twin `cd93393`), because a GPG signature was stripped. |
| Zamiell/slay-the-spire-2-emulator | HEAD `04cfe6d` | `main` | The original emulator (MIT). |

**Conventions**

- Citations are `file:line` or a commit SHA, as the readers gave them.
  - Plain paths are in r33hab/sts2 at `b745217`.
  - `coach/`, `panel/`, `tests/fakes/` and `docs/superpowers/` paths are in r33hab/spire-coach.
  - `McpMod*.cs` paths are in r33hab/STS2MCP.
  - "roadmap" means spire-coach `docs/superpowers/plans/2026-09-27-fidelity-and-strength-roadmap.md`.
  - "design" means spire-coach `docs/superpowers/specs/2026-09-23-spire-coach-design.md`.
  - "catalog" means `docs/divergence-catalog.md`.
- Status words (DONE, PARTIAL, PLANNED, ABANDONED) are the readers' classifications.
- **UNVERIFIED** marks four kinds of claim: a reader's own inference, a single source nobody
  confirmed, a number that exists only in a commit body with no data in any repo, and a figure
  derived by a reader.
- Many upstream docs lag the code. Where a doc and the code disagree, this map follows the code
  at the pin and says so.
- In upstream `rl/`, "real fights" means fight starts recorded during *simulated* self-play,
  not fights in the live game (`rl/prior_loop/real_fights.py:1-22`).
- People are named only by GitHub handle.

---

## 1. Summary

### 1.1 What it is

The upstream project reimplements the game logic of Slay the Spire 2 **v0.107.1** (Steam build
23811903) as a fast, deterministic C# .NET 9 NativeAOT library, with Python bindings. It is made
faithful to the live game by differential testing against the real game, which a modded copy of
the game exposes over a localhost HTTP API.

On top of the emulator sit three more pieces:

- **An agent stack:** determinized combat MCTS, a learned fight prior, and a run-level value
  network trained by self-play.
- **A local product, spire-coach:** a live move coach and grader, a fidelity scoreboard, an
  unattended "fight lab", and a whole-run autopilot.
- **Unattended training and capture jobs** that run on more than one machine.

None of it uses an LLM at runtime.

Lineage:

```
Emulator:  Zamiell/slay-the-spire-2-emulator (2026-05/06) -> evangambit/sts2 (2026-08-14..09-09)
           -> r33hab/sts2 (2026-09-23..10-05)
Mod:       Gennadiyev/STS2MCP -> evangambit/STS2MCP -> cat12079801/STS2MCP (merged 2026-09-23)
           -> r33hab/STS2MCP (fixes from cicero225 and enderzcx ported by hand)
Product:   r33hab/spire-coach (2026-09-23..10-05)
```

### 1.2 How far along (at the pin)

| Area | State | Key evidence |
|---|---|---|
| Combat content | All five character card pools are implemented and tested. Relics 296/296, potions 63/63, enchantments 21/22, and every game power is bucketed. 111 enemies, 88 encounters. | `Generated/*.g.cs`; `docs/enchantment-coverage.md:12`; catalog:2817-2828 |
| Run layer | 4 acts, Neow and ancients, rewards, shops, events, act transitions, The Architect, ascension 0-10 including the A10 double boss. **Ironclad only.** | `RunEngine.cs:19-117`, `RunEngine.cs:36-53`; `e2cde9e`; `0b83ff5` |
| Live verification | Strongest for **Act 1, A8, Ironclad**: combat starts 32/32, run generation 30/30, act selection 88/88, 32 full-run traces replay clean (one known capture race aside). Acts 2-3 are checked by combat sweeps and one live session. A10 evidence is thin. | `HANDOFF.md:176-200, 2049-2052`; `scripts/check_run_traces.py:35-57`; roadmap:19 |
| Throughput | About 72 µs per step (about 14,000 steps/s per env) and about 714 µs per MCTS simulation. That is about 10x short of the project's own target. | `docs/agent-interface.md:251-316` |
| Agent strength | Simulator only. The A10 Ironclad full-run champion reaches a mean of 29.3 floors on 1,000 eval seeds (generation 40), then plateaus. **No real-game win rate exists.** | spire-coach `0c403b0`; `1359912`; roadmap:101-112 |
| Coach | It works locally: live combat advice and grading, a fidelity check on every move, unattended fight lab and autopilot. Strategy advice is Act 1 only. | `coach/live.py`, `coach/grader.py`, `coach/autopilot.py` |
| Engineering health | CI has never run on r33hab and has been red upstream since 2026-08-19. Most measured results sit in commit bodies. Run data is gitignored. | `.github/workflows/ci.yml`; `HANDOFF.md:127-130` |

### 1.3 How it works

1. **Data.** The game DLL is decompiled locally with ilspycmd (`scripts/decompile.sh`). The
   `decompiled/` folder is gitignored, because it is the game's copyrighted code.
   `extract_data.py` writes the `Generated/*.g.cs` tables, and `data/id_map.json` freezes every
   entity id.
2. **Logic.** Behaviour is ported by hand from the decompiled source into C#: `CardEffects`,
   `EnemyAI`, `RelicEffects`, `RunEngine` and the rest. It sits on a bit-faithful port of the
   game's RNG and its named, counted streams.
3. **Bindings.** The library is built NativeAOT and loaded from Python through ctypes
   (`src/sts2_gym`). It is exposed as Gymnasium envs, a mod-style command layer, a live-snapshot
   converter and a JSON-lines engine service.
4. **Truth.** The live game runs with the STS2MCP mod, often headless, and is driven over HTTP
   on `localhost:15526`.
   - Captures become committed fixtures, and generators turn the fixtures into C# tests.
   - Expected values come from the decompiled source or from captures, **never from emulator
     output** (`AGENTS.md:123-125, 254-256`).
5. **Search.** `clone(resample_hidden=True)` produces determinizations, and MCTS runs over the
   clones. The engine service offers `analyze`, `check` and `strategy` to spire-coach.
6. **Learning.** Self-play on the emulator trains a fight prior and run-level value networks.
   Champions are exported to the coach and the autopilot.
7. **Feedback.** The coach, the fight lab and the autopilot check every live move against the
   emulator. Mismatches are written to gap files and then fixed in agent-driven sessions.

---

## 2. Timeline and how the work is done

### 2.1 Phases

| Phase | Handle | Dates | Commits | What it added |
|---|---|---|---|---|
| Original emulator | Zamiell | 2026-05-23 to 06-03 | 143 | The C# NativeAOT emulator, the Python gym and the Ralph agent loop, verified on Ironclad only. It used .NET's legacy `Random` and about 1,530 lines of trace-fitted "answer key" code. |
| Fidelity programme | evangambit | 2026-08-14 to 09-09 | 467 on main (about 660 counting the rewritten duplicates on other branches) | A faithful RNG port and removal of the answer-key code. Live capture harnesses, all five card pools read and captured, all relics, 32 run traces, the divergence catalogue (E1-E493), audits and the patch pipeline. Ends with combat MCTS and a transformer prior (`rl/FINDINGS.md`). |
| Coach and training | r33hab | 2026-09-23 to 10-05 | 432 across 3 repos (270 sts2, 25 STS2MCP, 137 spire-coach) | spire-coach, the live engine service, the live fidelity check, run-level self-play, real A10, the fight-prior loop, run replay of real sessions, the fight lab and autopilot, unattended jobs, and deck decisions from paired fights. |

Founding decisions from the evangambit phase (`PLAN.md`):

- Reimplement the simulator, and use the real game only as an oracle, because the game cannot
  be cloned fast enough for search (`PLAN.md:1-42`).
- Use C# rather than Rust, because porting C# into Rust would add bugs of its own
  (`PLAN.md:46-79`).
- Fork Zamiell's emulator rather than start again (`PLAN.md:210-250`).
- Model one fixed, fully unlocked profile (`PLAN.md:705-710`).
- Freeze entity ids and only ever append to enums (`PLAN.md:712-716`).

### 2.2 Key dates in the r33hab phase

| Date | Event | Evidence |
|---|---|---|
| 09-23 | spire-coach design spec | design |
| 09-24 | Mod token auth and hidden/debug gates; configurable ascension; live search; combat snapshot loader | STS2MCP `6dfd3b4`; `42d7782`; `b2e0e0b`; `9ec10b2` |
| 09-24 to 09-27 | Design stages 1-3 built and merged (the design estimated weeks for these) | `369bb67`, `04c80aa`, `ad4a95a`, `56e317f` |
| 09-27 | Roadmap with workstreams A-F and milestones M1-M4; Acts 2-3 playable end to end | spire-coach `6aeee71`; `c0cc012` |
| 09-28 | M1/M2 merges; A10 double boss; The Architect; fight lab and autopilot; seed-exact run replay; `audit_effects`; self-play at real A10 | `e2cde9e`, `0b83ff5`, spire-coach `7eb54ce`, `9a67d51`, `a33f846`, `d61d8a5` |
| 09-29 | Fight prior checked at the coach's budget and kept off by default | spire-coach `3977894`, `2cb5473` |
| 09-30 | Night-only and 24/7 job scripts | `a75de56`, `5b40dd7` |
| 10-01 | Promotion moved to 1,000 eval seeds; simbugs2 merge (80/80 quarantined seeds complete) | `788df59`, `9821f46` |
| 10-04 | Generation-40 champion drives the autopilot; warm start from the champion; a 19-hour native loop is quarantined | spire-coach `0c403b0`; `1359912`; `af335d3` |
| 10-05 | Deck decisions from measured paired fights; the autopilot card-reward bug fixed; all repos published | `dce4612` .. `b745217`; spire-coach `db6d486` |

### 2.3 How the work is done

- **Agent-driven development, both eras.**
  - In the evangambit era, most commits carry Claude co-author trailers (450 of 467 on main).
  - In the r33hab era, every spire-coach plan opens by requiring the subagent-driven-development
    skill from the Claude Code "superpowers" plugin.
  - Plans carry Global Constraints, a "Review Focus" list, checkbox tasks and acceptance tests.
  - A "controller" session dispatches implementer and reviewer subagents, merges their branches
    and runs live smoke tests. There is one git worktree per workstream.
  - Commits such as "Task N review follow-ups (k/3)" record the reviews (for example `307229c`,
    `4cff4be`, `64aacdf`). Specs are approved in conversation.
  - Only 5 of the 270 r33hab sts2 commits carry an AI trailer: Copilot, on simbugs2 (`53a12cf`,
    `38b0801` and others).
- **Errata and rulings.** `rl/run_train/DESIGN.md` has its own numbered errata (E3-E11, O4-O5),
  and plans add "Rulings against the spec". The largest is erratum E11, which moved training
  from ascension 0 to A10. A9 stood in until real A10 landed on 09-28.
- **Pace.** Design stages estimated at 4-6 and 3-4 weeks were built in about 3 days. On 10-05
  the deck-decision feature went from spec to plan to about 10 implementation commits in about
  40 minutes.
- **Ralph loop (inherited and dormant).** `scripts/ralph/ralph.sh` loops a coding agent (Copilot
  CLI by default, or Claude Code or amp) over `prd.json` stories.
  - Zamiell ran it once, for about 2 hours on 2026-05-24, and it produced 30 commits.
  - It has been unchanged since the fork's initial commit `aa4b0d8`, and neither evangambit nor
    r33hab ran it.
  - It contains Windows backslash paths.
- **Hidden working notes.** The SDD reports were removed from git (spire-coach `72be84e`). Two
  fidelity reports are still readable in history:
  `git show 702e745:.superpowers/fidelity-act23.md` and
  `702e745:.superpowers/sdd/fidelity-act23-report.md`. Some plans cite an SDD workspace (research
  notes, a "ledger" of rulings) that is in no repo.

### 2.4 Unattended jobs

The project runs jobs on more than one machine: a night-only job and a 24/7 job, with results
synced back every 5 minutes. The dashboard shows synced jobs as running while their files are
under 40 minutes old (`coach/dashboard.py:44-67`).

| Job | Script | Schedule | What it does | Evidence |
|---|---|---|---|---|
| A10 full-run training | `scripts/night_train.sh` | Night only. Started by hand each evening; stops itself at 07:30 or a set date. | Runs `rl.run_train` at real A10 with workers = cores - 2 and a 900 s per-seed timeout. Each learner warm-starts from the champion at lr 0.0005. Since 10-05 it plays 4,000 paired fights per generation. It plays its fights with the exported fight prior (on by default). | `night_train.sh:1-136`; `1359912`; `e394b78` |
| Fight-prior learning | `scripts/desktop_fight_job.sh`, `scripts/fight_loop_rounds.sh` | 24/7 in tmux | Runs `rl.prior_loop`. The dashboard lists four loops: a 300-sim teacher, a 192-wide 3-layer net, a 600-sim teacher, and the bigger net with a 600-sim teacher. It runs one round per process, because one long-lived process kept growing for 27 hours and trained 3.5x slower. | `desktop_fight_job.sh:2-21`; `757ad18`; `coach/dashboard.py:53-66` |
| Machine setup | `scripts/desktop_setup.sh` | One-off | Installs packages, uv and .NET 9 over SSH, builds the native library, runs the test suite and a 20-fight smoke run. | `desktop_setup.sh:1-92` |
| Training quarantine | `rl/run_train` runner | Inside every job | Seeds that crash, raise or time out are retried once, then quarantined to `retries.jsonl` and `quarantine.jsonl`. These lists fed the simbugs native fixes. | `rl/run_train/loop.py:9, 87, 456-464`; `9821f46` |
| Live sweeps | `scripts/capture_sweep.py`, `scripts/combat_sweep.py` | Per invocation | Launch the headless game if it is down, embark seeded runs and compare with the emulator. | `capture_sweep.py:123-158` |
| Fight lab, autopilot | spire-coach `fight-lab`, `autopilot` | Per invocation, unattended | Play real fights or whole real runs, with every move checked against the emulator. | `coach/fightlab.py`, `coach/autopilot.py` |

### 2.5 CI, tests and where results live

- **CI is effectively off.**
  - `.github/workflows/ci.yml` runs `lint-and-test.sh` on windows-latest.
  - On evangambit/sts2 it ran 197 times with 4 successes, the last on 2026-08-19. It has never
    run on r33hab/sts2.
  - HANDOFF records `lint-and-test.sh` as known to fail since a black version bump
    (`HANDOFF.md:127-130`).
  - All verification is run locally, by hand or by agents.
- **Results mostly live outside the tree.** `runs/` (sts2) and `data/` (spire-coach) are
  gitignored. No status, eval, champion, scoreboard or autopilot output is committed.
  - Measured numbers survive in long commit bodies (for example `0c403b0`, `3977894`, `2cb5473`,
    `db6d486`, `788df59`, `1359912`) and in the deleted reports at `702e745`.
- **History caveats.**
  - About ten SHAs cited in r33hab's own docs and messages do not resolve in any published repo
    (for example `4f6a485`, `272a8ef`, `7f06f06`).
  - Nothing has been pushed since publication, and the plans say "Never push", so any local
    progress after 2026-10-05 is not visible.

### 2.6 Where to read

| Document | Lines | Covers | Freshness |
|---|---|---|---|
| `HANDOFF.md` | 2,935 | Emulator fidelity work, how-tos, gotchas, measured numbers | Mostly written 2026-08-15..31. r33hab added about 22 lines. Many "open" items are closed in code. The test counts and API versions quoted are old. |
| `PLAN.md` | 993 | Founding decisions, progress log, a "Next up" list | Last edited 2026-08-31. Its "Next up" list predates all the RL work. |
| `AGENTS.md` | 572 | Coding conventions and fidelity rules | evangambit era. It claims `start_replay` exists; it does not. |
| `README.md` | n/a | Coverage tables | Stale: it says 250/296 relics. |
| `docs/divergence-catalog.md` | 2,993 | Every divergence found, with cause and metric | Frozen 2026-09-07. No r33hab-era findings are in it. |
| `docs/agent-interface.md` | n/a | Determinism, hidden-information contract, throughput | Mostly current |
| `docs/replay-verification.md` | n/a | Full-run replay design | Most of it is not built (section 4.5) |
| `rl/FINDINGS.md`, `rl/ARCHITECTURE.md` | n/a | evangambit's combat-agent results; the two-level search design | `ARCHITECTURE.md` says nothing in it was implemented when it was written (`rl/ARCHITECTURE.md:6-10`) |
| `rl/run_train/DESIGN.md`, `FULL_RUNS.md` | n/a | Run-level training design, errata, measured baselines | Current, with internal contradictions about A10 |
| spire-coach design, roadmap, deck-decision spec | n/a | Product goals, workstreams A-F, latest work | The roadmap is the real plan of record |

---

## 3. The emulator

### 3.1 Architecture

- **Size.** 54,527 lines of C# in 52 files, about 2.7x Zamiell's 20,558-line baseline. The
  largest files are `CardEffects` (10,870 lines), `RunEngine` (6,120), `EnemyAI` (5,761) and
  `CombatEngine` (5,304).
- **Combat.**
  - Card behaviour is one large switch: 254 constant `case` labels in `CardEffects.Apply`, plus
    481 by-name labels in `ApplyDefectCard`, `ApplyNecrobinderCard`, `ApplyRegentCard` and
    `ApplyMiscGeneratedCard`.
  - Any card without a case silently falls back to its printed damage and block
    (`CardEffects.cs:2453-2461, 7681-7714`). The name `ApplyGeneratedCardApproximation` is also
    the by-name dispatch path, and does not mean those cards are approximate.
  - Each monster is a bespoke case in `EnemyAI`. There is no general move machine
    (`src/sts2_gym/live/enemy_ai.py:1-23`).
  - There are 246 `BuffId`s and 28 `CardSelectionKind`s, so in-combat choices are real actions.
  - Action encoding: `0..hand-1` plays a card, with the target as a separate argument; `hand`
    ends the turn; `hand+1..` uses potions (`CombatEngine.cs:3-9`).
- **Run layer.** It covers:
  - Neow and the act ancients, map generation for 4 acts, and the encounter, event, elite and
    boss sequences.
  - Unknown rooms; card, gold, potion and relic rewards; shops with 14 slots; rest sites;
    treasure; the Crystal Sphere, Fake Merchant and Scroll Boxes screens.
  - Act transitions and The Architect.
  - There are 14 `RunPhase`s, and the action mask is 256 wide (`RunPhase.cs:3-34`;
    `RunConstants.cs:102`).
- **RNG.**
  - `MegaRandom` is a bit-faithful Xoshiro256** seeded through Splitmix64. `GameRng` mirrors the
    game's `Rng` wrapper method for method: `NextBool` is `Next(2)==0`, there is a cast bias,
    and the Gaussian uses banker's rounding.
  - There are 12 named run streams and 3 player streams, plus per-act map, act selection,
    Neow/ancient, per-event, per-encounter (seed + TotalFloor + hash) and per-relic streams.
  - Seeds are canonicalised as the game does it: uppercase, O to 0, I to 1.
  - Zamiell's .NET `Random` was deleted. PLAN.md records that its one "bit-exact" result had
    about 17% odds of being a coincidence (`PLAN.md:276-284`).
  - Evidence: `Core/Rng/*.cs`; `Core/Run/EncounterRng.cs`.
- **Cloning and determinization.**
  - Deep copies are written by hand and guarded by a reflection test.
  - `Clone(rngSeed)` / `clone(resample_hidden=True)` rebuilds every stream from a new seed at the
    *same call count*. It reshuffles only the unknown middle of the draw pile (`KnownTopCount` /
    `KnownBottomCount`), and a run clone also resamples the Crystal Sphere's fog.
  - RNG clones replay `CallCount` draws, so their cost grows with how far a stream has advanced
    (`Core/StateCloning.cs`; `GameRng.cs:129-144`).
  - For the gap in this, see section 3.6.
- **Combat snapshots.** `Sts2_LoadCombatSnapshot` (format `sts2-emu-snapshot/1`) builds a fight
  at any mid-combat position, for **any character**, including orb capacity, Osty and stars.
  - It refuses anything it cannot honour exactly, and names the JSON path that failed.
  - It carries no RNG: the caller's seed also orders the unknown middle of the draw pile.
  - `Sts2_GetStateJson` writes a fight back out (`Interop/CombatSnapshot.cs:25-79`).
- **Python.**
  - `native.py` binds 83 exports: combat API v32 and run API v22. It checks freshness and
    version on load.
  - `Sts2CombatEnv` and `Sts2RunEnv` (ascension 0-10). `reset_arena` takes a deck, relics,
    potions, HP, ascension and encounter, but **no character**.
  - `commands.py` maps mod-style payloads onto integer actions.
  - The live converter (`sts2_gym.live`) accepts all five characters and rebuilds monster AI
    state from the live `state_log`, using about 99 hand-built models (67 Cycle, 32 bespoke).
  - The engine service (`python -m sts2_gym.live.service`) speaks JSON lines: `health`,
    `analyze`, `check`, `strategy` and `shutdown`.
- **Observation.**
  - Combat is 276 ints (computed from the constants) and run is 682. The layout is exported.
  - Pile order is never exposed.
  - Caps truncate rather than error: 5 enemy buffs, 10 player buffs, 10 cards in hand, 64 in
    the deck, 32 relics (`CombatObservation.cs:5-98`; catalog:2215-2240).
- **The real game cannot be the simulator.** Its logic is tied to Godot's SceneTree and async
  queues. Transpiling the decompiled code was rejected, because it is Godot-coupled and would be
  a derivative work (`PLAN.md:722-731`; `HANDOFF.md:2694-2699`).

### 3.2 Content coverage

| Category | In game data (v0.107.1) | Modelled | Read or tested | Live-captured | Evidence |
|---|---|---|---|---|---|
| Cards | 577 `CardDef`s: Attack 195, Skill 234, Power 111, Curse 18, Status 16, Quest 3 | 559 names have an explicit case; the rest fall back to printed damage and block | 577/577 read (`690d815`); READ ledger has 579 entries; tested-but-unread went from 194 to 0 | 541 capture fixtures covering 529 distinct cards. The catalogue says 511 of 512 singleplayer-reachable cards were played against the game (catalog:1071). | `Generated/Cards.g.cs`; `ImplementedCards.g.cs`; `scripts/audit_cards.py:104` |
| Card pools | Ironclad 87, Silent 88, Defect 88, Necrobinder 88, Regent 88, Colourless 64, Curse 18, Status 12 | Ironclad 85 implemented / 86 with suites; Silent, Defect, Necrobinder, Regent 88/88; Colourless 64/64 (README table, last changed 2026-09-09) | Every pool had a READ pass against the source | Fixture tags: Necrobinder 103, Defect 86, Regent 82, Silent 64, untagged or Ironclad 176 | `Generated/CardPools.g.cs`; `README.md:104-113` |
| Relics | 296: Ancient 100, Rare 50, Uncommon 40, Event 35, Common 30, Shop 30, Starter 10, None 1. Pools: Shared 118 + 8 per character. | 296/296; `RelicEffects.UnmodelledInRun` is empty | READ ledger 296; relic read pass: 3 of 58 diverged | No per-relic capture count reported; run traces exercised some (for example E59, Gremlin Horn) | `audit_relics.py:277`; `754331a`; `README.md:122` (still says 250) |
| Potions | 63: Common 20, Uncommon 20, Rare 20, Event 2, Token 1 | 63/63 have combat effects | n/a | n/a | `PotionEffects.cs:29-42` |
| Powers | 261 power files in the game; 242 `PowerDef`s extracted | 246 `BuffId`s: 246 resolved, 6 declared or dead, 9 co-op only | READ ledger 219 | n/a | catalog:2817-2828; `audit_powers.py:126` |
| Enchantments | 22 | 21 (SlumberingEssence is dead content) | n/a | Live checks found that enchantments apply per hit | `docs/enchantment-coverage.md:1-14` |
| Enemies | 121 game classes | 111 `EnemyDef`s (the roadmap counts 111 of 121); converter AI models for 100 of 111 | `audit_enemy_moves` VERIFIED table: 14 monsters | Via combat sweeps | roadmap:17; `5081b87` |
| Encounters | 88 (enum ids 0-87) | 88, each with a suite (`CombatCoverageTests.Pending` empty) | Suites written from the source | 80 sweepable: Overgrowth 22, Underdocks 20, Hive 20, Glory 18 | `CombatCoverageTests.cs:51`; `combat_sweep.py:87-171` |
| Events | 58 event ids including The Architect, plus 8 ancients (Neow, Darv, Orobas, Pael, Tezcatara, Nonupeipe, Tanx, Vakuu) | Counts differ by source: roadmap 65 of 68 (09-27), README 57 | Event sweep tests | 156 fixtures: 52 events with option captures, 99 outcomes, 5 Crystal Sphere | `RunConstants.cs:340-391, 564-603` |
| Acts and map | 4 acts: act 1 Overgrowth or Underdocks, act 2 Hive, act 3 Glory | All generated at run start. Base rooms 15/14/13, weak encounters 3/2/2, 15 elites per act, map width 7. | `ActMapShapeTests` | Act 1 run generation 30/30; act 2-3 maps checked against 2 real A2 runs | `HANDOFF.md:1374-1376`; `ActMapShapeTests.cs:9-23` |
| Ascension | 0-10 | All modifiers, including the A10 double boss | `DoubleBossTests`; mutation check on the A10 side | Mostly A8 (section 3.3) | `Ascension.cs:26-62` |
| Characters | 5 | Combat: all 5. **Run layer: Ironclad only.** | n/a | n/a | `RunEngine.cs:36-53`; `RunConstants.cs:932-969` |
| Multiplayer | n/a | Not modelled. 21 multiplayer-only cards are filtered out and 9 co-op powers excluded. | n/a | n/a | `HANDOFF.md:1948-1959` |
| Afflictions | n/a | No affliction system. The converter accepts 7 names; only Bound is stored per card. | n/a | n/a | `convert.py:102-104` |

### 3.3 Fidelity by act, character and ascension

**By act**

| Evidence | Act 1 (Overgrowth, Underdocks) | Act 2 (Hive) | Act 3 (Glory) |
|---|---|---|---|
| Combat opening state vs live | 32/32 (16 encounters x 2 seeds, A8). The first run was 3/16. | Hive and Glory openings together: 38/38 | (included in the 38) |
| Multi-turn combat sweep | 41-42 encounters at `--turns 6`: no behavioural failure (32 ALL MATCH; 9 coverage-only, later closed with `--play`) | First `--turns 5 --play` pass over Hive and Glory: 10 of 33 fights diverged and 5 could not be driven (`CombatCoverageTests.cs:23-41`). After fixes E427-E436: 79/79 verdicts with 1 abort (catalog:1618, 2242). | 72/72 verdicts, 0 aborts, 15 coverage FAIL rows (catalog:2257) |
| Seeds swept | Openings: 2 seeds per encounter | Few: QS2GYXRKWN at A8 and A9. Three more seeds found 4 more divergences (catalog:83-95). | Same |
| Run generation | 30/30 captures in every section, including map edges; act selection 88/88 | Act-2 ancient: 7/7 captures; maps checked against 2 real A2 runs | Maps: the same 2 runs |
| Full-run traces | 32 committed traces, all act 1 | None committed | None |
| Run-layer replay of real runs | 959/959 offerings over 32 fixtures (`9a67d51`) | One A10 autopilot run, 23 floors into act 2: 80/80 offers (`4bad19f`) | None |
| Live one-step checks (one A10 Ironclad session, 2026-09-27) | 46/62 comparable, 46/46 match | 8/69 comparable, 8/8 match | 48/129 comparable, 47/48 match; 48/48 after `f4379e3` |

Later per-session Act 2 figures (28/28 and 7/7) appear only in commit bodies (UNVERIFIED). No
later aggregate scoreboard output is committed.

**By character**

| Character | Card pool state | How a fight is built | Run layer | Live evidence |
|---|---|---|---|---|
| Ironclad | 85 implemented / 86 tested of 87 | Native reset | Yes, the only character | Every run-level oracle (traces, run generation, run replay, live sessions) |
| Silent | 88/88. When its suites were written against the source, 4/15 commons, 6/12 uncommons, 4/9 rares and 1/4 basics turned out wrong. | Snapshot or test | No | 64 card fixtures |
| Defect | 88/88 implemented and tested. On reading: 3 of 5 orbs wrong (E176-E178), 6/24 basics and commons, 10/36 uncommons and 5/27 rares and ancients wrong (E180-E201); the orb ring was added to the observation (E179). The capture pass then found only 3 divergences (E324 Echo Form doubled itself, E326 Modded missing from extracted data, E327). All 8 Defect pool relics have hooks. | **Snapshot loader or test builder only**: `CombatFactory` never sets orb slots | No | 86 card fixtures. **Sources disagree:** HANDOFF and `626b802` say 86 of 88 were captured, with Scavenge (selection screen) and Ignition (needs an ally) unreachable. The catalogue's per-pool table lists Defect 88/88, counting Ignition as multiplayer-only and Scavenge as read. |
| Necrobinder | 88/88. The capture pass found 36 divergences in 88 cards; the read pass found 20-21 more of 45. | Snapshot or test | No | 103 card fixtures |
| Regent | 88/88. The capture pass found 28 divergences (star cost and forge were missing); the read pass found 13 of 27 wrong. | Snapshot or test | No | 82 card fixtures |

The catalogue's per-pool capture table (catalog:56-66) lists Ironclad 29/85, Silent 21/86 and
Colourless 23/53, with 182 cards never played. A later line in the same file says 511 of 512
reachable cards were played. One reader judged the table stale.

The authors' headline lesson is that reading and testing a pool first cut the live-capture
divergence yield by about 10x (Defect 3 against Necrobinder 36 and Regent 28), but not to zero.
They estimate that about half of all unread cards are wrong, whatever the captures show
(`HANDOFF.md:326-328, 351-353`).

**By ascension**

| Level | Committed evidence |
|---|---|
| A8 | `Ascension.DefaultLevel`. Every card, event and run-trace fixture; 47 of 50 combat fixtures. |
| A9 | Hive and Glory sweeps on QS2GYXRKWN. DeadlyEnemies (A9) is the only practical combat difference between A8 and A10. Training used A9 as a stand-in for A10 until 2026-09-28. |
| A10 | 2 combat fixtures (`UVUYCBYWB6-{corpse-slugs,toadpoles}-a10`); 1 run-history fixture (`GNM8G0F5RF-a10`, run with debug HP buffers before fights); 47 live A10 positions in `tests/python/fixtures/live/captured`. The live coach, fight-lab and autopilot sessions at A10 are in gitignored `data/` and cannot be reproduced from the repos. |
| A0 | The default of `Sts2RunEnv`. No committed A0 live evidence was reported. |

### 3.4 A10 support

- `Core/Ascension.cs` ports `GetValueIfAscension` and `HasLevel`. The run engine accepts 0-10
  (`42d7782`).
- **Modifiers read from `RunState.AscensionLevel`:**
  - SwarmingElites: 5 elites at A0, 8 from A1.
  - WearyTraveler HP.
  - Poverty: gold x0.75.
  - TightBelt: -1 potion slot (base slots are 2 at A8).
  - Ascender's Bane.
  - Inflation: removal cost.
  - Scarcity: rare odds. The A8 rarity constants are 0.0149/0.005, against 0.03/0.01 at A0,
    read from `godot.log`.
  - Tough and Deadly enemy values.
  - DoubleBoss.
  - Evidence: `Ascension.cs:26-62`; `HANDOFF.md:697-699`.
- **DoubleBoss** (`e2cde9e`, 2026-09-28) adds one extra UpFront draw after the last act's rooms
  and a second boss one map row above the first. Neither last-act boss room pays a reward
  (`DoubleBossTests.cs:7-28`). A7 reward upgrades landed in the same merge (`ccc96fb`).
- **Defaults differ by layer.** The combat layer defaults to A8, `Sts2RunEnv` to A0, and C#
  `RunEngine.Reset` to A8. `Sts2CombatEnv` refuses a non-default ascension unless an encounter
  and `total_floor` are also given (`env.py:196-206`; `native.py:843-853`).
- **What is verified:**
  - DoubleBoss is derived from the source only: no live capture reaches the last act at A10.
  - A buffed A10 smoke run (X000C0010) beat the first act-3 boss and died to the second
    (`rl/run_train/FULL_RUNS.md:136-147`).
  - The fight lab approximates the double boss by cycling single bosses
    (`coach/encounters.py:123-127`).
  - A mutation that corrupts only the high side of `Ascension.Value` fails the three `_a10_`
    tests and leaves every `_a8_` test green (`HANDOFF.md:2303-2306`).

### 3.5 Performance

| Measure | Value | Evidence |
|---|---|---|
| Step, mixed phases, one env | About 72 µs (about 14,000 steps/s); later 12,500-13,900 steps/s | `docs/agent-interface.md:255-257, 382-383` |
| Combat step | Median about 54-58 µs. End turn 125 µs against 10 µs to play a card. `WriteObservation` 1.3 µs. | `docs/agent-interface.md:331-349` |
| Clone | About 17 µs with resampling early on (59,000/s). Later: combat 1.4 µs; run 8.8 µs with resampling (8.7-10.7 at real run positions); faithful run clone 7.1-8.8 µs. `RunEngine.Clone` about 0.07 ms against about 149 ms for `Reset`. | `docs/agent-interface.md:260`; `rl/run_train/DESIGN.md:352-359`; `HANDOFF.md:964-978` |
| One MCTS simulation | About 714 µs (1,400/s). 448 µs on a combat handle against 648 µs on a run handle; 0.40-0.41 ms per simulation inside whole runs. | `docs/agent-interface.md:300-303`; `DESIGN.md:358-364` |
| Live search | About 285 µs per simulation; about 5,400 simulations per 1.5 s in one process; about 24,000 per call on 4 workers; about 40,000 per move at the coach's budget | `b2e0e0b`, `b7fde66`; spire-coach `3977894` |
| Self-play throughput | Rules baseline 3,014 runs/h on 8 workers; full-run generation 0 at 3,774 runs/h on 12 workers; Act 1 runs at 120/500 take 12.67 s per run in one process | `DESIGN.md:559-576`; `FULL_RUNS.md:109-111`; `rl/run_train/smoke.py` |
| Handles | 256 combat + 256 run per process (255 concurrent clones measured) | `NativeExports.cs:417`; `RunNativeExports.cs:26` |
| Target | 1e5-1e6 transitions/s/core, unmet by about 10x. Where the remaining combat-step cost goes has not been found. | `PLAN.md:22-23`; `docs/agent-interface.md:384-387` |
| Test suites | C# about 2-6 min (serial); full trace sweep about 8 min | `HANDOFF.md:52, 964-978` |

The engine is **not thread-safe**. Mutable statics in `CombatFactory` (and `CardEffects`) mean
tests run serially and parallelism has to be process-level (`HANDOFF.md:82-89`;
`src/Sts2Emulator.Tests/AssemblyInfo.cs:3`).

### 3.6 Known faults

| Fault | Effect | Status | Evidence |
|---|---|---|---|
| The run layer is Ironclad-only, on every branch | `Reset` always deals the Ironclad starter deck, Burning Blood and 80 HP, with Ironclad reward, relic and potion pools. `Sts2Run_Reset` takes only a seed and an ascension. **A Defect run cannot be simulated end to end.** | PLANNED (roadmap E5 defers other characters until Ironclad at A10 is strong) | `RunEngine.cs:36-53`; `RunRewardGenerator.cs:22, 95, 153`; `RunNativeExports.cs:133-155` |
| No native reset builds a Defect fight | `CombatFactory` never sets `OrbCapacity`, so `reset_arena` with a Defect deck gets 1 orb slot on the first channel instead of 3 | Open | `CardEffects.cs:5269-5281`; `CombatSnapshot.cs:437-438` |
| Run determinization gap (**UNVERIFIED**: one reader's reading of the code; the repo does not state it) | A `resample_hidden` run clone copies the pre-rolled encounter and event sequences and both relic grab bags' shuffled queues verbatim. `ResampleHiddenState` touches only the Crystal Sphere and the active combat, so the clone still "knows" the next encounter, the next event and the next relic of each rarity. No test asserts these are resampled. | Not recorded upstream | `StateCloning.cs:442-452, 501-502`; `RunEngine.cs:943-955`; `StateCloningTests.cs:252-331` |
| Hidden sequences are readable through the native API | Run state lists 11-13 expose the encounter and event sequences. Policy features avoid them by convention and by a grep test. | Open | `RunNativeExports.cs:278-280`; `DESIGN.md:760-764` |
| The direct combat env assumes every RNG stream is at call count 0 | Exact only for a run's first combat. Mid-run fights need `Sts2Run_ForkCombat` or a snapshot. | By design | `HANDOFF.md:441-449` |
| Native crashes | Intermittent SIGSEGV, about 1 run in 200 (roadmap), and a SIGABRT on PRB00058. The root cause is a macOS .NET 9 NativeAOT SIGUSR1/SA_SIGINFO fault, worked around in `native.py` (`f70f8b7`). `FULL_RUNS.md` still lists it as remaining, handled by retry. The roadmap's acceptance (10,000 crash-free runs) is not shown. | PARTIAL | `native.py:111-167`; `FULL_RUNS.md:163` |
| Native infinite loops | Fiend Fire and Cascade loops were fixed (`53a12cf`, `38b0801`). On 2026-10-04 a training fight looped for 19 hours and was killed and quarantined, not fixed. The engine has no internal step cap; `CombatWatchdogTests` checks for a 10,000-step bound. | PARTIAL | `af335d3`; `CombatWatchdogTests.cs:9-33` |
| Silent fallback for cards without a case | They play as printed damage and block | Gated by the coverage test | `CardEffects.cs:2458-2461` |
| Coverage-gate blind spot (E405) | Membership comes only from `CardEffects.cs` case labels, so 18 cards implemented elsewhere are invisible to it | PLANNED fix | `HANDOFF.md:1214-1234` |
| Auto-played and nested cards (Havoc, Hellraiser, Stampede) | Their selection is resolved automatically, not offered as a decision | Open | `HANDOFF.md:431-433` |
| Approximations named in code | White Star's boss card pool; Royal Stamp's Niche shuffle; `IsRemovable`/Eternal not extracted and event pets not modelled (Hive ancients); Discovery `canSkip`; **Genetic Algorithm's growth across fights (a Defect card)**; Mad Science's tinkered card type; the Forbidden Grimoire payout; Innate granted by enchantments or powers; the Spoils Map act-map generator | Open | `RunState.cs:233-237`; `RunNonCombatEffects.cs:1106-1111, 2993, 3105-3110`; `CardEffects.cs:1107, 3830-3833, 5986`; `BuffState.cs:465-470`; `Card.cs:393` |
| Card reward pools never checked live | Recorded rewards were pinned per floor, so the pools themselves have no live check | Open | `HANDOFF.md:1957-1959` |
| Profile dependence | Act selection and boss discovery read the profile. Only one fully unlocked, all-discovered profile is modelled, and sessions with content mods cannot be replayed. | By design | `HANDOFF.md:2094-2096, 2896-2925` |
| Pinned game version | Every fixture is v0.107.1 (build 23811903). The patch pipeline has never been exercised on a newer build. | n/a | `data/game_version.json` |
| Map floor numbering (**UNVERIFIED**, single source) | One reader reports 17-row maps per act against the game's 16/15, so emulator floor numbers may differ from the game's | Unconfirmed | Agent-work reader; no file cited |
| Platform divergence | The history replay of one run maps Sapphire Seed to Plant on linux-arm64, where the macOS build takes Eat. Left open. | Open | commit message 2026-09-30 |
| Dead code | 163 unreachable card case labels; five cards were wrong in their dead copy | Kept deliberately | `HANDOFF.md:2804-2812` |
| Stale docs | HANDOFF quotes API v19/v16 (code is v32/v22); a header comment describes a 164-int observation (it is 276); README says 250/296 relics; the enchantment doc's "13 of 22"; FULL_RUNS says A10 is both modelled and not modelled | n/a | Section 2.6 |

### 3.7 Building and using it: gotchas for the PC agent

- **Toolchain.**
  - Pinned versions: .NET 9.0.317, ilspycmd 8.2.0.7535, uv 0.12.5, CPython 3.12.14
    (`HANDOFF.md:31-65`).
  - `scripts/build.sh` runs `dotnet publish -c Release -r <rid> --self-contained`. It picks
    `osx-arm64`, `osx-x64` or `linux-x64` by platform, and `win-x64` otherwise. It prefers a
    .NET 9 SDK under `~/.dotnet` (`build.sh:1-31`).
  - `lint-and-test.sh` publishes `win-x64`. AGENTS.md says nothing in the repo is Windows-only.
    evangambit's `FINDINGS.md` reproduce steps target win-x64.
  - A linux-arm64 run passed 5546/5546 C# tests on 2026-09-30.
- **Freshness guard.**
  - `native.py` refuses calls when the library is older than the C# sources (override with
    `STS2_ALLOW_STALE_NATIVE=1`), and checks the API versions on load (native 32, run 22).
  - Running `dotnet csharpier format src/` makes the library look stale, so every Python call
    and replay fails at once. That is the guard working, not a regression
    (`HANDOFF.md:958-962`).
- **Tests.**
  - The C# suite runs serially on purpose (`DisableTestParallelization`).
  - `lint-and-test.sh` runs only 4 of the 42-43 Python test files. Use `unittest discover` after
    a native build to run them all.
  - Some tests, and every audit, need a local `decompiled/` tree (`scripts/decompile.sh`). Keep
    it out of the Spireline repo.
  - `env.py` sets `MAX_EPISODE_STEPS=50`, which cuts fixture replays short; FightChecks uses
    1,000,000.
- **Engine quirks.**
  - An extra `step(0)` with no screen open means "play card 0"; check `pending_selection_kind`.
  - A summon is inserted in front of its summoner, so hold creatures by reference, not index.
  - Every mutating native export must call `run.WriteObservation`.
  - When cloning runs in tests, clear `EventRngStream` and `EventRngName`
    (`HANDOFF.md:1312-1314, 1462-1468`).
- **macOS only.** The SIGUSR1 workaround in `native.py` is for a macOS .NET 9 GC fault. The
  upstream fix is in .NET 10.0.13+ (`f70f8b7`).
- **Driving the live game.**
  - Headless needs `--headless` and `steam_appid.txt` containing 2868840. It boots to drivable
    in about 6 s (another note says about 14 s) and uses about 148 MB RSS.
  - A capture takes about 40 s per seed (HANDOFF) or about 15 s (the `capture_sweep` docstring).
  - spire-coach drives the GUI game through `steam://rungameid/2868840` instead.
  - The mod loads only at boot, so a rebuilt mod needs a game restart.
- **The emulator repo's harness scripts will fail against r33hab's mod.**
  `start_real_game_run`, `trace_real_game*`, `capture_*`, `combat_sweep` and
  `validate_real_game_*` send no `X-STS2-Token`, so they get 401. They also read the
  compendium seed and `draw_pile_ordered`, which r33hab's mod now gates. These scripts were not
  updated after the gates landed, and every harness fixture predates 2026-09-02.
- **Mod gates.**
  - Debug actions need `allow_debug_actions: true` in `STS2_MCP.conf` and a restart.
  - Hidden fields need `allow_hidden_state` *and* `GET ?hidden=1`.
  - The token comes from the conf file, or the `STS2_MCP_TOKEN` environment variable overrides
    it.
- **Debug actions.**
  - `debug_gain_max_hp` takes a **delta**. Sending the target every fight once stacked to
    110,080 max HP.
  - `debug_add_card` with `pile:'deck'` changes the master deck, not the current fight.
  - `debug_force_play_phase` only reports readiness; it forces nothing.
- **Spire-coach's own scope.** The spire-coach design lists Windows as out of scope
  (design:342-350). The job scripts and spire-coach assume Unix tools (tmux, rsync, caffeinate,
  pkill) and sibling checkouts of sts2 and spire-coach (`SPIRE_COACH_REPO` overrides one
  direction).

---

## 4. Verification programme

### 4.1 The live-game bridge (r33hab/STS2MCP)

The mod is about 15,800 lines of C#. It is three forks stacked on Gennadiyev's upstream:

- **evangambit:** room jumps, staging and seeded runs.
- **cat12079801:** card uids, stable entity ids, the `wait=true` settle, `is_resolving`, the
  pause menu, queue bounds, resolved damage and warnings.
- **r33hab:** token auth, the hidden and debug gates, the schema-4 simulator fields, the action
  log, time scale and `debug_kill_enemy`.

| Feature | Detail | Evidence |
|---|---|---|
| Transport | HTTP on `localhost:15526`. 9 routes: `/`, `/api/v1/singleplayer` (GET/POST), multiplayer, profiles, profile, compendium (includes the run history), wiki, and `actions?since=`. | `McpMod.cs:179-182, 373-461` |
| Security | Every request needs the `X-STS2-Token` or Bearer token: 64 hex characters, generated into `STS2_MCP.conf` with mode 0600, compared in constant time. Any `Origin` header gets 403; a non-JSON POST gets 415. | `McpMod.Config.cs:49-144`; `McpMod.cs:351-369` |
| Hidden-state gate | Only three fields are hidden-only: `player.draw_pile_ordered`, enemy `move_follow_up_id`, and the compendium's `current_run.seed`. They need the conf flag and `?hidden=1`, and never appear in POST, multiplayer or markdown output. | `McpMod.Helpers.cs:171-178`; `docs/raw-full.md:86-103` |
| Default payload (schema 4) | See the list below the table | `McpMod.StateBuilder.cs`; `McpMod.StateExtras.cs:41-558` |
| Actions | 45 in `ExecuteAction` plus 3 handled before dispatch; 18 are not in upstream | `McpMod.Actions.cs:71-119` |
| Debug actions (13, gated) | `debug_start_encounter` / `_event` / `_shop`; `debug_add_card`, `debug_set_energy`, `debug_set_stars`, `debug_add_power`, `debug_enchant_card`, `debug_force_play_phase`; `debug_gain_max_hp`, `debug_upgrade_deck`, `debug_enter_next_act`, `debug_kill_enemy` | `McpMod.Actions.cs:104-116`; `McpMod.Debug.cs` |
| Settle signals | `is_resolving` with reasons. `wait=true` polls every 60 ms, needs 3 settled reads, gives up after 3,000 ms with no change, and has a 500-30,000 ms timeout. Main-thread marshalling has a 10 s timeout and a queue of 32, and a 503 means "not executed". | `McpMod.cs:64-97, 217-322` |
| Action log | Card plays, potions and End Turn, tagged `human` or `api`, in a 2,000-entry ring buffer | `McpMod.ActionLog.cs:16-318` |
| Speed | `set_time_scale` from 0.5 to 10x, kept through hit-stops, plus an injected "Instant Mode" setting | `McpMod.TimeScale.cs`; `McpMod.SettingsUI.cs` |
| Lifecycle | Menus, the custom-run screen (seeded starts with an ascension), abandon, `rooms_entered` (fixed an embark crash that hit about 1 embark in 5), and `timeline_reveal_epochs` | `McpMod.CustomRun.cs:16-116`; `McpMod.Debug.cs:563-584` |

The default schema-4 payload carries:

- stable card uids, numbered so they cannot leak draw order;
- resolved per-target damage;
- enemy `move_id`, `state_log` and `ai_fields` (every primitive monster field, but no RNG
  objects);
- relic counters, fields and saved state;
- the ordered hand, discard and exhaust piles, and a sorted draw pile;
- orbs, combat history, the map on decision screens, warnings, and `loaded_mods`.

**Gaps that matter for Spireline:**

- The mod sends no `battle.rng` stream counters.
- It does not send `cards_drawn_this_combat`, `cards_generated_this_combat` or
  **`lightning_orbs_channeled_this_combat`** (`coach/snapshot.py:84-95`).
- There is no relic or potion staging, no exact HP setter, and no save-state restore.
- The upstream MCP server (the LLM play path) does not send the token, so it gets 401. It is
  abandoned.

### 4.2 Every kind of check

| # | Check | Oracle | Automation | Scale | Results | Evidence |
|---|---|---|---|---|---|---|
| 1 | Combat opening state (`combat_sweep.py`) | Live game, headless, through the mod | Unattended | 32 captures, A8, Ironclad | Deck order, roster and HP, intents and player HP exact on 32/32 (first run 3/16). Enemy damage had been one ascension too high on 13 of the first 16. | `HANDOFF.md:176-180, 2203-2222` |
| 2 | Multi-turn combat sweep (`--turns N --play --add-card --buff-max-hp`) | Live game, headless | Unattended (about 20 min per act); a person interprets aborts | 80 encounters in 4 acts. Each turn it compares hand order, pile sizes, 8 RNG stream positions, block and powers, and move coverage. | Act 1: no behavioural failure. Hive 79/79 (1 abort). Glory 72/72 (15 coverage FAIL rows). Mutations 4/4 caught. | `combat_sweep.py:87-171, 1568-1700`; catalog:1618, 2242-2278 |
| 3 | Run-generation sweep (`capture_sweep.py`, `verify_run_generation.py`) | Live `current_run.save` | Unattended, about 15-40 s per seed | 30 captures, both act-1 acts | 30/30 in every section, including map edges. The first 16 had 3 map failures (19%). | `HANDOFF.md:2011-2077` |
| 4 | Act selection from run history (`verify_act_selection.py`) | The game's own `saves/history/*.run` | Offline, no game driving | 88 runs | 88/88 on v0.107.1; older builds about 50% | `scripts/verify_act_selection.py`; `HANDOFF.md:2163-2178` |
| 5 | Neow seed screener (`screen_neow_seeds.py`) | Committed traces | Offline | 10 | 10/10 exact. All 25 known blessings are captured and replay clean. | `HANDOFF.md:863-873, 1477-1479` |
| 6 | Per-card live capture, turned into generated tests (`capture_card.py`, `generate_card_capture_tests.py`) | Live game, one staged play, RNG position pinned | Semi-automated, one card per command | 541 fixtures, 529 distinct cards. All A8, seed ABCDEF, 539 unupgraded, 512 against ByrdonisElite. | 541 generated `[Fact]`s. Found that damage multipliers truncate (6 x 1.75 = 10). The last about 200 cards found 1 defect. `blocked/` is empty. | `CardCaptures.g.cs`; `tests/fixtures/cards/blocked/README.md`; catalog:491, 1071 |
| 7 | Event, Crystal Sphere and shop captures | Live game | Semi-automated | 156 event fixtures, 1 shop, all A8 | 99 generated event tests | `scripts/capture_event.py`; `EventCaptures.g.cs` |
| 8 | Full-run trace capture, replay and manifest gate (`trace_real_game_run.py`, `replay_full_run_trace.py`, `check_run_traces.py`) | Live game state at every step | Capture semi-automated; replay fully automated and offline | 32 traces (76 MB), 85-251 steps, Ironclad A8 act 1, dying on floors 5-17 | Compares 15 per-step fields and 6 boundary fields. All clean except one known capture race (E491). The manifest fails in both directions. Going from 10 to 15 compared fields found 5 divergences at once. | `replay_full_run_trace.py:57-69, 140-176`; `check_run_traces.py:35-57` |
| 9 | Buffed captures (max HP and an upgraded deck on both sides, rolling no RNG) | Live game | Semi-automated | buff200 (216 steps), buff400 (251 steps), BUFFTEST01 (206 steps) | Reached late act-1 content; found E59 (Gremlin Horn) and a new divergence at step 87 | `HANDOFF.md:1425-1473` |
| 10 | Seed-exact run-layer replay of real runs (`replay_real_run.py`, HistoryReplayer) | Session logs joined to the game's run history | Offline, automated; needs `decompiled/` for event option order | 32 fixtures and 1 A10 autopilot run | 959/959 offerings; 80/80 over 23 floors. Fights are resolved with debug hooks so combat differences do not leak in. Modded sessions are excluded. | `scripts/replay_real_run.py:1-37`; `9a67d51`; `4bad19f` |
| 11 | Live one-step fidelity check (`sts2_gym.live.fidelity`, service `check`) | The next settled live position. 16 resamples, up to 256 when an unseen value appears. | Automatic in the coach, fight lab and autopilot | One A10 session to Act 3 floor 48; 168 Aeonglass checks | See the table in 3.3. 168/168 Aeonglass checks match (`6261f21`). Only deterministic mismatches and impossible random outcomes are flagged. | `src/sts2_gym/live/fidelity.py:1-61` |
| 12 | Offline log replay and scoreboard (`fidelity_replay.py`, `replay_unchecked_moves.py`, spire-coach `fidelity-scoreboard`) | Recorded sessions | One command | Every session log | Reproduced the roadmap's table exactly. Marks checks tainted by debug actions. No later aggregate is committed. | `scripts/fidelity_replay.py:1-47`; `coach/fidelity_scoreboard.py`; `9929bc7` |
| 13 | Fight lab | Live game | Unattended | Every Act 1-3 encounter. Picks the act with the fewest comparable checks first, elites and bosses first, 3 attempts each. | No aggregate committed | `coach/fightlab.py:1-243`; `coach/encounters.py:143-170` |
| 14 | Autopilot runs as a fidelity source | Live game | Unattended | Not reported | Tungsten Rod caused 38 HP mismatches in one run before `a7b404f`. From 2026-09-29 to 10-05 no card reward was taken (0 of 1,090). | `db6d486` |
| 15 | Source-reading ledgers (`audit_cards`, `audit_relics`, `audit_powers`; `card_pair`, `relic_pair`) | Decompiled source, keyed by digest | The audit is automated; the reading is manual or agent work | READ: 579 cards, 296 relics, 219 powers | Tested-but-unread went from 194 to 0. Relic reading found 3 of 58 diverged, with defects moved into shared machinery. Every divergence in E158-E185 was in a card that already had a test. | `audit_cards.py:104`; `HANDOFF.md:2728-2802` |
| 16 | Mechanical audits (`audit_enemy_moves`, `audit_ascension_literals`, `audit_card_keywords`, `audit_dead_card_cases`, `audit_shared_card_bodies`, `audit_effects`) | Decompiled source | Automated; each needs `decompiled/` | n/a | Enemy moves went from 36 flags to 0 (14 VERIFIED by digest), with about 6 defects per monster found in the hits batches. Ascension literals went from 80 flags to 0, covering 147 of 318 intent constructions. 163 dead labels. `audit_effects` first raised 31 card, 9 relic, 2 potion and 53 power flags, and found about 8 bugs (Exterminate, Bread, Orichalcum, Rupture and others). | `audit_enemy_moves.py:118-135`; `audit_effects.py:1-38`; `a33f846` |
| 17 | Coverage gates (`CardCoverageTests`, `CombatCoverageTests`, `EveryPoolEncounterBuildsTests`, event coverage, `RelicConstantTests`, `BlockChokepointTests`) | Registry scrapes and invariants | Automatic in `dotnet test` | n/a | Both Pending lists are empty. The gates found 2 unbuildable Hive encounters (E85), 4 wrong and 6 phantom relic constants, and 16 of 19 HP changes that had not dispatched their hooks. | `CombatCoverageTests.cs:51`; `HANDOFF.md:1608-1613, 1183-1194, 2833-2835` |
| 18 | Event RNG invariants (`EventMaskAgreesWithStepTests`, `EventRngStabilityTests`) | Invariant | Automatic | Every event, situation and option | Caught Colorful Philosophers rolling its stream on a read (E378) | `HANDOFF.md:964-973, 1099-1103` |
| 19 | Mutation checks on fixtures | The fixtures themselves | Manual | n/a | Hand order 4/4; play fixtures 4/4; an A10 corruption fails 3 `_a10_` tests and 0 `_a8_`; deleting `totalFloor` fails 5 | `HANDOFF.md:2303-2306, 2352-2354, 2429-2430, 2627-2629` |
| 20 | Numerical equivalence (PickBranch against `Next(n)`) | Arithmetic | One-off | 400,000 rolls | Agree on every roll that is not an exact integer | `HANDOFF.md:1822-1828` |
| 21 | Soak, smoke and watchdog (`soak_act_one`, `rl.run_train.smoke`, `CombatWatchdogTests`) | Invariants only: stalls, empty masks, crashes | Automated | Random or greedy policy over every encounter | The soak found E7. The A10 smoke completed 20/20. The watchdog requires every fight to end within 10,000 steps. | `scripts/soak_act_one.py`; `1d50acc` |
| 22 | Training quarantine as a crash soak | Invariants | Unattended | Every self-play job | After simbugs2, 80/80 quarantined seeds complete | `9821f46` |
| 23 | Feature-contract parity (live front end against the engine) | Replay over the 32 traces | Tests | 958 of 1,090 non-combat screens compared field by field | All 113 relic names and 14 event slugs matched; the potion-slot formula matched on 4,188 payloads | `DESIGN.md:1025-1056` |
| 24 | Fixture metadata guards | Capture metadata | Automatic | Every fixture | Checks the version stamp, a fully unlocked profile, and that no profile data is present | `tests/python/test_live_fixtures.py:73-124` |
| 25 | Patch-day pipeline (`patch_update.sh`, `patch_refresh.py`) | Decompiled source of the new build | Semi-automated | Run once, on v0.107.1 | Sorts failures into MECHANISM (7 named RNG and hash tests: do not re-baseline) and content. Never rewrites expectations from emulator output. `patch_refresh` runs only 2 of the audits its doc lists. | `scripts/patch_refresh.py:49-211` |
| 26 | Unit suites | Source citations and captures | `dotnet test`; `unittest discover` | C#: 4,244 `[Fact]`/`[Theory]` attributes (912 InlineData rows). Python: 1,147 test functions. spire-coach: 707. | Measured passing counts: C# 5,411 with 1 skipped (09-27), 5,546/5,546 (09-30); Python 1,340 with 3 failures judged pre-existing; spire-coach pytest 587 (09-27) | `702e745` report; r33hab commit 2026-09-30 |

### 4.3 The divergence catalogue

`docs/divergence-catalog.md` (2,993 lines) records 492 engine defects (E1-E493: E79 and E80
were never used, and E365 is used twice) and 23 harness defects (H1-H22). Its "Open" table is
empty. It was written by hand alongside each fix and has been frozen since 2026-09-07. No
r33hab-era finding is in it; those are recorded only in commit messages and spire-coach code.

By what exposed each table row, as one reader classified them:

| Exposed by | Rows |
|---|---|
| Full-run trace replay | 57 |
| Live combat sweep | 17 |
| Live encounter `-play` captures | 9 |
| Live event captures | 3 |
| Live card capture or capture tooling | 25 |
| Audit scripts | 23 |
| Source reading with no capture | 35 |
| Soak | 1 |
| Harness | 23 |
| Named only by the unit test that pins it (mostly the card burn-down E130-E426) | 279 |

### 4.4 Methods worth adopting

These rules are stated in the upstream docs:

- **Never fit the engine to a capture.** About 1,530 lines that forced HP, gold, rewards and even
  wins were deleted. 841 C# and 195 Python tests still passed afterwards, so nothing had covered
  that code (`AGENTS.md:384-406`; `8244eee`).
- **Expectations come from the source or from captures, never from emulator output.** Fixtures
  are regenerated only from game captures (`HANDOFF.md:2883-2894`).
- **Mutation-check every fixture** to prove it can detect a defect.
- **A burn-down list can only shrink by what was on it.** For every "N of M" headline, ask what
  is in M (`HANDOFF.md:1152-1155, 1226-1229`).
- **A test that reaches its subject through the subject's own constant cannot validate that
  constant** (`HANDOFF.md:1197-1205`).
- **Read the whole divergence list sorted by step.** The deck field often names the real cause
  dozens of steps before HP diverges (`HANDOFF.md:1028-1032`).
- **Use free oracles that need no game driving:** the profile's `saves/history/*.run` files,
  `godot.log` lines that print every rarity roll with its threshold, and the Neow screener.
- **Buff without rolling RNG** (`GainMaxHp`, not `SetHp`), so a buffed capture stays honest
  differential evidence (`HANDOFF.md:1444-1460`).
- **Use a known-divergence manifest that fails in both directions.** A fixed divergence must be
  removed from the manifest before the gate passes again (`check_run_traces.py:1-12, 35-55`).
- **Key reading notes to a digest of the source,** so they go stale when the game patches.

### 4.5 Planned but not built

| Item | Source | Status |
|---|---|---|
| `start_replay` mod action for deterministic re-capture | `docs/replay-verification.md:25-28`; `HANDOFF.md:549-550` | Not in the evangambit or r33hab mods. It exists only on Zamiell/STS2MCP's `replays` branch (a 1,740-line recorder and 867-line playback). `AGENTS.md:540-541` wrongly says it was added. |
| Per-step canonical state hash; per-character corpus layout (`corpus/<char>/<policy>/`); random, fuzz, human and bot policy corpora; a per-character "replay-exact %" metric as a CI merge gate; loop until dry | `docs/replay-verification.md:60-131` | Not built. What exists instead is a field-by-field comparison with a two-way manifest, in a flat, Ironclad-only fixture folder. |
| Settled-state guards on debug and menu actions (rapid abandon, re-embark and debug cycling crashes the game) | `HANDOFF.md:539-542`; mod `FORK_NOTES.md:56-60` | PLANNED |
| Coverage-gate membership set to every card in the game (E405) | `HANDOFF.md:1231-1234` | PLANNED |
| Card reward pools checked against a live capture | `HANDOFF.md:1957-1959` | Not done |
| RNG stream counters (`battle.rng`) in a published mod | catalog:139-146, 899-904 | ABANDONED. **Sources disagree:** one reader says evangambit's *local* mod reported them and card captures used them, but they never reached any published mod, and r33hab's mod deliberately reads no RNG. Two other readers describe the mod as exposing them. The capture fixtures do carry seed and counter. |
| Sibling audits (DefendIntent amounts, bare `MoveIndex` switches) | `HANDOFF.md:1727-1731` | Not done |
| Working CI | `ci.yml` | Red, or never run |
| Roadmap scale gates: B1 (90% or more comparable in every act), B4 (zero open audit flags), B5 (10,000 crash-free runs), B6 (zero deterministic mismatches in 10,000+ real A10 moves), C1 (zero run-replay differences on 20+ real full runs), C3 (real A10 runs replay exactly), D1 (update regression report with no manual steps), F2 (400+ real A10 runs) | roadmap:36-128 | None met, as far as the reports show |
| spire-coach stage-1 gates: a 300-position round trip, 20 sanity positions, advice within 2 s, reproduce the 0.092 death rate | design:288-297 | Not built or not reported |

---

## 5. The agent and learning work

Everything here is **Ironclad, simulator-only**. evangambit wrote the combat-agent core and
`FINDINGS.md` (2026-09-07..09). Everything run-level, the prior loop, the live search, the jobs
and the deck-decision work are r33hab's (2026-09-24..10-05).

### 5.1 Components

| Component | File(s) | Status | What it does |
|---|---|---|---|
| Determinized combat MCTS | `rl/combat_mcts.py` | DONE | Clone-per-simulation MCTS over one fight, with draw order and enemy RNG resampled every simulation (PIMC-style). c=0.1 on an HP-fraction scale, a tempo-weighted rollout, common random numbers over the first 20% of root simulations, an optional PUCT prior with lazy evaluation, and batched prior calls. It plays every fight in self-play, evaluation, the prior loop and the deck fights. **It never picks a target:** it always hits the first living enemy. |
| Combat transformer | `rl/combat_net.py`, `combat_tokens.py`, `train_combat.py` | DONE (policy head) / ABANDONED (value head at the leaf) | Token-sequence encoding; a categorical end-HP value head with death as its own class; a pointer policy head trained on visit counts. Only the policy head is used, as a PUCT prior. |
| PPO trainer | `rl/train.py` | ABANDONED | A placeholder that checks the env contract |
| Live search | `rl/live_search.py` | DONE | Wall-clock-budgeted, root-parallel MCTS on snapshot-loaded positions. Per-enemy targets; identical cards collapsed (checked by play); a minimum 200-simulation CRN sweep per root move; confirmation rounds on fresh seeds that give paired value and death gaps with standard errors. Value is HP, death is -100, and each potion is worth 10. |
| Run session | `rl/run_train/engine.py` | DONE | Plays whole runs, skips trivial screens and surfaces decisions as option lists. Searches fights on run clones, or on combat forks when a prior is used. Budget 120/500 (normal / elite and boss). |
| Rules baseline | `rl/run_train/rules.py` | DONE | Hand-written Ironclad rules for every non-combat screen. It is generation 0 and the fallback. |
| Feature contract | `features.py`, `vocab.py`, `shards.py` | DONE | Shared between the engine and live payloads: a 1,843-number base vector, a block X and an 8-number fight block H. A grep test checks that the hidden encounter and event sequences are never read. |
| FightNet | `rl/run_train/models.py` | DONE | An MLP (181,262 params) that predicts death or an HP-lost bucket (22 classes) from fight-start state. It is summarised over the region's encounter *pools* into H, never the actual next fight. |
| Run value net V and policy | `policy.py`, `models.RunValueNet` | DONE | An MLP (about 268k params) over each option's afterstate, predicting a distribution over the final floor (53 classes; a win counts as floor 53). The policy is a **one-step lookahead** on expected floors. There is no run-level tree search. |
| Generation loop | `loop.py`, `runner.py`, `evaluate.py`, `cli.py` | DONE | Generate, pair, train, evaluate, promote. Atomic phase files, quarantine, rollback, stale-evaluation re-checks, and export of each champion to the coach. |
| Fight-prior loop (stage 3) | `rl/prior_loop/` | DONE | AlphaZero-style rounds on recorded fight starts, with promotion gated on a frozen 2,000-fight set |
| Prior in self-play / in the coach | `prior_check.py`; `combat_prior.py`, `coach_check.py` | DONE / PARTIAL | Paired tests. The prior is on in the night job and off by default in the coach. |
| Budget test | `scripts/fight_budget_test.py` | DONE | Plain search against prior-guided or doubled-budget search on the 2,000 fixed fights |
| Deck decisions from measured fights | `rl/run_train/deckfights.py`; `scripts/deck_benchmark.py`, `deck_rollout_ab.py` | PARTIAL, no results yet | For deck-changing screens, plays the region's pool fights and the boss for each candidate on shared seeds and replaces FightNet's H with the measured one. Includes a 500-decision frozen benchmark and paired-fight training rows. |
| Diagnostics | `waste_probe.py`, `target_info.py`, `card_tags.py`, `export_fight.py` (HTML viewer), `mcts_probe.py`, `agent_probe.py`, `smoke.py`, `probe_throughput.py` | DONE | Probes and readers |
| Planned | DESIGN 2.7, 5.6; `ARCHITECTURE.md:100-113`; roadmap E4, E5 | PLANNED | The budget recheck (250/500 against 120/500), a final test on 500 held-out seeds, run-level search (expectimax with chance nodes, rollouts for pivotal picks), and other characters |

### 5.2 Measured results

| Result | Setting | n | Value | Evidence |
|---|---|---|---|---|
| Exploration constant 1.4 to 0.1 | A8, Overgrowth weak and normal fights, synthetic Ironclad decks, held-out seeds 400+ | 240 fights per setting | P(death) 0.183 to 0.092 | `rl/FINDINGS.md:17, 114-123` |
| Tempo rollout | Same | 64 fights | +3.8 HP, paired SE 1.1 | FINDINGS |
| Common random numbers | Same | 1,500 rollouts | 4.6x variance reduction | FINDINGS |
| Policy head as a PUCT prior | 60 simulations | 64 held-out fights | +2.0 HP (paired SE 0.9); P(death) 0.078 to 0.047 | `FINDINGS.md:548-559` |
| Value head at the leaf | 15/60/150 simulations | 64 fights | -10.6 / +0.5 / -0.8 HP; it never beat the rollout | `FINDINGS.md:147-169` |
| Run-level MCTS over random | Floor value | n/a | +1.7 floors at 40 simulations, +4.6 at 120 | `docs/agent-interface.md:308-311` |
| Rules baseline | A9 standing in for A10, 120/500 | 200 seeds | Mean floor 12.88 (95% CI 12.25-13.50); Act 1 boss kills 8.0% (Wilson 5.0-12.6%) | `DESIGN.md:556-576` |
| Act 1 strategy model | A9 for A10 | n/a | Boss kills 54% rising to 60-75% from generation 3; the roadmap quotes 68-74% | `29d4a94`; roadmap:32 |
| Full-run generation 0 (rules, eps 0.15) | A9 | 1,999 runs | 4.6% reached Act 2, 0 wins, mean floor 12.66 | `FULL_RUNS.md:105-112` |
| A10 smoke | Rules, eps 0 | 20 runs | All completed; 2 reached Act 2; 0 wins; mean floor 14.1 | `FULL_RUNS.md:138-141`; `1d50acc` |
| A10 buffed smoke | +250 max HP | 12 runs | 10 reached Act 2 and 6 Act 3; 0 wins; mean floor 37.8; one beat the first Act 3 boss | Same |
| Prior inside self-play | A10, 120/500, paired | 395 seeds | +0.81 floors (95% CI -0.21, +1.82); Act 1 boss kills 65.3% to 67.6%; 0.83x time per decision | `DESIGN.md:1946-1951` |
| A10 full-run champion | Real A10 | 1,000 eval seeds | Generation 40: mean floor 29.3. Learners in generations 41-80 scored 29.0-29.9; their successors, trained from learners, fell to 27.5-28.2 and were rolled back. | spire-coach `0c403b0`; `1359912` |
| Evaluation noise | 200 seeds | n/a | Paired CI about ±1.2 floors. Generations 9-17 scored 25.4-26.8 against a champion at 26.6 (a "lucky champion"), which moved promotion to 1,000 seeds. | `788df59` |
| Prior loop, rounds 2-7 | Gate set | 600 fights | +0.2 to +0.44 HP over the champion; CI lower bounds -0.07 to -0.32 | `rl/prior_loop/loop.py`; `7b4e5ce`, `f148b4d` |
| Prior, round 4 | 120/500 | 2,000 fights | Deaths 490 to 427; end HP +0.82 [+0.53, +1.11] at 1.3x time. Doubling the budget instead gave 455 deaths and +0.48 at 1.9x. | `71dd153` |
| Prior, 600-simulation loop, rounds 8 and 9 | 60 simulations | 2,000 fights | 456 and 452 deaths against 476 (p 0.024 and 0.007) | `c874c21` |
| Prior, round 9 against round 4 | 120/500 | 2,000 fights | 419 against 427 deaths (p 0.21) | `c874c21` |
| Prior at the coach's budget | About 40,000 simulations per move | 300 fight starts | First check: +0.07 HP (95% CI -0.61, +0.74), deaths 72 against 60. After fixes: +0.42 HP (95% CI -0.19, +1.03), deaths 56 against 50. 25 fights were lost only with the prior and 7 only without. | spire-coach `3977894`, `2cb5473` |
| Act 1 smoke throughput | A8, 120/500 | 57 seeds | 12.67 s per run; mean floor 15.04 | `smoke.py` |
| FightNet sensitivity | Live Smith screens | n/a | Options differ by only 0.04-0.5 floors; the model upgrades Strikes about as often as anything | deck-decision spec:20-24 |
| Deck decisions (benchmark, A/B, paired training) | n/a | n/a | **None reported.** The truth file is not committed and all 52 plan checkboxes are unchecked. | `deck_benchmark.json`; deck plan:1896-1900 |
| Real-game win rate | n/a | n/a | **None reported anywhere** | roadmap:101-112 |

### 5.3 Current strength

- **Simulator, A10, Ironclad:** about 29-30 mean floors on 1,000 eval seeds, a plateau at
  which runs typically end in Act 2. No win rate is reported, and the emulator's floor numbering
  may differ from the game's (section 3.6, UNVERIFIED).
- **Act 1 only:** the Act 1 strategy model beats the Act 1 boss 68-74% of the time in
  simulation.
- **Combat:** the learned prior helps at self-play budgets but not at the coach's budget, so the
  coach plays plain search by default.
- **Real game:** no measurement. The autopilot is debug-assisted by default (section 6.4), and
  from 2026-09-29 until the 10-05 fix it took 0 of 1,090 card rewards. The roadmap's goal is an Ironclad agent
  winning 85-90% of real A10 runs, and its proof step (F2) has not started.

### 5.4 Training setup

- **Seed sets** are disjoint: T for training, E for evaluation (1,000 since 2026-10-01), and F
  for the final test (500). The evaluation seed list's SHA is part of the staleness check.
- **Promotion.**
  - The challenger's 95% CI lower bound on V_W must be above the champion's mean, plus a
    boss-kill or win guard. It is decided on the value, not the floor (`29d4a94`).
  - One reader notes this compares a CI to a mean rather than pairing the two models, on a
    scale where a win counts as 53.
- **Generations** are 2,000 runs. Exploration uses tau_g = max(0.10, 0.60 x 0.85^g) and
  eps 0.02, with a bootstrapped target beta of 0.3. The data era resets when the budget, ascension or
  features change.
- **Learners** warm-start from the champion at lr 0.0005, because warm-starting from the latest
  learner regressed by about 1.5 floors (`1359912`). Self-play uses the latest learner, and the
  coach gets only the champion.
- **Workers** are spawned and niced, with one seed per private pipe. A failing seed is retried
  once, then quarantined; a timeout kills it. DESIGN 1.5.7 acknowledges that quarantine biases
  the data.
- **Prior loop.**
  - Labels come from 300- or 600-simulation searches on 10,000 recorded fight starts (70% from
    the full-run job), and the last 3 rounds are merged.
  - The net is a 2-layer, 128-wide transformer.
  - The frozen 2,000-fight gate set comes from the A9 job but is dealt at A10.
  - A round is promoted on an end-HP CI above 0, or on clearly fewer deaths (exact McNemar,
    p < 0.025), with neither measure worse.
- **Divergences from the written design.**
  - The night job turns the prior on by default (`PRIOR=1`), although DESIGN 6.5 says to keep
    it off until the +0.81-floor result is resolved.
  - A known `W_END_TURN` bug in the rollout is left in on purpose
    (`combat_mcts.py:434-435`).
- **Scale.** At least generation 89 by 2026-10-05: the benchmark draws from generations 84-89.
  That implies about 178,000 A10 runs (a reader's estimate, UNVERIFIED). One report says the job
  was at generation 83 (section 7.4).
- **Ironclad assumptions** are built in: the run engine's start, the rules tiers, and the card
  pool used for paired fights.

---

## 6. spire-coach

A local product of about 11k lines of source and 15k lines of tests (137 commits,
2026-09-23..10-05). Its README is stale: it still describes a combat-only, Act 1, Ironclad
coach. It has no CI.

### 6.1 Features

| Feature | Status | Notes | Evidence |
|---|---|---|---|
| Live combat coach | DONE | Polls the mod about 5 times a second. A position is accepted once the same settled fingerprint shows twice in a row. The engine analyses it (4 workers, 1.5 s). The panel shows the best move, the rest of the turn (cut at the first draw), up to 3 alternatives with their paired HP cost, expected HP loss and death risk. | `coach/live.py:1-45, 594-676` |
| Move grading | DONE | Section 6.2 | `coach/grader.py` |
| In-combat selection grading | DONE | Graded by diffing piles before and after, because the mod does not log selections. Ambiguous multi-picks are never graded. | `coach/grader.py:218-370` |
| Quiz mode | DONE | Hides the advice until your move from that position is graded | `coach/view.py:143-153` |
| Floating panel | DONE | pywebview or a browser tab. Binds 127.0.0.1 only, with a DNS-rebinding guard and a CSP with no external assets. | `coach/server.py:1-28` |
| One-step fidelity check on every graded human move | DONE | Writes `data/gaps/<ts>.json` and warns for 10 moves | `coach/live.py:825-912` |
| Version and engine-health gating | DONE | Advice is off unless the game is v0.107.1, the mod reports schema 4 and version 0.4, and the engine is healthy. There is an override button. | `coach/bridge/versions.py:17-67` |
| Engine client | DONE | An out-of-process JSON-lines service that restarts once and retries once | `coach/engine.py` |
| Capture mode | DONE | Records states and actions without the engine | `coach/capture.py:35` |
| Setup commands | DONE | `doctor` (9 checks), `mod install` / `mod enable`, and `saves backup` / `seed-modded` / `restore` (refused while the game runs) | `coach/cli.py:97-339` |
| Fidelity scoreboard | DONE | Section 4.2, row 12 | `coach/fidelity_scoreboard.py` |
| Dashboard (port 15531) | DONE | Read-only: training progress, learning curves, fight-learning loops, fidelity trend | `coach/dashboard.py` |
| Fight lab | DONE | Section 6.4 | `coach/fightlab.py` |
| Autopilot | PARTIAL | Section 6.4 | `coach/autopilot.py` |
| Combat prior switch | DONE | Off by default after the paired checks | `coach/cli.py:64-71` |
| Non-combat strategy advice | PARTIAL | Ranks options in expected final floors, with no interval and no grading. **Act 1 only**, because the coach uses the Act 1 champion (the autopilot uses the A10 one). | `coach/live.py:678-728`; `coach/engine.py:255-263` |
| Deck rollouts (`--deck-rollouts`) | PARTIAL | Built 2026-10-05; no results | `coach/cli.py:476-483` |
| Known draw-pile positions (spec 6.2) | PLANNED | `build_live_snapshot` accepts `known_top` / `known_bottom` but no caller passes them, so the engine knows *less* than the player | `coach/snapshot.py:839-840, 919-926` |
| Post-run review with 10x re-analysis | PLANNED | No review module exists | design:210-214 |
| Strategy grades; re-grading past runs | PLANNED | n/a | design:239-241, 303-306 |
| Rules-based non-combat policy; run manager | ABANDONED | Replaced by the learned model and a generic fallback | `coach-autopilot-review.md:70-121` |
| Design's autopilot safety model (stop on an unreliable analysis or a mismatch, pause on human takeover, profile 3, restore the time scale) | ABANDONED | The built autopilot recovers with fallbacks and debug actions instead | design:216-227 |
| Tests | DONE | 707 test functions against a scripted fake mod and a fake engine. No test touches the real game or the simulator. | `tests/fakes/` |

### 6.2 How grading works

1. Each human in-combat move from the mod's action log is matched, by `action_log_seq`, to the
   position it was made from. A position first seen after the log has moved on gets no seq and
   is never graded. Moves made by the API are never graded.
2. The engine searches the position. It then runs **50 fresh paired confirmation rounds**
   (`confirm_pairs 50`) on fresh seeds, separate from the search. Each round plays the best root
   move and each other move, both followed by the same tempo rollout policy.
   - Separate rounds avoid the winner's curse and tree-depth bias. Measuring through the search's
     own subtrees gave false gaps of 17.7 ± 3.4 HP between identical twin enemies
     (`rl/live_search.py:47-62`).
3. The grade uses the **lower bound of a one-sided 90% interval on the paired gap, in HP**:
   `diff - 1.645 x stderr`.

| Grade | Rule (on the lower bound) |
|---|---|
| Best | 0.5 HP or less, or the same move |
| Good | Under 2 HP |
| Inaccuracy | 2 to 5 HP |
| Mistake | 5 to 10 HP |
| Blunder | 10 HP or more, or a death-risk lower bound of 0.10 or more |
| Ungraded | `paired_n` under 20, a missing statistic, or no analysis |

A grade is marked "(unreliable)" when the converter flagged unmodelled content.

- **The value** is end HP plus 10 per potion held if the fight is won, and -100 if dead. A
  truncated rollout counts as a win at current HP (`rl/live_search.py:18-23, 136`).
- **Stated limits.** These gaps compare the best root move and your move, each followed by the
  rollout policy. They are not values under optimal continuation. Potions are a fixed 10 HP
  each, so setup lines and potion-saving lines are judged short-sightedly (`README.md:204-205`).
  No grade distributions or calibration are in the repo.
- **Budget.** 4 workers x 1.5 s gives about 40,000 simulations per move (the design estimated
  about 8,000), with a minimum of 200 simulations per root move.

### 6.3 Fairness boundary

- **The mod** hides three fields unless the conf flag *and* `?hidden=1` are both set. The coach
  client has no way to send `?hidden=1`, and a test checks that
  (`tests/test_bridge_client.py:64-79`).
- **The snapshot** is built from an allow-list (`build_live_snapshot`). It never reads
  `draw_pile_ordered`, the seed, RNG, pools, upcoming encounters or `move_follow_up_id`.
  - The draw pile becomes a multiset sorted on a total key, so no tie-break leaks order.
  - A sentinel test injects hidden fields and unknown keys at every level and asserts that none
    reach the output (`tests/test_snapshot.py:1224-1291`).
- **Every simulation** starts from a resampled world.
- **Three gaps:**
  1. Enemy `ai_fields` (monster instance fields read by reflection) and relic fields pass
     through.
  2. The non-combat strategy path sends the whole mod payload to the engine and relies on the
     engine reading only named fields (`coach/bridge/live_run.py:5-11, 61-78`).
  3. Known top-of-draw positions are not wired in.
- Run logs store the full mod payload.

### 6.4 Fight lab and autopilot specifics

Both need `allow_debug_actions` and modded profile 2. The spire-coach README says slot 3; the
code requires profile 2. Both use no LLM and no network, run at 3x speed, and check every move
against the emulator.

- **Fight lab.**
  - For each fight it embarks a fresh A10 run, calls `debug_enter_next_act` to reach the act,
    then `debug_start_encounter`.
  - It stages a deck sampled from self-play shards into the draw pile, and gives elites and
    bosses an HP-only buffer (500 by default).
  - The engine plays every move.
  - Encounters are ranked by the act with the fewest comparable checks, then elites and bosses
    first.
  - Until `d653e63`, a bug staged the decks into the master deck, so every "Act 2-3" fight ran
    on a starter-like deck.
- **Autopilot.**
  - Plays whole real runs: Ironclad, A10 by default, unseeded standard runs.
  - Fights use the engine's best move. Non-combat screens use the A10 full-run champion, and
    anything else falls back to taking the first option that is not a skip, then proceeding.
  - Safety caps: up to 5 failed starts, a 4,000-screen cap, and jam detection when the game is
    stuck for about 60 s. `--restart-on-jam` kills the game and relaunches it through Steam.
- **Debug assists in the autopilot.**
  - `--buffer-hp` defaults to 0.
  - **Auto-kill is on by default:** after 8 rounds with no new low in total enemy HP, it sends
    `debug_add_power STRENGTH 999`, then `debug_kill_enemy` as a last resort.
  - An ignored End Turn triggers `debug_force_play_phase`, then a kill.
  - These are logged as `debug` records, and the replay tools mark checks they taint.
- **Incidents** reported in commit bodies:
  - 0 of 1,090 card rewards taken from 2026-09-29 to 10-05 (`db6d486`).
  - A buffer that stacked to 110,080 max HP (`854bfb2`).
  - A Crystal Sphere stall of about 4 hours.
  - A forced kill of a reviving boss froze the game.
  - Earlier buffered runs reached floors 38-49.

### 6.5 Roadmap workstreams and status

The goal is an Ironclad agent that wins 85-90% of real A10 runs, measured on real runs. Every
task has an acceptance test, and a task counts as done only when its test passes
(roadmap:1-3, 36). For a real win rate, 100 runs give ±7-10 points and 400 runs give ±4-5.

| Id | Task | Acceptance | Status |
|---|---|---|---|
| A1 | Fidelity scoreboard | Reproduces the roadmap's current-standing table | DONE (`9929bc7`) |
| A2 | Capture what the checks need (power fields, seed, full screens) | No check is not-comparable for a missing field | PARTIAL (power fields `a335c82`, `4026ec4`; acceptance not shown) |
| A3 | Seed-exact run replay | Clean runs show zero differences | PARTIAL (959/959 on fixtures; 80/80 on one real run) |
| B1 | Make Acts 2-3 comparable | 90% or more comparable in every act | PARTIAL (8/69 and 48/129 at 09-27) |
| B2 | Remaining enemies and events (six buff- or chance-gated enemies with Test Subject first, Mysterious Knight, Decimillipede, The Architect) | Every enemy seen live is modelled and checked | PARTIAL (`80d37d4`, `0b83ff5`) |
| B3 | Known deviations (Sparkling Rouge, Swift, the buff table) | A regression test each | PARTIAL (`f4379e3`, `d662e45`) |
| B4 | Audit every card, relic, potion and power | Zero open flags | PARTIAL (flag counts not reported) |
| B5 | Segfault root cause | 10,000+ runs with no native crash | PARTIAL (`f70f8b7`; no 10k evidence) |
| B6 | Zero mismatches at scale | No deterministic mismatch in 10,000+ real A10 moves | PLANNED |
| C1-C4 | Run-level fidelity: every roll, every event, A1-A10 modifiers, act transitions | Zero A3 differences on 20+ real full runs; real A10 runs replay | PARTIAL (code merged in `ccc96fb` and others; acceptance not reported) |
| D1 | Game-update pipeline | No manual steps | PARTIAL (the evangambit-era `patch_refresh.py` exists) |
| E1 | Fight learning | Less HP lost and fewer deaths at the same budget | PARTIAL (it gains at self-play budgets, not at the coach's) |
| E2 | Fight net everywhere | Win rate up at equal compute | PARTIAL (off in the coach) |
| E3 | Full-run model to a plateau on 1,000 seeds | n/a | PARTIAL (plateau at 29-30 floors) |
| E4 | Bigger play-time search, hidden-information handling, run-level rollouts for pivotal picks | n/a | PLANNED (deck rollouts are a precursor) |
| E5 | Other characters and ascensions | Deferred until Ironclad at A10 is strong | PLANNED |
| F1 | Autopilot completes 20 real runs without getting stuck | n/a | PARTIAL (not demonstrated) |
| F2 | 400+ real A10 runs with a 95% CI and the sim-to-real gap | n/a | PLANNED (not started) |
| F3 | Capture flywheel: every autopilot run feeds A1, A3 and B6 | n/a | PARTIAL (the logs are in scoreboard format; volume not reported) |

Milestones:

- M1 (A1, A2, B1, B3, B5) and M2 (A3, C1-C4, B2, B4) were merged as branches, without acceptance
  reports.
- M3 (F1, F3, E2, E3) was in progress at the pin.
- M4 (F2, E4, B6, D1) has not started.

The roadmap estimates several weeks of agent work in total (roadmap:126-128). Out of scope for
now, per the design: other characters, multiplayer, an in-game overlay, LLM explanations,
Windows, and cloud training (design:342-350).

---

## 7. Stated next steps, open problems and branches

### 7.1 Stated next steps (newest first)

| Source | Next step | Notes |
|---|---|---|
| Deck-decision plan (10-05) | Report the champion's benchmark agreement (top-1, Spearman, value lost); run the measured-H A/B on 200 eval seeds and adopt it only if the paired CI on mean floor is above 0; report 3 generations trained with paired fights; then wire in whatever helps. The self-play switch waits for the A/B. | All 52 checkboxes unchecked (spec:104-118; plan:1896-1900) |
| Roadmap | Finish M3 (F1, F3, E2, E3), then M4 (F2, E4, B6, D1). Outstanding M2 acceptance work: C1, B2, B4. | roadmap:114-128 |
| `rl/run_train/DESIGN.md` | Budget recheck (250/500 against 120/500 on B0000-B0199); final test of the champion against rules on the 500 F-seeds; keep the prior off in self-play until a larger run resolves it | The night script already turns it on |
| `FULL_RUNS.md` | Verify Acts 2-3 against the real game; if learning stalls, let the Act 1 champion play generation 0; show option labels verbatim; have the dashboard read `win_rate` | The Acts 2-3 task file it points to is in no repo |
| spire-coach | Model Test Subject's AI, named as the most valuable next task; root-cause the Sparkling Rouge mismatch (since fixed in `f4379e3`); widen `strategyplay` to `sphere.cell` and `merchant.throw`; turn the prior on once it passes | Deleted report at `702e745`; `coach/strategyplay.py:34-43` |
| `rl/FINDINGS.md` "Open" | Retune the rollout weights and fix `W_END_TURN`; drop the end-turn probe; take the policy target from the UCT phase only; mix net and rollout at the leaf; fill card-taxonomy gaps; add targeting to search | Targeting was later done in `live_search` only |
| `docs/agent-interface.md` | Emit the action type alongside the index; locate the remaining combat-step compute | `:220-227, 384-387` |
| `docs/replay-verification.md` | `start_replay`, a per-character corpus, a per-step hash, a CI metric, loop until dry | Section 4.5 |
| HANDOFF / PLAN (evangambit era, partly superseded) | Settled-state guards; coverage-gate membership; extract `IsRemovable` and card tags; model pets; sweep synthetic relic ids above 100000; check card reward pools live; model the readers of `combat_card_selection` (Aggression, Improvement, Bookmark, Jewelled Mask, **Power Cell**, Drain); triage the 163 dead labels; find BuffIds applied but never read (Soar and Withering Presence are O19/O20); remove the five mutable statics; capture on new axes (act 2, events nobody has walked, fights nobody has lost yet) | Several are closed in code: enchantments, Mad Science/O17 (E448), Strangle and the missing-mechanic cards (one reader did not verify those implementations are correct), unread cards, relics |
| Mod | Harden abandon, re-embark and `debug_start_encounter` with settled-state guards | `FORK_NOTES.md:56-60` |

### 7.2 Open problems

| Area | Problem | Evidence |
|---|---|---|
| Measurement | No real-game win rate. Every strength number comes from simulator eval seeds. | roadmap:101-112 |
| Measurement | Autopilot runs are debug-assisted (auto-kill on by default, optional HP buffers), and from 2026-09-29 to 10-05 they took none of 1,090 card rewards, so they are not evidence of strength. They also exercised deck-dependent interactions only lightly. | `coach/autoplay.py:52-78`; `db6d486` |
| Measurement | Results are not in the repos (gitignored `runs/` and `data/`), so most numbers cannot be reproduced. The deck-decision results are missing. | Section 2.5 |
| Fidelity | The run layer is Ironclad-only; Defect fights only load from snapshots or tests | Section 3.6 |
| Fidelity | Committed oracles are almost all A8. A10 has 2 combat fixtures and 1 run history. DoubleBoss is derived from the source only. | Section 3.3 |
| Fidelity | Acts 2-3: low comparability at the last aggregate (8/69, 48/129); no act 2-3 full-run trace; sweeps on few seeds | roadmap:19; catalog:83-95 |
| Fidelity | The resample-based live check can hide a deterministic error behind a field that is random for another reason. The Sparkling Rouge miss looked like a random field, so the check did not flag it. | `f4379e3` |
| Fidelity | Profile dependence; content-mod sessions cannot be replayed; version pinned; card reward pools never checked live | Section 3.6 |
| Engine | Native crashes and loops are contained, not proven fixed. Throughput is 10x short of target. The engine is not thread-safe. Observation caps truncate. | Sections 3.5-3.6 |
| Engine | Determinization gap in run clones (UNVERIFIED); hidden sequences readable through the native API; the player-known top-of-draw prefix is not recorded | Section 3.6; catalog:2280-2333 |
| Learning | The strategy model plateaus and overfits at A10 (29-30 floors). FightNet barely separates deck changes. Prior gains shrink at real budgets. Self-play search never targets. `W_END_TURN` is left in. Promotion is not paired. Quarantine biases data. | Section 5 |
| Tooling | CI is red or absent. Audits need the gitignored decompile. The harness scripts 401 against r33hab's mod. There is no `battle.rng`. Defect counters are missing from the payload. There is no relic or potion staging and no save-state restore. | Sections 2.5, 3.7, 4.1 |
| Live game | Jams can only be cleared by a restart. `debug_kill_enemy` on a reviving boss froze the game. `debug_enter_next_act` sometimes silently does not take. `debug_start_encounter` with the map open reports `map` forever. GET can return 500 mid room-transition. Abandon wedges the menu without `current_run.save.backup`. `debug_add_card` returns "ok" even when the card lands out of reach. | `coach/autoplay.py:79-90, 662-667`; `McpMod.Debug.cs:372-384`; `coach/navigator.py:258-303`; mod `README.md:122-135` |
| Docs | Stale counts and versions; unresolvable SHAs; a missing SDD workspace | Sections 2.5-2.6 |

### 7.3 Branches and unmerged work

| Repo | Branches | Unmerged content |
|---|---|---|
| r33hab/sts2 | 25-27 depending on how they are counted (readers report 25, 26 and 27). They include `m1-*`, `m2-*`, `e2`, `stage3-prior`, `simbugs`, `simbugs2`, `gaps2`, `bosscheck`, `full-runs`, `act1-event-tests`, nine `spire-coach-*` and `main`. | None of substance. `full-runs` is ahead only by back-merges. `spire-coach-debug` is ahead by 2 commits, including `f7a894b`, the same SIGUSR1 fix that landed as `f70f8b7`. `act1-event-tests` keeps evangambit's SHA `d41d852` (0 ahead). The 194 "unmerged" `evan/main` commits are content-identical rewrites (the diff is empty). |
| r33hab/spire-coach | 14 | None: every branch is 0 ahead of `dev` |
| r33hab/STS2MCP | 6 | None |
| evangambit/sts2 | `main`, `act1-event-tests` (merged through PR #1) | A deleted `feature/play-cli` survives only as a merge |
| Zamiell/STS2MCP | 8 public branches, including `replays` (in-mod recorder and playback with `start_replay`), `debug-start-encounter`, `return-to-main-menu`, `fix-seeded-starts`, `skip-intro` | **`replays` was never merged** into the evangambit or r33hab mods. It is the only built `start_replay`. |
| cat12079801/STS2MCP | Includes `codex/...` and `copilot/...` agent branches | Merged into r33hab's mod as `cat/main` on 2026-09-23 (`5a423e2`) |
| Local only | n/a | evangambit's local mod with `battle.rng` was never published. Anything r33hab did after the 2026-10-05 publication is not visible. |

### 7.4 Where the sources disagree

| Topic | Values | Likely reason |
|---|---|---|
| Defect live captures | 86 of 88 (HANDOFF, `626b802`) against 88/88 (catalogue table) | The table counts Ignition as multiplayer-only and Scavenge as read |
| Cards played against the game | Catalogue table: Ironclad 29/85, Silent 21/86, 182 never played; a later catalogue line: 511 of 512 reachable | The table predates the later line |
| Relic coverage | HANDOFF: 171/296 modelled and 63 read; "107 of 296"; 122/122 reachable read. README: 250/296. Audit: 296/296. | Written on different dates; the code says 296/296 |
| Events | 58 ids plus 8 ancients (code); 65 of 68 (roadmap); 57 (README) | Different counting rules and dates |
| Hive/Glory combat | 10 of 33 diverged and 5 undrivable (`CombatCoverageTests` docstring) against 79/79 Hive and 72/72 Glory (catalogue) | The docstring predates fixes E427-E436 |
| A10 job progress | Generation 83 (one report, from `ab7eab0`) against at least generation 89 (benchmark ids) | Different dates on 10-05 |
| Test counts | C# 3,650 / 4,801 / 5,411 / 5,546; Python 492 / 527 / 1,340 | Measured at different dates; HANDOFF's are the oldest |
| `battle.rng` | Absent from every published mod (one reader) against exposed by the mod (two readers) | Captures came from evangambit's local mod |
| Headless boot / capture time | About 6 s or about 14 s; about 40 s or about 15 s per capture | Different notes |
| Roadmap A2/A3 | DONE (one reader) against PARTIAL (another) | The acceptance tests are not reported |
| Prior coach-check deaths, second check | Reported as 50 to 56, and as 56 against 50 | The same result: 56 deaths with the prior, 50 without |
| evangambit commit count | 467 (main) against about 660 | The higher count includes the rewritten duplicates |

---

## 8. What this means for Spireline

Spireline's plan: certify the best play at Ascension 10, Acts 1-3, Defect first; honest search
with hidden information resampled; no LLM components; an allow-list info-state firewall;
oracle labels with confidence sequences and a per-decision regret benchmark; coverage-guided
differential testing against a headless real engine; invariant fuzzing; Spire Codex run
replays; and an automated mismatch-to-fix loop.

### 8.1 Plan item by plan item

| Spireline plan item | What upstream already has | Verdict | Build on | Still needed in Spireline |
|---|---|---|---|---|
| **Certify best play at A10, Acts 1-3** | The engine models A0-A10, including DoubleBoss, and all three acts. Upstream reports floors and win chances, and grades moves against its own search. It never certifies a decision. | Engine: **partly covered**. Certification: **new**. | `Ascension.cs`, `RunEngine`, `DoubleBossTests` | Live A10 evidence in every act (today: 2 combat fixtures, 1 run history, uncommitted sessions); a live check of DoubleBoss; Acts 2-3 comparability; verdicts with units |
| **Defect first** | All 88 Defect cards implemented, tested and read first; 86 live-captured with 3 capture divergences; all 8 Defect relics hooked; the converter loads live Defect fights with 3 orb slots | Combat: **partly covered**. Run layer: **new**. | The snapshot loader, the `DefectFight` tests, the 86 card captures | A character parameter for `RunEngine.Reset` / `Sts2Run_Reset` / `reset_arena`; Defect's starter deck, relic, HP and reward, relic and potion pools; orb slots in `CombatFactory`; Defect run-level and live A10 captures; `lightning_orbs_channeled_this_combat` and the other missing counters from the mod; Genetic Algorithm's growth across fights |
| **Honest search, hidden information resampled** | `clone(resample_hidden=True)` reseeds every stream at the same call count and reshuffles the unknown middle of the draw pile. `combat_mcts` and `live_search` use it, with CRN and fresh-seed confirmation rounds. | Combat: **covered**. Run level: **partly covered**. | `combat_mcts.py`, `live_search.py`, `StateCloning.cs` | Resample the run clone's encounter and event sequences and the relic grab-bag order (the gap is UNVERIFIED; test it first); keep the native run state lists 11-13 out of every caller; record and pass known top and bottom draw positions; targeting in self-play search; run-level search instead of one-step lookahead |
| **No LLM components** | The runtime has none. The coach, fight lab and autopilot state that they use no Claude, no LLM and no network. The mod's MCP and LLM path is abandoned and cannot authenticate. | **Covered** (aligned) | n/a | Nothing to remove. Ignore the mod's `AGENTS.md`, which is an upstream LLM gameplay guide, not a convention file. |
| **Allow-list info-state firewall** | Two layers: the mod's hidden gate, and the coach's allow-list snapshot with a sentinel test. The client cannot send `?hidden=1`. Card uids are numbered so they do not leak draw order. | **Partly covered** | The sentinel-injection test pattern (close to Spireline's canaries); the mod's hidden gate; uid numbering | Upstream passes enemy `ai_fields` and relic fields, sends the whole payload on the non-combat path, and logs the full payload. Spireline's v0 (every allow-list empty, D10) is stricter. The engine side needs its own guard, because hidden sequences are readable natively. |
| **Oracle labels with confidence sequences** | Paired CRN confirmation rounds with a fixed-n one-sided 90% lower bound on the HP gap; Wilson intervals; exact McNemar; a fixed 2,000-fight gate; 1,000 evaluation seeds | Statistics: **partly covered**. Time-uniform sequences and labels: **new**. | The confirmation-round design (fresh seeds, no winner's curse); paired seeds; the gate-set idea | Anytime-valid confidence sequences; labels with units and verdicts. Upstream gaps assume a tempo-rollout continuation and fixed 10-HP potions, so they are not optimal-continuation values and should not be reused as labels. |
| **Per-decision regret benchmark** | `deck_benchmark`: 500 frozen deck decisions (generations 84-89) scored on top-1, Spearman and value lost against "truth", which is V on H measured over 8 seeds. The truth is not committed and there are no results. Combat grades are per move, but no benchmark exists. | **Partly covered** (one decision class, no results). Otherwise **new**. | The benchmark item format; `fight_budget_test`'s fixed sets | Regret against an oracle that respects the information set, for combat and run decisions; pre-registration; committed labels; units |
| **Coverage-guided differential testing against a headless real engine** | Differential sweeps against the **headless real game** (`capture_sweep` launches it; `combat_sweep` measures move coverage against `enemy_moves.py` denominators); coverage burn-downs; the fight lab targets the least-covered act | **Partly covered** | `combat_sweep`, `capture_sweep`, `capture_card` / `_event` / `_shop`, `enemy_moves.py`, `screen_neow_seeds.py` | Guidance by measured coverage rather than hand-picked seeds. Update the harness for r33hab's token and hidden gates (the scripts 401 today). There is no `battle.rng` in any published mod. Each capture costs about 15-40 s. The real game cannot be the simulator. |
| **Invariant fuzzing** | `soak_act_one`; `CombatWatchdogTests` (a random policy over every encounter, 10,000-step bound); event mask and RNG invariants; chokepoint grep tests; reflection-guarded cloning; the training quarantine as a crash soak; mutation checks | **Partly covered** | These tests and the quarantine files | Structured fuzzing of states and actions; determinization invariants (no upstream test asserts that run hidden state is resampled, or that resampling leaves visible state unchanged); parallel runs must be process-level |
| **Spire Codex run replays** | `replay_real_run.py` replays the run layer of recorded sessions seed-exactly from the game's history files (959/959; 80/80 on one A10 run), resolving fights with debug hooks. No report mentions Spire Codex. | Mechanism: **partly covered**. Corpus: **new**. | `replay_real_run.py`, HistoryReplayer, `commands.py` | An adapter from the export format; **Defect runs cannot replay until the run layer takes a character**. Upstream models one fully unlocked, all-discovered profile, but act selection and boss discovery depend on the profile, so public runs from other profiles may not match. Content-mod runs cannot be replayed. Event option order needs `decompiled/`. The Linux-vs-macOS Sapphire Seed difference is still open. See [SPIRE_CODEX.md](SPIRE_CODEX.md). |
| **Automated mismatch-to-fix loop** | Detection is automated: one-step checks write `data/gaps/`, the scoreboard categorises them, the fight lab targets the gaps, and quarantine feeds the simbug branches. Fixes are made by agent-driven sessions and merged by a controller. | Detection: **partly covered**. Closed loop: **new**. | The gap-file format, the scoreboard categories, the `KNOWN_DIVERGENCES` manifest, the patch-day split into MECHANISM and content | Automatic triage, a minimised repro, a regression fixture from the capture, and a gated fix. Keep upstream's rule: never re-baseline from emulator output. |

### 8.2 Reuse directly

- **The engine, combat content and RNG port, as pinned.** Every relic, potion and power and
  nearly every card is modelled, and 492 catalogued defects have been fixed.
- **The combat snapshot loader** (`Sts2_LoadCombatSnapshot`). Apart from the C# test builder,
  it is the only way to build a correct Defect fight today.
- **The live converter and the engine service's `check`,** as a starting point for Spireline's
  tape checks.
- **The verification apparatus:** `check_run_traces.py` (the two-way manifest),
  `replay_real_run.py`, `combat_sweep.py`, the capture scripts (after the token fix), the audit
  ledgers keyed by digest, `screen_neow_seeds.py`, the patch-day split into MECHANISM and
  content, and the free oracles (run-history files and `godot.log` rarity rolls).
- **The methods in section 4.4,** especially: never fit the engine to a capture, never take
  expectations from emulator output, and mutation-check every fixture.
- **The confirmation-round and CRN designs** from `live_search.py`. Measuring through the
  search's own subtrees gives false gaps.
- **Upstream baselines and probes as comparators,** all Ironclad: `rl/FINDINGS.md`'s paired
  P(death) protocol, the rules baseline and `fight_budget_test`.

### 8.3 Genuinely new in Spireline

- A Defect run layer: a character parameter, pools, starter state and orb slots. Upstream defers
  this (roadmap E5).
- Certified per-decision verdicts with units, time-uniform confidence sequences and a regret
  bound.
- A per-decision regret benchmark with pre-registered seeds and committed labels.
- Run-level hidden-information resampling, if the reported gap is confirmed, and an engine-side
  firewall around the native hidden lists.
- Coverage-*guided* selection of differential tests, and structured invariant fuzzing.
- A10 live evidence in every act, for Defect.
- The Spire Codex corpus as a run-layer replay and distribution test.
- A closed mismatch-to-fix loop.

### 8.4 Traps and cautions

- **Do not read upstream "real fights" as live-game fights.** In `rl/` they are simulated
  fight starts.
- **Do not use autopilot or fight-lab outcomes as strength evidence.** They are debug-assisted
  by default.
- **Upstream strength numbers are Ironclad,** mostly at A9 standing in for A10 or at real A10 in
  simulation. They will not transfer to Defect.
- **Defect capture count.** Spireline's README and D2/D12 say Defect is "88/88 captured". The
  upstream sources support 86 cards with live captures; the 88/88 figure counts Ignition as
  multiplayer-only and Scavenge as read (section 7.4). The claim that Defect is the
  best-verified pool still holds.
- **The emulator's floor numbers may not equal the game's** (UNVERIFIED). Check this before
  comparing floor-based figures with real runs.
- **Upstream docs are often stale.** Trust the code at the pin, the commit bodies, and the
  deleted reports at `702e745`, roughly in that order. Several cited SHAs do not resolve.
- **No upstream CI gate.** Run `dotnet test` and `unittest discover` locally after every
  native build. `lint-and-test.sh` covers only 4 Python files and is known to fail.
- **Cross-platform determinism is not established.** One run-history replay differs between
  linux-arm64 and macOS (Sapphire Seed). On Windows or WSL2, re-run the trace gate and the
  run-history replays before trusting labels.
- **Keep `decompiled/` and any game files out of the Spireline repo.** The upstream audits
  and some tests need them locally.
