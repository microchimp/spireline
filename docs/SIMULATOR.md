# The simulator plan

Goal (D16): **a high-fidelity Slay the Spire 2 simulator with complete coverage**: every
character, act, ascension and piece of content, verified against the game's own code. Ironclad
first, then every character (D15). Search and agent work wait for it.

This file is the current plan. It integrates `DESIGN.md` and `research/IDEAS.md`, which were
written before D15 and D16; where they disagree with this file or `DECISIONS.md`, these win.

## Where things are

| What | Where |
|---|---|
| Simulator (our fork of r33hab/sts2 @ `b745217`) | private repo `microchimp/spireline-sim`; access by request (issue template "Request access to the simulator") |
| Fork rules, upstream policy, fidelity tooling | `FORK.md`, `CLAUDE.md`, `tools/fidelity/` in that repo |
| Security conditions for the fork and the referee | `SECURITY_REVIEW_ADDENDUM_1.md` |
| Upstream watch | `scripts/upstream_watch.py` |

## The referee

The game's own `sts2.dll` (v0.107.1, build 23811903), run headless from a hash-checked copy of
the archived build, with no network and no writes outside its scratch folder. The emulator and
the referee get the same seed and actions; after every action the canonical state
(`tools/fidelity/canon.py`, neutral level) and every RNG stream's call count are compared, and the
first difference is the bug. The referee replaces the sts2-cli fork that `DESIGN.md` §3 planned
as a Phase-3 referee. Its own fidelity to the real client is checked by spot checks against the
live game (addendum H6).

## Gates

Kept from `DESIGN.md` §3.3, widened from "Act 1, Defect" to every character, act and ascension:

| Gate | Pass |
|---|---|
| F1 tape replay | 100% match, per character, act and ascension |
| F2a coverage | ≥ 99% of positions, weighted by how often content appears in real runs (Spire Codex), use only verified content |
| F2b outcome parity | per encounter, |ΔE[HP loss]| ≤ 2 HP and |ΔP(death)| ≤ 3 pp against the referee (backstop to per-action checks) |
| F3 sweeps | multi-seed sweeps of every encounter with 0 open divergences |
| F5 one-step | ≥ 98% exact on deterministic fields, every miss catalogued |
| F8 canaries | crashes, loops, impossible transitions counted, never dropped |
| F9 RNG streams | no cross-stream dependence (α = 0.001) |
| Coverage contract | anything unimplemented, divergent or unverified is marked UNSUPPORTED, never guessed |

`DESIGN.md`'s F4 (map rows) is already met at `b745217` (commit `8be26d2`).

## Coverage checklist (from `research/UPSTREAM.md`, cross-checked 2026-10-13)

- [ ] Whole runs for the Silent, Defect, Necrobinder and Regent (the run engine starts every run as the Ironclad)
- [ ] Monsters: 10 of 121 classes unmodelled; only 14 of 111 verified against the source
- [ ] Acts 2-3: no full-run trace; encounter sweeps on very few seeds; Glory has 15 coverage FAIL rows
- [ ] A10: 2 fight fixtures and 1 run history; the double boss never checked live
- [ ] Card reward pools never checked live; about 10 named approximations
- [ ] Events: reconcile 58 + 8 ancients against 68
- [ ] Enchantments 21 of 22; afflictions and multiplayer not modelled
- [ ] The 18 random-choice enemies consume the AI stream bit-exactly
- [ ] No engine step cap (one run looped for 19 hours)
- [ ] Cards and relics: 296/296 relics in code (upstream's README still says 46 missing); 18 cards invisible to the coverage gate

## Steps

1. **Fork building and testing on the PC** (addendum F3: Claude builds and tests), pushed to the
   private repo once tests pass.
2. **Referee trial** once the addendum's section 3 has GO: list the API from `sts2.dll` metadata
   (no game code runs), classify every test-mode and Godot touchpoint on the rules path as
   cosmetic or rules-affecting (IDEAS fid-3), then generate one A10 map and one card-reward roll
   in both and compare (fid-6).
3. **Coverage measurement**: replay the fidelity corpus on an instrumented emulator build and
   map unexercised branches to cards, relics, monsters and powers (fid-11).
4. **Engine fixes in the fork**: a step cap; copy RNG stream state on clone instead of replaying
   every draw; an allocation-free `ValidActions`; guard `os.nice` and other POSIX-only calls so
   the upstream Python suite runs on Windows; whole runs for the other four characters.
5. **Run-history replay** of the Spire Codex v0.107.1 export (D13): seed plus choices per floor,
   so the emulator must offer what the game offered. 14,448 Ironclad A10 runs first.
6. **Full runs from the game's built-in autoplayer** through the referee (fid-8), and custom-mode
   modifiers as coverage amplifiers (fid-9).
7. **Cheap test sources**: other emulators' bug lists and later patch notes, where the class is
   unchanged in v0.107.1 (fid-14, fid-15).
8. **Speed**, each change checked against recorded traces (golden master).

The owner's own game logs and replays (IDEAS data-1) are a further source once the game is
played on a profile we can read; this PC has none yet.
