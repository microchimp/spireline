# The $100 API-credit plan (2026-10-23 to 2026-11-03)

A time-boxed plan for spending $100 of API credit that expires in early November, beside `PLAN.md` and without changing
it. An Opus session started on the API key runs it from section 4. The credit is spent through the API key only: a
Claude Code session started in a terminal where `ANTHROPIC_API_KEY` is set bills the key, not the subscription. The
key is typed into that terminal for that session and never written to a file, a user-level variable or the lab's
scheduled task (the same rule as the repo's no-stored-GitHub-token rule).

**Stop rules:** stop at $95 of spend on the Console's usage page, or on 2026-11-03, whichever comes first. The
orchestrator records spend per item in section 5 after each item.

## 1. Why this split

Current API prices: Sonnet 5.5 $2 / $10 per million input / output tokens, Opus 5.5 $4 / $20, Haiku 5.5 $0.10 / $0.50,
cache reads $0.20, and the Batch API at half of all of these. A reviewed Sonnet worker round like P0's costs about $2-4;
an Opus review round $4-8. A one-shot review sent as a batch request with the documents pasted in costs under $1. So:

- **Batch everything that reads and writes but does not edit code:** triage, fix kits, failing tests, reviews. About a
  tenth of the credit buys all of it.
- **Spend the agentic rounds on landing fixes** in Lane B, the lane `PLAN.md` starves most, and on the two
  option-neutral rebuild items the review named.
- **Nothing goes into the player** (D7: no LLM components) or into compute the PC already has (training runs on the
  PC's GPU once CUDA torch is installed).

## 2. Allocation

| # | item | how | model | est. | ceiling |
|---|---|---|---|---|---|
| 1 | Triage of the 218 agent-ranked groups, then the 1,880 open lab groups: mechanism, host-suspect confidence, single-site or architectural, with the evidence line | Batch API | Haiku 5.5 | $2 | $4 |
| 2 | Fix kits for every single-site agent-ranked group (~60): the exact divergence, the emulator mechanism and its other uses, the proposed change, the failing scenario test to write, risk | Batch API, one request per group, shared cached prefix (hook and queue code, scenario format) | Sonnet 5.5 | $5 | $8 |
| 3 | Independent one-shot reviews as batch requests: (a) the lockstep bridge and ranking method (`real-game-env.md`, the A1 notes, `top20.md`, HANDOFF section 0); (b) the G1 rule and this plan | Batch API | Opus 5.5 | $2 | $4 |
| 4 | The trace-mode hook-order patch (`rebuild-plan.md` D2) and local table generation (D5): option-neutral, needed for G1 evidence and for any rebuild | Claude Code on the key, Sonnet workers, one reviewer each | Sonnet 5.5 | $18 | $22 |
| 5 | Lane B fix cycle for week 2: land the item-2 kits through bug process v2, one reviewer each, behind the gates | Claude Code on the key, Sonnet workers, Opus amend only after a failed Sonnet round | Sonnet 5.5 | $55 | $55 |
| 6 | Lane F research only: the game's modding framework, what a mod may read, the game's and the framework's terms for a public mod | Claude Code on the key with web access, one capped round | Sonnet 5.5 | $5 | $6 |
| 7 | Reserve for amends | | | | $5 |
| | **total** | | | **$87** | **$100** |

Item 5 is the only one whose size floats: it takes what items 1-4 and 6-7 leave, at about $3 a reviewed round, so
roughly 15-20 landed-or-rejected fixes.

## 3. Order and dependencies

- **Day 1:** items 1, 2 and 3 are submitted as batches (results within hours) and item 4 starts. Item 2 works from the
  traces and repros that exist; groups whose minimal repro the lab has not made yet get a kit marked "repro pending".
- **Day 2 onward:** item 5 lands kits as the reviews and repros allow, in the ranking's order, single-site groups only.
  Architectural groups wait for G1 (`PLAN.md` section 8.3). Item 6 runs once, any day.
- **Division with the subscription session** (P1 week 2, `HANDOFF.md` section 0 briefs): the API-key session owns Lane B
  (brief B1) and item 4 for the two weeks; the subscription session owns C1, A2b, A1b, the leak follow-ups, D1 and the
  weekly review. If the API-key session has landed nothing by day 4, the subscription session takes B1 back. Landing is
  serialised by the fork's `main.lock` either way.
- **Owner prerequisites:** the lab task restarted (the `runs` repro step makes the minimal repros item 5 needs); the API
  key typed into one terminal.

## 4. Runbook for the API-key session

1. Read `docs/PLAN.md` sections 2, 5 (Lane B), 8 and 10, `docs/API_CREDIT_PLAN.md` (this file), and
   `D:/spireline/referee/backlog/HANDOFF.md` section 0 and section 9 (landing rules).
2. Add the `anthropic` package to the Spireline venv (`uv add anthropic`), write `tools/sweeps/batch_sweep.py`: it
   builds one batch per item from the inputs below, submits it with `client.messages.batches.create`, polls until
   `processing_status == "ended"`, and writes each result by `custom_id` into `D:/spireline/referee/agent/gen0/sweeps/`
   (`triage/`, `kits/`, `reviews/`). Requests share a cached system prefix (the mechanism code and formats); the user
   turn carries the per-group material. Outputs are Markdown with a fixed header (group id, verdict, confidence).
   - Item 1 inputs: `D:/spireline/referee/agent/gen0/rank/top20.md` and the group files it names, then
     `D:/spireline/referee/LAB/groups.json` entries for the open lab groups with their shrunk trace summaries.
   - Item 2 inputs per group: the group's symptom, minimal repro and trace; the emulator code of the mechanism (our fork,
     by file and lines); the game method, described from the local decompile in words with class and method names
     (never pasted into a repo, result file or commit); the scenario test format from the fork's tests.
   - Item 3 inputs: the documents named in the allocation table, pasted whole.
   Record the batch ids and the Console cost of each batch in section 5.
3. Item 4: one Sonnet worker per piece (the `L` patch per `rebuild-plan.md` D2, listed in H6 by the owner; table
   generation per D5), one reviewer each, landed per HANDOFF section 9.
4. Item 5: for each kit in ranking order, a capped Sonnet worker (brief: the kit, the test that must fail before and
   pass after, the gate counts, a 60-call cap), one reviewer with the `PLAN.md` section 10 checklist, landed per
   HANDOFF section 9. A worker that fails once gets one Opus amend from the reserve; a second failure parks the group
   with a note in the kit.
5. Item 6: one capped Sonnet round with web access; output `docs/research/MODDING.md` (facts with sources; no game
   text).
6. After every item: section 5 updated with spend; a line in `HANDOFF.md` section 0 under "API-credit lane".
7. Stop rules as above. Final report to the owner under 200 words: fixes landed and rejected, the change in the
   architectural share and in groups closed per round, batch outputs written, spend by item.

## 5. Spend log

| date | item | what | Console cost | running total |
|---|---|---|---|---|
| | | | | $0 |

## 6. What $100 does not buy

- The combat-kernel rebuild (~255 rounds) or its engine-neutral interface (~21 rounds, ~$70). The interface is the
  first thing to fund if the owner decides for the rebuild before G1; it is not in this plan.
- A faster real-game host (parked by `PLAN.md` section 8.1).
- Any LLM inside the player (D7).
