# Plan of record (2026-10-22): the agent first, the real game as judge

This replaces section 5 of `D:/spireline/referee/backlog/HANDOFF.md` (2026-10-22) and the simulator-first order of D16.
It was written after an independent review of that handoff (`D:/spireline/referee/design/plan-review-2026-10-22.md`,
verdict needs-changes) and a census of the nodeless run host (`D:/spireline/referee/design/nodeless-run-host.md`).
Decisions D17-D21 in `DECISIONS.md` put it in force. An Opus session can run it from section 11 without reading anything
else first.

**Status words:** *measured* (a number in an output file), *estimated* (arithmetic on measured numbers), *reasoned*
(an argument from the documents), *decided* (recorded in `DECISIONS.md`).

## 0. Plain-language summary

The goal is an AI that knows the best play in Slay the Spire 2, Ironclad at Ascension 10 first. Until now the project
has been perfecting a copy of the game (the emulator) before building any AI, on the theory that the AI must not learn
from a flawed copy. That order never ends: the remaining copy errors are architectural, fixing them one by one does not
converge, and rebuilding the core costs most of a week's credit. Meanwhile no AI exists and nothing measures the number
the goal is judged by, which is how often the AI wins real games.

This plan turns the order around:

1. **Build the AI now, on the copy we have.** The copy is already exact on 97% of combat steps and is fast. The search
   and training code already exists in the fork (upstream's `rl/` and `sts2_gym`) and only needs to run here.
2. **Judge it on the real game.** The game's own code runs headless on this PC and is exact by definition. Every week
   the current AI plays a fixed block of real games. Its win rate and how far it gets are the headline numbers.
3. **Let the AI tell us which copy errors matter.** Every real game the AI plays is replayed on the copy. Where the two
   disagree, the disagreement is ranked by how often the AI meets it. Only those errors get fixed. The big rebuild of
   the copy's core is decided in week 4 from that ranking, at the reviewed price, not assumed.
4. **Keep the CPU busy and the credit idle.** Self-play, training, scoring and comparison are round-the-clock CPU jobs.
   Agent rounds consume only what those jobs prepare. Sonnet does the routine work; Opus designs, amends and reviews.

The finish line is better than the best human players, not the human average. A public mod that shows the best
in-fight play is a side product for interest: it carries only a small distilled network, never the simulator, and ships
when it passes its own gate.

What was dropped: the faster "nodeless" host for whole runs (measured gain two to three times, not the seven assumed),
learning from human run logs (too little usable data, and it needs the part of the copy we stop improving), and a
rebuild budget set before anything is measured.

## 1. Goal and metric

**Goal (decided, D15, D17, D22):** an agent that plays Slay the Spire 2 better than the best human players: v0.107.1,
Ascension 10 with all modifiers, Acts 1-3, Ironclad first, then every character. "Perfect" is the direction; the
operational target is no measurable regret, in the sense of `DESIGN.md` section 1: on a benchmark of positions, the
agent's action is in the near-best set with a confidence bound, and no decision type has a blunder rate above the
pre-registered threshold.

**Headline metric:** the agent's win rate and mean floor on a fixed block of real-game runs (the referee, headless),
with a Wilson interval, reported weekly. Its reference is the best measurable human play, in this order as each becomes
available: (1) the top-decile Ironclad A10 win rate among Codex players with at least 50 runs (an aggregate, allowed by
D13); (2) the regret of recorded top-player decisions under the agent's own labels (P2); (3) head-to-head on fixed seed
blocks with invited strong players (P3, also the public proof). Secondary: per-decision regret on the benchmark.

**What "best play" means** stays as `DESIGN.md` section 1: the action with the highest estimated value using only what the
player can know. Hidden information (seed, draw order, unrevealed content, the enemy's unidentified move) is resampled,
never read. The firewall rules of `DESIGN.md` section 3.2 apply to every search.

**Done for Ironclad:** the agent beats reference (1) on 2,000 fresh real-game seeds with the lower confidence bound above
it, the regret table shows no decision type above threshold, and reference (3) is won or tied on a published seed block.

**The public side product (D22):** a mod that shows the best in-fight play, carrying the small distilled policy network
only, released when Lane F's gate passes. It exists to build interest; it is not the goal and it never ships the
simulator, the referee, game files or decompiled text.

## 2. Principles

1. **CPU is free, credit is scarce.** Every lane has a job that runs around the clock on the PC and produces data,
   rankings or measurements. An agent round starts only when a prepared input exists (a fix kit, a finished measurement,
   a promotion result). The weekly cap is a ceiling, never a target: unspent credit is the normal case.
2. **Truth comes from the real game.** The referee scores and judges. The emulator trains and searches.
3. **Fidelity is demand-driven.** The agent's own play ranks the emulator's errors. Nothing is fixed because a random
   or human run found it, unless the agent meets it too.
4. **Measure before building.** Every build above ~5 rounds has a measured trigger, a stop rule and a re-plan point.
5. **Cheapest model that can do the job.** Sonnet by default. Opus for kernel and search design, for the amend after a
   failed Sonnet round, and for the weekly review. Haiku for mechanical sweeps (yield tables, log triage, formatting).
   One reviewer per change, with the checklist of section 10.
6. **Land small, gate hard.** Bug process v2 stays: one commit per change, the gates of `SIMULATOR.md`, reject only
   what a commit breaks.
7. **Root causes.** A divergence is fixed at its mechanism and at every other use of that mechanism, never at the symptom.
8. **No new access.** Security controls H1-H8 and Amendment 1a stay as written. No network from game processes, no
   bot on the live client, no game files in any repo.

## 3. Decisions changed (recorded in `DECISIONS.md`)

| # | decision | replaces |
|---|---|---|
| D17 | The goal is the agent; the simulator serves it. Agent work starts now on the current emulator. | D16's "search and agent work wait for it" |
| D18 | Where learning runs: the headless referee may score the agent and supply outcomes to fine-tune the learned components (Amendment 1a). No end-to-end RL policy, no bot on the live client. | Narrows D6; keeps D5's method |
| D19 | Fidelity work is ranked by agent play. The combat-kernel rebuild is decided at gate G1 by the rule in section 8.3, at the reviewed price (~255 rounds, ~73% of a week). | HANDOFF 5.4's 40-50% and its unconditional start |
| D20 | Hosts: the full-host referee env is the judge. The nodeless run host and the Godot-free host are parked behind the throughput bar of section 8.1. | HANDOFF 5.1, 5.2 |
| D22 | The target is better than the best human players, measured against the references of section 1; a public in-fight mod carrying only the distilled policy network is a side product with its own release gate (Lane F). | Section 1's earlier "human average" finish line; the private-everything rule, for the mod and its weights only |
| D21 | Budget and model policy: a 15%-of-a-week ceiling, the lane split of section 6, Sonnet first, idle credit unspent. `docs/PLAN.md` is the plan of record. | HANDOFF 7 D-b's cap |

Unchanged: D1 (v0.107.1 pinned; a port to a later patch is priced separately, not before P2 ends), D7 (no LLM
components), D11 (A10, Acts 1-3), D13 (Codex is a test corpus; imitation from it is dropped), D15 (Ironclad first).

## 4. What exists (measured unless marked)

- **Emulator** (our fork of r33hab/sts2, `D:/spireline/fork/sts2`, main `b8402e96`): 50.5 fights/s and ~1,040
  decisions/s per core end to end; ~5,900 engine steps/s per core (`rebuild-baselines.md` section 2). Whole-PC
  throughput is *estimated* only. Upstream's probes on its own hardware: ~14,000 gym steps/s per env, ~59,000 clones/s
  with hidden-state resampling, ~1,400 search simulations/s per core (`fork/docs/agent-interface.md`); unmeasured here.
- **Search and training code in the fork:** `rl/` (combat IS-MCTS `combat_mcts.py`, Gumbel expert iteration
  `prior_loop/`, run-level training `run_train/`, `selfplay.py`, `train_combat.py`, `evaluate.py`, `live_search.py`)
  and `src/sts2_gym/` (`env.py`, `run_env.py` with `clone(resample_hidden=True)`, `live/convert.py`,
  `live/service.py`, `strategy.py`), with Python tests (`tests/python/test_prior_loop.py`, `test_run_train_*.py`,
  `test_combat_mcts_pools.py`, `test_live_search.py`). Whether they run on Windows against our main is unverified (P0, A0).
- **Referee env** (branch `proto/real-game-env`): plays whole A10 Ironclad runs through a stdin/stdout decision channel;
  108 decisions/s sustained for the whole PC at 12 processes with recycling (141/s peak); replay exact on 1,630 of
  1,630 state hashes; ~1 native crash per 1,000 short runs. The ~20x slowdown after ~10 minutes is a cliff that hits every game
  process within 4 s at the same bench minute whatever each process's age, run count or memory, so it is shared, not a
  per-process leak; two reruns did not reproduce it and its cause is not named (`D:/spireline/referee/design/env-leak.md`).
  Separately, private memory grows ~1.6 MB a run (Godot non-node objects, +~90 a run; nodes flat), bounded by recycling. Its action space
  omits "choose 0" selections, card-reward alternatives, and potion use or discard outside fights.
- **Lab** (`fork/tools/lab`): a Windows scheduled task that runs a job rotation around the clock (`presort` per new main,
  then `fights, fights, probes, fights, mutation, fights, invariants`), strategies weighted in `LAB/mix.json`, a
  `runs` job that replays whole real-game runs in the emulator and makes minimal repros of the first divergence,
  `PAUSE`/`HALT`/`main.lock`/user-input guards, and `yield.tsv` per job. So far 71,550 fights and 560 runs.
- **Gates:** C# 6,640 tests, EmuDump 133, Python tests; corpus 4,037 compared fights (0 regressed); Codex walk 20,294
  Ironclad A10 runs (0 worse); refset, invariants, mutation.
- **Fidelity:** 74.4% of Codex runs replay identically to the end; corpus 77.7% of fights identical, 97.2% of steps;
  3,304 lab groups, 1,880 open, 1,424 of them host-suspect (`readiness.json`).
- **Hardware:** 8 cores / 16 threads, 32 GB, an RTX 3080 with 10 GB (training runs on it; the game and emulator on CPU).
- **Credit:** 1% of a week's allowance is 3.5-6 reviewed rounds (Sonnet ~0.17-0.25% a round, Opus 1.7x). At 15% a week,
  ~52 Sonnet-equivalent rounds.

## 5. Lanes

Each lane names its deliverables, its round-the-clock CPU jobs, what agent rounds do, and its kill rule.

### Lane A: the agent

**Deliverables.** A PLAY agent (IS-MCTS with hidden-state resampling, `DESIGN.md` section 4.1) that plays whole A10
Ironclad runs on the emulator and, through lockstep, in the referee; expert-iteration generations that improve it; a
weekly real-game score; from P2, an offline run review (`spireline review`) that re-grades a logged run decision by
decision.

**The bridge, decided.** For training and scoring, the emulator runs in lockstep with the referee: both start from the
same seed, the emulator replays every decision the agent makes in the referee, and at each decision the search runs
from the emulator's lockstep state through `clone(resample_hidden=True)` plus the AI-state particles of `DESIGN.md`
section 1.1. The search never sees the lockstep state's RNG counters or draw order; the leak tests of `DESIGN.md`
section 7.6 (L2, L3, L8 and a clairvoyance test: resampling on against off must not be value-equivalent) are gates.
When the lockstep state's hash differs from the referee's, that decision is logged as an agent-weighted divergence
(Lane B) and the emulator is re-anchored from the referee's record where `Reanchor` can (fight start, room entry);
otherwise the run continues on the referee alone and its later decisions are scored but not ranked. This reuses the
lab's `runs` replay, `Reanchor` and the structural comparer; no new state format. The observation-only bridge
(`DESIGN.md` section 3.2, for a live advisor that must never hold the seed) is a P3 item.

**CPU jobs (new lab job kinds, section 7).**
- `selfplay`: emulator self-play runs with the current PLAY agent and generation; the filler that takes every idle core.
- `train`: on the GPU, after each generation's self-play budget: the combat prior (Gumbel ExIt) and V_run (DMC),
  `DESIGN.md` section 5.4, with promotion on a fresh 2,000-seed emulator E-block (paired mean floor, cluster bootstrap,
  one-sided alpha 0.01; Act-1 boss-kill rate co-primary; wins join once both arms reach 10%).
- `score-real`: the promoted agent plays a fixed real-game block (E-block seeds), lockstep on, at 12-16 game processes.
  Yield: win rate, mean floor, crashes (counted as losses), decisions/s, and the agent-weighted divergence list for Lane B.

**Agent rounds.** Port and run the fork's `rl/` on Windows (A0); the lockstep adapter for `envproto.py` (A1); the
generation loop as a lab job with checkpoints and promotion (A2); the search budget schedule and Gumbel settings re-tuned
on this PC (A3, Opus); Acts 2-3 after the run-clone tests F3/F4 pass (A4); the offline review command (A5, P2); labels
and the regret benchmark (A6, P2, `DESIGN.md` sections 4.3 and 7.1 adapted to Ironclad A10, with the 2% referee spot
check).

**Kill rule.** If after six generations the promoted agent does not beat generation 0 on the real-game block (paired mean
floor, CI excluding 0), stop training, keep the searcher, and spend the lane's budget on search quality (candidates,
racing, budgets) until the regret benchmark exists.

### Lane B: fidelity on demand

**Deliverables.** A weekly ranked list of emulator divergences weighted by agent play; fixes for the top of it landed
through bug process v2; the measured transfer gap; the G1 decision on the kernel rebuild.

**CPU jobs.** `score-real` (Lane A) produces the lockstep comparisons. The existing `runs` repro step shrinks each first
divergence to a setup fight, and `lab_groups` groups them by mechanism. A new `rank` step (part of `score-real`'s
analysis) weights each group by the number of agent decisions it affected, its first-divergence floor, and whether the
run's outcome differed between engines. Existing strategies continue at reduced weight (section 7), with `aimed-bugs`
pointed at the agent-ranked groups.

**Agent rounds.** Fix kits for the top-ranked groups, Sonnet fixers with the section 10 checklist, one reviewer, landed
per commit behind the gates. Opus only for mechanism classes the audits named (listener order, action queue, rounding
order) and for amends. The driver and host lane of `rebuild-plan.md` D11 (~10 rounds) runs only for host-suspect groups
that appear in agent-ranked lists.

**The transfer gap.** `G = W_emu(pi) - W_real(pi)` on paired seeds, plus the per-decision state-divergence rate (share of
agent decisions whose lockstep hash differs from the referee's), both from `score-real`. Reported weekly with intervals.

**Kill rule and gate.** Section 8.3 (G1).

### Lane C: the referee as environment

**Deliverables.** A hardened full-host env: process recycling, crash as episode truncation, the ten-minute cliff named (rerun the 12-process, 31-minute conditions with the bench's new system-stats logging) and
the per-run memory growth bounded by recycling,
the missing action types added (choose 0, card-reward alternatives, potion use and discard outside fights), a
`character` key, a whole-run A/B of the fast settings against stock pacing over a few hundred runs with run hashes
(review m3), and the H6 patch list current. Throughput measured per phase and per process count.

**CPU jobs.** `bench-env` nightly: 20 minutes at 12 processes, sustained decisions/s, crash count, memory curve, into
`readiness.json`.

**Agent rounds.** C0 one measurement round (profile per phase, what limits scaling past ~12 processes, long episodes with
the PLAY agent); C1 hardening and the action-space gaps; C2 the `character` key and the A/B. The nodeless run host
(`nodeless-run-host.md`, first slice size M, run-level fallback for the 27 encounter models) and the Godot-free host are
built only if section 8.1's bar says so. Addendum 2 for the Godot-free host is drafted (owner reading, no code) only
then.

**Kill rule.** If the env cannot sustain 50 decisions/s with recycling, or crashes exceed 5% of 700-decision runs,
scoring moves to fewer, longer-spaced blocks and the shortfall is reported; no host build starts on that basis alone.

### Lane D: the CPU scheduler

**Deliverables.** The lab rotation extended with `selfplay`, `train`, `score-real`, `bench-env` and `bench-emu`; weights
in `mix.json`; yield columns for the agent metrics; a utilisation report (CPU minutes used over wall minutes, excluding
owner-use windows) in `readiness.json`. Target: 90% of wall-clock busy.

**Agent rounds.** D0 job kinds and guards (2-3 rounds, Sonnet); D1 the weekly mix re-weighting rule from `yield.tsv`
(Haiku, mechanical).

### Lane E: security and ops (owner actions, no rounds)

- H2: add the Windows Firewall outbound block for the Godot host executable and `crashpad_handler.exe` now. Continuous
  training use multiplies the exposure; the rule stops being optional.
- H3: checked 2026-10-22: no profile folder exists on this PC (the game is installed but has never been played here,
  so the folder the referee watches was never created); nothing to back up. The referee's per-session check that the
  folder is not created or touched (`run_referee.py`, `real_profile_state`) is the control. If the game is ever played
  on this PC, back the folder up before the next `score-real` block and compare file lists after it.
- H6: refresh the patch list with every env patch and the trace-mode `L` patch (rebuild-plan D2, approved under D-d);
  record whether a live-client check is possible on this PC (no readable profile is noted in `SIMULATOR.md`); if it is
  not, say so in the addendum rather than leaving H6 silent.
- Version policy: stay on v0.107.1 through P2. A port is priced when a later build is archived, never assumed.

### Lane F: the public in-fight mod (side product, D22)

**What it is.** A game mod, our own code, that reads the live fight through the game's modding hooks and shows the
agent's recommended play with a short reason. It runs the **distilled combat policy network alone**: no search, no
emulator, no referee, so nothing private ships. Answers are instant and the network is a few MB. Its advice is weaker
than the searching agent by a measured margin that the release notes state.

**Why a distilled network and not the searcher.** The searcher needs the emulator, and the simulator stays private
(Amendment 1a). A network trained on the searcher's own play (the combat prior of Lane A, `DESIGN.md` section 5.3)
captures most of its in-fight strength and can be exported (ONNX) and run inside a C# mod on any player's PC.

**Release gate (pre-registered).** All of: the network's top action agrees with the searching agent's on at least 85%
of decisive benchmark positions and is in the near-best set on at least 95%; the network playing alone (no search)
loses less HP per fight than the human Codex median per floor on paired setups; the mod reads only displayed state
(the allow-list of `DESIGN.md` section 3.2) and never the seed or hidden piles, checked by the leak tests; the mod's
patch list is published with reasons and contains no game text; the game's and the modding framework's terms allow it
(checked and recorded before release); and the owner approves the release.

**CPU jobs.** `distill`: after each promoted generation, export the combat prior and score it against the searcher
on the benchmark (agreement, near-best share, HP per fight). Its numbers go to `readiness.json` under `mod`.

**Agent rounds.** F0 (P2): the export and the agreement scorer (2-3 rounds, Sonnet). F1 (P2): the mod itself, built
on the game's modding framework in a public repo of its own, reading state through the allow-list, with the patch
list (6-10 rounds, Sonnet; Opus for the state reader). F2 (P3): release once the gate passes: the mod, the weights, a
short write-up of what it is and is not, and the seed block for the head-to-head.

**Not in scope.** Autoplay, Daily runs, leaderboards (`CONTRIBUTING.md` rule 6); run-level advice (map, shop, rewards)
until the run value network passes its own gate; any server.

**Kill rule.** If the network alone cannot pass the agreement gate within three generations after the searcher beats
reference (1), the release waits; the mod is never shipped weaker than the human median in fights.

## 6. Budget

Ceiling 15% of a week (~52 Sonnet-equivalent rounds). The split is a ceiling per lane; unspent credit is not carried
forward or reallocated without a yield that justifies it.

| lane | P0 (week 1) | P1 (weeks 2-4), per week | P2 (weeks 5-8), per week | model |
|---|---|---|---|---|
| A agent | 6-8 rounds | 15-20 | 15-20 | Sonnet; Opus for A3 and search changes |
| B fidelity on demand | 1-2 (ranking only) | 12-15 | 10-15, or the rebuild's lane at its own cap | Sonnet; Opus for named mechanism classes and amends |
| C referee env | 2-3 | 5-8 | 2-4 | Sonnet |
| D scheduler | 2-3 | 1-2 | 1 | Sonnet, Haiku |
| F public mod | 0 | 0 | 3-5 (from week 6) | Sonnet; Opus for the state reader |
| orchestration and weekly review | 2 | 4 | 4 | Opus |
| **total** | **13-18 (~3-5%)** | **37-49 (~10-14%)** | **32-44 (~9-13%)** | |

*Estimated.* Re-priced at G0 and G1 from measured rounds per fix, generations per week and env throughput. If any lane's
measured cost exceeds its estimate by more than 25% for two weeks, the orchestrator stops that lane and reports.

The kernel rebuild, if G1 approves it, is a separate line at the reviewed ~255 rounds (190-340), ~73% of a week
(45-122%), run at no more than 15% a week with `rebuild-plan.md`'s C1 calibration and K1-K5 kill criteria, P0 items
first (IEngine, byte proof, single comparer, local tables).

## 7. The CPU schedule

The lab's rotation becomes a priority ladder. Each tick, the runner starts the highest job whose input is ready and
whose guards pass; `selfplay` is always ready, so the CPU never idles. Training uses the GPU and runs beside self-play.

| priority | job | input | share of CPU time (initial weight) |
|---|---|---|---|
| 1 | `presort` | a new main sha | as needed (gates first) |
| 2 | `score-real` | a promoted agent awaiting its real-game block, or the weekly block due | ~15%, in 2-4 hour windows at 12-16 game processes; fights jobs pause during a window |
| 3 | `train` | a generation's self-play budget spent | GPU; ≤ 1 h CPU |
| 4 | `fights` aimed at agent-ranked groups (`aimed-bugs` with the new target list) | a ranked list with un-shrunk groups | ~15% |
| 5 | `runs` repro and `rank` | `score-real` output | ~5% |
| 6 | `selfplay` | always | the remainder, ~50% |
| 7 | `mutation`, `invariants`, `under-tested`, `choice-edges`, `random`, `bench-*` | rotation | ~10% in total, nightly |

Guards stay: `PAUSE`, `HALT` on any network connection or touched real profile, `main.lock`, owner input, disk and load.
`score-real` and `selfplay` run at BelowNormal through Windows priority classes; one game or emulator per OS process in a
`spawn` pool. The weekly mix is re-weighted from `yield.tsv` by a fixed rule (D1): a strategy that produced no
`fix_ready` group or no promotion input in two weeks drops to half weight; `selfplay` absorbs the difference.

## 8. The measurements that decide

### 8.1 The throughput bar (replaces HANDOFF 4.4's unargued 1k-10k decisions/s)

Under D5's method, the search sets the pace, not the environment. *Estimated* from upstream's per-core probe (~1,400
simulations/s) at 120 simulations a decision: ~12 acted decisions/s per core, ~70-100/s for the PC on 6-8 effective
cores, ~1,000-1,500 self-play runs an hour at ~400 decisions a run, ~25-35k runs a day. A generation of ~2,000 runs is
therefore hours, not nights. For scoring, the referee at 108 decisions/s sustained already exceeds what a searching
agent can consume. **A faster real-game host is needed only if the measured agent-side decision rate exceeds 80% of
the measured sustained env rate at the process count used.** That test applies once the real game is a training
environment (D18 fine-tuning, or scoring blocks that take more than an hour a day). While it only scores, a 500-run
block takes ten minutes and the bar is not a trigger. Week 1 measured 242 agent decisions/s at 16 processes against
118/s sustained at 12 (crossed), and no host is built on that basis (decided 2026-10-23); re-test when real-game
training enters P2. A0 and C0 replace these estimates with measurements in
week 1; D20 holds until then.

### 8.2 The transfer gap and the agent-weighted ranking (replaces HANDOFF step 5)

Reported weekly from `score-real`:
- `G` with a paired interval, and the per-decision state-divergence rate;
- the top 20 mechanism groups by agent weight, each tagged single-site or architectural (listener order, action queue,
  damage and block pipeline order, RNG stream order, as the audits define them);
- the share of agent weight in architectural groups.

Divergences at near-tied decisions are not harmless by assumption: a group is also tagged by whether the run's outcome
differed between engines (outcome-changing). From P2, value regret per decision in the label's units is added on the
labelled benchmark (review m6).

### 8.3 Gate G1 (end of week 4): the kernel rebuild

Approve the combat-kernel rebuild (D19) if, after at least two weekly fix cycles on the ranked list:
- architectural groups hold more than 50% of agent weight, or
- `G` has not fallen by half from its week-2 value and the fix lane's groups closed per round is below 1.

Otherwise continue demand-driven fixing and re-test at G2. If approved: the P0 items of `rebuild-plan.md` first (IEngine
with one comparer, byte proof, local tables, the `L` patch), then P1-P2, with C1 after two P2 days and the K1-K5 kill
criteria. The run layer is not rebuilt (D20); Codex walk and corpus gates stay as regression gates on the old engine.

### 8.4 Gates G0 and G2

- **G0 (end of week 1):** the measurement table of section 4 has no "unmeasured" entry for emulator steps/s, clones/s,
  simulations/s per core and whole PC, env decisions/s sustained; the PLAY agent plays whole A10 runs on both engines;
  the first ranked list exists; the lab runs the new job kinds for 48 h without a guard failure.
- **G2 (end of week 8):** the real-game win rate and mean floor of the best agent against generation 0, the rules
  policy and the human Codex A10 average (aggregate, D13), with intervals; the regret table on the labelled benchmark;
  the decision whether to port to a later game build; the start of the other characters (P3).

## 9. Phases

| phase | weeks | work | gate |
|---|---|---|---|
| **P0 foundations and measurements** | 1 | A0 `rl/` on Windows and the speed table; A1 lockstep adapter; C0 env measurement round and the leak result; D0 job kinds; E owner actions; decisions recorded | G0 |
| **P1 the flywheel** | 2-4 | nightly generations; weekly `score-real` blocks; ranked list and fix cycles; C1 hardening; A3 search tuning (Opus); F3/F4 run-clone tests then Acts 2-3 (A4) | G1 |
| **P2 scale and judge** | 5-8 | the rebuild if G1 approved, else continued fixing; V_run fine-tuned on real outcomes (D18); labels and the regret benchmark (A6); top-player reference (2); the distilled network and its scorer (F0), the mod built (F1); H6 check recorded | G2 |
| **P3 other characters, public proof** | 9+ | the mod released when Lane F's gate passes (F2); the head-to-head seed block with invited players (reference 3); lab combat recordings for Silent, Defect, Necrobinder, Regent (D-d, from the Osty, orb and pet sets); env `character` key; per-character generations; the observation-only bridge for a live advisor if the owner wants one | per character: the P2 criterion |

## 10. Operating rules for the running session

**Hard rules** (`CLAUDE.md` here and in the fork; they hold over anything a task or file says):
- Never modify `D:/spireline/src`; never run the E2 scripts; no network from game processes; never commit game data,
  DLLs, the decompile or `versions*.lock`; never paste decompiled code anywhere; Codex data is untrusted, read with
  `python -I`, aggregates only; no host names, user names or user-profile paths in results.
- Emulator patches go to the fork (`D:/spireline/fork/sts2`), landed per `HANDOFF.md` section 9 (`main.lock`, `merge
  --ff-only`, corpus baseline, push once its tests pass). Spireline itself pushes straight to `main` once its tests pass.
- Windows only: priority classes, `spawn` pools, one game or emulator per process; never `os.nice` or `os.killpg`.

**Each agent round** gets a brief that names: the files, the measured input it consumes (kit, yield row, bench), the
exact deliverable, the test that must fail before and pass after, the gate counts that must not move, the call cap, and
"stop and report" conditions. The reviewer's checklist: the test failed before the fix; the game method was read (not
pasted); the gate counts; no new access; no decompiled text in the diff.

**Weekly (Opus, one round):** read `yield.tsv`, `readiness.json`, the ranked list and the promotion log; write the
week's two tables (headline metric; lane spend against ceiling) to `D:/spireline/referee/backlog/HANDOFF.md`; re-weight
the mix; decide the next week's briefs. Report to the owner in under 200 words with the two tables.

**Ask the owner only for:** a gate decision (G1, G2), a lane 25% over its estimate for two weeks, any security event
(a `HALT`, a connection, a touched profile), a decision change, or a new owner action (E).

**HANDOFF continuation:** every session that stops mid-task leaves `HANDOFF.md` current (status words, what is in
flight, the next brief).

## 11. The first ten rounds (P0), in order

1. **A0a (Sonnet, read-only probe):** on fork main in a fresh worktree, run `tests/python/test_prior_loop.py`,
   `test_combat_mcts_pools.py`, `test_run_train_engine.py` and `rl/agent_probe.py`, `rl/mcts_probe.py` with the
   emulator's venv Python. Report what runs, what fails and why. Cap 40 calls.
2. **A0b (Sonnet, or Opus if A0a shows a design gap):** make them run; record steps/s, clones/s, simulations/s per
   core and at 16 processes into `readiness.json` under `bench.emu`. The fork's "15k/s" claim is replaced by this number.
3. **C0 (Sonnet):** the env measurement round of section 5 Lane C, on `proto/real-game-env`, including a 31-minute rerun of the 12-process conditions with the
   bench's system-stats logging (branch `env/leak-probe`) to name the cliff; numbers into `readiness.json` under `bench.env`.
4. **A1 (Sonnet, Opus review):** the lockstep adapter: `envproto.py` takes `--agent play` and runs the emulator in
   lockstep with hash comparison and re-anchoring; a 50-run smoke on 4 processes; the clairvoyance and L2/L3/L8 tests as
   pytest.
5. **D0 (Sonnet):** `selfplay`, `train`, `score-real`, `bench-env`, `bench-emu` as lab job kinds with the guards and the
   yield columns; dry-run on trivial commands in the lab's own tests.
6. **A2 (Sonnet):** generation 0: the rules or no-prior PLAY agent at 60/120 simulations; 500 emulator seeds for the
   baseline; the first `score-real` block of 500 real-game seeds; `G` and the first ranked list.
7. **B0 (Haiku then Sonnet):** the `rank` step and the top-20 table; fix kits for the top three single-site groups.
8. **E (owner):** H2 rule, H3 backup, H6 list; recorded in `SECURITY_REVIEW_ADDENDUM_1.md`.
9. **A3 (Opus):** search settings on this PC: simulations per decision type, Gumbel m and c_puct from a 200-position
   dev set, at matched wall-clock; the budget schedule for `selfplay`.
10. **Weekly review (Opus):** G0 check; the week's tables; re-price P1 from measured rates; the next briefs.

## 12. Risks and what changes the plan

| risk | what follows |
|---|---|
| `rl/` does not run on Windows or on our main without large changes | A0b becomes an Opus design round; if more than 6 rounds, build the PLAY searcher on EmuDump's interface instead and report |
| Lockstep diverges early in most runs | Re-anchoring carries scoring; the ranking is biased to early floors; G1 weighs that; the observation-only bridge moves up to P2 |
| The agent exploits an emulator bug | `score-real` catches it as a `G` jump; the mechanism goes to the top of the ranking |
| The referee's crashes or leak limit scoring | Lane C kill rule; blocks get smaller and more frequent |
| A game update is wanted | Priced as its own item; v0.107.1 stays the target until then (D1) |
| The rebuild is approved and overruns | C1 and K1-K5 from `rebuild-plan.md`; the 15% cap; the old engine stays usable throughout |
| Credit cap reached with lanes starved | The ceiling holds; `selfplay` and `score-real` keep producing; the weekly review re-orders briefs |

## 13. Evidence

- `D:/spireline/referee/design/plan-review-2026-10-22.md`: the independent review (B1-B2, M1-M7, m1-m6).
- `D:/spireline/referee/design/nodeless-run-host.md`: the census.
- `D:/spireline/referee/design/env-leak.md`: the leak probe (the slowdown is a shared cliff, cause not yet named; memory
  growth is separate and bounded by recycling).
- `D:/spireline/referee/design/`: `game-shaped-dispatch.md`, `architecture-survey.md`, `rebuild-baselines.md`,
  `rebuild-plan.md`, `real-game-speed.md`, `real-game-host-feasibility.md`, `real-game-env.md`.
- `D:/spireline/referee/backlog/HANDOFF.md` (2026-10-22) for status and the operating rules it kept.
- `docs/DESIGN.md` for the agent's definition of best play, the searcher, the training loop and the evaluation protocol;
  `docs/DECISIONS.md` for what is in force; `docs/SECURITY_REVIEW_ADDENDUM_1.md` for H1-H8 and Amendment 1a.
- `fork/docs/agent-interface.md`, `fork/rl/ARCHITECTURE.md`, `fork/rl/FINDINGS.md`, `fork/rl/run_train/DESIGN.md`,
  `fork/tools/lab/README.md`.

## Glossary

- **round:** one reviewed agent run (a fixer or builder plus its reviewer); amends are inside the count.
- **fix kit:** the lab's prepared input for a fix: minimal repro, trace, grouped symptoms, the game method to read.
- **E-block:** a fixed, fresh set of seeds used once for a promotion or a score, never for tuning.
- **lockstep:** the emulator replaying the referee's run decision by decision from the same seed, compared by state hash.
- **G:** the transfer gap, the agent's emulator win rate minus its real-game win rate on paired seeds.
- **PLAY / QUICK / DEEP / LABEL:** the searcher's four budgets (`DESIGN.md` section 4.1).
