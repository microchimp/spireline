#!/usr/bin/env bash
# build-emulator.sh -- gated build and test of the pinned r33hab/sts2 emulator on Linux (WSL2).
#
# What it does, in order:
#   1. Security-review gate. With a review file (passed as the first argument, or found at the
#      default path) it prints the review's verdict line(s). Without one it prints a note that
#      the review is private and lives on the Mac. Either way it waits for you to type GO.
#   2. Re-checks that ~/src/sts2 is still the pinned, clean checkout (commit + tree hash).
#   3. Builds the NativeAOT library with the repo's own script:  bash scripts/build.sh linux-x64
#      (scripts/build.sh:10-28 -> dotnet publish src/Sts2Emulator/Sts2Emulator.csproj -c Release
#       -r linux-x64 --self-contained -o out/  ->  out/Sts2Emulator.so, the name
#       src/sts2_gym/native.py:13 loads on Linux)
#   4. Runs the C# suite:      dotnet test src/Sts2Emulator.Tests/Sts2Emulator.Tests.csproj --nologo
#      (lint-and-test.sh:68; HANDOFF.md:53)
#   5. Runs the Python suite:  uv sync --locked, then
#                              uv run --locked python -m unittest discover -s tests/python
#      (HANDOFF.md:65; it drives out/Sts2Emulator.so through ctypes, so it runs after the build)
#   6. Writes test counts, the library's sha256 and tool versions to versions.lock.
#
# Decompiling is NOT part of this: build.sh and Sts2Emulator.csproj never reference decompiled/
# or the game; the game data the build needs is committed as src/Sts2Emulator/Generated/*.g.cs.
# Python tests that need decompiled/ skip themselves when it is absent, so expect more skips
# than HANDOFF.md reports (it was written on a machine that had decompiled/).
#
# Usage:  bash ~/pc-setup/build-emulator.sh [path/to/SECURITY_REVIEW.md]
#         default review path: ~/code/spireline/docs/SECURITY_REVIEW.md (gitignored: the review is
#         private and is NOT in the public repo, so on a fresh clone it is normally absent)
# Environment (optional): EMU_DIR=~/src/sts2  MOD_DIR=~/src/STS2MCP  VERSIONS_LOCK=~/src/versions.lock
# Run it yourself, in a terminal. It refuses to run without one, so an agent cannot type GO for you.
set -euo pipefail

REVIEW_ARG="${1:-}"
REVIEW="${REVIEW_ARG:-$HOME/code/spireline/docs/SECURITY_REVIEW.md}"
EMU="${EMU_DIR:-$HOME/src/sts2}"
MOD="${MOD_DIR:-$HOME/src/STS2MCP}"
LOCK="${VERSIONS_LOCK:-$HOME/src/versions.lock}"
EMU_COMMIT=b7452170ce1df91de29d3c94acb11d87c7efc708
EMU_TREE=7d5c4dfe31fa5d5e6f27c3adc8100ece50090fe4
MOD_COMMIT=5a63f924f7e9dcbde4a1f70664e6d301c72e47c4
MOD_TREE=86f940c69836adeb553ba77db769bcf48a3d717f
RID=linux-x64
LIB="$EMU/out/Sts2Emulator.so"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOGDIR="$HOME/logs/build-emulator-$STAMP"

die() { printf '\nSTOPPED: %s\n' "$*" >&2; exit 1; }
hr() { printf '\n== %s\n' "$*"; }
sha() { sha256sum "$1" | awk '{print $1}'; }

[ "$(id -u)" -ne 0 ] || die "run as your normal user, not root"
[ -t 0 ] && [ -t 1 ] || die "run this in a terminal yourself: it needs a person to type GO"
mkdir -p "$LOGDIR"

# ------------------------------------------------------------------ 1. review gate
hr "1/6 security review"
need=GO
if [ -n "$REVIEW_ARG" ] && [ ! -f "$REVIEW" ]; then
  die "no review at $REVIEW (the path you passed). Fix the path, or run without an argument."
fi
if [ -f "$REVIEW" ]; then
  have_review=1
  review_sha="$(sha "$REVIEW")"
  n="$(grep -n -m1 -iE '^[[:space:]>*_#-]*(verdict|decision)\b' "$REVIEW" | cut -d: -f1 || true)"
  if [ -z "$n" ]; then
    echo "First lines of $REVIEW:"; head -n 15 "$REVIEW" | sed 's/^/  | /'
    die "no line starting with 'Verdict' or 'Decision' in the review. The review must state its verdict before anything is built."
  fi
  verdict="$(sed -n "${n},$((n + 3))p" "$REVIEW")"
  echo "Review:  $REVIEW"
  echo "sha256:  $review_sha"
  echo "Verdict (line $n):"
  printf '%s\n' "$verdict" | sed 's/^/  | /'
  if grep -qiE 'no[ -]?go|fallback|reject|blocked|not approved|do not (build|proceed|run)' <<<"$verdict"; then
    echo
    echo "!! The verdict text looks negative (no-go / fallback / reject / blocked)."
    echo "!! The design's fallback is evangambit/sts2 + cicero225 STS2MCP (design section 3.6, step 5)."
    need="GO ANYWAY"
  fi
  verdict_line="$(sed -n "${n}p" "$REVIEW" | tr -d '\r' | sed 's/"/\\"/g')"
else
  have_review=0
  review_sha="n/a"
  verdict_line="not shown: no review file on this PC"
  cat <<NOTE
NOTE: there is no SECURITY_REVIEW.md on this PC (looked for $REVIEW).
      That is expected. The security review of the pinned third-party code is private: it
      lives on the Mac and is not in the public Spireline repo. Read its verdict there
      before you go on. This script cannot show or check that verdict for you.
      To show the verdict line here, copy the review over yourself and pass its path:
        bash ~/pc-setup/build-emulator.sh /path/to/SECURITY_REVIEW.md
      If the verdict is no-go or fallback, stop now (CHECKLIST E1).
NOTE
fi
echo
if [ "$have_review" = 1 ]; then
  prompt="Type ${need} to build and test the emulator (anything else stops): "
else
  prompt="Type ${need} only if you have read the review's verdict on the Mac and it allows this build (anything else stops): "
fi
read -r -p "$prompt" answer
[ "$answer" = "$need" ] || die "not confirmed; nothing was built"

# ------------------------------------------------------------------ 2. pins
hr "2/6 pinned checkout"
[ -d "$EMU/.git" ] || die "$EMU is missing; run clone-pinned.sh first"
head="$(git -C "$EMU" rev-parse HEAD)"
tree="$(git -C "$EMU" rev-parse 'HEAD^{tree}')"
[ "$head" = "$EMU_COMMIT" ] || die "$EMU HEAD is $head, expected $EMU_COMMIT"
[ "$tree" = "$EMU_TREE" ] || die "$EMU tree is $tree, expected $EMU_TREE"
dirty="$(git -C "$EMU" status --porcelain --untracked-files=all)"
[ -z "$dirty" ] || { printf '%s\n' "$dirty" | head -20; die "$EMU has local changes (above); build only the reviewed code"; }
echo "emulator $EMU_COMMIT (tree $EMU_TREE), clean"
mod_state="not cloned"
if [ -d "$MOD/.git" ]; then
  if [ "$(git -C "$MOD" rev-parse HEAD)" = "$MOD_COMMIT" ] && [ "$(git -C "$MOD" rev-parse 'HEAD^{tree}')" = "$MOD_TREE" ]; then
    mod_state="pinned"
  else
    mod_state="NOT at the pinned commit"
  fi
fi
echo "mod      $MOD: $mod_state (recorded only; the mod is not built here)"

# ------------------------------------------------------------------ 3. toolchain + build
hr "3/6 toolchain and build ($RID)"
# The same environment desktop_setup.sh:65-66 and HANDOFF.md:43-44 set up.
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.local/bin:$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
export PYTHONUTF8=1 LANG=C.UTF-8 UV_PYTHON=3.12   # the code needs 3.12 (desktop_setup.sh:66)
command -v dotnet >/dev/null || die "dotnet not found in ~/.dotnet (run wsl-bootstrap.sh)"
dotnet --list-sdks | grep -qE '^9\.0\.' || die "no .NET 9 SDK (run wsl-bootstrap.sh)"
command -v clang >/dev/null || die "clang missing: NativeAOT needs it (run wsl-bootstrap.sh)"
command -v uv >/dev/null || die "uv missing (run wsl-bootstrap.sh)"
uv python find 3.12 >/dev/null 2>&1 || die "Python 3.12 not installed for uv (run wsl-bootstrap.sh)"

run_logged() { # logfile cmd... -> runs cmd, tees output, returns cmd's exit code
  local log=$1 rc; shift
  set +e
  "$@" 2>&1 | tee "$log"
  rc=${PIPESTATUS[0]}
  set -e
  return "$rc"
}

echo "NuGet restore downloads packages from nuget.org on the first build."
build_rc=0
run_logged "$LOGDIR/build.log" bash -c 'cd "$1" && bash scripts/build.sh "$2"' _ "$EMU" "$RID" || build_rc=$?
[ "$build_rc" -eq 0 ] || die "build failed (exit $build_rc); log: $LOGDIR/build.log"
[ -f "$LIB" ] || die "build finished but $LIB is missing"
lib_sha="$(sha "$LIB")"
echo "built $LIB  sha256 $lib_sha"

# ------------------------------------------------------------------ 4. C# tests
hr "4/6 C# tests (serial suite; HANDOFF.md says ~2 min on a quiet machine)"
cs_rc=0
run_logged "$LOGDIR/dotnet-test.log" bash -c 'cd "$1" && dotnet test src/Sts2Emulator.Tests/Sts2Emulator.Tests.csproj --nologo --logger "trx;LogFileName=csharp.trx" --results-directory "$2"' _ "$EMU" "$LOGDIR" || cs_rc=$?
cs_total="" cs_passed="" cs_failed="" cs_skipped=""
trx="$(find "$LOGDIR" -name '*.trx' -print -quit)"
if [ -n "$trx" ] && counters="$(grep -o '<Counters [^>]*>' "$trx" | head -1)" && [ -n "$counters" ]; then
  attr() { sed -n "s/.* $1=\"\([0-9]*\)\".*/\1/p" <<<"$counters"; }
  cs_total="$(attr total)"; cs_passed="$(attr passed)"; cs_failed="$(attr failed)"
  executed="$(attr executed)"
  [ -n "$cs_total" ] && [ -n "$executed" ] && cs_skipped=$((cs_total - executed))
else
  line="$(grep -E '(Passed|Failed)! +- +Failed: +[0-9]+' "$LOGDIR/dotnet-test.log" | tail -1 || true)"
  cs_failed="$(sed -n 's/.*Failed: *\([0-9]*\),.*/\1/p' <<<"$line")"
  cs_passed="$(sed -n 's/.*Passed: *\([0-9]*\),.*/\1/p' <<<"$line")"
  cs_skipped="$(sed -n 's/.*Skipped: *\([0-9]*\),.*/\1/p' <<<"$line")"
  cs_total="$(sed -n 's/.*Total: *\([0-9]*\),.*/\1/p' <<<"$line")"
fi
echo "C#: total=${cs_total:-?} passed=${cs_passed:-?} failed=${cs_failed:-?} skipped=${cs_skipped:-?} (exit $cs_rc)"

# ------------------------------------------------------------------ 5. Python tests
hr "5/6 Python tests (first run downloads ~2.7 GB of torch/CUDA wheels pinned in uv.lock)"
sync_rc=0
run_logged "$LOGDIR/uv-sync.log" bash -c 'cd "$1" && uv sync --locked' _ "$EMU" || sync_rc=$?
[ "$sync_rc" -eq 0 ] || die "uv sync --locked failed (exit $sync_rc). Do NOT run 'uv lock' (that changes the pins). Log: $LOGDIR/uv-sync.log"
py_rc=0
run_logged "$LOGDIR/python-test.log" bash -c 'cd "$1" && uv run --locked python -m unittest discover -s tests/python' _ "$EMU" || py_rc=$?
py_ran="$(grep -E '^Ran [0-9]+ tests? in' "$LOGDIR/python-test.log" | tail -1 | awk '{print $2}' || true)"
py_result="$(grep -E '^(OK|FAILED)( \(|$)' "$LOGDIR/python-test.log" | tail -1 || true)"
# unittest summary looks like "FAILED (failures=1, errors=2, skipped=9, expected failures=1)"
pyv() { sed -nE "s/.*(\(|, )$1=([0-9]+).*/\2/p" <<<"$py_result"; }
py_fail="$(pyv failures)"; py_err="$(pyv errors)"; py_skip="$(pyv skipped)"; py_xfail="$(pyv 'expected failures')"
echo "Python: ran=${py_ran:-?} result='${py_result:-?}' (exit $py_rc)"
python_version="$(cd "$EMU" && uv run --locked python --version 2>&1 | awk '{print $2}')"

# ------------------------------------------------------------------ 6. versions.lock
hr "6/6 versions.lock"
# Optional, read-only: the Windows Steam install, if the C: drive is mounted at /mnt/c.
game_buildid="not found from WSL" game_dll_sha="not found from WSL"
steam="/mnt/c/Program Files (x86)/Steam"
libs=("$steam")
if [ -f "$steam/steamapps/libraryfolders.vdf" ]; then
  while IFS= read -r p; do
    p="${p//\\\\/\\}"; p="${p//\\//}"
    [ "${#p}" -ge 2 ] && libs+=("/mnt/$(tr '[:upper:]' '[:lower:]' <<<"${p:0:1}")${p:2}")
  done < <(sed -n 's/.*"path"[[:space:]]*"\([^"]*\)".*/\1/p' "$steam/steamapps/libraryfolders.vdf")
fi
for l in "${libs[@]}"; do
  acf="$l/steamapps/appmanifest_2868840.acf"
  [ -f "$acf" ] || continue
  game_buildid="$(sed -n 's/.*"buildid"[[:space:]]*"\([0-9]*\)".*/\1/p' "$acf" | head -1)"
  dll="$(find "$l/steamapps/common/Slay the Spire 2" -maxdepth 3 -type f -name sts2.dll -path '*data_sts2_*' 2>/dev/null | head -1 || true)"
  [ -n "$dll" ] && game_dll_sha="$(sha "$dll")"
  break
done

if [ -f "$LOCK" ]; then cp -p "$LOCK" "$LOCK.prev-$STAMP"; echo "previous lock kept as $LOCK.prev-$STAMP"; fi
nv() { "$@" 2>/dev/null | head -1 | tr -d '\r' || echo unknown; }
cat >"$LOCK" <<EOF
# versions.lock -- written by pc-setup/build-emulator.sh. Do not edit by hand.
written_utc: $STAMP
machine: $(hostname) / $(. /etc/os-release && echo "$PRETTY_NAME") / kernel $(uname -r)
cpu: $(lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -1); nproc=$(nproc); ram_gb=$(free -g | awk '/^Mem:/ {print $2}')
gpu: $(nv nvidia-smi --query-gpu=name,driver_version --format=csv,noheader)

game_build_target: 23811903   # Slay the Spire 2 v0.107.1 (Steam app 2868840)
game_buildid_on_this_pc: $game_buildid
game_sts2_dll_sha256_on_this_pc: $game_dll_sha

emulator_repo: https://github.com/r33hab/sts2.git
emulator_commit: $EMU_COMMIT
emulator_tree: $EMU_TREE
mod_repo: https://github.com/r33hab/STS2MCP
mod_commit: $MOD_COMMIT
mod_tree: $MOD_TREE
mod_checkout_on_this_pc: $mod_state

security_review: $([ "$have_review" = 1 ] && echo "$REVIEW" || echo "not on this PC (private review kept on the Mac)")
security_review_sha256: $review_sha
security_verdict_line: "$verdict_line"
confirmed_with: "$need"

runtime_id: $RID
dotnet_sdk: $(dotnet --version)
clang: $(nv clang --version)
uv: $(nv uv --version)
python: $python_version
uv_lock_sha256: $(sha "$EMU/uv.lock")
native_lib: $LIB
native_lib_sha256: $lib_sha

csharp_tests: total=${cs_total:-?} passed=${cs_passed:-?} failed=${cs_failed:-?} skipped=${cs_skipped:-?} exit=$cs_rc
python_tests: ran=${py_ran:-?} failures=${py_fail:-0} errors=${py_err:-0} skipped=${py_skip:-0} expected_failures=${py_xfail:-0} result="${py_result:-?}" exit=$py_rc
reference_counts: "HANDOFF.md:52,65 = C# 3650 pass + 1 skipped, Python 492 pass + 6 skipped; rl/FINDINGS.md:102-103 = C# 4801/4801, Python 526/527 (TENDER_POWER in test_sweep_buff_map.py)"
logs: $LOGDIR
EOF
echo "wrote $LOCK"

hr "done"
sed 's/^/  /' "$LOCK"
echo
echo "Notes:"
echo "  * More Python skips than HANDOFF.md is expected here: decompiled/ is absent (tests/python/test_sweep_buff_map.py:142-143,"
echo "    test_live_enemy_ai.py:870, test_live_selection.py:2199 skip without it)."
echo "  * Two timing tests can fail on a busy machine (scripts/desktop_setup.sh:81-82): re-run on a quiet PC before calling it a regression."
echo "  * Copy $LOCK next to the Spireline repo as versions.pc.lock. It is gitignored (it holds this"
echo "    machine's host name and paths): keep it local, never commit it to the public repo."
if [ "$cs_rc" -ne 0 ] || [ "$py_rc" -ne 0 ]; then
  echo
  echo "Some tests FAILED (C# exit $cs_rc, Python exit $py_rc). Logs: $LOGDIR"
  exit 1
fi
