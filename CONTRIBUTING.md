# Contributing

Thanks for looking. Spireline is a small research project, so these rules are short and strict.

1. **Tests must pass.** Run `uv sync --locked --extra dev && uv run pytest -q` before you open a
   pull request; CI runs the same. New behaviour comes with a test. Don't loosen an existing
   test to make a change pass.
2. **No game code.** Don't add Slay the Spire 2 code, assets, DLLs, decompiled source or text
   copied from the game. Don't add raw community run data either (aggregates with attribution
   are fine). Third-party projects (the emulator, the mod) stay separate dependencies, pinned
   by commit and never vendored.
3. **No LLM components without a demonstrated benefit.** Spireline has none (D7, D14 in
   `docs/DECISIONS.md`). A proposal to add one needs a new dated decision and a paired,
   pre-registered win on a fresh evaluation block, under the same gates as any other
   component.
4. **Keep the hidden-information rules.** Search, priors, values and features see only an
   `InfoState` built by the firewall (`spireline/infoset/firewall.py`). The firewall is an
   allow-list: a field that is not listed is dropped and logged. Never request `?hidden=1`.
   Don't add anything that lets hidden state (seeds, draw order, enemy `move_id`, AI fields)
   reach an `InfoState`, a log or a decision. Adding a field to an allow-list needs a dated
   entry in `docs/DECISIONS.md` with its evidence, plus a canary test.
5. **Report honestly.** Values carry their units (L0 points are never P(win)). Numbers that
   were not measured are marked UNVERIFIED. Results are at Ascension 10 (D11).
6. **No bots on Daily runs or leaderboards.** Not for testing, not ever.

Keep personal data out of commits: no real names, no email addresses other than a GitHub
noreply address, no local paths with a user name in them, and no machine-specific files
(`versions.lock`, `versions.pc.lock` and `bench/results/` are gitignored for this reason).

By contributing you agree that your contribution is licensed under the MIT licence in `LICENSE`.
