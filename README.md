# Spireline

Spireline tries to certify the best play in Slay the Spire 2 at **Ascension 10** (all ten
modifiers on), **Acts 1-3**, starting with **the Ironclad** and then every character (D15). It is pinned to game
**v0.107.1 (Steam build 23811903)** and uses only what the player can know. "Best" means the
action with the highest estimated value over the player's information set. That value comes
from honest search on the r33hab/sts2 emulator, with hidden information resampled. Each answer
is reported with its unit, a time-uniform confidence sequence, a survivor-scoped regret bound
and a verdict (DECISIVE / CLOSE / UNCERTAIN / UNSUPPORTED). Phase 1 values are combat-local
**L0 points**, never P(win). Learned parts (a Gumbel ExIt prior and a DMC run value) come
later, and only when the ledger calls for them. There are no LLM components and no
end-to-end RL. The decisions so far are in `docs/DECISIONS.md`; the design is `docs/DESIGN.md`, and the
current simulator plan is `docs/SIMULATOR.md`. The simulator itself is a private repository
(`microchimp/spireline-sim`); to get read access, open an issue with the "Request access to the
simulator" template.

**Status (2026-10-13): building the simulator first (D16).** The emulator (r33hab/sts2 @
`b745217`) is built natively on Windows after the security review's GO (D3), its upstream test
suites have run, and the day-4 benchmarks have run (`bench/`). Spireline's simulator is now its
own fork of that emulator, to be refereed by the game's own code run headless. Nothing has been
run against the real game yet. The interfaces, the information-set firewall, canary audits, the
statistics and the DRAFT Phase-1 pre-registration exist and are tested; there is no search code
yet.

## Disclaimer

- Spireline is an **unofficial fan project**. It is **not affiliated with or endorsed by
  Mega Crit**. Slay the Spire 2 and everything in it belong to Mega Crit.
- This repo contains **no game code, no game assets and no decompiled source**.
- Using it with the real game **requires your own copy of Slay the Spire 2**.
- It aims to respect Mega Crit's content policy for fan projects and mods.
- **Never use bots on Daily runs or leaderboards**, this one included. Spireline is for
  analysis and offline research.
- The emulator and the game mod are separate projects with their own licences and terms.
  Spireline neither vendors nor redistributes them.

## Dependencies and credits

- **Emulator:** [r33hab/sts2](https://github.com/r33hab/sts2) (MIT), pinned at
  `b7452170ce1df91de29d3c94acb11d87c7efc708`. It is a separate dependency, not vendored. Its
  lineage is [evangambit/sts2](https://github.com/evangambit/sts2), which builds on Zamiell's
  original emulator. Thanks to all three.
- **Game state bridge:** [STS2MCP](https://github.com/Gennadiyev/STS2MCP) by Gennadiyev, the mod
  whose `GET /api/v1/singleplayer` payload the firewall reads. Spireline pins r33hab's fork,
  [r33hab/STS2MCP](https://github.com/r33hab/STS2MCP) @ `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4`
  (payload schema 4). The firewall was written by reading that code. None of it is copied
  here.
- **Run-layer test corpus:** the public run exports of [Spire Codex](https://spire-codex.com)
  (v0.107.1). Only aggregate numbers appear in this repo, with attribution (D13). Raw runs are
  never committed.
- **Gumbel search ideas:** Google DeepMind's [mctx](https://github.com/google-deepmind/mctx)
  and Danihelka et al., "Policy improvement by planning with Gumbel" (ICLR 2022). They are
  referenced for the planned Gumbel root search. No mctx code is in the repo yet, and any
  port will be attributed in the file.
- **Statistics:** the confidence sequences follow Howard, Ramdas, McAuliffe and Sekhon (2021,
  empirical Bernstein) and Waudby-Smith and Ramdas (betting). Citations are in
  `spireline/eval/stats.py`.
- **Baselines:** [cicero225/STS2FableBot](https://github.com/cicero225/STS2FableBot) (MIT)
  is a comparator. Its published figures are A0 and serve as context only (D11).
- Python dependencies: numpy and scipy, plus pytest for the tests (pinned in `uv.lock`).

## Layout

```
spireline/
  __init__.py          pins (game build, emulator and mod commits) and the target: A10, Acts 1-3, Ironclad first
  api.py               §2.2 protocols (Engine, AiBelief, Prior, RunValue, Searcher), SemAction,
                       Handle, StepResult, Budget, the §1.4 Decision contract, verdict rules,
                       the units ladder and the ε table
  infoset/
    schema.py          InfoState: frozen, hashable, canonical JSON, blake2b info_state_hash, det_seed
    firewall.py        allow-list STS2MCP schema-4 payload -> InfoState, drop log, flags, meta
    canary.py          plant unique tokens in hidden payload fields; audit that none survive
  eval/
    stats.py           Wilson, exact McNemar, paired TOST, cluster bootstrap, EB and betting
                       confidence sequences, sample size / power / MDE
    seeds.py           seed pools (T/E/F/P), seed-block hashes for pre-registration
eval/prereg/phase1.yaml   DRAFT pre-registration (A10 scope, seeds, Tier-A sizes, ε, recall, cost-cut rule)
docs/DECISIONS.md      dated decisions D1-D14
LOG.md                 dated log: findings, measurements, open issues
versions.lock.template what every record's lock hash covers (§3.5); filled copies stay local
scripts/cs_width_probe.py  worlds-to-half-width check behind the LOG.md open issue
tests/                 pytest; fixtures/sts2mcp_payload_example.json is SYNTHETIC
bench/                 day-4 emulator throughput benchmarks for the PC (UNTESTED; see its README)
pc-setup/              Windows + WSL2 setup kit for the always-on PC (start with CHECKLIST.md)
.github/workflows/     CI: the test suite on ubuntu-latest, Python 3.12
CONTRIBUTING.md        the rules for changes
LICENSE                MIT
```

## The firewall in one paragraph

`apply_firewall(payload)` reads a `GET /api/v1/singleplayer` payload from r33hab/STS2MCP @
`5a63f92`. It returns an `InfoState` plus a drop log of `(path, reason, count)`, never values.
Anything not explicitly read is dropped. Piles and the deck become multisets; the hand stays
ordered. Always dropped: every seed, `draw_pile_ordered`, `move_follow_up_id`, the other
`*_ordered` lists, `run.start_time`, and the last `state_log` entry (the pending move). Enemy
`move_id` and `ai_fields`, HUD-hidden powers, `revive.in_turns`, relic raw state and card
dynamic vars each pass only through an allow-list in `FirewallPolicy`, and all of those
lists are empty today. The adapter must never request `?hidden=1`. Tests check two things:
perturbing any hidden value leaves the InfoState hash unchanged, and no canary token reaches
the InfoState, the drop log, flags, meta or log output. Field-by-field citations are in the
module docstring.

## Run the tests

Use a virtual environment. Never install into a base or system Python (Anaconda base
included). With [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/microchimp/spireline && cd spireline
uv sync --locked --extra dev          # exact pins from uv.lock, into ./.venv (gitignored)
uv run pytest -q                      # whole suite, about 10 s
uv run pytest -q -m "not slow"        # skip the coverage simulations
```

The maintainer keeps the environment outside the repo instead:

```bash
uv venv ~/.venvs/spireline --python 3.12
UV_PROJECT_ENVIRONMENT=~/.venvs/spireline uv sync --locked --extra dev
~/.venvs/spireline/bin/python -m pytest -q
```

CI (`.github/workflows/tests.yml`) runs the same suite on every push and pull request.

## Set up a PC

The heavy work (emulator build, batteries, labels) is meant to run on an always-on Windows PC
inside WSL2 Ubuntu, with Claude Code sandboxed there and reachable through Remote Control (D8).
Follow `pc-setup/CHECKLIST.md`, parts A to F, in order. `pc-setup/README.md` explains each file
and the sandbox settings. The kit ships inside this repo, so cloning it (CHECKLIST D0) is
enough to bring the kit over. The security review that gates the emulator build (part E) is
in [docs/SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md). It covers only the pinned commits; review
any other commit yourself before building it.

## Docs

- [docs/DESIGN.md](docs/DESIGN.md): the full design (v1.1), with a note on what has changed since.
- [docs/DECISIONS.md](docs/DECISIONS.md): the decision log; it wins where the design disagrees.
- [docs/SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md): the review of the pinned emulator and mod commits.
- [docs/research/](docs/research/): the landscape critique, the upstream project map, the Spire Codex corpus, enemy AI notes, compute budget, ideas and raw dossiers.
