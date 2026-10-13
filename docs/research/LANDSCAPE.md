# Comparative critique: existing StS2 and StS1 approaches, judged on whether they find the best play

## Bottom line

1. **Nobody has measured decision quality.** No StS2 project computes per-decision regret against a reference that respects what the player can see. The closest thing is evangambit's paired P(death)-per-fight measurement on an emulator, and it only covers single combats. Everything else reports win rate or floor reached, mostly at N = 3 to 50.
2. **Only two approaches have honest StS2 results that are statistically meaningful.**
   - **STS2FableBot:** turn search against the visible board, hand-written macro scoring, real game. 20.7% at A0 Ironclad over 343 runs (CI 16.7 to 25.3%). It is coded by Claude with a human owner directing the work, which is exactly the owner's way of working. It is under-weighted in the dossier and is the template to beat ([README](https://github.com/cicero225/STS2FableBot), read 2026-10-10).
   - **evangambit/r33hab:** determinized MCTS on the emulator, measured over 240+ fights per setting ([FINDINGS](https://github.com/evangambit/sts2/blob/main/rl/FINDINGS.md)).
3. **End-to-end RL has a documented ceiling and a documented money pit.**
   - On StS1, 3.55B decisions bought 15.4% at A0 Ironclad ([Slay_RL](https://github.com/DavidSnoble/Slay_RL/blob/master/docs/schema_v4_handoff.md)). That is below Bottled AI's honest 20% from search and rules.
   - On StS2, Spirebird's engine is about 2M games in, and its latest 10,000 training runs had 0 wins (Wilson upper bound 0.04%) ([engine-stats](https://spirebird.com/engine-stats.html)).
4. **Jev is not compute.** It is a closed, hosted classifier at $0.00046 per decision. Its headline benchmark (27/30 vs 29/30) measures nothing about best play: Fisher p ≈ 0.61, effective n = 10 fixtures, weights tuned on the test set. Its end-to-end record is 1 win in 182 runs upstream and 0 in 9 in the fork.

**Scoring scale for the matrix:** 0 = absent or harmful, 3 = strong, judged against the goal of finding the best play. Column 8 is scored so that 3 = low legal risk. Column 5 is scored so that 3 = cheap and fast.

---

## 1. Critique matrix: decision-makers

| Approach (exemplars) | 1. Measures decision quality? | 2. Statistical rigour | 3. Hidden info / stochasticity | 4. Long-horizon credit | 5. Cost & throughput | 6. Fidelity & version drift | 7. Reproducibility | 8. Legal / ToS (3 = low risk) | 9. Reusable |
|---|---|---|---|---|---|---|---|---|---|
| **A. Hand-rule bots, live game** (JoeB08 Silent, spirecomm, brmarcosbr greedy) | 1: damage/floor and depth; no oracle | 1: 15–20-run sets with CIs; overlapping CIs treated as no difference | 2: visible state only; no belief model | 1: author's priors | 2: free per decision; game caps it at about 1 decision/s | 2: real game; mods break every patch | 1: JoeB08 run logs withheld | 3 | Watchdog, settle gate, snapshot-replay refactor check |
| **B. Turn search + hand evaluator, live game** (Bottled AI on StS1; **STS2FableBot**) | 1: logs scores and rationale per decision, can replay offline; no regret | 2: 343 runs, CI 16.7–25.3% (FableBot); about 50 per character (Bottled) | 2: no peeking; within-turn search; no explicit chance nodes | 2: FableBot's map DP prices elites from its own fight history; GBM P(win) heads in progress | 2: cheap; about 280 runs/day at 3x is the real-game ceiling | 2: outcomes are real; its own Python board model is fixed "one death tape at a time" | 2: MIT; config hash in every run log | 3 | **3: the baseline to beat and the architecture template** |
| **C. Raw LLM agents** (STS2MCP reference agent, CharTyr agent, TokenSpire2, AGI-Eval, Orak) | 0 | 0: N = 3–10; AGI-Eval used one seed for every model | 1: sees visible state; does its own arithmetic | 1: over-weights the current turn; no attrition plan | 0: 17–93M tokens/run; 8.5–9.9 min/floor | 2: real game, old builds | 1: model churn, non-deterministic | 3 | 1: failure taxonomy |
| **D. Memory-augmented LLM** (AgenticSTS, SpireMind) | 1: Opus LLM-judge on about 12 cases; A/B gate only observes | 2: honest Wilson and Fisher, but N = 10 per cell (p ≈ 0.37) | 1: no belief model; plan checks are base-damage sums | 1: cross-run memory; A7 3/4, A8 0/18 | 1: about 5k-token prompts, about 80 min/run | 1: real game but pinned to v0.103 | **3: code, data and scripts public** | 2: AGPL mod fork | **3: 298 trajectories, 3,214 combat episodes, schemas, stats scripts** |
| **E. Jev factored decisions** (jev-the-spire, jev-the-spire2) | 0: string match on the first action, 10 fixtures, "not optimality" | 0: effective n = 10; ±3/30 noise; tuned on the test set | 1: good visible-state discipline; no stochastic reasoning | 0: myopic; weight fitter refused (5 deaths in 476 turns) | 2: $0.00046/decision, but network-bound with bimodal latency (0.3 s / 7–16 s) | 2: live game; v0.111 needs an unmerged fork | 1: closed, non-deterministic, vendor in early access | 2: distillation terms unknown | 2: waste veto, factored nouls, candidate generator |
| **F. GRPO-tuned LLM** (sts2-agent Track 1) | 0: no results | 0: training loop never run | 2: sorted piles, server-side seeds, 200/40 train/eval seed pool | 0: per-combat shaped reward | 0: est. $1.0–1.4K for combat only; about 40x that for full runs | 1: pipeline still on an obsolete approximate sim | 1: licence NOASSERTION; private dataset | 1: Docker image bakes in game DLLs | 2: env pool, game service, bug write-ups |
| **G. End-to-end RL** (Slay_RL StS1; Zaaacqwq PPO StS2; zhiyue PPO; Spirebird) | 0: win/floor only | 2: Slay_RL is excellent (10k paired seeds); the rest weak or closed | 2: observation-only policy, masked | 2: full-run Monte Carlo returns, the only family that tries; needs about 10^9 decisions | 0 on StS2: real engine 20–170 steps/s | 1: fast StS2 sims unvalidated | 2: Slay_RL open; Spirebird closed | 2 | 2: action masks, paired evaluation, wins-outrank-losses telemetry |
| **H. Clairvoyant search** (sts_lightspeed ScumSearch, scumthespire, sts-rl-agent combat) | 0, and invalid as a reference | 1: 50 seeds; 7/50 vs 3/50, p ≈ 0.32 | **0: sees RNG and draw order** | 1: learned macro layer worth about 11 floors | 3: about 2M decisions/s (StS1) | 0 for StS2: StS1 only | 2 | 3 | 1: upper bound only; distilling it is a trap |
| **I. Honest determinized MCTS, StS2 emulator** (evangambit / r33hab `rl/`) | **2: P(death) and HP per fight, paired** | **3: 240+ fights per setting, SEs, common random numbers** | **3: `clone(resample_hidden=True)`, CRN** | 1: combat-local value; run-level search only +1.7/+4.6 floors over random | **3: about 14k steps/s, about 1.4k sims/s, Mac arm64** | 1: reimplementation, bit-exact mainly in Act 1; pinned to v0.107.1 | 2: needs a local decompile | 1: built from decompiled source | **3: search core and oracle** |

## 1b. Critique matrix: environments (the simulators that rows A–I sit on)

| Backend | Fidelity | Throughput | Rollback / clone | Information hygiene | Version | Legal | Right role |
|---|---|---|---|---|---|---|---|
| **STS2MCP + forks** (live game) | Exact | 30–40 decisions/min at 1x, 61.5 at 3x ([LOG](https://github.com/cicero225/STS2FableBot/blob/main/LOG.md)); hangs at about 13 GB after 3 h | Room-level only, seconds per reload | Draw pile sorted ([StateBuilder](https://github.com/Gennadiyev/STS2MCP/blob/main/McpMod.StateBuilder.cs)), but `/compendium` leaks the seed ([Compendium.cs](https://github.com/Gennadiyev/STS2MCP/blob/main/McpMod.Compendium.cs)) | Upstream broken on v0.111 ([#131](https://github.com/Gennadiyev/STS2MCP/issues/131)); cicero225 v107/v111 forks work | MIT; low | Final evaluation and live advisor |
| **CharTyr/STS2-Agent** | Exact | Same ceiling | None | Legal-action list; grouped stacks | Validated on v0.111 | AGPL | Alternative evaluation backend |
| **sts2-cli** (upstream / mingxuan fork) | Real logic, but stubs cause silent bugs: Gardener runaway enemy phase ([bug](https://github.com/mingxuan-he/sts2-agent/blob/main/docs/BUG_gardener_runaway_phase.md)) and Kaiser Crab false boss win ([repro](https://github.com/mingxuan-he/sts2-agent/blob/main/docs/astra-kaiser-crab-reproduction.md)) | About 20 steps/s per process; 140/s with 16 workers ([Zaaacqwq](https://github.com/Zaaacqwq/SlayTheSpireRL/blob/main/plan/timeline.md)); Mac figure UNVERIFIED | Room-level save plus prefix replay | `set_draw_order` and `get_piles` expose hidden state, so they must be masked | v0.107.1 and v0.111 | Copies the owner's own DLLs; cloud use is grey | Real-engine rollouts, spot-check labels, differential oracle |
| **r33hab / evangambit emulator** | Reimplementation. Combat starts exact in 32 live captures, Act-1 selection 88/88; Acts 2–3 less verified ([HANDOFF](https://github.com/r33hab/sts2/blob/main/HANDOFF.md)) | 58–72 µs/step | **17–70 µs clone with hidden-state resampling** ([agent-interface](https://github.com/r33hab/sts2/blob/main/docs/agent-interface.md)) | Built in | v0.107.1 | Derived from decompiled source | Search engine and label factory |
| zhiyue / Akirakato / StS2Sim | Unvalidated / patch 103.2 / no enemy turns | Fast | — | — | Stale | Varies | Don't build on these |
| sts_lightspeed (StS1) | RNG-accurate | About 2M decisions/s | Full clone, which makes search clairvoyant | Leaks | StS1 only | MIT | Conceptual reference only |

---

## 2. Approach-by-approach critique

### A. Hand-rule bots on the live game

They need no training, are interpretable, and are honest by construction. They never define what a good decision is beyond the author's taste.

The most useful thing here is JoeB08's evaluation hygiene ([repo](https://github.com/JoeB08/Slay-the-Spire-2-Automatic-Bot)):
- changes are measured over sets of 15–20 runs with 95% CIs, and overlapping CIs are treated as no difference;
- damage taken per floor "moved first" both times a change made things worse, even while average depth looked fine;
- a decision-snapshot replay proves that refactors leave behaviour unchanged.

At 15–20 runs, though, the CIs are about ±20 points wide, so almost every change reads as no difference. JoeB08's own KNOWLEDGE.md documents the cost of the live game: room-level restore only, and a relaunch resumes the fight with enemies at full HP. brmarcosbr has effectively one validated fight (7 turns, 35 actions, 0 rejections) and no win rate ([dev.to](https://dev.to/brmarcosbr/i-made-an-agent-play-slay-the-spire-2-on-its-own-and-what-unlocked-it-was-the-game-saying-no-2hc2)). Its useful idea is turning the game's refusals into state the agent can learn from.

### B. Turn search plus an evaluator (Bottled AI, STS2FableBot): the strongest honest family

**Bottled AI (StS1)** searches up to 11,000 orderings of the current hand and scores end states on about 40 weighted features. It wins 20/40/33/52% at A0 with Ironclad/Silent/Defect/Watcher over about 50 runs each, and it has beaten the Heart ([winrates](https://github.com/xaved88/bottled_ai/blob/main/docs/winrates.md)). Its authors state the Ironclad CI themselves (8.9–31.1%; my Wilson interval is 11.2–33.0%) and estimate about 1,000 runs per character for ±3%.

**STS2FableBot** (MIT, created 2026-06-12, last push 2026-10-03, Windows) is the most relevant prior art for this user. I confirmed the details from its README:
- combat is a DFS over this turn's play sequences against a model of the visible board, with a small forward model for kill deadlines, setup windows and race-vs-defend;
- map routing is a dynamic program that prices elites and bosses from the bot's own fight history;
- drafting, shops, events, rest sites and potions use hand-written scoring;
- learning is limited to offline gradient-boosted P(win) heads;
- there is no end-to-end RL;
- most of the code is written by Claude (Fable 5.1) while the human owner directs.

Results:
- 20.7% A0 Ironclad over 343 runs (CI 16–25%), roughly the "dedicated-player average about 20%" it cites;
- 19.4% at A1 over 175 runs;
- about 4,200 logged runs, all on v0.107.1, the same build as the owner's install and the emulator.

Its most transferable empirical finding: "Arriving healthy turned out to be the strongest single predictor of beating a boss or an elite." That is a ready-made first proxy for a run-level value function.

Critique:
- **Decision quality is still not measured.** Every decision is replayable against its logged state, but nothing scores those decisions against a reference.
- **The board model is hand-built and fixed one death at a time.** That is a fidelity debt.
- **No chance nodes.** Draw-dependent turns risk the strategy-fusion problems described in the theory dossier ([Long et al.](https://ojs.aaai.org/index.php/AAAI/article/view/7562)).
- **Throughput is capped by the real game.** About 35 runs per 3 h at 3x.
- **It reports a small-N result next to the solid ones.** "A1 25.6% with the boss-campfire rest rule (39 runs)" has a Wilson CI of about 14.5–41%, so it is indistinguishable from 19.4%.

**Verdict:** this is the blueprint policy the new framework should copy or wrap. Any proposed method has to beat it on paired seeds.

### C. Raw LLM agents

**Results:**
- [AgenticSTS re-runs](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/docs/experiments/competitor_comparison/RESULTS.md): STS2MCP's reference agent 0/5 and CharTyr's agent 0/5 (Wilson 0–43% each), mean floors 17.6 and 5.6, at 93M and 17M tokens per run.
- [TokenSpire2](https://github.com/collinzrj/TokenSpire2): 0 wins in every row; Opus 4.6 averaged floor 17.2 over 10 runs.
- [AGI-Eval](https://gitcode.csdn.net/6a01b6b80a2f6a37c5a944ee.html): 0 wins across 5 frontier configurations, all on one fixed seed. Its "improvement over restarts" is partly the memory learning that seed.
- [Orak](https://arxiv.org/abs/2506.03610) (StS1): 51.9 ± 31.9 on n = 3.

None of these define decision quality, and their sample sizes cannot separate anything from zero.

**Real failure modes:**
- [CharTyr](https://github.com/CharTyr/STS2-Agent)'s HTTP 409 invalid-action cascades;
- STS2MCP prompts growing to about 527k tokens;
- [ai-spire](https://github.com/biolbe1230/ai-spire)'s silent 15 s fallback to rules, which contaminates any "LLM" result.

The controlled MiniStS evidence is the useful part ([Bateni & Whitehead](https://dl.acm.org/doi/fullHtml/10.1145/3649921.3650013)). Depth-3 search beat GPT-3.5 on arithmetic-heavy lines (Batter-Stimulate: 56.8 vs 25.68 HP). The LLM won only where the payoff fell beyond the search horizon (Bomb: 34.74 vs 17.2). So LLMs are a horizon-extending prior, not a tactician.

### D. Memory-augmented LLM agents (AgenticSTS)

AgenticSTS is the best-documented LLM agent and the most honest about its own statistics ([arXiv 2607.02255](https://arxiv.org/abs/2607.02255)).

**What the headline supports:**
- The skill-layer headline (baseline 3/10 → triggered skills 6/10) has Fisher p ≈ 0.37. Pooled scaffolded vs unscaffolded (18/30 vs 7/20) gives p ≈ 0.15. That supports "no detectable effect" at this N, as the authors' "directional" framing concedes.
- The pooled archive gives 44/93 at Silent A0 (CI 37.5–57.4%). It mixes conditions, though, and excludes 66 agent_abort rows of 385, a survivorship risk ([history.jsonl](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS-Data/runs/history.jsonl)).
- The ascension ladder stalls at A8, with 0/18 (CI 0–17.6%).

**Decision quality:**
- The only measure is an Opus-4.6 1–5 rubric over about 12 cases ([eval_decision_quality.py](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/scripts/eval_decision_quality.py)).
- Its A/B skill gate runs in observation mode and does not block writes.
- Hand-authored seed skills mix human expertise into what is credited to memory.

**Hidden information:** plan arithmetic is checked only with base-damage sums. The agent missed a non-damage loss condition: about 53% of Insatiable deaths were Sandpit-timer kills ([design doc](https://github.com/AlayaLab/AgenticSTS/blob/main/AgenticSTS/docs/2026-04-08-rich-combat-analytics-design.md)).

**Most valuable diagnostic:** 136 of 202 defeats (67%) happen on boss floors 17/33/48. That says where search compute pays off.

**Reuse:**
- the CC-BY trajectories ([HF](https://huggingface.co/datasets/AlayaLab/AgenticSTS-trajectories));
- the 3,214-episode combat store, for per-enemy HP-loss baselines;
- the typed decision JSON;
- the stats scripts.

**Caveat:** all of this data is v0.103. Re-scoring those states in a v0.107.1 engine needs reconstruction with `set_player` and `enter_room`, and cards and enemies changed between builds. Fidelity of those re-scores is UNVERIFIED.

[SpireMind](https://github.com/optima-xu/SpireMind) contributes memory hygiene: a lesson activates only after regression across 3 or more training seeds, holdout seeds stay isolated, and counterexamples deactivate lessons. It explicitly does not claim a better win rate.

### E. Jev factored decisions

**What the numbers actually show:**
- **The 27/30 vs 29/30 benchmark.** It is 10 fixtures × 3 repeats, graded by string match on the first action. The grader says it is "not optimality or win probability" ([suite.mjs](https://github.com/shoemoney/jev-the-spire2/blob/main/spire-demo/benchmark/suite.mjs)), and the author states a ±3 noise floor. Fisher p ≈ 0.61, and repeats of the same fixture are not independent, so the effective n is 10.
- **The LLM arm was not prompted the same way.** It got state cut to 24,000 chars and candidates to 16,000 chars, and none of the nouls ([vs-llm.mjs](https://github.com/shoemoney/jev-the-spire2/blob/main/spire-demo/benchmark/vs-llm.mjs)). Whether the truncation actually cut any fixture is UNVERIFIED.
- **The sweep winner.** Waste-veto scored 45/50 vs no-waste 35/50, which is p ≈ 0.02 only if the 50 trials were independent. They were 10 fixtures × 5 repeats; at fixture level a 9/10 vs 7/10 split would be p ≈ 0.58 (illustrative). The waste question was written after seeing which fixtures failed, and there is no held-out set ([SWEEP-FINDINGS](https://github.com/shoemoney/jev-the-spire2/blob/main/SWEEP-FINDINGS.md)). Hedge-only configurations, which cannot change the choice, ranged 21–25/30, which is the noise floor.
- **"15x faster".** The table supports 11.4x (vs Opus 5.5) to 17.6x (vs Fable 5.1). "259x cheaper" is against Fable 5.1 only; against Opus 5.5 it is about 102x.
- **End to end.**
  - Upstream: 1 win in 182 runs (CI 0.1–3.0%), with the policy changing across runs, so it is not a win rate for any single policy ([data](https://github.com/alexmeckes/jev-the-spire/tree/main/spire-demo/progress-site/dist)).
  - Fork: 0/9 (CI 0–30%), and a median floor of 17 that stayed flat over 140+ iterations of an autonomous coding loop ([ralph-loop](https://github.com/shoemoney/jev-the-spire2/blob/main/.opencode/ralph-loop.local.md)).
  - Latency is bimodal: about 53% of calls were in a 7–16 s slow mode earlier on the same day the sweep ran in fast mode.

**What survives:** the factoring pattern. Code generates candidates, one call asks many independent yes/no questions, and code recombines the answers. The waste noul was the only configuration with 0/9 self-harm trap failures. Both are good blunder filters and feature generators around a search.

### F. GRPO-fine-tuned small models

There are no results: [sts2-agent](https://github.com/mingxuan-he/sts2-agent)'s first loop never ran, and the pipeline still uses an approximate Python sim the README calls obsolete.

**Design problems:**
- **Shaped reward bakes in combat-local proxies that can disagree with run value.** +0.01 per damage dealt, −0.02 per HP lost, ±1 per combat.
- **Cost.** Estimated $1.0–1.4K for a combat-only campaign ([model-selection](https://github.com/mingxuan-he/sts2-agent/blob/main/docs/model-selection-2026-08.md)).
- **Instability.** Multi-turn RL on LLMs is documented to collapse ("Echo Trap", [RAGEN](https://arxiv.org/abs/2504.20073)).

The infrastructure is better than the method: HeadlessEnvPool, server-side seed pools, sorted piles, action-attempt logging, and the two fidelity-bug write-ups.

### G. End-to-end RL

**Slay_RL (StS1)** is the gold standard of rigour and the clearest negative result:
- 15.43% vs 9.84% for the KL-0 champion, +5.59pp, CI [+4.82, +6.36], over 10,000 paired seeds, after about 3.55B decisions on a 202k decisions/s GPU pipeline;
- that is still below Bottled AI's search-plus-rules Ironclad 20%.

**StS2:**
- [Zaaacqwq](https://github.com/Zaaacqwq/SlayTheSpireRL/blob/main/plan/rl_v2_current_stage.md) peaked at a 12% Act-1 pass rate on the real engine at about 170 steps/s. A potential-based shaping bug paid a death in front of the boss +1.76 versus +0.65 for winning the fight, so the policy learned to walk to the boss and die.
- [zhiyue](https://github.com/zhiyue/sts2-rl-agent)'s about 92% Act-1 combat win rate is in its own unvalidated simulator.
- Spirebird: about 2M games, 0 wins in the latest 10,000.

**Credit:** this is the only family that does real run-level credit assignment, through full-run Monte Carlo returns. That is exactly the piece the new framework needs, but as a value function inside search, not as the policy.

**Compute check:** on the emulator, 3.55B raw steps at roughly 8 cores × 14k steps/s is about 10 h of raw stepping (my estimate, excluding NN inference and Python overhead; UNVERIFIED). Raw speed is therefore not the blocker. The 15% ceiling and Act 2–3 fidelity are.

### H. Clairvoyant search (StS1)

sts_lightspeed's MCTS searches from the true RNG state ([README](https://github.com/gamerpuppy/sts_lightspeed): "best result, knowing the state of the game's rng"). scumthespire learns the future through save/load.

**sts-rl-agent** pairs a learned macro MLP with that MCTS ([HF](https://huggingface.co/Jialeiv/sts-rl-agent)):
- 14% vs 6% on 50 seeds (Fisher p ≈ 0.32 if unpaired). The floor gain, 42.5 vs 31.2, is the more believable signal.
- Even with clairvoyant combat, the result stays low.
- Distilling the clairvoyant teacher plateaued at 0.44 imitation accuracy, and the distilled nets reached floors 8–14 against the teacher's 23.

**Use:** clairvoyant values only as an upper bound (the value of perfect information).

### I. Honest determinized MCTS on the StS2 emulator

This is the only work that measures decision-procedure quality quantitatively with paired comparisons ([FINDINGS](https://github.com/evangambit/sts2/blob/main/rl/FINDINGS.md)):
- **Exploration constant.** c = 1.4 → 0.1 cut P(death) from 0.183 to 0.092 (44/240 vs 22/240, Fisher p ≈ 0.005; a real effect).
- **Common random numbers.** 4.6x variance reduction.
- **Tempo rollout.** +3.8 HP, paired SE 1.1.
- **Budget multiplier.** The augmentations at 60 sims (P(death) 0.036) roughly match plain MCTS at several hundred to 1,500 sims (0.026).
- **Learned components.** The value head never beat rollouts. The PUCT prior added +2.0 HP. Four richer observations did nothing: "Everything that worked was about the SEARCH or its TARGET."

**Weaknesses:**
- the value is combat-local (HP and P(death)), not P(run win);
- run-level search gains only +1.7 to +4.6 floors over random;
- it is a reimplementation with a divergence catalogue (87 or 450 entries, see section 7);
- it sits in a legal grey zone because its data comes from decompiled source.

**Strength for this project:** it is pinned to v0.107.1, the main-branch build installed on the owner's Mac and the build FableBot plays.

---

## 3. Headline numbers vs what the data supports

| Claim | Data | What it actually supports |
|---|---|---|
| AgenticSTS skills double wins (3/10 → 6/10) | Fisher p ≈ 0.37; CIs 10.8–60.3 vs 31.3–83.2 | No detectable effect |
| Jev ≈ frontier LLMs (27/30 vs 29/30) | p ≈ 0.61; effective n = 10 fixtures; author's noise ±3 | Cost and latency only |
| Jev waste-veto beats no-waste (45/50 vs 35/50) | 10 fixtures × 5 repeats; question written after the failures | Fixes the traps it was written for |
| Jev "first win" | 1/182, policy changing (CI 0.1–3.0%) | About a 0.5% baseline |
| Learned macro + MCTS beats heuristics (14% vs 6%) | 7/50 vs 3/50, p ≈ 0.32 | Floors (+11) maybe; wins no |
| BFS vs MCTS, StS1 Silent (1/30 vs 3/30, [Doron Singer](https://dev.to/feed/doronsinger)) | p ≈ 0.61 | Nothing |
| FableBot A1 rest rule 25.6% | 10/39, CI about 14.5–41% | Indistinguishable from 19.4% |
| FableBot 20.7% A0 | 71/343, CI 16.7–25.3% | **Real** |
| Slay_RL +5.59pp | 10,000 paired seeds, CI [+4.82, +6.36] | **Real** |
| evangambit c = 0.1 halves P(death) | 44/240 vs 22/240, p ≈ 0.005 | **Real** (single combats) |
| Spirebird engine | 0/10,000, upper bound 0.04% | **Real** negative result |

**Power budget (80% power, α = 0.05, unpaired):**
- 20% → 25% needs about 1,094 runs per arm;
- 5% → 10% about 434;
- 50% → 55% about 1,565.

At about 280 runs/day (a rules bot at 3x on the live game), a 20% → 25% A/B takes about 8 machine-days. At jev's pace (about 50 runs/day), it takes about 44 days. Pairing with common random numbers on a seedable engine divides n by roughly (1 − ρ). This is why evaluation has to move off the live game and down to the per-decision level.

---

## 4. Five lessons the new framework must steal

1. **Factor the problem the way FableBot and Bottled AI do, with one value currency.**
   - Exhaustive or determinized search inside combat.
   - A cheap judgment model for macro decisions: map DP pricing fights from observed history, card, shop and event scoring.
   - Policies written as pure functions `(state, kb, config) -> (action, scores, rationale)`, with the config hash logged so every decision can be replayed and re-scored ([FableBot](https://github.com/cicero225/STS2FableBot)).
   - Score everything in run-level units, never mixing end-of-fight HP and P(win) in one backup ([ARCHITECTURE](https://github.com/evangambit/sts2/blob/main/rl/ARCHITECTURE.md)). "Arriving healthy" is the first proxy for that run-level value.
2. **Determinize correctly and compare actions under common random numbers.** Use `clone(resample_hidden=True)`, which re-seeds every unobserved RNG stream and reshuffles the unknown part of the draw pile. Compare sibling actions in the same sampled worlds, pick by mean value, and tune the exploration constant to [0,1] values. These were the biggest measured gains, and they cost nothing (evangambit/r33hab).
3. **Code owns legality and arithmetic; models only return indices or probabilities.** Examples: numbered legal-action lists ([brekkylab](https://github.com/brekkylab/sts2-llm-coop-mod)), jev's candidate generator plus lethal gate, SpireMind's calculator, brmarcosbr's rejection channel. CharTyr's 409 cascades show the cost of skipping this. Also log which policy made every decision, to avoid an ai-spire-style silent fallback.
4. **Evaluation hygiene from day one.**
   - Frozen, version-tagged, paired seed batteries plus an untouched held-out pool (sts2-agent's 200/40; Slay_RL's 10k paired seeds).
   - Wilson and Fisher statistics with pre-registered denominators, and aborts counted rather than dropped (AgenticSTS).
   - Sensitive secondary metrics: damage per floor (JoeB08), P(death) per fight (evangambit).
   - Telemetry that checks every win outranks every loss in the reward (it would have caught Zaaacqwq's inversion and Slay_RL's stalling loophole).
5. **Treat the real engine as the fidelity oracle and pin the version.**
   - Differential tapes: mingxuan's 97/97 deterministic replay, r33hab's capture sweeps.
   - Doron Singer's fidelity harness found about 100 bugs; fixing them raised Act-1 boss wins from 6.5% to 36%. Fidelity bugs dominate early progress.
   - Pin **v0.107.1**: the owner's install (build 23811903), the emulator, FableBot, and 630,765 Spire Codex human runs ([manifest](https://spire-codex.com/api/exports/runs/manifest)).

Also worth borrowing:
- AgenticSTS's bounded, typed, roughly 5k-token context;
- jev's waste veto;
- Zelnia's "simulate the next elite with each candidate card" ([thesis](https://project-archive.inf.ed.ac.uk/ug4/20233951/ug4_proj.pdf));
- Spire Codex and the owner's own `.run` files as a confounded cold start for the run-level value function. Run files store seed and build, so v0.107.1 macro decisions can be replayed counterfactually.

## 5. Five traps the new framework must avoid

1. **Treating outcome anecdotes as decision quality.** N ≤ 50 win rates, single-seed comparisons (AGI-Eval), fixture string matches (jev) and LLM judges on 12 cases (AgenticSTS) cannot rank decisions. The target metric is regret in win-probability points against a non-clairvoyant reference, with CIs.
2. **Clairvoyance leaks.** Sources of leakage:
   - sts_lightspeed's RNG-aware search;
   - scumthespire's save/load;
   - STS2MCP's `/compendium` seed;
   - the evangambit ordered-pile oracle fork;
   - sts2-cli `set_draw_order` / `get_piles` exposed to the policy;
   - Spire Codex replays carrying `draw_order` and `rng_state`;
   - the "Real Draw Pile Order" mod;
   - raw seed determinism.

   A leaked teacher both inflates results and poisons distillation (0.44 imitation plateau, floors cut in half).
3. **Tabula-rasa RL, hand-shaped rewards, or LLM fine-tuning first.** Spirebird: about 2M games, 0 wins in the last 10k. Slay_RL: 3.55B decisions for 15%. Also Zaaacqwq's reward inversion, RAGEN's Echo Trap, and sts2-agent's shaping constants.
4. **Trusting an undiffed simulator, or tuning on the test set.**
   - zhiyue's 92% in its own sim; METR's subtly wrong Claude-built StS1 clone ([note](https://evals.alignment.org/notes/2026-03-03-balatro-sts-cli/)); the Kaiser Crab false boss victory.
   - jev's weights chosen on its own fixtures; Strens & Moore's fixed-seed overfitting.
   - Doron Singer's card-pick model with the best offline accuracy (55.8%) did worst in-game ([part 3](https://dev.to/doronsinger/part-3-good-models-finish-last-2n6a)).
5. **Putting a network model in the inner loop, or using the live game as the lab.**
   - A Jev call at p50 315 ms is about 5,000x a 58 µs emulator step.
   - A 200-expansion Jev-prior search costs about $30 per run.
   - The live game does about 50–280 runs/day, hangs at about 13 GB after 3 h, and STS2MCP took about 40 days to recover from the v0.107.1 patch.

---

## 6. Verdict on the owner's two premises

### Premise 1: "use RL"

**Mostly a mistake as stated, but correct as a toolkit.**

**Where it genuinely helps:**
- **Defining the objective.** Best play = argmax_a Q(h, a) over the player's information set, with the seed and RNG counters excluded.
- **Policy improvement by search.** SPARTA one-step rollouts over a FableBot-style blueprint, with a guarantee of doing no worse ([SPARTA](https://arxiv.org/abs/1912.02318)); later, Expert Iteration that distils the emulator's honest search into a policy prior.
- **Learning the run-level value function.** Monte Carlo regression from simulated runs, DouZero/Suphx-style ([DouZero](https://arxiv.org/abs/2106.06135), [Suphx](https://arxiv.org/abs/2003.13590)). This is the long-horizon credit problem that no StS2 project has solved, and the place where RL earns its keep.
- **Tiny-budget root search.** Gumbel root selection when real-engine simulations are expensive ([Gumbel](https://iclr.cc/virtual/2022/poster/6418)).
- **A fast rollout policy.** Masked PPO trained on the emulator.

**Where it is a mistake:**
- end-to-end PPO or GRPO as the policy;
- RL in the live game or on sts2-cli at 20–170 steps/s;
- hand-shaped dense rewards;
- LLM fine-tuning before a regret-labelled oracle exists. If the owner ever gets there, the reward should be negative oracle regret, not wins.

### Premise 2: "use jev's cheap compute"

**Wrong framing.** Jev is cheap hosted inference: closed weights, no fine-tuning, non-deterministic, vendor in early access with possibly subsidised pricing ([docs](https://docs.typesafe.ai/models), [DataCamp](https://www.datacamp.com/blog/system-one-models-jev)). Money was never the constraint: about $0.15–0.25 per run. Throughput, simulator fidelity and evaluation are the constraints, and Jev helps with none of them. The cheap compute that actually matters is local: the v0.107.1 emulator on the owner's Mac (free, about 10^4 steps/s per core), sts2-cli workers, and small locally trained nets.

**Where Jev genuinely helps:**
- **Root prior.** One batched call per real decision returns a distribution over up to 255 legal actions, fed into Gumbel or SPARTA search. Mix it with a uniform prior so the search can always overrule it.
- **Blunder filter.** The waste and self-harm noul.
- **Cheap labeller.** About $460 per 1M states at the rate limit, as a warm-start prior, never as ground truth.
- **A baseline to measure regret against.**

**Where it is a mistake:**
- as an oracle (about 0.5% A0 end to end);
- as a rollout or per-node policy (network latency);
- as evidence (its benchmark);
- as a trainable component;
- as a hard dependency.

Distillation terms are UNVERIFIED ([terms](https://typesafe.ai/terms)). So Jev should sit behind a model-agnostic `policy(info_state, legal_actions) -> distribution` interface that a local net or a Claude model can fill.

**The one experiment that justifies keeping it:** at matched compute on the emulator, does a Jev prior lower regret on a held-out oracle set compared with a uniform prior and a small learned prior? Run a calibration curve of P(choice) against oracle Q alongside it. Until that experiment says yes, Jev is optional.

---

## 7. Dossier conflicts and unverified items (for the framework designers)

- **"Current game version."** The tooling dossier treats v0.111 as current. In fact main is **v0.107.1** (the owner's build 23811903) and v0.111.0 is a public beta (game dossier; [Steam news](https://store.steampowered.com/news/app/2868840)). So the emulator's v0.107.1 pin is an asset, not a staleness problem. The next patch (alternate Act 2 plus a sixth character, no date) will break every backend at once.
- **RNG.** The theory dossier cites System.Random seeded with runSeed + hash ([ing-gom](https://github.com/ing-gom/sts2-rng-fix)). The game dossier and r33hab say v0.107.1 switched to xoshiro256** ([RNG rework notes](https://store.steampowered.com/news/app/2868840/view/1835871199305790)). Treat the correlated-RNG exploits ([tck.mn](https://tck.mn/blog/correlated-randomness-sts2/)) as pre-v0.107.1 only, and confirm in the engine.
- **Emulator numbers.** 58 µs/step and 0.07 ms clone (r33hab) vs 72 µs and 17 µs clone (evangambit). Same order of magnitude. Divergence catalogue: 87 entries (r33hab HANDOFF) vs 450 (evangambit). Which entries are still open is UNVERIFIED.
- **sts2-cli speed.** About 20 steps/s per process comes from Zaaacqwq, and the setup involved a Windows timer fix. The Mac figure and the cost of a load-plus-replay "clone" are UNVERIFIED. Upstream applies 2 IL patches (including the one that causes the Gardener runaway); the mingxuan fork applies 0 IL patches and uses a real frame pump, so always name the fork.
- **Human baseline.**
  - Mega Crit: 16% at A0 ([Neowsletter](https://megacrit.com/news/2026-5-22-neowsletter-issue-22/)).
  - Spire Codex, self-selected uploaders: 22.0% at A0 ([stats](https://spire-codex.com/api/runs/stats)).
  - FableBot cites about 20% for dedicated players.
- **FableBot method details.** I verified these from the README on 2026-10-10. Its macOS portability is UNVERIFIED: it runs on Windows, but STS2MCP's DLL is cross-platform.
- **Unverifiable sources.** elysianx138's random baseline (repo returns 404), OpenAI's StS2 daily-challenge run (page returned 403), and the AGI-Eval ascension level all remain UNVERIFIED.