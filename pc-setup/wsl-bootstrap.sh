#!/usr/bin/env bash
# wsl-bootstrap.sh -- prepare Ubuntu 24.04 on WSL2 for Spireline. Idempotent: safe to re-run.
#
# Installs
#   * apt packages (the ONLY place sudo is used):
#       - .NET NativeAOT on Linux: clang zlib1g-dev
#         (learn.microsoft.com/dotnet/core/deploying/native-aot/ , Prerequisites > Ubuntu)
#       - .NET SDK runtime dependencies on Ubuntu: libicu (via libicu-dev), libgssapi-krb5-2,
#         libstdc++6, tzdata, ca-certificates, libssl3t64
#         (learn.microsoft.com/dotnet/core/install/linux-ubuntu-decision , Dependencies)
#       - Claude Code sandbox on Linux/WSL2: bubblewrap socat
#         (code.claude.com/docs/en/sandboxing , "Set up Linux and WSL2")
#       - tools: build-essential git tmux jq unzip curl gnupg procps file
#   * .NET 9 SDK into ~/.dotnet with Microsoft's dotnet-install.sh, after checking its GPG
#     signature against Microsoft's published key fingerprint
#   * uv into ~/.local/bin with Astral's installer, then Python 3.12 via `uv python install`
#   * a guarded PATH/DOTNET_ROOT block in ~/.bashrc
# Checks (prints what to do; changes nothing): GPU passthrough (nvidia-smi), sandbox
# prerequisites (AppArmor user-namespace rule, a bwrap smoke test), WSL interop.
# Builds nothing and clones nothing.
#
# Usage:  bash ~/pc-setup/wsl-bootstrap.sh
# Optional environment:
#   DOTNET_SDK_VERSION=9.0.317   install this exact SDK instead of the newest 9.0 SDK
#   UV_VERSION=0.13.0            install this uv version instead of the newest
set -euo pipefail

PY_VERSION=3.12
DOTNET_CHANNEL=9.0
DOTNET_DIR="$HOME/.dotnet"
# Primary key fingerprint printed by Microsoft's "Signature validation of dotnet-install.sh"
# (learn.microsoft.com/dotnet/core/tools/dotnet-install-script).
DOTNET_KEY_FPR=2B930AB1228D11D5D7F6B6ACB9CF1A51FC7D3ACF
MIN_NVIDIA_MAJOR=580   # CUDA 13.0 wheels (r33hab/sts2 uv.lock: cuda-toolkit 13.0.2, nvidia-cuda-runtime 13.0.96)
BASHRC="$HOME/.bashrc"
MARK_BEGIN='# >>> spireline wsl-bootstrap >>>'
MARK_END='# <<< spireline wsl-bootstrap <<<'

summary=()
note() { summary+=("ok    $*"); }
warn() { printf 'WARN: %s\n' "$*" >&2; summary+=("WARN  $*"); }
step() { printf '\n== %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "run this as your normal user, not root (sudo is used only for apt)"

TMPW="$(mktemp -d)"
trap 'rm -rf "$TMPW"' EXIT

# ------------------------------------------------------------------ environment
step "environment"
if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  case "$(uname -r)" in
    *WSL2*) note "WSL2 kernel $(uname -r)" ;;
    *) warn "kernel $(uname -r) does not look like WSL2; the Claude Code sandbox needs WSL2 (wsl --set-version Ubuntu-24.04 2)" ;;
  esac
else
  warn "not running under WSL (fine on plain Linux; the WSL-specific checks below will say so)"
fi
# shellcheck disable=SC1091
. /etc/os-release
if [ "${ID:-}" = ubuntu ] && [ "${VERSION_ID:-}" = 24.04 ]; then
  note "OS ${PRETTY_NAME}"
else
  warn "expected Ubuntu 24.04, found ${PRETTY_NAME:-unknown}; package names may differ"
fi
case "$HOME" in /mnt/*) die "your home folder is on a Windows drive ($HOME); use the Linux filesystem" ;; esac
note "home $HOME on $(df -T "$HOME" | awk 'NR==2 {print $2}') ($(df -h "$HOME" | awk 'NR==2 {print $4}') free)"
note "cpu $(nproc) logical; ram $(free -g | awk '/^Mem:/ {print $2}') GB visible to WSL"

# ------------------------------------------------------------------ apt
step "apt packages (sudo is used here and nowhere else)"
libssl=libssl3t64
[ "${VERSION_ID:-}" = 24.04 ] || libssl=libssl3
PKGS=(
  clang zlib1g-dev                                    # NativeAOT
  libicu-dev libgssapi-krb5-2 libstdc++6 tzdata ca-certificates "$libssl"  # .NET SDK runtime deps
  bubblewrap socat                                    # Claude Code sandbox
  build-essential git tmux jq unzip curl gnupg procps file
)
need=()
for p in "${PKGS[@]}"; do
  if [ "$(dpkg-query -W -f='${db:Status-Status}' "$p" 2>/dev/null || true)" != installed ]; then
    need+=("$p")
  fi
done
if ((${#need[@]})); then
  echo "missing: ${need[*]}"
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${need[@]}"
  note "apt installed: ${need[*]}"
else
  note "apt: all ${#PKGS[@]} packages already installed"
fi

# ------------------------------------------------------------------ .NET 9 SDK
step ".NET ${DOTNET_CHANNEL} SDK in ${DOTNET_DIR}"
want="${DOTNET_SDK_VERSION:-${DOTNET_CHANNEL}.}"
have_sdk() {
  [ -x "$DOTNET_DIR/dotnet" ] || return 1
  "$DOTNET_DIR/dotnet" --list-sdks 2>/dev/null | awk '{print $1}' | grep -qF -- "$want" || return 1
}
if have_sdk; then
  note "dotnet SDK already present: $("$DOTNET_DIR/dotnet" --list-sdks | awk '{print $1}' | tr '\n' ' ')"
else
  for f in dotnet-install.sh dotnet-install.sig dotnet-install.asc; do
    curl -fsSL --proto '=https' --tlsv1.2 -o "$TMPW/$f" "https://dot.net/v1/$f"
  done
  export GNUPGHOME="$TMPW/gnupg"
  mkdir -m 700 "$GNUPGHOME"
  gpg --batch --quiet --import "$TMPW/dotnet-install.asc" 2>/dev/null || die "could not import Microsoft's dotnet-install signing key"
  status="$(gpg --batch --status-fd 1 --verify "$TMPW/dotnet-install.sig" "$TMPW/dotnet-install.sh" 2>/dev/null || true)"
  unset GNUPGHOME
  if ! grep -qE "^\[GNUPG:\] VALIDSIG .*${DOTNET_KEY_FPR}" <<<"$status"; then
    die "dotnet-install.sh signature did not verify against key ${DOTNET_KEY_FPR}; not running it"
  fi
  echo "dotnet-install.sh signature OK (key ${DOTNET_KEY_FPR})"
  args=(--install-dir "$DOTNET_DIR" --no-path)
  if [ -n "${DOTNET_SDK_VERSION:-}" ]; then args+=(--version "$DOTNET_SDK_VERSION"); else args+=(--channel "$DOTNET_CHANNEL"); fi
  bash "$TMPW/dotnet-install.sh" "${args[@]}"
  have_sdk || die "dotnet-install.sh finished but no ${want}* SDK is listed in $DOTNET_DIR"
  note "dotnet SDK installed: $("$DOTNET_DIR/dotnet" --list-sdks | awk '{print $1}' | tr '\n' ' ')"
fi
export DOTNET_ROOT="$DOTNET_DIR"
export PATH="$HOME/.local/bin:$DOTNET_DIR:$DOTNET_DIR/tools:$PATH"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1

# ------------------------------------------------------------------ ~/.bashrc
step "~/.bashrc PATH block"
if grep -qF "$MARK_BEGIN" "$BASHRC" 2>/dev/null; then
  note "bashrc block already present"
else
  {
    printf '\n%s\n' "$MARK_BEGIN"
    cat <<'EOF'
# Added by Spireline wsl-bootstrap.sh: .NET 9 SDK in ~/.dotnet, uv in ~/.local/bin.
export DOTNET_ROOT="$HOME/.dotnet"
case ":$PATH:" in
  *":$HOME/.dotnet:"*) ;;
  *) export PATH="$HOME/.local/bin:$HOME/.dotnet:$HOME/.dotnet/tools:$PATH" ;;
esac
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1
EOF
    printf '%s\n' "$MARK_END"
  } >>"$BASHRC"
  note "bashrc block added (open a new shell or run: source ~/.bashrc)"
fi

# ------------------------------------------------------------------ uv
step "uv"
if command -v uv >/dev/null 2>&1; then
  note "uv already present: $(uv --version)"
else
  url="https://astral.sh/uv/install.sh"
  [ -n "${UV_VERSION:-}" ] && url="https://astral.sh/uv/${UV_VERSION}/install.sh"
  curl -fsSL --proto '=https' --tlsv1.2 -o "$TMPW/uv-install.sh" "$url"
  # UV_NO_MODIFY_PATH=1: the installer leaves shell profiles alone; the bashrc block above
  # already puts ~/.local/bin on PATH (docs.astral.sh/uv/getting-started/installation/).
  UV_NO_MODIFY_PATH=1 sh "$TMPW/uv-install.sh"
  command -v uv >/dev/null 2>&1 || die "uv installer finished but uv is not on PATH ($HOME/.local/bin)"
  note "uv installed: $(uv --version)"
fi

# ------------------------------------------------------------------ Python 3.12
step "Python ${PY_VERSION} via uv"
uv python install "$PY_VERSION"
py="$(uv python find "$PY_VERSION")"
note "python $("$py" --version 2>&1 | awk '{print $2}') at $py"

# ------------------------------------------------------------------ GPU
step "GPU passthrough"
smi=""
if command -v nvidia-smi >/dev/null 2>&1; then smi="$(command -v nvidia-smi)"
elif [ -x /usr/lib/wsl/lib/nvidia-smi ]; then smi=/usr/lib/wsl/lib/nvidia-smi
fi
if [ -n "$smi" ] && gpu="$("$smi" --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null)" && [ -n "$gpu" ]; then
  note "gpu $gpu"
  drv="$(head -1 <<<"$gpu" | awk -F', *' '{print $2}')"
  major="${drv%%.*}"
  if [[ "$major" =~ ^[0-9]+$ ]] && ((major < MIN_NVIDIA_MAJOR)); then
    warn "NVIDIA driver $drv is older than R${MIN_NVIDIA_MAJOR}; update it ON WINDOWS (CHECKLIST A5). The torch wheels pinned in r33hab/sts2 use CUDA 13."
  fi
else
  warn "nvidia-smi does not work inside WSL. Fix it on WINDOWS: install or update the NVIDIA driver there, then run 'wsl --shutdown' in PowerShell. Do NOT install an NVIDIA or CUDA driver inside Ubuntu. (The emulator is CPU-only; the GPU matters only for torch.)"
fi

# ------------------------------------------------------------------ sandbox prerequisites
step "Claude Code sandbox prerequisites"
for b in bwrap socat; do
  if command -v "$b" >/dev/null 2>&1; then note "sandbox: $b present"; else warn "sandbox: $b missing"; fi
done
userns="$(sysctl -n kernel.apparmor_restrict_unprivileged_userns 2>/dev/null || echo absent)"
if [ "$userns" = 1 ]; then
  warn "AppArmor blocks unprivileged user namespaces (kernel.apparmor_restrict_unprivileged_userns=1): add the bwrap AppArmor profile in CHECKLIST C2"
else
  note "AppArmor user-namespace restriction: $userns (no action needed)"
fi
if bwrap --ro-bind / / --dev /dev --proc /proc --unshare-all --die-with-parent true 2>/dev/null; then
  note "bwrap smoke test: a sandbox could be created"
else
  warn "bwrap could not create a sandbox; Claude Code will refuse to start with the kit's settings (failIfUnavailable). See CHECKLIST C2 and troubleshooting."
fi

# ------------------------------------------------------------------ WSL interop
step "WSL interop (can Linux processes launch Windows programs?)"
interop=absent
for f in /proc/sys/fs/binfmt_misc/WSLInterop*; do
  [ -e "$f" ] && interop="$(head -1 "$f")"
done
if [ "$interop" = enabled ]; then
  warn "WSL interop is enabled: a sandboxed command could start a Windows program, which runs outside the Linux sandbox, unless the optional seccomp filter is installed. Decide in CHECKLIST C7 (after /login)."
else
  note "WSL interop: $interop"
fi
if [ -f /etc/wsl.conf ]; then
  echo "-- /etc/wsl.conf"; sed 's/^/   /' /etc/wsl.conf
fi
note "pid 1 is $(ps -p 1 -o comm= 2>/dev/null || echo unknown)"

# ------------------------------------------------------------------ folders
step "folders"
mkdir -p "$HOME/code" "$HOME/src" "$HOME/logs" "$HOME/.local/state/spireline-rc"
chmod 700 "$HOME/.local/state/spireline-rc"
note "folders ~/code ~/src ~/logs ~/.local/state/spireline-rc exist"

# ------------------------------------------------------------------ summary
step "summary"
printf '  %s\n' "${summary[@]}"
echo
echo "versions:"
printf '  %-8s %s\n' dotnet "$("$DOTNET_DIR/dotnet" --version 2>/dev/null || echo missing)"
printf '  %-8s %s\n' clang "$(clang --version 2>/dev/null | head -1 || echo missing)"
printf '  %-8s %s\n' git "$(git --version 2>/dev/null || echo missing)"
printf '  %-8s %s\n' tmux "$(tmux -V 2>/dev/null || echo missing)"
printf '  %-8s %s\n' jq "$(jq --version 2>/dev/null || echo missing)"
printf '  %-8s %s\n' uv "$(uv --version 2>/dev/null || echo missing)"
printf '  %-8s %s\n' python "$("$py" --version 2>&1 || echo missing)"
printf '  %-8s %s\n' claude "$(command -v claude >/dev/null 2>&1 && claude --version 2>/dev/null | head -1 || echo 'not installed yet (CHECKLIST C3)')"
echo
echo "Next: open a new Ubuntu window (or run: source ~/.bashrc), then continue with CHECKLIST C2/C3."
