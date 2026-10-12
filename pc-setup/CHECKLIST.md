# Spireline gaming PC setup: checklist

> **On native Windows (no WSL)?** Follow [WINDOWS.md](WINDOWS.md) instead of this checklist.

Do these steps in order. Total time is about 4 to 5 hours of your attention, plus about 2 hours of unattended benchmark time (part F). Steps E and F wait for your security-review decision. Everything here is done by you at the PC. Nothing in this kit has been run yet.

Placeholders: `<you>` is your Windows user name. `<ubuntu-user>` is the Linux user you create in B2.

Before you leave the Mac (10 min):
- [ ] With D0 (recommended), you need nothing from the Mac: `pc-setup/` ships inside the public repo at https://github.com/microchimp/spireline.
- [ ] Otherwise, copy this `pc-setup` folder to a USB stick (or a folder the PC can reach).
- [ ] If you pick D1, also make the bundle described there.

---

## A. Windows (about 75 min)

- [ ] **A1. Copy the kit (2 min).** Copy `pc-setup` to `C:\Users\<you>\spireline-pc-setup\`. With D0, take it from the public repo instead: on https://github.com/microchimp/spireline use Code > Download ZIP and extract its `pc-setup` folder there. Windows only needs `spec-check.ps1`; B3 takes the Linux copy from the clone.

- [ ] **A2. Run the spec check (5 min).** In PowerShell (no admin needed):
  ```powershell
  cd $env:USERPROFILE\spireline-pc-setup
  powershell -NoProfile -ExecutionPolicy Bypass -File .\spec-check.ps1 | Tee-Object -FilePath "$env:USERPROFILE\Desktop\spec-check.txt"
  ```
  `-ExecutionPolicy Bypass` applies to that one process only. The script changes nothing. Keep `spec-check.txt`: B1 needs its suggested `.wslconfig`, and F needs the CPU line. Read the warnings at the end.

- [ ] **A3. Never sleep on mains power (5 min).** In an **Admin** PowerShell:
  ```powershell
  powercfg /change standby-timeout-ac 0
  powercfg /change hibernate-timeout-ac 0
  powercfg /change disk-timeout-ac 0
  powercfg /change monitor-timeout-ac 15
  powercfg /hibernate off
  ```
  The monitor may still turn off. `/hibernate off` also turns off Fast Startup. Check that A2's "Sleep after (AC)" and "Hibernate after (AC)" now say `never`. Optional: in Device Manager, open your network adapter > Power Management and untick "Allow the computer to turn off this device". Optional: in the BIOS, set "Restore on AC power loss" to On.

- [ ] **A4. Windows Update active hours (5 min).** Go to Settings > Windows Update > Advanced options > Active hours > Manually. Pick the widest window you are likely to use the PC (up to 18 h). Leave "Get me up to date" off. If you start a long run, you can also use "Pause updates". On the Home edition, Group Policy can't block restarts, so after any reboot use C10 or start `rc-launch.sh` by hand.

- [ ] **A5. NVIDIA driver (15 to 25 min, with a reboot).** Install the current GeForce driver on **Windows** from the NVIDIA App or nvidia.com. Get R580 or newer. The torch 2.12 wheels pinned in r33hab/sts2 `uv.lock` are CUDA 13.0 (`uv.lock:200-201`, `:759-760`), and CUDA 13 needs an R580+ driver. Inside WSL, CUDA uses this Windows driver. **Never install an NVIDIA or CUDA driver inside Ubuntu.** Reboot, then re-run A2 and confirm `nvidia-smi` shows the new version.

- [ ] **A6. Steam and the game (15 to 25 min).**
  - Library > right-click Slay the Spire 2 > Properties > Updates > Automatic updates: **Only update this game when I launch it**.
  - Properties > General: turn **off** "Keep game saves in the Steam Cloud".
  - Check the build: re-run A2. It should print `buildid 23811903` and `Build check MATCH`, and `AutoUpdateBehavior 1`. To check by hand: `Select-String -Path "<library>\steamapps\appmanifest_2868840.acf" -Pattern '"buildid"'`.
  - If A2 warns about a queued update (`TargetBuildID`), or the buildid is not 23811903, **don't launch the game from Steam**. See troubleshooting T6.
  - Back up with the game closed. Pick a drive with room for the "Game folder size" A2 printed:
    ```powershell
    robocopy "$env:APPDATA\SlayTheSpire2" "D:\Backups\sts2-saves-2026-10-11" /E
    robocopy "<library>\steamapps\common\Slay the Spire 2" "D:\Archive\sts2-0.107.1-23811903" /E
    copy "<library>\steamapps\appmanifest_2868840.acf" "D:\Archive\sts2-0.107.1-23811903\"
    ```
    Robocopy exit codes 0 to 7 mean success. Save the `sts2.dll sha256` line from A2 next to the archive.

- [ ] **A7. Git for Windows (5 min).** Run `winget install --id Git.Git -e --source winget`, or use the installer from git-scm.com. The Claude Code docs recommend it on Windows.

- [ ] **A8. Claude Desktop app (5 min).** Install from claude.ai/download and sign in with the same claude.ai account you use on the phone. Use it for chat and Dispatch. **Don't run coding sessions natively on Windows for this project.** The Claude Code sandbox doesn't exist on native Windows: commands there run unsandboxed (code.claude.com/docs/en/sandboxing). So leave Settings > Claude Code > "Connect new sessions to Remote Control" off. Coding happens in the WSL server from part C.

## B. WSL2 (about 30 min, plus a possible reboot)

- [ ] **B1. Write `%UserProfile%\.wslconfig` first (5 min).** `sparseVhd` only affects virtual disks created after it is set, so this file must exist before you install Ubuntu. Paste the "Suggested .wslconfig" block from `spec-check.txt` into `C:\Users\<you>\.wslconfig`. It has this shape:
  ```ini
  [wsl2]
  # RAM for the Linux VM. Leave 6-12 GB (about a quarter) for Windows, Steam and the Desktop app.
  memory=24GB
  # Logical processors for the VM. Leave 2 for Windows so the desktop stays usable during runs.
  processors=14
  # Disk-backed overflow, so a big build or test run slows down instead of being killed.
  swap=8GB

  [general]
  # Do not shut the Linux instance down when no terminal is open (keeps the rc-launch tmux alive).
  instanceIdleTimeout=-1

  [experimental]
  # Give cached memory back to Windows gradually instead of dropping it all at once.
  autoMemoryReclaim=gradual
  # New virtual disks shrink when files inside are deleted.
  sparseVhd=true
  ```
  Put comments on their own lines. The Microsoft example uses whole-line `#` comments only. Leave `networkingMode` at the default (NAT) for now. `networkingMode=mirrored` is needed later, on the live-coach day, but only if code in WSL must reach the game mod's API on Windows `127.0.0.1:15526` (r33hab/sts2 `HANDOFF.md:143`). The mod binds localhost only. Mirrored mode needs Windows 11 22H2+. Key reference: learn.microsoft.com/windows/wsl/wsl-config.

- [ ] **B2. Install Ubuntu 24.04 (15 min).** In an **Admin** PowerShell:
  ```powershell
  wsl --install -d Ubuntu-24.04
  ```
  Reboot if asked. The Ubuntu window then asks for a Linux user name and password. That password is what `sudo apt` asks for. Then run:
  ```powershell
  wsl --update
  wsl -l -v          # Ubuntu-24.04 must show VERSION 2
  ```
  If it shows 1: `wsl --set-version Ubuntu-24.04 2`. The sandbox needs WSL2, not WSL1.

- [ ] **B3. Copy the kit into Linux (3 min).** In Ubuntu, with D0 (Ubuntu ships `git`; `~/pc-setup` must not exist yet, or `cp -r` nests the folder):
  ```bash
  git clone https://github.com/microchimp/spireline ~/code/spireline     # this is D0
  cp -r ~/code/spireline/pc-setup ~/pc-setup && cd ~/pc-setup && sha256sum -c SHA256SUMS
  ```
  Without D0, from the copy made in A1:
  ```bash
  mkdir -p ~/pc-setup && cp /mnt/c/Users/<you>/spireline-pc-setup/* ~/pc-setup/
  chmod 755 ~/pc-setup/*.sh
  cd ~/pc-setup && sha256sum -c SHA256SUMS     # every line must say OK
  ```
  Against a clone, `sha256sum -c` catches a damaged or edited copy; the checksums come from the same repo, so it does not prove who published it.
  Keep the kit in `~/pc-setup`, outside `~/code`. The settings deny Claude any edits there, so Claude can't rewrite its own launcher.

## C. Inside WSL (about 75 min)

- [ ] **C1. Bootstrap (15 to 25 min).** Run `bash ~/pc-setup/wsl-bootstrap.sh`. It asks for your Linux password once, for apt only. Read its summary. Every `WARN` line names the step that fixes it. Then open a new Ubuntu window, or run `source ~/.bashrc`.

- [ ] **C2. Only if C1 printed the AppArmor warning (5 min).** These commands come from code.claude.com/docs/en/sandboxing, "Ubuntu 24.04 and later":
  ```bash
  sudo tee /etc/apparmor.d/bwrap > /dev/null <<'EOF'
  abi <abi/4.0>,
  include <tunables/global>

  profile bwrap /usr/bin/bwrap flags=(unconfined) {
    userns,
    include if exists <local/bwrap>
  }
  EOF
  sudo systemctl reload apparmor
  ```
  Re-run `bash ~/pc-setup/wsl-bootstrap.sh`. The bwrap smoke test should now say OK.

- [ ] **C3. Install Claude Code (3 min).**
  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  claude --version && claude doctor
  ```

- [ ] **C4. Install the PC settings before the first session (2 min).**
  ```bash
  mkdir -p ~/.claude && install -m 600 ~/pc-setup/claude-settings.json ~/.claude/settings.json
  ```
  `~/.claude/settings.json` is the user settings file (code.claude.com/docs/en/settings). If one already exists, merge the two by hand instead of overwriting. With `sandbox.failIfUnavailable` on, Claude Code refuses to start if the sandbox can't. That is intended. Fix it with C2 or T3.

- [ ] **C5. First session: login, sandbox, notifications (15 min).**
  ```bash
  cd ~/code && claude
  ```
  - `/login`: sign in with your **claude.ai** account. Remote Control doesn't accept API keys. Trust `~/code` when asked.
  - `/sandbox`: there should be no Dependencies-only screen. The Overrides tab should show strict sandbox mode (`allowUnsandboxedCommands: false`). An optional "seccomp filter" note on the Dependencies tab is expected; C7 decides it.
  - Ask Claude to run `touch ~/sandbox-probe`. Expect `Read-only file system`, the Linux/WSL2 result listed in the sandboxing docs.
  - Ask it to run `cat ~/.ssh/known_hosts`. Expect a denial.
  - `/config`: turn on **Push when actions required** (permission prompts reach your phone) and, if you like, **Push when Claude decides**.
  - `/exit`.

- [ ] **C6. First Remote Control run, interactively (10 min).**
  ```bash
  cd ~/code && claude remote-control --name gaming-pc
  ```
  Answer `y` to `Enable Remote Control? (y/n)`, then `y` to `Trust /home/<ubuntu-user>/code? [y/N]`. Both questions come only once. Trust is never saved for your home folder, which is why the launcher uses `~/code`. Press space for the QR code. On the phone, open the Claude app > **Code** and check that the `gaming-pc` session is listed. Send it "which folder are you in?". Then press Ctrl-C here.

- [ ] **C7. Close the remaining sandbox gaps (10 min, recommended).** On Linux and WSL2, the sandbox blocks Unix-socket connections only when its optional seccomp filter is installed. Without the filter, sandboxed commands can open Unix sockets freely (code.claude.com/docs/en/settings-reference#sandbox-network-allowallunixsockets). On WSL, launching a Windows program goes over such a socket and runs **outside** the Linux sandbox (sandboxing docs, "WSL2 notes").
  1. Turn off WSL interop. Do this after C5's `/login`, because the browser hand-off uses interop. Run `sudo nano /etc/wsl.conf`, keep what is there (for example `[boot] systemd=true`), and add:
     ```ini
     [interop]
     enabled=false
     appendWindowsPath=false
     ```
     In PowerShell, run `wsl --shutdown`, wait 10 s, and reopen Ubuntu. To check: `cmd.exe /c ver` must now fail. Side effects: `explorer.exe`, `code .`, `clip.exe` and browser hand-off no longer work from Linux. `wsl.exe` from Windows into Linux still works, so C10 is fine.
  2. Decide on the seccomp filter. It closes the rest of the gap, such as the systemd user bus (`systemd-run --user`). The docs install it with `npm install -g @anthropic-ai/sandbox-runtime`, which needs Node.js in WSL. It is Anthropic's package, but it is still new code on the box. Your call. If you skip it, the kit already puts the launcher's tmux socket where sandboxed commands can't read it, and deny rules block `tmux`, `systemd-run` and `systemctl` by name. The deny rules are not a security boundary. Optionally set `[boot] systemd=false` in `/etc/wsl.conf` to remove the user bus too. Nothing in this kit needs systemd, and C2 would then become moot.

- [ ] **C8. Start the always-on launcher (5 min).**
  ```bash
  ~/pc-setup/rc-launch.sh          # starts tmux session spireline-rc and attaches
  ```
  The first start shows `[rc-launch] ... starting (fresh)`, because the launcher has no record of C6. C6 ran in the same folder less than four hours ago, so per the Remote Control docs a plain `claude remote-control` there brings C6's session back as well. Later restarts within 3.5 h show `starting (continue)`. Detach with Ctrl-b then d. Later you can use `rc-launch.sh status | attach | restart | fresh | stop`. The log is `~/logs/rc.log`.

- [ ] **C9. Phone tests (10 min).** From the Claude app > Code > gaming-pc:
  - [ ] "list the files in ~/code": it answers.
  - [ ] "run `curl -sI https://example.com`": a push notification asks for permission. **Deny** it.
  - [ ] "show me ~/.ssh": refused.
  - [ ] On the PC, run `~/pc-setup/rc-launch.sh restart`. Within about a minute the same session answers again on the phone.

- [ ] **C10. Optional: start the launcher at Windows sign-in (10 min).** In PowerShell:
  ```powershell
  $a = New-ScheduledTaskAction -Execute 'wsl.exe' -Argument '-d Ubuntu-24.04 -- bash -lc ~/pc-setup/rc-launch.sh'
  $t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
  Register-ScheduledTask -TaskName 'Spireline Remote Control' -Action $a -Trigger $t -Settings $s
  ```
  If it says access denied, run it in an Admin PowerShell. It only runs once you sign in. Windows auto sign-in would make it fully unattended after an update reboot, but weakens the PC's security. That is your choice. After the first reboot, check `rc-launch.sh status`. Keeping the instance alive relies on `instanceIdleTimeout=-1` from B1, which is untested here.

## D. Bring the Spireline repo over (5 to 30 min). **You choose one option. Don't let anyone assume.**

The Mac repo is `~/Documents/code/spireline` (design section 10). On the PC it goes to `~/code/spireline`. The security review comes with it, at `docs/SECURITY_REVIEW.md` (see E1).

- [ ] **D0. RECOMMENDED: clone the public repo.** `git clone https://github.com/microchimp/spireline ~/code/spireline` (already done if you used D0 in B3). No credentials and nothing to carry over, and `pc-setup/` ships inside it, so A1 and B3 can take the kit from the clone: `cp -r ~/code/spireline/pc-setup ~/pc-setup && cd ~/pc-setup && sha256sum -c SHA256SUMS`. Updates come down with `git pull`, which you run yourself. It is one-way: the PC holds no credential to push with, so use D1 or D2 below if results must go back as commits. Keep machine-specific files (bench results, `versions.pc.lock`, `spec-check.txt`) out of the public repo, because they hold host names and paths; `.gitignore` already excludes `bench/results/`, `versions.lock` and `versions.pc.lock`. If the public repo is not reachable yet, use D1.

For two-way sync, use D1 or D2:

- [ ] **D1. Option 1: git bundle over USB or a LAN share.** No third party, and no credentials on the PC. Syncing is manual in both directions.
  - Mac:
    ```bash
    cd ~/Documents/code/spireline && git status --short     # commit first
    git bundle create ~/Desktop/spireline-$(date +%Y%m%d).bundle --all
    git bundle verify ~/Desktop/spireline-*.bundle && shasum -a 256 ~/Desktop/spireline-*.bundle
    ```
  - Copy the file to `C:\Users\<you>\Downloads\`, by USB stick or a Windows shared folder opened from Finder with Cmd-K `smb://<pc-name>`.
  - WSL:
    ```bash
    cp /mnt/c/Users/<you>/Downloads/spireline-*.bundle ~/ && sha256sum ~/spireline-*.bundle   # compare
    git bundle verify ~/spireline-*.bundle
    git clone ~/spireline-YYYYMMDD.bundle ~/code/spireline
    ```
  - To bring results back, make a bundle on the PC (`git bundle create ~/code/pc-results.bundle --all`) and `git fetch` from it on the Mac.
- [ ] **D2. Option 2: a PRIVATE GitHub repo.** Easy two-way sync, but the code sits on GitHub, and the PC needs a credential.
  - You create the repo in the GitHub web UI (private) and push from the Mac.
  - On the PC, use a fine-grained token limited to that one repository, or a repo-scoped deploy key. The settings hide `~/.git-credentials`, `~/.config/gh` and `~/.ssh` from Claude's sandboxed commands. So a push from inside Claude's sandbox can't find the credential: Claude commits, and you run `git push` yourself. Store the token with git's `store` helper or `gh`, not `credential-cache`: sandboxed commands can reach the cache's socket unless the seccomp filter from C7 is installed. `git fetch`/`pull`/`push` also ask for permission by rule.
- (A third option, not prepared here: `git clone ssh://<you>@<mac>.local/...` straight from the Mac. This needs Remote Login turned on on the Mac and an SSH key on the PC.)

Optional: copy any private notes you keep outside the repo (design, research) to `~/code/` for reference. They stay out of the public repo.

## E. Emulator: only after reading SECURITY_REVIEW.md and deciding (45 to 90 min, mostly unattended)

- [ ] **E1. Read the review and decide (15 to 30 min).** Read `~/code/spireline/docs/SECURITY_REVIEW.md` and decide. If the verdict is fallback or no-go, stop here and follow design section 3.6 step 5. The review covers only the pinned commits.
- [ ] **E2. Clone the pinned commits (5 min).** Run `bash ~/pc-setup/clone-pinned.sh`. It fetches r33hab/sts2 @ `b7452170ce1df91de29d3c94acb11d87c7efc708` and r33hab/STS2MCP @ `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4` into `~/src`. It checks both commit and tree hashes and builds nothing. `clone-pinned.sh` may print a NOTE listing tracked agent/config files; never start a Claude session with `~/src/STS2MCP` as its folder.
- [ ] **E3. Build and test (30 to 60 min).** Run `bash ~/pc-setup/build-emulator.sh [path/to/SECURITY_REVIEW.md]` in your own terminal, not through Claude. If it finds the review (at the default path, or the path you pass), it prints the verdict line. If not, it prints a note asking you to read the review first. Either way it waits for you to type `GO`. It then runs the repo's `scripts/build.sh linux-x64`, `dotnet test` and the Python suite, and writes `~/src/versions.lock`. The first run downloads NuGet packages and about 2.7 GB of torch/CUDA wheels.
- [ ] **E4. Check and record (10 min).** Compare the counts with `HANDOFF.md` (C# 3650 + 1 skipped, Python 492 + 6 skipped) and `rl/FINDINGS.md` (4801/4801, 526/527). Expect more Python skips here, because `decompiled/` is absent. Then run `cp ~/src/versions.lock ~/code/spireline/versions.pc.lock`. That file is gitignored, because it holds this machine's host name and paths: keep it local and bring it back to the Mac with the other results, never in the public repo.

## F. Day-4 benchmarks (about 2 h, unattended)

- [ ] Follow `~/code/spireline/bench/README.md`. On the Mac it is `~/Documents/code/spireline/bench/README.md`. It is written separately; if it isn't there yet, use the day-4 list in the design, section 10, item 5.
- PC differences: run it inside tmux, either by asking Claude from the phone or with your own `tmux new -s bench`, not `caffeinate`. Name the output for this machine, for example `bench/pc-3080ti-2026-10.json`, and attach `spec-check.txt`. Check both for host names, user names and paths before anything from this run goes into the public repo. The emulator is CPU-only, so the GPU stays idle. Don't play games on the PC during the run: the C# suite and the probes are sensitive to other load (`HANDOFF.md:91-98`). For a hybrid Intel CPU, record the P-core and E-core counts by hand, because spec-check reports totals.

---

## Troubleshooting

- **T1. `bash: $'\r': command not found`, or `sha256sum -c` fails.** A Windows tool or editor changed the files, usually by adding CRLF line endings. Copy them again straight from the USB stick without opening them, and `sha256sum -c SHA256SUMS` must then pass. As a last resort, `sed -i 's/\r$//' ~/pc-setup/*.sh` fixes the line endings, but the checksums will then differ.
- **T2. `running scripts is disabled on this system`.** Use the full `powershell -NoProfile -ExecutionPolicy Bypass -File ...` command from A2.
- **T3. Claude Code exits at startup about the sandbox.** Run `bash ~/pc-setup/wsl-bootstrap.sh` again and read the sandbox section. Check that `bubblewrap` and `socat` are installed, that the C2 AppArmor profile is in place, and that `wsl -l -v` shows VERSION 2. Restart Claude Code after installing packages.
- **T4. `Workspace not trusted` in `~/logs/rc.log`.** C6 was skipped, or `RC_DIR` points at a new folder. Run `claude remote-control` once interactively in that folder.
- **T5. The phone doesn't show gaming-pc.** Run `~/pc-setup/rc-launch.sh status` and `tail ~/logs/rc.log`. After a network outage of 10 minutes or more, server mode exits and the loop restarts it. If a resumed session misbehaves, run `rc-launch.sh fresh`. "Remote Control requires a claude.ai subscription" or a full-scope token error means you need to `/login` again with claude.ai, not an API key, and unset `ANTHROPIC_API_KEY` and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`.
- **T6. buildid is not 23811903.** Don't launch through Steam, because it would install the update. The emulator build (E) doesn't need the game, so carry on with it. Keep the A6 archive. Patch-day policy is in design section 3.5.
- **T7. No push notifications.** In `/config`, check "Push when actions required". If it says "No mobile registered", open the Claude app once. On Android, exempt the app from battery optimisation.
- **T8. A sandboxed command fails with `Read-only file system`.** It wrote outside `~/code`, `~/src`, `~/logs` or `~/.venvs/spireline`. That is the design. The launcher already points the uv, NuGet, dotnet and torch caches into `~/code/.cache`. For an interactive `claude`, run `eval "$(~/pc-setup/rc-launch.sh env)"` first. NuGet may also want to create `~/.nuget/NuGet/NuGet.Config` the first time: run E3 (or one `dotnet restore`) yourself first.
- **T9. A new host prompts on every command.** Approve it on the phone, or add it to `sandbox.network.allowedDomains` in `~/.claude/settings.json`. Package registries such as `pypi.org`, `files.pythonhosted.org` and `api.nuget.org` are the usual ones.
- **T10. `nvidia-smi` is missing inside WSL.** Update the Windows driver (A5), run `wsl --update` and `wsl --shutdown` from PowerShell, and reopen Ubuntu. Don't install a Linux NVIDIA driver.
- **T11. `uv sync --locked` fails in E3.** The lockfile and the project disagree. Don't run `uv lock`, because it changes the pins. Note the error for the review.
- **T12. The C# suite is slow, or two timing tests fail.** The suite runs serially (`HANDOFF.md:82-103`). Check `uptime` for other load first. `scripts/desktop_setup.sh:81-82` names the two timing tests that can fail on a busy machine.
- **T13. After a killed session, 0-byte read-only files appear at `.claude` settings paths.** These are leftover sandbox placeholders (sandboxing docs, troubleshooting). Delete them yourself.
