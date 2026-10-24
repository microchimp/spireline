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

**Model note (2026-10-24):** a cloud session runs on the account's default model; the Sonnet/Opus split in the table is
the intended effort per item, not a setting, so the estimates are approximate.

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

## 2. Allocation (revised 2026-10-24 after the independent review, D26)

| # | item | where | est. |
|---|---|---|---|
| 1 | Environment proof (done: PR #1 `cloud/env-proof`, `docs/CLOUD_ENV.md`; all six suites green on Linux) | cloud, fork | $5 |
| 2 | Lane B fixes from kits, one mechanism per session: `cloud/run-flow-1` (Thieving Hopper steal, Fairy in a Bottle), `cloud/combat-core-1` (Bolas, HeldPlayedCard, ShivDamage), then the kit queue in rank order; F08 excluded (rebuild lane) | cloud, fork | $45 |
| 3 | Reviews in the cloud: the pilot, every Lane B PR and the landings get a full review; C2-C6 and the cleanups a light one | cloud, fork | $35 |
| 4 | Kernel handler batches from the fork's `docs/rebuild/CLOUD_BRIEFS.md`: C1 pilot (PR #6), C7 (PR #5), C8 (PR #3) delivered; C2-C6 start from the pilot branch once the pilot's cloud review posts | cloud, fork | $70 |
| 5 | Lab Python measurement items that need no PC data (the rest moved to the subscription) | cloud, fork | $8 |
| 6 | Lane F research (done: `docs/research/MODDING.md`, merged) | cloud, this repo | $6 |
| 7 | Independent one-shot reviews (done: lockstep bridge and ranking, PR #2 fork; F08 migration design, PR #4 fork; this plan and the week-3 briefs, merged here) | cloud, both | $20 |
| 8 | Confirming tests: scenario tests for every gate rejection the PC exports, and the step-API acceptance test the F08 review asks for | cloud, fork | $15 |
| 9 | Documentation the PC lanes have no time for (rebuild docs, kit index, `CLOUD_ENV.md` upkeep) | cloud, fork | $8 |
| 10 | Promotion statistics (D24 follow-up): the guard at one-sided 0.05, the drift check over the lineage's last three blocks, the boss-damage paired guard, a retry cap of two, the power table for `DESIGN.md` 5.4, with tests; flipped on locally | cloud, fork | $8 |
| 11 | Reserve | | $30 |
| | **total** | | **$250** |

**Re-priced 2026-10-24 ~13:40Z on the first usage-page reading:** a delivered session costs about $12, not $5-8, so the $147 left buys
about twelve sessions. Order from here: C2-C6 (five, after the fixed pilot lands), the next Lane B mechanism batches (two or three),
confirming tests (one or two), documentation (one), reserve (one or two). Cloud reviews of PRs stop: the PC lanes review on the
subscription, which has its own weekly limit but no expiry. The table above keeps the intended shares; the counts are the rule.

Items 2 and 4 float: they take what the others leave. The usage page is the only cost signal (cloud sessions do not report per
session), so the table is re-priced after the first three readings.

## 3. Order and ownership

- **Day 1:** item 1. Then items 6 and 7 (no dependencies), and the first kit batch as soon as three kits exist.
- **Day 2 onward:** items 2, 3 and 5 in a loop: kits locally, implementers in the cloud, reviews in the cloud, landing
  locally. Item 4 as the rebuild lane marks batches.
- **Who starts cloud sessions:** the orchestrator session, or the week-3 subscription session for its own lane, with
  `target: cloud` and the repository named; one session per batch; Sonnet unless the item says Opus.
- **Division of the week-3 briefs:** the week-3 subscription session owns A2c, C2, the leak tests, D and the weekly
  review, plus the local half of this pipeline for Lane B (kits, gate, landing); the rebuild lane owns the kernel, F08
  and local tables, and gates item 4; cloud sessions own implementation, review and research only.
- **Environment (set 2026-10-24 by the orchestrator in the owner's browser session):** the Default cloud environment allows the
  .NET installer hosts (`builds.dotnet.microsoft.com`, `download.visualstudio.microsoft.com`, `dotnetcli.azureedge.net`,
  `dot.net`, `ci.dot.net`, `aka.ms`) and runs a setup script that installs the .NET 9 SDK, restores the tools and syncs the
  locked Python environment, with the registry-image route of `docs/CLOUD_ENV.md` as the fallback; the result is cached.
- **Starting a cloud session:** the app starts one only on a message the owner types (or clicks) in the desktop app, never from
  a session-to-session note or over Remote Control; so the orchestrator prepares the briefs and asks for one click per batch.
- **Overnight 2026-10-24/25:** the owner delegated the decisions until morning ("I trust you to do what you think") and
  cannot click; the orchestrator holds the owner's last turn open and starts C2-C6 from it once the kernel lane pushes the
  fixed pilot, and the next Lane B batches if kits K5-K7 publish, within the re-priced counts; a refused start waits for
  the morning click. No new spending route (routines, other repositories) is tried unasked.
- **Liveness rule:** no branch within the time box (60 minutes for a proof, 90 for a batch or review) means the orchestrator
  opens the session at claude.ai/code in the browser pane, reads its transcript, and restarts it or reports; nobody waits
  longer. Day 1 lost six hours to a GitHub access failure nobody could see from the PC.
- **Default rule:** a brief whose acceptance is unit tests is a cloud item; the subscription keeps traces, score-real analysis,
  the gate, landing and the weekly review.
- **Kits:** a six-line header (base sha, cloud and local halves, allowed-file footprint, expected corpus footprint, run-first
  counts, stop rules); one mechanism per session; probe-first kits are local-first.
- **The local gate:** gate the PR tip once, bisect only on red, two landing windows a day, no second read of a cloud-reviewed
  PR; every corpus rejection is exported as an expected-failure scenario so the cloud sees it as a unit test.
- **Rules that reach the cloud:** the fork's `CLAUDE.md` (no game files, no decompiled text, no POSIX-only process APIs
  in Windows code, one emulator per process); results and docs hold no host or user names; cloud PRs go to the fork's
  `main` only, never to upstream unless a local session decides so.

## 4. Spend log

Cloud spend shows on the account's usage page, not per session, so the orchestrator records the running total once a
day here, with what landed.

| date | items run | landed | usage-page total |
|---|---|---|---|
| 2026-10-24 | 1, 6, 7 (three reviews), 4 (C1 pilot, C7, C8), then at ~13:30Z 2 (`cloud/run-flow-1`, `cloud/combat-core-1`) and 10 (D24 guard, `cloud/d24-guard`); the pilot's cloud review waits for the kernel lane's fixed push; every session requested before ~11:00Z died at clone (the GitHub app install was not registered with the Claude account until the claude.ai callback at ~10:55Z); all eight re-requested at ~11:00Z and all eight delivered PRs by 11:37Z | fork PRs #1 env proof, #2 lockstep review, #3 C8, #4 F08 review, #5 C7, #6 C1 pilot (gating on the PC); spireline PRs #1 modding, #2 plan review merged | **$103 spent, $147 left at ~13:40Z** (usage page): eight delivered sessions plus three just started, so about $12 per delivered session, two to three times the table's estimates |

## 5. What the credit does not buy

- Anything that needs the PC: the corpus gate, the byte proof, game traces, scoring blocks, the lab, local tables.
- Any LLM inside the player (D7).
- A faster real-game host (parked, `PLAN.md` section 8.1).
