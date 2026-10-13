# Spireline: a framework for finding the best play in Slay the Spire 2

> **Status (2026-10-12).** This is design v1.1 from 10 October 2026, published unchanged apart from removing personal details. Several decisions have changed since. Where this document disagrees with [DECISIONS.md](DECISIONS.md), DECISIONS.md wins.
>
> - **Target: Ascension 10 only, Acts 1–3, Defect first** (D11, D12). Where this document says A0, Track D at A0, or "Act 1 first", read A10 and Acts 1–3.
> - **No LLM components** (D14). Section 6 (LLM roles, Jev, Haiku, experiment E1) and the LLM baselines B4/B5 are void. Jev stays relevant only as part of the landscape critique.
> - **The always-on worker is a native Windows PC**, not WSL2. See [pc-setup/WINDOWS.md](../pc-setup/WINDOWS.md). Throughput figures for the owner's machines here are estimates, not measurements.
> - **The security review is done and published** as [SECURITY_REVIEW.md](SECURITY_REVIEW.md): GO WITH CONDITIONS. It replaces §3.6's "this is not a security review" note. It confirmed the run-level resampling leak (resampled run clones keep the pre-rolled encounters, events and relic order), so run-level labels stay gated (its condition E13; leak tests L2 and L3 here).
> - **The upstream emulator models the A10 double boss** (merged 2026-09-28). Most of its live-game captures were taken at A8, so A10 fidelity is still to be verified.
> - **The Spire Codex v0.107.1 export is the run-layer test corpus** (D13): 56,137 vanilla A10 single-player runs, 11,350 of them Defect. See [research/SPIRE_CODEX.md](research/SPIRE_CODEX.md).
> - Further research: [LANDSCAPE.md](research/LANDSCAPE.md) (critique of existing StS bots and agents), [UPSTREAM.md](research/UPSTREAM.md) (what the upstream emulator project already does), [ENEMY_AI.md](research/ENEMY_AI.md), [COMPUTE.md](research/COMPUTE.md), [IDEAS.md](research/IDEAS.md) (unverified efficiency ideas) and the raw [dossiers](research/dossiers/).


**Final design, v1.1 (revised after adversarial review) · 2026-10-10 · pinned to StS2 v0.107.1 (Steam build 23811903), r33hab/sts2 `b745217`, r33hab/STS2MCP `5a63f92`**

*Working name: **Spireline**. A "line" is a sequence of moves, as in chess. The system's job is to find the best line from what the player can see. Code: this repository, with its own Python venv.*

---

## Executive summary

Spireline answers "what is the best play here?" for Slay the Spire 2. **Best play** means the action with the highest estimated value, using only what the player can know. The ideal value is the probability of winning the run. The run seed, RNG state, draw order, the enemy's move behind a non-identifying intent, and unrevealed future content are kept out by an allow-list firewall.

**How it estimates best play.**
- It does not write its own simulator. The live game is read through an MIT-licensed mod, built from source after a code review.
- Each position is converted into the **r33hab/sts2 emulator** (MIT, C# NativeAOT, targets v0.107.1). On the author's Apple M4 Max it measured about 58–72 µs per step, about 0.4–0.7 ms per search simulation, and a clone with **built-in resampling of hidden state** (`clone(resample_hidden=True)`) ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md), [ARCHITECTURE](https://github.com/r33hab/sts2/blob/spire-coach/rl/ARCHITECTURE.md)). Speed on the owner's Mac has not been measured.
- Every candidate action is scored on the same set of sampled worlds (common random numbers, CRN). A declared continuation policy finishes play from each world.
- Every answer comes with:
  - the recommended action;
  - its value, **labelled with its unit**;
  - a confidence interval that stays valid however many times it is checked (a time-uniform confidence sequence);
  - an upper bound on regret, valid for the candidates that survived screening;
  - a verdict: DECISIVE, CLOSE, UNCERTAIN or UNSUPPORTED.

**Units are explicit.**
- Phase 1 combat labels are in **L0 points**, a combat-local utility. They are **not** P(win).
- Act-level labels are in pp of P(clear act).
- A label is reported in pp of P(win) only after two conditions hold: the reference policy wins at least 10% of runs, and the run-value model beats a base-rate model on Brier skill.

**Trust in the foundation is not assumed.**
- Three repos underpin the design: the emulator, the mod fork and spire-coach. All three were created by one account within 9 seconds on 2026-10-05. They have 0 stars and no GitHub fork lineage, and spire-coach has no licence ([GitHub API](https://api.github.com/repos/r33hab/sts2)).
- Week 1 therefore starts with a code review, sandboxed builds and a documented fallback: evangambit/sts2 plus the cicero225 STS2MCP fork.

**Benchmark character, decided now.**
- **Track D (Defect, A0)** is the primary benchmark (SpireBench) and the oracle/RL target. Defect's card pool is 88/88 captured against the live game.
- **Track I (Ironclad, Act 1)** is limited to positions whose cards are all captured. It exists for the comparators that are Ironclad-only (FableBot, spire-coach) and for live advice.

**Where RL fits.** RL appears in three places:
- the definition of the target (Q over information sets);
- policy improvement by search;
- two learned components that make search cheaper and longer-sighted.

It is not an end-to-end policy.

**Where Jev fits.** Jev and other cheap LLMs are optional root priors and baselines, kept behind a pre-registered kill-switch experiment.

**What the owner gets, and when.**
- **Week 1–2:** spire-coach, an existing free tool. After review, it gives a live combat advisor for v0.107.1 Ironclad Act 1 ([README](https://github.com/r33hab/spire-coach)).
- **By week 5:** Spireline's first deliverable of its own, a `spireline review` report that re-grades the owner's logged fights.
- **Phase 2:** a macro advisor.
- **Throughout:** an oracle-labelled benchmark that measures **per-decision regret**, which no StS2 project has measured to date.

**Budget.**
- About 120–170 hours of the owner's time to the end of Phase 3.
- Under about $150 in compute and API spend to the end of Phase 3, and under about $300 including Phase 4.
- About 60–170 hours of dedicated live-game Mac time in Phase 3.

### How does RL fit?

Best play is defined as the RL quantity `argmax_a Q*(I, a)`: win probability over the player's information set I.

**The oracle.** It is Monte Carlo evaluation of `Q^π_ref(I, a)`. This gives one-step policy improvement over a declared reference policy (SPARTA-style, [arXiv 1912.02318](https://arxiv.org/abs/1912.02318)). A second, structurally different reference policy is used to detect continuation bias.

**The learned parts.**
- A combat policy prior, trained by **Gumbel Expert Iteration** ([Anthony et al.](https://arxiv.org/abs/1705.08439), [Danihelka et al.](https://iclr.cc/virtual/2022/poster/6418)).
- An afterstate run value **V_run**, learned by Deep Monte Carlo regression on emulator self-play ([DouZero](https://arxiv.org/abs/2106.06135), [Suphx](https://arxiv.org/abs/2003.13590)). It starts as the Act-1 head (18 classes). The 53-class full-run head is trained only once the emulator's Act 2–3 map and encounter fidelity checks pass (F3/F4).

V_run is the long-horizon credit assignment that no StS2 project has solved.

**Rejected: end-to-end PPO or GRPO.**
- On StS1, Slay_RL reached 15.43% after 3.55B decisions ([handoff](https://github.com/DavidSnoble/Slay_RL/blob/master/docs/schema_v4_handoff.md)). That is below the 20% Bottled AI gets with search plus rules.
- Spirebird's latest 10,000 StS2 training runs had 0 wins ([engine-stats](https://spirebird.com/engine-stats.html)).

### How do Jev and cheap compute fit?

Jev is **cheap hosted inference, not compute**.
- Closed weights, cannot be fine-tuned, non-deterministic, in early access ([docs](https://docs.typesafe.ai/models)).
- About $0.00046 per factored decision at p50 315 ms, with a 7–16 s slow mode.
- Its headline benchmark (27/30 vs 29/30, Fisher p ≈ 0.61) measures a first-action string match on 10 fixtures. Its own grader says it is "not optimality or win probability" ([suite.mjs](https://github.com/shoemoney/jev-the-spire2/blob/main/spire-demo/benchmark/suite.mjs)).
- End-to-end results: upstream won 1 of 182 runs; the fork won 0 of 9.

The cheap compute that matters is the owner's Mac running the emulator. It should reach an estimated 5,000–8,000 simulations per second across 6 workers. That is extrapolated from M4 Max measurements and is measured on day 4.

Jev, and Claude Haiku 5.5 as the Claude-native default, may serve only as:
- a **root prior** that search can overrule;
- a soft blunder feature;
- an explainer;
- a **baseline whose regret we measure**.

They are never an oracle, never inside the search tree, and never a hard dependency.

Experiment E1 decides whether they stay. It is a pre-registered test at matched wall-clock and dollar cost, costing about $2–5. A provisional verdict comes in Phase 2, against uniform and heuristic priors. A final verdict comes in Phase 3, against the learned net prior, if that exists.

---

## What we're stealing, what we're rejecting

| Project | Steal | Reject | Why |
|---|---|---|---|
| **r33hab/sts2** emulator (MIT) at `b745217` (2026-10-05, default branch `spire-coach`) | NativeAOT emulator<br>`clone(resample_hidden=True)`<br>`combat_mcts.py` settings (c≈0.1, CRN, tempo rollout)<br>`combat_tokens` encoder<br>`rl/prior_loop` (ExIt)<br>`rl/run_train` (V_run 18/53-class heads, FightNet, `deckfights.py` paired fight signal)<br>`sts2_gym.live.convert` + `CombatSnapshot.cs`<br>engine service (`analyze`/`check`/`strategy`)<br>capture and sweep tooling | Trusting it unreviewed; maintaining a private fork of its internals | Only engine with cheap clone plus information-respecting resampling ([agent-interface](https://github.com/r33hab/sts2/blob/spire-coach/docs/agent-interface.md)). All of these files are present at `b745217`; none has been run by us.<br>Provenance: 730 commits, 467 attributed to evangambit ([contributors API](https://api.github.com/repos/r33hab/sts2/contributors)). But evangambit's head `37e4264` is absent and `fork:false`, so the history was rewritten and a tree diff is needed (§3.6).<br>Test counts conflict inside the repo: [FINDINGS](https://github.com/r33hab/sts2/blob/spire-coach/rl/FINDINGS.md) says C# 4801/4801 and Python 526/527; [HANDOFF](https://github.com/r33hab/sts2/blob/spire-coach/HANDOFF.md) says 3,650 (+1 skipped) and 492 (+6 skipped). |
| **r33hab/spire-coach** (no licence; created 2026-10-05; default branch `dev`) | After review, run as-is in Phase 0 as the owner's live combat advisor and quiz. Also baseline B3 (HP-valued search) | Its installer commands (`mod install`, `mod enable`, `saves seed-modded`); copying or redistributing its code; its HP currency as the definition of "best" | All rights reserved, so local use only. Verified scope from its [README](https://github.com/r33hab/spire-coach): v0.107.1, Ironclad, Act 1, combat only.<br>Value = end HP + 10 HP per held potion, −100 for death. Defaults: 4 workers, 1.5 s per position. Show/quiz modes. |
| **r33hab/STS2MCP** `spire-coach` branch (MIT; payload schema 4; head `5a63f92`) | Live bridge, chosen because the converter expects it.<br>Listener binds only `localhost`/`127.0.0.1` and needs an API token ([McpMod.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.cs)).<br>`set_time_scale` keeps its speed through hit-stops ([McpMod.TimeScale.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.TimeScale.cs)).<br>Custom-run seeded embark ([McpMod.CustomRun.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.CustomRun.cs)) | Its **default payload taken at face value**; any `?hidden=1` read; upstream Gennadiyev main / v0.4.0 | Schema 4 adds enemy `move_id`, AI history (`state_log`) and every primitive AI field (`ai_fields`) to the **default** payload ([McpMod.StateExtras.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.StateExtras.cs)). Behind a non-identifying intent, these can carry hidden information, so they pass an allow-list (§3.2).<br>Upstream fails on v0.111 ([#131](https://github.com/Gennadiyev/STS2MCP/issues/131)) and its `/compendium` exposes the seed ([Compendium.cs](https://github.com/Gennadiyev/STS2MCP/blob/main/McpMod.Compendium.cs)). |
| **evangambit/sts2** (MIT; created 2026-08-15, last push 2026-09-10) + **cicero225/STS2MCP** fork | Documented **fallback substrate** if the review of r33hab code fails | n/a | Older, publicly developed upstream of the same lineage ([FINDINGS](https://github.com/evangambit/sts2/blob/main/rl/FINDINGS.md), [cicero225](https://github.com/cicero225/STS2MCP)) |
| **STS2FableBot** (MIT) | **The bar to beat on Track I**: 71/343 = 20.7% (Wilson 16.7–25.3%) at A0 Ironclad on v0.107.1.<br>Also: pure-function policies with config hash, the watchdog pattern, "arriving healthy" as the first value proxy | Its hand-built Python board model as a simulator; comparing it with Track D | Strongest honest StS2 result. Same build, but Ironclad only ([README](https://github.com/cicero225/STS2FableBot)) |
| **Bottled AI** (MIT, StS1) | Turn enumeration plus a hand-written end-of-turn evaluator: baseline **B8** and the second reference policy | Its UI-speed runtime | Strongest honest StS1 method (20–52% at A0) ([winrates](https://github.com/xaved88/bottled_ai/blob/main/docs/winrates.md)). Comes almost free from `candidates.py`. |
| **evangambit / r33hab `rl/FINDINGS.md`** | c = 1.4 → 0.1 halves P(death) (0.183 → 0.092, 240 fights each)<br>CRN gives 4.6x variance reduction<br>The value head never beat rollouts<br>Prior gives +2.0 HP under visit selection (+0.6 under mean selection, 64 paired fights) | Argmax-mean move selection under a prior | Measured, paired evidence ([FINDINGS](https://github.com/r33hab/sts2/blob/spire-coach/rl/FINDINGS.md)) |
| **mingxuan-he/sts2-agent** fork of sts2-cli | Real-engine referee for Acts 2–3 (Phase 3); 200/40 seed-pool discipline; action-attempt logging; bug write-ups (Gardener, Kaiser Crab) | Its GRPO track; using it as the search engine | No in-combat clone; about 20 steps/s per process on Windows ([Zaaacqwq](https://github.com/Zaaacqwq/SlayTheSpireRL/blob/main/plan/timeline.md)); its training loop never ran |
| **jev-the-spire2** (MIT) | Factored-question pattern; the "waste/self-harm" noul as a *soft* feature (the only config with 0/9 trap failures) | The harness, its fixture benchmark, any veto role | Benchmark tuned on its test set; 0/9 live ([SWEEP](https://github.com/shoemoney/jev-the-spire2/blob/main/SWEEP-FINDINGS.md)) |
| **AgenticSTS** (Apache-2.0 code, CC-BY data) | Bounded typed context (~5k tokens); Wilson/Fisher scripts; the finding that defeats cluster on boss floors (136/202 on floors 17/33/48) | Using it as a decision-maker or oracle | Pinned to v0.103 and Silent; skill effect p ≈ 0.37 ([arXiv 2607.02255](https://arxiv.org/abs/2607.02255)) |
| **JoeB08 bot** | Damage per floor as a leading indicator; decision-snapshot replay for refactor checks | 15–20-run A/B sets | CIs of about ±20 pp ([repo](https://github.com/JoeB08/Slay-the-Spire-2-Automatic-Bot)) |
| **Spire Codex** export (630,765 v0.107.1 runs) | Optional cold-start, the currency-stability check and the real-data RNG correlation check (F9), *if its terms allow* | Replays carrying `draw_order` / `rng_state` unless scrubbed; using it as ground truth | Licence NOASSERTION; uploaders are self-selected (22.0% at A0 vs Mega Crit's 16%) |
| sts_lightspeed ScumSearch, scumthespire | Clairvoyant value as a value-of-perfect-information diagnostic only | Any clairvoyant teacher | Distilling such teachers plateaued at 0.44 accuracy ([sts-rl-agent](https://huggingface.co/Jialeiv/sts-rl-agent)) |
| CharTyr/STS2-Agent, Communication_Mod_STS2, HKUDS bridge, zhiyue / Akirakato / StS2Sim sims | Nothing; CharTyr's legal-action contract is noted as a good pattern | All | AGPL and heavy; or no licence and leaks draw order; or stale; or unvalidated |
| Writing our own simulator | n/a | Rejected | METR found subtle rule bugs in a Claude-built StS clone ([note](https://evals.alignment.org/notes/2026-03-03-balatro-sts-cli/)) |

### What changed from the three candidate designs

The base is the search-first design, which the judges scored 22.5. The table shows how each flaw the judges found is fixed in v1.1.

| Judge-flagged flaw | Fix in Spireline |
|---|---|
| Ironclad is the least-verified character (29/85 cards captured live; Silent 21/86) | The benchmark character is decided now: **Track D = Defect (88/88)** for SpireBench, oracle and RL. **Track I = Ironclad Act 1**, restricted to fully captured cards, for the Ironclad-only comparators |
| Phase-2 gate "emulator A0 ≥ 20.7%" unsupported (r33hab gen 0: 0/1,999 at A9, 95.4% Act-1 deaths) | All gates are relative and paired against internal baselines. The cross-character 20.7% stretch goal is dropped |
| User-facing value arrives last | Phase 0 runs spire-coach after review. Week 5 ships `spireline review`. Phase 2 adds the macro advisor |
| Week 1 holds about 3 weeks of work | Week 1 is about 16–20 h of review, setup, measurement and leak tests, with no new search code. Spill into week 2 is planned |
| Redundant adapter; mod fork mismatch | Use r33hab/STS2MCP `spire-coach` with `sts2_gym.live.convert`, behind our own allow-list firewall; no private emulator fork |
| Circular leak test; seed-swap test as specified is infeasible | Non-circular variety tests (L2/L3/L8), a positive control, canary tokens, and seed-swap via snapshot import |
| Argmax-mean final move under a prior | Gumbel + Sequential Halving with completed-Q targets during play; fresh-world, equal-n estimation in labels |
| Sim-to-real parity accepted on "no significant gap" | TOST equivalence, ±5 pp margin, paired same-seed runs, deterministic search |
| "Matched compute" counted in simulations | Matched wall-clock *and* dollars, LLM latency included |
| E1 run before the macro benchmark exists | The E1 verdict needs Tier A and Tier B. It is provisional in P2 and final in P3 |
| Oracle-trained parts graded only by the oracle | They must also win paired batteries on fresh seed blocks and pass the "too good to be true" audit (F7) |
| Monster AI internal state copied into clones | Allow-list firewall, a likelihood-weighted particle belief over AI state and the current move, and leak tests L7/L8 |
| Shadow emulator holding the true seed | Rejected; positions are imported from visible state only |
| Unclustered bootstrap | Cluster bootstrap by fight and by run |

---

## 1. Definition of "best play"

### 1.1 Model

Single-player StS2 is a POMDP against nature, with no adversary. Hidden information comes almost entirely from chance:
- draw order;
- RNG-driven enemy moves;
- random effects;
- unrevealed rewards and encounters.

The true state s includes the run seed σ and every RNG stream's call counter. The game is deterministic given σ and the action sequence: sts2-agent measured byte-identical states 31 decisions deep ([sts2-agent](https://github.com/mingxuan-he/sts2-agent)).

**Information state.** `I_t = canon(o_0, a_0, …, o_t)` is the canonicalised history of what the player saw.

| Visible: may enter I | Hidden: must never enter I, features, prompts, or an un-resampled clone |
|---|---|
| HP, max HP, block, energy, stars, gold, potions, relics with counters, master deck | Run seed and RNG counters, **even though the game shows the seed** (the mod sends a seed only on the game-over screen, [StateBuilder](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.StateBuilder.cs)) |
| Draw, discard and exhaust piles as **multisets**; known top/bottom cards (`KnownTopCount`/`KnownBottomCount`) | Draw order outside known regions; `draw_pile_ordered`; any ordered-pile debug output |
| Enemy HP, block, powers. Current intent as displayed: exact damage × hits for attacks, the category (and any number the UI shows) otherwise. Moves already executed in this fight | **The enemy's current move id when the displayed intent does not identify it uniquely**; `move_follow_up_id` (the next move); AI fields not deducible from the observed history |
| Act map node types; act boss; shop, reward, event and Ancient options once on screen; encounters already served (`map.encounters_seen`) | Which encounter sits behind each node; reward contents, shop stock, event outcomes and Ancient offers before they are shown |

Whether the game's intent tooltip names the specific move behind a Buff, Debuff or Unknown intent is **UNVERIFIED**. Leak test L8 (§7.6) settles it per monster by comparing the mod's displayed intent `label`/`description` with move ids. A move id that the displayed intent identifies uniquely counts as visible.

**Knowledge convention.** Expert knowledge of the rules is allowed: monster move tables, reward odds, card text. Exploiting RNG structure is not.
- v0.107.1 replaced .NET System.Random with xoshiro256** ([Steam notes](https://store.steampowered.com/news/app/2868840/view/1835871199305790)). The cross-stream correlations documented for v0.107.0 ([tck.mn](https://tck.mn/blog/correlated-randomness-sts2/)) should therefore be gone.
- We do **not** rely on the patch note. Check F9 (§3.3) tests the documented correlations on emulator seeds and on real v0.107.1 runs.
- Whatever F9 finds, the belief uses nominal distributions. If F9 finds dependence, labels are reported as "what a player who doesn't exploit RNG correlations should do", and the deviation is recorded.
- Banned: mods such as "Real Draw Pile Order", the `/compendium` seed field, any `?hidden=1` read, and the Spire Codex replay fields `draw_order` and `rng_state`.

**Belief b(s | I).**
- The unknown region of the draw pile is a uniform permutation.
- Every RNG stream whose output has not been observed is replaced with a fresh, independent stream.
- Generated but unseen content (encounters behind nodes, rewards, shop stock, event outcomes) is redrawn from its generator.
- **Monster AI state and current move: likelihood-weighted particles.**
  - Forward-simulate each monster's AI from combat start with fresh `MonsterAi` streams.
  - Keep the particles that reproduce the observed move history and the current displayed intent (category, damage, hits).
  - Weight each survivor by prior × likelihood. This is the posterior; sampling uniformly among consistent states would bias intent forecasts when moves are probabilistic.
  - If no particle survives within K = 4,096 tries, the state comes from a deterministic reconstruction that uses history only (§3.2). The position is flagged `ai_state_assumed`.

In code, a sample from b is `clone(resample_hidden=True)` followed by the AI-particle draw. The emulator's run-clone docstring says the clone resamples "the rewards, shop stock and encounter compositions still to come" ([run_env.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/run_env.py)). Two points are **UNVERIFIED** until tested:
- Whether the clone actually redraws content materialised at act start, such as `NormalEncounterSequence`. Tested by L2/L3.
- Whether the clone re-rolls an enemy's already-chosen current move. Tested by L8; the expectation is that it does not, and needs a patch.

**These tests block every macro label (L2/L3) and every gold combat label (L7/L8) until they pass.**

**Target.** Let W = 1 if the run is won (Act 3 boss beaten; both bosses at A10).
- `V*(I) = sup_π E_{s~b(I)}[W | π]` over policies that read only information states.
- `Q*(I, a)` is the same after taking a.
- **Best play** = `argmax_a Q*(I, a)`.
- The **ε-best set** is `A*_ε = {a : Q*(a) ≥ max Q* − ε}`. Every action in it counts as correct.
- **Regret** is `r(a) = max_b Q(b) − Q(a)`, always reported in the label's own units.

### 1.2 What the system certifies

Q* cannot be computed. Each label is an estimate under declared assumptions:

```
Q̂_{π_ref, H, L}(I, a) = mean over worlds w_j ~ b(I) of  u_L( state at horizon H )
                        after executing a in w_j, then continuing with π_ref
```

**Continuation rule.** π_ref decides from *its own* information state, never from w_j's hidden state. Every continuation decision re-clones its current state with `resample_hidden=True`. The world only decides what happens. Under this rule, a label is a one-step policy improvement over a non-clairvoyant π_ref: no worse than π_ref, up to rollout error ([SPARTA](https://arxiv.org/abs/1912.02318)).

**Value ladder.** Each label uses one currency, and its level and unit are always printed. Different levels are never mixed in one backup ([ARCHITECTURE](https://github.com/evangambit/sts2/blob/main/rl/ARCHITECTURE.md)).

| Level | u_L at the horizon | Unit printed | Used when |
|---|---|---|---|
| **L0**, combat-local | 0 if dead, else `0.5 + 0.5·min(1, (HP_end + 10·potions_held)/maxHP)`. This combines AlphaStS's win-first shape ([AlphaStS](https://github.com/MANGO1234/AlphaStS)) with spire-coach's 10 HP per potion | **L0 points** (1 point = 0.01 of u_L0). Never "pp of P(win)" | Phase 1, before V_run exists. Potion-heavy positions (≥ 2 potions held, or a potion among the candidates) are tagged `currency_sensitive`, because a flat 10 HP misprices strong potions |
| **L1**, act-level | P(clear the current act's boss \| state), from act rollouts or FightNet-chained estimates | pp of P(clear act) | Phase 2 macro labels inside an act; **Act 1 only** until F3/F4 pass |
| **L2**, run-level | `V_run(state)`. While π_ref's win rate is below 10%, `U_λ = p_won + λ·E[floor]/53` with λ = 0.1, annealed to 0. U_λ keeps every win above every loss (1.0 > 0.1·52/53) | "U_λ units" while π_ref < 10% wins; **pp of P(win) only after** π_ref ≥ 10% and V_run passes the Brier-skill gate (§5.3) | Below 10% wins, L2 best play effectively means "reach more floors", and the reports say so |

**Error sources, reported separately.**
1. **Monte Carlo error** goes into the confidence sequence.
2. **Continuation bias.** `Q^π_ref ≤ Q*`, and a stronger π_ref could reorder actions. Two checks:
   - within the policy family: the same argmax under π_ref@60 and @300, and across ExIt generations;
   - **across families**: a 200-position stratified subset is relabelled under a structurally different π_ref (B8: Bottled-style turn enumerator with a static evaluator and rules macro). Positions where the two disagree are tagged `continuation_sensitive` and excluded from top-1 metrics.
3. **Model error** (emulator fidelity, V_run bias, AI-belief assumptions) is tracked by `fidelity_flags`, `ai_state_assumed` and a currency-stability check. It is never folded into the CI.

### 1.3 Per decision type

| Decision | Candidate unit | Chance after the action | Horizon / level | Notes |
|---|---|---|---|---|
| **Combat** (card × target, potion use/discard, in-combat card select, end turn) | **Information-boundary macro-action**: a deterministic play sequence that stops at end turn or at the first action that reveals hidden information (draw, scry, random target or effect, card generation, random-outcome potion) | Draws, random targets and effects, enemy rolls | End of combat → L0; later V_run (L1/L2) | Recommend the line's first atomic action, then re-plan after every observation. This removes within-turn strategy fusion at the root ([Long et al.](https://ojs.aaai.org/index.php/AAAI/article/view/7562)). Lethal and fatal-end-turn checks are done in code |
| **Card reward / skip** | Afterstates (deck + card, or skip) | None (deterministic afterstate) | Act boss → L1 (Act 1); L2 later | About 26 per winning run (from local run files). Paired upcoming fights via CRN, as in [Zelnia](https://project-archive.inf.ed.ac.uk/ug4/20233951/ug4_proj.pdf) and r33hab [`deckfights.py`](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/deckfights.py) |
| **Map step** | Next reachable node, chosen by enumerating full paths | `?` room contents; encounter identity | Act boss → L1; L2 later | Expectimax with explicit chance nodes (ADVISE/LABEL only) |
| **Shop** | Affordable bundles (cards, relics, potions, removal) plus "leave", pruned to ≤ 32 | Inner choice of removal target | Act boss → L1 | |
| **Rest site** | Rest / smith(k) for each k / other | None | Act boss → L1 | |
| **Event** (multi-page) | Each page option | Event RNG | Act end → L1 | Unmodelled event → UNSUPPORTED |
| **Relic, boss relic, Ancient, Neow** | Offered options | Some (random relic) | End of next act → L1 chained / L2 | Rare and high-stakes: always gold-tier Monte Carlo in LABEL mode |
| **Card select out of combat** (remove, transform, upgrade, enchant) | Deck cards | Transform outcome | Act boss → L1 | |

### 1.4 Output contract (every decision, live or offline)

```json
{
  "decision_id": "run-7f3a:f12:card_reward", "game_build": 23811903,
  "engine_sha": "b745217+patches@3", "oracle_cfg": "sha256:…", "info_state_hash": "9b2d…",
  "track": "D", "mode": "LABEL-B-gold",
  "value_level": "L1", "value_units": "pp P(clear act 1)",
  "options": [
    {"a": "Take <card A>", "q": 61.2, "cs95": [59.4, 63.0], "n_worlds": 620},
    {"a": "Take <card B>", "q": 58.9, "cs95": [57.2, 60.6], "n_worlds": 620},
    {"a": "Skip",          "q": null, "cs95": null,          "n_worlds": 0, "pruned_at": "screen:V_run+deckfights"}],
  "best": "Take <card A>", "p_best": 0.95,
  "gap": 2.3, "gap_cs95": [0.4, 4.2], "ci_method": "empirical-Bernstein CS (time-uniform)",
  "epsilon": 2.0, "verdict": "DECISIVE",
  "regret_ucb95_if_follow": 0.0, "regret_bound_scope": "survivors_only", "screen_recall_dev": 0.985,
  "pi_ref": "playlite@gen0 (combat 60/300, macro V_run-greedy)", "horizon": "act_boss",
  "stability": {"pi_ref_60_vs_300": "same_argmax", "second_family_B8": "same_argmax"},
  "continuation_sensitive": false, "currency_sensitive": false,
  "vpi_clairvoyant": 6.1, "ai_state": "particles(k=64)",
  "fidelity_flags": [], "prior": {"source": "none"}, "wall_s": 4120, "usd": 0.0
}
```

**Field rules.**
- **Precision** is defined one way only: the **half-width of the 95% confidence interval** on the paired gap.
- **CIs are time-uniform confidence sequences**, not fixed-n intervals that are checked repeatedly. Two forms are used:
  - empirical-Bernstein CS for bounded paired differences ([Howard et al. 2021, arXiv 1810.08240](https://arxiv.org/abs/1810.08240));
  - betting CS for [0,1] outcomes ([Waudby-Smith & Ramdas, arXiv 2010.09686](https://arxiv.org/abs/2010.09686)).

  `stats.py` unit-tests their coverage by simulation, requiring ≥ 95% under optional stopping.
- **Cross-fitting.** One set of CRN worlds selects the survivors; a disjoint fresh set estimates them. This avoids winner's-curse bias.
- **`p_best`** is a bootstrap over the paired fresh worlds.
- **`regret_ucb95`** = `max(0, max_{b ∈ survivors, b≠â} UCB(b) − LCB(â))`, Bonferroni-corrected across survivors.
  - It is a bound **conditional on the survivor set**. Screening may use a cheaper continuation than estimation, so a pruned candidate carries no valid bound and is listed as `pruned_at`.
  - `screen_recall_dev` reports how often, on 200 dev positions, the full-estimation argmax survived screening (§4.1). The pre-registered requirement is ≥ 98%.
- **Verdict.** ε depends on mode and level:

  | Mode | Quantity | ε |
  |---|---|---|
  | QUICK combat | Q^{tempo}, L0 | 1.0 L0 point |
  | DEEP combat (opt-in) | Q^{PLAY@16}, L0 | 1.0 L0 point |
  | Silver label | Q^{PLAY@60}, L0 | 1.0 L0 point |
  | Gold label | Q^{PLAY@300}, L0 | 0.5 L0 point |
  | QUICK macro | V_run + paired deck fights, L1 | 2 pp P(clear act) |
  | Tier B gold | act rollouts, L1 | 2 pp P(clear act) |
  | L2 (when allowed) | P(win) | 1 pp |

  - **DECISIVE**: LCB(gap) > 0 and point gap ≥ ε.
  - **CLOSE**: the gap CS lies inside [−ε, +ε]. This is an equivalence statement: "either action; regret ≤ ε with 95% confidence".
  - **UNCERTAIN**: the budget ran out first.
  - **UNSUPPORTED**: any of the following, and the answer is still shown, marked unverified:
    - any card, relic, power, enemy or event is unimplemented, catalogued as divergent, or **never captured against the live game**;
    - the converter produced a warning;
    - a one-step fidelity alarm fired in this fight.

  Gold labels also require `ai_state` ≠ `ai_state_assumed`.
- **`vpi_clairvoyant`** is the same estimate with `resample_hidden=False`. It is a diagnostic only (how much the position depends on luck) and is never used as a label.

### 1.5 What "best" does not mean here

It is not "best given the seed", not provably optimal, not multiplayer, and not portable across patches. It is not P(win) unless the unit says so. A label is valid only for its `(game_build, engine_sha, π_ref, value_level)`.

---

## 2. Architecture

### 2.1 Components and data flow

```
 LIVE GAME (Mac, v0.107.1 build 23811903, MODDED profile, Steam Cloud off for the game)
   STS2_MCP <- r33hab/STS2MCP @ 5a63f92 (MIT, schema 4; REVIEWED, built from source)
              REST 127.0.0.1:15526, API token required
        |                                          |
        | (Phase 0-1, after review,                | (Phase 1+)
        |  outbound network denied)                v
        v                                    spireline/live/
  r33hab/spire-coach (no licence)              mod_client
  live combat panel, HP grades,                FIREWALL = ALLOW-LIST: only displayed fields; piles as
  quiz, fidelity-gap logs                        multisets; move_id only if the intent identifies it;
  (= baseline B3)                                ai_fields only from a per-monster "deducible" list;
                                                 never ?hidden=1, never /compendium
                                               settle gate · watchdog · runner
                                                     |  InfoState (+ tape, build id, canary audit)
                                                     v
 +------------------ spireline core (Python; batch jobs run as macOS user `spireline`) -------------------+
 | infoset/ schema.py · firewall.py · ai_belief.py (likelihood-weighted AI-state / current-move particles)|
 | engine/  emu.py       sts2_gym (r33hab/sts2 @ b745217 + patches/*.diff; NativeAOT osx-arm64)          |
 |          snapshot.py  InfoState -> emu state via sts2_gym.live.convert + CombatSnapshot.cs;           |
 |                       hidden parts and current moves drawn from b(I); warnings -> fidelity_flags     |
 |          worlds.py    CRN world bank: det_seed = blake2b(info_state_hash, k)                          |
 |          referee.py   (Phase 3) mingxuan sts2-cli fork: real sts2.dll, room save + replay             |
 | search/  candidates.py    info-boundary lines; DFS + end-state dedup (cap 5,000); every line          |
 |                           pre-scored by 4 tempo rollouts, cut to 16; recall-checked                   |
 |          gumbel_root.py   Gumbel-top-k + Sequential Halving + CRN (numpy port of mctx logic)          |
 |          ismcts.py        PLAY searcher: SO-ISMCTS, SemAction keys, targets, availability counts      |
 |          racing.py        cross-fitted two-stage estimation; time-uniform CSs; survivor-scoped bounds |
 |          enumerate_eval.py  B8: Bottled-style turn enumerator + static evaluator (no rollouts)         |
 |          macro.py · mapdp.py · shop.py · verdict.py                                                  |
 | value/   ladder.py · vrun.py (Act-1 18-class head; 53-class after F3/F4) · vrun_human.py (check only) |
 | priors/  base.py Prior protocol · uniform · heuristic (B8 scores / deck-fight) · net · haiku · jev    |
 | oracle/  label.py (bronze/silver/gold; tiers A/B/L) · posbank.py (SpireBench-107: Track D, Track I)   |
 | learn/   exit.py (wraps rl/prior_loop) · dmc.py (wraps rl/run_train)                                  |
 | eval/    battery.py · regret.py · stats.py (Wilson, McNemar, TOST, cluster bootstrap, CSs, power)     |
 |          fidelity.py · rngcorr.py (F9) · prereg/*.yaml                                               |
 +------------+--------------------------------+----------------------------------+--------------------+
              v                                v                                  v
        ledger/ (SQLite + Parquet:      advise/ macro + combat page          dash/ claude.ai artifact:
        every decision, who chose it,   (127.0.0.1, read-only, unit-labelled  regret by decision type,
        cfg hash, units, flags)         values, verdict badges, quiz)         battery funnels, parity
```

### 2.2 Interfaces (`spireline/api.py`)

```python
class Engine(Protocol):                         # emulator; referee and live implement subsets
    def from_info_state(self, I: InfoState, hidden_seed: int, ai: AiParticle) -> Handle: ...
    def clone(self, h: Handle, resample_hidden: bool, det_seed: int) -> Handle: ...
    def legal(self, h: Handle) -> list[SemAction]: ...   # (DefId, upgraded, enchant, cost, target id)
    def step(self, h: Handle, a: SemAction) -> StepResult: ...
    def info_state(self, h: Handle) -> InfoState: ...    # firewall-filtered, hashable
    def afterstate(self, h: Handle, a: SemAction) -> InfoState | None: ...

class AiBelief(Protocol):                       # infoset/ai_belief.py
    def sample(self, I: InfoState, k: int, seed: int) -> list[tuple[AiParticle, float]]: ...

class Prior(Protocol):                          # uniform | heuristic | net | haiku | jev; swappable, logged
    name: str; version: str
    def __call__(self, I: InfoState, legal: list[SemAction]) -> PriorOut: ...  # logits, nouls, $, latency

class RunValue(Protocol):
    level: Literal["L0", "L1", "L2"]; units: str
    def value(self, X: InfoState) -> float: ...             # in the level's own units
    def dist(self, X: InfoState) -> np.ndarray | None: ...   # 18- or 53-class floor/won

class Searcher(Protocol):
    def decide(self, I: InfoState, budget: Budget, prior: Prior, value: RunValue) -> Decision: ...
```

**Invariants.**
- Priors, values, features and prompts receive only `InfoState`.
- The firewall is an **allow-list**: a payload field that is not listed is dropped and logged.
- Code owns legality and arithmetic. Models return indices or probabilities. This is the [brekkylab](https://github.com/brekkylab/sts2-llm-coop-mod) pattern; [CharTyr's 409 cascades](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/docs/experiments/competitor_comparison/RESULTS.md) show the cost of skipping it.
- Every ledger row records **which policy actually chose the action**. A fallback can then never silently contaminate results, as happened in [ai-spire](https://github.com/biolbe1230/ai-spire).
- Policies are pure functions `(state, kb, config) -> (action, scores, rationale)` with a logged config hash (FableBot's discipline).

**Ledger row:** `position_id, track, game_build, engine_sha, versions_lock_hash, I, legal[], chosen, chosen_by, q_table[], value_level, value_units, verdict, epsilon, pi_ref, budget, wall_ms, usd, fidelity_flags, ai_state, one_step_check`.

### 2.3 Reuse vs build

- **Reuse unchanged after review:**
  - r33hab/sts2 (emulator, `sts2_gym`, `rl/`);
  - the r33hab/STS2MCP `spire-coach` branch;
  - spire-coach (user tool and baseline only, run under a network deny);
  - mctx's Gumbel logic (about 150 lines, ported to numpy);
  - the jev factored pattern (about 100 lines, ported).
- **Patch queue** (`patches/*.diff` against `b745217`, each offered upstream as a PR):
  - re-roll of a non-identifying current enemy move on `resample_hidden` (L8; expected to be needed);
  - fixes for L2/L3/L7 if they fail;
  - SIGSEGV fixes.
- **Map row count, as an upstream request.** The emulator builds 17-row maps in Acts 2–3; the game uses 16 and 15 (`BaseNumberOfRooms` 14/13) ([FULL_RUNS](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/FULL_RUNS.md)).
  - The fix must match the game's map-generation RNG consumption exactly. That makes it a small port, verified by captures, not a one-line patch.
  - Estimate: 8–20 h of Claude Code work plus about 10 live Act-2/3 map captures.
  - It is an entry criterion for Acts 2–3 work, not for Phase 2 as a whole.
- **Build:** the `spireline/` package listed in §2.1. New logic:
  - firewall, AI belief and leak suite;
  - macro-action candidates and the Gumbel root;
  - a semantic, target-aware ISMCTS wrapper with availability counts;
  - two-stage racing with confidence sequences, and verdicts;
  - B8, the value ladder, the oracle and the position bank;
  - eval and stats;
  - the live adapter, runner and watchdog;
  - the macro advisor page and the dashboard export.

---

## 3. Simulator strategy

### 3.1 Three backends, one pinned version

| Backend | Fidelity | Throughput | Rollback | Role |
|---|---|---|---|---|
| **r33hab emulator** (NativeAOT osx-arm64) | A reimplementation built from a local decompile.<br>**Act 1:** combat starts exact across 32 captures (16 encounters × 2 seeds); run generation exact across 30 captures; selection 88/88 ([HANDOFF](https://github.com/r33hab/sts2/blob/spire-coach/HANDOFF.md)). All catalogue captures are **A8 custom-mode seeded runs**, so A0 exactness is untested.<br>**Card capture against the live game:** Defect 88/88, Necrobinder 88/88, Regent 87/87, Ironclad 29/85, Silent 21/86, Colorless 23/53. **182 singleplayer-reachable cards were never played against the game.**<br>**Divergence catalogue:** about 449 closed entries, "Open: None" at `b745217`. The catalogue itself warns that the count is a bad proxy ([divergence-catalog](https://github.com/r33hab/sts2/blob/spire-coach/docs/divergence-catalog.md)).<br>**Acts 2–3:** Hive and Glory suites were written from source; 10 of 33 diverged on move tables, all now closed. Map rows are 17 vs the game's 16/15 | Measured on an **Apple M4 Max (10P+4E, 36 GB)** ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)):<br>• step 58–72 µs<br>• simulation 435–448 µs on a combat handle (evangambit: ~714 µs, machine unknown)<br>• 300-sim decision ≈ 85 ms without prior<br>• fight ≈ 1.5 s at 300 sims (no prior), 0.65–0.86 s at 60 sims; about 2x with the batched prior<br>• A9 rules run 9.32 s at 120/500 sims: 3,014 runs/h on 8 workers; 3,774/h on 12 (gen 0)<br>**Mac: unmeasured.** Assumed 1.5–2x slower per core | In memory: ~17 µs (evangambit) to ~70 µs (r33hab) per clone, hidden state resampled | **All search, labels, batteries and training** |
| **Live game** + r33hab/STS2MCP | Exact | 61.5 decisions/min at 3x and about 35 runs per 3 h for a rules bot, measured on **Windows** ([LOG](https://github.com/cicero225/STS2FableBot/blob/main/LOG.md)); Mac UNVERIFIED. Our estimate with PLAY-mode search: 8–15 min per run (§3.4) | Room level only | Live advice, one-step fidelity checks (F5), parity (F6) |
| **sts2-cli, mingxuan fork** (Phase 3) | Real sts2.dll with Godot stubbed; a frame pump replaces the IL patches. Upstream has stub bugs (Gardener runaway, Kaiser Crab false win) | About 20 decisions/s per process (Windows); Mac UNVERIFIED | Room save + `set_draw_order` + prefix replay | Referee for Act 2–3 parity and a 2% spot-check of gold labels |

**Why v0.107.1.**
- It is main-branch Steam build 23811903, the build installed on the owner's Mac.
- It is also the emulator's target, FableBot's build and spire-coach's build.
- Spire Codex holds 630,765 human runs on it.
- v0.111.0 is still a public beta ([Steam news](https://store.steampowered.com/news/app/2868840)).

### 3.2 Getting live positions into the emulator

`engine/snapshot.py` calls `sts2_gym.live.convert`, which turns `live-snapshot/1` into `emu-snapshot/1` and loads it through `CombatSnapshot.cs`. That code path exists at `b745217`; we have not run it.

**The firewall runs first, as an allow-list.**
- **Admitted:** player and pile fields as multisets; card ids, upgrades, enchantments and afflictions; relic counters; enemy HP, block and powers; intents as displayed (`type`, `damage`, `hits`, the displayed `label`); `state_log` entries for moves already executed.
- **`move_id`** is admitted only when L8 has shown that this monster's displayed intent identifies the move uniquely. Otherwise it is replaced by the intent category.
- **`ai_fields`** are admitted only from a per-monster list of fields proven deducible from observed history. For example, a pack's `CallForBackupCount` can be counted from observed calls; [enemy_ai.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/live/enemy_ai.py) already reconstructs it from move logs. All other fields are dropped and reconstructed from history.
- **Always dropped:** `move_follow_up_id`, `draw_pile_ordered`, every seed, `/compendium`.
- The adapter never requests `?hidden=1`.

**Hidden parts** (the draw-pile permutation, unobserved streams, current non-identified moves, unobserved AI fields) come from b(I), using a synthetic seed and AI particles (§1.1). They never come from the game's seed or the payload.

**`ai_state_assumed`** means only one thing: "AI state set from a deterministic reconstruction that uses history only, because no particle survived". The value is never taken from the payload. Such positions are excluded from gold labels.

**Converter warnings.** Every `ConversionResult.warnings` entry becomes a `fidelity_flag`, which makes the position UNSUPPORTED.

**Run-level snapshots** (deck, relics, map, gold, potions) for macro decisions go through the engine service's `strategy` method. That method takes "the training design's live-run object and a live screen" ([strategy.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/live/strategy.py)). Whether it covers every macro screen is **UNVERIFIED**; it is a week-2 spike.

**Rejected:** keeping a "shadow emulator" in lockstep with the true seed. It is a leak surface, and whole-run lockstep is verified only in Act 1.

### 3.3 Fidelity programme

| ID | Check | Pass criterion |
|---|---|---|
| F1 | Seeded tape replay, emulator vs live (ordered piles in the test harness only) | 100% match on ≥ 50 Act-1 **Defect** tapes and ≥ 50 Act-1 Ironclad tapes, **at A0** as well as A8 ([replay-verification](https://github.com/r33hab/sts2/blob/spire-coach/docs/replay-verification.md)). Tapes are captured in custom mode, the mode the catalogue already uses |
| F2a | **Frequency-weighted card capture coverage**: the share of card instances in 2,000 sampled agent positions whose card is captured live | Track D: ≥ 99% (expected, at 88/88). Track I: positions with any uncaptured card are excluded. The coverage number is reported, and the Ironclad capture sprint is optional |
| F2b | Outcome-distribution parity, emulator vs referee: top 40 encounters × 200 fights, same fixed policy | \|ΔE[HP loss]\| ≤ 2 HP and \|ΔP(death)\| ≤ 3 pp. Failures are flagged and excluded from test splits |
| F3 | Multi-seed encounter sweeps for Acts 2–3 (`combat_sweep.py`, ≥ 5 seeds) | 0 open divergences for encounters in test splits. **Gates RL-2 training beyond Act 1** |
| F4 | Map row count | Matches the game (16 / 15). **Gates RL-2 training beyond Act 1 and every L2 label** |
| F5 | **One-step prediction on every live decision**: deterministic fields (enemy HP/block, player HP/block/energy, powers, post-intent HP) predicted before the action. spire-coach's `check` already flags impossible outcomes | ≥ 98% exact on deterministic Act-1 actions. Each miss becomes a catalogue entry |
| F6 | Sim-to-real parity: same policy, same seeds, emulator vs live | TOST equivalence at ±5 pp (§7.4) plus a floor survival curve. Decision agreement is reported separately from outcome agreement |
| F7 | "Too good to be true" audit: any line whose Q exceeds the root value by more than 15 points is replayed in the referee or the live game | Search actively hunts emulator bugs ([ARCHITECTURE](https://github.com/evangambit/sts2/blob/main/rl/ARCHITECTURE.md)) |
| F8 | Canaries: native crash (retried and logged), combat ending without enemy deaths, 500 → 0 HP in one enemy phase | Sample invalidated, counted, never silently dropped |
| F9 | **RNG cross-stream correlation test.** Documented v0.107.0 dependences: first-fight potion drop by Act-1 region (about 76% Underdocks vs 4% Overgrowth); Neow's Bones → Debt about 54% in Underdocks ([tck.mn](https://tck.mn/blog/correlated-randomness-sts2/)). Run on 20,000 emulator seeds, on the owner's own v0.107.1 `.run` files, and on Spire Codex v0.107.1 runs if terms allow | No dependence at α = 0.001 on the pre-listed pairs. The emulator test is only as good as its MegaRandom port, which is why real runs are checked too. A failure is recorded and the knowledge convention (§1.1) is applied |

Fidelity bugs dominate early progress. Doron Singer's harness found about 100 bugs, and fixing them raised Act-1 boss wins from 6.5% to 36% ([series](https://dev.to/feed/doronsinger)).

### 3.4 Throughput and time budgets (Mac: 8 performance + 2 efficiency cores, 16 GB)

All Mac figures are **estimates**. They take r33hab's M4 Max measurements and apply an assumed per-core slowdown of 1.5–2x. Day 4 of week 1 replaces them with measurements.

| Quantity | Estimate | Basis |
|---|---|---|
| Machine-wide combat sims/s | 5,000–8,000 (6 workers) | 435–714 µs/sim on faster machines; ≈ 0.9 scaling per worker measured at 8 workers |
| Batched prior call | ≈ 1–1.5 ms/state | 0.7–0.9 ms per batched prior call on M4 Max (forward 0.14–0.38 ms/state at batch 32, plus 0.55 ms encode) ([FINDINGS](https://github.com/r33hab/sts2/blob/spire-coach/rl/FINDINGS.md)) |
| Tempo rollout to end of fight | ≈ 0.7–0.9 ms | 435–448 µs on M4 Max |
| Remaining-fight continuation | @60: 0.5–0.9 s; @300 with prior: 2–3 s | About half a fight's ~17 decisions |
| Live combat advice (QUICK) | ≤ 10 s p90 | §4.3; spire-coach uses a 1.5 s budget on 4 workers |
| Self-play run | ≈ 1.2 s per floor reached (gen 0, rules) to ≈ 2.5 s per floor (prior, larger boss budgets) | 9.32 s per run at mean floor 12.88 on M4 Max (≈ 0.72 s/floor) |
| Live run with PLAY-mode search | 8–15 min | ~1 s game time per decision at 3x, plus 0.2–1.5 s single-threaded search, × ~350 decisions, plus relaunches |
| Cloud (optional) | Hetzner CCX43, 16 vCPU, about $0.45–0.51/h (third-party trackers, UNVERIFIED) | `scripts/build.sh` supports `linux-x64` ([build.sh](https://github.com/r33hab/sts2/blob/spire-coach/scripts/build.sh)); untested by us. Holds only our private binaries, never game DLLs or the decompile. **Default is local** |

**Unattended overnight runs on a laptop.**
- Run jobs under `caffeinate -i -s -w <runner pid>`.
- Mac on AC power, lid open (or clamshell with an external display), Low Power Mode off.
- `pmset -g therm` is logged every 10 min into the job record.
- Jobs checkpoint and resume; the r33hab runner already resumes generations.
- Workers run at `nice 10`.
- At most 6 workers overnight. At most 3 while the game runs (the game's working set reached 13.3 GB after about 3 h at 3x on Windows; Mac UNVERIFIED).

### 3.5 Version drift

- **Freeze now.**
  - Set Steam to update the game only on launch.
  - Archive `SlayTheSpire2.app` with `ditto`, and back up saves.
  - Write `versions.lock` with: build 23811903, the `sts2.dll` sha256, mod commit `5a63f92`, `b745217` plus the patch hashes, the decompile hash, and the **test counts observed at pin time**.
  - Every record and label carries the lock hash.
- **Patch day.** The next main patch (alternate Act 2 plus a sixth character, no date given) will break the mod, the emulator and sts2-cli together. The v0.107.1 recovery of STS2MCP took about 40 days. Policy:
  - stay on the archived v0.107.1;
  - labels remain valid for v0.107.1;
  - wait for upstream ports rather than porting the emulator ourselves;
  - then re-run F1–F3 and F9 and re-label overnight under a new tag.
- **Cheap drift alarm.** Re-score frozen positions with the LLM prior on the new card text.
- **Don't chase the v0.111 beta.**

### 3.6 Supply chain and sandbox

**The risk.** r33hab/sts2, r33hab/STS2MCP and r33hab/spire-coach were created at 17:36:11–17:36:20Z on 2026-10-05 and pushed about 20 s later.
- 0 stars, `fork:false`, `parent:null` ([GitHub API](https://api.github.com/repos/r33hab/spire-coach)).
- spire-coach has no licence.
- The plan builds a native dylib loaded by ctypes and installs an in-process DLL into the game.

**What we know so far.** A cursory grep at the pinned commits on 2026-10-10 found:
- no `HttpClient`, `Socket` or `DllImport` in `src/Sts2Emulator`;
- no HTTP client use in `src/sts2_gym` or `rl/`;
- the mod's listener binds only `localhost` and `127.0.0.1`, and it requires a token.

This is **not** a security review.

**Plan, before anything is built or run (week 1, day 1).**
1. **Provenance diff.**
   - Tree-diff r33hab/sts2@`b745217` against evangambit/sts2@`37e4264`. The SHAs differ because history was rewritten, so diff trees, not commits.
   - Diff r33hab/STS2MCP@`5a63f92` against Gennadiyev/STS2MCP main and cicero225/STS2MCP.
   - Claude reads every new or changed path that does any of: native exports or P/Invoke; networking; process spawn; file writes outside the repo or game mods folder; build scripts and MSBuild targets; `uv` scripts, entry points and pre/post hooks.
   - Claude reads spire-coach's installer and save-editing code paths.
   - Findings go in `spireline/docs/SECURITY_REVIEW.md` with a go / fallback decision.
2. **Build from source only.** Never use prebuilt DLLs. Pin SHAs, record artefact hashes in `versions.lock`, and use the project's `uv` lockfile inside `a dedicated venv`.
3. **Isolation.**
   - The emulator build, labelling and training run as a dedicated standard (non-admin) macOS user `spireline`. The owner creates it in System Settings. It holds copies of the game DLLs needed for the decompile, from the owner's own install.
   - spire-coach and the live adapter run as the main user but with outbound network denied. The options are LuLu (open-source firewall, installed by the owner) or a `sandbox-exec` deny-network profile; `sandbox-exec` on Darwin 24.6 is UNVERIFIED.
4. **Mod install by hand.**
   - Never run `spire-coach mod install`, `mod enable` or `saves seed-modded`.
   - After review, copy the built `STS2_MCP.dll` and its manifest into the mods folder, and enable it in the game's own Mods screen (spire-coach's README documents that screen).
   - Preferred target is a second, modded copy of the app launched with `steam_appid.txt` while Steam runs. Whether that works on macOS is UNVERIFIED. The fallback is the Steam install's `mods/` folder.
   - The pristine archive is never modified.
5. **Fallback substrate** if the review fails: evangambit/sts2 plus the cicero225 STS2MCP fork, with `sts2_gym.live.convert` replaced by our own converter. That costs an estimated +15–25 h, and spire-coach is dropped.
6. **Licence.** The owner asks the r33hab author for licence terms for spire-coach. Until then it is used locally only and never copied.

---

## 4. Search and oracle

### 4.1 One searcher, four budgets

**PLAY** mode is the fast agent: self-play, batteries, autopilot. It is also the reference policy π_ref. **QUICK**, **DEEP** and **LABEL** are slower evaluators: one-step improvements over a stated continuation.

**PLAY mode** (`search/ismcts.py`, wrapping r33hab `run_search`):
- **Single-observer IS-MCTS.** Every simulation starts from `clone(resample_hidden=True)` of the root plus an AI particle. Statistics are shared across determinizations.
- **Children are keyed by `SemAction`**: DefId, upgraded, enchant, cost this turn, target creature id. They are not keyed by phase-local mask index, because below a draw the same index can name different cards in different worlds ([combat_mcts.py](https://github.com/r33hab/sts2/blob/spire-coach/rl/combat_mcts.py)). Identical cards collapse into one action.
- **Availability counts.** Below chance nodes, different worlds offer different actions. The exploration term uses `N_avail(a)`, the number of visits in which a was legal, in place of the parent count. This is ISUCT ([Cowling, Powley & Whitehouse 2012](https://eprints.whiterose.ac.uk/id/eprint/75048/)). It avoids over-exploring rarely available actions.
- **Targets are enumerated.** The current search uses target −1 on multi-enemy fights.
- **Inside the tree:** PUCT with the net prior and a tempo rollout at truncated leaves. The leaf mix is `λ_leaf·net + (1−λ_leaf)·rollout`, with λ_leaf starting at 0 because the value head never beat rollouts.
- **Root selection: Gumbel + Sequential Halving.**
  - m = clamp(⌊n/8⌋, 4, 16): 7 candidates at 60 sims, 16 at ≥ 128. Rounds = ⌈log₂ m⌉, with CRN worlds shared within a round.
  - Final move = `argmax(g + logits + σ(q̂))`. Policy target = `softmax(logits + σ(completed q))`, with `σ(q) = (maxvisit_init + max_b N_b)·value_scale·q` ([mctx qtransforms](https://github.com/google-deepmind/mctx/blob/main/mctx/_src/qtransforms.py)).
  - Root actions are information-boundary lines, legal in every world. Below the root, an action unavailable in a world is treated as **missing** in completed-Q, not as zero.
  - c_puct and value_scale are **re-tuned in ablation A3**. The measured c ≈ 0.1 was for UCT with argmax-mean selection and is only the starting point.
  - This fixes two measured failures:
    - argmax-mean under a prior "selects for noise" (+0.6 vs +2.0 HP);
    - CRN makes root visits uniform, which shrank the policy-target window from 0.320 to 0.105 nats at crn_fraction 0.6 ([FINDINGS](https://github.com/r33hab/sts2/blob/spire-coach/rl/FINDINGS.md)).
- **Budgets:** hallway 60–120 sims, elite 300–500, boss 500–1,000. They are weighted toward bosses because 67% of AgenticSTS defeats happened on boss floors ([history.jsonl](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS-Data/runs/history.jsonl)).

**QUICK / DEEP / LABEL, combat** (`search/candidates.py`, `racing.py`):
1. **Candidates.**
   - DFS over this turn's deterministic plays from the imported state, stopping at the information boundary.
   - Deduplicate by end-state hash and cap at 5,000 lines (Bottled AI caps at 11,000).
   - **Every** deduplicated line is pre-scored by 4 tempo rollouts. That is at most 20,000 × ~0.8 ms ≈ 16 core-s, and usually far less.
   - Keep 16: all lethal lines, "end turn now", and the top lines by pre-score, so a hand-written static evaluator never decides alone.
   - **Candidate recall** is measured on 200 dev positions against a 64-candidate run. Pre-registered: ≥ 98%.
2. **Stage 1, screening.**
   - Sequential Halving over the 16 with tempo-rollout continuation: 16×32 → 8×64 → 4×128 → 2×256 CRN worlds, about 2 core-s.
   - Pruning is conservative: keep up to 6 candidates whose upper bound reaches the leader's lower bound, with a minimum of 3.
   - **Screening recall** is measured on 200 dev positions by running Stage 2 on all 16 and counting how often the full-estimation argmax was pruned. Pre-registered: ≥ 98%. Below that, Stage 1 switches to PLAY@16 continuation.
3. **Stage 2, estimation on fresh worlds.**
   - Survivors get **equal** numbers of new CRN worlds. The continuation depends on mode:

     | Mode | Continuation | Quantity estimated |
     |---|---|---|
     | QUICK | Tempo rollout | Q^{tempo} |
     | DEEP (opt-in, ≈ 60 s) | PLAY@16 | Q^{PLAY@16} |
     | Silver label | PLAY@60 | Q^{PLAY@60} |
     | Gold label | PLAY@300 | Q^{PLAY@300} |

   - Racing on the paired top-2 difference uses **time-uniform confidence sequences**. It stops when the verdict is determined or the budget runs out.
   - **QUICK answers are Q^{tempo}, not Q^{π_ref}**, and the advisor page says so.
4. **Play.** Recommend the first atomic action and re-plan after new information.

**Why macro-actions instead of observation-branching trees.** Information-boundary candidates remove strategy fusion at the root at almost no cost. Full observation-keyed MO-ISMCTS ([Cowling et al.](https://eprints.whiterose.ac.uk/id/eprint/75048/)) is ablation A1. It enters the core only if PIMC and SO-ISMCTS labels disagree on more than 5% of decisive Tier-A positions.

### 4.2 Macro decisions

- **PLAY and self-play (no π_ref Monte Carlo).**
  - The policy is the V_run afterstate argmax.
  - When the top-2 gap is under 2 points, add a capped paired deck-fight signal: ≤ 32 tempo-rollout fights per candidate, ≈ 0.1 core-s.
  - Map choices use V_run's built-in map-ahead features ([DESIGN §3](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)). No map DP runs in self-play.
- **QUICK macro (live, ≤ 30 s).**
  - V_run on every afterstate, plus paired deck fights ([`deckfights.py`](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/deckfights.py)): 3 top candidates × 6 fight queries × 4 seeds ≈ 72 prior-guided fights ≈ 90–100 core-s.
  - The answer is labelled **"V_run + deck-fights"**, not Q^{π_ref}. V_run error is model error and is not in the CI.
- **LABEL Tier B gold** (card reward, rest, out-of-combat card select, relic, Ancient, shop top-2, map top-2).
  - Stage 1 is V_run plus paired deck fights.
  - Stage 2 runs CRN act rollouts to the act boss under a "PLAY-lite" continuation: combat MCTS@60 hallway and @300 elite/boss, macro V_run-greedy, every decision re-resampled per §1.2.
  - An AIVAT-style control variate subtracts `V_run(afterstate)` ([AIVAT](https://arxiv.org/abs/1612.06915)).
  - Target half-width: 2 pp of P(clear act).
- **Map** (`mapdp.py`, ADVISE/LABEL only).
  - Enumerate paths to the boss.
  - Value each path by expectimax:
    - FightNet outcome distributions per encounter class, given deck and relics, **cached by (deck hash, encounter class) and refit only at act boundaries or on cache miss**;
    - explicit chance nodes for `?` rooms, using the engine's `RunConstants` odds;
    - V_run at rest and shop nodes.
  - Verify the top 2 next nodes by act rollouts in LABEL mode. Explicit chance nodes beat determinization at run level ([ARCHITECTURE](https://github.com/evangambit/sts2/blob/main/rl/ARCHITECTURE.md)).
- **Shop.** Enumerate affordable bundles (≤ 32 after blueprint pruning; removal target chosen by an inner argmax). Score with V_run, then verify the top 2 in LABEL mode.
- **Events.** Each page is a decision. Outcomes are chance nodes, sampled through resampled clones.

### 4.3 Budgets

Costs are per position on the Mac (estimates; the week-3 pilot replaces them).

| Mode | Combat | Macro | Typical cost |
|---|---|---|---|
| PLAY | 60–120 / 300–500 / 500–1,000 sims (hallway / elite / boss), Gumbel root | V_run argmax + capped deck fights | 0.05–1.5 s per decision |
| QUICK | Candidates + Stage 1 + Stage 2 with tempo continuation (up to ~35,000 rollouts) | V_run + 72 deck fights | Combat ≤ 10 s p90 on 5 workers; macro ≤ 30 s |
| DEEP (opt-in) | Stage 2 at PLAY@16, about 1,500 continuations | n/a | ≈ 60 s |
| LABEL silver (Tier A) | ≥ 100 fresh worlds per survivor, racing to half-width 1 L0 point, PLAY@60 | n/a | 2.5–22 core-min; central ≈ 8 |
| LABEL gold (Tier A) | Half-width 0.5 L0 point, PLAY@300, stability vs B8 continuation, 0 flags, particles, 2% referee spot-check | n/a | 14–98 core-min; central ≈ 45 |
| LABEL Tier B silver | n/a | V_run + deck fights, 3 × 8 × 8 = 192 fights | ≈ 4 core-min |
| LABEL Tier B gold | n/a | PLAY-lite act rollouts (8–25 s each), half-width 2 pp after control variate | 1.8–7.2 core-h |

**Derivation.** Worlds needed for half-width h at paired standard deviation σ are n = (1.96σ/h)².
- Tier A at σ = 3–8 L0 points: 35–246 worlds per survivor for h = 1 point; 138–983 for h = 0.5 point.
- Tier B at residual σ = 15–30 pp: 216–864 rollouts per survivor for h = 2 pp.
- σ, survivors per position and remaining decisions are measured in the week-3 pilot.

**Pre-registered cost rule.** If pilot central costs exceed these estimates by more than 2x, Tier A silver is cut from 1,000 to 600 positions and Tier B gold from 80 to 50.

### 4.4 Hidden-information checklist

1. `InfoState` is the only input to priors, values, features and prompts.
   - A test fails if feature code reads run-engine state lists 11–13, the future encounter and event sequences ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)).
   - A test fails if `combat_tokens` encodes any enemy field other than those the game displays. The encoder embeds a current-intent magnitude and a "secondary intent" with a magnitude. In the emulator source, the secondary intent is the current move's second declared intent ([EnemyAI.cs `SecondaryIntentFor`](https://github.com/r33hab/sts2/blob/spire-coach/src/Sts2Emulator/Core/EnemyAI.cs)), although a comment in `combat_tokens.py` calls it "the turn after". Whether the game displays non-attack magnitudes is UNVERIFIED.
2. The live firewall is an allow-list (§3.2). It never requests `?hidden=1` and never calls `/compendium`.
3. Every simulation and every continuation decision starts from `clone(resample_hidden=True)` plus an AI particle.
4. CRN worlds use synthetic seeds `blake2b(info_state_hash, k)`, never the game's seed.
5. Macro labels are blocked until L2 and L3 pass. Gold combat labels are blocked until L7 and L8 pass.
6. Any un-resampled clone in policy code must be justified as reading only on-screen information.
7. Clairvoyant runs are tagged and used only for the VPI diagnostic.
8. The live adapter asserts that piles are multisets, and canary tokens are audited (L6).

### 4.5 Label tiers

| Tier | π_ref / continuation | Volume | Cost (Mac estimate) |
|---|---|---|---|
| Bronze (combat) | Tempo rollout → L0 | 100k | ≈ 1 core-s each, ≈ 28 core-h |
| **Silver Tier A** (combat) | PLAY@60 → L0 | 1,000 per track (600 dev / 400 test). Track D first; Track I is 400 (250 / 150) | ≈ 135 core-h for Track D (range 40–370) ≈ 3 nights at 6 workers |
| **Gold Tier A** | PLAY@300 + B8-continuation check + 0 flags + particles + spot-check | 200 (subset of silver; doubles as the @60 vs @300 agreement measurement) | ≈ 150 core-h (47–330) ≈ 3 nights |
| Tier B silver (macro) | V_run + paired deck fights → L1 | 300 (180 dev / 120 test), Act 1 | ≈ 20 core-h |
| Tier B gold (macro) | PLAY-lite act rollouts → L1 | 80 (50 dev / 30 test), Act 1 | ≈ 320 core-h (145–580) ≈ 7 nights, or ≈ 20 h on CCX43 (≈ $10, UNVERIFIED) |
| Full-run check (exploratory, P3) | PLAY-lite to run end → L2 | 20 | 100–300 core-h, optional cloud |
| Tier L (live) | Positions from live runs and the owner's play, converted with zero warnings, labelled silver | ≥ 300 | As silver |

**Rules on keeping labels.**
- Bronze labels are kept only if Kendall τ against silver is ≥ 0.6 on decisive positions.
- Tier B silver is kept as a label only if its argmax agrees with Tier B gold on ≥ 80% of decisive gold positions. Otherwise it is a prior only.
- Labels are regenerated whenever π_ref is promoted, because stored labels go stale in the optimistic direction ([ARCHITECTURE](https://github.com/evangambit/sts2/blob/main/rl/ARCHITECTURE.md)).

---

## 5. Where RL fits

### 5.1 Exact algorithms

1. **RL-1: Gumbel Expert Iteration for the combat policy prior.** Search (§4.1 PLAY mode) generates improved policy targets. A pointer network distils them, and the stronger prior makes the next search cheaper. This wraps r33hab `rl/prior_loop`.
2. **RL-2: Deep Monte Carlo afterstate value V_run, plus FightNet.** Run outcomes are regressed onto afterstates from emulator self-play, with Suphx-style global reward prediction. This is how the system values "this deck at this HP on floor 12".
   - It wraps r33hab `rl/run_train`: 18-class Act-1 head and 53-class full-run head, bootstrap β = 0.3 ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)), plus the paired deck-fight signal.
   - **It trains on Act 1 only until F3 and F4 pass.** The emulator's 17-row Act 2–3 maps would otherwise mis-specify E[floor] and the 53-class head.

Neither starts until a ledger signal justifies it (§8, flywheel table). Phases 0–2 already use RL concepts: Q over information sets, Monte Carlo evaluation and SPARTA improvement.

### 5.2 Environment, encoding and reward

- **Environment:** emulator `Sts2CombatEnv` / `Sts2RunEnv`, v0.107.1, Track D (Defect A0). A10 comes in Phase 4.
- **Seed pools** (r33hab base-34 scheme), disjoint, with SHA-256 recorded:
  - `T…` train;
  - `E…` evaluation, 40,000 seeds split into **20 fresh blocks of 2,000, one block per promotion and never reused**;
  - `F…` final test, 2,000 seeds, touched once per phase gate;
  - `P…` oracle positions.
- **Observation:**
  - Combat: r33hab `combat_tokens`. Cards are compositional `EmbeddingBag` sums initialised at 1/√K, which beat per-card embeddings by 0.073 nats. Piles are counts, never order. Player and enemy powers are separate token types. Enemy fields are limited by §4.4 item 1.
  - Run: an input 1,851 wide, which already includes the 8-number fight-signal block H. It holds a count-weighted deck, relics, potions, act one-hot, floor and map-ahead features ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)).
  - FINDINGS' lesson applies: fixing a broken observation helped; enriching a working one did nothing. Encoding work is limited to bug fixes and leak fixes.
- **Action:** a masked pointer over (card, target) SemActions, potions and end turn. Macro decisions are scored as **afterstates** (action-as-features, DouZero-style), not as fixed output slots.
- **Reward:** terminal W only; U_λ during warm start (§1.2). **No dense shaping constants.**
  - Constants like sts2-agent's +0.01 per damage bake in combat-local proxies.
  - A shaping bug paid Zaaacqwq's agent +1.76 for dying in front of the boss vs +0.65 for winning ([rl_v2](https://github.com/Zaaacqwq/SlayTheSpireRL/blob/main/plan/rl_v2_current_stage.md)).
  - Telemetry asserts that every win outranks every loss in realised return.

### 5.3 What is learned and when it is kept

| Component | Learned by | Keep only if |
|---|---|---|
| Combat policy prior | Gumbel ExIt | At **matched wall-clock**: lower Tier-A dev regret than the no-prior searcher (paired CI excludes 0), **and** a paired gain on a fresh E-block (primary metric: mean floor) |
| V_run | DMC + bootstrap | **Brier skill score > 0** against a base-rate model **and** against V0, the hand-written FableBot-style "arrive healthy" value (HP fraction, potions, act), with the paired CI excluding 0; log-loss improves; **ECE ≤ 3 pp computed only over bins containing ≥ 30 wins** (or ≥ 30 boss kills for the Act-1 head); lower Tier-B regret than V0; a battery gain |
| FightNet | Supervised on search-played fights | Beats the per-encounter marginal (r33hab: NLL 1.798 vs 2.161) |
| Combat leaf value | Supervised (λ = 0.3 blend of search and outcome) | λ_leaf > 0 wins paired at matched wall-clock |
| Macro policy | No separate head | V_run argmax plus search is the policy |
| Fast rollout policy (masked PPO, optional) | PPO with reward = ΔV_run | Only if it acts as a budget multiplier over the tempo rollout |

**Anti-circularity rule.** No component trained on oracle targets is graded only by oracle regret. Each promotion also needs a paired win on a fresh E-block and a clean F7 audit.

### 5.4 Training loop (`learn/exit.py`)

```
for gen in 0..G:                                   # each generation capped at ~8 h wall-clock
  # R: run level (Act 1 only until F3/F4 pass)
  self-play A0 Defect runs on T-seeds until the 5-h self-play budget is spent
      combat = PLAY(prior_gen, V_run_gen, 120/500/1000, Gumbel noise)
      macro  = V_run afterstate argmax, eps 0.15 -> 0.05, capped tempo deck-fights on close calls
               (NO pi_ref Monte Carlo verification inside self-play)
  train V_run, FightNet on last 3 generations (validation split BY RUN)
  # C: combat ExIt
  6,400 fights sampled from this generation's runs, 300 sims, crn_fraction 0.2 -> Gumbel completed-Q targets
  train combat net (per-head checkpoints, 167k-935k params; capacity was never the limit)
  # promotion, on a FRESH 2,000-seed E-block each generation
  primary:     paired mean floor (cluster bootstrap), one-sided, alpha 0.01
  co-primary:  Act-1 boss-kill rate (exact McNemar); wins join as co-primary once both arms >= 10%
  AND F7 audit clean; else revert and log in DECISIONS.md
  regenerate 200 rotating silver labels under the new pi_ref; report argmax stability across generations
```

Promotions are engineering decisions, made on independent fresh blocks. At α = 0.01, about 0.2 false promotions are expected over 20 generations. Headline claims use only the F pool, once per phase gate.

### 5.5 Compute estimate (Mac, 6 workers; estimates)

| Item | Mac | CCX43 (optional) |
|---|---|---|
| Self-play per generation | ≈ 2 h at gen 0 (20 s/run, ~2,000 runs) to the 5-h cap later (60–120 s/run, ~900–1,800 runs). Run time is modelled as ≈ 1.2–2.5 s per floor reached and re-estimated after gen 0 | ≈ 3x faster, ≈ $0.5–1.5 |
| One combat ExIt iteration (6,400 fights × 300 sims with prior, ≈ 4–6 s/fight) | ≈ 7–11 core-h ≈ 1.2–1.8 h | ≈ $0.5 |
| Network training | ≤ 1 h (CPU/MPS) | n/a |
| One generation | ≈ 4.5–8 h, one per night | n/a |
| 10–20 generations | ≈ 2–5 weeks of nights | ≈ $15–60 |
| Data | 10–20 gens × ~1,500 runs × ~400 decisions ≈ 6–12M decisions | n/a |

6–12M decisions is 0.2–0.3% of Slay_RL's 3.55B. The bet is that search amplification makes up the difference, and ablation A5 measures it.

**Honest expectation.** r33hab's generation 0 at A9 (rules policy, 12 workers) won 0 of 1,999 runs (Wilson 0–0.2%), with 95.4% Act-1 deaths and mean floor 12.66 ([FULL_RUNS](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/FULL_RUNS.md)). A0 is easier, but V_run starts with almost no wins to learn from. That is why gates are relative, the primary promotion metric is mean floor, and V_run is gated on Brier skill.

### 5.6 Not done

- End-to-end PPO or GRPO as the policy.
- RL on sts2-cli or the live game.
- Hand-shaped dense rewards.
- Distilling clairvoyant teachers.
- Multi-turn LLM RL, which is documented to collapse ("Echo Trap", [RAGEN](https://arxiv.org/abs/2504.20073)).

The only LLM-RL option is in Phase 5 and optional: a single-decision bandit on a small local model with reward = −oracle regret, allowed only if E1 passes.

---

## 6. Where cheap LLM compute fits, and where it must not be trusted

### 6.1 Allowed roles, all behind `Prior` and all off by default

| Role | Mechanics | Gate before use |
|---|---|---|
| **Root prior for macro decisions**, and for combat roots with more than 16 surviving lines | One batched call per real decision. Logits are mixed `0.5·llm + 0.5·uniform` (or with the heuristic or net prior) and feed Gumbel candidate sampling only. Search can always overrule them | **E1** |
| **Soft blunder feature** (Jev "waste/self-harm" noul) | Down-weights a prior logit by ×0.1. **Never a veto.** Hard removal is reserved for self-harm proven in code (lethal or fatal end turn) | **E4:** false down-weight of the oracle-best ≤ 1% |
| **Baseline policy** scored on SpireBench | Argmax over numbered legal candidates from a compact typed state (≤ 3k tokens) | None. This produces the first measured LLM regret on StS2 |
| Per-patch card/relic feature cache | About 20 yes/no judgements per card and relic, cached per build | **E5:** improves V_run Brier skill |
| Explainer on the advisor page | Writes prose **from Decision numbers only**. Every number is regex-checked against the Decision, units included; a mismatch means regenerate | None |

**Providers.**
- **Default: none.** The whole system runs offline.
- **Claude-native option:** Claude Haiku 5.5 (`claude-haiku-5-5`). Thinking can be disabled only at effort `high` or below, and the default effort is `medium`. Output is structured per-candidate scores..
- **Experiment arm:** Jev 1.13 pinned to `typesafe/jev-1.13-20260917`, through OpenRouter or TypeSafe, using the owner's own key.
- Only firewall-filtered game state is ever sent.

### 6.2 Where it must not be trusted

- **Not as an oracle or label source.** Jev went 1/182 upstream and 0/9 in the fork. Frontier LLMs without scaffolding have 0 wins in every published StS2 table ([TokenSpire2](https://github.com/collinzrj/TokenSpire2), [AgenticSTS re-runs](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/docs/experiments/competitor_comparison/RESULTS.md)).
- **Not inside node expansion or rollouts.** One 315 ms call costs as much time as several hundred emulator simulations.
- **Not for arithmetic, legality, lethal checks or non-damage loss conditions.** About 53% of AgenticSTS's Insatiable deaths were Sandpit-timer kills ([design doc](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/docs/2026-04-08-rich-combat-analytics-design.md)).
- **Not its self-reported calibration**, until E2 reliability curves against oracle Q exist.
- **Not fixture benchmarks as evidence.**
- **Not as a trainable component.** Jev weights are closed.
- **Not as a distillation teacher** until TypeSafe's terms are read (UNVERIFIED, [terms](https://typesafe.ai/terms)).
- **Never a hard dependency.** Every role has a uniform or local fallback, and fallbacks are logged.

### 6.3 Cost model

The model assumes a compact prompt of about 3k input and 120 output tokens. Jev's measured figure comes from its larger factored prompt (about 11k tokens); at 3k tokens it would be about $0.00013.

| Provider | Price | $/call | $/average run, macro only (~100 calls) | E1 (1,000 positions × 5 repeats) | $/1M labels |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | $0.10 in / $0.50 out per MTok for prompts ≤ 100K ($0.50 / $2.50 beyond); Batches 50% off (Anthropic model table, cached 2026-10-06; confirm at https://www.anthropic.com/pricing) | $0.00036 ($0.00018 batch) | $0.036 | ≈ $1.80 | ≈ $180 batch |
| Jev 1.13 factored | $0.042 per M input, output free ([docs](https://docs.typesafe.ai/models)) | $0.00046 (measured, ~11k-token prompt) | $0.046 | ≈ $2.30 | ≈ $460 |
| Claude Opus 5.5 (reference only) | $4 / $20 per MTok; thinking cannot be disabled, so the real cost is higher | ≥ $0.0144 | ≥ $1.44 | ≥ $72 | n/a |

**Latency.**
- Jev p50 is 315 ms in fast mode, with a 7–16 s slow mode (about 53% of calls on 2026-09-23). Haiku 5.5 latency is UNVERIFIED.
- Calls are cached by `(info_state_hash, candidate_set_hash, provider, prompt_version)`.
- LLM calls are never used in self-play: 200k macro calls per generation would add about $92 and about 17 h of latency.

**Bottom line.** Money is not the constraint: the whole LLM line item is $5–40 for the project. Evidence is the constraint.

### 6.4 Experiment E1, which decides whether any LLM stays

- **Positions:** held-out positions from **both** Tier A and Tier B (Tier B gold where available). The hypothesis is that LLMs help on macro and long-horizon decisions, as in MiniStS (Bomb 34.74 vs 17.2 HP, [Bateni & Whitehead](https://dl.acm.org/doi/fullHtml/10.1145/3649921.3650013)).
- **Arms and timing.**
  - **Provisional verdict (Phase 2):** uniform, heuristic (B8 static-evaluator scores for combat; deck-fight signal for macro), Haiku, Jev, Jev + heuristic mix.
  - **Final verdict (Phase 3, only if RL-1 is funded):** adds the net prior and Jev + net mix.
  - Both decision points are pre-registered in `eval/prereg/e1.yaml`.
- **Budget:** **matched wall-clock including LLM latency**, at 4 levels, with dollars reported. Selection uses Gumbel / fresh-world estimation, never argmax-mean under a prior.
- **Metrics:**
  - paired mean regret in the label's units (cluster bootstrap);
  - paired blunder rate P(regret > 1 L0 point), compared by McNemar, which has more power for zero-inflated regret;
  - top-1 on decisive positions;
  - calibration: ECE, and reliability of P(choice) against oracle Q rank.
- **Keep rule:** keep a provider only if one of these holds:
  - it cuts regret by ≥ 15% versus uniform **and** beats the best non-LLM prior available at that decision point (heuristic in P2, net in P3), with paired CI excluding 0 at the same wall-clock;
  - **or** it reaches equal regret (within a pre-declared ±0.2 L0-point equivalence margin) at ≤ ½ the wall-clock.

  Otherwise the LLM is demoted to explainer only.
- **Cost:** about $2–5 per verdict.

---

## 7. Evaluation protocol

### 7.1 SpireBench-107 (the primary instrument)

- **Scope:** v0.107.1, A0.
  - **Track D:** Defect, full game, Act 1 first.
  - **Track I:** Ironclad Act 1, positions with every card captured (0 UNSUPPORTED). Track I exists so FableBot (B2) and spire-coach (B3) can be compared on their own character.
- **Position sources:** PLAY-agent self-play, the rules policy, and ε-perturbed play (so mistakes are present), plus Tier-L live positions.
- **Stratification:** by act, fight type and turn index, with bosses and elites oversampled 2x.
  - Tier A mix: 40% boss turns, 30% elite, 30% hallway.
  - Tier B mix: 30% card rewards, 20% map, 12% shop, 12% rest, 12% event, 14% relic/Ancient.
- **Splits:** dev and test. Test is hashed into `MANIFEST.sha256` and scored only at phase gates. All tuning happens on dev, which avoids jev's selection-on-test problem.

**Label validity battery (dev):**
- **Label-noise floor.** Re-label every position on fresh worlds. "Oracle vs itself" regret should be under 0.3 L0 points; differences below the floor are noise.
- **Budget ×4 stability:** < 5% of DECISIVE positions change argmax.
- **Within-family continuation stability:** argmax agreement under π_ref@60 / @300 / @1,500.
- **Cross-family continuation stability:** argmax agreement between π_ref and B8 continuation on the 200-position subset. Disagreements are tagged `continuation_sensitive`.
- **Currency stability:** compare V_run^bot, HP-only L0 and `vrun_human` (a logistic fit on the owner's local `.run` files, used *only* as a check). Disagreeing positions are tagged `currency_sensitive`.
- **Act-horizon vs full-run labels:** agreement on the 20 exploratory full-run positions is reported, with no gate.
- **Screening and candidate recall:** both ≥ 98% (§4.1).
- **External anchor ("expert check set").**
  - 100 DECISIVE positions (60 Track D, 40 Track I) graded blind by 2–3 strong human players whom the owner recruits (for example, regular A10 winners).
  - Spirebird/Jorbs annotated replays are added if their terms allow.
  - Report expert–oracle agreement. Every disagreement is triaged by an F7 live or referee replay.
  - If no experts can be recruited, the fallback is triage of the owner's own quiz disagreements. That is a weaker anchor, and is stated as such.

### 7.2 Metrics

- **Per decision**, always in the label's units:
  - mean, p90 and p99 regret;
  - blunder rates P(regret > ε) and P(regret > 5ε);
  - top-1 accuracy on decisive, non-continuation-sensitive positions (anything in the CLOSE set counts as correct);
  - each broken out by decision type, act and encounter.

  CIs use a **cluster bootstrap over fights or runs**.
- **Power.** Per-position regret is zero-inflated and heavy-tailed. The paired σ of regret differences is assumed to be 3–5 L0 points until the pilot measures it.
  - At n = 400 test positions, the minimum detectable effect is MDE ≈ 2.8σ/√n ≈ 0.42–0.70 L0 points, or 0.5–0.85 with design effect 1.5.
  - Pre-registered target effects are therefore **≥ 0.5–1 L0 point**, never 0.2.
  - Blunder-rate differences, tested by paired McNemar, are the more powerful secondary.
- **Consistency with outcomes (performance-difference lemma):** `V^π(I_0) − V^{π_ref}(I_0) = E_{τ~π}[Σ_t A^{π_ref}(I_t, a_t)]`.
  - **Combat-level (primary).** Within fights, the sum of L0 advantages along the agent's trajectories must predict the paired end-of-fight L0 gap within CI.
  - **Run-level (exploratory).** Sample 1–2 uniformly random decisions per trajectory, weighted by trajectory length, over about 300 runs, at act horizon. Reported with a wide CI. With L0/L1 labels the identity holds only in those units.
- **Per run:**
  - win rate (Wilson), floor reached, boss kill rate per act, P(death) per elite and boss;
  - **HP lost per floor** (JoeB08's leading indicator);
  - discordance rate across paired seeds;
  - aborts and crashes, counted as losses and reported separately, never dropped (AgenticSTS dropped 66 of 385 rows).

### 7.3 Sample sizes

Computed for this design; α = 0.05 two-sided, 80% power unless noted.

| Comparison | n |
|---|---|
| Unpaired win rates 20% → 25% / 10% → 15% / 5% → 10% / 20% → 30% | 1,094 / 686 / 434 / 293 per arm |
| Paired McNemar, 5 pp, discordance 0.10 / 0.15 / 0.25 / 0.35 | 312 / 469 / 783 / 1,096 seeds |
| TOST equivalence ±5 pp, true gap 0, paired discordance 0.05 / 0.10 / 0.15 / 0.20 | 171 / 343 / 514 / 685 seeds |
| Per-decision regret, paired σ = 3 / 5 L0 points: MDE at n = 400 | 0.42 / 0.70 L0 points |
| Promotion, paired mean floor, σ_diff ≈ 6 floors (assumed; measured in gen 0), n = 2,000, one-sided α = 0.01 | MDE ≈ 0.44 floors |
| Promotion on wins at 2% vs 3%, n = 2,000 | power ≈ 55–65%, so wins are only a co-primary metric at low win rates |
| Live vs FableBot's historical 71/343, minimum detectable gap at n = 300 / 600 | ≈ 9.3 / 7.9 pp |

At discordance 0.35, two policies are essentially independent and pairing buys nothing. **Discordance is therefore measured in the pilot and reported.**

### 7.4 Run-level protocol

- **Emulator batteries.**
  - Pre-registered in `eval/prereg/phaseN.yaml` before launch: seed-block hashes, n, primary metric, threshold.
  - Both arms run on the same fresh E-block, 1,000–2,000 seeds; F pool for phase gates.
  - About 3–6 h overnight per pair on the Mac (estimate).
- **Sim-to-real parity (F6).**
  - Run the same PLAY policy on the same seeds in the emulator and in **custom-mode seeded live runs** on the modded profile.
  - Seeding is feasible in principle: the mod's custom-run embark sets a seed, and the r33hab catalogue's captures are all custom-mode seeded runs that the emulator reproduces in Act 1.
  - Whether the owner's modded profile has the Seeds epoch and the needed unlocks is **UNVERIFIED**. It is checked in week 2.
  - **Determinism controls:** single-threaded search, fixed simulation counts (no wall-clock budgets), `det_seed` derived only from `info_state_hash`. **Decision agreement is reported separately from outcome agreement.**
  - **TOST at ±5 pp.** n is set from the pilot's measured discordance: 171 seeds at d ≤ 0.05, 343 at d ≤ 0.10. If the emulator really is bit-exact in Act 1, d should be small, which is itself a strong parity signal.
  - Also reported: per-step agreement (F5 ≥ 98% in Act 1) and the floor survival curve.
- **Live-time budget.**
  - 171–343 parity runs × 8–15 min ≈ 23–86 h of exclusive game time.
  - Scheduled as 4–6 h sessions while the owner is away, with ≤ 3 emulator workers and a game relaunch every 15 runs.
  - That is 1–3 weeks in Phase 3, during which overnight training pauses on session nights.
- **Headline comparison with FableBot (Track I only).**
  1. **Primary:** per-decision regret of FableBot's pure-function policies on Track I Tier-L positions, run offline. Mac portability of its Python policies is UNVERIFIED; it is a week-2 spike.
  2. **Optional:** 300 live Track I runs against FableBot's historical 71/343, run only if the live budget allows. Superiority is claimed only if the CI on the difference excludes 0. The minimum detectable gap is ≈ 9.3 pp, and this is stated up front.
  3. **Optional:** a paired same-seed live head-to-head, if FableBot runs on the Mac.

  The 600-run unpaired headline from v1.0 is dropped.

### 7.5 Baselines

| ID | Baseline | Where |
|---|---|---|
| B0 | Masked uniform random | Emulator battery + SpireBench (D, I) |
| B1 | Emulator rules policy (+ MCTS 120/500). r33hab A9 Ironclad, 200 seeds: boss kill 8.0% (5.0–12.6%), mean floor 12.88 ([DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md)). Whether the rules macro is character-general is UNVERIFIED; if not, Track D uses rules macro + MCTS combat | Battery + SpireBench |
| B2 | **STS2FableBot**: 20.7% live (16.7–25.3%) | Track I only: Tier L offline + live historical |
| B3 | **spire-coach engine** (HP-valued combat search) | Track I live ledger + Tier A. Tests whether P(win)-style valuation changes combat play (ablation A6) |
| B4 | jev-the-spire2 factored policy, no search | SpireBench (about $0.70/pass); live record 0/9 |
| B5 | Claude Haiku 5.5 single call over numbered candidates | SpireBench. Stands in for the STS2MCP reference LLM agent (0/5 Silent A0 in re-runs) |
| B6 | AgenticSTS | Cited only (v0.103, Silent, Gemini): 3/10 → 6/10 (p ≈ 0.37), pooled 44/93; not comparable |
| B7 | **The owner** | Quiz mode on Tier B/L: personal regret per decision type, **stated as regret relative to π_ref, not as absolute mistakes**. The owner's own win rates are kept private |
| B8 | **Bottled-style enumerator**: turn enumeration over `candidates.py` lines, a hand-written static end-of-turn evaluator (~20–40 weighted features: kills, damage taken, block, HP, powers, potions), rules macro, **no rollouts** | Battery + SpireBench (D, I); also the second π_ref family (§1.2). Answers the open question "enumeration vs MCTS on StS2" |

### 7.6 Ablations and leak tests (pre-registered, dev only)

**Ablations:**

| ID | Ablation |
|---|---|
| A1 | PIMC vs SO-ISMCTS vs observation-keyed MO-ISMCTS, plus clairvoyant VPI: the size of strategy fusion |
| A2 | CRN on/off; crn_fraction 0 / 0.2 / 0.6 |
| A3 | Gumbel vs PUCT root at n ∈ {8, 16, 32, 64, 300}, at matched wall-clock; c_puct and value_scale re-tuned for the Gumbel root |
| A4 | Prior: uniform / heuristic / net / Haiku / Jev / mix (E1) |
| A5 | Combat budget scaling 60 → 1,500: where does more search stop paying? |
| A6 | Combat terminal value: spire-coach HP vs L0 vs V_run. **Does "best play" differ from "least HP lost"?** |
| A7 | Macro: V_run greedy vs + paired deck fights vs + Monte Carlo verification |
| A8 | Leaf: rollout vs net vs mix |
| A9 | Information-boundary macro-actions vs full-turn lines |
| A10 | Availability counts on/off in SO-ISMCTS |
| A11 | Character transfer: rerun A1, A2 and A6 on Track I to check that conclusions hold where fidelity is weaker |
| A12 | MCTS (PLAY) vs B8 enumeration at matched wall-clock |

**Leak suite** (`spireline/infoset/test_leaks.py`, in CI):

| ID | Test |
|---|---|
| L1 | The draw-pile unknown region is permuted across clones; known top and bottom cards are kept |
| L2 | **Non-circular:** from a map state, 200 resampled clones entering the same monster node produce more than one encounter id whenever the pool has more than one |
| L3 | Same as L2 for reward contents, shop stock, event outcomes and Ancient offers |
| L4 | Feature, prior and prompt code never reads hidden state lists 11–13. `combat_tokens` emits only displayed enemy fields (§4.4 item 1) |
| L5 | **Seed-swap via import:** the same InfoState imported with two different hidden seeds gives labels that agree within CI |
| L6 | Live adapter output contains no seed, ordered pile, `move_follow_up_id`, or non-allow-listed field. **Canaries:** a unique token planted in every hidden or conditionally hidden raw field (seed, ordered piles, `move_follow_up_id`, `move_id`, every `ai_fields` entry) of recorded payload fixtures must never appear in any InfoState, log or prompt unless the allow-list admitted that field |
| L7 | For monsters with history-dependent AI, resampled clones vary next intents consistently with the move-pattern rules, and particle posteriors match analytically computed move-table posteriors (unit tests on known tables) |
| L8 | **Current move behind a non-identifying intent.** For each monster with a Buff, Debuff, Defend, Status or Unknown intent whose move table allows more than one move, 200 clones (emulator) and 200 imports (live) must produce more than one current move id, in posterior proportions. Also records, per monster, whether the displayed `label`/`description` identifies the move; that per-monster result is what the firewall's `move_id` allow-list is built from |
| L+ | **Positive control:** `resample_hidden=False`, and importing the payload's true `move_id`, must each measurably inflate Q. This proves the suite can detect a leak |

### 7.7 "Show me": the dashboard

A private claude.ai artifact, exported from the ledger, with:
- a position viewer: InfoState, Q table with CSs **and units**, verdict, VPI, fidelity and AI-state flags;
- regret distributions by decision type and encounter, with the label-noise floor drawn in;
- a baseline leaderboard (B0–B8) per track on SpireBench;
- battery funnels: floor survival and boss kills per generation;
- the parity panel: emulator vs live, decision agreement, TOST;
- expert-check agreement;
- quiz results.

---

## 8. Scope and phased roadmap

**Assumptions.** About 6 h/week of the owner directing Claude Code, with overnight Mac compute. Effort is the owner's hours; Claude Code usage is not counted in $. All gates are relative and pre-registered.

| Phase | Weeks | Deliverable | Success criterion | Effort | $ |
|---|---|---|---|---|---|
| **P0: Safe foundation + live coach** | 1–2 | Security review with go/fallback decision<br>Emulator built and measured on the Mac<br>spire-coach running live (network-denied)<br>`spireline` scaffold, allow-list firewall, leak suite L1/L2/L4/L6/L8/L+<br>`stats.py` with confidence sequences<br>F2a and F9 numbers<br>B0/B1 batteries | `SECURITY_REVIEW.md` signed off<br>Tests match the counts recorded at pin time (no failures beyond the documented `TENDER_POWER` one)<br>Measured sims/s/core recorded (target ≥ 1,000; plan adjusted below 600)<br>c = 0.1 vs 1.4 reproduced (P(death) ≈ 0.09 vs 0.18, 240 fights)<br>Leak results recorded, or upstream issue filed with repro<br>CS coverage ≥ 95% in simulation<br>One Act-1 fight played with the coach | 16–22 h | $0 |
| **P1: Combat oracle + first regret report** | 3–8 | SemAction/target IS-MCTS with availability counts, Gumbel root, recall-checked candidates, two-stage racing and verdicts, B8<br>Track D Tier A: 1,000 silver + 200 gold (L0); Track I: 400 silver<br>Regret table for B0–B8 and the owner<br>Dashboard v1<br>**P1a (week 5): `spireline review`**, which re-labels every decision in the owner's coached-fight logs with Spireline's QUICK/DEEP oracle and publishes a per-fight report | Label-noise floor < 0.3 L0 points<br>Budget-×4 stability ≥ 95%<br>Screening and candidate recall ≥ 98%<br>Gumbel@n regret ≤ PUCT at matched wall-clock<br>F1 passes on Defect A0 tapes<br>F5 ≥ 98% in Act 1<br>P1a shipped by week 5 | 30–40 h | $5–20 |
| **P2: Run value + macro advisor (Act 1)** | 9–16 | Patches for L3/L7/L8 as needed<br>Act-1 V_run in the L1 ladder<br>Map DP, shop, rest, event and card-reward search<br>Tier B silver 300 + gold 80<br>Local advisor page (combat + macro, unit-labelled, quiz, optional explainer)<br>Expert check set (if recruits exist)<br>**E1 provisional verdict**<br>Upstream map-row fix requested | Macro search beats rules macro on Act-1 boss-kill rate (exact McNemar, p < 0.01, 1,000 fresh E-seeds) with mean floor as secondary<br>Tier-B regret reported per decision type<br>V_run Brier skill > 0 vs base rate and V0 (CI excludes 0)<br>A pre-registered share of supported live positions DECISIVE or CLOSE at the §1.4 ε. Set after the pilot measures σ; initial target 50% for QUICK combat | 35–50 h | $15–50 |
| **P3: Agent + real-game proof** (RL-1/RL-2 as gated by the flywheel) | 17–26 | Live runner with watchdog<br>Referee parity on Acts 2–3<br>ExIt generations if gated (RL-2 beyond Act 1 only after F3/F4)<br>Seeded live parity runs (171–343)<br>Per-decision FableBot comparison<br>**E1 final verdict** if RL-1 ran | Parity TOST passes at ±5 pp<br>If RL ran: generation k beats generation 0 on the F pool (paired mean floor, CI excludes 0)<br>Headline vs FableBot reported per §7.4 | 30–50 h + 23–86 h unattended live time | $20–80 |
| **P4: User's level** | Months 7–10 | A10 (double boss; confirm r33hab `m2-asc` is merged); a second track character; advisor polish; re-grading the owner's past v0.107.1 runs (deck reconstructable from `.run` files; feasibility UNVERIFIED) | A10 regret table; A10 battery on the owner's most-played character beats that character's own A10 win rate, with lower CI above it, on 2,000 seeds | 40–60 h | $30–150 |
| P5 (optional, gated) | Later | Port to the next patch; single-decision LLM bandit with reward = −oracle regret | Only if E1 passes and the flywheel calls for it | Open | Open |

Through P3 that totals about 120–170 h of the owner's time and about $40–150. That is well inside $500 for the first 3 months (P0–P2 ≈ $20–70).

**Data flywheel: the ledger decides what gets funded next.**

| Signal | Fund | Not this |
|---|---|---|
| UNCERTAIN > 50% on QUICK combat, or DEEP needed on > 25% of positions, or a battery takes > 8 h | RL-1 (ExIt prior) | A bigger LLM |
| Tier B silver disagrees with gold on > 20% of decisive positions, or V_run fails the Brier-skill gate | RL-2 (DMC V_run) | Hand-tuned shaping |
| UNSUPPORTED > 10% of live decisions, or F5 < 95% | Capture sprint, upstream fixes, referee | An LLM coverage fallback |
| Regret concentrated on `continuation_sensitive` long-horizon setups | E1 LLM-prior arm | n/a |
| Security review finds unexplained native, network or file-write behaviour | Fallback substrate (§3.6) | Running it anyway |
| Two consecutive phase gates fail | Stop; write up; keep the advisor | Scope growth |

**Explicit non-goals:**
- our own simulator or rules port;
- end-to-end PPO, GRPO or LLM fine-tuning as the policy;
- co-op;
- Daily runs, leaderboards, or any bot play on the vanilla profile;
- the v0.111 beta, or chasing patches before upstream ports;
- all five characters at once;
- clairvoyant or save-scum search as a result;
- training on unscrubbed replays;
- publishing the decompile, emulator data tables, game DLLs or spire-coach code;
- cloud machines holding game DLLs;
- monetisation;
- claims of optimality (statistical bounds only), superhuman A10 play, or P(win) where the unit is not P(win).

---

## 9. Risks and mitigations

| Risk | Likelihood / impact | Mitigation |
|---|---|---|
| **Supply chain**: emulator, mod and coach from one 5-day-old, 0-star account with rewritten history; spire-coach unlicensed; native code and an in-game DLL | Medium / high | §3.6: provenance diff, Claude code review, source-only builds, separate macOS user, network deny, manual mod install, documented fallback substrate |
| **Hidden-information leak through the mod's default payload** (`move_id`, `ai_fields` behind non-identifying intents) | High (as shipped) / high | Allow-list firewall, AI-state particles, L6 canaries, L8, positive control L+; gold labels exclude `ai_state_assumed` |
| Emulator clones inherit an enemy's already-chosen current move | Likely / high for labels | L8 on emulator clones; patch to re-roll non-identifying current moves on `resample_hidden`; offered upstream |
| Track I character poorly captured (Ironclad 29/85) | Certain / medium | Track D (Defect 88/88) is primary; Track I restricted to captured cards; UNSUPPORTED for uncaptured cards; A11 transfer ablation |
| Run-level resampling misses pre-generated content (encounter sequences) | Medium / high: macro labels become clairvoyant | L2/L3 block macro labels; fix in the clone path (patch queue, upstream PR) |
| Emulator Act 2–3 maps (17 rows vs 16/15) contaminate V_run | Certain / high | RL-2 and L2 labels gated on F3/F4; Act-1 head first; map fix as an upstream request with an estimated 8–20 h port |
| V_run mispricing spreads everywhere (self-play bootstrap) | Medium / high | Value ladder with explicit units; Brier-skill gate; currency-stability tags; PDL check; live parity anchor; labels regenerated per generation |
| Self-play finds almost no wins early (0/1,999 at A9) | High / medium | U_λ warm start; A0 first; mean floor and boss kills as primary promotion metrics; relative gates |
| Continuation bias inside one policy family | Medium / high | Second-family π_ref (B8) on 200 positions; `continuation_sensitive` tags; expert check set; user regret stated relative to π_ref |
| Winner's curse, optional stopping, label noise, small-N self-deception (FableBot's "25.6% over 39 runs" has CI 14.5–41%) | High / high | Cross-fitting; time-uniform CSs; noise floor; cluster bootstrap; pre-registration; frozen test split; Wilson everywhere |
| Overfitting to seed batteries | Medium / high | Fresh E-block per generation; F touched once per gate ([Strens & Moore](https://www.jmlr.org/papers/v3/strens02a.html)) |
| Emulator vs live gap hidden by low power or search nondeterminism | Medium / high | TOST with a declared margin; deterministic single-threaded parity search; decision vs outcome agreement; per-step F5; F7 exploit audit |
| Compute estimates wrong (M4 Max → Mac scaling unmeasured) | High / medium | Day-4 measurements; week-3 pilot; pre-registered cut rule (§4.3); optional cloud for Tier B gold |
| Live-time budget conflicts with overnight training | High / medium | Parity n set from measured discordance; 600-run headline dropped; scheduled live sessions; ≤ 3 workers while live |
| Single-maintainer upstream (r33hab repos created 2026-10-05; Zamiell idle since 2026-06-04) | Medium / medium | Pin `b745217`/`5a63f92`; all our code in `spireline/`; small patch queue; archived checkouts; evangambit fallback |
| Next patch (alternate Act 2 + 6th character) breaks everything | High within a year / high | Archived build, `versions.lock`, freeze policy, version-tagged labels |
| Live game hangs, 13.3 GB after ~3 h (Windows), time scale resets on cinematics | High / low | Watchdog: fingerprint polls, kill and relaunch after a 30 s stall, relaunch every 15 runs, settle gate. The r33hab mod re-asserts time scale through hit-stops |
| Modded-profile unlocks or Seeds epoch missing on the owner's Mac; Steam Cloud overwrites copied saves | Medium / medium | Check in week 2. Steam Cloud off, backups first, game's own modded profiles. Copying vanilla progress only by hand after review (not via spire-coach) |
| Unattended overnight runs (sleep, thermal throttling, lid) | Medium / low | `caffeinate`, AC power, lid open, `pmset` thermal logging, checkpoint and resume, `nice 10` |
| Legal / ToS: decompiling (Steam Subscriber Agreement §2.G); bots and stats (§4.C); Mega Crit content policy | Low / high | Decompile only the owner's own install, locally; never redistribute; no Daily or leaderboards; modded profiles only; no monetisation ([policy](https://www.megacrit.com/content-policy/)). Not legal advice |
| Vendor risk: Jev pricing, slow mode, terms; privacy | Medium / low | Off by default; Haiku as the Claude-native option; pinned snapshot; no distillation until terms are read; only firewall-filtered game state is sent |
| Claude Code writes plausible but wrong code | High / medium | Reproduce published numbers before extending (c = 0.1 result, test counts); stats module unit-tested against §7.3 and by CS coverage simulation; tests on captured live states; never simulate rules ourselves |
| Hobby bandwidth, scope creep | High / medium | Every phase ships something usable (P1a by week 5); kill criteria; flywheel funding rules |

---

## 10. Week-1 plan (about 16–20 h; spilling into week 2 is planned)

Third-party checkouts go in a separate folder (spire-coach expects `~/Documents/git/`). Spireline lives in this repository. Python environments are per-project (uv `.venv`, and `a dedicated venv`), never the base Anaconda install.

1. **Day 0: protect the baseline (1 h).**
   - In Steam, set the game to update only on launch, and turn Steam Cloud off for the game.
   - `ditto` the `SlayTheSpire2.app` bundle to `~/Games/sts2-0.107.1-23811903/`.
   - Back up the saves folder.
   - Record the build id and `sts2.dll` sha256 in `versions.lock`.
   - Create a standard, non-admin macOS user `spireline` in System Settings.
   - Optionally install LuLu.
2. **Day 1: security review (3–4 h, mostly Claude reading; nothing is built or run).**
   - Shallow-clone, at pinned SHAs:
     - r33hab/sts2@`b745217`, r33hab/STS2MCP@`5a63f92`, r33hab/spire-coach@`dev` (record the SHA);
     - evangambit/sts2@`37e4264`, Gennadiyev/STS2MCP main, cicero225/STS2MCP.
   - Run the §3.6 tree diffs and code reading. Write `docs/SECURITY_REVIEW.md`.
   - **Go/fallback decision.**
3. **Day 2: build the emulator as user `spireline` (2–3 h).**
   - Install the .NET 9 SDK to `~/.dotnet`, plus `uv` and Python 3.12.
   - Copy the DLLs needed for the decompile from the owner's own install.
   - Following [HANDOFF](https://github.com/r33hab/sts2/blob/spire-coach/HANDOFF.md):
     - regenerate `decompiled/` with `ilspycmd` 8.2.0.7535;
     - run `bash scripts/build.sh osx-arm64`, `dotnet test` and the Python tests.
   - **Accept:** the counts the runner reports are recorded in `versions.lock`, with no failures beyond the documented one. For comparison, FINDINGS states 4801/4801 C# and 526/527 Python; HANDOFF states 3,650 + 1 skipped and 492 + 6 skipped.
4. **Day 3: live coach (1–2 h).**
   - Build `STS2_MCP.dll` from the reviewed source, with the game closed.
   - Copy the DLL and manifest into the mods folder by hand (§3.6 step 4).
   - Launch via Steam, tick the mod in the game's Mods screen, and pick a modded profile.
   - Set `SPIRE_COACH_TOKEN` from `STS2_MCP.conf`.
   - With outbound network denied, run `spire-coach doctor`, then `spire-coach coach --mode quiz`.
   - Play one Act-1 Ironclad fight and keep the run log as the first live fixtures.
   - **Accept:** grades appear; any "(unreliable)" warnings are noted.
5. **Day 4: measure the Mac (2 h, mostly unattended, under `caffeinate`).**
   - Run `rl/agent_probe.py`, `rl/mcts_probe.py --section invariants`, `rl/combat_mcts.py --verify`, `rl/run_train/probe_throughput.py`, and a 20-run A0 Defect smoke test.
   - Write the results to `bench/m1pro-2026-10.json` and replace the §3.4 estimates.
   - **Sanity reproduction:** c = 0.1 vs c = 1.4 over 240 fights each.
   - **Accept:** sims/s/core recorded; P(death) ≈ 0.09 vs 0.18 within CI; 0 unretried crashes. If the c result doesn't reproduce, stop and debug before anything else.
6. **Day 5: scaffold and firewall (2–3 h).**
   - Create the Spireline repo with `api.py`, `infoset/schema.py`, `infoset/firewall.py` (allow-list) and an `ai_belief.py` stub.
   - Write `test_leaks.py` with L1, L4, L6 (canaries on recorded payload fixtures), L8, the L+ positive control, and the non-circular L2 encounter-variety test.
   - Run it against the emulator and the day-3 payload fixtures.
   - **Accept:** results recorded. A red L2 or L8 is filed upstream with a repro seed and blocks the corresponding labels, as designed.
7. **Day 6: coverage, stats and RNG check (2–3 h).**
   - Sample 2,000 A0 combat positions per track from rules self-play. Compute **F2a** from `docs/divergence-catalog.md`.
   - Write `eval/stats.py`: Wilson, exact McNemar, TOST, cluster bootstrap, power, empirical-Bernstein and betting confidence sequences.
     - Unit-test against §7.3 (1,094; 469; 343; 16.7–25.3%).
     - Simulate CS coverage under optional stopping (≥ 95%).
   - Run **F9** on 20,000 emulator seeds and on the owner's v0.107.1 `.run` files.
8. **Day 7: pre-register and decide (1–2 h).**
   - Write `eval/prereg/phase1.yaml`: seed-block hashes, Tier-A sizes, ε table, recall thresholds, the cost-cut rule.
   - Start `docs/DECISIONS.md` and `LOG.md`.
   - Launch the overnight B0/B1 1,000-seed Defect batteries, which also give the first discordance and run-time-per-floor estimates.
   - **Go/no-go:** review passed; emulator builds and meets the speed target; c result reproduced; live coach works; leak results known.
   - If the emulator won't build or run on the Mac, fall back to the mingxuan sts2-cli fork as the substrate: room save plus prefix-replay search at Gumbel n = 8–32. spire-coach's live panel is unaffected.

**Week 2 spikes:**
- modded-profile Seeds epoch and unlocks;
- `strategy` coverage of macro screens;
- FableBot on macOS;
- whether the archived app copy can be launched modded;
- the Defect F1 tape-capture plan.

**Week 3 starts P1:** the Gumbel port with SemAction keys and availability counts, then the oracle, then the Tier-A pilot of 100 positions to measure σ, survivors per position, cost and the label-noise floor.

---

## Carried-forward UNVERIFIED items

- Mac per-core speed relative to r33hab's M4 Max. All Mac throughput, label-cost and live-run-time figures are extrapolations until day 4 and the week-3 pilot.
- Whether the game's intent tooltips name the move behind non-attack intents (L8). Whether the game displays non-attack magnitudes that `combat_tokens` encodes.
- Whether run-level `resample_hidden` redraws content generated at act start but not yet seen (L2/L3). Whether it re-rolls an already-chosen current enemy move (L8). Which monsters have AI state not deducible from history (L7).
- That `sts2_gym.live.convert`, `CombatSnapshot.cs`, `deckfights.py`, `rl/prior_loop` and the engine service's `analyze`/`check`/`strategy` methods work at `b745217`. They exist; none has been run by us. Whether `strategy` covers every macro screen.
- Emulator Act-1 bit-exactness at A0, and for Defect run traces. Catalogue captures are A8 custom-mode runs.
- Whether the owner's modded profile has the Seeds epoch and the needed unlocks. The modded profile spire-coach describes as "fully unlocked" is the author's machine.
- Launching a separate modded copy of the app on macOS; `sandbox-exec` behaviour on Darwin 24.6.
- sts2-cli throughput on a Mac, and the cost of its room-replay "clone".
- Live-game decision rate at 3x and memory growth on macOS (both measured on Windows).
- FableBot's Python policies running on macOS against live-format states. Whether r33hab's rules macro is character-general.
- A linux-x64 NativeAOT build in practice (`build.sh` supports it) and CCX43 pricing (third-party trackers).
- Whether r33hab's A10 work (`m2-asc`) is merged. Whether `deckfights.py` is complete at `b745217`.
- Haiku 5.5 latency; TypeSafe's distillation terms; Spire Codex data terms.
- Re-grading the owner's past runs from `.run` files without leaking their seeds.
- Whether strong human players can be recruited for the expert check set.

**Primary sources re-checked today (2026-10-10):**
- GitHub API for r33hab/sts2, r33hab/STS2MCP and r33hab/spire-coach: creation times 2026-10-05T17:36:11–20Z, `fork:false`, 0 stars, licences MIT / MIT / none, 730 commits with 467 attributed to evangambit. Also evangambit/sts2 (created 2026-08-15) and cicero225/STS2FableBot (last push 2026-10-03).
- r33hab/sts2 at `b745217`: [divergence-catalog](https://github.com/r33hab/sts2/blob/spire-coach/docs/divergence-catalog.md) (capture table, 182 uncaptured cards, "Open: None", custom-mode A8 captures); [FULL_RUNS](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/FULL_RUNS.md) (gen 0 0/1,999; 17-row maps); [DESIGN](https://github.com/r33hab/sts2/blob/spire-coach/rl/run_train/DESIGN.md) (M4 Max; B1 8.0%; 3,014 runs/h; 1,851-wide input; β = 0.3); [FINDINGS](https://github.com/r33hab/sts2/blob/spire-coach/rl/FINDINGS.md) (c-sweep, +2.0/+0.6 HP, 0.320 → 0.105 nats, batch timings, test counts); [HANDOFF](https://github.com/r33hab/sts2/blob/spire-coach/HANDOFF.md) (other test counts); [run_env.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/run_env.py); [enemy_ai.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/live/enemy_ai.py); [strategy.py](https://github.com/r33hab/sts2/blob/spire-coach/src/sts2_gym/live/strategy.py); [EnemyAI.cs](https://github.com/r33hab/sts2/blob/spire-coach/src/Sts2Emulator/Core/EnemyAI.cs).
- r33hab/STS2MCP at `5a63f92`: [McpMod.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.cs) (schema-4 comment, localhost-only listener); [McpMod.StateExtras.cs](https://github.com/r33hab/STS2MCP/blob/spire-coach/McpMod.StateExtras.cs) (default `move_id`, `state_log`, `ai_fields`; hidden-only `move_follow_up_id`); TimeScale and CustomRun files.
- [r33hab/spire-coach README](https://github.com/r33hab/spire-coach): scope, value function, grades, defaults, installer commands, save profiles.
- Anthropic's model table (cached 2026-10-06) for Haiku 5.5 and Opus 5.5 pricing and thinking rules.

The sample-size, MDE and Wilson figures in §7.3 were computed for this document. Downloaded spire-coach spec copies are in `<scratch>`. Repo clones read for this revision are in `<scratch>` and `<scratch>`.

---

## Changes after review

**Critical issues**
1. **Live payload leak.** Verified in code: schema 4 ships `move_id`, `state_log` and every primitive `ai_fields` entry by default. Fixed with:
   - an allow-list firewall;
   - a likelihood-weighted particle belief over AI state and the current move;
   - a precise definition of `ai_state_assumed` (history-only reconstruction, never the payload, excluded from gold);
   - new leak test L8, canaries on `move_id` and `ai_fields`, and a positive control.
2. **Supply chain.** Verified: creation timestamps, no fork lineage, rewritten history, no licence on spire-coach. Added §3.6:
   - provenance diff and code review before any build;
   - source-only builds, a separate macOS user and network deny;
   - manual mod install, never spire-coach's installer;
   - a licence request and a documented evangambit + cicero225 fallback.
3. **Label costs.** Recomputed from r33hab's per-decision measurements:
   - silver now uses PLAY@60 continuation (2.5–22 core-min); gold uses @300 (14–98 core-min);
   - Tier B is split into a cheap silver (V_run + deck fights) and an act-rollout gold of 80 positions;
   - QUICK combat and macro are explicitly Q^{tempo} and "V_run + deck-fights", not Q^{π_ref};
   - a pre-registered cost-cut rule was added.
4. **Self-play cost.** Removed π_ref Monte Carlo verification from self-play (capped tempo deck-fights only). FightNet is cached by (deck hash, encounter class) and refit at act boundaries. Generation time is modelled per floor reached and capped by wall-clock.

**Major issues**
- ε now depends on mode and level, with a single precision definition (95% half-width). The 70% gate is replaced by a pilot-calibrated, pre-registered gate.
- Screening currency mismatch: regret bounds are now scoped to survivors; screening recall and candidate recall are measured with a ≥ 98% requirement; the static top-16 cut is replaced by tempo pre-scoring of every line.
- Optional stopping: replaced fixed-n racing intervals with time-uniform confidence sequences (empirical-Bernstein and betting), with simulated coverage tests.
- Power: assume σ = 3–5 L0 points; MDE ≈ 0.4–0.7 at n = 400; target effects ≥ 0.5–1 point; blunder-rate McNemar added.
- V_run gates are now Brier skill and log-loss vs base rate and V0, with ECE only over bins with ≥ 30 wins. Units are printed on every number. L0 is never shown as pp of P(win); L2 is "U_λ units" until π_ref wins ≥ 10%.
- Continuation bias: added a second-family π_ref (B8) on 200 positions, `continuation_sensitive` tags, and user regret stated relative to π_ref.
- Promotion: a fresh E-block per generation, α = 0.01, mean floor and boss kills as primary metrics, wins co-primary only above 10%.
- Character: decided now. Track D Defect is primary; Track I Ironclad Act 1 (captured cards only) serves FableBot and spire-coach. The cross-character 20.7% stretch goal is dropped.
- Live budget: computed (171–343 parity runs ≈ 23–86 h of live time). The 600-run headline is dropped. Seeds-epoch and unlock checks were added. Custom-mode seeding is supported by the mod and the catalogue's captures.
- Map rows: verified 17 vs 16/15. RL-2 training beyond Act 1 is gated on F3/F4, the Act-1 head comes first, and the map fix is an estimated upstream port.
- PDL check: now primarily combat-level with L0; the run-level version is sampled and exploratory.
- IS-MCTS: availability counts (ISUCT) added; unavailable actions are treated as missing in completed-Q.
- Monster-AI belief: changed from uniform to likelihood-weighted particles, with analytic unit tests.
- E1: provisional verdict in P2 against uniform and heuristic priors; final verdict in P3 against the net prior.

**Minor issues**
- Gumbel m = clamp(⌊n/8⌋, 4, 16), with c_puct and value_scale re-tuned in A3.
- Test-count acceptance is now "matches counts at pin". Both conflicting in-repo counts are cited.
- The divergence catalogue is described accurately (~449 closed, none open, warned as a bad proxy).
- Self-play time is modelled by floor reached.
- Parity search is deterministic, and decision agreement is reported separately from outcome agreement.
- Potion-heavy positions are tagged `currency_sensitive`.

**Omissions filled**
- B8 Bottled-style baseline.
- Expert check set as an external anchor.
- L8.
- Sandbox plan.
- Live-time budget.
- Seeds-epoch check.
- Anytime-valid statistics.
- Low-win-rate promotion power and seed rotation.
- Overnight power management.
- F9 empirical RNG correlation test.
- P1a `spireline review` as a deliverable of Spireline's own by week 5.

**Claims verified and corrected**
- Card capture coverage, gen-0 figures, B1, 3,014/3,774 runs/h, +2.0/+0.6 HP, 0.320 → 0.105 nats, 0.073 nats, FightNet NLL and 167k–935k parameters were all verified against the repo.
- Run input corrected to 1,851 wide, including H.
- Batched prior timing corrected to 0.7–0.9 ms per call.
- Measurement machine identified as an M4 Max.
- `set_time_scale` and the `linux-x64` build target confirmed present.
- spire-coach features verified from its README.

**Claims removed or flagged**
- "About 150 live runs/day" removed.
- Remaining Mac speeds, the A0 exactness of the emulator, intent-tooltip content, modded-profile unlocks and the other items are listed under UNVERIFIED.