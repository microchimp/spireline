# The $100 API-credit plan (started 2026-10-24; $100 spent by Wednesday 2026-10-28)

A time-boxed plan for spending the first $100 of the $200 API credit, beside `PLAN.md` and without changing it. An
Opus session started on the API key runs it from section 4. The credit is spent through the API key only: a Claude
Code session started in a terminal where `ANTHROPIC_API_KEY` is set bills the key, not the subscription. The key is
typed into that terminal for that session and never written to a file, a user-level variable or the lab's scheduled
task (the same rule as the repo's no-stored-GitHub-token rule).

**Status (2026-10-24): started by the owner (D25).** The owner's deadline for this half is the end of Wednesday
2026-10-28. The second $100 is planned separately once this half's yield is known, before the credit expires in early
November. History: the plan was on hold from 2026-10-23 for one day; during the hold the subscription session wrote the
by-family report and the rebuild lane took the `L` patch and the local tables, so those items are gone from the table.

**Stop rules:** stop at $100 of spend on the Console's usage page for this half, or at the end of 2026-10-28, whichever
comes first. The orchestrator records spend per item in section 5 after each item and at the end of each day.

## 1. Why this split

Current API prices: Sonnet 5.5 $2 / $10 per million input / output tokens, Opus 5.5 $4 / $20, Haiku 5.5 $0.10 / $0.50,
cache reads $0.20, and the Batch API at half of all of these. A reviewed Sonnet worker round costs about $2-4; an Opus
review round $4-8. A one-shot review sent as a batch request with the documents pasted in costs under $1. So:

- **Batch everything that reads and writes but does not edit code:** triage, fix kits, reviews. About a tenth of the
  credit buys all of it.
- **Spend the agentic rounds on landing fixes** in Lane B, the ranked queue of single-site emulator bugs that the
  subscription lanes cannot afford while the rebuild lane runs. This is the same work the fix lane always did, paid
  through the key instead of the subscription.
- **Nothing goes into the player** (D7: no LLM components), into compute the PC already has, or into the kernel rebuild
  and the F08 migration, which the rebuild lane owns.

## 2. Allocation (four days)

| # | item | how | model | est. | ceiling |
|---|---|---|---|---|---|
| 1 | Triage of the open groups on the fixed-lockstep ranking (`D:/spireline/referee/agent/gen0/rank-s2-m12/`): mechanism, single-site or architectural, host-suspect confidence, evidence line; each of the 49 unplaced groups gets a proposed family rule | Batch API | Haiku 5.5 | $2 | $4 |
| 2 | Fix kits, one per single-site group in rank order, F08 excluded (rebuild lane): run flow (treasure HP, gold, potions; `select_cards` deck), rewards, the `HeldPlayedCard` snapshot, the Bolas duplicate, the ShivDamage alias. Each kit: the exact divergence, the emulator mechanism and its other uses, the proposed change, the failing scenario test to write, risk | Batch API, one request per group, shared cached prefix (mechanism code, scenario format) | Sonnet 5.5 | $6 | $10 |
| 3 | Independent one-shot reviews as batch requests: (a) the lockstep bridge after the M1/M2 fixes and the ranking method; (b) the F08 migration design (kill inside each Damage call) in the rebuild lane's `TIER1_KERNEL.md`, for that lane; (c) the week-3 briefs in `HANDOFF.md` section 0 | Batch API | Opus 5.5 | $3 | $5 |
| 4 | Lane B fix cycle (HANDOFF week-3 brief B1, F08 kill timing excluded): traces first for Lagavulin Matriarch plating, Shrinker Beetle and Soul Fysh, fixes where single-site; then the item-2 kits in rank order through bug process v2, one reviewer each, behind the gates; then the by-family record fields (acted, turn, encounter) and rules, and widening the lockstep diff to powers, energy and relic counters | Claude Code on the key: two or three capped Sonnet workers in parallel, one reviewer each; Opus amend after a failed Sonnet round | Sonnet 5.5 | $70 | $70 |
| 5 | Lane F research only: the game's modding framework, what a mod may read, the game's and the framework's terms for a public mod; output `docs/research/MODDING.md` | Claude Code on the key with web access, one capped round | Sonnet 5.5 | $5 | $6 |
| 6 | Reserve for amends | | | | $5 |
| | **total** | | | **$86** | **$100** |

Item 4 is the only one whose size floats: it takes what the others leave, at about $3 a reviewed round, so roughly 20
landed-or-rejected fixes and the measurement work.

**Pace line (Console total at each day's end):** Saturday $20, Sunday $45, Monday $70, Tuesday $90, Wednesday $100. If
the total is more than $10 under the line at a day's end, spend on quality rather than let the credit lapse: an Opus
reviewer on every landing, a third parallel worker, a confirming game trace for every kit. Never pad with idle calls.

## 3. Order and dependencies

- **Day 1 (Saturday):** items 1, 2 and 3 are submitted as batches (results within hours); item 4 starts at once with the
  three traces and the top run-flow kit, from the traces and repros that exist. Groups whose minimal repro the lab has
  not made yet get a kit marked "repro pending" and a lab `runs` repro request.
- **Day 2 onward:** item 4 lands kits as the reviews and repros allow, in the ranking's order, single-site groups only.
  Architectural groups and everything in F08 go to the rebuild lane. Item 5 runs once, any day.
- **Division of the week-3 briefs:** the API-key session owns Lane B (brief B1) for the week; the subscription session
  owns A2c, C2, the leak tests, D and the weekly review; the rebuild lane owns the kernel, the F08 migration and local
  tables. Landing is serialised by the fork's `main.lock`; a game process needs `QUIET.lock` (session name and UTC time,
  wait if under two hours old); HANDOFF section 0 is append-only, under the heading "API-credit lane".
- **Owner prerequisites:** the lab task running (its `runs` repro step makes the minimal repros item 4 needs); the API
  key typed into one terminal.

## 4. Runbook for the API-key session

1. Read `docs/PLAN.md` sections 2, 5 (Lane B), 8 and 10, `docs/API_CREDIT_PLAN.md` (this file),
   `D:/spireline/referee/backlog/HANDOFF.md` section 0 (the week-2 review and the week-3 brief B1) and section 9
   (landing rules), `D:/spireline/referee/rebuild/f08-diagnosis.md` (to know what not to touch) and
   `D:/spireline/referee/agent/gen0/rank-s2-m12/by_family.md`.
2. Add the `anthropic` package to the Spireline venv (`uv add anthropic`), write `tools/sweeps/batch_sweep.py`: it
   builds one batch per item from the inputs below, submits it with `client.messages.batches.create`, polls until
   `processing_status == "ended"`, and writes each result by `custom_id` into `D:/spireline/referee/agent/gen0/sweeps/`
   (`triage/`, `kits/`, `reviews/`). Requests share a cached system prefix (the mechanism code and formats); the user
   turn carries the per-group material. Outputs are Markdown with a fixed header (group id, verdict, confidence).
   - Item 1 inputs: the ranking files under `rank-s2-m12/` and the group files they name.
   - Item 2 inputs per group: the group's symptom, minimal repro and trace; the emulator code of the mechanism (our fork,
     by file and lines); the game method, described from the local decompile in words with class and method names
     (never pasted into a repo, result file or commit); the scenario test format from the fork's tests.
   - Item 3 inputs: the documents named in the allocation table, pasted whole.
   Record the batch ids and the Console cost of each batch in section 5.
3. Item 4: for each trace or kit in ranking order, a capped Sonnet worker (brief: the kit, the test that must fail before
   and pass after, the gate counts, a 60-call cap, no killing processes by image name), one reviewer with the `PLAN.md`
   section 10 checklist, landed per HANDOFF section 9. A worker that fails once gets one Opus amend from the reserve; a
   second failure parks the group with a note in the kit.
4. Item 5: one capped Sonnet round with web access; output `docs/research/MODDING.md` (facts with sources; no game
   text).
5. After every item and at every day's end: section 5 updated with the Console total; a line in `HANDOFF.md` section 0
   under "API-credit lane"; the pace line checked.
6. Stop rules as above. Final report to the owner under 200 words: fixes landed and rejected, the change in the
   architectural share and in groups closed per round, batch outputs written, spend by item, and what the second $100
   should buy.

## 5. Spend log

| date | item | what | Console cost | running total |
|---|---|---|---|---|
| | | | | $0 |

## 6. What this $100 does not buy

- The kernel rebuild, the F08 migration or local tables (the rebuild lane, D23 and D25).
- A faster real-game host (parked by `PLAN.md` section 8.1).
- Any LLM inside the player (D7).
- The second $100: planned after this half reports, before the early-November expiry.
