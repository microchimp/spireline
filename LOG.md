# Log

Newest first. Facts measured here carry the command that produced them; anything not run is
marked UNVERIFIED.

## 2026-10-11 · Public scaffold prep (Mac)

**Retargeted** to Ascension 10 with all ten modifiers on, Acts 1-3, Defect first
(docs/DECISIONS.md D11-D14). `eval/prereg/phase1.yaml` is now 0.2-DRAFT (`ascension: 10`,
`acts: [1, 2, 3]`; seed-block hashes unchanged). `spireline/__init__.py` gains `ASCENSION`,
`ACTS` and `PRIMARY_CHARACTER`. The synthetic fixture's `ascension` is 10. New test
`tests/test_prereg.py::test_prereg_targets_a10_defect_acts_1_to_3`.

**Public-repo prep:** MIT `LICENSE`, `CONTRIBUTING.md`, CI (`.github/workflows/tests.yml`). The
third-party security review is private: it was moved out of the repo and `docs/SECURITY_REVIEW.md`
is gitignored, along with `data/`, `*.jsonl.gz`, `results/`, `bench/results/`, `.cache/`,
`versions.lock` and `versions.pc.lock`. The PC setup kit now ships as `pc-setup/`. Its CHECKLIST
recommends cloning the public repo (D0). `build-emulator.sh` still requires a typed GO when the
review is absent and prints a note that the review lives on the Mac.

**Checked on the Mac:** `bash -n` on every `.sh`; `python3 -m json.tool pc-setup/claude-settings.json`;
`shasum -a 256 -c pc-setup/SHA256SUMS` (8 OK); `uv lock --check --offline` (lock up to date).
The review gate of `build-emulator.sh` ran in a scratch HOME under `script` (a pty): with no
review, "nope" stopped it and GO reached step 2, which stopped because `~/src/sts2` is missing.
With a synthetic review file it showed the verdict line, and with a wrong path it stopped.
Nothing was built.

**Tests:** `~/.venvs/spireline/bin/python -m pytest -q` -> `66 passed` (65 before, plus the new
prereg test). CI has not run yet: there is no remote.

## 2026-10-10 · Scaffold (Mac, M1 Pro)

**Created** the `spireline` package (Python 3.12, uv, venv `~/.venvs/spireline`): `api.py`
(§2.2 protocols and the §1.4 contract), `infoset/` (schema, allow-list firewall, canaries),
`eval/stats.py`, `eval/seeds.py`, the DRAFT `eval/prereg/phase1.yaml`, tests. Nothing
third-party was built, imported or run; the firewall was written by reading r33hab/STS2MCP @
`5a63f92`. Files are uncommitted; no remote.

**Tests:** `~/.venvs/spireline/bin/python -m pytest` -> `65 passed in 9.53s` (Python 3.12.14, numpy 2.5.3, scipy 1.18.1, pytest 9.1.1).

### Findings from reading the mod (r33hab/STS2MCP @ 5a63f92)

1. **`state_log` carries the current move.** Its last entry is normally the rolled,
   not-yet-executed move (docs/raw-full.md:718-722; built at McpMod.StateExtras.cs:248-258),
   so admitting `state_log` as-is leaks exactly what withholding `move_id` protects. The
   firewall always drops the last entry, deciding from no hidden field. Stunned, dead and
   enemy-turn reads are flagged `state_log_trim_unverified:*` until live captures confirm
   the rule (L6/L8).
2. **The sorted `draw_pile` can leak order.** It is sorted by (rarity, id) with `List.Sort`
   (McpMod.StateBuilder.cs:1733-1737), which is unstable, so ties between same-id cards that
   differ in upgrade or enchantment (Strike vs Strike+) can fall in true draw order. Multisets
   close this; the firewall test permutes both lists and checks the hash is unchanged.
3. **HUD-hidden powers are reported** whenever they have a stack (McpMod.StateBuilder.cs:4214-4220,
   flagged `hidden_in_ui` at 4265-4266). Dropped unless allow-listed.
4. **`run.start_time`** (McpMod.StateBuilder.cs:698-700) is the wall-clock run start, not shown in
   the run. Whether the game derives standard-run seeds from the clock is UNVERIFIED; dropped.
5. **`revive.in_turns`** is computed by walking `FollowUpState` (McpMod.StateBuilder.cs:2669-2686),
   the same edge `move_follow_up_id` exposes. Dropped unless the power is allow-listed
   (candidate: REATTACH_POWER, whose 2-turn rule is fixed).
6. **Draw-pile selection grids** (Seeker Strike, Secret Technique) list cards by screen position
   (McpMod.StateBuilder.cs:3692-3716); ties within the screen's (rarity, name) sort can follow
   draw order. The firewall re-sorts such grids canonically.
7. Doc drift, minor: `ThieveryPower` emits `fields.stolen_gold` (McpMod.StateExtras.cs:482-487),
   absent from the docs table (docs/raw-full.md:437-442). Allow-listed (the player saw the gold go).
8. The emulator's converter requires `move_id`, `state_log` and `ai_fields` on each enemy
   (r33hab/sts2 src/sts2_gym/live/convert.py:455-487). `engine/snapshot.py` must therefore
   fill them from AI particles (design §3.2) before calling it; the firewall never supplies them.

### Statistics checks (spireline/eval/stats.py)

- §7.3 reproduced: 1,094 / 686 / 434 / 293 per arm; McNemar 312 / 469 / 783 / 1,096; TOST
  171 / 343 / 514 / 685; Wilson 71/343 = 16.7-25.3%. The table rounds to the nearest integer;
  the ceilings are 435, 294, 1,097, 172 and 686 for five entries (tests accept both).
- **Discrepancy:** §7.3 "promotion MDE ≈ 0.44 floors" (sigma 6, n 2,000, one-sided alpha 0.01,
  80% power) computes to **0.425**; 0.44 matches none of the obvious variants (two-sided 0.01
  gives 0.458). Not material, but the table should say 0.43.
- **Coverage under optional stopping** (seeded; time-uniform over T steps):
  EB CS 1.000 on paired Bernoulli and paired Beta utilities (P=2,000, T=1,000); betting CS
  0.968 / 0.990 / 0.967 on Bernoulli(0.2) / (0.05) / (0.5) (P=2,000, T=500). The peeking
  fixed-n Wald interval on the same paths covers 0.31-0.56 (positive control).

### Open issue for the design: time-uniform CSs cost far more worlds than §4.3 assumes

§4.3 sizes Stage 2 with fixed-n normal theory, n = (1.96 sigma / h)^2: 35-246 worlds per
survivor for h = 1 L0 point at sigma = 3-8 points. §1.4 requires time-uniform CSs whose only
assumption is the a-priori range of a paired L0 difference, [-1, 1]. Measured worlds to reach
half-width h (`scripts/cs_width_probe.py`, normal differences clipped to [-1, 1], seed 1):

| sigma (L0 pts) | fixed-n, h=1 | betting CS, h=1 | EB CS, h=1 | fixed-n, h=0.5 | betting, h=0.5 | EB, h=0.5 |
|---|---|---|---|---|---|---|
| 3 | 35 | 750 | 2,144 | 138 | 1,611 | 5,023 |
| 5 | 96 | 773 | 2,735 | 384 | 1,761 | > 6,000 |
| 8 | 246 | 852 | 3,670 | 983 | 2,955 | > 6,000 |

The EB CS's linear term k2·c·l(v)/t (c = 2) dominates when sigma is far below the range; the
betting CS is 3-4x cheaper but still 3.5-20x the §4.3 figure. Silver/gold label costs and the
Tier-A night counts in §4.5 would grow by that factor. Options to decide before freezing
`phase1.yaml`: (a) keep CSs for racing/early stopping only, and certify each label with a
pre-planned fixed-n (or group-sequential, alpha-spending) interval; (b) asymptotic CSs
(Waudby-Smith et al., "Time-uniform central limit theory", arXiv:2103.06476), roughly 2-3x
fixed-n width, valid as t grows; (c) accept the cost and cut volumes. Nothing chosen yet.

### Tomorrow (PC setup), what this repo needs

1. Commit here first (left uncommitted on purpose), then move it without a remote:
   `git bundle create spireline.bundle --all`, copy the file, `git clone spireline.bundle` inside WSL2.
2. In WSL2: install uv, `uv venv ~/.venvs/spireline --python 3.12`,
   `uv pip install --python ~/.venvs/spireline/bin/python -e '.[dev]'`, run pytest; expect the
   same summary line.
3. Record CPU/RAM and the WSL2 kernel in `versions.lock` (from the template).
4. `bench/` (separate workstream) has its own README for the day-4 measurements.

## 2026-10-12

Published a scrubbed copy of the third-party security review as `docs/SECURITY_REVIEW.md`, so agents on the PC can read it, and updated the README, DECISIONS (D3), the checklist and `build-emulator.sh` to point to it. It adds a note that on native Windows the offline first build in `pc-setup/WINDOWS.md` section 6 replaces the WSL2 containment.
