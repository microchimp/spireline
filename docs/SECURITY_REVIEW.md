# Spireline security review: emulator and mod

> **About this copy (2026-10-12).** This is the public version of the review that decision D3 requires before any third-party code is built or run. It covers r33hab/sts2 @ `b7452170ce1df91de29d3c94acb11d87c7efc708` (tree `7d5c4dfe31fa5d5e6f27c3adc8100ece50090fe4`) and r33hab/STS2MCP @ `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4` (tree `86f940c69836adeb553ba77db769bcf48a3d717f`), plus their provenance. It was a static read on 2026-10-10: nothing third-party was built, installed, imported or executed. Personal details were removed for publication. Findings, severities and conditions are as reviewed, except that condition R1 and the LIC-1 action now reflect that the Spireline repo is public.
>
> The review was written for a WSL2 setup. On native Windows, the offline first build in `pc-setup/WINDOWS.md` section 6 (fetch online, disconnect, build and test, reconnect) replaces the containment in §7.2 and condition E8. Without a sandbox it cannot hide files from the build, so keep credentials off the PC as that section says. Read Linux paths, `linux-x64` and `Sts2Emulator.so` as their Windows equivalents: the work folder in `WINDOWS.md`, `win-x64` and `out\Sts2Emulator.dll`. Kit statuses in §4 and §7.2 describe the WSL2 kit as it was on 2026-10-10.
>
> These findings have not been reported upstream yet. Anyone may open issues on the respective repos.

VERDICT: GO WITH CONDITIONS — build and run the r33hab/sts2 emulator @ b745217 inside WSL2 on the PC. The C# library is pure computation over caller-supplied buffers. Every risk found is in upstream setup, sync and agent scripts or in how the library is used (threads, oracle exports), and conditions E1-E16 contain them.

VERDICT (mod): GO WITH CONDITIONS — install r33hab/STS2MCP @ 5a63f92 into Slay the Spire 2 once live work starts (setup day does not need it). You build it from source, after a full save backup, on its own profile slot, with both gates off, and Spireline's client and firewall are its only caller (conditions M1-M9).

- **Date:** 2026-10-10, on a Mac, before the PC setup.
- **Basis:** four static reviews (emulator C#, Python layer, mod, provenance), plus a re-read of the load-bearing citations the same day. Nothing third-party was built, installed, imported or executed.
- **Gate:** this file is the go record that decision D3 requires before any third-party code is built or run. It replaces the "this is not a security review" note in design v1.1 §3.6.

**The short version:**

- **Use our own setup.** Use `pc-setup/` (our own kit), never the upstream `scripts/desktop_setup.sh` or its fight/night/sync jobs. Never run `scripts/ralph/ralph.sh`.
- **Contain the first build.** Run the first build and both test suites offline, with secrets and `/mnt/c` hidden (§7.2). The WSL2 kit runs them in your own terminal, with network, outside the sandbox. On native Windows, see the note at the top.
- **Keep secrets off the box.** No Mac Remote Login. No SSH key from the PC to the Mac. No GitHub token on the PC until the first build and tests are done.
- **One emulator per process.** Run each emulator instance in its own OS process. Search code reaches the library only through an allow-list wrapper that forces `resample_hidden=1`.
- **Mod comes later.** The first build does not need it. When it is needed: back up the saves, use a dedicated profile slot, keep `allow_hidden_state` and `allow_debug_actions` false, and put the firewall in front of it.

---

## 1. Verdicts and reasons

### 1.1 Emulator (r33hab/sts2 @ b745217, built and run in WSL2 Ubuntu): GO WITH CONDITIONS

**What is clean:**
- The emulator library (`src/Sts2Emulator`, 48 .cs files) has no networking, process spawning, file, environment or registry access, dynamic assembly loading, P/Invoke or runtime code generation (E-F01).
- The build is a plain `dotnet publish`. The main csproj has no `Exec` task, custom target or `PackageReference` (E-F08).
- All 1592 tracked files are text. There are no committed binaries, opaque blobs or live git hooks (E-F18).
- The Python layer has 0 `shell=True` calls, safe deserialization (`weights_only=True`, `allow_pickle=False`), and no network code except urllib to the mod on localhost (PY-11, PY-12, PY-13).
- `uv.lock` resolves 61 packages, all from PyPI and all sha256-pinned (PY-15).

**Where the risk is:**
- **Upstream ops scripts.**
  - `desktop_setup.sh` pipes installers into a shell and creates SSH trust from the PC to the Mac.
  - The fight and night jobs run rsync loops to the Mac.
  - `ralph.sh` runs coding agents with every permission check skipped.
- **Live-game scripts.** These abandon runs and write into the Steam saves folder.
- **Library use.** The library is not thread-safe, and a bad handle aborts the host process.
- **Honest search.** Oracle and debug exports exist, and a resampled run clone still carries the true future encounters, events and relic order (E-F05). That leak does not touch combat-local phase 1.

**What would change this to NO-GO:**
- `clone-pinned.sh` reports a commit or tree mismatch.
- Restore fetches anything other than Microsoft's .NET packages (ILCompiler, runtime packs, plus Test.Sdk and xunit for the tests), or fetches from anywhere other than nuget.org.
- A "before build" condition in §4 can't be met.

In any of those cases the design's fallback applies (§3.6 step 5: evangambit/sts2 plus cicero225/STS2MCP with our own converter).

### 1.2 Mod (r33hab/STS2MCP @ 5a63f92, installed into the game): GO WITH CONDITIONS

**What is clean:**
- **Listener:** it binds `localhost` and `127.0.0.1` only (M-F9).
- **Authentication** (M-F10):
  - It requires a 256-bit token, compared in constant time.
  - It rejects any request with an `Origin` header with 403.
  - It sends no CORS headers and accepts POST only with a JSON body.
- **No outbound activity.** It never starts a process and makes no outbound network call. Its only file write is its own conf (M-F11, M-F15).
- **Gates.** The hidden-state gate and the debug-action gate are built correctly (M-F7, M-F13).
- **Hardening.** Upstream Gennadiyev/STS2MCP `55e0648` has no authentication and sends `Access-Control-Allow-Origin: *`. This fork adds the token check and drops that header.

**Where the risk is:**
- `POST /api/v1/profiles` with `delete` wipes a save slot, and it is not gated (M-F8).
- `GET` has side effects: it opens treasure chests and the shop inventory (M-F12).
- Run-ending menu actions are not gated (M-F13).
- The default payload leaks hidden information. These leaks are inputs to the firewall (§6).

**Containment:**
- The mod runs inside the game process, natively on Windows, with your privileges. No sandbox applies.
- The controls are therefore the static review, building from the pinned source, and the localhost-plus-token listener.

---

## 2. What was reviewed, how, and at which commits

| Review | Repository @ commit (tree) | Files examined | Surface |
|---|---|---|---|
| emulator-native | r33hab/sts2 `b7452170ce1df91de29d3c94acb11d87c7efc708` (tree `7d5c4dfe31fa5d5e6f27c3adc8100ece50090fe4`), branch `spire-coach` | 530 | `src/Sts2Emulator` (Core, Generated, Interop), `src/Sts2Emulator.Tests`, both csproj, `ILLink.Roots.xml`, `.config/dotnet-tools.json`, all 9 shell scripts, `lint-and-test.sh`, `package.json`/`bun.lock`, `pyproject.toml`, CI, git hooks and config, every tracked file checked for binaries. Spot checks: `src/sts2_gym/native.py`, model loading in `rl/`. |
| python-layer | same commit | 177 | `src/sts2_gym` (incl. `live/`), `rl/` (incl. `prior_loop/`, `run_train/`), `scripts/*.py`, `tests/python`, `pyproject.toml`, `uv.lock`, and the shell and agent files beside them. |
| mod | r33hab/STS2MCP `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4` (tree `86f940c69836adeb553ba77db769bcf48a3d717f`), branch `spire-coach` | 34 | All C# (listener, routing, auth, config, state builder, actions, debug, profile, compendium, Harmony patches), csproj, `build.ps1`, manifest, `FORK_NOTES.md`, `.claude/`, `AGENTS.md`, `mcp/server.py`. Tree-diffed against Gennadiyev/STS2MCP main `55e0648`. |
| provenance | lineage Zamiell/slay-the-spire-2-emulator `04cfe6d` → evangambit/sts2 `aa4b0d8`..`37e4264` → r33hab/sts2 `b745217` | 40, plus git objects and GitHub metadata | Full-history clones of evangambit and Zamiell; the r33hab clone unshallowed with all 25 branches; pairwise tree, metadata and signature comparison; tree diff of r33hab against evangambit's head; licence blobs; PyPI hash checks; `gh api` metadata. |

**Method (all four).** Read only.
- Each reviewer swept for its risk classes: network, process spawn, file and environment I/O, reflection and dynamic loading, native interop, deserialization, secrets, build hooks and agent configs.
- Each reviewer then read every hit in context.
- Clones were shallow single-commit checkouts, plus full-history local review clones.
- Nothing was built, installed, imported or executed.

**Re-check (2026-10-10).** The adversarial verification pass returned no results for any of the four reviews (every `verifications` list is empty). So no finding is marked refuted, and every severity is the reviewer's own. To compensate, the load-bearing citations were re-read in the pinned clones; those findings are marked ✓ in §3. These were also recomputed:
- **Commits and trees:**
  - Emulator: `b7452170…`, tree `7d5c4dfe…`. The clone is shallow: one commit, dated 2026-10-05 17:26:44 UTC.
  - Mod: `5a63f924…`, tree `86f940c6…`.
- **evangambit's head:** evangambit `main` has tree `0c70a122143e…`, the same tree as r33hab `main` `cd93393`.
- **The r33hab range:** `cd93393..b745217` is 263 commits: 326 files, +109,124/−1,566.
- **Signature:** the evangambit PR #1 merge `e9efc57` carries a `gpgsig` header; its r33hab twin `7790e1f` has none.
- **Wheels:** every package in `uv.lock` has a CPython 3.12 / abi3 / pure-Python wheel for Linux x86_64. So `uv sync --no-build` is possible, and no sdist needs to be built (no install-time code).

**Not covered:**
- The r33hab/spire-coach repository (§8).
- The cicero225/STS2MCP fork, which design §3.6 step 1 asked to diff against.
- The intermediate evangambit/STS2MCP history: the mod clone is a single shallow commit, so only its tree diff against Gennadiyev is known.
- The game itself.

---

## 3. Findings

**How to read this:**
- **Severity** is the reviewer's own (no verifier output exists; see §2).
- **✓** means the cited lines were re-read on 2026-10-10 and say what the finding says.
- **IDs:**
  - `E-` emulator-native.
  - `PY-` python-layer.
  - `M-` mod.
  - `PROV-`, `LIC-`, `BUILD-`, `NET-`, `FFI-`, `AGENT-`, `DEP-`, `PROC-`, `DESER-` provenance.
- Duplicates across reviews are merged into one row that lists every ID.
- Paths are relative to each repo root. Mod files are `McpMod.<name>.cs` in the STS2MCP root.

No critical or high findings.

### 3.1 Medium

| ID | File:line | What | Why it matters | Action |
|---|---|---|---|---|
| E-F05 ✓ | `src/Sts2Emulator/Core/StateCloning.cs:439-451, 501-502`; `src/Sts2Emulator/Core/Run/RunEngine.cs:913-955` | `RunState.Clone` copies every act's `NormalEncounters`, `EliteEncounters` and `Events` arrays and both relic bags verbatim, even under a new seed. `ResampleHiddenState` only resamples the Crystal Sphere, the combat RNG streams and the unseen middle of the draw pile. | A run-level search over `Sts2Run_Clone(resample=1)` foresees the next hallway fight, elite, event and relic. Combat-local phase 1 is unaffected. | Before any run-level search, resample the unvisited sequence suffixes and the unpulled bag order under the game's constraints. Add a test that two resampled clones diverge on the next encounter and relic. Record it in the design doc as a known leak. |
| E-F04 ✓ | `Core/CombatFactory.cs:12, 16, 25, 386-396`; `Interop/NativeExports.cs:417, 594`; `Interop/RunNativeExports.cs:26` | Static mutable state with no locks: both 256-slot handle pools, `_lastLoadError`, `_currentNicheHpRng`, `_usedNicheHps`, `_currentAscension`. `ctypes.CDLL` releases the GIL (`native.py:180`). | Threads can share a pool slot or silently corrupt enemy HP rolls and determinism. | One emulator per OS process (spawn pool). Never call the library from threads. Add a determinism regression test. |
| E-F11, PY-03, BUILD-1 ✓ | `scripts/desktop_setup.sh:14, 43, 49-51, 61, 65-74, 83-89` | Upstream WSL2 bootstrap. It runs `sudo apt-get` (43). It creates a passphrase-less ed25519 key and runs `ssh-copy-id` to the Mac (49-51), which needs Mac Remote Login. It clones from the Mac (14, 61). It pipes `astral.sh/uv/install.sh` and `dot.net/v1/dotnet-install.sh` (channel 9.0, unpinned) from curl into a shell (67, 69). It appends to the rc file (70-74). It runs `uv run`, syncing torch and SB3, and then the test suite (83-89). | It is the obvious script to run on setup day, and it would give the always-on PC a standing shell on the Mac. | Do not run it. Use `pc-setup/wsl-bootstrap.sh`. Create no SSH trust from the PC to the Mac. |
| E-F12, NET-1 ✓ | `scripts/desktop_fight_job.sh:36-46, 84-100`; `scripts/night_train.sh:48-53, 65-74, 105-116`; `scripts/fight_loop_rounds.sh:14-19` | tmux and nohup loops rsync shards and results with `$MAC` every 300 s. `night_train.sh:68` pulls the Mac's priors with `rsync --delete` into `runs/prior/` and trains from them. `night_train.sh:107` runs `caffeinate`. NET-1 rated this low because `$MAC` defaults to a placeholder. | These need the SSH trust from E-F11, and a pulled file becomes training input with no check. | Don't adopt them. Spireline has its own job runner on the PC. Results move by a pull that you start. |
| E-F13, PY-04 ✓ | `scripts/ralph/ralph.sh:8-9, 133-140` | An agent loop with no iteration limit by default. Each pass runs `amp --dangerously-allow-all`, `copilot --allow-all-tools` (the default) or `claude --dangerously-skip-permissions --print`. | On a box with Claude Code installed, one run gives an agent unprompted control. It also contradicts D7 (no LLM components). | Never run it, and never vendor `scripts/ralph/`. The PC settings disable bypass mode, which neutralises the `claude` branch. Add a deny rule as well (condition E2). |
| PY-01 ✓ | `scripts/capture_sweep.py:142-147, 179, 207-230`; `scripts/start_real_game_run.py:295-345`; `scripts/capture_card.py:118, 129, 141, 153, 238`; `scripts/trace_real_game_run.py:854-862` | The live-game capture scripts do several things to the real game and profile:<br>- write `current_run.save.backup` into the Steam saves folder;<br>- save-and-quit, then abandon the current run;<br>- send `debug_*` cheat commands;<br>- launch the game;<br>- run `pkill -9 -if "slay the spire 2"` (179). | They would destroy a real run and modify the real profile. Their paths are macOS-only, so they stay inert on WSL2 unless someone adapts them. | Never run them against your real profile. If live ground truth is needed, write our own capture code, on a separate profile, after a save backup. |
| PY-02 ✓ | `scripts/fidelity_replay.py:62-70`; `tests/python/test_live_sessionlog.py:164-187` | Puts `$SPIRE_COACH_REPO` or `~/Documents/git/spire-coach` at `sys.path[0]` and imports `coach.snapshot`. The standard `unittest discover` run loads the script through `exec_module`. | Any code at that path runs during the upstream test suite and shadows module names. It is inert while the path is absent (the test then skips). | Keep `SPIRE_COACH_REPO` unset and make sure the path is absent on the PC. Check both before every upstream test run (E9). |
| M-F1 ✓ | `McpMod.StateExtras.cs:219-239, 248-258` | The default payload carries each enemy's `move_id` and `state_log`. Only `move_follow_up_id` is behind the gate. | `move_id` plus the emulator's static move graph reveals wired follow-up moves. `state_log` can list moves that were rolled and then replaced before the player saw them. | The firewall strips `move_id` (allow-list per monster, on L8 evidence only) and keeps our own log of observed intents (§6). |
| M-F2 ✓ | `McpMod.StateExtras.cs:239, 316-338` | `ai_fields` dumps every int, bool, enum and string field and property declared by the concrete monster class, private ones included, keeping defaults. Property getters run on every GET. | A pre-rolled choice or hidden counter stored in a plain field leaks, and a getter with side effects runs on every poll. | Default-deny. Admit fields per monster and key, on L7 evidence. |
| M-F3 ✓ | `McpMod.StateBuilder.cs:1733-1737` (uid at 2242) | `draw_pile` is sorted by (rarity, id) with `List<T>.Sort`. For partitions of 16 or fewer, .NET introsort uses insertion sort, which is stable, so tied cards keep their true draw order. Each entry also carries a stable uid. | In a pile of 16 or fewer cards, the exact relative order of, for example, the one upgraded Strike among the Strikes is readable. | Reduce to a multiset keyed by card identity, with no order and no uids. |
| M-F8 ✓ | `McpMod.Profile.cs:183-194`; routing `McpMod.cs:421-429` | `POST /api/v1/profiles {"action":"delete"}` calls `SaveManager.DeleteProfile` on any non-active profile 1-3. It is not behind `allow_debug_actions`. `switch` (143-181) changes the active profile. Upstream has the same delete. | Anyone holding the token can wipe a save slot. | The client never calls `/api/v1/profiles`. Back up `%AppData%\SlayTheSpire2` first. Spireline runs on its own profile slot. |
| LIC-1, PY-18 ✓ | Zamiell repo `decompiled/**` (3418 files); r33hab `.gitignore:11-13`; `scripts/extract_data.py:2, 11-14`; `src/Sts2Emulator/Generated/*.g.cs:1` | Zamiell's repo contains a `decompiled/` directory of decompiled MegaCrit game code. evangambit's history starts without it (`aa4b0d8`). r33hab's committed `Generated/` and `data/` are generated from a local decompile. | This is a redistribution question, not a code-safety risk. It matters for anything Spireline publishes. | Never vendor from Zamiell's repo. Delete the local review clone of it. Publish nothing from `Generated/`, `data/` or `decompiled/`. Keep `decompiled/` ignored everywhere. |

### 3.2 Low

| ID | File:line | What | Why it matters | Action |
|---|---|---|---|---|
| E-F02 ✓ | `Interop/NativeExports.cs:698, 706, 722, 743, 781, 800, 828, 849, 868, 877, 891, 907, 951, 1031, 1048, 1059, 1065, 1071, 1077, 1126, 1139, 1170, 1184, 1212`; `Core/CombatFactory.cs:1081` | 24 combat exports index `_pool[handle]!` unchecked. An unknown encounter id throws `ArgumentOutOfRangeException`. Under NativeAOT, an exception in an `[UnmanagedCallersOnly]` method fail-fasts the host process. | A bad value kills the worker process. Memory is not corrupted, because the code is managed and bounds-checked. | Validate the handle (0..255, live) and the ids in our wrapper. Run workers in subprocesses. |
| E-F03 | `Interop/NativeExports.cs:984-993, 1075-1090, 1124-1149, 1168-1207, 1420-1423`; `Interop/RunNativeExports.cs:119, 153, 179, 217, 228, 239, 255` | Raw-pointer writes trust the caller's buffer size. Capacity counts items, not ints: 3 ints per enemy, 2 per relic or pile entry. The existing Python sizes these correctly (`native.py:1150-1190`). | An undersized buffer in a new binding corrupts the Python heap. | Query `Sts2_ObsSize`, `Sts2Run_ObsSize` and `Sts2Run_InfoSize` at load time. Allocate stride × capacity. Add a binding test with sentinel guards. |
| E-F06 ✓ | `Interop/NativeExports.cs:515-591, 792-804, 846-872, 1181-1207`; `Interop/RunNativeExports.cs:93-125, 276-280, 389-537` | Oracle and debug exports:<br>- clones with `resampleHidden=0`;<br>- `Sts2_GetPile(0)`, the true draw order;<br>- `Sts2Run_GetStateList` 11-13, the future normal, elite and event sequences;<br>- `Sts2_RngCallCount`;<br>- `Debug*` mutators. | Low as a security issue, but central to honest search: one call from search code invalidates its labels. | Allow-list wrapper (E12, §6.2). |
| E-F09 ✓ | `scripts/build.sh:14-18` | The `uname -sm` switch has no `Linux aarch64` case, so any unknown host falls through to `win-x64`. | Irrelevant on the x86_64 PC; a trap on ARM. | Always pass the RID. The kit does: `RID=linux-x64`. |
| E-F10 ✓ | `scripts/build.sh:1-31`; `lint-and-test.sh:1-71`; `scripts/desktop_setup.sh:65, 72` | .NET CLI telemetry is on by default. Only `desktop_setup.sh` opts out. | Sends usage data to Microsoft, which this setup avoids. | Set `DOTNET_CLI_TELEMETRY_OPTOUT=1` and `DOTNET_NOLOGO=1` (E6). |
| E-F14 ✓ | `lint-and-test.sh:10-11, 23-24, 35-65, 47` | Hardcoded `/mnt/c/Users/<user>/...` paths. Publishes `win-x64`, which fails under WSL. Runs csharpier and many repo Python scripts. `audit_powers.py` needs the decompile. | Fails on WSL, and runs far more code than needed. | Don't run it. Use `build.sh linux-x64` plus `dotnet test`. |
| E-F17 | `scripts/decompile.sh:5, 10-30, 44-55`; `scripts/patch_update.sh:7-29` | Needed only after a game patch. The Steam path is the Git-Bash form, wrong under WSL (15). It runs `ilspycmd`, which is not in the tools manifest (53). It calls bare `python`, which resolves to whatever Python is first on `PATH` (10, 13, 25, 29). | Breaks the venv rule, and runs a third-party tool on the game DLL. | Skip while on 0.107.1 (E15). |
| E-F21 ✓ | `Core/CombatFactory.cs:165`; `Core/Effects/RelicEffects.cs:2879` | Two fallbacks use OS-seeded `new Random()`. Native entry points pass seeded streams, so these should not trigger. | If either is hit, results stop being reproducible. | Determinism regression test (E11). |
| E-F23, PY-05, FFI-2 ✓ | `src/sts2_gym/native.py:11-15, 149-164, 167-186` | The loader passes `$STS2_LIB_PATH/Sts2Emulator.so`, then `<repo>/out/`, to `ctypes.CDLL`, with no hash check. `STS2_ALLOW_STALE_NATIVE=1` skips the freshness check. The macOS-only `sigaction` workaround does not apply on Linux. | Whoever controls that variable chooses the native code loaded into the process. | Never set `STS2_LIB_PATH` or `STS2_ALLOW_STALE_NATIVE`. Spireline loads the library by absolute path and checks its sha256 from `versions.lock`. |
| PY-06 ✓ | `rl/run_train/policy.py:67-68`; `rl/run_train/cli.py:263, 294-303`; `rl/run_train/loop.py:404-414`; `rl/prior_loop/loop.py:73-81, 1515-1519`; `rl/prior_loop/cli.py:47-53, 151`; `rl/prior_loop/real_fights.py:40`; `scripts/deck_benchmark.py:230` | Both training loops export promoted models to `~/Documents/git/spire-coach/data/models/...` by default. Several readers default to `~/Documents/git/sts2-wt/...`. | Writes outside the tree. Inside the sandbox they fail; outside it they land in a spire-coach path. | Use `--no-export` or an in-tree `--export-dir`, and set `export_dest` (E14). |
| PY-07 ✓ | `rl/run_train/cli.py:166-178, 236-240` | `stop` sends SIGTERM to whatever pid is in `loop.pid` if that pid is alive. | After a crash or a Windows Update reboot, the pid can belong to an unrelated process. | Check the pid's command line first, or supervise the loop. |
| PY-08 ✓ | `scripts/card_pair.py:16`; `scripts/relic_pair.py:26` | `sys.path.insert(0, "scripts")`, relative to the working directory. | What they import depends on where they are run from. | Not needed; don't run them. |
| PY-09, DEP-1 | `uv.lock` (`rpds-py` entry); `pyproject.toml:16` | `rpds-py 2026.6.3` uses CalVer and was published after the reviewer's knowledge. Its sdist sha256 matches PyPI's JSON API (DEP-1). It is pulled in by `jsonschema`, a dev dependency, and 6 upstream test files reference `jsonschema`. | Publisher legitimacy is unconfirmed. Dropping the dev group would break those tests. | Confirm the publisher on pypi.org and run an OSV check before the first sync (E9). |
| PY-10 | `rl/train.py:11-14, 81` | stable-baselines3 and sb3-contrib are used only by a legacy trainer. SB3 zips are cloudpickle. | Loading a foreign SB3 zip runs code. SB3 pulls in about 13 extra packages. | Never load SB3 zips. Drop SB3 from Spireline's own lock. |
| M-F4 ✓ | `McpMod.StateBuilder.cs:4217-4220, 4253-4266` | Powers that the HUD hides are reported, marked `hidden_in_ui`, whenever their amount is non-zero. | They may encode hidden countdowns or flags. | Strip them (§6). |
| M-F5 | `McpMod.StateBuilder.cs:2527-2532, 2606-2613, 2669-2686` | `revive.in_turns` is computed by walking `NextMove.FollowUpState` up to 4 steps. | That is the same move graph `move_follow_up_id` hides. | Strip it (§6). |
| M-F6 ✓ | `McpMod.StateBuilder.cs:539, 766-767, 1340-1341`; `McpMod.Compendium.cs:286, 333, 387`; `McpMod.Profile.cs:115-116` | Seeds appear outside the gate: `game_over.seed`, `seed_input`, `lobby.seed` and `run_history[].seed`. `/compendium` and `/profiles` return absolute save paths, which include the Windows username and SteamID64. | Seed knowledge breaks honest replay and common-random-number evaluation (CRN). The paths are personal data. | Run setup in a separate process (M6). The firewall drops seeds (§6). The client denies those endpoints (M4). |
| M-F11 | `McpMod.Config.cs:192-221, 228-242` | On Windows, `STS2_MCP.conf` (which holds the token) is written with plain `File.WriteAllText`, so it inherits the folder's ACL. | Any local process can read the token. That includes all of WSL through `/mnt/c`, since the conf sits under the Steam folder, not `/mnt/c/Users`. | Acceptable on a single-user PC. Optionally tighten the ACL by hand. |
| M-F12 ✓ | `McpMod.StateBuilder.cs:633-637, 2800-2811, 4150-4156` | GET opens the shop inventory, and `ForceClick`s the Fake Merchant and the treasure chest. | A polling client takes game actions it didn't choose. | Log every GET as an action, and check parity after polls on those screens (M9). |
| M-F13 ✓ | `McpMod.Actions.cs:103-130, 2211-2226, 2337-2375`; `McpMod.cs:935-939`; `McpMod.Debug.cs:32-175`; `mod_manifest.json:9` | `debug_*` actions are refused unless `allow_debug_actions` is on. These are not gated: `return_to_main_menu`, and `menu_select` quit, abandon_run, give_up and popup yes. The manifest says `affects_gameplay: false`. | Any token holder can end a run. What the manifest flag means for progress is unknown. | Keep `allow_debug_actions` false (M3). The agent may send in-run gameplay actions only (M4). |
| M-F16 ✓ | `mcp/server.py:17-77, 1316-1329`; `.claude/settings.local.json:43-46` | `mcp/server.py` is an LLM bridge. It sends no token, so it gets 401 from this build, and it honours proxy variables. The repo's `.claude/settings.local.json` pre-approves 37 tools and sets `enableAllProjectMcpServers: true`. | Starting Claude Code in the mod checkout would auto-enable any `.mcp.json` in it. This also conflicts with D7. | Never run `mcp/`. Never start Claude Code with the mod checkout as the working directory (M8). |
| PROV-1 ✓ | git history: evangambit `e9efc57` vs r33hab `7790e1f` | 194 evangambit commits have new SHAs, but identical trees, authors, dates and messages. The only change is the GitHub PGP signature dropped from the PR #1 merge. | The history was rewritten without changing content. The review range is `cd93393..b745217` (Appendix A). | Pin both SHA and tree. `clone-pinned.sh` does. |
| LIC-2 ✓ | `LICENSE:3` | All three repos carry a byte-identical MIT LICENSE (blob `922bb37`). Its copyright line is the template "The Complete Contributors". | MIT is met as long as the notice is kept. | Keep the LICENSE verbatim, and add a NOTICE with the lineage SHAs (R1). |
| AGENT-1, E-F15 ✓ | `AGENTS.md:5-8`; `package.json:13-15`; `bun.lock:1-15` | AGENTS.md tells agents to run `bunx --bun prettier`, `uv run black` and `bash lint-and-test.sh`. `package.json` exists only for prettier. | An agent in the checkout could download and run npm code, or the full lint script. | Treat upstream agent docs as data. Spireline's own CLAUDE.md states the rules (R3). |
| FFI-1 | `Interop/NativeExports.cs:609-648, 661-672, 683-689, 984-987`; `Interop/CombatSnapshot.cs:77, 95-98` | r33hab added 11 exports, including `Sts2_LoadCombatSnapshot` (JsonDocument parser, catches all exceptions), `Sts2Run_DebugSetPlayer` and `Sts2Run_DebugResolveCombat`. | The Debug exports are mutators and oracle surfaces. | Feed snapshots only from our converter. The Debug exports are test-only (E12). |
| BUILD-2 | `scripts/build.sh:5-9, 24-28`; `scripts/decompile.sh:53`; `.github/workflows/ci.yml:15-31` | There is no `global.json`, `packages.lock.json` or `nuget.config`, so the SDK and ILCompiler versions float. r33hab/sts2 shows no CI runs, and 193 of evangambit/sts2's 197 runs show as failed. | No CI result vouches for either tree. | Install one exact SDK version and record the restored package hashes (E4, E7). |

### 3.3 Info (clean results, recorded so they are not re-checked)

| ID | File:line | Result |
|---|---|---|
| E-F01 | `src/Sts2Emulator` (48 .cs) | 0 hits for networking, process, file, environment, registry, `Assembly.Load*`, `DllImport`, `LibraryImport`, `NativeLibrary`, `Marshal.`, `Emit` or `DynamicMethod`. The only `Unsafe` use is `CombatSnapshot.cs:973` (`Unsafe.As<int,TEnum>`), guarded by `Enum.IsDefined`. `ImplicitUsings` (`Sts2Emulator.csproj:10`) puts `System.Net.Http` in scope, but nothing uses it. |
| E-F07 | `Interop/CombatSnapshot.cs:77, 95-109, 397, 495, 973-976, 1085`; `Interop/NativeExports.cs:612-647` | The snapshot loader:<br>- uses `JsonDocument` only;<br>- refuses unknown fields;<br>- caps the hand and enemies;<br>- catches all exceptions.<br>It has no byte cap, so the caller caps the input size. |
| E-F08 ✓ | `scripts/build.sh:7-9, 14-28`; `Sts2Emulator.csproj:7, 8, 10` | `PublishAot` and `InvariantGlobalization` are set. No `Exec` task and no `PackageReference`. Needs clang and zlib1g-dev. The output is `out/Sts2Emulator.so`. |
| E-F16 | `src/Sts2Emulator.Tests/Sts2Emulator.Tests.csproj:13-15` | The test packages are pinned: Microsoft.NET.Test.Sdk 17.10.0, xunit 2.9.0, xunit.runner.visualstudio 2.8.2. There is no lock file for transitive versions. |
| E-F18 | repository | 1592 tracked files, all us-ascii or utf-8 text. No base64 or hex blobs, no bidi characters, hooks are `*.sample` only, no submodules. |
| E-F19 ✓ | `.github/workflows/ci.yml:5-31` | CI runs on GitHub only, with `permissions: contents: read`. |
| E-F20 | `src/Sts2Emulator.Tests/Support/StepCostProbe.cs:27, 60, 116` | The only C# file write is a skipped performance probe to `/tmp`. |
| E-F22 ✓ | `Interop/NativeExports.cs:417`; `Interop/RunNativeExports.cs:26` | 256 handles per pool. `Create` and `Clone` return −1 or −2 when the pool is full, and only `Destroy` frees a handle. |
| PY-11, PROC-1 ✓ | multiple (`rl/run_train/cli.py:200-207`; `rl/prior_loop/loop.py:180`; `src/sts2_gym/live/service.py:821-826, 857`) | 0 `shell=True`, no `os.system` or `os.popen`; every subprocess call uses list argv. multiprocessing always uses `spawn` with pipes. `service.py` puts `rl/` first on `sys.path`, so keep the checkout read-only to the runtime. |
| PY-12, NET-2 | `scripts/start_real_game_run.py:11-38`; `scripts/trace_real_game.py:10-27`; `rl/fight_viewer.template.html:2` | The only HTTP code is urllib to `localhost:15526`. The engine service speaks JSON lines over stdin and stdout. The fight-viewer HTML loads Google Fonts; strip that link if the viewer is ever used. |
| PY-13, DESER-1 ✓ | `rl/combat_prior.py:151`; `rl/run_train/models.py:494, 653`; `rl/live_search.py:1663` | Every `torch.load` passes `weights_only=True`. `np.load` passes `allow_pickle=False` or relies on numpy's default, which is also False. `pickle.loads` only round-trips the process's own bytes. |
| PY-14 | `scripts/game_version.py:23-26` and others | Nothing reads `~/.ssh`, keychains, browser profiles or tokens, and environment variables are never sent anywhere. |
| PY-15 | `uv.lock`; `pyproject.toml:1-22` | 61 PyPI packages plus the virtual root. No git, url or path sources. All 861 artifacts are on files.pythonhosted.org with sha256 hashes. The CUDA-13 stack is `sys_platform == 'linux'` only. |
| PY-16 | `uv.lock` | No known serious CVE at the pinned versions, as of the reviewer's knowledge; re-check on OSV (E9). |
| PY-17 | `rl/combat_mcts.py:284-297`; `rl/live_search.py:76-77, 681-686`; `rl/run_train/selfplay.py:455-470` | `Combat.fork(None)` is an oracle copy. Treat every call site as a review gate (§6.2). |
| M-F7 ✓ | `McpMod.Helpers.cs:177-178` | The hidden gate needs both `allow_hidden_state: true` and `?hidden=1`. Only `HandleGetState` and `HandleGetCompendium` honour it. State embedded by a POST and multiplayer state are never hidden. |
| M-F9 ✓ | `McpMod.cs:179-182, 198-201` | Listens on `localhost` and `127.0.0.1` only. If `Start()` throws, the error is logged and the bridge stays off (it fails closed). |
| M-F10 ✓ | `McpMod.Config.cs:89-112, 250-270`; `McpMod.cs:351-369` | The token comes from the OS cryptographic RNG and is compared with `FixedTimeEquals`. Requests with an `Origin` header get 403, auth runs before routing, and POST must be JSON. |
| M-F14 | `McpMod.cs:204-215`; `McpMod.TimeScale.cs:40-62` | Harmony `PatchAll` on the mod's own assembly. No combat or RNG logic is patched. After `set_time_scale`, `KeepApiTimeScale` rewrites `Engine.TimeScale` every frame. |
| M-F15 | `STS2_MCP.csproj:29-44, 52-63`; `build.ps1:73` | No `Process.Start`, HttpClient, Socket or `OS.Execute`. The game DLLs are referenced with `Private=false`. The only MSBuild `Exec` runs `git rev-parse` and `git status`. |
| M-F17 | `McpMod.cs:534-539, 549-550, 660-665, 910-912` | 500 responses include stack traces, and request bodies are read with an unbounded `ReadToEnd`. Both are reachable only by token holders. |
| M-F18 | `FORK_NOTES.md:1-12` | Against Gennadiyev `55e0648`: 27 files changed, +9108/−778. `build.ps1`, the manifest and `.claude/` are unchanged. |
| M-F19 | `McpMod.cs:373-461` | Endpoint inventory, used in §6.1. |
| PROV-2 | GitHub API | Three repos and 25 branches were published on 2026-10-05, 17:36:11-17:36:34Z. No secrets, binaries, releases or tags. |

---

## 4. Conditions

**Kit status** refers to the WSL2 `pc-setup/` kit as read on 2026-10-10, before it moved into this repo. Kit line numbers refer to that version and may have shifted since. On native Windows, see the note at the top. The status values:
- **met:** the kit already does it.
- **partly:** the kit does some of it.
- **open:** a kit or Spireline change is needed.
- **Spireline:** Spireline code still to be written.

### 4.1 Emulator: before and during the first build

| # | Condition | From | Kit status |
|---|---|---|---|
| E1 | Clone from GitHub at `b7452170…` and refuse unless the tree is `7d5c4dfe…`. Build only a clean checkout. | PROV-1, E-F18 | met: `clone-pinned.sh:20`; `build-emulator.sh` checks HEAD, tree and a clean status |
| E2 | Never run these:<br>- `scripts/desktop_setup.sh`, `desktop_fight_job.sh`, `night_train.sh`, `fight_loop_rounds.sh`<br>- `lint-and-test.sh`<br>- `scripts/ralph/ralph.sh`<br>- `decompile.sh`, `patch_update.sh`, `patch_refresh.py --apply`<br>- any `capture_*`, `trace_real_game*`, `validate_real_game_*`, `combat_sweep`, `start_real_game_run` or `compare_draw_pile` script against a live game<br>- `bun install` or `bunx` | E-F11-F14, F17, PY-01, PY-03, PY-04, AGENT-1 | partly: the kit invokes none of them; bypass mode is disabled; `bun`/`bunx`/`claude` are ask rules. Open: add a deny rule `Bash(*ralph*)` to `claude-settings.json` |
| E3 | No trust from the PC into the Mac: no Mac Remote Login, no PC key in the Mac's `authorized_keys`, no rsync loops. Results move by a pull that you start. | E-F11, E-F12 | met: the kit creates no keys; `ssh`, `scp` and `rsync` are ask rules |
| E4 | Toolchain from signed or pinned sources:<br>- apt `clang` and `zlib1g-dev`;<br>- the .NET 9 SDK through a GPG-verified `dotnet-install.sh` with one exact `DOTNET_SDK_VERSION`;<br>- uv at a pinned `UV_VERSION`, with its release checksum checked;<br>- Python 3.12 through uv. | E-F11, BUILD-2, PY-03 | partly: the dotnet signature is checked (`wsl-bootstrap.sh:106-117`), but the channel is the default (`:119`). uv is downloaded to a file rather than piped (`:157-160`), but its version is optional and there is no checksum. Open: set both versions and check the uv tarball's sha256 |
| E5 | No `Directory.Build.*`, `nuget.config` or `global.json` in `~/src`, `~` or `/`. `~/.nuget/NuGet/NuGet.Config` lists only nuget.org. Pin the SDK by installing exactly one version, not with a `global.json` (Appendix A, reconciliation a). | E-F08, BUILD-2 | open: add an `ls` check before the build |
| E6 | Telemetry off before the first `dotnet` call: `DOTNET_CLI_TELEMETRY_OPTOUT=1`, `DOTNET_NOLOGO=1`. | E-F10 | met: `build-emulator.sh:100`, `wsl-bootstrap.sh:126`, `claude-settings.json` `env` |
| E7 | Build with an explicit RID (`bash scripts/build.sh linux-x64`). Record in `versions.lock`:<br>- the `Sts2Emulator.so` sha256;<br>- `dotnet --version`;<br>- the id, version and `.nupkg.sha512` of every package restored. | E-F08, BUILD-2, PY-05 | partly: the RID and the `.so` sha256 are recorded. Open: the package hashes |
| E8 | The first build and both test suites run contained: offline after a fetch-only step, with `/mnt/c`, `~/.claude` and `~/.ssh` hidden and only the checkout writable (§7.2). | PROV condition 3, §7 | open: `build-emulator.sh` runs them in your terminal, online and unsandboxed. On native Windows: replaced by the offline first build in `pc-setup/WINDOWS.md` section 6 |
| E9 | Upstream Python goes only into the checkout's own `.venv`, via `uv sync --frozen --no-build`. Spireline's `~/.venvs/spireline` never syncs the upstream `pyproject.toml`. Before the first sync:<br>- check the pins on osv.dev;<br>- confirm the publisher of `rpds-py` 2026.6.3;<br>- confirm the Windows NVIDIA driver supports CUDA 13 (the cu13 wheels are about 2.7 GB).<br>Before every upstream test run: `SPIRE_COACH_REPO` and `STS2_LIB_PATH` are unset, and `~/Documents/git/spire-coach` and `~/Documents/git/sts2-wt` do not exist. | PY-02, PY-05, PY-09, PY-16, E-F11 | partly: `build-emulator.sh:148` uses `uv sync --locked` (hash-checked) in the checkout. Open: `--no-build`, the OSV, publisher and driver checks, and the environment and path pre-checks |

### 4.2 Emulator: in Spireline's code

| # | Condition | From | Status |
|---|---|---|---|
| E10 | One emulator instance per OS process (spawn pool); never call it from Python threads. Destroy handles explicitly, through a handle arena of 256 or fewer per process, and check the −1/−2 return codes. | E-F04, E-F22 | Spireline |
| E11 | A determinism regression test: the same seed and actions give an identical trajectory and observations. | E-F04, E-F21 | Spireline |
| E12 | An allow-list wrapper over the native surface (§6.2):<br>- every clone in search or agent code uses `resample_hidden=1`;<br>- `Sts2_GetPile(0)`, `Sts2Run_GetStateList` 11-13, `Sts2_RngCallCount` and all `Debug*` exports are banned outside verification code, asserted by a test;<br>- handles and ids are validated before each call;<br>- buffers are sized from the `*ObsSize` and `InfoSize` queries;<br>- the snapshot input size is capped. | E-F02, F03, F06, F07, FFI-1, PY-17 | Spireline |
| E13 | Before any run-level search (Phase 2), fix E-F05, with a test showing two resampled clones diverge on the next encounter and relic. | E-F05 | Spireline (Phase 2 gate) |
| E14 | Upstream training loops run only with in-tree paths: `prior_loop run --no-export` or an in-tree `--export-dir`; `export_dest` set for `run_train`. Never set `STS2_ALLOW_STALE_NATIVE`. Load the library by absolute path and check its sha256 against `versions.lock`. | PY-06, E-F23 | Spireline |
| E15 | Keep the game at v0.107.1, Steam build 23811903 (D1). Decompile only after a deliberate patch update, with `ilspycmd` 8.2.0.7535 and the venv's Python. `decompiled/` never leaves the machine. | E-F17, LIC-1 | D1 |
| E16 | Make the third-party checkouts read-only to the processes that run search and training: `rl/` is first on `sys.path` (PY-11), and `service.py` imports by bare module name. | PROC-1 | open: `chmod -R a-w ~/src/sts2` after the build, except `out/` |

### 4.3 Mod

| # | Condition | From | Status |
|---|---|---|---|
| M1 | Install only when live work starts. You build `STS2_MCP.dll` on Windows with the Microsoft .NET 9 SDK, from `5a63f924…` (tree `86f940c6…`); never a prebuilt DLL. Record the DLL's sha256. Confirm that `GET /` reports `mod_commit` 5a63f92, and that the game log shows `[STS2 MCP] ... server started`. | M-F15, M-F18, M-F9 | open (live day) |
| M2 | Back up the whole `%AppData%\SlayTheSpire2` folder before the first modded launch. Give Spireline runs their own profile slot. | M-F8, PY-01 | partly: the CHECKLIST A-step `robocopy` backs up the saves. Open: the dedicated slot |
| M3 | `STS2_MCP.conf` keeps `allow_hidden_state: false` and `allow_debug_actions: false` for any session the search reads. Either one is turned on only for emulator-validation sessions, on a profile other than the main one. | M-F7, M-F13 | open (live day) |
| M4 | Spireline's client is the mod's only caller, and it enforces an endpoint allow-list. Allowed: `GET /api/v1/singleplayer` without `?hidden`, and `POST /api/v1/singleplayer` with in-run gameplay actions only. Denied to the agent: `/api/v1/profiles` (GET and POST), `/profile`, `/compendium`, `/wiki`, `/actions`, multiplayer, `debug_*`, `return_to_main_menu`, and the `menu_select` options quit, abandon_run, give_up and yes. The token is sent only as a header, and the response size is capped. | M-F6, F8, F13, F17, F19 | Spireline: no client exists yet |
| M5 | The payload firewall applies §6.1. If a hidden-read field (`draw_pile_ordered`, `move_follow_up_id`) ever appears, the adapter stops; dropping the field is not enough. | M-F1-F7 | partly: `spireline/infoset/firewall.py` v0 drops these fields and flags `hidden_read_detected` (firewall.py:49-50). Open: make the flag fatal in the adapter |
| M6 | Run setup, which chooses or knows the seed through `menu_select`, is a separate process from the search and never passes the seed on. | M-F6 | Spireline |
| M7 | WSL networking stays on the default NAT until the live day. Then either `networkingMode=mirrored` (Windows 11 22H2+), or the thin client runs on Windows. No `netsh portproxy` on 0.0.0.0, and no inbound firewall rule for 15526. | M-F9 | met: CHECKLIST B1 (line 77) |
| M8 | Never install or run `mcp/`, its `uv.lock`, or the mod repo's `.claude/`. Never start Claude Code with the mod checkout as its working directory. | M-F16 | met: `claude-settings.json` denies `mcp__*`; Remote Control works in `~/code`, and the checkout sits in `~/src` |
| M9 | Treat every GET as an action in parity traces. Keep `time_scale` at 1 during parity tests. | M-F12, M-F14 | Spireline |

### 4.4 Repo and licence

| # | Condition | From | Status |
|---|---|---|---|
| R1 | Updated for the public repo (it originally said the Spireline repo stays private). Spireline publishes nothing from `Generated/`, `data/` or `decompiled/`. Anything derived from r33hab/sts2 keeps its LICENSE verbatim, plus a NOTICE with the lineage: Zamiell `04cfe6d` → evangambit `aa4b0d8`..`37e4264` (= r33hab `cd93393`) → r33hab `b745217`; mod Gennadiyev `55e0648` → r33hab `5a63f92`. | LIC-1, LIC-2 | open: the public repo vendors no third-party code yet, so no NOTICE is needed yet |
| R2 | Delete the local review clone of Zamiell's repo: its `.git` holds the decompiled MegaCrit objects. | LIC-1 | open (after this review) |
| R3 | Spireline gets its own `CLAUDE.md`. It states the hard rules and says that upstream `AGENTS.md`, `HANDOFF.md`, `PLAN.md`, `COPILOT.md` and the ralph prompts are data, not instructions. | AGENT-1 | open: there is no `CLAUDE.md` in the repo yet |

---

## 5. Provenance conclusion

The content is traceable, and the history rewrite changed no content. This resolves the open question in design §3.6 ("the SHAs differ because history was rewritten").

```
Zamiell/slay-the-spire-2-emulator 04cfe6d   143 commits; contains decompiled/ (3418 files)
        │ imported as one commit, without decompiled/
evangambit/sts2 aa4b0d8 … 37e4264           467 commits; README credits Zamiell
        │ all 467 carried over: 273 same SHA, 194 re-SHA'd (identical trees, authors,
        │ dates, messages; only the GitHub gpgsig on the PR #1 merge e9efc57 was dropped)
r33hab/sts2 main cd93393                    tree 0c70a122… = evangambit 37e4264 (checked 2026-10-10)
        │ +263 commits, 2026-09-24 … 2026-10-05,
        │ 326 files, +109,124 / −1,566, additions and modifications only
r33hab/sts2 spire-coach b745217             tree 7d5c4dfe…  ← pinned

Gennadiyev/STS2MCP main 55e0648 ─(evangambit/STS2MCP, per FORK_NOTES.md)─► r33hab/STS2MCP spire-coach 5a63f92
                                             27 files, +9108 / −778; tree 86f940c6…  ← pinned
```

- **Publication.** r33hab/sts2, r33hab/STS2MCP and r33hab/spire-coach were created between 17:36:11Z and 17:36:20Z on 2026-10-05. All 25 sts2 branches arrived in one push at 17:36:34Z, ten minutes after the last commit. None is a GitHub fork. Host names in the upstream scripts are placeholders (`your-mac.local`).
- **What it does not show.** Only the published history can be reviewed: the 263 commits in `cd93393..b745217`. Earlier history is not public.
- **What to pin.** Commit and tree for both repos, which `clone-pinned.sh` checks. Keep the review clones as a local mirror, because any upstream branch can move or disappear later.
- **Where the effort goes.** The remaining risk is mostly correctness, not code safety. Effort belongs in fidelity tests of the 109k added lines (design §3.3) rather than more security review of the same commits.

---

## 6. Hidden-information inventory (input to the firewall)

This is the input to `spireline/infoset/firewall.py` and decision D10. The rules: any change to an allow-list is a new dated D-entry with its evidence; nothing here is admitted without L7 or L8 evidence; when in doubt, the field is dropped.

### 6.1 Mod payload (STS2MCP schema 4)

**Columns:**
- **Default:** whether the field is in the default payload, with no `?hidden=1`.
- **Firewall v0:** what `firewall.py` does today, read from its module docstring (firewall.py:1-50).

| Field | Source (`McpMod.<file>.cs:line`) | Default | Leak | Firewall rule | Firewall v0 |
|---|---|---|---|---|---|
| `draw_pile_ordered` | StateBuilder:1760-1761 | no (needs `allow_hidden_state` and `?hidden=1`, Helpers:177-178) | true draw order | block; stop the adapter if present | dropped and flagged; open: make the flag fatal (M5) |
| `move_follow_up_id` | StateExtras:225, 229-230 | no | the next move after this one | block; stop the adapter if present | dropped and flagged; open: make the flag fatal |
| `/compendium` `current_run.seed` | Compendium:404-412 | no | the run seed | deny the endpoint | transport (M4); no client yet |
| `move_id` | StateExtras:219-228 | yes | with the static move graph, reveals wired follow-ups | strip; allow-list per monster, on L8 evidence | allow-list empty |
| `state_log` | StateExtras:237, 248-258 | yes | the tail is the rolled, not yet executed move; earlier entries can include moves rolled and then replaced | strip; keep our own log of observed intents | partly: v0 trims only the last entry. Open: the earlier rolled-then-replaced entries (M-F1) argue for dropping it whole |
| `ai_fields` | StateExtras:239, 316-338 | yes | any pre-rolled choice or hidden counter; getters run | default-deny; allow-list per monster and key, on L7 evidence | allow-list empty |
| `revive.in_turns` | StateBuilder:2527-2532, 2669-2686 | yes | walks `FollowUpState` | strip | allow-list empty |
| `draw_pile` list order and uids | StateBuilder:1733-1737; uid at 2242 | yes | ties keep their true order (stable insertion sort for 16 or fewer cards) | multiset keyed by (id, upgrade, enchantment, affliction, cost fields); no order, no uids | multiset, uids dropped. The docstring calls the sort "not stable"; the mechanism is the opposite, but the remedy is the same (Appendix A) |
| powers with `hidden_in_ui` | StateBuilder:4217-4220, 4265-4266 | yes, when non-zero | hidden countdowns or flags | strip | allow-list empty |
| relic `fields`, `saved` | StateExtras:387-441 | yes | private relic state | allow-list per relic; keep the displayed `counter` | allow-list empty; `counter` kept |
| card `vs_targets[].values` | StateBuilder:2096-2110 | yes | preview dynamic variables | strip; keep damage, hits and block | allow-list empty (D10) |
| `run.start_time` | StateBuilder:692-701 | yes | wall-clock time; a possible seed correlate | strip | dropped |
| `game_over.seed` | StateBuilder:539 | yes, after the run | the seed of the run just played | strip | dropped (all seeds) |
| custom-run `seed_input`, `lobby.seed` | StateBuilder:766-767, 1340-1341 | yes, on menus | the next run's seed | strip; run setup is a separate process (M6) | dropped: non-combat screens are not admitted in v0 |
| `run_history[].seed`, `save_path`, `history_path` | Compendium:286, 333, 387; Profile:115-116 | yes, on those endpoints | past seeds; Windows username and SteamID64 | deny the endpoints | transport (M4) |
| `/profile`, `/profiles`, `/wiki?scope=all`, `/actions` | McpMod:421-457 | token only | profile data; destructive POSTs | deny to the agent | transport (M4) |
| boss and second-boss id, `can_be_modified` | StateBuilder:3139-3159, 3473-3474 | yes | unknown whether the game UI shows them at that time | verify against the UI before admitting them | dropped: map screen not admitted in v0 |
| uid numbering of deck and hand | StateBuilder:2358-2411 | yes | none: uids follow deck order and random ties (fixed in this fork, 2344-2347) | hand stays ordered with uids (D10) | kept for the hand |
| `encounters_seen`, `elite_cycle` (counts) | StateBuilder:3283-3397 | yes | none | OK | not admitted in v0 (map) |
| `crystal_sphere` | StateBuilder:4070-4080 | yes | none: items in hidden cells are withheld | OK | not admitted in v0 |
| `special_card` reward | StateBuilder:3559-3565 | yes | none: the game shows it on hover | OK | not admitted in v0 |
| state embedded by a POST `wait`; multiplayer state | McpMod:809, 894, 511; MultiplayerState:254, 276 | never hidden | none | OK | n/a |

Two more behaviours of the mod also count as information channels:
- GET's side effects (StateBuilder:633-637, 2800-2811, 4150-4156) change what the next payload shows.
- `ai_fields` getters run on every GET (M-F2, M-F12).

### 6.2 Emulator surfaces (input to the search allow-list, E12)

| Surface | Source | What it reveals | Rule |
|---|---|---|---|
| `Sts2_Clone`, `Sts2Run_Clone`, `Sts2Run_ForkCombat` with `resampleHidden=0` | NativeExports.cs:515-546; RunNativeExports.cs:93-125 | a faithful copy (oracle) | search and agent code must pass `resample_hidden=1` |
| `Combat.fork(None)` | rl/combat_mcts.py:284-297; rl/live_search.py:681-686 | oracle copy, used to read the observation | review gate at each call site. Add a test that permuted draw piles give identical observations and prior outputs (PY-17) |
| `Sts2_GetPile(handle, 0, …)` | NativeExports.cs:1181-1207 | true draw-pile order | banned outside verification code |
| `Sts2Run_GetStateList` lists 11, 12, 13 | RunNativeExports.cs:276-280 | future normal, elite and event sequences | banned outside verification code (also design §4.4 item 1) |
| `Sts2_RngCallCount` | NativeExports.cs:846-872 | RNG stream positions | banned outside verification code |
| `Debug*`, `Sts2Run_DebugSetPlayer`, `Sts2Run_DebugResolveCombat` | NativeExports.cs:792-804; RunNativeExports.cs:389-537 | state mutation | test code only |
| resampled run clone | StateCloning.cs:439-451, 501-502; Core/Run/RunEngine.cs:913-955 | next encounter, elite, event and relic (E-F05) | no run-level search until E13 |
| snapshot export (`Sts2_GetStateJson`) | CombatSnapshot.cs:1269-1300 | none: the unordered middle of the draw pile is sorted | OK |

---

## 7. What reading cannot establish, and how the setup contains it

### 7.1 Open questions

| Unknown | Why reading can't settle it | Containment or settlement |
|---|---|---|
| What the compiled NativeAOT `.so` actually does | This was a source-only review, and the ILCompiler and runtime packs come from NuGet at restore time | Build it ourselves from the pinned tree and record its sha256 (E7). Run it only contained (§7.2). Load it by absolute path (E14). |
| Whether the restored NuGet packages are untampered | There is no `packages.lock.json`; this rests on nuget.org signing | Restore from nuget.org only (E5). Record each `.nupkg.sha512` (E7). Optionally set `DOTNET_NUGET_SIGNATURE_VERIFICATION=true`; whether that is already the default on Linux for this SDK is UNVERIFIED. |
| Whether the PyPI artifacts are benign; CVEs after the reviewer's cutoff; `rpds-py` CalVer | Nothing was downloaded | `uv sync --frozen --no-build` gives hash-checked wheels and no build scripts, so no code runs at install. Check OSV and the publisher first (E9). |
| Whether `dotnet-install.sh` and uv's `install.sh` are benign at fetch time | They are fetched live | dotnet: GPG check (kit). uv: pinned version and tarball checksum (E4). |
| History before the published commits; whether the repos change later | Earlier history is not public | Pin commit and tree (E1). Keep the review clones as a mirror. Re-review before taking any new upstream commit. |
| Fidelity of the 109k added lines, including whether StS2 really pre-rolls the sequences E-F05 relies on | Correctness, not security | Design §3.3 fidelity programme (F1-F9). |
| Behaviour under search load: memory growth, abort rate, clone throughput | Needs execution | Subprocess workers (E10), the `.wslconfig` memory cap (CHECKLIST B1), the handle arena. |
| Whether the upstream suites pass on Linux, given spawn plus NativeAOT signals (r33hab/sts2 shows no CI runs) | Needs execution | The first contained run records pass/fail counts in `versions.lock`. Failures are data, not a reason to run `lint-and-test.sh`. |
| The PC's environment: parent-directory MSBuild or NuGet config, Ubuntu version, CPU and RAM | Not visible from the Mac | The E5 check; `spec-check.ps1`; the kit's `wsl-bootstrap.sh` summary. |
| Whether http.sys lets a non-admin process register the `127.0.0.1` prefix | Windows runtime behaviour | If it can't, the bridge stays off (it fails closed). Check the game log line on the live day (M1). |
| Whether any monster `ai_fields`, relic fields or HUD-hidden powers carry hidden information; whether getters or `UpdateDynamicVarPreview` consume RNG; whether the boss ids and `can_be_modified` are visible in the UI; whether `StartRunLobby.Seed` is filled for standard runs; whether intent-hiding or draw-revealing relics exist | Depends on the game's code and UI | Default-deny firewall with evidence-gated allow-lists (§6.1, D10); parity checks after GETs (M9). |
| What `affects_gameplay: false` means for progress and achievements; whether `DeleteProfile` is recoverable | The game's behaviour | Full save backup (M2), a dedicated profile, and the client never calling `/profiles` (M4). |
| Whether the DLL you build matches this source | Nothing was compiled | You build from the pinned tree, record the sha256 and check `mod_commit` (M1). |
| The licence status of files generated from a decompile (`Generated/`, `data/`) | A legal question, not a technical one | Nothing from `Generated/`, `data/` or `decompiled/` is redistributed (R1). |

### 7.2 Containment on the PC

This section describes the WSL2 setup. On native Windows, the offline first build in `pc-setup/WINDOWS.md` section 6 takes its place (see the note at the top).

These layers come from the kit as read on 2026-10-10. Where a gap remains, the fix is given.

1. **No third-party code runs natively on Windows**, except the mod inside the game and its build (M1).
   - Claude Code does not run natively on Windows (CHECKLIST A8).
   - WSL interop is turned off after `/login` (CHECKLIST C7), so WSL processes can't launch Windows programs.
2. **The WSL2 VM is a weak boundary on its own.**
   - All WSL2 distros share one utility VM and kernel, so a dedicated distro adds little.
   - `/mnt/c` is mounted read-write as your Windows user. That covers the saves under `%AppData%`, the Startup folder, and the Steam `mods/` folder with the mod's token.
   - The real boundaries are bubblewrap and keeping `/mnt/c` out of reach.
3. **Claude Code's sandbox** (strict mode, `claude-settings.json`) applies to everything Claude runs:
   - writes only to `~/code`, `~/src`, `~/logs` and `~/.venvs/spireline`;
   - `~/.ssh`, `~/.aws`, `~/.gnupg`, the GitHub credentials, `~/.claude/.credentials.json` and `/mnt/c/Users` are unreadable;
   - each network host needs your approval;
   - nothing falls back to running unsandboxed.
   - Remaining gap: `/mnt/c` outside `Users` (the Steam folder, including `STS2_MCP.conf`) is readable. That is acceptable, because the live client needs the token.
4. **Separate directories.**
   - Third-party checkouts live in `~/src`; Spireline lives in `~/code`.
   - The upstream venv is the checkout's own `.venv`, kept apart from `~/.venvs/spireline`.
   - After the build, make `~/src/sts2` read-only except `out/` (E16).
5. **No secrets on the box during the first build and tests.**
   - Allowed: the Claude Code login token only.
   - Not yet: no GitHub token, SSH keys, cloud credentials or browser logins in WSL.
   - The fine-grained, single-repo GitHub token (CHECKLIST line 198) comes after E8.
6. **Network deny where possible.**
   - The first build and test run is offline after a fetch-only step (below).
   - Routine sandboxed work allows only `api.nuget.org`, `pypi.org`, `files.pythonhosted.org` and `github.com` (CHECKLIST T9).
   - The Windows Firewall keeps its default inbound block.

**The gap this review asks to close (E8).** `build-emulator.sh` runs in your own terminal, outside the sandbox, so that an agent cannot type GO. It runs four things there:
- `dotnet publish` (ILCompiler from NuGet);
- `dotnet test`, over about 456 upstream C# test files;
- `uv sync`;
- the upstream Python suite, which spawns subprocesses.

They run with full network access, with `~/.claude/.credentials.json` readable, and with `/mnt/c` writable. The reviews found nothing in that code that reaches out. But the compiled binary and the downloaded packages are exactly what reading cannot vouch for. Keep the human GO gate, and change what runs after it:

- **Option B (tightest; recommended for the first run).** Split the run into a fetch step and an offline step. The fetch step runs no third-party code: NuGet restore runs no package scripts, and `--no-build` refuses sdists. The offline step runs under bubblewrap, which the kit already installs for Claude Code. It gets no network, a read-only root, `/mnt`, `~/.claude`, `~/.ssh` and `~/.config` hidden, and only the checkout and log directory writable. **UNTESTED:** expect to adjust the binds once. What must hold is `--unshare-net`, and that no path outside `~/src/sts2` and `$LOGDIR` is writable.

  ```bash
  # 1. fetch only, online
  cd ~/src/sts2
  dotnet restore src/Sts2Emulator/Sts2Emulator.csproj -r linux-x64
  dotnet restore src/Sts2Emulator.Tests/Sts2Emulator.Tests.csproj
  UV_PYTHON=3.12 uv sync --frozen --no-build
  # 2. build and test, offline
  bwrap --unshare-net --unshare-pid --die-with-parent --new-session \
    --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs /mnt \
    --tmpfs "$HOME/.claude" --tmpfs "$HOME/.ssh" --tmpfs "$HOME/.config" \
    --bind "$HOME/src/sts2" "$HOME/src/sts2" --bind "$LOGDIR" "$LOGDIR" \
    --setenv DOTNET_CLI_TELEMETRY_OPTOUT 1 --setenv DOTNET_NOLOGO 1 \
    bash "$HOME/pc-setup/offline-build-and-test.sh"   # ours, to write: cd ~/src/sts2; build.sh linux-x64; dotnet test --no-restore; .venv/bin/python -m unittest discover -s tests/python
  ```

  The wrapper script is ours and does not exist yet. It lives in `~/pc-setup/`, outside the checkout, because the checkout must stay clean. Run the publish step's implicit restore as a no-op. If it tries the network, call `dotnet publish … --no-restore` with build.sh's arguments directly.
- **Option A (simpler; the right default after the first run).** You approve in chat, and Claude runs the same steps inside its sandbox, with network approved only for `api.nuget.org`, `pypi.org` and `files.pythonhosted.org`. Secrets and `/mnt/c/Users` are already hidden. The cost: `~/code` (the Spireline repo) and `~/.venvs/spireline` stay writable, so run `git status` in `~/code/spireline` afterwards.
- **Option C (if neither works).** Do E3 as a separate Linux user, `sts2build`, which has no Claude login and no access to your home folder. With the default DrvFs mount options (no `metadata`), `/mnt/c` files show as owned by uid 1000 with umask 022, so a second uid can read them but not write them. This is UNVERIFIED: confirm it with a `touch /mnt/c/Users/<you>/probe` as `sts2build`, which should fail.

**Minimum if all three fail:**
- WSL interop off;
- `[automount] enabled = false` in `/etc/wsl.conf` for the duration (copy the kit in first, then `wsl --shutdown`);
- no secrets on the box other than the Claude login.

---

## 8. spire-coach: not reviewed, not used

"spire-coach" names two different things.

- **The branches.** `spire-coach` is the branch name on r33hab/sts2 and r33hab/STS2MCP. Those trees are MIT, and they are what this document reviews.
- **The separate repository.** `r33hab/spire-coach` was created in the same bulk publication (§5). It has no licence (design §3.6), so all rights are reserved by default. It was not reviewed, and Spireline does not use it.
- **What that rules out:**
  - no cloning into Spireline;
  - no running it, including `spire-coach mod install`, `mod enable` and `saves seed-modded` (design §3.6 step 4);
  - no vendoring, and no reading it to port code.
- **Consequences:**
  - The live converter is our own (`spireline/infoset/firewall.py`, written from the mod's C#; D3).
  - Baseline B3 (spire-coach) cannot run unless licence terms are granted (design §3.6 step 6).
- **Upstream hooks into spire-coach to neutralise:**
  - `scripts/fidelity_replay.py:62-70` imports `coach.snapshot` from `~/Documents/git/spire-coach` (PY-02, E9).
  - Both training loops export into `~/Documents/git/spire-coach/data/models` by default (PY-06, E14).
  - `.claude/commands/playsts2.md` in the mod repo is part of the `.claude/` directory that is never used (M8).
  - `~/Documents/git/spire-coach` must not exist on the PC.

---

## Appendix A. Refuted findings, corrections and reconciliations

**Refuted by verifiers: none.** The adversarial verification step returned no output for any of the four reviews, so nothing could be refuted. All findings above stand at the reviewers' severities.

**Corrections from the 2026-10-10 re-read:**

1. **PY-12** says WSL2 "localhost forwarding or mirrored networking" lets WSL reach the Windows mod on `localhost:15526`. Only mirrored mode does. `localhostForwarding` works the other way: Windows reaches WSL. Under the default NAT, WSL can't reach Windows `127.0.0.1`. M-F9 and CHECKLIST B1 are right.
2. **PROV-1** limits the code review to evangambit's `main`..`b745217` (the 263 r33hab commits). That range actually has 457 commits, because the 194 rewritten commits have new SHAs. The range with the 263 r33hab commits is `cd93393..b745217`: 326 files, +109,124/−1,566 (checked 2026-10-10).
3. **E-F05** cites `RunEngine.cs:913-955`. The file is `src/Sts2Emulator/Core/Run/RunEngine.cs`; the lines are correct.
4. **`firewall.py:21-23`** says `List.Sort` "is not stable". M-F3 is the more precise statement: for 16 or fewer elements, .NET uses insertion sort, which is stable, so tied cards keep their exact draw order. The remedy (multiset) is unchanged; only the docstring wording needs fixing.
5. **`firewall.py` v0 keeps `state_log` minus its last entry.** M-F1 notes that earlier entries can include rolled-then-replaced moves the player never saw, and recommends dropping the log and keeping our own observed-intent log. This is listed as open in §6.1.

**Reconciled conflicts between reviews:**

- **(a) `global.json`.** BUILD-2 says to add our own `global.json`, but E-F08's condition says there must be no `global.json` in any parent directory of the clone. Placing one inside the checkout would also dirty the tree that `build-emulator.sh` requires to be clean. Resolution: no `global.json`. Pin by installing exactly one SDK version and recording `dotnet --version` (E4, E5, E7).
- **(b) Where upstream Python goes.** The emulator review says "don't let `uv run` sync the repo's pyproject; use Spireline's venv". The Python review says "`uv sync --frozen` into the project venv". Resolution: the upstream lock goes only into the checkout's own `.venv` and is used only to run the upstream suite, contained. `~/.venvs/spireline` never receives it (E9).
- **(c) Where the first build runs.** PROV's condition says the first build runs inside the Claude Code sandbox, while the kit's E3 runs it in your terminal so that a human types GO. Resolution: keep the human gate, and run the build and tests offline under bubblewrap (Option B), or in the sandbox after approval in chat (Option A) (§7.2, E8).
