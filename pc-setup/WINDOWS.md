# Native Windows setup (no WSL)

Use this instead of `CHECKLIST.md` if you'd rather not install Linux. The emulator supports Windows directly: its Python loader expects `out\Sts2Emulator.dll`, and `scripts/build.sh` defaults to `win-x64`.

The trade-off is that Claude Code's sandbox only exists on Linux, WSL2 and macOS. On native Windows its commands run unsandboxed, so keep Claude Code in a mode that asks before commands, and keep credentials and personal files out of reach of this Windows account (or use a separate standard Windows user for it).

The examples use `D:\spireline` as the work folder. Any drive with about 30 GB free works.

## 1. You, in an Administrator PowerShell (5 min)

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0
powercfg /change monitor-timeout-ac 15
powercfg /hibernate off
```

`/hibernate off` also turns off Fast Startup and removes `hiberfil.sys`. Then, in a normal PowerShell, turn .NET telemetry off before the first `dotnet` call:

```powershell
setx DOTNET_CLI_TELEMETRY_OPTOUT 1
setx DOTNET_NOLOGO 1
```

Open a new terminal afterwards so the variables apply. Optional: Settings > Apps > App execution aliases, turn off the two `python` aliases so they can't open the Microsoft Store.

## 2. Toolchain (Claude can run these, with your approval)

```powershell
winget install --id Git.Git -e --source winget
winget install --id astral-sh.uv -e --source winget
uv python install 3.12
winget install --id Microsoft.DotNet.SDK.9 -e --source winget
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

- The emulator targets .NET 9 (`net9.0`), whatever the game's own files use. Install exactly one 9.0 SDK; don't add a `global.json`.
- Build Tools with the C++ workload provides the linker and Windows SDK that NativeAOT needs. Expect 5 to 8 GB and 10 to 20 minutes.
- Checks: `git --version`, `uv --version`, `dotnet --list-sdks` (one 9.0.x line), and
  `& "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`.
- Make sure there is no `Directory.Build.props`, `Directory.Build.targets`, `nuget.config` or `global.json` in `D:\spireline` or any parent folder, and that `%AppData%\NuGet\NuGet.Config` (if it exists) lists only nuget.org.

You don't need the separate CUDA Toolkit. PyTorch's CUDA wheels bring their own runtime; the Windows NVIDIA driver must be R580 or newer for CUDA 13.

## 3. The game (you, in Steam). The build doesn't need it.

- Install Slay the Spire 2.
- Properties > Updates: **Only update this game when I launch it**. Properties > General: turn off Steam Cloud on this PC.
- Check the build:
  ```powershell
  Select-String -Path "C:\Program Files (x86)\Steam\steamapps\appmanifest_2868840.acf" -Pattern '"buildid"'
  ```
  It should say `23811903` (v0.107.1, the build the emulator targets). If it doesn't, stop and report it; getting an exact older build needs a Steam depot download.
- Archive the install folder right away, for example `robocopy "C:\Program Files (x86)\Steam\steamapps\common\Slay the Spire 2" "D:\Archive\sts2-0.107.1-23811903" /E`.
- Don't install any mods yet. The STS2MCP mod waits for the live-game day.

## 4. Clone the pinned sources

```powershell
mkdir D:\spireline; cd D:\spireline
git clone https://github.com/microchimp/spireline
git clone https://github.com/r33hab/sts2 src\sts2
cd src\sts2
git checkout --detach b7452170ce1df91de29d3c94acb11d87c7efc708
git rev-parse "HEAD^{tree}"     # must be 7d5c4dfe31fa5d5e6f27c3adc8100ece50090fe4
git status --porcelain          # must print nothing
```

Refuse to build if either check fails. (For the live-game day later: r33hab/STS2MCP at `5a63f924f7e9dcbde4a1f70664e6d301c72e47c4`, tree `86f940c69836adeb553ba77db769bcf48a3d717f`. Don't build it yet.)

## 5. Never run these from the emulator repo

- `scripts/desktop_setup.sh`, `desktop_fight_job.sh`, `night_train.sh`, `fight_loop_rounds.sh`, `lint-and-test.sh`, `scripts/ralph/ralph.sh`
- `decompile.sh`, `patch_update.sh`, `patch_refresh.py --apply`
- any `capture_*`, `trace_real_game*`, `validate_real_game_*`, `combat_sweep`, `start_real_game_run` or `compare_draw_pile` script against a live game
- `bun install`, or anything under the mod repo's `mcp/` or `.claude/`

## 6. Build and test (Git Bash, from `D:\spireline\src\sts2`)

```bash
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
bash scripts/build.sh win-x64                 # produces out/Sts2Emulator.dll
dotnet test src/Sts2Emulator.Tests/           # upstream reports 3,650 pass + 1 skipped; takes several minutes
```

Python, into the checkout's own `.venv` only:

1. Before the first sync, check the pins in `uv.lock` against osv.dev for known vulnerabilities.
2. `uv sync --frozen --no-build`. The first run downloads about 2.7 GB of PyTorch CUDA wheels.
3. `uv run python -m unittest discover -s tests/python`. Upstream reports 492 pass + 6 skipped; expect more skips here, because `decompiled/` is absent.

Don't play games on the PC while the tests run; a few tests are timing-sensitive.

Record the results in `D:\spireline\versions.pc.lock` (it's gitignored): `dotnet --version`, the SHA-256 of `out\Sts2Emulator.dll` (`Get-FileHash out\Sts2Emulator.dll`), both test counts, and the commit and tree hashes above.

## 7. Benchmarks

Follow `spireline/bench/README.md`. It was written for Linux; run it from Git Bash and adapt any Linux-only commands. Write results under `bench/results/` and keep host names out of anything you commit.

## 8. Rules for code that drives the emulator

- One emulator instance per OS process; never call it from several Python threads.
- Every clone used by search or agent code passes `resample_hidden=1`.
- The debug and oracle exports (`Sts2_GetPile(0)`, `Sts2Run_GetStateList` 11 to 13, `Sts2_RngCallCount`, `Debug*`) are for verification code only.
- Run-level search waits until resampled run clones also redraw upcoming encounters, events and relic rewards. Today they keep the pre-rolled ones.

## Windows 10

Windows 10's paid security-update extension for home users ends on 13 October 2026. Before leaving an always-on agent running on this PC, consider the free in-place upgrade to Windows 11, which keeps apps and files. Ryzen 2000-series and newer CPUs are supported; it needs TPM 2.0 (AMD fTPM in the BIOS) and Secure Boot.
