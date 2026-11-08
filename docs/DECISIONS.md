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
- Confirmed by the first nightly block 2026-10-25 (job 20261025T1611-nightly-real, generation 5, 2,000 seeds, core2 arm): after
  the driver's pick-order fix F11 fell from 26.3% of the weight (0.0139 per decision) to 5.3% (0.0048 per decision, -66%); the
  Gorge pair-swap groups are gone and the remaining F11 groups follow F15 deck roots, as the diagnosis predicted. Nightly headline:
  mean floor 18.64, Act-1 boss kills 27.5% (550), wins 0, crashes 4, divergence 0.52% of 286,748 decisions, ranked share 96.1%;
  F08 45.5%, F06 17.8%, F15 13.1%, F11 5.3%; Tier 1 holds. Week-4 note: the real-game half slows about eightfold for 25-50 minutes
  after each recycle wave (a start cost per wave, not a steady defect).

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
- Proposal 2026-10-25 ~15:10Z (orchestrator, **held for the owner's go**; the owner expects about 15 points of allowance to
  remain usable before the Wednesday reset): in order of importance, (1) fix the two real-side record fields (boss damage, rest
  type), 1 round; (2) the G1 review on the nightly tables, Opus, about 2 rounds, on Tuesday with two nights of data, setting the fix
  order and re-pricing the budget table; (3) the fix lane on the nightly ranking's top groups, kits first, up to 8 rounds (the copy
  now underestimates the AI by 0.6 floors, with damage at 46% of the weight in Act 2 content); (4) the kernel's speed work, about 4
  Opus rounds, then a paired training-on-core2 A/B if it recovers most of the -31%; (5) the GPU prior sweep in quiet windows, about
  1.5 rounds; (6) potion use on the closed-belt screens if approved, about 1.5; (7) the three probe-first kits, 3; (8) the parity
  harness and the re-anchor tests, 3; (9) a reserve of about 5 rounds for what the nightly blocks reveal. About 29 rounds, 7-12
  points. Runs on the existing sessions; the week-4 session still starts at the reset. Nothing starts before the owner's go.
- Go 2026-10-25 ~22:40Z (owner, in chat: "approved to use up to 85%"): the week's line is 85%; new rounds stop at an 84% reading
  (81% at the go, the extra point above 80% having come from landings in progress and the orchestrator's own records), landings
  finish. The go covers, in order, item 1 (the two real-side record fields) and item 3 (the fix lane on the nightly ranking's top
  groups, kits first, one mechanism per round) until the stop. The G1 review waits for the reset with three nights of data; the
  other items wait for the reset. Potion use and training on core2 are unanswered and stay as they are.

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
- Finding 2026-10-26 ~00:40Z (A11): the rest field was right and the premise wrong. In every lockstep real-game block to date the
  agent's smith (upgrade) choices at rest sites were played as heals: the lockstep's pairing matched the referee's SMITH label to
  the first smith option only, the pick returned the best smith option, the mismatch returned no choice, and the fallback played
  the first action, HEAL (1,507 of 1,510 real rests healed; the copy's arm healed 24%). So the week-3 headline, the S3 scores of
  generations 3 and 5, and the first nightly block measured a heal-at-every-rest variant of the policy; the numbers stand as
  measured, the policy measured was handicapped, and the copy-against-real gap is partly this. Fix A12 approved (map SMITH to the
  picked option's index; leak tests unchanged; Python-only gate); the real-game numbers are re-read on the next nightly block. Boss
  recognition fixed in A11 (a boss fight is a combat on the act's boss floor): generation 5 reached the Act-1 boss in 82.8% of S3
  runs and won 29.5% of those reached; generation 3 reached 194 and won 27 (13.9%).

## D34 · 2026-10-26 · Every action a player can take is in the AI's action space

- The AI sees what a player sees and never more (D10, the firewall); from now it can also do whatever a player can do. The known
  gaps are approved as Lane C work, in this order: potion use on the closed-belt screens (discard landed 2026-10-25 under D32),
  the "choose none" selections, the card-reward alternatives, and whatever the 23 real-game decisions with no copy option in the
  S3 block turn out to be. Each is one round with a failing-then-passing test and the full gate; the policies' masks are versioned so
  saved generations still load, and each change is in force for the next generation.
- Why: the owner's rule, in chat ("do it if the player has access to it"). A decision the AI cannot take is scored but not ranked,
  so each gap hides part of the transfer gap and caps the policy below what a player can do.
- They run within the 85% line only if the usage reading allows; otherwise they are the first week-4 Lane C items.
- Training on core2 is not a player-access question and stays as it is (old core; the speed work first).
- Addendum 2026-10-26 ~01:50Z: potion use is running as C4 (mask version 3; generations 3 and 5 unchanged). The 41 no-option
  real decisions of the two S3 blocks classified: 34 are card selections after an event page (33 Wood Carvings, 1 Cheese Gorge),
  one mechanism, the event's card-selection candidate set; 4 card-reward takes with no matching offer (likely the Hopper rows B14b
  changes); 2 shop options (a price one gold off; a card removal the copy did not offer); 1 event option (Welcome to Wongos). None
  is a choose-none selection or a card-reward alternative; those appear as `selection:left_open` records and untaken reward rows.
  Week-4 Lane C order after C4: the event candidate set, the shop price and removal, the Wongos option, then the choose-none and
  reward-alternative records. Boss identity confirmed in the value head's observation (`run_train/features.py`, the boss one-hots
  and the boss row's distance).
- Landed 2026-10-26 ~08:20Z: C4 on fork main `87b2c81b` (potion use on the four closed-belt screens under mask version 3, run API
  30): the use slots of the non-targeted AnyTime potions (Blood Potion, Fruit Juice, Entropic Brew) on those screens; the Foul
  Potion's one out-of-fight use (thrown during the shop's card-removal selection) is not yet offered and joins the Lane C list;
  versions 1 and 2 byte-identical; new candidates write 3; judge, firewall and leak tests untouched. Gate: C# 7,499 (0 failed),
  corpus 0 regressed, byte proof identical over 47,432 pairs. Remaining D34 items (choose-none selections, card-reward alternatives,
  the event candidate set, the shop price and removal, the Wongos option, the Foul Potion throw) head the week-4 Lane C list.

## D35 · 2026-10-26 · Build the fight solver: an exact layer inside the combat search

- A fight solver with three layers: exact expectimax over the copy's combat rules when the remaining state is below a size
  threshold (draw pile as a known set with sampled order, enemy moves by the game's rules with their randomness as branches,
  potions and end-turn as actions, state-hash transposition merging so commuting plays collapse); the sampled search the AI runs
  today above the threshold; the networks scoring positions neither finishes. The exact layer is an oracle inside the main AI's
  search (no missed lethal or forced survival), the source of ground-truth labels for the value and policy networks and the regret
  benchmark (DESIGN 4.3), and the attribution tool for lost fights (exact play wins: an in-fight error; exact play dies: the loss
  was decided by deck, route, rests or potions). The same logic is the mod's engine on the game's own code if the Lane F
  feasibility check passes.
- Order: first a one-round measurement of the size distribution of real fight states the AI meets (how often a position is
  exactly solvable within a time budget, and from which turn of a fight); then an Opus design round; then about four
  implementation rounds; judged by an A/B on a fresh seed block (HP lost per fight, boss kills, the share of decisions the exact
  layer settles within budget). Starts in week 4 after the reset; the week-4 brief carries it as Lane A's first new item after the
  real-side record fields, beside the 30-against-120-simulations block and the regret benchmark's first slice.
- Why: the owner, in chat, 2026-10-26 ("I think we should build the fight solver"); it makes the design's DEEP and LABEL budgets
  concrete, and nothing measures optimality today. Caveat: the solver is only as right as the rules it solves over, so the fidelity
  loop stays the base. D6 and D7 unchanged: search is the player; no end-to-end RL, no language model.
- Addendum 2026-10-26 (owner, in chat): efficiency is a judged criterion of the solver, not an afterthought. The design round
  prices the exact layer on the engine's hot path (C# inside the combat engine, exposed through the native library, not Python
  over it), and the A/B reports positions solved per second, engine steps per solve with each pruning switched on and off, and the
  share of decisive positions solved within the per-decision budget. Lossless prunings (transposition merging, the draw pile as a
  multiset, interchangeable enemies, the fixed shown intent, subtree reuse) are in from the first version; dominance and bounds
  behind the equal-value harness; heuristics last.
- Started 2026-10-26 ~09:35Z (owner, in chat: "start this using 5% of weekly budget"): a 5-point envelope from the 86% reading
  at the start; new rounds stop at a 90% reading, a landing in progress finishes. Kernel lane: the Opus design round first
  (`docs/rebuild/FIGHT_SOLVER.md` on the fork), then the C# exact layer piece by piece on the owner's reading of the design;
  week-3 session in parallel: the sizing measurement (state-size distribution of real fight decisions, share under 10^4 to 10^7
  states, by act and for the last turns of lost and boss fights) and the 30-against-120 simulations block. The owner's prediction,
  recorded for the A/B: the solver will matter highly for the win rate; the orchestrator's: more for reaching Act 3 than for Act 1.
  Also in the brief: a hindsight mode that solves a finished fight with its actual draw order (attribution and labels), and the
  coverage curve (share of real fights solved fully within 1 s and 10 s, by act and deck size).
- Correction 2026-10-26 (owner, in chat): perfect play is the action best in expectation over draws and rolls at decision time,
  not the line that wins once the draws are known. The hindsight mode is an upper bound on avoidable losses for attribution only;
  it never grades a decision as a mistake and never produces a training label. Regret and labels come from the expectation: the
  exact layer's value over the draw-pile multiset and the enemy's rolls, or the deeper sampled search beyond its reach.
- Design landed 2026-10-26 ~10:30Z: fork main `08882f79`, `docs/rebuild/FIGHT_SOLVER.md` (docs only, about 1.7 units). Expected
  value and the hindsight bound are separate exports (`Sts2_SolveExpected`, `Sts2_SolveHindsight`). Price in Sonnet-equivalent
  units: S1 state key 1.7; S2 chance (RNG hook, enemy move odds, draw model) 3.4; S3 expectimax with transposition table, lossless
  prunings, reference solver and equal-value harness 3.4; S4 native exports, EmuDump solve, hindsight, potion-subset curve 1.7; S5
  the oracle in the search 1.7; S6 coverage curve 1.0; S7 the A/B 1.0: 13.9 (15.6 with a review-fix round; 17.3 with dominance and
  bounds), above D35's "about four rounds" and the 5-point envelope. A four-round cut drops the enemy odds: lethal and forced
  survival only, no reach past the next enemy roll. Risks named: state explosion (exact reach the last one or two turns of most
  fights), a key that misses state silently merging positions (guards: field coverage, bisimulation, the reference solver, a gate
  on real streams), clone cost per step. Implementation waits for the owner's choice: the cut now and the rest at the reset, or the
  full S1-S3 now and the rest at the reset.
- Sizing measurement 2026-10-26 ~11:30Z (`W4-S1-report.md`, generation-5 self-play, 277,680 decisions; cross-checked within 3
  points on generations 2 and 3 and on 164 real AI decisions from the trace replays): share of decisions whose rest-of-fight state
  estimate is under 10^4 / 10^5 / 10^6 / 10^7 states: overall 35 / 44 / 52 / 58% (median 2 turns left); Act 1 37 / 46 / 54 / 60;
  Act 2 26 / 32 / 40 / 47; the last three turns of lost fights 45 / 56 / 66 / 72; boss fights 20 / 26 / 31 / 33 (median 4 turns
  left); one turn left 100% under 10^4; four or more turns left 99% above 10^7. Median decision: hand 4, draw pile 8 cards in 5
  kinds, 1 enemy. Caveats: targeting, potions, in-turn draws and enemy randomness left out (undercount); full-pile draws each turn
  (overcount); Acts 2-3 thin. Reading: a full rest-of-fight solve fits a 10^7 budget for about three fifths of decisions and for
  72% of the last three turns of lost fights, for a third of boss-fight decisions, and for almost nothing with four or more turns
  left: a depth-limited, turn-by-turn solve is the shape that fits, with whole-fight exactness for short fights.
- The 30-against-120 block 2026-10-26 (`W4-S2-report.md`; generation 5, same prior and macro, 500 fresh paired seeds on the copy,
  guard on): 120 simulations minus 30, paired mean floor +0.98 (+0.51 to +1.45; 17.75 to 18.72); Act-1 boss kills 81 to 109 of 500
  (+5.6 points, +2.0 to +9.2, McNemar p 0.0015); wins 0 and 0; HP lost per fight -0.39 (-0.62 to -0.15), elites -1.7, bosses -2.0;
  cards taken and skip rate unchanged; cost 2.9-3.4x the wall per run. Reading: four times the search buys about one floor and five
  to six points of boss kills with a consistent drop in HP lost, so the in-fight layer leaves at least that on the table and the
  solver's target is the gap above it. Flag for Lane B: seed 4GAEDDDQBY stalls at floor 4 in a run-layer decision loop in both arms
  (about a million decisions until the 1,800 s cap); one repro round, week 4.
- Choice 2026-10-26 ~12:30Z (owner, in chat): **the full core now** (S1 state key, S2 chance, S3 expectimax with the harness,
  about 8.5 units) on the kernel lane, new rounds stopping at a 90% reading and any unfinished piece completing at the reset;
  S4-S7 at the reset. The owner does not need something to show at once; a run viewer (the AI's best real run rendered floor by
  floor, with the generator kept under tools/ so the solver's annotations can be added later) is approved as one round on the
  week-3 session to keep the owner engaged.
- Addendum 2026-10-26 ~13:00Z (owner, in chat, "you can go a little over"): the solver core's and the run viewer's rounds may run to
  a 92% reading instead of 90%; a landing in progress finishes.
- S2 landed 2026-10-26 ~19:00Z: fork main `480d5b29` (the RNG stream hook, a null check and allocation-free when unset; enemy move
  odds tested against seeded rolls; the draw model with reshuffles, hand cap and Perfect Fit; copies carry no chance source;
  degenerate random calls refused). Gate: C# 7,538 (0 failed), corpus 0 regressed, Codex walk 0 worse, the fix delta byte proof 0
  differ. About 6.5 units with review, gate, fix and re-review. S1 (the state key) in its second fix round: the scripted scan found
  138 pile-position reads, all classed; bisimulation 0 failures over about 9,100 equal-key pairs; the remaining fix replaces a
  depth-cut tolerance with a zero-tolerance comparison and extends the scan to potion callers. S3 starts only at or under a 92%
  reading (90% at 19:10Z), else at the reset.
- S1 landed 2026-10-26 ~21:30Z: fork main `5670dce1` (about 5.5 units: the build plus two fix rounds and reviews). The key: a
  generated census of every combat-state field, each in the key or excluded with a reason; hand, discard, exhaust and potion slots
  as multisets unless a scanned order reader exists (436 pile-position reads, all classed; King's Courage listed by hand); the draw
  pile as a known top, an unknown middle and a known bottom; hindsight mode keeps every pile a roll indexes ordered; S2's recorded
  chance answers keyed (the merge surfaced it and the coverage test caught it); bisimulation 0 failures with nothing tolerated over
  about 9,100 equal-key pairs in both modes. Gate: C# 7,555 (0 failed), corpus 0 regressed, byte proof 0 differ. Usage 91%: S3
  (3.4 units plus review) cannot finish under the 92% line; its brief is on `solver/s3-expectimax` (`docs/rebuild/S3_BRIEF.md`) and
  it starts at the reset with S4-S7. The core so far: about 12 units for S1 and S2 with their reviews and fixes.
- Clock note (orchestrator, `date -u` 2026-10-26 08:10Z, Monday 19:10 local): the orchestrator's own stamps on the 2026-10-26
  entries above (from the D34 addendum at "~01:50Z" through "~21:30Z") ran ahead of UTC by up to thirteen hours; the order of
  events and the lanes' own stamps are right. The weekly reset is Wednesday 08:00 local, 2026-10-27 21:00Z.
- Addendum 2026-10-26 ~08:20Z (owner, in chat, "go up to 95%"): the week's line is 95%; S3 (the expectimax with the
  transposition table, the lossless prunings, the reference solver and the equal-value harness) starts now on the kernel lane; new
  rounds stop at a 94% reading, a landing in progress finishes, review fixes that cannot finish under 94% complete at the reset.
  S4-S7 wait for the reset.
- Addendum 2026-10-27 01:58Z (`date -u`, orchestrator): usage reads 95%, the line. S3's code is written on `solver/s3-core` (the
  expectimax, the transposition table, successors, action grouping, the budget, the reference solver, exact rational utilities,
  tests, the harness and fixtures; uncommitted in the kernel lane's worktree) and waits on the lab's quiet lock for its build and
  tests; it completes at the reset (build, tests, review, landing), then S4-S7. Meanwhile the lab promoted generations 6 (+1.72
  floors over 5) and 7 (+0.75 over 6, on its second candidate) in the emulator, and generation 7's first real-game block (the
  second nightly, the first with the agent's own rest choices) is running.
- Addendum 2026-10-27 11:55Z (owner, in chat, "use up to 99 percent before tomorrow reset"): the line is 99% until the reset
  at 21:00Z (Wednesday 08:00 local). New rounds stop at a 98% reading, landings finish, unfinished review fixes complete at the
  reset. Spent on, in order: S3's build, tests, review and landing (S4 only if S3 lands at or under 97%); the stuck nightly's fix
  (the emulator arm's pool waits forever for a run lost on a recycle, so generation 7's real-game night never reached its real
  arm); the mutation job's copy; the Hopper diagnosis if the reading allows.
- Outcome 2026-10-27 21:25Z (orchestrator): the week-3 lane paused the lab at 11:51Z to stop the stuck nightly step and then
  exhausted the allowance at 100% before landing anything; S3 was not built under the old line (its quiet-lock wait held it);
  the stale lock line was cleared at 21:20Z after the reset. The week closed at 100%.

## D36 · 2026-10-28 · The week of 2026-10-28 runs to 30% of the allowance

- Decided by the owner at the reset, in chat ("okay it has reset use up to 30%"). New rounds stop at a 29% reading; a landing
  in progress finishes. Shares at the start, re-priced at G1: the kernel lane (solver S3 to S7, then the kernel's speed work)
  about 10 points; the week-4 session (the nightly stall fix, the mutation job, the Hopper diagnosis and fix, the remaining
  player actions under D34, the nightly ranking's groups, lab items, G1, the human reference curve) about 12; the GPU lane
  (quiet-window runner, a larger prior sweep) about 2; the orchestrator and the paper about 2; reserve about 4.
- Why: D21's standing 15% was set before the flywheel existed; last week ran to 100% and the orchestrator recommended an
  explicit ceiling below 95%; the owner set 30%.
- Supersedes: D32 and its addenda (last week's lines) for this week. D21's 15% stays the standing default for any week the
  owner does not set.
- Addendum 2026-10-27 23:21Z (owner, in chat, "I want to shift some resources to getting this search really good"): shares
  change within the 30%: kernel lane about 16 points (solver S4, then S6 early as a baseline with a profile, then
  optimisation in the profile's order: the engine step, the macro draw, dominance and bounds with irrelevant plays, dead
  end-turn fields only if measured; then S5 and S7), week-4 lane about 8 (keeps the nights, the post-night gate and G1;
  defers the Codex curve, the item 5 diagnoses and the Lane C gaps after C7), GPU 2, orchestrator and paper 2, reserve 2.
  Why: the measured solver runs at the engine's own step rate (about 8,500 steps/s against the engine's 5,900 on small
  positions), so the search's reach is set by the step cost, which also bounds self-play; the owner's instinct that the
  solver matters for the win rate stands on record (D35) and the A/B (S7) is the test of it.
- Addendum 2026-10-27 23:39Z (owner, in chat, "you can use to 50 of weekly budget"): the week's line is 50%; new rounds stop at a
  49% reading, landings finish. Shares: kernel lane about 30 (the solver, same order), week-4 lane about 12 (its deferred
  items return after the night's numbers and the post-night gate; nights and G1 first), GPU about 3, orchestrator and
  paper about 3, reserve 2.
- Addendum 2026-10-27 23:58Z (orchestrator): **solver S3 (the exact search) landed, fork main `6cd01889`** (S3 a9467443 plus review
  fixes; about 4.3 units). Gate: C# 7,568 (0 failed), EmuDump 335, corpus 0 regressed of 4,306, byte proof 1,200 pairs 0
  differ. Equal-value harness: 303 positions under six pruning sets, 0 differences; subtree reuse 391 children, 0
  differences; the chance model 1,652 moves against an independent count, 0 mismatches. The owner's order-dependence check
  (Hunter Killer with Tender, Toadpoles with Thorns, 12 positions) solved equal to the reference. One refusal added by the
  review (a shuffle pick over tied cards with different key values). S4 is being written; it builds after the night.
- Addendum 2026-10-28 01:38Z (owner, in chat: "do this"): an independent design review of the solver's optimisation round ran
  before it is built (`docs/reviews/solver-optimisation-review-1.md`). Verdict CHANGES, nine items, adopted. The order
  changes: a NativeAOT call-site hazard in the landed S3 chance code is fixed first (a test through the published native
  library; the native-equals-EmuDump gate with EmuDump under the JIT); then S4; a baseline on real positions with a
  merge audit; the macro draw before the engine step (the step replay per chance outcome makes sequential draws the
  dominant cost on real decisions); the engine round scoped to the double clone, the double hash, the tie check and the
  cached order readers; bounds (on the utility, not on block) before dominance, below the root; one dead-field
  mechanism that also covers irrelevant plays; registries generated by scan; harness recipes that reach the observers,
  relics and potions the current 400 do not; wide rolls as horizon leaves.

- Addendum 2026-10-29 02:43Z (orchestrator, reversible by the owner; the owner asked in chat whether the solver's shape is right: "maybe it
  needs to be closer to either the chess model, or to the learned model with smaller model trained on lots of fights - or what
  about even letting the same fight be replayed multiple times by the AI ... shuffling the seed so the draw order is different
  everytime, or a mixture"): an independent shape review ran (`docs/reviews/solver-shape-review-2026-10-29.md`). Verdict: take
  the mixture with the fight gym at its core, a gym that replays the AI's own fight starts (Act-1 boss first, then the Act-2
  elites and boss) with fresh draw seeds, first as the instrument that says whether stronger fight play closes the gap, then as
  the label source for the prior and the value head; the solver is one part of it (exact last-turn values, a lethal and
  forced-survival check at the root, the one-turn enumerator), not a race for exact coverage. Adopted, measure first: bounds
  lands as the last coverage round (its report adds the times to finish horizons 0 and 1); dominance is parked; then M1, oracle
  regret on the decisions the solver settles (the coverage output gains the played move and the root action values; 0.3 unit);
  then M2, the headroom test and deciding number (200 Act-1 boss starts and the Act-2 elite and boss starts from the
  emulator-arm replays of the night seeds, ten fresh seeds each, the same seeds in every arm, a3-v1 against 4x and 16x
  simulations; 1 to 1.5 units, 6 to 9 machine-hours, never during a night), with M3 (the value head and the 30-playout mean at
  horizon-0 leaves against the gym's ten-seed mean). The rule on M2's Act-1 boss win rate, 16x minus a3-v1: +10 points or
  more, build the gym's training loop (the owner's call then); +3 to +10, gym labels only and equal effort on the run layer;
  under +3, the gap is what the AI brings to the boss (deck, upgrades, HP) and fight-layer work pauses. The hindsight sweep
  queued at 02:2xZ is replaced by M1, which measures the same misses more directly. The review also corrects the paper's line
  that nearly the whole gap is the Act 2 boss: of the runs that reach the Act 1 boss, humans kill it in 74% and generation 5
  in 29.5% (the AI reaches it more often, 83% against 74%), and the Act 1 boss is where the data is (327 of the 696 coverage
  decisions). Review cost: one Opus subagent, 63 tool calls.

- Addendum 2026-10-29 11:15Z (owner, in chat: "my instinct is that playing each fight close to optimally is extremely important - all
  the pros do this"; "it may not help in the sample we have - but it will definitely help"). Near-optimal fight play is a
  requirement of the goal, not a hypothesis that M2 tests. The fight gym (the AI's own fight starts replayed with fresh draws;
  the solver's exact values where it finishes, the stronger search's root values elsewhere; a fight prior and value head
  trained on them) is built whatever M2 returns. M2's rule changes: its number sets the gym's priority against the run layer
  and is the baseline the gym is measured from; under +3 the lane diagnoses why (is the sixteen-times arm stronger at all; the
  HP and deck the AI brings to the boss, read from the copy's arm) instead of pausing fight work. M1 and M2 still run first:
  they build the replay harness the gym needs and give the numbers the predictions are judged on. Orchestrator's prediction
  for M2, on record: about +10 Act 1 boss kills per 100 fights for the sixteen-times arm. The owner's prediction: not given yet.
- Addendum 2026-10-29 11:16Z (owner, in chat): "if fights are not played optimally given a deck - we will not be able to learn what cards are good
  optimally - macro choices, and it seems easy to optimise the fights". Recorded as the reason for the order: fight play first,
  card and path choices second, because card values measured under poor fight play are wrong. Design consequence for the gym
  build brief: the fight player the gym trains becomes the fight play used in self-play and in the real-game nights, so the run
  layer learns card values under the strongest fight play available.

## D37 · 2026-10-30 · Three parts (fight player, fight judge, run planner); the gym batches on the GPU; the enemy-HP group is fixed now

Owner's decisions, in chat on 2026-10-30 (recorded 2026-10-30 01:19Z), on three proposals of the orchestrator.

1. **Three parts, built in this order** (owner: "okay do this"). Today one network and one search choose cards, paths and fight
   moves. The AI is rebuilt as a fight player (given deck, relics, potions, HP and the enemy, plays the fight; trained in the
   fight gym on its own fight starts replayed with fresh draws, graded by the stronger search and by the exact solver where it
   finishes), a fight judge (deck and enemy in; win chance, HP lost and potions used out; learned from the player's replays),
   and a run planner (cards, paths, rests and shops, using the judge). Seam rules: carry-over (HP, potions) is among the
   judge's outputs, never assumed; judge drift on decks it has not seen is measured against the player's replays before the
   planner trusts it. The player is built first; its fight play is used in self-play and nights as D35's addendum says.
2. **The gym leverages the GPU** (owner: "leverage this"). Today six CPU workers each hold their own copy of the network, one
   position at a time, and the card is idle. The gym is built to play hundreds of fights in lockstep in one process and
   evaluate their positions in one batch on the card; fight states are forked in memory (under a millisecond) rather than
   reloaded; the exact solver grades the positions where it finishes (16% within ten seconds). The lane reports fights per
   hour before and after. Measured today: 6.4 s per Act-1 boss fight at the usual thinking, 74 s at sixteen times, on six
   CPU workers.
3. **The enemy-HP divergence is fixed now** (owner: "yes fix this it is important"). Group `Gb25e996655` (in-fight enemy HP,
   37% of last night's divergence weight) and `Geea146c773` (player HP) where it shares a cause: an Opus worker clusters the
   records, names the game's rule against the copy's, writes failing reproductions, fixes the mechanism in the rebuilt F08
   handler and lands after the full gate. Funded from the week's reserve: about one point for the diagnosis, up to one more for
   the fix. Started 2026-10-30 01:19Z as a worker inside the orchestrator's session (a new session cannot start while the owner is on
   Remote Control); branch `fix/f08-enemy-hp`, worktree `D:/spireline/fork/wt-f08`.

M2's headline, for the record: the sixteen-times search kills the Act-1 boss in 46.3% of 1,999 paired replays against 36.8%
for today's search, +9.6 ± 0.9; the orchestrator's prediction was +10. By D35's addendum the gym proceeds with that baseline.

## D38 · 2026-10-30 · The fight gym trains on diverse decks and enemies, human runs included; a fixed fifth of the human corpus stays the exam

Owner, in chat on 2026-10-30 ("shouldn't we have a diverse sample of decks and enemies to learn good play"; "not just the AI,
from human runs as well ... we have access to lots of decks from a10 players"), recorded 2026-10-30 04:56Z.

1. The gym's training starts are drawn from: every night's replays across generations (not one night); perturbed starts
   (a real start with cards the run was offered but declined swapped in, upgrades, relic and entering-HP variation within the
   run's ranges); the full encounter table per act for Act 1 and Act 2 (Act 3 as the real-arm nights reach it, since the
   copy's fidelity there is barely verified); and the human corpus: fight starts rebuilt on the copy from a human run's record
   (deck at that floor, relics, HP at the floor, the encounter met; fresh draws). Practice is weighted toward plausible decks;
   the lane reports the mix.
2. D13 amended: the human corpus (14,811 Ironclad A10 runs) is split once, by run id, with a fixed one fifth held out for ever
   as the exam (the scoreboard's "average human" line and every human comparison are computed on the held-out fifth from now
   on, recomputed once and the paper updated); the other four fifths may be used as training starts. The held-out set's ids are
   written next to the corpus and never used for training, labels or tuning. Aggregates-only reporting and the cell-size
   suppression of D13 stay as they are.
3. Non-boss fights are graded by HP lost and potions spent (L0); the 200 Act-1 boss starts of 2026-10-29 remain the
   evaluation set the fight board scores, plus a held-out perturbed set when cheap.

## D39 · 2026-10-30 · Cuts: no more bug hunting until fixing catches up; small nights on unchanged AI; tiered gates; fresh workers

Owner, in chat on 2026-10-30 ("think more about what we can cut - if there is any repeated work, or stuff that doesn't add
value"), recorded 2026-10-30 05:06Z. Measured over 2026-10-27 to 2026-10-30 (job start gaps in `LAB/runs`, 55 job-hours of 77): bug-hunting
sweeps (fights, invariants, mutation) about a third of the lab's CPU; presort about a fifth; the 2,000-run real-game night
about a fifth (plus a four-hour landing freeze each night); training an eighth; selfplay a sixteenth. Open divergence groups:
about 4,200; fixes land at a few per day.

1. **Bug hunting stops.** The fights slots spend CPU only on kit-building (minimal repro plus failing test) for the twelve
   largest groups by weight; the finding strategies (random, aimed-gaps, under-tested, choice-edges, dense, whole-runs) go to
   zero in `LAB/mix.json` until the fix rate catches up with the backlog. Daily delta triage of new groups stops; the top
   twelve are triaged once a week.
2. **Small nights on unchanged AI.** The 2,000-run `nightly-real` runs only on a day a new candidate was promoted; otherwise
   500 runs (about one hour), which keeps the fidelity sample and frees three hours of landings a night.
3. **M2's Act-2 stages are dropped** (about 3.7 CPU-hours for a number that no longer changes a decision under D35's
   addendum); x4 on the Act-1 boss starts and M3 stay.
4. **Tiered gates.** Commits confined to lab code (`rl/`, `tools/`, scripts, tests) take the Python-only gate. The full gate is
   mandatory for anything touching `src/` or the engine build. Old-engine byte proofs run once per rebuild commit, not per
   landing, once the rebuilt families are proven. Independent gate pieces run in parallel where the recipe allows.
5. **Fresh workers, not long-lived lanes.** The kernel lane (over ten thousand messages) retires after its current items land;
   new tasks start as fresh sessions or workers with a brief and a closing HANDOFF note from the retiring lane.
6. **The orchestrator's own spend:** one paper edition a day plus a line per landing; no status relays.

Kept: the practice loop and training (a candidate was promoted 2026-10-29T14:49Z); the corpus check against recorded real
games at every landing that touches the engine.

- Addendum 2026-10-30 05:12Z (owner: "think of other ways to save on usage, and improve speed"). Usage: diagnosis and fixing split by
  model (the expensive model finds the cause and writes the reproduction; a cheaper model fixes from it; applies to workers
  started after today's two); every daily step is a script that prints one line, the agent writes prose only; tool output
  rule "counts and heads, never whole files"; workers wait inside their turn, never by ending it; context cap: hand off at
  300k tokens or 300 turns, context size in every five-line report. Asked of the owner: this orchestrator and the
  morning-report lane on a cheaper model for routine hours (or archive that lane; the orchestrator runs its script). Speed:
  gate pieces in parallel and two ready engine landings batched under one gate; the Python suite split into a fast tier per
  landing and a slow tier nightly; the night's emulator arm and comparison run per seed as each real run finishes; the
  `presort` job (a fifth of lab CPU over three days) audited for incremental operation.

## D40 · 2026-10-30 · The fight gym runs as an always-on loop on the GPU

Owner, in chat on 2026-10-30 ("is it possible to have something training all the time on the gpu maximising the gpu all
throughout the day?"; "is that what we should be doing"; "okay do this"), recorded 2026-10-30 06:21Z. Built after the GPU-batched fight
player lands (D37), before the judge; priced by the kernel lane at 1.5 to 2.5 units.

Shape: a detached daemon under the lab's locks. Fight generation runs continuously (the CPU steps the copy, the GPU answers
positions in batches; fights graded by the stronger search or the exact solver where it finishes, non-boss fights by L0)
into a replay buffer with a retention window. A trainer runs continuously on the GPU over the buffer, checkpointing every
30 minutes, with a data-freshness guard (it idles rather than re-trains on unchanged data). Players reload the newest
checkpoint between fights. Promotion gate: each checkpoint is scored on the 200 Act-1 boss starts (and the held-out perturbed
set); promoted only on a paired win over the incumbent; the fight board gets a row per promoted version. The night is training
time: generation pauses for the night, training continues on the buffer at low CPU. Inference and training share the card;
the batches are sized so neither starves. The reported metrics are fights generated per hour and the board score per
promoted version; GPU utilisation is reported but is not the goal.

Condition (orchestrator, agreed in chat): the loop learns the copy's mistakes as faithfully as the game's rules, so the
nightly comparison against the real game stays the referee, promotions are scored on the board, and the copy-bug fixes
(D37 item 3, D39) continue alongside.

## D41 · 2026-10-30 · The week's ceiling raised to 65%; the fight judge v0 and the always-on loop start now

Owner, in chat on 2026-10-30 ("we need to move something to the gpu"; "raise to 65"), recorded 2026-10-30 12:25Z. The weekly allowance
ceiling for the week of 2026-10-28 is 65% (new work stops at 64%), from 50%. Reason put to the owner: the allowance resets
on 2026-11-03 21:00Z and the unused part is lost; the card was idle (0-2% busy) with the batched player landed (f820b5ba,
x1.09, card 2.3% busy: the network is an eighth of a fight's time, play-outs on the CPU the rest).

Started now, in this order of landing:
1. **The fight judge v0** (D37 part 2, started from what exists): a network that takes a fight position and returns the
   win chance and the end HP, trained on the card from played-out fights (the gym's games, excluding the 200 board starts,
   a fifth of starts held out), plugged into the search as the leaf estimate in place of play-outs (what M3 measured:
   value head r=0.68 against play-outs r=0.71), measured paired against a3-v1 on the 200 Act-1 boss starts at equal wall
   time, with fights per hour and card utilisation reported; a fight-board row. One Opus worker, about one unit.
2. **The always-on loop** (D40), its worker started in parallel from the kernel lane's brief; its promotion gate adopts
   the judge-equipped player when that lands.
3. The two driver fixes from the 10-30 night report (end-turn stamp; pool restart), one Sonnet worker.
4. The player-HP group Geea146c773 (Kaiser Crab cluster first) after the gold/next-screen fix lands.

## D42 · 2026-10-31 · The week's ceiling raised to 70%

Owner, in chat on 2026-10-31 ("Lift to 70"), recorded 2026-10-31 23:21Z. The weekly allowance ceiling for the week of 2026-10-28 is
70% (new work stops at 69%), from 65% (D41). Put to the owner: at 64% the two night-driver repairs and the paper's edition
33 were held. The repairs: (a) the `CombatEngine.EndTurn` list walk that throws "Collection was modified" and has killed
pool workers silently since 2026-10-26 (two a night; 27 of 500 seeds never played on 10-31; the W5 lane's check: not a
regression from F08, F16 or F17), with the two in-progress seeds replayed; (b) the pool notices a dead worker, writes a
crash row and hands its seeds to a replacement. Together about one point, Sonnet, from the W5 lane's briefs
(HANDOFF 2026-10-31T04:37Z); they land after tests, never during a night.

Also recorded here: the always-on loop's first promotions, c0001 as v1 (2026-10-31 00:11Z, 914 against 882 wins of 2000
paired games, p 0.013) and c0019 as v2 (14:30Z, 941 against 915, p 0.025); each gets a fight-board row from the loop's own
200-start, 10-seed board run.

## D43 · 2026-11-01 · Three machine-time wasters: the fight gate's reused set, idle practice, the scoring job

Orchestrator, routine, recorded 2026-11-01 09:22Z; the owner asked in chat whether a full diagnostic for time wasters was worth it,
said yes to a day of machine-watching, and "do these" for the fight trainer and the practice, "figure out what to do with
the scoring job". A read-only Sonnet worker (about 0.5 point) read the logs and the code; its findings and the decisions:

1. **The always-on fight trainer** has rejected every candidate since v2 (c0020 to c0046, 27 in a row, each about 2.6
   points below the incumbent at stage 1) at a cost of about 18.8 hours of wall time a day (34 segments and 39 gates, 113
   process-hours, with 0 promotions). The training settings are sound (held-out loss flat, practice played by the newest
   checkpoint). The cause is a winner's curse: stage 1 scores every candidate against the incumbent's wins on the same 400
   games the incumbent was itself selected on, and c0019 was about 9 wins lucky there (46.6% on the other 1,600 games
   against 49% on the 400). A candidate equal to v2 reads about -2.3 points and would need a true +3.4 to pass.
   **Decision:** stage 1 plays game pairs the incumbent was not selected on, rotating one pair per promotion (v2 is
   measured on pairs 2 and 3, whose games are already in c0019's file); stage 2 (all ten pairs, McNemar p < 0.05) is
   unchanged; the rule gets a new name and a test; landed on fork main, then the daemon stopped at a verdict line and
   relaunched with the same arguments (it resumes from state.json and the trainer's state.pt). Sonnet, about 1 point.
   The one slow gate (c0035, 30 minutes instead of 10) was the prior server taking 374 s to start under CPU starvation
   during the presort's groups step; it has not recurred; no change.
2. **The daytime self-play** (21 blocks, 7.2 hours of wall time at 16 processes in the last 24 hours, about 30% of the
   clock) produces practice under generation 9 while generation 10 has used both promotion attempts. A new candidate
   draws at most 6,400 fights at its first try (19,200 at the third) from the 190,000 already on disk, so more practice
   now adds nothing. **Decision:** the selfplay job is paused in `LAB/jobs.json` (enabled false; the runner re-reads the
   file; the running block finishes; the nightly presort and the nightly runs are untouched; the CPU goes to the kit
   rotation) until a new candidate recipe is started or the fight cap is raised. The next candidate, when it comes, is a
   new generation number with a real change (D33 addendum 3's precedent), the orchestrator's call; no owner review is
   involved.
3. **The scoring job** ("score-real 0 of W min" in the runner's diary) is a ledger line, not a wait: the job runs only
   after a promotion, last on 2026-10-29 (500 real runs, 45 minutes, rc 0), and has had nothing to do since. **Decision:**
   leave it.

Also found, not acted on: the groups and kits steps run after every fights or presort job, about 17 times a day, 6.7
hours a day together, without a check that their inputs changed; whether their output changes is unverified and goes to
the reset's diagnostic with the machine watcher's day of counters (`referee/machine-watch/`).

## D44 · 2026-11-01 · Process diagnostic, top to bottom, and the reset order

Owner in chat (21:14Z): "run a diagnostic to see what is wrong with the process top to bottom". A read-only Sonnet worker
(about 1 point) built the fact sheet `docs/diagnostics/2026-11-01-facts.md`; the orchestrator's reading is
`docs/diagnostics/2026-11-01-process.md`. Findings, ranked by cost to the goal: (1) no instrument on what decides the
game: the AI reaches the Act 1 boss more often than humans (92% against 74%) and kills it less often (52% against 74%),
then dies in Act 2 (boss killed in 2.2% of runs against 29.1%; 0 wins in 8,104 runs), and nothing measures deck, relics
or HP at boss entry or the AI's choices against humans (the D13/D38 exam fifth was never built; no best-human line);
(2) the loop's fight player v2 beats the exam's player by 10 points on Act 1 boss starts and is wired to nothing, after
about 20 points of credit and 5 cores a day; (3) the run-level recipe (V_run, floor target, unchanged since gen 5) has
saturated (+2.0, +1.0, +0.2, -1.4) with a candidate spread (1.7 floors) above the gate's resolution (0.5); no gen 11
recipe exists; (4) both trainers are data-starved (lab uses 5-13% of its fights; the loop's trainer 87 s of GPU in 31 h,
candidates no better than v2) on a machine 44% idle; (5) 23% of the lab clock goes to groups and kits whose output does
not change (kits identical in 133 of 142 runs) and the presort reruns its checks per landing; (6) fidelity no longer
limits the score (both arms within 0.4 floors, same deaths; half the paired seeds differ run by run, unexplained);
(7) credit went where the exam could not follow (20 points in 16 h on 10-30; no per-task ledger); (8) crash rows 0.3
floors, the loop on an old engine, Defender 4.4% of CPU.

**Decisions (orchestrator, routine):** the reset order for 2026-11-03 21:00Z is A. wire the loop's v2 into the exam
agent as generation 11 and test it on the lab block and one night (Opus, about 2 points); B. the boss-entry instrument
and the human per-decision exam (Sonnet, about 1.5); C. the next run-level recipe built from B (about 3); D. the lab
clock: skip unchanged bookkeeping, run it beside replays (about 1); E. the loop's engine move (0.5), then feed the loop
only if A confirms transfer, else stop it; F. a ledger line per worker (start and end usage) at no cost. Rule from
finding 2: no trainer is built or kept without its consumer wired first. Nothing starts before the reset (usage near
68%, ceiling 70) except E on the owner's word. Not changed: the exam size, the lab gate's statistics, the night driver.
Recorded 2026-11-01 21:36Z.

## D45 · 2026-11-02 · The reset order starts now; the week's ceiling is 85

Owner in chat (01:3xZ): "What changes at the reset, in this order - do this now usage up to 85". The D44 order (A wire the
loop's fight player v2 into the exam agent as generation 11; B the boss-entry instrument and the human per-decision exam;
C the next run-level recipe from B; D the lab clock; E the loop's engine move, then feed or stop the loop; F a usage line
per worker) runs now instead of from 2026-11-03 21:00Z, under a ceiling of 85 in 100 (new worker starts stop at 83;
usage 69 all / 54 Fable at 01:38Z). The owner's open question of 11-01 (the engine move after a night or at the reset) is
answered by this: E runs in its place in the order.

**Decisions (orchestrator, routine):** workers are Agent subagents (sim-worker; no new session can start while the owner
is on Remote Control): A on Opus and B on Sonnet start together (they share no files: A works in the fork's `rl/` and the
lab's train and promotion path, B reads the lab and writes to the Spireline repo; B is light on the machine); C starts
when B reports; D starts when A has landed (both touch the fork); E runs after D at a verdict line of the loop; F from the
first worker: every worker's HANDOFF line carries the usage at its start and end. The night is untouched: nothing lands
after about 19:00Z on 11-02 without checking `LAB/nightly/active`, no `jobs.json` edit during a night, A's block runs
only if it can finish before 18:30Z. Estimates as D44: A 2, B 1.5, C 3, D 1, E 0.5, about 10 points with orchestration,
to about 79 in 100. The paper gets one line now and one per landing. Recorded 2026-11-02 01:43Z.

## D38 · Addendum 1 · 2026-11-02 · The exam fifth is fixed

Worker B (reset order step B) found that the held-out fifth D38 names had never been cut, and cut it: of the 14,745 vanilla runs
in the corpus export (`runs-v0.107.1`), the runs whose id falls in the fifth under a fixed hash of the run id (the rule is in
`tools/boss_entry.py`) are the exam, 2,924 runs. The id list sits beside the corpus (`data/spire-codex/human-exam-fifth-ids.txt`)
and in `referee/backlog/boss-entry/human-exam-fifth-ids.txt`. The exam is read only to score the AI (first use: the per-decision
exam of `docs/diagnostics/2026-11-02-boss-entry.md`); no training input may carry these runs. Orchestrator, routine; recorded 2026-11-02 02:37Z.

## D46 · 2026-11-02 · Claude compute: the balance between credit and quality

Owner in chat (11:2xZ): "what skills can you use to reduce the amount of compute Claude uses"; then (12:0xZ): "Do whatever you
think balances compute without compromising quality in the long run." The week's credit went to three things: the workers'
own reading and writing, the orchestrator's turns on the most expensive model, and wakes (every notification re-reads a long
conversation). Decisions (orchestrator, under that word):

1. **Model by task.** Sonnet for measurement, building to a clear brief, and verification; Opus only where judgement decides
   (mechanism diagnosis, a recipe or design decision, engine work); Haiku for mechanical verification (checking a landing,
   running a suite and reporting counts, copying numbers into a page). The orchestrator stays on the top model but takes
   fewer turns (2). The quality rule: the model that decides is never cheaper than the decision; the model that measures or
   checks can be.
2. **Fewer wakes.** Workers report once, in at most ten lines, after their HANDOFF line (as now). Landings are recorded in
   batches: a paper line per landing is still written, but at the next wake, and the page is published at most twice a day
   (the edition and one batch) unless a landing changes the headline. The paper stays at one edition a day (D39).
3. **Effort by task.** Measurement and verification workers run at low reasoning effort; builders at the default; Opus
   workers at their default. This is the one lever the harness only allows on the owner's explicit word, which this is.
4. **Scripts for the routine.** The night's morning report (today a Sonnet lane that wakes each night) becomes a script
   that writes the numbers and the HANDOFF line, checked by a Haiku worker; built at the reset (2026-11-03 21:00Z), not
   before tomorrow's night, so no report is at risk. Likewise the paper's edition figures come from a script where they can.
5. **A ledger, and a fresh start.** Every worker line carries usage at start and end (D45 F). The usage breakdown of this
   conversation is read once at the reset, and the orchestrator starts a fresh conversation from HANDOFF at the reset, since
   a long context costs more per turn.
6. **Not changed.** No worker is cut below what its task needs; a diagnosis that would be guessed on a cheaper model is not
   run on it; the exam, the gate statistics and the night driver are untouched by this decision.

Also decided under the same word, as a routine and reversible operation: the move of the lab's run files to the solid-state
drive goes ahead in the first quiet window after the 2026-11-03 night, in the order the disk-bound report gives, by a
directory link at the old path, the old copy kept one day. Recorded 2026-11-02 11:56Z.

## D47 · 2026-11-02 · Generation 12 refused; no second attempt before a ranking check

Step C's recipe (the run head V_run refit only on runs played by generation 11's own fighter, pure Monte Carlo floor target,
exploring self-play) was refused on attempt 1 of 2: -5.91 floors against generation 11 on 2,000 paired seeds (E12-2026-11-02;
17.08 against 22.98; Act 1 boss kills 541 against 1,033), both guards fired. It rested 2.1 times against 3.1 and healed 0.73
against 1.34 before the Act 1 boss, so 41% of its runs died before that boss against 9%: the fit undervalues HP. The keep test
checks outcome forecasts, not how options are ranked, so it could not catch this. Likely causes, untested: a third of the
planned data (3,781 exploring runs instead of 8,000; the clock went to score-real and two presorts) and beta 0.

**Decisions (orchestrator, routine):** no second attempt this week (usage 83, the line for new starts). Before any further
V_run block: a ranking check on held-out decisions (does the candidate rank rest, heal, path and card options as the
incumbent or humans do) as part of the keep test; then the second attempt with the full 8,000 runs and beta tuned, at the
reset. Process finding: score-real ran without `--resume`, so every load stop restarted the real arm from zero (C's gate runs
tripped the load guard 4 or 5 times); `--resume` added to the job where the driver has it. Recorded 2026-11-02 16:04Z.

## D48 · 2026-11-02 · The machine: practice as the filler, cores not turns, the card fed by the work

Owner in chat (16:4xZ): after "how do we maximize the cpu and gpu in this process", "Okay do what you think in terms of cpu and
gpu". The measured state (D44 finding 4, the 2026-11-02 sweep and disk report): the processor busy about 56 in 100 over the
watched day, 44% of core-hours idle; the card 21 in 100 busy and limiting nothing (inference batches of 1.3 ms; training
minutes a day); the lab runner runs one job at a time, pauses when other processes pass 50% of the CPU for 120 s, and practice
is switched on and off by hand (D43 paused it).

**Decisions (orchestrator):**
1. **Practice is the filler.** Whole-run self-play on the copy and the always-on loop's fight practice run whenever nothing
   higher needs the machine, at BelowNormal priority, recording shards with no train marker (the recipe and its ranking check
   decide when a fit is made, D47), so data is ready when a recipe is. They stop for the night exactly as the loop does today
   (no start while `LAB/nightly/active` exists or within 30 minutes of the night's due time; stopped when it starts).
2. **Cores, not turns.** The runner gives out cores: a promotion block or a scoring job takes its cores and runs beside the
   filler instead of after it; training on the card runs beside either; the pause rule counts only non-filler load, so a
   filler never stops a job and a job never waits for a filler. The night is unchanged and keeps the whole machine.
3. **The card is fed by the work, not scheduled.** More practice and the larger training set (32,000 fights, D44 step E) are
   what raise its use; no change to batching or models under this decision.
4. **Scope and cost.** Built in the fork's lab code (runner, plans, jobs) with tests, by one Opus worker (about 1.5 points),
   landed before 18:30Z on 11-02 or after the night; the runner restart that switches it on is the orchestrator's, after the
   night, together with D's and the accounting line's. The engine's fight-step speed (core2, 3x the old engine's cost) is a
   separate lane, next week. The budget: the owner asked what 90 in 100 would buy and then gave this word; the orchestrator
   reads that as headroom to 90 for this work and the night's follow-up, stopping new starts at 89. Recorded 2026-11-02 22:22Z.

## D49 · 2026-11-03 · Ceiling 95, then stop: four items before the reset

Owner in chat (02:2xZ): "okay use up to 95 then stop". Usage 86 all / 61 Fable at 02:22Z; the reset is 2026-11-03 21:00Z.
**Decisions (orchestrator):** four workers start at once on disjoint files, new starts stop at 94, nothing after them:
(1) the Pillage hang in the copy (Opus, about 2.5 points: the draw-until mechanism made to stop when no eligible card
remains, as the game does, every other draw-until use checked, the three seeds as tests, build, Python gate, byte-proof,
the engine-edit regeneration before the gate; landed before 19:00Z so tonight's library carries it, else after the night);
(2) the ranking check that joins the keep test before any V_run block (Sonnet, about 1; D47): generation 12's refused fit
must fail it and generation 11's head pass; (3) the always-on trainer's gate pre-filter by held-out loss with a floor of one
gate per six hours (Sonnet, about 0.5; sweep finding 5); (4) the night's morning report as a script, tested on the last two
nights against the lane's reports, not replacing the lane tonight (Sonnet, under 1; D46 item 4). Edition 37 after tonight's
block. Recorded 2026-11-03 04:57Z.

## D50 · 2026-11-03 · The rest of the week's allowance, with a margin

Owner in chat (08:5xZ): "Use as much compute as you can before the reset but not go over". Usage about 93 all / 63 Fable;
the reset is 21:00Z. **Decisions (orchestrator):** three items from PLAN.md section 14 start together on disjoint files,
each with a hard budget, new starts stop here, and the orchestrator keeps about two points of margin so the allowance is
never exhausted before the reset (an exhausted allowance would also stop the night lane): (1) the always-on trainer's
library move to fork main c4401980, the Hellraiser fix (Sonnet, 0.5; at a verdict line, publish, relaunch, the
incumbent's games replayed on the new tag); (2) the test funnel (Sonnet, 1.5): a 200-seed smoke block and the paired block
run sequentially with an early stop either way, the full 2,000-seed fresh-seed block kept as the final gate, in the train
job's promotion path, tests only, no block run today; (3) the sub-problem board (Sonnet, 0.8): the six pieces with their
current and human numbers, fast tests and owners, as `docs/SUBPROBLEMS.md` with the script that refreshes its numbers.
Not started: generation 12's second attempt (D47: the full 8,000 exploring runs first, next week), the churn trace and the
`C:` disk watch (housekeeping, next week). Recorded 2026-11-03 20:45Z.

**Addendum 2026-11-03 20:46Z:** the three workers were stopped one minute after starting: the orchestrator had misread the clock (they started at 20:45Z, fifteen minutes before the reset, not twelve hours), so their spending would have fallen into next week before the owner set its ceiling. Nothing was landed or left half-done. They restart at the reset under next week's ceiling on the owner's word. Usage at the stop 93 all / 64 Fable.

## D51 · 2026-11-03 · Next week: ceiling 65; the three D50 items restart at the reset

Owner in chat (20:5xZ): "Next week cap is at 65 and yes". The week of 2026-11-03 21:00Z runs under a ceiling of 65 in 100
(new worker starts stop at 63), with D46 in force (model and effort by task, reports once, landings batched, the page at most
twice a day). First starts at the reset, on the owner's yes: the always-on trainer's library move to c4401980 (after tonight's
block ends, at a verdict line), the test funnel in the promotion path (tests only), and the sub-problem board. Then edition 37
from tonight's block, and the rest of PLAN.md section 14 in its order. Recorded 2026-11-03 20:54Z.

## D52 · 2026-11-04 · Two token items: a cheap landing checker and a usage ledger

Owner in chat, asked which items meaningfully improve token usage and told "Yes do these" for the two not yet done.
**Decisions (orchestrator):** (1) routine verification moves off the orchestrator: a `landing-checker` agent
(Haiku, low effort, read-only) that takes a worker's report and the evidence a script gathers (commits on main,
gate counts, loop status, runner lines, HANDOFF placeholders, the paper's changelog) and marks each claim confirmed,
not found or contradicted; the morning report gets a `--check` that recomputes its headline figures by a second
path; (2) a usage ledger, `tools/usage_ledger.py`, that reads the start/end usage notes on HANDOFF lines and
prints the cost of each item and each week, flagging overlapping items instead of pretending precision.
One Sonnet worker, budget about 0.5, Spireline repo only; the orchestrator keeps deciding and recording.
Recorded 2026-11-04 01:35Z.

## D53 · 2026-11-04 · The training-and-testing memo's items start

Owner in chat ("okay do all the changes you think"; and, on the compute part, "do this"), after the memo
`docs/research/2026-11-04-train-and-test-ideas.md`. **Decisions (orchestrator):** four Sonnet workers start together on disjoint
files: (1) the fight exam (`rl/fight_exam.py`: stratified starts from the nights' replays, four paired draws, judge-value
adjustment, held-out halves, the champion's calibration run under a `fight-exam` lock line) as a parallel instrument; the promotion
rule (`PROMOTION_RULE`, D43) is not switched to it until it has read several gates; (2) practice starts from the human corpus's
four fifths (`rl/human_starts.py`, Act 2 and bosses first, the exam fifth excluded by id) and a regret-weighted sampler with a
staleness term and pre-loss states in `gym_loop.py`; the loop is relaunched onto it after tonight's block, not during the day;
(3) the nightly exam's power in `tools/morning_report.py` (copy-arm control variate, progress score with SEs, fight-quality
measures where the rows carry them); (4) the compute-allocation measurement (`docs/diagnostics/2026-11-04-compute-allocation.md`),
which the owner asked for before the teacher-depth design. Queued behind them: the Opus design of the deeper training-time
teacher and of hindsight labels for human run decisions (memo 3.3 and 6.2), then the trainer's auxiliary targets and resets
(memo 3.4) once (1) and (2) have landed. Every heavy run ends by 15:45Z and every landing by 16:00Z for the night. Recorded 2026-11-04 10:16Z.

- Addendum 2026-11-04 10:38Z (owner: "one hour per 500 runs here - this seems slow"; "if there is a path to a kill do we stop searching"; "okay do what you think"): the block's hour is the AI's search (87,700 decisions at 31 a second against the game's measured 108) plus the copy arm run afterwards (22 minutes); no kill check exists in the search (grep of `combat_mcts.py`, `search_configs.py`, `solver/`: none; the root lethal check of the 2026-10-29 shape review was never built). A fifth Sonnet worker (speed lane) lands `--emu-runs` in `rl/nightly_real.py` with the night job at 200 copy-arm seeds (backup + dated note in `jobs.json`, by 15:30Z or the night stays unchanged), and a root kill check as a config option `a3-v1-k` measured paired against `a3-v1` on the board (400 games each); the night's config stays `a3-v1` until the numbers are read. The confidence fast path for easy decisions, the teacher's leaves on the judge, the trainer's passes per row (the trainer trains 8 in 100 of its time, waiting for fresh fights), the lab's daytime cores and the rented-cores pricing go to the Opus design round's scope.

- Addendum 2026-11-04 11:11Z (orchestrator, security control H2): the decisions audit (Spireline main c1ae7d3) found that the game copies moved to the SSD at 03:41Z (`C:/spireline-ssd/game-env`, `game-lab`, reached through junctions) had no outbound firewall block rules: H2's 84 rules are by program path and name the `D:/spireline/referee/...` folders; verified by `netsh advfirewall firewall show rule` (0 rules name the SSD) while 12 game processes of the lab's bench-env job ran from `C:/spireline-ssd/game-env/SlayTheSpire2.exe`. Action: `LAB/PAUSE` written, the game processes ended within 85 s, the two junctions removed and the hard-linked old folders renamed back to `game-env` and `game-lab` (covered by the existing rules), PAUSE removed; the SSD copies stay in place unused. Tonight's block runs from the HDD again with the boot-retry fix; the start-up stall may recur. The junctions go back to the SSD only after the owner adds block rules for both SSD copies (SlayTheSpire2.exe and crashpad_handler.exe under `C:/spireline-ssd/game-env` and `game-lab`). Rule for every future copy: no game copy runs from a path without its block rules; the move checklist gains that line.

## D54 · 2026-11-04 · The cheap fixes and the refused-move crash

Owner, in chat (2026-11-04 19:54Z): "Do all of them including the game refusing a move - it seems important", on the orchestrator's list of fixes whose cause this session had already found. Started as subagent workers (the owner is on Remote Control, so no fresh sessions): (1) Sonnet, Spireline: the morning report's check mode writes its `--out` files, the D11C line prints "absent" for a missing rank, the confidence-sequence coverage test stops depending on the wall clock; (2) Sonnet, fork: the hidden-information test failing at `rl/engine.py:760` since 11-03, the parallel-searcher niceness test that fails only in the full suite (bisected per module before being called load), the pre-loss order's tie across two writers in one nanosecond; (3) Opus, diagnosis: the real arm's `RuntimeError: the engine refused action N in phase 5` crash rows (12 since 10-30), mechanism, classification of the 12, minimal reproduction on the copy, a Python fix landed or a contained C# fix with the full gate, else the options; (4) Sonnet, audit: the turn-one effects (Clarity, Demesne, Tools of the Trade and the rest) after engine 8db0b791, with a contained fix and the full gate only if the mechanism is the same class; (5) Sonnet, lab tooling, held until the idle-time filler worker lands (same files): the yield ledger's false zero for new groups (`by_job` empty), the gate script that waits forever on the practice loop's permanent QUIET line. Not started: anything needing a diagnosis beyond these (the dozen unexplained Act 2 records, the run that ended mid-fight on 11-05, the 82 runs that lost the lockstep on a state difference). Cost about 3.5 units; usage 21% all / 9% Fable at the start.

- Addendum 2026-11-04 20:47Z (owner in chat: "Fix it now", after the orchestrator's read of the enemy-health pile): the enemy-health diagnosis starts now with the stronger model, not after the day's other workers; the sweep is not pointed at its enemies separately, since the aimed sweep is now once a day and the worker has the shrunk setups. Also started: the lab's job cadence fix (mutation, invariants, probes and retest once per presorted tree), because the aimed-bugs cap left the rotation churning small jobs and the practice filler never idle.

## D55 · 2026-11-05 · The strategy is rethought: the player learns from human runs and from whole runs

Owner, in chat on 2026-11-05 (shortly before 08:23Z), after the orchestrator's read of the promotion ledger (`referee/agent/promotions.tsv`:
the player ends at floor 23.1 on average, 0 wins in the ~36,000 judged runs since 2026-10-23, about one floor per promotion over
the last three, two rejected generation-12 candidates since): "I think we need a breakthrough in our process I am not convinced we
get there with this process"; on the two rules the orchestrator named (the run judgement trained on Act 1 only; the human corpus
never trained on), "Okay change both of these and rethink the whole strategy".

1. D13 amended again (after D38): the four training fifths of the human corpus (Ironclad A10, 14,811 runs; the exam fifth excluded
   by id, `human-exam-fifth-ids.txt` beside the corpus) may be used as training targets, not only as practice starts: the run value
   and the macro priors (card reward, shop, rest, route, event) may be fit on them. The held-out fifth stays the exam only (D38):
   nothing is tuned on it, and the paper's human lines stay computed on it.
2. The F3 gate on RL-2 beyond Act 1 (DESIGN §4 fidelity table, §5.1) is lifted: the run head trains on whole runs on the copy as it
   stands (the 53-class full-run head, or whatever the rethink chooses), with the nightly real-game check reporting Act 2 and 3
   accuracy beside it; divergences there stay fixes, not blockers.
3. The whole strategy is re-examined by the strongest model in a design memo (`docs/design/2026-11-05-strategy-rethink.md`) before
   any recipe change lands: what to keep, stop and start; the human-imitation recipe; the full-run head; compute; a two-week plan
   with its own go or no-go test. Nothing running changes until the memo's decisions are recorded (the label run, the lab and the
   loop continue).

Recorded 2026-11-05 08:23Z by the orchestrator.

- Addendum 2026-11-05 08:50Z (orchestrator, after the memo `docs/design/2026-11-05-strategy-rethink.md`, Spireline c495e30; checker: all
  confirmed, the per-act accuracy figures and the 53-class head for generations 9 and 11 hand-checked): the memo's two-week plan
  (section 5) is the plan of record to 2026-11-19 in place of PLAN.md's D17-D21 for that fortnight; the headline measure becomes
  Act 2 boss kills per 100 runs (5.0 in the game, humans 28.9), mean floor stays the promotion measure; the generation-12 line
  (self-play refit, beta, blended fit) is closed; the hindsight label run continues to its 1,200 read and on, used as the arbiter
  between the human prior and the judgement (memo 3.5), not as a blended-refit target; milestone 1 (play or deck: generation 11's
  fighter on 300 + 300 human boss starts from fifth 4 at a3-v1, x4, x16; the potion hold smoke if time allows) started now as a
  Sonnet worker under a `play-or-deck` QUIET line, ending by 15:45Z. Correction to the owner's briefing: the run judgement has
  had 53 whole-run classes since generation 5 (gen 9 and 11 `run_value.npz`: floor_head 53 x 256); only its keep test and its data
  were Act 1, so item 2 of D55 changes the keep test and the data, as the memo's 3.4 specifies. The owner's two questions (renting
  cores in week 2 under about $50; the no-go fallback's start) are open.

- Addendum 2026-11-05 09:51Z (owner in chat: "yes we can budget spending this - but can we lower the cost anyway", on the memo's question 1):
  rented cores are approved for week 2 (2026-11-12 to 11-19) under the memo's terms: the copy only (our binary, the player's
  weights, seeds; the game's files, the decompile and the nightly check never leave the PC), a ceiling of about $50 for the
  fortnight, spent only when a decided block has waited more than a day; the owner creates the machines from their own account
  and lends the PC a key for the fortnight only (no provider credential is held by Claude). Cost-lowering measures (orchestrator):
  the funnel's early stops (D51) and the 200-seed smoke stay the first filter so only the top one or two candidates reach a rented
  2,000-seed block; machines are shut the hour a block ends; a rented block resumes from its finished seeds if interrupted, so
  spot-priced machines are acceptable where the owner's provider offers them (prices unverified until the implementing worker
  reads them); the first lever is the PC's own idle time (the compute diagnostic found the CPU half used over 11-01 to 11-03).
  The memo's question 2 (the fight-first fallback on a no-go) is still open; until the owner says otherwise it starts at once.

- Addendum 2026-11-05 09:52Z (owner in chat: "ok switch on your own"; "why you can start teaching using human play tonight"): on a no-go on
  2026-11-19 the orchestrator switches to the fight-first fallback (memo 5.2) without a review. Milestones 2 and 3 (the human
  decision set and the prior `pi_h`) start now rather than on 11-06/11-07: they are on the critical path whichever way
  milestone 1 falls (memo 5.1: on "play dominates", milestone 7 follows milestone 2), they touch no file the play-or-deck
  worker uses, and the build is light on cores (at most 4 processes, BelowNormal, stopping heavy CPU use when the night's line
  appears; the fit itself is minutes on the card). One Sonnet worker on a fork worktree (`feat/human-prior`); landing on fork main
  after the night if the night is active when it is ready.

- Addendum 2026-11-05 11:58Z (owner in chat: "Yes, build it"): the event option-name table (event id to option titles and indices) may be built
  with the fork's decompile reader (`scripts/generate_event_options.py`'s approach); the table is game data strings, not
  decompiled code, and is cross-checked against the live captures in `tests/fixtures/events`. With it, the human record's
  event choices (option title only) become decision rows for the prior, and whole-run seed replays stay in step past events.

- Addendum 2026-11-05 15:01Z (orchestrator, milestone 1 result, `docs/diagnostics/2026-11-05-play-or-deck.md`, Spireline 1288c78): on the
  humans' own boss starts (fifth 4, 300 + 300, two draws) generation 11's fighter wins the Act 1 boss 52.5 in 100 (humans 73.7 on
  the same starts; on its own starts 57.2) and the Act 2 boss 44.4 (humans 74.3; own starts 14.7): the Act 1 gap is play, the Act 2
  gap half play and half the hand (potions 1.68 vs 0.48 at the door, relics, HP). Thinking time pays: x4 +4.2 / +6.2 points, x16
  +10.6 / +10.7 at the two bosses (paired, intervals above zero). Decisions (routine, memo 3.5 step 4 and 5.1): the milestone
  order is both halves, the fight half's milestone 7 right after milestone 2; three candidates are built tonight for the lab:
  the stakes schedule (elite x4, boss x16, as a candidate property honored by the funnel, the night and self-play), the potion
  hold rule on top, and the win-conditioned prior v1 sampled at lambda 0.5 on top of those (the bare argmax over-takes cards:
  the imitation sanity run skipped 5.4 in 100 against humans' 15.4 and lost 4.3 floors; lambda 0.5 was level). Landings and
  markers after the night, after a Python re-gate of 58aaa6fe on a quiet machine. Block cost rises (x16 boss fights); renting
  (approved for week 2) is the relief if the queue forms.

**D55 addendum (2026-11-05 19:16Z, orchestrator, under the memo's milestone "a new keep test replacing D33").** The keep test v2 (`docs/design/2026-11-05-keep-test-v2.md`, Opus design) replaces D33's rule for every judgement from the day its code lands. A candidate is promoted by route A (on paired seeds it beats more bosses from the frontier on, today the Act 2 boss, the Act 3 bosses and wins, counted per 100 runs: one-sided p < 0.005, gain at least +1.0 per 100, and the mean floor's 95% lower bound no worse than -1.0) or by route F (D33's floor rule at 0.005 with the frontier measure not worse). The frontier is the deepest boss the incumbent beats in 1.5 of 100 runs over its last three blocks, so the ladder moves up by itself. The Act 1 kill and damage guards become report-only; the crash guard, drift, the attempt cap and the wins clause stay. A route A promotion stands only if the next night's real-game Act 2 boss rate beats generation 11's pooled 3.40 per 100; otherwise it is reverted. Nothing of the exam fifth is used. Sensitivity: `candidate-imit-l05` passes at the 1.0-floor margin (its lower bound is -0.63) and fails at 0.5; the margin is 1.0 because the memo's headline measure is the Act 2 boss and the real-game check guards the floor. Retroactively only that one verdict changes of 19 judged blocks. Blocks grow to 3,000 seeds once the incumbent passes 5 per 100. Corrected baseline: generation 11's pooled Act 2 boss rate is 2.36 per 100 on copy blocks and 3.40 in the real game, not the memo's single-night 5.0 / 6.5; the go/no-go bar of 2026-11-19 stays at 8 per 100 on the copy's paired blocks (the memo's absolute bar), now a 3.4x gain over the true baseline. Build: Sonnet worker on `feat/keep-test-v2` (Python-only gate), then the first use is a re-judgement of `candidate-imit-l05` from its saved rows; if promoted it becomes generation 12 and the next night's player.

**D55 addendum 2 (2026-11-05 21:29Z, orchestrator; the keep test v2 in force and its first use).** The keep test v2 landed on the fork's main (48bf4295, 21:27Z) and replaces D33's rule for every judgement from now; the lab's train job takes `--keep-rule v2` at its next tree refresh. First use: `candidate-imit-l05` re-judged from its saved 2,000-seed arms and promoted by route A (Act 2 boss 107 against 49, +3.05 per 100, 0.005 lower bound +1.50; mean floor -0.31 with a 95% lower bound of -0.63; no crashes; drift clear). Generation 12 is the half-weight human-prior player; it is the incumbent for the real night of 2026-11-06 and the lab's daytime score. Under the D55 addendum the promotion stands only if the night's real-game Act 2 boss kills per 100 runs beat generation 11's pooled 3.40 per 100 with the one-sided 95% lower bound of the difference above zero, and its mean floor is not more than 1.0 below the pool's 23.33 at 95% (the design's section 5 as `tools/morning_report.py` computes it; on 2,000 real runs that needs about 4.4 per 100 or more); the revert is `current.json` back to generation 11 with the ledger row marked reverted. Three wording questions the build raised are settled as the rule: (1) the frontier is read from the promoted lineage's last three judged blocks (what the retro and the lineage pooling do), not strictly the incumbent's own blocks; (2) D24's Act 1 boss co-primary, which would have blocked this player, goes with the kill guard under v2 and is reported only, so D24 is superseded by this test for the fight-lineage keep test; (3) the morning report's confirmation reads the ended-run floor. The build's commits carry a Sonnet trailer (worker slip, disclosed).

**D55 addendum 3 (2026-11-05 22:06Z, owner: "Yes build").** The three stakes candidates of milestone 7 are built and queued for the lab's judgement (`docs/rl/STAKES_AND_HOLD.md` section 1), on generation 12's deck prior rather than the plain macro, since generation 12 is now the player they must beat: thinking time x4 at elites and x16 at bosses (`gen13/candidate-stakes`), the same plus the hallway potion hold at 30 in 100 of max HP (`candidate-stakes-hold`), and both with the win-conditioned human prior sampled (`candidate-winprior-sample`). Each block costs about 80 core-hours for the candidate's arm (the lab's train timeout is raised to 9 hours for them); the first two run tonight before the real night, the third after it. The skip-calibrated fourth waits on the three stacking cleanly.

**D46 addendum (2026-11-06 01:57Z, owner: "raise the line to 75").** The Claude weekly allowance ceiling is 75% (stop line 73%), up from 65% / 63%, for the week ending 2026-11-10 21:00Z and onward until changed. Context: 41% used at 2026-11-06 00:21Z after two days of the week (19% a day), with the three deeper-search candidates' judgements, tonight's two-player real night, the stakes-hold and win-prior blocks and the expert-iteration preparation (hindsight labels, blend weight) ahead. The rest of D46 stands: Sonnet measures and builds, Opus decides, Haiku checks at low effort, landings batched, the page published at most twice a day.

**D55 addendum 4 (2026-11-06 03:46Z, owner: "okay do all 4", after "whatever the bottleneck is runs first" and "we should be aiming for big steps").** (1) The improvement loop of the memo's 3.5 (play exploring whole runs on the copy, hindsight labels, refit the judgement and the prior, judge) starts now instead of 11-12; the lab's filler plays the current player exploring and the label run resumes at its share. (2) The small-tweak candidates are dropped: `ready-11-g13-stakes-hold` moved to `LAB/train/dropped/`, `ready-11-g13-winprior-sample` never written, the skip-calibrated fourth not built; their builds stay on disk. (3) The real game runs weekly in one batch (nightly-real every_h 168: the newest player 2,000 runs, the 200 copy replays), plus a block the orchestrator triggers by hand (`LAB/nightly/pending`) when a promotion claims a gain of 3 per 100 or more on the frontier boss; a triggered block runs at the top of the ladder as soon as the running job ends and plays each generation promoted since the last block; the route A confirmation of addendum 2 is read from the next real block whenever it runs. Tonight's block (generations 12 and 13) is triggered by hand as soon as the change is in. (4) One rented 16-core Linux machine (owner provides: Ubuntu 22.04 or 24.04, 16 vCPU, 32 GB RAM, 60 GB disk, SSH key access, no game files) for the copy's build and one-block identity check; scaling to two to four machines is decided after round 1 by the memo's rule (decided blocks waiting more than a day). The owner asked for the compute need with these changes; the orchestrator's estimate and the big-step design (an Opus design, docs/design/2026-11-06-big-step.md) answer it.

**D55 addendum 5 (2026-11-06 04:35Z, owner: "yes 1").** The 2026-11-19 go/no-go bar is the Act 2 boss beaten in 15 of 100 runs on the copy's paired blocks, with the paired bound above generation 13 and the real game agreeing (the big-step memo's section 6 step 16), replacing the memo's 8, which generation 13 meets on its point estimate (9.2). The rented machine (addendum 4 item 4) is not yet decided; the orchestrator's estimate of its Claude cost: about 3 to 5 points of the weekly allowance for the build and the five checks if the Linux build goes cleanly, up to 8 if it needs fixes, against 25 points left to the 75% line this week; recommended after the 11-10 reset unless A's board fails.

**D55 addendum 6 (2026-11-06 04:39Z, owner: "we should be using the mac hours overnight anyway").** The owner's MacBook Pro (M1 Pro, 8 performance cores, 16 GB, macOS 15.7, Claude Code installed) runs the copy's work in its idle hours: a night window in the owner's local time, stopped on any user activity, resumable jobs only (exploring practice games and hindsight labels first; a test block over two nights only with resume), under a separate macOS user account, the lid open on power. Setup is a Claude Code session on the Mac itself: the build probe first (the macOS/ARM64 build is untested; stop at about one allowance point if it fails), then the big-step memo's five identity checks, then the night scheduler. Timing: right after the 2026-11-10 21:00Z reset so this week's two builders keep their allowance; the real game is not ported (addendum 4's note stands). A rental stays the fallback for full-time capacity.

**D55 addendum 7 (2026-11-06 05:27Z, owner: "okay do this").** (1) A builder may download the current Spire Codex public run export for v0.107.1 (spire-codex.com exports page, about 3 GB, the published manifest sha256 checked) into D:/spireline/data/spire-codex/ beside the October copy, which is kept. (2) This week's deck refit (the big-step memo's row C, round 1) trains the human prior on strong players' choices: players with at least 20 kept runs at Ascension 10, ranked by a shrunk win rate, the top group chosen so that no published cell is under 20 runs; the pseudonymous player ids never appear in any document, result or commit; D13/D38/D55 stand (aggregates only with attribution, the exam fifth never trained on, raw runs never leave the folder; new runs join the fifths by the same rule as the October ones). The candidate carries generation 13's recipe with the new prior and enters the first big-step stack if its fit passes the ranking check and the held-out label leg.

**D55 addendum 7, note (2026-11-06 05:54Z, orchestrator).** The strong set cannot be formed: `player_token` is null in all 840,381 runs of the new export (and in the October one); the per-player id is 1 everywhere. The download, the rebuilt subset (74,287 A10 standard single; 72,863 vanilla; Ironclad 18,125 with 1,953 wins; exam fifth 3,588 by the existing hash rule, the October exam ids kept) and the strong-set tool landed (Spireline 0c12198, 252 tests). Item (2) of the addendum stands only if a source with player ids appears; the week's deck refit (row C) uses the larger file with all players (14,537 non-exam Ironclad runs) in round 1's refit. A run-level stand-in (winning runs only) is not used: it selects on luck as well as skill, and the win-conditioned prior v1-win already lost on the label leg. New label-leg reading (674 graded card and rest decisions): the lambda 0.5 blend with pi_h-v0 is level with the judgement alone (-0.00 ± 0.06 floors) and the prior alone is worse (-0.15 ± 0.09), while the same prior gave +3.05 per 100 at the Act 2 boss on 2,000 paired seeds: the labels and the blocks disagree about the prior, which must be understood before the labels arbitrate lambda or round 1's refit (the memo's 3.4; an Opus question, queued).

**D55 addendum 7, correction (2026-11-06 06:04Z, orchestrator, from the Haiku check).** The runs do carry a per-player key: `players[0].id` has 16,221 distinct values in the new file (the worker had read it as 1 everywhere; 1 is a placeholder, the rest are 17-digit platform account ids). Item (2) proceeds on that key, treated as sensitive: used only to group runs inside the data folder, never written anywhere else; cells under 20 runs never published. Also: the October file's sha256 is 92b3cc40…, not D13's 55557226… (D13 recorded the manifest as checked on 2026-10-10; the file was downloaded 2026-10-13); the sidecar written at download is being read and SPIRE_CODEX.md will say which snapshot each hash belongs to.

**D55 addendum 7, outcome (2026-11-06 06:29Z, orchestrator).** The per-player key is set only on multiplayer runs; every single-player run, which is the whole corpus the pipelines read (74,287 kept), carries the placeholder. So no strong-player prior for single play from this export; item (2) is closed on this source. A counts-only probe of the co-op seats (A10 standard, 2+ players, exam fifth out, team outcomes): 31,133 Ironclad seats from 3,752 accounts; 332 accounts with 20+ seats; the top quarter (83 accounts, 2,940 seats) wins 55.3 in 100 against the pool's 21.5, Act 1 / Act 2 boss 90.7 / 77.0 against 69.8 / 34.7 for the other eligible accounts. A prior fitted on those seats' choices is a different population (co-op maps, two decks) and an unchecked replay; queued as a cheap candidate experiment after the 11-10 reset (pipeline seat selection, a map-identity check, 1-2 h of the copy, judged by the keep test), not part of the first stack. SPIRE_CODEX.md now records D13's hash as the 2026-10-10 snapshot (no longer on disk) and the file on disk as the 2026-10-13 fetch (sha256 92b3cc40…, equal to its sidecar). Spireline 149c885.

**D55 addendum 8 (2026-11-06 21:58Z, orchestrator; the first hand-triggered real block, generations 12 and 13, and the reading of addendum 2's confirmation).** Block `20261106T0852-nightly-real` (08:52Z-21:26Z, folder `LAB/nightly/2026-11-06T0852`, tree 20454762, no interruption). Generation 13 on 1,995 ended real runs: Act 2 boss beaten 7.77 per 100 (155; generation 11's real pool 3.42 = 119 of 3,479; +4.35 points, SE 0.67), mean floor 24.15 (+0.68 on the pool's 23.47, SE 0.24), Act 1 boss 56.6%, 0 wins, 5 crash rows, 2 fight_unfinished. Generation 12 on 1,992: 5.52 per 100 (110; +2.10, one-sided 95% lower bound +1.12), mean floor 22.84 (-0.63 on 23.47; lower bound -1.017 as `tools/morning_report.py` computes it, -0.88 against the 23.33 that addendum 2 names, which was the copy-arm pool, a slip), Act 1 boss 47.9%, 8 crash rows. Reading: the Act 2 clause holds for both; generation 12's floor clause misses by 0.017 on the script's pool and passes on the recorded figure. Decision: generation 12 is not reverted and generation 13 stays the current player. The floor clause guards against an Act 2 gain bought with floors, and the player that would be kept, generation 13 (generation 12's prior plus stakes), shows the opposite in the same block on its own 2,000 runs: floors up 0.68, the Act 2 rate more than doubled. Rule from now: a confirmation is judged on the player that would be kept; when a later promotion built on the one under confirmation has its own real result in the same block, that result decides and the ancestor's hairline miss is recorded, not acted on; the floor clause reads against the real-arm pool as the script computes it. Copy against real: generation 13's 500-seed look said 9.2 per 100, the real game 7.77 (within the look's SE of 1.3); generation 12's 2,000-seed block said 5.35, the real game 5.52; the 200-seed paired replays put the copy 1.07 floors above the real game for generation 13 (sd 9.11; Act 1 boss agreement 73.9%) and 0.06 below for generation 12 (agreement 75.5%); the copy's Act 2 rate on those 200 seeds was 8.0% (13) and 9.5% (12). The next real block comes with the next promotion claiming 3 per 100 or more on the frontier boss, else from the 168-hour clock (08:52Z 2026-11-13).

**D55 addendum 9 (2026-11-07 12:04Z, owner: "do these" on the 2026-11-07 speed items).** The orchestrator's speed measurement of 2026-11-07 is the round's cost map: of a run's CPU the game copy takes 54%, the judgement network 15% and the search's own Python 30%; the Act 1 boss fight at x16 is 31.6 of a run's 55.4 CPU-s; a batched GPU scorer saves at most 15-18% and is not a priority. Decided: (1) now, a boss-search x8 arm of generation 13 (`gen14/candidate-stakes-b8`, recipe `vrun+pi_h:lambda=0.5:pi_h=2ebfe6d7+stakes:a3-v1@h1e4b8`: the same combat prior, V_run fit and deck prior, only the boss multiplier halved) is judged by the lab's train job against generation 13 on a fresh paired E-block. A refusal is expected (route A needs +1.0 per 100); the paired figures decide: the x8 schedule holds when the Act 2 boss rate difference's one-sided 95% lower bound is at or above -1.0 per 100 and the floor difference's at or above -1.0, and then the owner decides whether the current player moves to x8 (a round about 1.4x faster). (2) After the 2026-11-10 21:00Z reset: the judge retrain (design 1.3's fallback) and a Sonnet tidy of the search's Python. (3) An M6 Mac mini purchase waits for addendum 6's build probe and identity checks on the MacBook; 24 GB is the configuration if it passes.

**D55 addendum 9, outcome (2026-11-08 04:36Z, orchestrator).** The x8 arm (`gen14/candidate-stakes-b8` against generation 13 on E14-2026-11-07, 2,000 paired seeds, all seven looks, verdict rejected as expected) does not hold by the addendum's rule: Act 2 boss 8.5 against 9.3 per 100 (170 and 186 kills; paired -0.80 per 100, SE 0.52, one-sided 95% lower bound -1.65, below the -1.0 bar), floor 24.13 against 24.24 (lower bound -0.29, within the bar), Act 1 boss 54.0 against 55.2 in 100, wall per run 0.61 of x16. Player 13 stays at x16; whether x8 serves the practice and label stages joins the labels question after the reset.

**D55 addendum 10 (2026-11-08 08:19Z, owner: "okay do this" to the human fight bar).** The human corpus sets a per-fight bar for the fight player. Reading first: the humans' own boss fights (play-or-deck, 2026-11-05, fifth 4) have the humans at 73.7 / 74.3 in 100 (Act 1 / Act 2 boss) against the player at 52.5 / 44.4 at its normal search and 64.3 / 54.1 at x16, so the teacher itself is below the humans on their fights; single-player runs carry no player id, so 'expert' is the Ascension 10 pool and 'winnable' is a fight the human survived. Built now (Sonnet, lab code only, Python-only gate; started within this week's allowance at 60% because the unused part is lost at the reset): (1) each rebuilt human fight start carries the human's own result (survived, HP lost, turns, potions used) from the record's per-floor fields; (2) the fight exam gets a human stratum from clean training-fifth starts, additive to the existing exam (the champion's readings do not change), so every judgement prints the player against the human on the same fights, survival and HP lost, paired per start, by act and kind; (3) the practice sampler gets a human-shortfall regret mode (a human start's priority is how far the player's latest plays fell below the human's result there), switched on through `starts/mix.json` once landed; (4) the set 'the human survived, the player's latest plays all lost' is written as a diagnosis list for the solver and the judge retrain. Milestone line: parity with the humans on Act 1 boss starts, then Act 2. The exam fifth stays untouched (D38); aggregates only, cells under 20 hidden; no human card plays exist in the record, so the learning signal stays the copy's deeper search.

**D55 addendum 10, outcome (2026-11-08 10:14Z, orchestrator).** The human fight bar landed on fork main `20dc5b35` (six commits `041ac2b2..20dc5b35`, Sonnet worker; Python-only gate 4,692 tests, 17 failing = 16 baseline + 1 flake that passes alone, 0 new; the landing checker CONFIRMED the hash on origin, the lab-only diff, the counts, the sidecar's 46,410 entries, the 400-start stratum, the exclusion list and the diagnosis files; the orchestrator re-ran `fight_exam.py report --player v2` and read the same figures). **First reading, champion v2 on the human stratum** (400 clean training-fifth starts, one per run, 1,600 games, paired on the same starts; survival in 100, player / human): Act 1 hallway 100 / 100, elite 77.4 / 80.6, boss 50.1 / 71.4; Act 2 hallway 98.4 / 100, elite 71.0 / 77.4, boss 52.5 / 83.5; all 62.0 / 79.8 (-17.8 points, 95% -21.3 to -14.4); HP lost 38.6 against 33.2 (+5.4). Widest boss gaps: Kaiser Crab 44.2 / 80.0, Insatiable 52.4 / 87.1, Soul Fysh 53.3 / 83.3. Reading of the record: the human's end HP is the HP after the floor less the smaller of the healing logged and the relics' post-fight heal (Meat on the Bone's heal is a guess, 701 starts); a heal inside the fight and a potion drunk after it are not separable; HP in - damage + healed = HP after holds on 99.93% of starts. The exam's human stratum is hand-run only (no lab job calls the exam); it adds 1,600 games (about 32 min at 6 processes) to a full play and about 800 (16 min) to a compare. **Practice switched on:** the fight-gym daemon was stopped at 10:12:02Z between segments (phase generate, no gate running) and relaunched at 10:12:34Z (Windows PID 16200, trainer 13948, segment 183) from `wt-gym-loop-run` at `eebed28f` = `e1e94e19` plus the cherry-pick of `a6e044cc` (the practice-mix commit alone: fork main's `src/` has moved since `e1e94e19`, so the full code move needs an engine publish and an incumbent replay and waits for the next engine move); `starts/mix.json` sets regret mode `human-shortfall`, confirmed in the daemon's first line. **Diagnosis** (`referee/backlog/human-bar/diagnosis.md`, 801 human starts practised so far): 74 starts the human survived where the player's last four plays all died; 115 where the player lost 15 HP or more above the human; the by-enemy table is the solver and judge work's input. Milestone unchanged: parity with humans on Act 1 boss starts (50.1 against 71.4 today), then Act 2 (52.5 against 83.5). The exam fifth is untouched; aggregates only, no cell under 20 runs; attribution "Spire Codex public run export for v0.107.1".

**D46 addendum (2026-11-08 11:05Z, owner: "wire this in now - use up to 80" and "i mean use up to 80 for whatever is next in priority queue").** This week's ceiling moves from 75% (stop 73%) to 80% of the weekly allowance, spent on the priority queue in the memo's order (`docs/design/2026-11-06-big-step.md` section 6); usage 61% all / 44% Fable at 10:56Z, reset 2026-11-10 21:00Z. The ceiling returns to D46's 75 / 73 at the reset unless the owner says otherwise.

**D55 addendum 11 (2026-11-08 11:05Z, owner: "wire this in now").** The human fight bar becomes part of every automatic judgement, report-only (the promotion rule of the fight-gym gate and the keep test v2 are unchanged): (1) the fight-gym gate plays the human stratum (400 starts, four draws, the exam's own configuration) for every candidate that reaches stage 2, and its verdict line, `gates/verdicts.jsonl` and the loop's state carry the human line: candidate, incumbent and human survival and HP lost on the same starts, and the candidate-minus-incumbent difference on the stratum with a 95% interval; a promoted candidate's games become the incumbent's human reading; about 1,600 games (20 to 30 min of six processes) per stage-2 candidate; a daemon flag turns it off. (2) The lab's judgement (keep test v2) prints the fight network the judged player uses and that network's latest human reading with its date, or says it has none; no new games there, since the lab's candidates share one fight network. Activation needs the daemon on fork main: the orchestrator does the engine move (stop between segments, `wt-gym-loop-run` to the landed main, publish, relaunch) and checks the incumbent's replayed games at the next gate as D51 did. Started now under the 80 ceiling, four lanes: the wiring (Sonnet, `feat/human-bar-wire`, brief `referee/backlog/human-bar/BRIEF-wire.md`); the round's code, memo row 5 (Sonnet, `feat/round1-code`, `referee/backlog/round1/BRIEF.md`: labels at K 2, the prior refit with the KL anchor, the judgement refit with human rows, the lab job chain as an uninstalled fragment, every weight a config parameter); B resumed, memo row 6 (Sonnet, `feat/run-currency`, `referee/backlog/run-currency/BRIEF-resume.md`: rebase, the fast tests against the stop rule, the `-r` config for the real-game player, land only on a pass); the labels-against-blocks question with x8's place in practice and labelling (Opus analysis, `referee/backlog/labels-question/BRIEF.md`, memo `docs/design/2026-11-08-labels-vs-blocks.md`, a decision draft for the round's weights). Next in the queue as lanes free up: the judge retrain (design 1.3's fallback), the search's Python tidy (30% of a run), the co-op-seat prior experiment, a paper edition.

**D55 addendum 12 (2026-11-08 12:41Z, orchestrator; the labels-against-blocks question answered and round 1's weights decided).** The round's code landed on fork main `aa11b5fb` (Sonnet; `rl/round1.py`, `round1_data.py`, `round1_prior.py`, `round1_judgement.py`, `round1_config.json`, 23 tests, `docs/rl/ROUND.md`; gate 4,715 tests, 16 failing = baseline, 0 new; dry run of the chain play, label, refit-prior, refit-judgement, smoke, block on a scratch agent; the job chain as `referee/backlog/round1/jobs-fragment.json`, not installed; checker CONFIRMED hash, scope, counts and config). The Opus memo `docs/design/2026-11-08-labels-vs-blocks.md` (Spireline 93b757f) finds that the labels and the blocks never disagreed: 1,437 of the 1,449 labels graded Act 1 decisions (K 4), where the half-weight human prior costs a little (Act 1 boss -3.9 per 100, SE 1.2), while its whole gain at the frontier comes from its Act 2 choices (a 925-run probe on generation 11's Act 1 boss winners, Act 1 play matched on 924: the Act 2 choices alone give deep +3.38 per 100, SE 0.62, floors +0.28; the Act 1 choices cost Act 1 boss -3.94, SE 1.05, floors -0.63, SE 0.19, and add nothing at the frontier, deep -0.65, SE 0.76). The mechanism is which decisions get labelled, and the unit (floors a decision against boss kills a run); not horizon, compounding, noise or K. **Decided:** (1) labels do not choose lambda: `prior.lambda` 0.5, `lambda_rule` fixed; (2) round 1's refit weights `prior.weights` human 1.0 / agent 0 / label 0, `kl_beta` 1.0, `judgement.human_weights` picked on the held-out clears-Act-2 log-loss; (3) lambda per act becomes a recipe option and generation 13's recipe with lambda 0 in Act 1 and 0.5 from Act 2 is built as a candidate for the lab's judgement (3,000 seeds against generation 13, keep test v2; the memo expects the floor rule to pass, not the Act 2 rule); (4) at least half of the labels go to Act 2, two a run per act, ancients a new label kind; label continuations run at the x8 schedule (about 1.7 times the labels a core-hour; the round's exploring play, the kept player and the gym teacher stay at x16); (5) the round's skip guard and label bound become report-only (the label bound refuses a level candidate about 83 times in 100 at 240 held-out decisions). Built now by a Sonnet worker (`feat/round1-memo`, brief `referee/backlog/round1/BRIEF-2.md`). Unverified: the Act 1 cost under generation 13's x16 boss search (the probe ran at a3-v1); the x8 label cost is estimated, not timed. Usage 64% all / 45% Fable at 11:58Z; ceiling 80.

**D55 addendum 11, outcome (2026-11-08 13:15Z, orchestrator).** The human bar is in every automatic judgement: fork main `5f5a8567` (five commits, Sonnet; gate 4,726 tests, 17 failing = 16 baseline + 1 flake, 0 new; the landing rebased over the round's nine commits with no file overlap and re-ran its own, the round's and hindsight's tests; checker CONFIRMED hash, scope, the untouched `PROMOTION_RULE` and `decide`, flags, docs, locks). The fight-gym gate plays the human stratum after every stage-2 verdict (400 starts, four draws, a3-v1; about 32 min of six processes a candidate; `--human-bar on|off`, on) and records the human line in the verdict, the state and `gates/verdicts.jsonl`; a promotion carries the games to the new incumbent's name. The keep test v2's promotion record gets `human_bar` and its promote and rejudge print the fight network's latest human reading; the lab's fight network `64d057e174ac` (generations 11 to 13) is byte-identical to the gym's `players/v2`, so today the line reads 62.0 against the humans' 79.8 in 100, HP lost 38.6 against 33.2. `tools/gym_engine_move_check.py` compares an incumbent's games across engines (on the D51 pair: outcome 1,998, end HP 1,995, move hash 1,973 of 2,000). **The daemon moved** (orchestrator): stopped 13:12:54Z in its yield between gate plays (c0177's stage 1 resumes from its saved games), `out/` backed up as `out-backup/out-5efe972f85e1`, `wt-gym-loop-run` to `5f5a8567`, published 13:13:48Z (restore, publish, EmuDump rc 0; engine tag `e853638def14`), relaunched 13:13:58Z (PID 3996, six processes, K 2, teacher x16, judge-v0; human bar on; regret mode human-shortfall; it waited on B's `b-fast` line). Open: the incumbent's replayed games on the new engine are checked at c0177's gate with the move-check tool; v2's human-stratum games are on the old engine, so the first human lines say the engines differ until v2's stratum is replayed (about 32 min, after B's tests and the judge board free the machine). Usage 65% all / 45% Fable (13:15Z); ceiling 80.

**D55 addendum 12, outcome (2026-11-08 15:19Z, orchestrator).** Round 1's follow-up landed on fork main `b484a503` (three commits, Sonnet: `09e472d3` lambda by act, `d5aeab57` hindsight's labels per act, `b484a503` the round's code; lab code only, `rl/`, `tests/python`, `docs/rl`; gate 4,804 tests, 20 failing = 16 baseline + 4 flakes that pass alone, 0 new; checker CONFIRMED the hash, the config defaults, the recipe parser, the candidate's eight weight files sha256-identical to generation 13's, the seeds and the marker, `jobs.json` and `current.json` untouched, the HANDOFF line). In the code now: `rl/round1_config.json` defaults human 1.0 / agent 0 / label 0, `kl_beta` 1.0, `lambda` 0.5 fixed, `lambda_acts` {} (a zero-weight source is neither trained on nor steers the early stop); `judgement.human_weights` 0.25 / 1 / 4 is a selection step (the lowest held-out clears-Act-2 log-loss among weights that keep clears-Act-1 no worse than the incumbent's; grid and figures in `refit.json` and `vrun_fit.json`); the recipe part `:act<N>=<lambda>` (Act 1 floors 1 to 17, Act 2 from 18) recorded in `agent.json` `human_prior.lambda_acts`, built by `gen0 build --lambda-act 1=0`, the plain recipe byte-identical (tested); labels two a run per act, quota 1,200 split 600 / 600 (`label.act2_min_share` 0.5), ancients a label kind, continuations on the x8 boss schedule `a3-v1@h1e4b8` while the replay and the exploring play stay at x16, `labels.jsonl` schema 3 with `schedule` and `cont_schedule`; the ranking check, card skip guard and label bound are numbers under `guards` and decide `kept` only with `judgement.guards` "gate" (default "report"); `chain.json` carries sha256 and size for every input and output of every step, and a step refuses an input changed since its producer recorded it. **The lambda-by-act candidate** `gen14/candidate-prior-act2` (recipe `vrun+pi_h:lambda=0.5:pi_h=2ebfe6d7:act1=0+stakes:a3-v1@h1e4b16`) waits for the lab's own judgement: seeds `LAB/seeds/E14-2026-11-08.json` (3,000) and the marker `LAB/train/ready-11-g14-prior-act2` (15:12Z), read by the train job's tag form `ready-<gen>-g<target>-<tag>` (D33 addendum (b)); the keep test v2 decides (the memo expects the floor route, not Act 2). Orchestrator checks: the lab tree is at `5f5a8567` and the recipe parses only from `b484a503`, but the runner presorts first when main moved and the last presort (13:10Z) is over an hour old, so the tree moves before the train job starts; `train.timeout_min` 540 against about 14 h of 16 processes for both arms at x16 (generation 13's candidate arm took 20.7 h of wall): the block's `runs.jsonl` resumes across train jobs (`resume_rows`, keyed by agent, configuration and engine), so the judgement completes over two or three jobs; `jobs.json` is not edited while score-real runs (owner option: raise the timeout to 900 at a quiet moment). Unverified: a full-size label run (Act 2 quota fill, x8 yield), the GPU selection step at full size, the block's result. `backlog/round1/jobs-fragment.json` regenerated, still not installed. Usage 67% all / 46% Fable (15:14Z); ceiling 80.

**D55 addendum 13 (2026-11-08 15:22Z, orchestrator; change B's outcome, memo row 6).** B, the run currency (fights priced by the frozen run head), fails its stop rule and is not landed: on the exam's Act 1 hallway cell (100 starts, twelve draws) the player with the currency drinks more, not less (the share of won, potion-holding fights with a potion drunk 60.0 to 66.1 in 100, +5.9 points [+1.3, +10.5]); the rule wanted it down. The rest holds or is level: audit passed; the Act 1 boss board (200 starts, 2,000 games an arm) 41.5 to 41.8 in 100, +0.3 [-0.6, +1.2], lower bound -0.63 against the rule's -2, potions used identical in both arms (0.68 a game); hallway won 97.0 to 96.8, HP lost 9.63 to 9.42; elite won 90.1 both, HP lost 34.4 both; the 200-run copy batch potions at the Act 1 boss door 0.72 to 0.80 (+0.07 +- 0.05), boss kills +3.0 +- 3.6 per 100. Two clauses read false for other reasons: "hallway win at least 99" fails for both arms (the exam cell is harder than the runs' 99.2) and "relics at the door not down" is -0.018 of a relic, 1.35 standard errors. Reading: the currency prices a hallway potion below the HP it saves (drinking up, HP lost a little down) and does not reach the boss decisions (identical potion use, +0.3). **Decided:** B stops here by its rule; nothing lands; the branch `feat/run-currency-r2` (`a4cd7dbb` on the fork, rebased on `b484a503`: the currency, `tools/currency_fast.sh`, the real-game player's `-r` configuration in `referee/lockstep.py` with 8 tests, unplayed against a live game; `docs/rl/RUN_CURRENCY.md`; readings in `referee/backlog/run-currency/fast-20261108T1107Z/report.json`) is kept for the record; `feat/run-currency` (`ec7d0636`) is stale (deletion is the owner's). The unplayed second batch (400 runs at `a3-v1-r`) is not played: the failing clause is on the exam cell with a tight interval, and the batch cannot change the verdict. A redesign (the worker's idea of a potion-price floor of 10 HP in hallways, or pricing a potion by its boss value) is a new experiment for the owner's queue, not a landing. Gate on `9abd0b25`: 4,820 tests, 18 failing = 15 baseline + 3 flakes, 0 new. Usage 67% all / 46% Fable (15:24Z); ceiling 80.

**D55 addendum 14 (2026-11-08 19:01Z, orchestrator; the search's Python tidy, D55 addendum 9 item (2) brought forward under the 80 ceiling).** Landed on fork main: code `556bd7b7`, docs `8a6d79de` (lab code only: `rl/live_search.py`, `Combat.legal` in `rl/combat_mcts.py`, `tests/python/test_search_tidy.py` with 13 tests, one existing spy test re-pointed at `_tempo_weights`, `docs/rl/SEARCH_TIDY.md`). What changed is how the search computes, not what: the observation is read in slices instead of per index; the rollout's weights and pick are Python floats that match numpy's sum and `Generator.choice` to the bit and draw the same one uniform (none for a lone move); a tree step reads its legal actions and moves once and shares them across the merge, the heuristic prior and the network request; each share's invariant is in the doc. Identity, the landing's condition: the fight exam's human stratum (400 starts x 4 draws, player v2, `a3-v1`, CPU prior, same `out/`) before and after, compared with `tools/gym_engine_move_check.py`: outcome 1,600 / 1,600, end HP 1,600 / 1,600, move hash 1,600 / 1,600, root value largest difference 0.0, 1,814,963 simulations and 43,967 decisions alike. Cost on 20 fight-exam starts, one process, CPU time, before and after side by side on the same load: 1013.8 to 892.0 CPU-s (-12.0%) and 907.4 to 813.5 (-10.3%), 4.7 to 6.1 CPU-s a fight, about 6.2 of a run's 55.4 CPU-s (11.2%, above the 5% bar); the gym's teacher configuration (K 2, x16, 20 fights) 1207.3 to 1084.5 CPU-s (-10.2%), 20 of 20 alike. The search's own Python fell from 24.1% to 15.1% of the profiled time; the emulator's step is now 76%. Gate (Python-only, `D:/spireline/logs/fork-tests/8a6d79de.txt`): 4,817 tests, 16 failing = the baseline (4 failures + 12 errors), 0 new, 0 flakes. A side result closes an open item: the before-run is v2's human stratum on the new engine `e853638def14`, and it agrees with the loop's older server-prior games on `e911430a94a1` in all 1,600 games on all three measures, so the engine move did not change the fight player's human-bar reading (62.0 in 100). **Decided:** the landing stands. The lab froze its tree at `b484a503` at 18:26Z and started the train job of `gen14/candidate-prior-act2` then, before this landing, so tonight's judgement runs without the tidy (the decisions are identical either way); the lab takes it at its next presort. The gym daemon's worktree (`wt-gym-loop-run`, `5f5a8567`) moves to main at the next quiet moment with no real-game job and the daemon between segments, not now (the lab's score-real holds `lab-score`). Unverified: the proof used the CPU prior, not the GPU server's batching (the same Python handles the server's values; the bit-equality helpers are guarded by tests against numpy 2.4.6); per-fight CPU on the loaded machine swings 10-40% between runs, only the paired totals are trusted. Checked (landing checker, Haiku, 8 claims, all confirmed): fork main `8a6d79de` on `556bd7b7` on `b484a503`, both on origin; scope four lab files plus the doc; gate file 4,817 / 16 / bad=0; after.txt's three 1,600 of 1,600 and the paired CPU totals; the HANDOFF line first of the worker lines, CRLF; `wt-gym-loop-run` at `5f5a8567`; no user paths. By hand: `Combat.legal` is a three-line change, the spy moved from `live_rollout_weights` to `_tempo_weights`; the files newer under `referee/agent/` are the lab's own E14 arms (its train job of gen14/candidate-prior-act2 has run since 18:26Z: 200 candidate runs done at 18:53Z, the incumbent arm playing). Usage 70% all / 47% Fable (2026-11-08 18:58Z); ceiling 80.

**D46 addendum 2 (2026-11-08 23:40Z, owner: "go up to 90", 2026-11-08 about 23:30Z).** This week's ceiling is 90 (it was raised to 80 on 2026-11-08 morning, D46 addendum); it returns to 75 with new work stopping at 73 at the 2026-11-10 21:00Z reset. Usage at the decision 72% all / 47% Fable (2026-11-08 22:47Z).

**D55 addendum 15 (2026-11-08 23:40Z, owner decisions of 2026-11-08 23:10Z to 23:50Z, recorded by the orchestrator).** On the question "where can we get more data to improve training": (1) **Other characters' runs for the shared decisions (map, rest, shop): rejected.** Owner: "disagree, these depend on the character." Not used for any Ironclad decision. (2) **Co-op runs: never trained on.** Owner: "don't train on coop, very different game." The co-op-seat prior experiment queued in D55 addendum 7's outcome is dropped. (3) **The best players by achievement: now.** Owner: "best players filter do it now." The export's per-player key is blank on solo runs (addendum 7 outcome), so strength is read from the run: S-win (A10 solo Ironclad runs that won) and S-high (A11 to A20 solo Ironclad runs, any outcome), exam fifth out, fifths by the existing hash rule; four fits (all, S-win, S-high, both) on the code path of `pi_h=2ebfe6d7`; held-out leg on won runs and on all runs plus the ranking check; the fit chosen by held-out log-loss on the won runs if within 0.02 nats of the all-player fit on the all-player held-out; a candidate `gen14/candidate-best-players` (generation 13's recipe, only the prior replaced); no marker until the lab has judged `gen14/candidate-prior-act2`. Brief `referee/backlog/best-players/BRIEF.md`; Sonnet worker started. (4) **Labels searched to convergence on human positions.** Owner: "instead of fixed depth, take every A10 position players were in with the decks they had, and search until we are satisfied we have the optimal solution to those turns, with a lesser constraint on time; it is about finding solutions we know are good to train on." Recorded as the direction. The search already draws the unknown cards and enemy rolls afresh in every line (no hidden information), so the labels are for play under uncertainty; "converged" means stable under the current judge, not perfect. First a measurement: 200 boss turns from the exam's human positions searched at 16, 32, 64, 128, 256 with a stopping rule (same move as at half the budget and a top-two gap of two standard errors), reporting agreement, convergence shares, CPU-s to convergence and the cost of a 10,000-turn corpus. Brief `referee/backlog/converged-labels/BRIEF.md`; Sonnet worker started. Whether to build the corpus, and at what budget cap, is decided on the report. (5) **The weekly real block.** Owner asked what it waits for. Rule unchanged (D55 addenda 5 and 8): the next promotion of 3 or more per 100 at the Act 2 boss on the copy, else the 168-hour clock from 2026-11-06 08:52Z, so by 2026-11-13 08:52Z; a block costs about twelve hours of the whole machine and measuring the same player again adds nothing. Awaiting the owner's word if the trigger should change. Usage 72% all / 47% Fable (2026-11-08 22:47Z); ceiling 90.
