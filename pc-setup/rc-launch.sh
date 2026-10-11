#!/usr/bin/env bash
# rc-launch.sh -- keep `claude remote-control --name gaming-pc` running in ~/code inside a tmux
# session called spireline-rc, restarting it with backoff whenever it exits.
#
#   rc-launch.sh            start the session if needed, then attach (only when run in a terminal)
#   rc-launch.sh start      start the session if needed; never attach (for Task Scheduler)
#   rc-launch.sh attach     attach to the running session (detach again with Ctrl-b then d)
#   rc-launch.sh status     running or not, last exit, last log lines
#   rc-launch.sh stop       stop the server and the restart loop
#   rc-launch.sh restart    stop, then start (resumes the same remote session if within the window)
#   rc-launch.sh fresh      stop, forget the last session, start a NEW remote session
#   rc-launch.sh env        print the cache exports, for an interactive session:
#                           eval "$(~/pc-setup/rc-launch.sh env)"; claude
#
# Restart rule. After the server stops, `claude remote-control --continue` brings the session back
# for about four hours (code.claude.com/docs/en/remote-control, "Resume sessions after stopping the
# server"). Within RC_RESUME_WINDOW seconds of the last exit this loop restarts with --continue;
# after that, or when a --continue attempt ends within 60 s, it starts a fresh named session.
# Server mode also exits by itself after ~10 minutes without network ("Limitations"); the loop
# simply starts it again. Backoff: 5 s doubling to 300 s, reset after a run of 10 minutes or more.
#
# Ctrl-C on the Claude screen ends that server run and the loop starts it again (resuming).
# Ctrl-C during the "restarting in N s" countdown ends the loop. To stop for good: rc-launch.sh stop.
#
# Optional environment:
#   RC_NAME=gaming-pc   RC_DIR=$HOME/code   RC_RESUME_WINDOW=12600   RC_CAPACITY=<N>
#   RC_PERMISSION_MODE=<mode>   (default, acceptEdits, plan, ...; bypassPermissions is refused)
#   RC_DEBUG=1      add --debug-file ~/logs/rc-debug.log
#   RC_PANE_LOG=1   also copy everything shown in the session to ~/logs/rc-pane.log
#
# Log: ~/logs/rc.log (one line per start, exit and backoff).
set -uo pipefail

RC_NAME="${RC_NAME:-gaming-pc}"
RC_DIR="${RC_DIR:-$HOME/code}"
SESSION=spireline-rc
RESUME_WINDOW="${RC_RESUME_WINDOW:-12600}"   # 3.5 h, inside the documented ~4 h
BACKOFF_MIN=5
BACKOFF_MAX=300
HEALTHY_RUN=600
# The tmux socket lives in a private folder that claude-settings.json also hides from sandboxed
# commands (sandbox.filesystem.denyRead), so a command Claude runs cannot reach this tmux server
# and start something outside the sandbox through it.
STATE_DIR="$HOME/.local/state/spireline-rc"
SOCK="$STATE_DIR/tmux.sock"
TMUX_CONF="$STATE_DIR/tmux.conf"
STOP_FILE="$STATE_DIR/stop"
LAST_STOP_FILE="$STATE_DIR/last_stop"
LOG_DIR="$HOME/logs"
LOG="$LOG_DIR/rc.log"
SELF="$(readlink -f "${BASH_SOURCE[0]}")"

export PATH="$HOME/.local/bin:$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"

die() { printf 'rc-launch: %s\n' "$*" >&2; exit 1; }
log() { mkdir -p "$LOG_DIR"; printf '%s %s\n' "$(date -Is)" "$*" >>"$LOG"; }
tmuxc() { tmux -S "$SOCK" "$@"; }
running() { tmuxc has-session -t "$SESSION" 2>/dev/null; }

preflight() {
  [ "$(id -u)" -ne 0 ] || die "do not run as root"
  command -v tmux >/dev/null 2>&1 || die "tmux is missing (run wsl-bootstrap.sh)"
  command -v claude >/dev/null 2>&1 || die "claude is missing (CHECKLIST C3)"
  mkdir -p "$RC_DIR" "$LOG_DIR" "$STATE_DIR" || die "cannot create folders"
  chmod 700 "$STATE_DIR"
  [ "$(readlink -f "$RC_DIR")" != "$(readlink -f "$HOME")" ] \
    || die "RC_DIR must not be your home folder: Remote Control never saves workspace trust there"
  case "${RC_PERMISSION_MODE:-}" in
    bypassPermissions) die "bypassPermissions is not allowed on this PC" ;;
  esac
  printf '%s\n' 'set -g history-limit 50000' 'set -g mouse on' >"$TMUX_CONF"
}

cache_env() {
  # Sandboxed commands may write only to ~/code, ~/src, ~/logs and ~/.venvs/spireline
  # (claude-settings.json). Keep tool caches inside ~/code so uv, NuGet, dotnet and torch work
  # for Claude without widening the sandbox to folders that your own unsandboxed builds trust.
  local c="$RC_DIR/.cache"
  printf 'export %s=%q\n' \
    UV_CACHE_DIR "$c/uv" \
    UV_PYTHON_DOWNLOADS never \
    NUGET_PACKAGES "$c/nuget/packages" \
    NUGET_HTTP_CACHE_PATH "$c/nuget/http-cache" \
    NUGET_PLUGINS_CACHE_PATH "$c/nuget/plugins-cache" \
    DOTNET_CLI_HOME "$c/dotnet-cli-home" \
    DOTNET_ROOT "$HOME/.dotnet" \
    DOTNET_CLI_TELEMETRY_OPTOUT 1 \
    DOTNET_NOLOGO 1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE 1 \
    TORCH_HOME "$c/torch" \
    TRITON_CACHE_DIR "$c/triton" \
    MPLCONFIGDIR "$c/matplotlib"
}

rotate_log() {
  if [ -f "$LOG" ] && [ "$(stat -c %s "$LOG" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv -f "$LOG" "$LOG.1"
  fi
}

run_loop() {
  preflight
  cd "$RC_DIR" || die "cannot cd to $RC_DIR"
  unset TMUX TMUX_PANE            # claude and its commands do not learn this tmux server's socket
  eval "$(cache_env)"
  mkdir -p "$UV_CACHE_DIR" "$NUGET_PACKAGES" "$NUGET_HTTP_CACHE_PATH" "$NUGET_PLUGINS_CACHE_PATH" \
    "$DOTNET_CLI_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" "$MPLCONFIGDIR"
  trap 'touch "$STOP_FILE"' INT    # a SIGINT that reaches this loop (e.g. during the countdown) means stop
  local delay=$BACKOFF_MIN resume_ok=1 now last mode t0 t1 rc dur pause i
  local -a args
  log "loop start pid=$$ dir=$RC_DIR name=$RC_NAME"
  while :; do
    if [ -e "$STOP_FILE" ]; then
      rm -f "$STOP_FILE"
      log "loop exit (stop requested)"
      return 0
    fi
    rotate_log
    now=$(date +%s)
    last=$(cat "$LAST_STOP_FILE" 2>/dev/null || echo 0)
    [[ "$last" =~ ^[0-9]+$ ]] || last=0
    if ((resume_ok)) && ((last > 0)) && ((now - last < RESUME_WINDOW)); then
      mode=continue
      args=(remote-control --continue)          # --continue cannot be combined with --capacity/--spawn
    else
      mode=fresh
      args=(remote-control --name "$RC_NAME")
      [ -n "${RC_CAPACITY:-}" ] && args+=(--capacity "$RC_CAPACITY")
    fi
    [ -n "${RC_PERMISSION_MODE:-}" ] && args+=(--permission-mode "$RC_PERMISSION_MODE")
    [ "${RC_DEBUG:-0}" = 1 ] && args+=(--debug-file "$LOG_DIR/rc-debug.log")

    log "start ($mode): claude ${args[*]}"
    printf '\n[rc-launch] %s  starting (%s): claude %s\n\n' "$(date '+%F %T')" "$mode" "${args[*]}"
    t0=$(date +%s)
    claude "${args[@]}"
    rc=$?
    t1=$(date +%s)
    dur=$((t1 - t0))
    printf '%s\n' "$t1" >"$LAST_STOP_FILE"
    log "exit rc=$rc after ${dur}s ($mode)"

    if [ "$mode" = continue ] && ((dur < 60)); then
      resume_ok=0
      log "resume did not hold; the next start is a fresh session"
    else
      resume_ok=1
    fi
    [ -e "$STOP_FILE" ] && continue

    if ((dur >= HEALTHY_RUN)); then delay=$BACKOFF_MIN; fi
    pause=$delay
    delay=$((delay * 2))
    ((delay > BACKOFF_MAX)) && delay=$BACKOFF_MAX
    log "restart in ${pause}s"
    printf '[rc-launch] restarting in %ss (Ctrl-C now, or rc-launch.sh stop, ends the loop)\n' "$pause"
    for ((i = 0; i < pause; i++)); do
      [ -e "$STOP_FILE" ] && break
      sleep 1
    done
  done
}

cmd_start() { # auto|never
  preflight
  if running; then
    echo "spireline-rc is already running (socket $SOCK)."
  else
    rm -f "$STOP_FILE"
    tmuxc -f "$TMUX_CONF" new-session -d -s "$SESSION" -c "$RC_DIR" -x 200 -y 50 \
      "bash $(printf '%q' "$SELF") --loop" || die "tmux could not start the session"
    if [ "${RC_PANE_LOG:-0}" = 1 ]; then
      tmuxc pipe-pane -o -t "$SESSION" "cat >> $(printf '%q' "$LOG_DIR/rc-pane.log")"
    fi
    log "tmux session $SESSION started"
    echo "started tmux session $SESSION in $RC_DIR (log: $LOG)"
  fi
  if [ "${1:-auto}" = auto ] && [ -t 0 ] && [ -t 1 ] && [ -z "${TMUX:-}" ]; then
    echo "attaching; detach with Ctrl-b then d (Ctrl-c inside stops the server)"
    exec tmux -S "$SOCK" attach -t "$SESSION"
  fi
}

cmd_stop() {
  if ! running; then echo "not running"; return 0; fi
  mkdir -p "$STATE_DIR"
  touch "$STOP_FILE"
  tmuxc send-keys -t "$SESSION" C-c
  sleep 2
  running && tmuxc send-keys -t "$SESSION" C-c   # in case the screen asks for a second Ctrl-C
  for _ in $(seq 1 20); do running || break; sleep 1; done
  if running; then
    tmuxc kill-session -t "$SESSION"
    date +%s >"$LAST_STOP_FILE"
  fi
  rm -f "$STOP_FILE"
  log "stopped by rc-launch.sh"
  echo "stopped"
}

cmd_status() {
  if running; then echo "running: tmux session $SESSION (attach: rc-launch.sh attach)"; else echo "not running"; fi
  if [ -f "$LAST_STOP_FILE" ]; then
    local age=$(($(date +%s) - $(cat "$LAST_STOP_FILE")))
    echo "last server exit: ${age}s ago (resume window ${RESUME_WINDOW}s)"
  fi
  echo "--- last lines of $LOG"
  tail -n 15 "$LOG" 2>/dev/null || echo "(no log yet)"
}

case "${1:-}" in
  "") cmd_start auto ;;
  start) cmd_start never ;;
  attach) running || die "not running"; exec tmux -S "$SOCK" attach -t "$SESSION" ;;
  status) cmd_status ;;
  stop) cmd_stop ;;
  restart) cmd_stop; cmd_start never ;;
  fresh) cmd_stop; rm -f "$LAST_STOP_FILE"; log "fresh session requested"; cmd_start never ;;
  env) cache_env ;;
  --loop) run_loop ;;
  -h | --help | help) sed -n '2,31p' "$SELF" ;;
  *) sed -n '2,31p' "$SELF"; exit 2 ;;
esac
