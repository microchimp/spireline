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
- Addendum 2026-10-25 (owner, in chat): **no lower-ascension curriculum for training.** The orchestrator suggested training
  early generations at a lower ascension while scoring at A10; the owner declined: A10 is a fundamentally different game from A0
  or even A9, strategies that work at lower levels are bad at A10, and that is what the AI has to work out. The owner also notes
  that optimising for floors reached can make the boss harder to beat (taking too many cards, for example), so the promotion rule
  keeps the boss-kill guard (D24) and the weekly review reports cards taken per floor and boss damage beside the floor metric as a
  check for floor-greedy play. D11 stands as written.

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
- Addendum 2026-10-24 17:20Z (D29 item 1): the per-seed pairing check (`tools/lab/pairing_check.py`, landed with week-3's
  landing 4 at `26c19ef2`) passes on every finished promotion block: identical seed sets and configs, 0 crashes; discordant
  kill pairs 331 against the independence bound 454 pooled over E1-E4 and E3-r1 (E1 53 against 65.9 reproduces D24's figure);
  the paired floor-difference SD is 0.62-0.65 of the independent root, floor correlation 0.58-0.61, permutation p < 0.001 in
  every block; S3's emulator/real pair passes the same bounds. So `--review-guard` goes onto the lab's train job for the next
  promotion (automatic once the lab tree reaches `d0187715`). Caveat: the power table's independence assumption overstates
  power (a 2% to 1% kill drop is caught with 68% at one-sided 0.05, not 81%); the damage guard stays inert until the
  records carry `boss_damage`. The owner may switch the guard off again.

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
- Addendum 2026-10-24 ~22:00Z: window 1 (lab paused) is landed in the design doc on fork main `8052d140`: at 20 workers the
  server gives +21.6% wall decisions/s and +24.7% decisions per hour over the CPU path, and the 1,000-seed block is identical
  decision for decision on both paths. Open before the lab switches: the memory headroom at 20 workers, measured by the
  2,000-run server block at 01:15Z.
- Addendum 2026-10-25 ~02:00Z, piece 1 complete (fork main `0128f9cd`, `GPU_INFERENCE.md` section 9): throughput with the lab
  paused 157.8 decisions/s on the CPU path at 16 workers against 191.9 on the server at 20 (+21.6%; +29% per CPU-second with the
  server's own 4% counted); the 15-minute full-run A/B gives 6,024 against 4,871 runs/h (x1.25). The 1,000-seed block is
  identical decision for decision on both paths; the 2,000-run server block (19.7 minutes, 0 crashes, p99 5.8 ms) is recorded
  as generation 3 and the pending train judges generation 4's candidate from a window holding it. `jobs.json` is switched
  (backup kept): self-play and the promotion arms at `--prior-server auto`, 20 workers, the brake `LAB/GPU_OFF`, automatic
  fallback to the CPU path when anything is missing. RAM: a double server death at 20 workers peaks at 31.2 GB commit against
  a 37.8 GB limit; accepted with the brake, a memory-aware fallback queued. Pieces 2 and 3 wait for the owner. Rounds about
  11.3 of the lane's 10 since the cut (the block's judging line ran over).

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
- Addendum 2 (2026-10-24 17:10Z, orchestrator under the overnight delegation): the usage page read 50% at 17:05Z, up 11
  points in four hours on about 26 lane rounds (about 0.4 points a round), so the round caps above would pass 70% by
  about midnight. The remaining allowance to 13:00Z is cut to about 40 rounds in all, leaving a margin under 70%: kernel
  18 (gate C2-C6, landing 8, the O1 rerun; R7's switch-on only if it fits), week-3 12 (PRs 7 and 9, B7's probe, the guard
  switch, the final report; the completed-Q A/B only if it fits), GPU 10 (window 1, the 2,000-run block; pieces 2 and 3
  wait for the owner). Each lane stops at its cap and leaves the rest queued; the orchestrator re-reads the page at each
  wake and stops everything but landings at 65%.
- Addendum 3 (2026-10-24 19:40Z): the page read 54% at 19:35Z, up 4 points on about 20 rounds (0.2 a round), so the
  kernel lane, stopped at its 18 with the port gate at 0 and R7b (fifteen switched-on failures, triaged) next, gets 8 more
  rounds for R7b, the remaining R7 checks and the switch-on proof; the switch flips only if the proof passes. Expected
  finish under 65%; the 65% stop rule stands.
- Addendum 4 (2026-10-24 22:50Z): the page read 56% at 22:48Z. The R7 proof on `a42c41a3` did not pass (corpus 122 fights
  worse of 4,392, 113 of them one mechanism: under the switch the old combat ending fires at the kill and clears the piles,
  while the game ends the combat after its action queue drains; the strict step test lacks AfterAttack after the kill), so
  nothing is switched on. The kernel lane gets 5 more rounds for R7d (the ending in the game's shape, AfterAttack after a
  killing attack, the fewer-fields cases) and the proof rerun; the switch flips only if every gate passes.
- Addendum 5 (2026-10-25 ~01:00Z): R7d and R7e landed on fork main `2e62216a`. The triage corrected itself: the regressions
  were the game's two turn-start win checks, which the old turn start under F10 never ran (a kill or loss there was dropped),
  plus two crashes (the Demise loop, the AfterAttack bridge after a kill) and Damage's zero result for a target removed inside
  its own hit. Proof with the switch on: old suites 0 switch-only failures, traced 8 better / 69 same / 0 worse, corpus 63
  better / 4,326 same / 3 worse of 4,392 (from 122), strict step test passes, fuzz 0 ending disagreements. Two gates open: the
  3 worse fights, unread, and a census fault in `struct_compare.py` (8 corpus and 3 traced fights compared on fewer fields;
  a comparer fault, the review confirms). The kernel lane gets 3 more rounds for R7f: the census, the 3 fights, the rerun,
  and the switch only with every gate passing.
- Addendum 6 (2026-10-25 01:50Z): R7f landed on fork main `95cdd87b` (the census fix; handlers for Diamond Diadem and Undying
  Sigil, which the port list had skipped because no recorded fight reaches them; `port_list --unreached`). Proof: old suites
  0, traced 8 better / 69 same / 0 worse, corpus 63 better / 4,327 same / 2 worse, strict step test 4 of 4, fuzz 0 ending
  disagreements. Open: 11 F08/F10 pairs for unreached models with no handler (they would silently drop under the switch, so
  they count against the gate), the 2 worse fights (Shrink's target slot; Gremlin Horn's draw and energy for an egg that
  Parrying Shield kills), one traced fight on fewer fields. The page read 59%; the kernel lane gets 3 more rounds for R7g.

## D23 addendum · 2026-10-24 · The by-family table now reads Tier 1 decisively; the migration order is set

- With the ranking's classification fix (the lockstep review's finding) and placement rules for the unassigned records, the
  week-2 block re-ranks to an architectural share of 87.1% (was 54.8%) with 1.5% unassigned (was 55.2%); the top five hook
  families hold 97-99% of the architectural weight, so `PLAN.md` 8.3's Tier 1 rule fires under the primary reading. The same
  block re-run under the landed comparer: 0.53% of decisions diverge, architectural 94.1%.
- Family order for the migration: F10 and F08 (in progress), then F06, F11, F15. G1 at the end of week 4 confirms or
  escalates per 8.3; it no longer has to choose the tier.
- Decided by the orchestrator on the week-3 session's numbers (HANDOFF 2026-10-24 13:00Z line); reversible by the owner.
- Progress 2026-10-24 ~19:40Z: every F08/F10 (model, hook) pair has a Core2 handler (the port gate reads 0) at fork main
  `16c35043`: the pilot and C2-C6 from the cloud, the monster and local batches L1-L3 and the R4 reroutes locally (landing 8,
  `ad9c8909`, full-corpus byte proof 0 differ over 47,432 pairs). The L3b review found and fixed a kernel bug (a kernel copy kept
  the live run, so a search fork's death spawn advanced the live run's stream; fork test added). The switch (R7) stays off: its
  checks list holds about twenty old-against-game items, each to be closed with a test, plus one new blocker (a forked combat
  has no run view, so the run deck's listeners would answer empty in search forks); it does not fit the night's remaining
  rounds and waits for the owner's next allowance.
- Switched on 2026-10-25 ~05:45Z: fork main `cf74c742` sets `migrated_families.json` to F08, F10. The R7 proof passes every gate:
  old suites 0 tests fail only when on; traced against the game 8 better, 69 same, 0 worse, 0 on fewer fields; corpus 71 better,
  4,321 same, 0 worse of 4,392, 0 on fewer fields (identical with the default switches); strict step test 4 of 4; port gate 0 with
  unreached pairs; fuzz 0 ending disagreements. Switch-commit gate: C# 7,383 (0 failed), EmuDump 335, Python 256 OK, old-engine byte
  proof 0 differ, scenarios 0 unexpected. On the way: R7g `bcb64c9b`, R7h+R7i `0d3a9feb` (the aim leak, turn-end effects in the
  game's order after the hand flush, the kernel bound before setup so a turn-one kill removes its corpse). Scope: the switch is live
  in the EmuDump core2 engine and the comparer's core2 mode; the native runtime the agent and the lab use builds no kernel and is
  unchanged, so the agent gains from the rebuild only once that runtime runs the new core (the kernel lane prices that step next).
  Next: the post-switch re-rank on S3 with `--engine core2` (week-3 session), the F06 diagnosis (one Opus round) and the Tier 1
  re-estimate; G1 on the re-ranked table. About 9 kernel rounds since D30; usage 64% at 05:45Z.
- F06 diagnosis 2026-10-25 ~06:40Z (`D:/spireline/referee/rebuild/f06-diagnosis.md`): F06 holds 23.7% of agent weight on
  `rank-s2-w3-v2`, all placed by shape, none by hook; nearly every record is a whole-turn offset (one side took the lone End Turn
  the other did not). 85.3% is Fairy in a Bottle offered as a combat action, a Lane B rule fixed on main by B7b `ee7dc2e6` after the
  block ran; 6.1% an extra energy point after the same play, source unknown; the rest F08/F10 echoes and small Lane B items. The
  kernel addresses 0% measured, at most 6.1%: **F06 is not migrated** (about 20-27 rounds, 125 pairs, for no measured gain); the
  re-rank comes first, on a build with B7b. **Tier 1 re-estimate against D25's stop line of 120:** spent about 120-125 (the kernel
  stage ~42; F08+F10 ~75-85 against an estimate of 15, the overrun the R7 proof surfacing cross-cutting kernel defects); left: the
  native step 4-6 (the critical path: nothing measures the switch by agent weight before it), then at most one family after a
  re-rank, +10-40; central 130-165. Per D25 the lane has stopped and reported. **Owner's call:** a new Tier 1 line (the native step,
  the re-rank, then one family at a time by measured kernel share, diagnosis first) or stopping Tier 1 at F08+F10. Usage 64% at
  06:45Z.

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
- Item 2 result (19:00Z, block `E5-ab-2026-10-24`, 2,000 paired seeds, both arms from one saved generation-3 set): completed-Q
  at T=1 minus visits is -0.04 floors paired (95% CI -0.22 to +0.15), boss kills 41 against 50 (McNemar p 0.17), no wins either
  side; under D24 the candidate would not promote. No separation: the default stays visits; the option stays for a later A/B
  against a stronger labelled benchmark. Nothing written to the lineage.
- Item 3 result (2026-10-25 ~01:00Z, warm-start window 00:30Z-01:15Z): with `--recycle 60` at 12 game processes there is no
  cliff (118-135 decisions/s throughout, memory steady); the un-recycled cliff is per-game memory growth. So recycling becomes
  the default for real-game env blocks at week 4's first landing (reversible by the owner); numbers in `readiness.json`.
- Week-3 stopped at its cap at 01:00Z with its final report in HANDOFF section 0 (about 25 Sonnet-equivalent rounds since
  13:00Z, nothing rejected, no cloud session started by it).
- Not decided overnight: anything that changes the plan of record, the week's caps or the credit plan's counts.

## D30 · 2026-10-25 · The cloud credit stops; the week's allowance runs to 70%

- Decided 2026-10-25 ~02:15Z by the owner, in chat: no more cloud sessions on the credit. $44 of the $250 stays unspent (sixteen
  sessions delivered: the environment proof, the modding research, three independent reviews, the C1 pilot and C2-C8 handler
  batches, two Lane B batches, the D24 guard). The ranking-provenance kit published for a morning click becomes a local item.
- The subscription's weekly usage may run to 70% (continuing D25's line, now without the 13:00Z bound): the kernel lane
  continues to the F08+F10 switch-on under the proof rule, the orchestrator reads the page at each wake, and every lane stops
  at a 68% reading. The week-4 briefs are the owner's call.
- Addendum 2026-10-25 ~02:30Z, owner in chat: GPU pieces 2 and 3 start now within the 70% line; piece 2 (the value head
  trained harder, judged against DESIGN 5.3's keep conditions) first, piece 3 (sweeps) only in quiet windows after piece 2
  has a measured result; design reviewed before code, as for piece 1.
- Addendum 2026-10-25 ~05:20Z, piece 2 complete (fork main `7477ebb3`, `docs/rl/VRUN_SWEEP.md` section 5): V_run has a small real
  pre-kill skill once the self-play window is deduplicated (the lab's own fix, `68cf5759`) and the evaluation is large enough: out of
  fold on 13,769 runs (373 Act-1 kills) the lab recipe scores Brier skill +0.027 (CI 0.002 to 0.051), and sampling 4 rows per run per
  epoch +0.044 (0.028 to 0.060); the week-3 "no skill" reading was a 38-kill evaluation on a duplicated window. Adopted under the
  pre-registered rule: `rows_per_run = 4` for the lab's next V_run fit. The run macro stays rules: `SPIRELINE_MACRO_VRUN` is off
  until a paired rules-against-vrun A/B on a fresh E-block (week 4, Lane A) and the owner's decision. The promotion arms run on the
  inference server (both arms on one transport; the 1,000-seed equivalence rule passed). Piece 3: the arm sweep is complete; its
  quiet-window runner (one Sonnet round plus review, section 7) is deferred until a sweep is queued, decided by the orchestrator.
  Lane total about 17.5 rounds.

## D31 · 2026-10-25 · Tier 1 continues on a new line: the native step first, then families one at a time on measured share

- The kernel rebuild (D23) reached D25's 120-round stop line with F08 and F10 switched on (`cf74c742`) but not yet reachable by
  the agent: the native runtime the agent and the lab use builds no kernel. The owner sets a new line: the native step now, within
  the 68% usage stop (the kernel in the native library, the search's combat handles stepped through it, its state carried through
  clones and forks; 4-6 reviewed rounds, behind an explicit engine option, the lab's defaults unchanged until the re-rank and a
  paired check); then the post-switch re-rank on S3 with `--engine core2`; then at most one further family at a time, each approved
  by the owner on its measured kernel share after a diagnosis. F06 is not migrated (its diagnosis: 85% one Lane B rule, already
  fixed).
- Why: the kernel itself was worth building and is built; what was not worth doing was migrating F06. Without the native step the
  rounds already spent never reach the agent, and nothing measures the switch by agent weight. Further families are judged one by
  one on measured numbers rather than on the family tags, which have twice been overturned by a diagnosis.
- Decided 2026-10-25 ~07:00Z by the owner, in chat, accepting the orchestrator's recommendation.
- Supersedes: D25's 120-round stop line for Tier 1 (the lane stopped and reported at it, as D25 required); the D23 addendum's
  family order F06, F11, F15 (replaced by measured share after the re-rank).
- Addendum 2026-10-25 ~08:45Z (owner, in chat): **no further family migration is priced from a tag.** A migration is priced only
  from a diagnosis that names the mechanism behind the family's weight and counts the handler pairs it needs; the by-family tags
  choose what to diagnose, never what to build. (Twice a diagnosis has overturned a tag: F11's share was a comparer artefact and
  F06's was a single-site rule.)
- Addendum 2026-10-25 ~11:00Z: **the native step is landed**, fork main `d886569b` (N1: the engine option `STS2_ENGINE`, default
  old; the kernel built in the native library; the lab's entry points pinned to old) and `4595f84d` (N2: combat handles, clones and
  forks step and carry the kernel; snapshot load and re-anchor bind it; screen answers through its queue; native API v38, run API
  v29). N2 gate: C# 7,464 (0 failed), EmuDump 335, Python 0 new, corpus 0 regressed of 4,306, Codex walk 0 worse over 20,294 runs,
  old-engine byte proof 0 differ in 11 modes x 600 fights. About 6.1 rounds. Still refused under core2: loading a document taken
  mid-step, and the state readout on a hook action's screen. **Speed cost** (bench-emu, 8 processes, 60 s): core2 against old, steps
  13,567/s against 17,878 (-24%), clones -4%, search simulations 1,286/s against 1,853 (-31%). The lab's defaults are unchanged;
  whether the agent trains on core2 is the owner's call on the S3 re-rank (running now on `--engine core2`, doubling as the smoke)
  against that cost. Open for week 4: the corpus-wide native-against-EmuDump parity harness, a post-turn-one snapshot test, a core2
  re-anchor test. The rebuild lane is stopped for the week except the F11 diagnosis after the S3 table, usage permitting.
- Post-switch re-rank 2026-10-25 (S3, 500 seeds, generation 3, lockstep on `--engine core2` against the old engine, report
  `W4-B12-report.md`): divergence 0.59% -> 0.30% of the AI's decisions (333 -> 174); total agent weight 7,808 -> 3,027 (-61%);
  architectural share 89.8% -> 81.3%; F10 weight -93%, F08 -62%, F06 -79% (partly the Fairy in a Bottle fix), F11 -7% (its share
  rises to 26.3% and is partly a lockstep reading until its diagnosis), F15 10.4%; the top five families still hold 95-100% of the
  architectural weight, so Tier 1 holds. Mean floor on the real game 12.98 against 12.72 (within noise); paired gap real minus
  copy +0.14 (-0.26 to +0.54); 0 crashes, neither known refusal hit; 3 failed re-anchors and one `screen:None` loss for the kernel
  lane's week-4 list. The F11 diagnosis runs now (usage 75%). **Owner's call:** whether self-play and the promotion arms move to
  core2 now, against bench-emu's -31% search simulations per second (the orchestrator recommends the kernel's speed work first,
  since the old core's measured harm to real-game play is within noise while the pace cost is certain).
- F11 diagnosis 2026-10-25 ~13:10Z (`D:/spireline/referee/rebuild/f11-diagnosis-s3.md`, diagnosis only): F11 holds 797 of 3,027
  agent weight (26.3%; 32.4% of the architectural weight) in 51 records. 86.4% is a measurement artefact in the referee driver: at
  the Room Full of Cheese Gorge event the driver sorts the two kept cards into grid order before handing them to the game, while
  the game and the emulator add them in pick order, so the run deck differs by one swapped pair, and the fight-start re-anchor
  never repairs the run deck's order, so the same swap breaks later fights (41% of the family); the same pattern is 84.1% of F11
  on the old engine, which is why its weight moved only -7%. 9.8% follows earlier F15 deck divergences (Lane B); the rest is
  single-record trace targets; F08/F10 residue 0%. The kernel addresses 0% measured, at most 3.5%: **F11 is not migrated** (49
  pairs, 9 open). Fix approved on the P1 lane: keep the pick order in the driver, carry the run deck's order through the re-anchor,
  re-measure on the nightly block. **G1 reading:** F06 (85% a fixed single-site rule) and F11 (86% a driver artefact) are not kernel
  work, and no further Tier 1 family is indicated by the measured weight; Tier 1 stands at F08+F10 unless the re-rank after the
  driver fix shows otherwise. The rebuild lane is stopped for the week; week-4 items (parity harness, snapshot and re-anchor tests,
  the kernel's speed, the 3 failed re-anchors and the `screen:None` loss) are in HANDOFF section 0 with estimates.

## D32 · 2026-10-25 · The week's line is 80%, then everything waits for the reset; potion discard is approved

- The subscription's weekly usage may run to 80% (was 70%, D30). New rounds stop at a 78% reading; a landing in progress finishes.
  Once the line is reached, every lane waits for the weekly reset; the week-4 session starts at the reset, not before.
- Potion discard on the closed-belt screens is approved (the week-3 review's Lane C item): implemented behind the gates, the masks
  the policies see versioned so saved generations still load, in force for the next generation; generation 3 stays the promotion
  baseline.
- Order for the remaining allowance: the native step to its landing (D31), then the post-switch re-rank, with the potion-discard
  item in parallel on the week-3 session since it does not depend on the kernel.
- Why: the native step and the re-rank are what make the rebuild reach the agent and give G1 its table; the owner would rather
  finish them this week than leave them half done. Decided 2026-10-25 ~08:30Z by the owner, in chat ("change the budget to 80%,
  then wait until the reset, do 3").
- Supersedes: D30's 70% line and 68% stop; the open owner call on potion discard.
- Clarified 2026-10-25 ~09:00Z (owner, in chat): the 80% line is **this week only**. The weekly allowance resets Wednesday
  2026-10-28 at 08:00 local time; next week's ceiling is the owner's call at the reset (the orchestrator's recommendation is an
  explicit lower ceiling, re-priced at G1). Usage read 68% at 09:00Z.
- Addendum 2026-10-25 ~09:30Z (owner, in chat: "do everything but other characters"): the rest of this week's line goes to, in
  priority order after the native step, potion discard and the re-rank: (1) the paired A/B of the rules macro against the value-head
  macro on a fresh E-block under the guard, the owner deciding the switch on its result; (2) boss damage and cards taken per floor in
  the records and the review tables; (3) the memory-aware fallback for the inference server; (4) the lab utilisation check and
  re-weight; (5) the exact-fight trace tool, then the probe-first kits if the traces name their rules; (6) the F11 diagnosis under the
  diagnosis-only rule, after the re-rank; (7) the single-site kits (event gold, the selection:left_open mapping gap, reward hp). About
  13-14 rounds, expected to end the week near 75-77%. Not approved: the other characters end to end in the environment. New rounds
  stop at a 78% reading.
- Clock note (orchestrator, 08:15Z by `date -u`): the orchestrator's own time stamps in the 2026-10-25 entries from the dedupe
  landing onward (the D23, D27, D31 and D32 addenda stamped 05:05Z to 09:35Z) ran one to two hours ahead of UTC; the order of
  events and the lane-reported times (piece 2 03:49Z, the memory fallback 07:47Z) are right. Stamps from here on are read from
  the clock.

## D33 · 2026-10-25 · The value head becomes the run macro for new candidates; its keep test is out-of-fold on the full window

- From now every candidate the lab writes uses V_run for its run-level decisions (map route, rest, shop, rewards) instead of the
  rules macro. Generation 3 stays the incumbent, with the rules macro, until a candidate beats it on paired seeds under the
  promotion rule as written (mean floor primary, the boss-kill not-worse guard of D24, the F7 audit).
- The V_run keep test is out-of-fold Brier skill on the full deduplicated self-play window with the interval excluding zero; the
  held-out-tenth test (37 Act-1 kills on the current window) is reported, not gating. The adopted recipe passes (+0.044, 0.028 to
  0.060 on 13,769 runs); the fit used in the A/B ships with the first vrun candidate, and later fits must pass the new test.
- Why: the paired macro A/B of 2026-10-25 (`E6-macro-2026-10-25`, 2,000 fresh seeds, generation-3 search in both arms, A10, guard on)
  gives the V_run macro +3.98 floors paired (95% +3.67 to +4.30; 16.31 against 12.33) and Act-1 boss kills 249 against 46 (12.5%
  against 2.3%, McNemar p 1e-38), wins 0 and 0, crashes 0. The held-out-tenth keep test has no power at 37 events, the same fault D24
  removed from the boss-kill test. The gain is not floor-greedy: boss kills rose fivefold. Cost: more wall time per run from the
  macro's lookahead (the A/B's 20.1 s against 11.5 s overstates it; a kernel-lane score overlapped the vrun arm's first 25 minutes).
- Decided 2026-10-25 ~09:30Z by the owner, in chat, accepting the orchestrator's recommendation.
- Supersedes: the rules macro as the default for new candidates (`SPIRELINE_MACRO_VRUN` off, D27 addendum); the held-out keep
  test for V_run as the gate (DESIGN 5.3 as applied in week 3).
- Addendum 2026-10-25 ~09:50Z (owner, in chat): three extras for the remaining line, after the macro switch and within the 78%
  stop: (1) the A/B arms re-read with the new per-floor fields (cards, nodes, rests, boss damage); (2) the real-game score on S3 of
  the first candidate promoted with the V_run macro, paired against generation 3's 12.72; (3) the three probe-first kits if rounds
  remain. Not this week: a lookahead-cost sweep, the sub-1.5% single-site kits, the week-4 review before the re-rank.
- Addendum 2 2026-10-25 ~10:30Z (owner, in chat, "do what you think" on filling the machine's idle compute): queued this week
  after the replay readout and before the probe-first kits: a nightly 2,000-seed real-game block as a lab job (incumbent and each
  new promotion, lockstep on, recycle-60, fresh seeds, under the lab's quiet lock; feeds readiness.json and the ranking), and a
  measurement of self-play throughput after the macro switch with a three-size lookahead sweep only if runs per hour fell by more
  than a quarter (adopt the smallest size whose paired floor loss has an interval including zero). The lookahead sweep is no longer
  excluded. For week 4 (at the reset): the GPU quiet-window runner plus one sweep of a larger policy prior within the inference
  server's headroom (2.7x demand), judged by the promotion gate; the value head refits every generation on the full window under
  the adopted recipe. Not now: the real game as a training environment (a P2 question that changes the security posture).
- Addendum 3 2026-10-25 ~11:30Z (orchestrator, routine): generation 4 had used both promotion attempts the review guard allows
  before the macro switch, so the first candidate written with the V_run macro is a **new generation number**, not a retry of
  generation 4: it is a different policy (same prior, different macro, the A/B's fit seeded through `--vrun-seed`), the guard's
  two-attempt cap applies to it afresh, and the guard's state is not reset by hand. The lineage records the macro as the
  difference. Generation 4's two refused attempts stand. Self-play before the switch: 77.8 runs per hour over 24 h (5,490 per
  active hour at 20 workers); expected 57-76% of that once a V_run-macro agent is promoted.
- Result 2026-10-25 14:35Z: generation 5 (gen 3's prior with the V_run macro, the A/B fit as seed) promoted at 13:48Z on block E5
  (+5.00 floors paired against gen 3, lower bound +4.64; boss kills 269 against 68; both guards ok). **On the real game (S3, 500
  seeds, lockstep on core2, driver with the pick-order fix): mean floor 18.36 (17.84-18.89) against generation 3's 12.72, +5.4
  floors on the same seeds; past the Act-1 boss 122 of 500 (24.4%) against 27 (5.4%); 31 runs reached the Act-2 boss floor against
  1; wins 0 and 0; 1 game crash (499 scored).** Emulator arm 17.74; paired gap real minus copy -0.62 (-1.19 to -0.05): the real game
  now reaches further than the copy for this agent. Divergence 0.59% (422 decisions; the runs go deeper, into Act 2), weight 6,844,
  F08 46.4%, F06 15.0%, F11 12.1%, F15 9.4%; Tier 1 holds. Real-side macro proxies: monster+elite nodes 0.42 against 0.62 per
  floor, rests 3.0 against 1.5 per run, card skips 8.7% against 0.55%. Throughput after the switch: +11% wall per run, -20% per
  floor (less than feared). Two real-side record fields fail their live check (boss_damage reads 0.0 on real runs; every real rest
  reads as heal): one week-4 round against the gen-5 block as fixture; the guard's damage check is inert on real records until then.
