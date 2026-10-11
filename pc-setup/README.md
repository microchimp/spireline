# Spireline PC setup kit

This folder turns the always-on Windows gaming PC (RTX 3080 Ti) into the Spireline compute box. The heavy work runs in Ubuntu 24.04 under WSL2. Claude Code runs there inside its sandbox, and you reach it from your phone through Remote Control. Start with `CHECKLIST.md`. It is the step-by-step plan for 2026-10-11 and uses every file below.

None of these scripts has been run on the PC yet. They were syntax-checked on the Mac (`bash -n`), and only the review gate of `build-emulator.sh` (its step 1) was exercised there, in a scratch home folder.

The kit ships inside the public Spireline repo (CHECKLIST D0), so `git clone https://github.com/microchimp/spireline` brings it along. The security review it refers to does not: that review is private and stays on the Mac.

## The files

| File | Where it runs | What it is for |
| --- | --- | --- |
| `CHECKLIST.md` | You read it | The ordered tick-box plan with time estimates, parts A to F, and a troubleshooting list. |
| `spec-check.ps1` | Windows PowerShell | Reports the PC's CPU, RAM, GPU, VRAM, driver, Windows build, free disk, power and update settings, WSL state, and the Slay the Spire 2 install. That includes the Steam `buildid` from `appmanifest_2868840.acf` and the `sts2.dll` sha256. It prints a `.wslconfig` sized to the machine. **It changes nothing.** |
| `wsl-bootstrap.sh` | Ubuntu (WSL2) | One-time setup, safe to re-run. It installs the apt packages needed by .NET NativeAOT, the .NET SDK and the Claude Code sandbox. It installs the .NET 9 SDK in `~/.dotnet`, but only after checking Microsoft's GPG signature on `dotnet-install.sh`. It installs uv and Python 3.12. It checks the GPU, the sandbox prerequisites and WSL interop, then prints a summary. It uses `sudo` for `apt` only. |
| `clone-pinned.sh` | Ubuntu | Downloads the two reviewed third-party repos at their exact pinned commits into `~/src`. It refuses if the commit or tree hash differs, and it builds nothing. |
| `build-emulator.sh` | Ubuntu, in your own terminal | Shows the verdict line from `SECURITY_REVIEW.md` if the file is on the PC (the default path or a path you pass). If it isn't, it prints a note that the private review lives on the Mac. Either way it waits for you to type `GO`. It then builds the emulator with the repo's own script, runs both test suites, and writes the test counts and the library's sha256 to `~/src/versions.lock`. |
| `rc-launch.sh` | Ubuntu | Keeps `claude remote-control --name gaming-pc` running in `~/code` inside a tmux session (`spireline-rc`). It restarts with backoff, resumes the same phone session with `--continue` when it can, and logs to `~/logs/rc.log`. Also has `status`, `attach`, `stop`, `restart`, `fresh` and `env`. |
| `claude-settings.json` | Copied to `~/.claude/settings.json` in Ubuntu | Claude Code's user settings for the PC. It turns the sandbox on in strict mode, blocks destructive and data-leaking commands, asks before network and push actions, and blocks bypass mode. |
| `README.md` | You read it | This file. |
| `SHA256SUMS` | Ubuntu | Checksums of the files above. `sha256sum -c SHA256SUMS` proves the copy (USB stick, share or git clone) arrived intact. |

## Where things live on the PC

| Path (inside Ubuntu) | What |
| --- | --- |
| `~/pc-setup/` | This kit. Claude can read it but can't edit it. |
| `~/code/` | Remote Control's working folder. `~/code/spireline` is the Spireline repo, and `~/code/.cache` holds tool caches for Claude's commands. |
| `~/src/sts2`, `~/src/STS2MCP` | The pinned third-party checkouts. `~/src/versions.lock` is written by `build-emulator.sh`. |
| `~/logs/` | `rc.log`, plus a folder per build run. |
| `~/.local/state/spireline-rc/` | The launcher's tmux socket and state. It is hidden from Claude's sandboxed commands. |
| `~/.dotnet`, `~/.local/bin`, `~/.local/share/uv` | .NET 9 SDK, uv and Claude Code, and uv's Pythons. Claude can't write to any of them. |
| `C:\Users\<you>\.wslconfig` | WSL VM size: memory, processors, swap. |

## What Claude can and can't do on the PC

These limits apply with `claude-settings.json` installed.

- **Without asking:** it can read files, except the hidden ones below. It can run shell commands inside the sandbox, and those commands can write only in `~/code`, `~/src`, `~/logs` and `~/.venvs/spireline`. The operating system enforces that limit through bubblewrap.
- **Only after you approve on the phone:** any network host a command wants to reach. Also `git push`/`fetch`/`pull`/`clone`/`remote`, `curl`, `wget`, `ssh`, `scp`, `rsync`, package installs (`pip install`, `uv add`, `npm`, `dotnet tool`), `bash -c`, every WebFetch, and every file edit. File edits are asked for in default mode.
- **Never:**
  - `sudo`.
  - Writing anywhere else on the disk.
  - Reading `~/.ssh`, `~/.aws`, `~/.gnupg`, GitHub credentials, its own login token (`~/.claude/.credentials.json`), or your Windows user folders (`/mnt/c/Users`).
  - `rm -rf`, force or mirror pushes, piping a download into a shell, running Windows `.exe` files, or using `tmux`/`systemd-run`.
  - Editing its own settings or launcher.
  - Using MCP connectors.
  - Switching to bypass mode, or retrying a command outside the sandbox.

Command-name rules (the `Bash(...)` deny and ask lists) stop the usual spelling of a command, not every possible form. The docs say so themselves (code.claude.com/docs/en/permissions#bash-rule-limits). The hard boundary is the sandbox, which is why it is in strict mode and why C7 matters.

## Settings key reference (`claude-settings.json`)

Every key was checked against the docs on 2026-10-10. JSON can't hold comments, so the explanations live here.

| Key | Value | What it does | Doc |
| --- | --- | --- | --- |
| `$schema` | schemastore URL | Editor autocomplete and validation only | https://code.claude.com/docs/en/settings |
| `env` | dotnet telemetry off, `UV_PYTHON=3.12` | Environment variables for every session and its subprocesses | https://code.claude.com/docs/en/settings-reference#env |
| `permissions.defaultMode` | `"default"` | Sessions start in normal ask-first mode | https://code.claude.com/docs/en/settings-reference#permissions-defaultmode |
| `permissions.disableBypassPermissionsMode` | `"disable"` | Nobody can enter `bypassPermissions`, and `--dangerously-skip-permissions` is rejected | https://code.claude.com/docs/en/settings-reference#permissions-disablebypasspermissionsmode |
| `permissions.allow` | `Read(~/src/**)`, `Read(~/logs/**)`, `Read(~/pc-setup/**)` | Lets Claude read the third-party checkouts, logs and this kit without a prompt | https://code.claude.com/docs/en/settings-reference#permissions-allow (path syntax: https://code.claude.com/docs/en/permissions#read-and-edit) |
| `permissions.ask` | push/fetch/pull/clone, network tools, package installs, `bash -c`, `WebFetch` | Always prompts, even for sandboxed commands | https://code.claude.com/docs/en/settings-reference#permissions-ask (wildcards: https://code.claude.com/docs/en/permissions#wildcard-patterns) |
| `permissions.deny` | see the groups below | Always blocks. Deny wins over ask and allow from any file. | https://code.claude.com/docs/en/settings-reference#permissions-deny (limits: https://code.claude.com/docs/en/permissions#bash-rule-limits) |
| `permissions.deny` `Bash(dangerouslyDisableSandbox:true)` | parameter rule | Refuses any request to run a command outside the sandbox | https://code.claude.com/docs/en/permissions#match-by-input-parameter |
| `permissions.deny` `mcp__*` | tool-name glob | Removes every MCP tool, so no claude.ai connectors (mail, calendar, drive) on this box. Delete the line if you ever want one. | https://code.claude.com/docs/en/permissions#tool-name-wildcards |
| `sandbox.enabled` | `true` | OS-level filesystem and network isolation for Bash | https://code.claude.com/docs/en/settings-reference#sandbox-enabled |
| `sandbox.failIfUnavailable` | `true` | Claude Code refuses to start rather than run unsandboxed | https://code.claude.com/docs/en/settings-reference#sandbox-failifunavailable |
| `sandbox.allowUnsandboxedCommands` | `false` | Strict mode: no "retry outside the sandbox" escape hatch | https://code.claude.com/docs/en/settings-reference#sandbox-allowunsandboxedcommands and https://code.claude.com/docs/en/sandboxing#turn-off-the-retry-with-strict-sandbox-mode |
| `sandbox.autoAllowBashIfSandboxed` | `true` (the default, set explicitly) | Sandboxed commands run without a prompt. Ask and deny rules still apply. | https://code.claude.com/docs/en/settings-reference#sandbox-autoallowbashifsandboxed |
| `sandbox.filesystem.allowWrite` | `~/code`, `~/src`, `~/logs`, `~/.venvs/spireline` | The only folders sandboxed commands may write, besides the per-session temp folder | https://code.claude.com/docs/en/settings-reference#sandbox-filesystem-allowwrite (prefixes: https://code.claude.com/docs/en/settings-reference#sandbox-path-prefixes) |
| `sandbox.filesystem.denyRead` | secrets, launcher state, `/mnt/c/Users` | Hidden from sandboxed commands at the OS level | https://code.claude.com/docs/en/settings-reference#sandbox-filesystem-denyread |
| `sandbox.network.allowAllUnixSockets` | `false` (the default, set explicitly) | Documents intent. On WSL, `true` would also reopen launching Windows programs. | https://code.claude.com/docs/en/settings-reference#sandbox-network-allowallunixsockets |

The deny list has these groups:
- **Destructive commands:** every forced recursive `rm`; recursive `rm` aimed at `/`, `~` or `$HOME`; `find -delete`; `shred`, `mkfs`, `dd of=/dev/...`.
- **Force pushes:** `git push --force`, `-f`, `+refspec` and `--mirror`.
- **Pipe-to-shell:** a bare `sh`/`bash`/`zsh`/`dash` at the end of a pipe, `-s`, `/dev/stdin`, `<(...)`, `eval`, `python -`. Claude Code splits pipelines and checks each part, so `curl ... | sh` is caught at the `sh`.
- **Privilege:** `sudo`, `su`, `doas`, `pkexec`, `runuser`.
- **Permissions:** `chmod 777` and `a+rwx`.
- **Secret reads:** `~/.ssh`, `~/.aws`, GitHub and git credentials, Claude's login token, `/mnt/c/Users`.
- **Edits to startup and tooling files:** shell rc files, systemd/autostart, Claude's settings, `~/pc-setup`, `~/.dotnet`, `~/.local/bin`, uv's Pythons, `/etc`, `/usr`.
- **Escape helpers:** `.exe`, `tmux`, `screen`, `systemd-run`, `systemctl`, `crontab`, `at`.

**Why `~/.venvs/spireline` is in `allowWrite`:** it is the Spireline venv by convention, so Claude can `uv sync` its own project. It goes beyond "only `~/code`, `~/src`, `~/logs`". Remove it if you want Claude unable to change that venv. In that case, keep the venv at `~/code/spireline/.venv` instead.

**Why the caches go to `~/code/.cache`:** `rc-launch.sh` sets `UV_CACHE_DIR`, `NUGET_PACKAGES`, `DOTNET_CLI_HOME`, `TORCH_HOME` and similar. Without that, uv and dotnet run by Claude would fail writing `~/.cache` and `~/.nuget`. Widening the sandbox to those folders would let Claude alter caches that your own unsandboxed builds later trust.

## Notes from preparing this kit

1. **What the kit runs upstream.**
   - The kit uses the emulator's own `scripts/build.sh` plus `dotnet test` and the Python suite (the HANDOFF commands), and never runs upstream setup or lint scripts.
   - Nothing is decompiled: `decompiled/` is gitignored upstream and the kit never creates it.
   - Never start a Claude session inside the `~/src` checkouts. The launcher always runs in `~/code`.
2. **Expect different test counts on the PC.**
   - The reference numbers are `HANDOFF.md:52,65` (C# 3650 + 1 skipped, Python 492 + 6 skipped) and `rl/FINDINGS.md:102-103` (4801/4801 and 526/527, the one failure being `TENDER_POWER`).
   - Tests that need `decompiled/` skip themselves: `tests/python/test_sweep_buff_map.py:142-143`, `test_live_enemy_ai.py:870,1118`, `test_live_selection.py:2199`, `test_run_train_live_replay.py:617-619`.
   - The `TENDER_POWER` test is inside that skipped block (`test_sweep_buff_map.py:139-150`), so the documented failure may not show up at all.
   - `scripts/audit_powers.py:36` also needs `decompiled/`. It runs in `lint-and-test.sh:61` but not in the HANDOFF smoke test (`HANDOFF.md:2929-2934`), so the kit doesn't run it.
3. **WSL sandbox gap.**
   - Without the optional seccomp filter, the Linux sandbox doesn't block Unix sockets (settings-reference, `allowAllUnixSockets`).
   - On WSL that includes the socket that launches Windows programs, outside the sandbox (sandboxing docs, "WSL2 notes"). Any reachable tmux server or systemd user bus can also start commands outside the sandbox.
   - The kit hides its own tmux socket and blocks those commands by name. CHECKLIST C7 turns interop off and asks you to decide on the filter.
4. **A repository's `.claude/settings.json` can loosen the sandbox.**
   - It can add `excludedCommands`, `allowWrite`, `allowedDomains` or `allowAllUnixSockets`, unless the sandbox is "admin-required" (code.claude.com/docs/en/sandboxing#repository-settings-under-an-admin-required-sandbox).
   - Making it admin-required takes managed settings at `/etc/claude-code/managed-settings.json` on Linux and WSL (code.claude.com/docs/en/managed-settings).
   - Optional hardening: `sudo install -D -m 644 ~/pc-setup/claude-settings.json /etc/claude-code/managed-settings.json`. After that, only `sudo` can change those rules.
   - Not done by default, because it also locks you out of quick edits.
5. **Toolchain facts.**
   - **.NET 9 end of support:** 2026-11-10, a month away (devblogs.microsoft.com/dotnet/dotnet-8-9-end-of-support/). The emulator targets `net9.0` (`Sts2Emulator.csproj:5`). That is fine for a pinned research build, but there are no security fixes after that date.
   - **CUDA 13 wheels:** the lock pins them (`uv.lock:200-201,759-760`), which needs an R580+ Windows driver. The first `uv sync` downloads about 2.7 GB of torch/CUDA wheels.
   - **Python 3.12:** `pyproject.toml:4` says `>=3.11`, but the code needs 3.12 (`scripts/desktop_setup.sh:66`, `HANDOFF.md:36-37`). The kit forces `UV_PYTHON=3.12`.

## Not verified yet (watch for these tomorrow)

- The meaning of Steam's `AutoUpdateBehavior` values (0 always, 1 on launch, 2 high priority). That is community convention, not Valve documentation, so spec-check says to confirm in the game's Properties.
- Whether `instanceIdleTimeout=-1` keeps the detached tmux alive after the `wsl.exe` that started it exits (C10). Check with `rc-launch.sh status` after a sign-in.
- Whether `claude remote-control` stops on one Ctrl-C or two. `rc-launch.sh stop` sends a second one, then kills the session if needed.
- Whether `--name` may be combined with `--continue`. The docs don't list them as incompatible, but the launcher doesn't combine them.
- Whether the Desktop app's "run in WSL" mode still works with WSL interop off.
- Whether `Register-ScheduledTask` with a logon trigger needs an Admin PowerShell.
- Whether NuGet tries to create `~/.nuget/NuGet/NuGet.Config` from inside the sandbox on a fresh box (T8 has the workaround).
- The R580 minimum for CUDA 13. Check NVIDIA's CUDA 13.0 release notes if the driver is close to it.

## Changing things later

- **Settings:** edit `~/.claude/settings.json` yourself. Claude can't, by design. Claude Code reloads it without a restart.
- **Allow a network host permanently:** add it to `sandbox.network.allowedDomains`.
- **Launcher options:** use environment variables (`RC_NAME`, `RC_DIR`, `RC_PERMISSION_MODE`, `RC_CAPACITY`, `RC_DEBUG=1`, `RC_PANE_LOG=1`) and see `rc-launch.sh help`.
