#!/usr/bin/env bash
# clone-pinned.sh -- fetch the two reviewed third-party repos at their pinned commits into ~/src.
# Builds nothing, runs nothing from the repos, installs nothing.
#
#   r33hab/sts2      (emulator)  commit b7452170ce1df91de29d3c94acb11d87c7efc708 -> ~/src/sts2
#   r33hab/STS2MCP   (game mod)  commit 5a63f924f7e9dcbde4a1f70664e6d301c72e47c4 -> ~/src/STS2MCP
#
# Both commit SHAs and their tree SHAs were read on the Mac on 2026-10-10 from the clones the
# security review used (git rev-parse HEAD / HEAD^{tree}). The script refuses to continue if
# what GitHub serves does not hash to exactly these values, and it never overwrites an
# existing folder.
#
# Usage:  bash ~/pc-setup/clone-pinned.sh            (SRC_DIR=~/src by default)
# Only run it after reading SECURITY_REVIEW.md and deciding to go ahead (CHECKLIST E).
set -euo pipefail

SRC_DIR="${SRC_DIR:-$HOME/src}"
# name | url | commit | tree | branch the commit lives on
PINS=(
  "sts2|https://github.com/r33hab/sts2.git|b7452170ce1df91de29d3c94acb11d87c7efc708|7d5c4dfe31fa5d5e6f27c3adc8100ece50090fe4|spire-coach"
  "STS2MCP|https://github.com/r33hab/STS2MCP|5a63f924f7e9dcbde4a1f70664e6d301c72e47c4|86f940c69836adeb553ba77db769bcf48a3d717f|spire-coach"
)

die() { printf 'REFUSED: %s\n' "$*" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || die "run as your normal user, not root"
command -v git >/dev/null 2>&1 || die "git is missing (run wsl-bootstrap.sh first)"

# Hardened git: no hooks, no fsmonitor program, no submodules, no local-file transport,
# no LFS smudge, no credential prompts (both repos are public).
export GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1
g() {
  git -c core.hooksPath=/dev/null -c core.fsmonitor=false -c protocol.file.allow=never \
      -c submodule.recurse=false -c advice.detachedHead=false "$@"
}

verify_checkout() { # dir commit tree -> 0 if HEAD/tree match and the work tree is clean
  local dir=$1 commit=$2 tree=$3 head htree dirty
  head="$(g -C "$dir" rev-parse HEAD 2>/dev/null || true)"
  htree="$(g -C "$dir" rev-parse 'HEAD^{tree}' 2>/dev/null || true)"
  dirty="$(g -C "$dir" status --porcelain --untracked-files=all 2>/dev/null || echo '?')"
  if [ "$head" != "$commit" ]; then echo "  HEAD is ${head:-none}, expected $commit"; return 1; fi
  if [ "$htree" != "$tree" ]; then echo "  tree is ${htree:-none}, expected $tree"; return 1; fi
  if [ -n "$dirty" ]; then echo "  work tree has changes:"; printf '%s\n' "$dirty" | head -20 | sed 's/^/    /'; return 1; fi
  return 0
}

mkdir -p "$SRC_DIR"
tmp=""
cleanup() { [ -n "$tmp" ] && [ -d "$tmp" ] && rm -rf -- "$tmp"; return 0; }
trap cleanup EXIT

for pin in "${PINS[@]}"; do
  IFS='|' read -r name url commit tree branch <<<"$pin"
  dest="$SRC_DIR/$name"
  printf '\n== %s @ %s\n' "$name" "$commit"

  if [ -e "$dest" ]; then
    [ -d "$dest/.git" ] || die "$dest exists and is not a git checkout; move it aside yourself"
    if verify_checkout "$dest" "$commit" "$tree"; then
      echo "  already present and pinned: OK"
      continue
    fi
    die "$dest exists but is not the pinned, clean checkout (see above). This script will not modify it."
  fi

  tmp="$SRC_DIR/.clone-$name-$$"
  g init -q "$tmp"
  g -C "$tmp" remote add origin "$url"
  echo "  fetching $commit from $url"
  if ! g -C "$tmp" fetch -q --depth 1 --no-tags origin "$commit"; then
    echo "  fetch by commit failed; fetching branch $branch to look for it"
    g -C "$tmp" fetch -q --no-tags origin "$branch" || die "could not fetch $url"
    g -C "$tmp" cat-file -e "${commit}^{commit}" 2>/dev/null \
      || die "$commit is not on $branch any more (history rewritten?). Stop and re-review before using anything newer."
  fi
  g -C "$tmp" checkout -q --detach "$commit"
  verify_checkout "$tmp" "$commit" "$tree" || die "$name does not match the reviewed pin; nothing was kept"
  if g -C "$tmp" fsck --no-progress --no-dangling >/dev/null 2>&1; then echo "  git fsck: OK"; else echo "  git fsck: reported problems (shallow clones can be noisy); HEAD and tree hashes still match"; fi

  # Point out repo files that would change Claude Code's behaviour if a session were started here.
  agent_files="$(g -C "$tmp" ls-files -- .claude .mcp.json CLAUDE.md AGENTS.md .gitmodules 2>/dev/null || true)"
  if [ -n "$agent_files" ]; then
    echo "  NOTE: tracked agent/config files (do not start a Claude session with this folder as its working directory):"
    printf '%s\n' "$agent_files" | sed 's/^/    /'
  fi

  mv -- "$tmp" "$dest"
  tmp=""
  echo "  pinned checkout ready: $dest"
done

printf '\n== summary\n'
for pin in "${PINS[@]}"; do
  IFS='|' read -r name url commit tree branch <<<"$pin"
  printf '  %-8s %s\n' "$name" "$(g -C "$SRC_DIR/$name" log -1 --format='%H tree %T  %ci  %s')"
done
echo
echo "Nothing was built. Next: bash ~/pc-setup/build-emulator.sh   (CHECKLIST E3)"
