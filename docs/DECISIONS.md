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
