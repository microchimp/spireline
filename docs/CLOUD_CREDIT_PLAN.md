# The $250 cloud-credit plan (2026-10-24 to 2026-11-05)

The owner's account holds $250 of **Claude Code cloud-session credit**, applied automatically to cloud sessions and
expiring at 18:59 GMT+11 on 2026-11-05. It is not API credit: there is no API key, no Batch API and no key session. The
earlier `API_CREDIT_PLAN.md` is replaced by this file (D25, corrected 2026-10-24).

A cloud session is a Claude Code session running in Anthropic's hosted environment on a clone of a GitHub repository:
`microchimp/spireline` (this repo) or `microchimp/spireline-sim` (our fork of r33hab/sts2). It can read and change code,
run the fork's .NET and Python unit suites, search the web, and push a branch. It cannot reach this PC: no game, no
recordings, no lab data, no corpus, no decompile. So the credit buys **implementation against unit tests, reviews and
research**, and the PC's subscription sessions keep **kit writing, the corpus gate, the byte proof and landing**.

**Pace:** the owner asked for half spent by the end of Wednesday 2026-10-28 ($125) and the rest before expiry. Spend
on quality, never on idle calls: Opus reviewers, confirming tests, a second implementer on a hard kit.

## 1. The pipeline

1. **Kit (local, subscription, cheap).** A Sonnet subagent on the PC writes a kit per single-site group into the fork at
   `docs/kits/<group>.md`: the symptom in words, the expected behaviour from the game method (described, with class and
   method names, never pasted), the emulator mechanism and its other uses, the scenario test to write, the gate counts.
   No game data, no recordings, no decompiled text in the kit.
2. **Implement (cloud, credit).** One cloud session per batch of three to five kits of one family, Sonnet, on the fork:
   for each kit a scenario test that fails before and passes after, the fix, the unit suites green (`dotnet test` for
   `src/Sts2Emulator.Tests` and `tools/emudump.Tests`, the Python suite under `tests/python`), one commit per kit on a
   branch `cloud/<family>-<n>`, pushed, with a PR to the fork's `main` describing each commit. Never
   `lint-and-test.sh` (E2 list); never anything that needs the game.
3. **Review (cloud, credit).** An Opus cloud session reviews the PR with the `PLAN.md` section 10 checklist and posts
   its verdict on the PR.
4. **Gate and land (local, subscription, mechanical).** The week-3 subscription session fetches the branch, runs the full
   gate (corpus 0 regressed with a stored baseline, byte proof where the engine is touched, EmuDump), lands commit by
   commit per HANDOFF section 9, rejects only what a commit breaks, pushes fork `main`, and closes the PR.

## 2. Allocation

| # | item | where | model | est. | ceiling |
|---|---|---|---|---|---|
| 1 | Environment proof: build the fork in the cloud (Linux, .NET 9, uv), run both .NET suites and the Python suite, record setup commands and anything Windows-only in `docs/CLOUD_ENV.md` | cloud, fork | Sonnet | $5 | $8 |
| 2 | Lane B fixes from kits: run flow (treasure HP, gold, potions; `select_cards` deck), rewards, the `HeldPlayedCard` snapshot, the Bolas duplicate, the ShivDamage alias, then the kit queue in rank order; F08 excluded (rebuild lane) | cloud, fork | Sonnet | $60 | $75 |
| 3 | Reviews of every cloud PR and of the rebuild lane's landings this week | cloud, fork | Opus | $30 | $35 |
| 4 | Kernel handler batches the rebuild lane marks as cloud-able in `docs/rebuild/` (F08 handler batches, later families), from the migration doc and unit tests; the rebuild lane gates and lands | cloud, fork | Sonnet | $60 | $70 |
| 5 | Lab Python measurement items: by-family record fields (acted, turn, encounter) and placement rules for the 49 unplaced groups; the runner's unknown strategies; the utilisation report | cloud, fork | Sonnet | $20 | $25 |
| 6 | Lane F research: the game's modding framework, what a mod may read, the game's and the framework's terms for a public mod; `docs/research/MODDING.md` in this repo, facts with sources, no game text | cloud, this repo | Sonnet | $10 | $12 |
| 7 | Independent one-shot reviews: the lockstep bridge after M1/M2 and the ranking method; the F08 migration design; this plan and the week-3 briefs | cloud, this repo | Opus | $20 | $25 |
| 8 | Reserve | | | | $20 |
| | **total** | | | **$205** | **$250** |

Items 2 and 4 float: they take what the others leave. Item 1 runs first and alone; nothing else starts until it says
the suites run in the cloud.

## 3. Order and ownership

- **Day 1:** item 1. Then items 6 and 7 (no dependencies), and the first kit batch as soon as three kits exist.
- **Day 2 onward:** items 2, 3 and 5 in a loop: kits locally, implementers in the cloud, reviews in the cloud, landing
  locally. Item 4 as the rebuild lane marks batches.
- **Who starts cloud sessions:** the orchestrator session, or the week-3 subscription session for its own lane, with
  `target: cloud` and the repository named; one session per batch; Sonnet unless the item says Opus.
- **Division of the week-3 briefs:** the week-3 subscription session owns A2c, C2, the leak tests, D and the weekly
  review, plus the local half of this pipeline for Lane B (kits, gate, landing); the rebuild lane owns the kernel, F08
  and local tables, and gates item 4; cloud sessions own implementation, review and research only.
- **Rules that reach the cloud:** the fork's `CLAUDE.md` (no game files, no decompiled text, no POSIX-only process APIs
  in Windows code, one emulator per process); results and docs hold no host or user names; cloud PRs go to the fork's
  `main` only, never to upstream unless a local session decides so.

## 4. Spend log

Cloud spend shows on the account's usage page, not per session, so the orchestrator records the running total once a
day here, with what landed.

| date | items run | landed | usage-page total |
|---|---|---|---|
| 2026-10-24 | | | $0 |

## 5. What the credit does not buy

- Anything that needs the PC: the corpus gate, the byte proof, game traces, scoring blocks, the lab, local tables.
- Any LLM inside the player (D7).
- A faster real-game host (parked, `PLAN.md` section 8.1).
