# Independent review: the cloud-credit plan and the week-3 briefs

Written 2026-10-24 (about 11:00Z) in a cloud session, read-only. Inputs: `docs/CLOUD_CREDIT_PLAN.md` (through the
spend-log entry of 11:00Z), `docs/PLAN.md` (sections 5, 6, 8, 10), `docs/DECISIONS.md` (D23, D24, D25 and its
correction), `docs/DESIGN.md` sections 5.3, 5.4 and 7.3, `docs/review-input/week3-briefs.md`, and, in the fork
(`microchimp/spireline-sim`), `docs/kits/*`, `docs/rebuild/CLOUD_BRIEFS.md`, the review-input snapshots
(by-family ranking, F08 diagnosis) and the promotion code in `rl/gen_loop.py`. Nothing on the PC was readable:
no `HANDOFF.md`, no records, no usage page. Status words as in `PLAN.md`: *measured*, *estimated*, *reasoned*.

Two things were checked rather than read: the state of both repositories on GitHub (branches, pull requests) and
whether a cloud container of this environment can install .NET 9 and run the fork's suites (appendix B).

## 0. Summary

1. **The pipeline did not stall on its design; it stalled on access.** Every cloud session requested before 11:00Z
   died at clone (GitHub app not registered until the owner completed the callback at about 10:55Z). Six hours
   and eight first requests went to that, and the plan's "item 1 first and alone" rule protected nothing because
   item 1 was the thing failing silently. The fix is procedural: a time box per session and the orchestrator
   reading the session's transcript, not the owner checking a UI.
2. **The next stall is the environment.** This container has no .NET SDK, the official installer's download hosts
   are blocked by the network policy, and no reachable package repository carries a .NET 9 SDK (Ubuntu's archive
   has 8.0 and 10.0; Microsoft's repository for Ubuntu 24.04 has none). The fork targets .NET 9. Without a
   network-policy change (one allowed domain) the env proof cannot deliver what the plan assumes; appendix B records
   what was tried and the one fallback that was measured.
3. **The kits are not too thin; three of twelve are not cloud work at all** (probe-first: they need the game), and
   the rest lack four header lines that would let the local gate reject mechanically and the cloud self-check:
   base sha, allowed-file footprint, expected corpus footprint, stop rules. Batch by mechanism, not by count.
4. **The local gate, not the credit, is the binding constraint.** Lane B has 3 to 5 subscription rounds this week
   for kits, gate and landing together, the gate pauses for quiet windows, and each cloud PR is read twice (Opus
   in the cloud, again at landing). Gate the PR tip once, bisect only on red, drop the second read.
5. **Allocation:** item 2 ($60) is sized for a Lane B queue that, after the comparer artefacts were removed, holds
   about 4% of agent weight plus three audit kits; item 5 ($20) is mostly done or needs PC data. Move $35 to the
   F08 handler batches, confirming tests, documentation and a D24 statistics item. The ceilings sum to $270: the
   "reserve" is not one.
6. **Week-3 briefs:** B1 is the brief most likely to fail as written (double-allocated with the cloud plan, needs
   traces in a window that pauses the gate, and its targets are models the rebuild lane owns). Four of the five
   items landed at 06:36Z were cloud-able and consumed subscription rounds while the credit sat idle.
7. **D24 is statistically right about the co-primary and too timid about the guard.** At 2,000 seeds and a 2%
   kill rate the one-sided 0.01 guard detects a halving of the kill rate 57% of the time and a 25% drop 11% of the
   time; six generations of 25% drops pass unnoticed with probability about one half. Run the guard at 0.05 (a
   false fire costs one retrial block, a missed collapse costs generations) and add a drift check across
   generations. A co-primary at today's rates needs 5,000 to 18,000 paired seeds per block; the 10% switch is right.

## 1. The pipeline: where it wastes credit or stalls

### 1.1 What happened on day 1 (measured from the repositories and the spend log)

| time (Z) | event |
|---|---|
| 04:52 | env-proof session created |
| 05:14, 06:27 | no `cloud/env-proof` branch; the orchestrator asks the owner to look in the cloud UI |
| ~08:15 | F08 pilot and two cleanup batches requested before item 1 reported (rule broken, reasonably) |
| ~08:15 to 10:20 | starts refused over Remote Control; re-requested on a desktop message |
| ~10:55 | owner completes the GitHub app callback; the repo picker lists both repos |
| ~11:00 | all eight sessions re-requested with the same briefs |
| 11:11 | this review's check: no `cloud/*` branch on the fork, no pull request open or closed on either repository |

Six hours of the credit window produced nothing, and the reasons (app registration, Remote Control, a session
that died at clone) were all invisible to the plan's rules. What the plan lacks is not an ordering rule but a
**liveness rule**: a cloud session that has not pushed a branch within a time box (60 minutes for the env proof, 90
for a batch) is read by the orchestrator through the remote-session tools (`get_session`, `list_events`), and
restarted with a narrower brief or reported. The owner should never be the one checking a UI for a stuck session.

### 1.2 The environment assumption (measured in this container; see appendix B)

- `dotnet` is not installed. `uv` and Python 3.13 are.
- The official installer route (`dot.net/v1/dotnet-install.sh`, which downloads from `builds.dotnet.microsoft.com`)
  is blocked by the environment's network policy; `nuget.org`, `packages.microsoft.com` and `archive.ubuntu.com` are
  reachable. Ubuntu 24.04's archive carries the 8.0 and 10.0 SDKs and no 9.0; Microsoft's apt repository for
  Ubuntu 24.04 carries no .NET SDK at all. The fork's six projects target `net9.0`. So a .NET 9 SDK cannot be
  installed here by any package manager; it needs the installer's host allowed in the environment's network
  settings (appendix B), or the fallback measured there.
- 35 of the 129 Python test files mention EmuDump or dotnet, so "Python: no new failing name against the baseline
  list" needs a baseline list that only a cloud run can produce. No such list exists yet; `docs/CLOUD_ENV.md` is
  the place and item 1 is its owner.

If the fork's cloud sessions run in the same environment as this one, an implementer that follows the plan's
"run `dotnet test`" spends its first half hour discovering that no route exists, or reports failure. The remedy
costs nothing in credit and is an owner action: allow `builds.dotnet.microsoft.com` under the environment's network
settings (the steps are in the cloud-environments documentation; the "Allow package managers" box stays ticked),
and put the installer call and the two restores in the environment's setup script, so the SDK is present before
a session's first command. `docs/CLOUD_ENV.md` then records the commands, the suite durations and the Python
baseline. Until the policy changes, the only fallback is the 10.0 SDK with major roll-forward (appendix B), which
runs the tests on a runtime the PC does not use and is acceptable for unit tests only because the PC's gate stays
the arbiter.

### 1.3 Kits: too thin for an implementer with no game?

No. The owner kit (`G74caa1c59d`, 37 lines) names the game methods, the emulator sites, four facts with their
assertions and which fail before, a fix sketch, the gate counts and what the landing session must confirm. `Bolas`
and `HeldPlayedCard` are 68 and 85 lines of the same shape. The satellite kits (`G8318fb1cf5` and three more) are
22 lines of "see the owner kit", which is right. The failure modes are different:

1. **Three of twelve kits are probe-first** (`HeldPlayedCard`, `Gc44f78e430`, `G1162c5de18`): their root cause is
   not known and the probe needs the game or the lockstep. `HeldPlayedCard` is nevertheless in `cloud/combat-core-1`.
   The cloud can write the deterministic test and the idempotent `Release`, and that is worth doing, but the kit
   must say which half is the cloud's and that landing without the probe leaves the route unfound.
2. **Baselines and line numbers drift.** Every kit cites 6,755 C# tests; main had 6,774 after landing 1 and has
   moved three times since the kits were written (`7727a1b7` to `f1a869e0`, `2fbd17ad`, `4a4b15fa`). "About line
   4730" is a hint, not an address. The cloud session should run the suites on its branch point first and record
   the counts it saw; the kit should name the branch point.
3. **No allowed-file footprint, no stop rules, no call cap.** `PLAN.md` section 10 requires each brief to carry the
   call cap and the stop-and-report conditions; `CLOUD_BRIEFS.md` has an exact footprint rule ("`git diff --stat
   main...HEAD` must show exactly those") and stop rules; the kits have neither. The footprint is what lets the
   local gate reject in one glance and the cloud self-check before pushing.
4. **The expected corpus footprint is optional today.** `Bolas` states it ("expect the 3 audit fights to change,
   everything else byte-identical"); the others say only that the landing session runs the corpus. Making it
   mandatory turns the one gate signal the cloud cannot see into a prediction the cloud wrote down.

### 1.4 The local gate rejecting what the cloud cannot see

The corpus (4,298 fights, 0 regressed) and the byte proof are the two signals a cloud session cannot produce. A
rejection on either returns to the cloud as prose, and the cloud iterates blind. Two mitigations, both cheap:

- **Predict the footprint** (1.3 item 4): a commit whose corpus change matches its own prediction lands; one that
  does not is rejected with the fight ids.
- **Export the failure as a scenario.** The fork already has a scenario runner (`tests/scenarios`, `SCENARIOS.md`,
  four scenario groups today) and the C8 cleanup adds the block and enemy HP setters it lacks. When the gate rejects
  a commit on a corpus fight, the landing session writes that fight's setup as a scenario with the game's expected
  values and commits it as an expected failure. The cloud then has a unit test that fails for the right reason.
  This is the structural fix; it makes C8 the most valuable of the two cleanups and worth running first.

### 1.5 Serialisation on the single local gate

- `PLAN.md` section 6 gives Lane B 3 to 5 subscription rounds this week for kits, gate and landing together. The
  kit writers have used part of that. Two or three landing rounds remain for Lane B's cloud PRs; the F08 batches are
  gated by the rebuild lane, which is uncapped this week (D25) but shares the one PC.
- The gate pauses during quiet windows (the C2 cliff rerun needs 105 minutes with no builds, tests or corpus runs),
  and the rebuild lane's gate for a handler branch is longer than Lane B's (port-list gate, sites check, construct
  checks, byte proof in 11 modes, a 300-fight fuzz, a per-handler decompile review).
- "Lands commit by commit" with the full gate after each commit multiplies the gate cost by the commits per PR.

Smallest changes: gate the PR tip once and land every commit when it is green; bisect only on red (this is still
"reject only what a commit breaks"). Two landing windows a day instead of a landing per PR. The cloud review is the
only reading review of a cloud PR; the landing session runs gates and reads nothing twice (landing 1 shows each
item "reviewed (ACCEPT, or CHANGES applied)", which is the second read). Medium term, the gate belongs in the lab as a
job on an integration branch (the lab already runs `presort` on a new main sha), with the result in
`readiness.json`, so the session reads a verdict instead of holding the PC.

### 1.6 Review cost per landed commit

Item 3 holds $30 for "every cloud PR and the rebuild lane's landings this week". The pipeline as planned produces
12 to 16 PRs (2 Lane B, the pilot, 5 handler batches, 2 cleanups, 2 to 4 lab, test and docs items) plus the local
landings. An Opus read of a 3 to 5 kit PR against a 6,700-test suite is *estimated* at $3 to $8; $30 buys 4 to 10
of them. Either the line grows to about $45 or the reviewer is matched to the risk: Opus for the pilot (it fixes the
pattern for five batches), for every engine-touching Lane B PR and for the rebuild lane's landings; Sonnet for
C2 to C6 and the cleanups, whose shape the pilot's review has already fixed and whose handlers are inert.

### 1.7 The smallest changes to the kit format and the batch size

**Kit header (six lines, in every kit and in the batch row of the README):**

```
base: <fork main sha the kit was written against>      batch: cloud/<family>-<n>
cloud part: <what the cloud implements> | local part: <probe, trace, corpus check>
footprint: <files that may change>; everything else is a rejection
expect: <corpus fights that change, or "none">; byte proof <identical | differs in modes ...>
run first: dotnet test (both projects), python suite; record the counts on the base sha
stop and report: <conditions>; cap: <calls or minutes>; a failing-test-only commit is an accepted output
```

Keep the body as it is. Replace "about line N" with the function name plus a grep pattern where the kit does not
already give one.

**Batch size.** For Lane B: one mechanism per session, however many groups it closes (the Hopper steal is one
session for five groups; Fairy in a Bottle is another). A session carrying two unrelated mechanisms doubles the
chance that one stop rule idles both. For F08 handler batches: keep the 7 to 10 model rows, but start C2 to C6 from
the pilot branch once the pilot's cloud review is posted, not after its local landing; the local session already
expects to merge the `Registry.cs` blocks by hand. For reviews: cap a PR at ten commits or about 600 changed lines;
split above that.

## 2. Allocation and order

### 2.1 Dependencies and the real critical path

Nothing implements until item 1 reports; item 4 waits on the pilot; C2 to C6 wait on the pilot's landing; Lane B
PRs wait on the local gate's two or three rounds. The credit cannot be spent faster than one gate lands, except on
work that needs no gate: reviews, research, documentation, confirming tests and handler batches that are inert
until R7 flips the switch. The owner's pace (half by Wednesday 2026-10-28) is therefore met only through the
gate-free work, and that is also where quality is bought, so the two goals agree.

*Estimated:* sessions that can run without waiting on a landing by Wednesday: env proof (1), research (1), the
three one-shot reviews (3), pilot (1), cleanups (2), C2 to C6 from the pilot branch (5), two Lane B batches (2),
reviews of those (about 8), confirming tests (2), docs (1), the D24 statistics item (1): about 28 sessions. At the
plan's own average ($205 over about 30 sessions, about $7) that is $125 to $195. The pace is reachable if the eight
re-requested sessions work today and the orchestrator starts the gate-free items without waiting for landings.

### 2.2 The table: what moves earlier, what is missing, what to cut

| # | item | plan est. | proposed | change and why |
|---|---|---|---|---|
| 1 | env proof, plus the setup script and `docs/CLOUD_ENV.md` with suite durations and the Python baseline list | $5 | $8 | the deliverable grows: a recipe every later session uses, not a yes/no |
| 2 | Lane B kits | $60 | $45 | the cloud-able queue after B3's comparer fixes is the Hopper steal (175 weight, 2.5%), Fairy (108, 1.5%), three audit kits and the probe-first residue; the regenerated ranking may add to it, so the item still floats |
| 3 | reviews | $30 | $35 | one reviewer per PR, Opus where 1.6 says, a second Opus read of the pilot only |
| 4 | F08 handler batches | $60 | $70 | 60 pairs are cloud-able now; a second wave (the registered pairs of mixed models) follows if the rebuild lane marks it; the best credit sink in the plan |
| 5 | lab Python items | $20 | $8 | the utilisation report landed locally at 06:36Z; the "unknown strategies" question was answered (an accounting rule, not a runner bug); the placement rules for the unassigned 55% need the records, so only a cloud session fed an exported, aggregated sample of diff shapes can write them |
| 6 | Lane F modding research | $10 | $6 | P2 and P3 work; one session, filler |
| 7 | one-shot reviews | $20 | $20 | in flight |
| 9 | **new:** confirming tests: scenario exports of gate rejections, regression tests for B3's comparer fixes and for landing 1's items, the "other uses of the mechanism" tests `PLAN.md` principle 7 asks for | - | $15 | the cheapest quality the credit can buy and the input to 1.4 |
| 10 | **new:** documentation the PC lanes have no time for: `PLAN.md` section 4 refresh (test counts, corpus size, main sha are stale), the kits README status table, a `docs/rebuild/` status page, `DESIGN.md` 5.4's power note | - | $8 | reading-only work; no gate |
| 11 | **new:** promotion statistics (section 4): the guard at 0.05, the drift check, a retry cap, a power table, unit tests in `rl/gen_loop.py`'s suite | - | $8 | Python with tests; no game needed; the local flip is one line |
| 8 | reserve | $20 | $27 | the plan's ceilings sum to $270 against $250, so the plan has no reserve today |
| | total | $205 | $250 | the credit expires; unspent is lost, so the estimate column should sum to the credit and the ceilings below it |

Order: item 1 today with the setup script; then the pilot, both cleanups (C8 first), the reviews and item 11 at
once; C2 to C6 as soon as the pilot's review posts; Lane B's two batches when their kits carry the header; items 9
and 10 as fillers whenever the usage page lags the pace line.

### 2.3 Two settings the plan treats as fixed

- **Model.** The plan says the Sonnet/Opus split "is not a setting". The remote-session tool that starts a cloud
  session takes a model, and a session started from the app runs on the model the app is set to. Whoever starts a
  session chooses; the spend log should record the model per session, because if the account default is Opus the
  estimates are off by a factor of three to five.
- **Permissions.** A cloud session that hits a permission prompt nobody answers looks exactly like the env proof
  looked this morning. Start sessions in a mode that does not prompt inside the environment, and put the installs in
  the setup script so there is nothing to prompt for.

## 3. The week-3 briefs

### 3.1 Gaps

- No brief owns `docs/CLOUD_ENV.md`, the setup script or reading the usage page; the spend log's last column says
  "not read".
- No brief regenerates the ranking after B3. The kits and the by-family table were built on a block in which 22
  groups (about 450 weight, 6.4%) were comparer artefacts, and the table's "unassigned" is 55.2% of the weight.
  `G1162c5de18` is already suspected to be the residue of an earlier comparer fix. Kit writers should not be pointed
  at a table that the same session has since corrected.
- No landing schedule. Two landing windows a day, published in the status file, would let the cloud and the rebuild
  lane plan around the gate instead of asking for quiet windows ad hoc.
- The weekly review brief quotes the G1 numbers (architectural share 54.8%, top five 54.5%) without saying what the
  table can and cannot show: only five families carry weight, the lockstep diff cannot see powers, counters, energy
  or potions, and 55% is unassigned. The by-family document says this; the brief should.

### 3.2 Contradictions with the plan

- **B1 against D25 and the cloud plan.** B1's second and third parts (HeldPlayedCard, Bolas, ShivDamage, then the
  by-family rules) are item 2 and item 5 of the cloud plan. D25 moved Lane B's single-site fixes to the credit; B1
  still lists them as a 3 to 5 round subscription brief.
- **"Item 1 runs first and alone"** against the spend log, which started items 6, 7 and three item-4 batches before
  item 1 reported. The log's reasoning is sound (they need only `dotnet test`, bounded risk), so amend the rule: the
  ordering applies to sessions that need the suites, and even those may start once the setup script exists.
- **A2c's "4x search cost" item** rests on a week-2 number that did not reproduce (1.4x in CPU time, measured at
  landing 1). The brief item is moot; the batched or cached inference work it asks for has no measured trigger.
- **The C2 cliff rerun's premise.** C2a found that `Driver.Save` never runs in env sessions, so the incremental Save
  was not the cliff's cause; two earlier reruns did not reproduce the cliff. The rerun stays worth doing once with
  the bench's system-stats logging, but it should not hold a 105-minute window every time the hypothesis changes.
- **`PLAN.md` 8.3 has a gap between 50% and 70%.** The weekly review brief reports "neither tier rule" at 54.5%.
  The rule should say what happens in the gap; since the owner already chose Tier 1's kernel (D23) and the F08
  migration is under way (D25), G1 now decides the family order and any escalation, not whether to rebuild. The
  brief should be rewritten to that question, and the "two fix cycles" precondition read accordingly.

### 3.3 Items that should be cloud items instead of subscription items

Landing 1 (06:36Z) landed five items from subscription workers. Four needed no game: the leak tests (C# facts), D's
runner changes (Python tooling), C2b (`Sts2Run_ResetAs` and potion use outside fights, C# with tests) and C2a
(`ResultsFile.cs`). Only B3 (the comparer, measured against records) was local work. Going forward, the default
rule should be: **a brief whose acceptance is unit tests goes to the cloud; the subscription keeps game-touching
work (traces, score-real analysis, the gate, landing) and the weekly review.** Under that rule, of the week-3 list:
A2c's emulator-side code (batched inference, V_run keep conditions as code) is cloud with a local measurement
step; C2's remaining emulator options are cloud; the leak tests are cloud; D's runner items are cloud; B1's fixes
are cloud (they already are, on paper). What stays local: B1's traces, C2's cliff rerun and recycle check, the
A2c dev-set measurements, the weekly review.

### 3.4 The brief most likely to fail as written: B1

B1 fails on three counts at once. Its last two thirds are double-allocated (3.2). Its first third needs one game
trace per F08 mechanism (D, E, C, then B as an interim) inside a quiet window that pauses the gate the same session
must run, and the quiet-window request already covers the cliff rerun, the F08 trace targets and the recycle check
in 105 minutes. And its targets are the rebuild lane's: `CLOUD_BRIEFS.md` lists Lagavulin Matriarch and Soul Fysh
under the LOCAL monster batches of the F08 migration and Shrink and Slow as open pairs in power-1 and power-3, so a
Lane B single-site fix in the old engine for D, E, C or the Slow interim edits `EnemyAI.cs` and `BuffSystem.cs`,
which R4 is rerouting and whose hashes `sites.json` records. The fix either collides with R4 or is thrown away by the
migration within the week. Rewrite B1 as a trace brief: run the six trace targets the F08 diagnosis lists, hand A
and F to the rebuild lane, and turn D, E and C into kits for the cloud only where the trace shows a rule that lives
outside the files R4 edits. The runner-up is the C2 cliff rerun, for the reasons in 3.2.

## 4. D24: the boss-kill guard

### 4.1 Power at the current rates

The promotion block is 2,000 paired seeds (`resolve_e_block`, n = 2000; D24's 53 discordant pairs match it), not
500; the 500-run figure is the real-game scoring block. Both are tabulated. The test is the exact one-sided McNemar
on discordant pairs, as implemented in `rl/gen_loop.py` (`mcnemar_exact_one_sided`, `decide`). *Estimated* under
independence of the two arms' kills on a seed (discordance = p1 + p2 - 2 p1 p2); real arms are positively
correlated (D24 saw 53 discordant pairs where independence predicts 66), so the true power is lower still.

Guard mode: the probability that a candidate whose kill rate fell is stopped (incumbent at 2%).

| true drop | seeds | one-sided 0.01 | one-sided 0.05 |
|---|---|---|---|
| 2.0% to 1.5% (a quarter) | 500 | 2% | 10% |
| 2.0% to 1.3% (a third) | 500 | 4% | 16% |
| 2.0% to 1.0% (a half) | 500 | 9% | 28% |
| 2.0% to 1.5% | 2,000 | 11% | 29% |
| 2.0% to 1.3% | 2,000 | 24% | 49% |
| 2.0% to 1.0% | 2,000 | 57% | 81% |
| 2.0% to 0.5% | 2,000 | 98% | 100% |

At 500 seeds there are about 15 discordant pairs and the 0.01 guard needs 13 of them one way: a formality. At
2,000 the guard catches a collapse to a quarter and usually a halving; it does not see a 25% drop. The compounding
case is the one that matters: six generations each losing a quarter of the kill rate take it from 2% to 0.4%, and
the probability that the 0.01 guard never fires along the way is about 0.89^6, one half. At 0.05 it is 0.71^6,
about one in eight, and the guard weakens further as the rate falls (fewer discordant pairs).

Co-primary mode: the probability that a real improvement passes (one-sided 0.01).

| improvement | 500 seeds | 2,000 seeds | 4,000 seeds | seeds for 80% power |
|---|---|---|---|---|
| 1.35% to 2.0% (generation 1) | 4% | 20% | 44% | about 7,700 |
| 2% to 2.5% | - | - | - | about 17,600 |
| 2% to 3% | 6% | 35% | 68% | about 4,800 |
| 2% to 4% | 26% | 91% | 100% | about 1,400 |
| 10% to 13% | 18% | 73% | 97% | about 2,300 |
| 10% to 15% | 49% | 99% | 100% | about 900 |

### 4.2 Verdict on D24

- **Dropping the co-primary at 1 to 2% is right.** A co-primary with 80% power against a 50% relative gain needs
  about 4,800 paired seeds (2.4 blocks); against a 25% gain, about 17,600 (nine blocks, a day of self-play per
  generation). The lab cannot pay that per generation. The 10% switch is well placed: at 10% and 2,000 seeds a 30%
  relative gain has 73% power, a 50% gain 99%.
- **The guard at 0.01 is nearly free of false fires and nearly free of power.** Its cost model is asymmetric: a
  false fire costs one retrial on a fresh block (the loop already grants another budget after a rejection); a
  missed collapse costs generations and shows up only in the weekly real-game block. A guard should lean toward
  firing. Run it at one-sided 0.05: power against a halving rises from 57% to 81%, against a one-third drop from 24%
  to 49%, at the price of about one spurious retrial in twenty generations.
- **Re-judging generation 1 on its existing block under the new rule** is post hoc, and D24 says so; it is
  defensible because the primary passed at p = 5e-5 and the rule change was argued from power, not from the result.
  It should not become a habit: rule changes apply from the next block.

### 4.3 A better guard

Keep the McNemar guard (at 0.05) and add two checks that cost no extra runs:

1. **A drift check across generations.** Pool the promoted lineage's last three blocks (6,000 seeds) and compare the
   candidate's kill rate on its block with the pooled rate (unpaired, same seed distribution; Wilson intervals). Flag
   the promotion for the weekly review when the candidate's 95% upper bound is below the pooled lower bound; block it
   when that happens twice in a row. This catches the slow trade of kills for floors that no per-generation test at
   these rates can see.
2. **A continuous boss-fight measure as a paired guard.** Damage dealt to the Act-1 boss as a fraction of its HP, 0
   when the boss is not reached, paired by seed, cluster bootstrap exactly as the floor primary, not-worse at
   one-sided 0.05. It measures the intent of the boss-kill check (the ability to win the boss fight) with the power
   of a continuous variable, and becomes informative long before kills reach 10%. It needs one field in `runs.jsonl`.

Two side findings from the promotion code and log. (a) The loop grants another budget after each rejection with
no cap: generation 3 was rejected at 23:29Z and promoted at 00:54Z on a fresh block. The retried candidate is
retrained, so it is not the same test twice, but each attempt is another 1% draw; over 20 generations with two
attempts each the expected false promotions are about 0.4, not 0.2. Cap attempts at two per generation and record
the attempt in `promotions.tsv` (the block name already carries `-r1`). (b) Promotions at the margin (lower bounds
+0.09 and +0.06 floors) are real under the rule but subject to the winner's curse: the promoted agent's true gain is
smaller than its block showed. The real-game block is the unbiased number, which is why the headline must stay there.

## 5. Ranked recommendations

| # | recommendation | expected effect | cost |
|---|---|---|---|
| 1 | **Unblock the environment today:** allow the .NET installer's host (`builds.dotnet.microsoft.com`) in the environment's network settings, and a setup script that installs the 9.0 SDK and restores both test projects; `docs/CLOUD_ENV.md` with the commands, the suite durations and the Python baseline list; sessions started in a non-prompting mode. Until the policy changes, the 10.0 SDK with major roll-forward is the measured fallback (appendix B) | every implementer session starts at the tests instead of at the installer; the env proof becomes a recipe | two owner actions (a domain and a few lines in the environment's settings), one cloud session ($5 to $8) |
| 2 | **A liveness rule for cloud sessions:** no branch within the time box (60 min env proof, 90 min batch) means the orchestrator reads the session's transcript with the remote-session tools and restarts or reports | the six silent hours of day 1 do not repeat; the owner stops being the monitor | none |
| 3 | **Kit header and batch-by-mechanism** (1.7): base sha, cloud and local halves, footprint, expected corpus footprint, run-first, stop rules; one mechanism per Lane B session; probe-first kits marked local-first | fewer rejections the cloud cannot see; a stuck mechanism idles one session, not two | one hour of kit-writer time per batch |
| 4 | **Gate the PR tip once, bisect on red, two landing windows a day, no second read of a cloud-reviewed PR** | landing capacity two to three times today's within the same 3 to 5 rounds | none; a line in the status file |
| 5 | **Export every gate rejection as a scenario** (expected failure in `tests/scenarios`); run C8 first among the cleanups because it supplies the setters | the corpus signal reaches the cloud as a unit test; the blind iteration loop closes | C8 as planned; 10 minutes per rejection |
| 6 | **Re-allocate** per 2.2: item 2 to $45, item 5 to $8, item 6 to $6, item 4 to $70, item 3 to $35; add confirming tests ($15), documentation ($8), promotion statistics ($8); estimates sum to $250 and ceilings below it | the credit goes where the queue is (F08 handlers, tests, docs) and the pace line is met with gate-free work | none |
| 7 | **Start C2 to C6 from the pilot branch when the pilot's cloud review posts**, not after its landing; Sonnet reviewers for C2 to C6 and the cleanups, Opus for the pilot, Lane B and the landings | five batches run in parallel this week instead of after one landing; review spend matched to risk | the local merge of `Registry.cs` blocks, already planned |
| 8 | **Rewrite B1 as a trace brief** and move its fixes to the cloud queue; drop A2c's "4x" item; make the weekly review brief ask G1's real question (family order and escalation) and amend `PLAN.md` 8.3 for the 50 to 70% gap; regenerate the ranking after B3 before the next kits | the brief most likely to fail is replaced by one that feeds both lanes; kits stop chasing artefacts | one subscription round for the ranking; edits to the briefs |
| 9 | **D24 follow-up** (4.3): guard at one-sided 0.05, drift check over the lineage's last three blocks, the boss-damage paired guard, a retry cap of two, the power table in `DESIGN.md` 5.4; as a cloud item with tests, flipped locally | a slow loss of boss-kill ability is caught in two generations instead of six; one spurious retrial in twenty generations | one cloud session ($5 to $8), a one-line local change |
| 10 | **Default rule:** a brief whose acceptance is unit tests is a cloud item; the subscription keeps traces, score-real analysis, the gate, landing and the weekly review; record the model and the cost per session in the spend log and re-price the table after the first three usage-page readings | subscription rounds stop going to work the credit could do; the estimates become measured | none |

## Appendix A: how the numbers in section 4 were computed

Exact McNemar power: for n paired seeds with kill rates p1 (incumbent) and p2 (candidate), discordance
d = p1 + p2 - 2 p1 p2 (independence); the number of discordant pairs m is Binomial(n, d); given m, the count of
incumbent-only kills is Binomial(m, (p1 - p1 p2) / d); the guard fires when that count reaches the smallest k with
P(X >= k | m, 1/2) <= alpha. Power is the mixture over m. Sample sizes for 80% power use the normal approximation on
the discordant pairs, one-sided alpha 0.01. The independence assumption overstates discordance and so overstates
power for real arms. The arithmetic is 60 lines of standard-library Python and can be re-run by anyone.

## Appendix B: the environment check in this container

Measured in this review session's container (Ubuntu 24.04, 4 cores, no .NET SDK installed), which runs under
this repository's cloud environment; the fork's sessions may use another environment, so the env proof should
repeat the check. HTTP status through the environment's proxy: `dot.net/v1/dotnet-install.sh` 301 to a blocked
host; `builds.dotnet.microsoft.com` and `download.visualstudio.microsoft.com` unreachable; `packages.microsoft.com`
200; `archive.ubuntu.com` 200; `api.nuget.org` 200. After `apt-get update`: Ubuntu's archive offers
`dotnet-sdk-8.0` and `dotnet-sdk-10.0` and no 9.0; Microsoft's repository for Ubuntu 24.04, added and updated,
lists no `dotnet-sdk` package. The fork's six projects target `net9.0`. The cloud-environments documentation
names the remedy: the host goes under Allowed domains in the environment's network settings, with the package
managers box left ticked.

**The fallback, measured here:** `apt-get install dotnet-sdk-10.0` from Ubuntu's archive took 15 s; with
`DOTNET_ROLL_FORWARD=Major`, `dotnet restore` of the emulator test project took 13 s (NuGet supplied the 9.0
targeting pack) and `dotnet build` 27 s with 24 warnings and no error, so a `net9.0` project builds under the 10.0
SDK. The emulator suite was still running on the 10.0 runtime when this document was committed; its pass count and
duration are appended below once it finishes. A suite that passes there is evidence for unit-test work only: the PC
gates on .NET 9, and any difference between the runtimes is the PC's to see.
