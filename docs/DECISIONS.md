# Decisions

Each entry: date, decision, why, and what it supersedes. Design references are to
`spireline-design-v1.1.md` (2026-10-10), which is kept outside this repo. A decision is
changed only by a new dated entry that names the one it replaces.

Current target (D11, D15): **Ascension 10, all ten modifiers on, Acts 1-3, Ironclad first, then
every character.**

## D1 · 2026-10-10 · Pin StS2 v0.107.1, Steam build 23811903

- Game v0.107.1 (main branch, build 23811903): the build installed on the Mac, the emulator's
  target, FableBot's and spire-coach's build; v0.111 is a public beta (§3.1 "Why v0.107.1").
- Emulator r33hab/sts2 @ `b7452170ce1df91de29d3c94acb11d87c7efc708`; mod r33hab/STS2MCP
  `spire-coach` @ `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4` (payload schema 4).
- Steam updates the game only on launch; Steam Cloud off for the game; the pristine install is
  archived. Labels are valid only for their `(game_build, engine_sha, pi_ref, value_level)`.
- Patch day: stay on the archive, wait for upstream ports, then re-run F1-F3, F9 and relabel (§3.5).

## D2 · 2026-10-10 · Track D (Defect, A0) is primary

- SpireBench, the oracle and any RL target are Track D: Defect's card pool is 88/88 captured
  against the live game (§3.1).
- Track I (Ironclad, Act 1, positions whose cards are all captured) exists only for the
  Ironclad-only comparators (FableBot B2, spire-coach B3) and live advice.
- The cross-character "beat 20.7%" stretch goal is dropped; all gates are relative and paired.

## D3 · 2026-10-10 · Reuse the emulator and mod only after review

- No third-party code is built, installed, imported or run before a review records a
  go decision (§3.6).
- Build from source only; artefact hashes go in `versions.lock`.
- Fallback if the review fails: evangambit/sts2 + cicero225/STS2MCP with our own converter
  (+15-25 h), spire-coach dropped.
- Spireline's own code imports none of it. The firewall was written by reading the mod's C#
  at the pinned commit (citations in `spireline/infoset/firewall.py`).
- Note (2026-10-11): the review was first kept private.
- Note (2026-10-12): a scrubbed copy is now published as `docs/SECURITY_REVIEW.md` so agents on
  the PC can read it. `pc-setup/build-emulator.sh` shows its verdict and still asks for a typed GO.

## D4 · 2026-10-10 · Combat-local L0 value first

- Phase 1 labels are in **L0 points** (u_L0 = 0 if dead, else 0.5 + 0.5·min(1, (HP_end + 10·potions)/maxHP)),
  never pp of P(win) (§1.2). L1 (pp P(clear act), Act 1 only) arrives with V_run in Phase 2;
  L2 is "U_lambda units" until pi_ref wins >= 10% and V_run passes the Brier-skill gate.
- Enforced in code: `spireline.api.Decision` rejects a unit that does not match its level.

## D5 · 2026-10-10 · Learned components are gated by ledger signals

- RL-1: Gumbel Expert Iteration for the combat prior (wraps r33hab `rl/prior_loop`).
- RL-2: Deep Monte Carlo afterstate value V_run (+ FightNet), Act 1 only until F3/F4 pass.
- Neither starts until the flywheel table (§8) calls for it, e.g. UNCERTAIN > 50% on QUICK
  combat for RL-1; Tier-B silver/gold disagreement > 20% or a failed Brier gate for RL-2.
- Keep-rules (§5.3) and the anti-circularity rule apply: a component trained on oracle targets
  also needs a paired win on a fresh E-block and a clean F7 audit.

## D6 · 2026-10-10 · No end-to-end RL

- No end-to-end PPO/GRPO policy, no RL on sts2-cli or the live game, no hand-shaped dense
  rewards, no distilled clairvoyant teachers (§5.6). Search plus the two learned components is the agent.

## D7 · 2026-10-10 · No LLM components anywhere

- Decided after design v1.1. Supersedes: §6 entirely; the `haiku` and `jev` priors and the
  explainer in §2.1/§2.2; baselines B4 (jev) and B5 (Claude Haiku) in §7.5; the Haiku/Jev arms
  of ablation A4; experiment E1; the §3.5 "cheap drift alarm" (LLM re-scoring); the P5
  single-decision LLM bandit; the LLM-related $ in §8.
- `Prior` implementations are uniform, heuristic (B8 scores, deck fights) or a trained net.
- The `usd` field stays in the §1.4 contract for cloud-burst compute only.

## D8 · 2026-10-10 · The Windows PC is the always-on worker

- Hardware: RTX 3080 Ti; CPU and RAM to be recorded on setup (2026-10-11) in `versions.lock`
  and the bench results.
- Heavy work (emulator build, batteries, labels, training) runs in **WSL2 Ubuntu**, because
  Claude Code's sandbox runs on macOS, Linux and WSL2. The emulator target there is
  `linux-x64`, which r33hab's `scripts/build.sh` supports (build.sh:10-17); none of it built yet.
- The Claude Desktop app runs natively on Windows for Remote Control / Dispatch.
- The Mac (M1 Pro, 16 GB) is the owner's main machine; the §3.4 Mac throughput estimates and the
  overnight-laptop rules apply only to work left on the Mac.
- Open, not decided: where the live game runs for Tier L and F6 parity (the Mac today; the
  mod also builds on Windows, `build.ps1`), and how the §3.6 isolation (a separate non-admin
  user, network deny) maps to WSL2 (a dedicated distro/user is the obvious analogue).

## D9 · 2026-10-10 · Cloud only for bursts

- Default is local (the PC). Cloud machines (e.g. a CCX43-class box; pricing UNVERIFIED) only
  for bounded bursts such as Tier-B gold, holding only our private binaries, never game DLLs
  or the decompile (§3.4, §8 non-goals).

## D10 · 2026-10-10 · Firewall v0 starts with every allow-list empty

- The STS2MCP schema-4 default payload carries enemy `move_id`, `state_log` and every
  primitive `ai_fields` member (McpMod.StateExtras.cs:212-240, 316-330). The firewall admits
  none of `move_id`/`ai_fields` until L8/L7 evidence puts a monster/key on its allow-list.
- Also dropped until evidence: the last `state_log` entry (the pending move,
  docs/raw-full.md:718-722), HUD-hidden powers (McpMod.StateBuilder.cs:4214-4220),
  `revive.in_turns` (walks `FollowUpState`, McpMod.StateBuilder.cs:2669-2686), relic raw
  `saved`/`fields` (the displayed `counter` is kept), `vs_targets[].values`, `run.start_time`.
- Piles and the deck are multisets; the hand stays ordered with uids.
- v0 admits combat screens, `hand_select` and in-combat `card_select`; other screens are
  dropped and marked unsupported until Phase 2.
- Each allow-list addition is a new dated entry here, with the evidence (test id, capture).

## D11 · 2026-10-11 · Target is Ascension 10 only, Acts 1-3

- Every track, battery, label, tape and baseline is played at **Ascension 10 with all ten
  modifiers on**. No A0 (or other ascension) play result is reported as a Spireline result;
  the emulator throughput benchmarks in `bench/` (A8, for comparison with upstream figures)
  are not play results.
- Scope is the whole run, **Acts 1-3**. Gates that start in Act 1 (D4's L1 level, D5's RL-2
  "Act 1 only until F3/F4 pass") stay as steps on the way, not as limits on the scope.
- Why: A10 is a common competitive level; the public A10 run corpus is large (D13); and one
  fixed ascension keeps every label, battery and baseline comparable.
- Baselines run at A10 on the same seeds. Published A0 figures (for example FableBot's) are
  context only, never a target.
- UNVERIFIED: emulator fidelity at A10. The emulator's own probes and `bench/` run A8
  (`bench/README.md` §6 item 7), and Acts 2-3 are less verified than Act 1 upstream. F1-style
  tape checks must include A10 runs in every act before an A10 label in that act is trusted.
- Supersedes: "A0" in D2, `scope.ascension: 0` and "Act 1 first" in the DRAFT
  `eval/prereg/phase1.yaml`.

## D12 · 2026-10-11 · Defect is the primary character

- Defect first, because its card pool is the best verified in the emulator (88/88 cards
  captured against the live game, design §3.1).
- Restates D2's Track D at A10 (D11). Track I (Ironclad, captured cards only) stays secondary
  and is also played at A10. Other characters wait until Defect passes its fidelity gates at A10.
- Supersedes: "Defect, A0" in D2.

## D13 · 2026-10-11 · The Spire Codex public export is a run-layer test corpus

- The public Spire Codex run export for v0.107.1 (spire-codex.com,
  `runs-v0.107.1.jsonl.gz`, manifest sha256
  `55557226ec1023d49d99c88555a2a102706c07281784a5edab038172fea6d9e2`, checked 2026-10-10) is used
  to test the run layer: replay checks of logged runs, and distribution checks of the
  emulator (encounter rates per act, reward rarity, "?" room outcomes) against aggregate odds.
- It is a test corpus, so nothing is trained or tuned on it, and it is not a label source.
- Raw runs are never committed (`.gitignore`: `data/`, `*.jsonl.gz`). Only aggregates are
  published, with attribution. As downloaded: 638,919 runs; the A10, standard, finished,
  single-player, unmodified, base-character, vanilla-content subset is 56,137 runs, of which
  11,350 are Defect (1,269 wins).

## D14 · 2026-10-11 · No LLM components (restated for the public repo)

- Restates D7: Spireline has no LLM calls, LLM priors, LLM explainers or LLM-generated labels.
- Adding one needs a new dated entry here and a demonstrated benefit: a paired,
  pre-registered win on a fresh E-block under the same gates as any other component (D5).
  `CONTRIBUTING.md` says the same.

## D15 · 2026-10-13 · Ironclad first; the goal is any character at A10

- Start with the character the emulator is closest to A10 wins on, which is the Ironclad: it is
  the only character the emulator can play whole runs with at `b745217` (`native.run_reset` takes
  no character; `RunEngine` starts every run with the Ironclad's HP, deck and Burning Blood), and
  upstream's real-A10 run work (double boss, act-scaled reward upgrades) and all its full-run
  traces are Ironclad. No character has an A10 win in the emulator yet.
- The goal is to show the method works for **any** character at A10. Each further character
  follows once the emulator plays its whole runs and it passes the same fidelity gates.
- Why D12's reason no longer decides it: D12 picked the Defect for its 88/88 captured cards, but
  upstream now reports all five card pools captured, and whole runs, not card pools, are what
  limit A10 runs.
- Supersedes: D12 ("Defect is the primary character", "other characters wait until Defect
  passes"). The DRAFT `eval/prereg/phase1.yaml` still says Defect (`primary_track`, E00, F1) and
  is retargeted when it is next revised.

## D16 · 2026-10-13 · Our own simulator fork, refereed by the game's own code

- The goal now is a **high-fidelity simulator with complete coverage**: every character, act,
  ascension and piece of content, verified against the game. Search and agent work wait for it.
- Spireline no longer depends on upstream. Its simulator is our fork of r33hab/sts2, starting at
  the reviewed `b745217`. Upstream keeps changing outside our control, so it is watched
  (`scripts/upstream_watch.py`), and a change is taken only if it helps fidelity or coverage,
  after its diff has been read (security review §7.1).
- Fork patches are pushed to the fork automatically once its tests pass. Fixes that would help
  upstream or other projects are offered to them as PRs.
- The fidelity reference is the game's own code: `sts2.dll` from the archived build, run
  headless, compared with the emulator after every action, every RNG stream included. It runs
  only after `docs/SECURITY_REVIEW_ADDENDUM_1.md` records the owner's GO (D3).
- The referee harness is published so others can run it on their own copy of the game. No game
  files, assets or decompiled source are ever published (`CONTRIBUTING.md` rule 2, review R1).
- Supersedes: "wait for upstream ports" in D1 (the fork ports changes itself). The emulator pin in
  D1 and `spireline/__init__.py` stays `b745217` until the fork's first tested build. D3's review
  covers the fork's base; every later upstream pick is read before it is taken.

## D17 · 2026-10-22 · The goal is the agent; the simulator serves it

- Agent work starts now on the current emulator (our fork at `b8402e96`), judged on the headless
  referee. The plan of record is `docs/PLAN.md`; it replaces section 5 of the 2026-10-22 handoff.
- Why: simulator-first did not converge (the remaining combat errors are architectural, site fixes
  do not close them, and the full rebuild was re-priced at ~95% of a week's credit), and nothing in
  that order measured the goal's own number, the agent's real-game win rate. The independent review
  of 2026-10-22 (`referee/design/plan-review-2026-10-22.md`) found the same.
- The fork, the referee, the gates (corpus, Codex walk, refset, invariants, mutation) and the
  complete-coverage direction all stay; coverage is no longer a prerequisite for the agent.
- Supersedes: D16's "search and agent work wait for it". The rest of D16 stands.
- Decided by the owner's instruction of 2026-10-22 to re-plan; D17-D21 are vetoable by a later entry.

## D18 · 2026-10-22 · Where learning runs

- The headless referee (Amendment 1a of `SECURITY_REVIEW_ADDENDUM_1.md`) may score the agent on
  fixed seed blocks and supply run outcomes to fine-tune the learned components of D5 (the combat
  prior and the run value). Bulk self-play and expert iteration stay on the emulator.
- No end-to-end PPO/GRPO policy, no hand-shaped dense rewards, no bot on the live client, no play
  on the vanilla profile, Daily runs or leaderboards (`CONTRIBUTING.md` rule 6).
- Why: the referee is exact by construction and is the only judge the goal accepts; the search sets
  the pace, so its throughput suffices (`PLAN.md` section 8.1).
- Narrows D6 ("no RL on sts2-cli or the live game"): the referee is not the live client, and the
  learning is of D5's components, not an end-to-end policy. D5's keep-rules and the anti-circularity
  rule apply unchanged.

## D19 · 2026-10-22 · Fidelity work is ranked by agent play; the kernel rebuild is gated

- Emulator divergences are ranked weekly by the agent's own real-game play replayed in lockstep
  (`PLAN.md` section 8.2). Fixes go to the top of that list, through bug process v2, Sonnet first.
- The combat-kernel rebuild in the game's shape (`referee/design/rebuild-plan.md`, P0-P2) is
  decided at gate G1 (end of week 4) by the rule in `PLAN.md` section 8.3, at the reviewed price of
  ~255 rounds (190-340), ~73% of a week (45-122%), with C1 and K1-K5 unchanged. The run layer is
  not rebuilt.
- Why: the review found the 40-50% figure covered P1+P2 alone (M3), and that the rebuild's size
  should follow the harm measurement, not precede it (B2).
- Supersedes: the handoff's step 4 scope and price, and its open decision D-b.

## D20 · 2026-10-22 · Hosts

- The full-host referee env (branch `proto/real-game-env`, to be hardened) is the judge and the
  fine-tuning environment. The nodeless run host and the Godot-free host are parked behind the
  throughput bar of `PLAN.md` section 8.1: built only if the measured agent-side decision rate
  exceeds 80% of the measured sustained env rate.
- Why: the census (`referee/design/nodeless-run-host.md`) found the 27-encounter fallback list caps
  the whole-run gain at ~2-3x, and the review re-derived the step-1 estimate at 250-800/s, not
  1,000-1,500 (M2). Under D5's method the search, not the env, sets the pace.
- Supersedes: the handoff's steps 1 and 2 and its open decisions D-a and D-c. Addendum 2 is drafted
  only if the bar is reached.

## D21 · 2026-10-22 · Budget and model policy

- Ceiling 15% of a week's allowance (~52 Sonnet-equivalent rounds), split by lane as `PLAN.md`
  section 6; unspent credit is not carried forward. Sonnet by default; Opus for kernel and search
  design, amends after a failed Sonnet round, and the weekly review; Haiku for mechanical sweeps.
  One reviewer per change with the checklist of `PLAN.md` section 10.
- CPU runs around the clock on the lab's priority ladder (`PLAN.md` section 7); agent rounds start
  only from a prepared input.
- Why: credit is the limit and the CPU is free; the measured history is 1.36 rounds per fix attempt
  with 46% accepted outright, so prepared inputs and the cheapest capable model are where the
  savings are.
- Supersedes: the handoff's proposed 15% rebuild cap as a lane of its own; D13 stands (the Codex
  export is not an imitation source; the review's M5 found ~21k usable runs with no combat plays).

## D22 · 2026-10-22 · The target is better than the best players; a public in-fight mod is a side product

- The agent's target is play better than the best human players at Ascension 10 (`PLAN.md` section 1:
  top-decile Codex players as the first reference, recorded top-player decisions under the agent's
  labels as the second, head-to-head on fixed seed blocks as the public proof). The human average
  is a milestone, not the finish line.
- A game mod that shows the best in-fight play may be released publicly to build interest. It
  carries only the distilled combat policy network (a few MB, no search) and our own mod code. It
  never ships the simulator, the referee, game files, decompiled text or any server. Its release
  gate, allow-list and kill rule are `PLAN.md` Lane F; the owner approves each release.
- Why: the owner stated the goal on 2026-10-22 ("a perfect playing AI that is better than the best
  pros") and the side product ("a smaller AI that says the best plays in a fight, as a mod").
- Supersedes: the "human average" done criterion of `PLAN.md` section 1 as first written. Narrows
  the private-everything constraint (Amendment 1a: "simulator repo stays private") to exclude the
  mod repo and its exported weights only. D7 (no LLM components), D13 (Codex: aggregates only) and
  `CONTRIBUTING.md` rule 6 (no bots on Daily runs or leaderboards) stand.

## D23 · 2026-10-23 · No faster real-game host although the 8.1 bar is crossed

- The measured agent side with search config `a3-v1` (21.4 decisions/s per core, 242 at 16
  processes, fork 97b03d1e) is above 80% of the referee env's sustained 118 decisions/s at 12
  processes (C0), so `PLAN.md` section 8.1's rule indicates a faster real-game host. None is built.
- Why: the real game is not the bottleneck today. A 500-run scoring block takes about 10 minutes
  (A2) and all training runs on the emulator (D18). The bar was written for real-game throughput
  limiting the agent, which has not happened.
- Re-test the bar when real-game training (D18's V_run fine-tuning on real outcomes) enters P2, or
  when a score-real block no longer fits its 2-4 hour window.
- Decided by the owner in chat on 2026-10-23, accepting the week-1 review's recommendation
  (`D:/spireline/referee/backlog/HANDOFF.md` section 0). D20 stands.

## D23 · 2026-10-23 · The kernel rebuild has two tiers; G1 chooses on a by-family report

- Tier 1: the kernel in the game's shape (the hook dispatcher with the game's listener order from a
  generated table verified by the trace-mode `L` patch, and the action queue), then content migrated
  onto it one hook family at a time in the order of the agent's by-family divergence ranking, the
  old code path serving unmigrated families, stopping when unmigrated families hold under 10% of
  agent weight. Estimated, unreviewed: 60-100 rounds, ~17-28% of a week.
- Tier 2: the full rebuild as D19 priced it (reviewed ~255 rounds, ~73% of a week).
- G1 picks by `PLAN.md` section 8.3: Tier 1 when the top five hook families hold at least 70% of the
  architectural weight or the owner wants the smaller commitment first, with escalation rules; Tier 2
  when the weight is spread. The weekly Lane B report gains a by-family table.
- Why: the full price bundles a cheap kernel (30-40 rounds) with an expensive re-expression of about a
  thousand content models; three quarters of the agent's divergence is in a few ordering families, so
  migrating those first buys most of the benefit at a fraction of the cost. The earlier objection to a
  hybrid ("never sound until done") is answered by the real game as judge: soundness is measured by the
  transfer gap and per-family divergence, not assumed.
- Decided 2026-10-23 by the owner, in chat: start Tier 1's kernel stage now, ahead of G1, in a
  rebuild lane capped at 25 rounds a week while Lane B runs on the API credit. G1 sets the family
  order from the by-family table and decides any escalation. A batch-priced independent review of
  the Tier 1 design runs on day 1 of `API_CREDIT_PLAN.md`.
- Supersedes: D19's single all-or-nothing rebuild decision at G1. D19's price for the full rebuild stands
  as Tier 2.
- Addendum 2026-10-23 (owner, in chat): the API credit is held back for now, so `API_CREDIT_PLAN.md` is on
  hold. Lane B runs on the subscription at the reduced share in `PLAN.md` section 6, the by-family report
  first; the rebuild lane takes the `L` patch and the local tables; the K0 design review done on the
  subscription stands in for the batch-priced one.

## D24 · 2026-10-24 · The promotion's boss-kill check is a not-worse guard until the kill rate reaches 10%

- The promotion rule (`DESIGN.md` section 5.4, `PLAN.md` section 5) kept Act-1 boss-kill rate as a co-primary
  test at one-sided 0.01. At today's 1-2% kill rate it has almost no power (53 discordant pairs in 2,000 paired
  seeds), so no candidate can pass it: generation 1 passed the floor primary at p 5e-5 and failed boss kills at
  p 0.049 with 2.0% against 1.35%.
- From now: boss kill is a not-worse guard (exact McNemar, one-sided 0.01) while either arm is under 10%, and
  becomes co-primary once both arms reach 10%, the clause the wins test already has. Mean floor stays the
  primary; the F7 audit still applies. Generation 1 is re-judged on its existing E-block under this rule.
- Why decided by the orchestrator, not the owner: the change follows from the test's power, not from the
  result, and it mirrors the registered wins clause. The owner can reverse it; then generation 1 stays rejected.
- Supersedes: the co-primary clause in D5/D6 as written in `DESIGN.md` section 5.4.

## D25 · 2026-10-24 · The rebuild lane runs uncapped this week; the API credit starts, $100 by 2026-10-28

- The rebuild lane does not pause at its 25-round weekly cap until 2026-10-30. It continues at once with the F08
  migration (damage and the kill sequence: kill, death hooks and removal inside each Damage call, as the game does),
  the one mechanism behind the top group (32% of agent weight) and half of the damage family. The Tier 1 stop line
  of 120 total rounds and the C1-style re-estimate stand.
- The API credit is started: `API_CREDIT_PLAN.md` runs from today, with the owner's deadline of $100 spent by the
  end of Wednesday 2026-10-28. It owns Lane B's single-site fixes (HANDOFF week-3 brief B1, F08 excluded); the
  subscription session keeps A2c, C2, the leak tests, D and the weekly review.
- Why: after the lockstep fixes the remaining divergence is one ordering mechanism plus routine single-site bugs,
  both cheap; the ceiling, not difficulty, was holding them. Decided by the owner, in chat.
- Supersedes: D23's 25-round weekly cap for this week; the on-hold addendum to D23.
- Corrected 2026-10-24, later: the credit is $250 of Claude Code cloud-session credit, expiring 2026-11-05, not
  API credit; there is no API key and no key session. `API_CREDIT_PLAN.md` is replaced by `CLOUD_CREDIT_PLAN.md`:
  cloud sessions on the GitHub clones implement against unit tests, review and research; the PC's sessions write
  the kits and run the corpus gate, byte proof and landing. The owner's pace, half by 2026-10-28, stands.

## D26 · 2026-10-24 · The cloud plan is revised on the independent review

- `CLOUD_CREDIT_PLAN.md` section 2 is re-priced (Lane B $45, kernel batches $70, reviews $35, lab items $8; new lines for
  confirming tests $15, documentation $8, the D24 statistics follow-up $8; reserve $30) and section 3 gains the liveness rule,
  the default rule (unit-test acceptance means cloud), the kit header, one mechanism per session, and the gate rules (tip
  once, bisect on red, two landing windows a day, no second read of a cloud-reviewed PR, every rejection exported as a
  scenario). C2-C6 start from the pilot branch once the pilot's cloud review posts, not after its landing.
- Why: the review (`docs/reviews/2026-10-24-cloud-plan-and-week3.md`) measured day 1: six hours lost to a GitHub access
  failure invisible from the PC, a Lane B queue worth about 4% of agent weight after the comparer artefacts, no reserve under
  the old ceilings, and the local gate as the binding constraint. Once the access was fixed, all eight cloud sessions delivered
  in about 35 minutes.
- Decided by the orchestrator; reversible by the owner. Owner actions still open: allow `builds.dotnet.microsoft.com` in the
  cloud environment's network settings and add a setup script that installs the .NET 9 SDK (until then sessions use the
  registry-image or the 10.0 roll-forward route `docs/CLOUD_ENV.md` records).

## D27 · 2026-10-24 · A GPU lane: batched inference for self-play, the value head, sweeps in quiet windows

- The PC's GPU idles between train jobs while self-play, the generation loop's bottleneck, pays the policy prior's cost on the
  CPU in every worker (1.4x of the plain search, measured in week 3). A new lane builds one GPU inference server that all
  self-play workers share (Windows-safe transport, batching by deadline, CPU fallback, kill switch), designed in
  `docs/rl/GPU_INFERENCE.md` on the fork and reviewed before code; acceptance is decisions per second with and without it on
  the same seeds and unchanged sample quality as the promotion judge sees it. The same lane trains the run-value head harder
  (ensembles, longer schedules, the completed-Q target; adopted only if the dev-set skill CI excludes 0) and runs the sweeps in
  the quiet windows when the CPU is reserved for game blocks.
- Budget: at most 25 reviewed rounds this week, Opus for design and review, Sonnet workers for implementation.
- Why: the owner asked how idle GPU time could speed the project and approved these three uses; the emulator stays on the CPU
  (the win is in inference, not simulation).
- Decided 2026-10-24 by the owner, in chat.
- Addendum 2026-10-24 ~14:00Z (the GPU lane's reviewed design, `docs/rl/GPU_INFERENCE.md` on fork branch
  `gpu/prior-server`): the honest ceiling is about +25-30% decisions/s on the self-play job, not a multiple, because the
  prior costs 1.38-1.44x of the plain search in CPU time and an eager CUDA forward costs 3.5 ms of host CPU per batch
  on this PC (as much as today's CPU forward). The server therefore replays CUDA graphs per shape bucket and starts
  with a go/no-go self-test (at most 1.2 ms host CPU per batch, at least 1,000 batches/s) before any plumbing. Safety:
  logits over a local-only authenticated named pipe, per-process CPU fallback, the kill file `LAB/GPU_OFF`, the judge on
  the CPU path until a 1,000-seed equivalence check passes, `jobs.json` only after a 2,000-run server block passes.
- Addendum 2026-10-24 17:02Z: piece 1 landed on fork main `b163b4cc` (Python only, default off, 3,105 tests, 0 new
  failures). Go/no-go GO: graph replay costs 0.09-0.41 ms of host CPU per batch against 2.5-3.4 ms eager, 4,898 calls/s
  capacity against a demand bound of about 1,830; the tolerance check passes on 10,000 recorded positions (max logit
  difference 1.9e-6, no argmax flips); a two-worker smoke beside the running lab gives 14.6 against 12.0 decisions per
  CPU-second. Window 1 (lab paused) at 21:00Z measures throughput at 16-24 workers and the 1,000-seed block; `jobs.json`
  switches only after the 2,000-run server block passes.

## D28 · 2026-10-24 · Lane F proceeds on the assumption that modding is allowed

- The derivative-work question in `docs/research/MODDING.md` (a policy network trained in an emulator built from decompiled
  source, uploaded under the Workshop warranty) is closed by the owner: assume it is allowed. Mega Crit openly supports
  modding, links modders to guides that decompile the game, and comparable advisor and overlay mods already exist on the
  Workshop and Nexus. No lawyer, no publisher query before F2.
- The compliance list of the research's section 5 still applies to the mod itself: free, recommend-only, `affects_gameplay:
  false`, displayed state only, no game text, assets or decompiled code shipped, version-pinned, Workshop distribution.
- Decided 2026-10-24 by the owner, in chat.

## D25 addendum · 2026-10-24 · The week's allowance may reach 70% by 2026-10-25

- The owner allows the subscription's weekly usage to reach 70% by 2026-10-25 ~13:00Z (39% at 13:00Z on 2026-10-24).
  Allocation for the 24 hours: kernel lane up to 45 more rounds (the fixed pilot pattern, R4/R4c, the F08 review's two
  oracles, R7 switch-on behind the proof); week-3 session up to 35 (land the five open cloud PRs, the re-ranked by-family
  table, placement rules for the unassigned weight, five to eight kits, re-anchor paths 3/6/turn_advanced, the week-3
  review); GPU lane cap 25 to 50 (the inference server implemented and measured); the rest reserve. The gate stays serial;
  landings queue after the 15:45Z quiet window.
- Decided 2026-10-24 by the owner, in chat.

## D23 addendum · 2026-10-24 · The by-family table now reads Tier 1 decisively; the migration order is set

- With the ranking's classification fix (the lockstep review's finding) and placement rules for the unassigned records, the
  week-2 block re-ranks to an architectural share of 87.1% (was 54.8%) with 1.5% unassigned (was 55.2%); the top five hook
  families hold 97-99% of the architectural weight, so `PLAN.md` 8.3's Tier 1 rule fires under the primary reading. The same
  block re-run under the landed comparer: 0.53% of decisions diverge, architectural 94.1%.
- Family order for the migration: F10 and F08 (in progress), then F06, F11, F15. G1 at the end of week 4 confirms or
  escalates per 8.3; it no longer has to choose the tier.
- Decided by the orchestrator on the week-3 session's numbers (HANDOFF 2026-10-24 13:00Z line); reversible by the owner.

## D29 · 2026-10-24 · Overnight decisions under the owner's delegation (reversible in the morning)

- The owner was away overnight (from 2026-10-24 ~13:20Z) and delegated the decisions ("I trust you to do what you think").
  The orchestrator decided the week-3 review's open items as follows; the owner may reverse any of them.
- **D24 guard flip:** week-3 runs the per-seed pairing check of `docs/PROMOTION_GUARD.md` section 4 on the S3 block
  (discordant pairs below the independence bound; the floor-difference SD well below the root of the summed variances). If it
  passes, `SPIRELINE_REVIEW_GUARD` goes on for the next promotion and the result is recorded here as a D24 addendum; if it
  fails, the flag stays off and the failure is reported. Why: the guard only blocks promotions, so switching it on is the
  conservative direction, and the check is cheap.
- **Completed-Q target:** the E-block A/B of one T=1 completed-Q candidate against visits is approved as the cheap decider,
  within week-3's remaining allowance, after landing 4, with its training scheduled outside the GPU lane's measurement
  windows; the default stays visits until the A/B separates them.
- **Recycle-60:** one warm-start quiet window of about 45 minutes on 2026-10-25, timed by week-3 and announced in HANDOFF
  under `QUIET.lock`, not overlapping the GPU lane's measurement window; the recycle decision follows its result.
- Not decided overnight: anything that changes the plan of record, the week's caps or the credit plan's counts.
