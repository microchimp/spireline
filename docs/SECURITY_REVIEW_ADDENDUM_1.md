# Security review addendum 1: our fork, and the game's own code as referee

> **Decision (2026-10-13): sections 1 and 3 GO, with the choices in the GO record; section 4 private for now.**
> Sections 1 and 2 extend conditions the review already set.

- **Date:** 2026-10-13, on the Windows PC.
- **Basis:** `docs/SECURITY_REVIEW.md` (the review of r33hab/sts2 @ `b745217` and r33hab/STS2MCP @
  `5a63f92`), decision D16, a file listing of the archived game build, and published notes from
  two projects that already run the game's code headless (favet/divine-sts2, wuhao21/sts2-cli).
  Nothing new was built, installed or run for this addendum.
- **Scope:** (1) building and testing our fork of the emulator, (2) taking upstream changes into
  it, (3) running Mega Crit's `sts2.dll` outside the game client as a fidelity referee,
  (4) publishing that referee harness.

## 1. The fork: builds, tests and credentials

The fork starts at the reviewed `b745217` (tree `7d5c4dfe…`); its base needs no new review.
What changes is that code now changes after the review, and that a GitHub credential arrives.

| # | Condition |
|---|---|
| F1 | Our own commits are reviewed as they are written: no new `PackageReference`, `Exec` task, MSBuild target, network, process, file or P/Invoke use in `src/Sts2Emulator` without a note in the commit message saying why. The library stays pure computation over caller buffers (review E-F01). |
| F2 | Builds and tests of the fork run offline against the NuGet cache already restored and recorded for `b745217` (E7). A commit that needs a new package goes back through E5-E7 first. |
| F3 | Who runs fork builds and tests (review §7.2 options): either the owner runs `offline-build-and-test.ps1` against the fork's working copy, or Claude runs `dotnet build`/`dotnet test` there after the owner approves it once in chat (Option A). Native Windows has no sandbox, so Option A means upstream test code runs with the owner's files readable. |
| F4 | GitHub credential: the narrowest token that works. A fine-grained token limited to the fork (and Spireline, if wanted) with Contents and Pull requests write. If a fine-grained token cannot open PRs on other owners' repos, open those from the browser rather than widening the token. A stored token is readable by everything running as the user (HANDOVER), which includes test code under F3. |
| F5 | The fork's `main` never contains game files, `.pck`, assets or decompiled source. Upstream's `Generated/*.g.cs` and `data/` are already published by upstream; whether a public fork republishing them is acceptable is the owner's call (review §7.1, last row). Until it is decided, the fork is a private repository. |

## 2. Taking upstream changes

| # | Condition |
|---|---|
| U1 | `scripts/upstream_watch.py` only lists changes through the public GitHub API. It fetches no code. |
| U2 | A change is taken only after its full diff has been read, with the review's eyes: E2 scripts, network, process and file access, new dependencies (review §7.1, "re-review before taking any new upstream commit"). |
| U3 | Never merge a whole upstream branch blind. Cherry-pick or re-apply, and name the source as `upstream: <repo>@<sha>` in the commit message. |

## 3. The referee: the game's own code, run headless

**What would run.** The archived build (v0.107.1, Steam build 23811903) ships its game logic as
managed .NET 9 code: `sts2.dll`, with `GodotSharp.dll`, `0Harmony.dll`, the MonoMod libraries,
`Steamworks.NET.dll` with `steam_api64.dll`, `Sentry.dll` with `libsentry` and
`crashpad_handler.exe`, and its own .NET 9.0.7 runtime. This is the code that already runs every
time the game is played, from Steam, and the pristine copy is hash-recorded. The new things are
how it runs (outside the client, patched by our harness, for hours, on every core) and what it
might touch while doing so.

**Where the risk is:**
- **Network.** Sentry crash reporting and Steamworks could reach out if initialised. A crash
  report carries machine details.
- **The owner's saves and settings.** Game code may write to `%APPDATA%\SlayTheSpire2`.
- **A Godot host binary**, if plain .NET is not enough: divine-sts2 found that card effects reach
  logging that calls into Godot natively, and used a headless Godot 4.5.1 host.
- **Harmony patches** that skip presentation code. A fidelity risk more than a security one: a
  skipped method that also draws from a gameplay RNG stream would change results.
- **Decompiling** to learn the game's API. Review condition E15 allows it only after a deliberate
  patch update, with `ilspycmd` 8.2.0.7535, and `decompiled/` never leaves the machine.
- **Terms.** Running the game's code outside the client is a use the owner should be comfortable
  with under Mega Crit's terms and fan-content policy. The README's disclaimer already applies.

| # | Condition |
|---|---|
| H1 | Run only a copy of the archived build, made into the referee's own folder and checked against the archive's `.manifest.sha256` before every session. The archive itself is never written to. |
| H2 | No network for the referee. The harness never initialises Sentry or Steamworks, and every session checks that the referee process opened no network connection. A Windows Firewall outbound block rule for the host executable (and `crashpad_handler.exe`) is the owner's optional second layer, required if a session ever shows a connection. |
| H3 | No writes outside the referee's scratch folder. Saves are in memory, and Godot's `user://` points at the scratch folder. Before the first run, back up `%APPDATA%\SlayTheSpire2` (as review M2), and compare its file list and modification times before and after the first session. |
| H4 | If a Godot host is needed: the official headless .NET build at one pinned version (4.5.1), downloaded only with the owner's approval, from the Godot project's official GitHub releases, checked against the published checksums, sha256 recorded in `versions.pc.lock`. |
| H5 | Learn the API without executing it: read type and method names from `sts2.dll`'s metadata (System.Reflection.Metadata, which runs no game code), plus the class names upstream already cites. Decompile only under E15. |
| H6 | Every Harmony patch is listed in one file with its reason. Skipped methods must be presentation only. The referee's fidelity to the real client is itself checked: the same seed and actions in the live game (through the mod, review M1-M9, on a dedicated profile) and in the referee must give the same RNG call counts and state. |
| H7 | The referee is verification code. Its outputs (traces, states, hashes) feed fidelity checks only; search and agent code never call it. |
| H8 | One referee per OS process, as review E10 sets for the emulator. |

## 4. Publishing the referee harness

| # | Condition |
|---|---|
| P1 | The published harness is our code only: the host, the Harmony patch list (method names, not bodies), the comparison layer and docs. No game files, assets, decompiled source or text from the game (`CONTRIBUTING.md` rule 2, review R1). |
| P2 | It runs only on the user's own copy of the game and refuses a build whose `sts2.dll` sha256 it does not know. |
| P3 | Its README carries the same disclaimer as Spireline's: unofficial, not affiliated with or endorsed by Mega Crit, never for Daily runs or leaderboards. |

## GO record

| Item | Decision | Date | By |
|---|---|---|---|
| Section 1 (fork builds: who runs them, F3) | GO: Claude builds and tests the fork (Option A), offline from the recorded package cache | 2026-10-13 | owner, in chat |
| Section 1 (repository visibility, F5) | Private repository `microchimp/spireline-sim`; read access on request (issue template), and for upstream (r33hab) | 2026-10-13 | owner, in chat |
| Section 3 (referee, stages H1-H8) | GO, with these choices: (1) run the archived game's code headless for checking only; (2) download the official headless Godot .NET build rather than stubbing Godot, so as little as possible is faked (H4); (3) decompile `sts2.dll` locally with the pinned `ilspycmd` 8.2.0.7535, output never leaves the PC, which amends E15's "only after a patch update" for v0.107.1 (H5); (4) no firewall rule for now: the harness never initialises Sentry or Steamworks, and each session checks the referee opened no network connection (H2) | 2026-10-13 | owner, in chat |
| Section 4 (publishing the harness) | Private for now: the harness lives in the private simulator repo; publishing waits | 2026-10-13 | owner, in chat |
