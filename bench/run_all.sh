#!/usr/bin/env bash
# run_all.sh -- day-4 benchmarks for the r33hab/sts2 emulator (pinned b745217), on Linux/WSL2.
#
# UNTESTED. Written 2026-10-10 on the Mac by reading the emulator's source; never executed.
# Run it only AFTER the emulator is built (out/Sts2Emulator.so) and its venv exists.
#
#   EMU=~/git/sts2 bash run_all.sh                       # every step, in order
#   EMU=~/git/sts2 STEPS="03 06" bash run_all.sh         # only steps whose names start 03 / 06
#   EMU=~/git/sts2 WORKERS_LIST="1,2,4,8,12" bash run_all.sh
#
# Raw output of every step goes to $OUT (default bench/results/<host>-<date>/), one
# <step>.log each, plus JSON where the step writes one, steps.tsv (exit code, seconds, load)
# and summary.json from collect.py. README.md lists what each step produces.
set -u -o pipefail

BENCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMU="${EMU:-$HOME/Documents/git/sts2}"
EMU="$(cd "$EMU" 2>/dev/null && pwd || echo "$EMU")"
PY="${PY:-$EMU/.venv/bin/python}"          # the emulator's own venv (numpy, gymnasium)
SYS_PY="${SYS_PY:-python3}"                # collect.py is stdlib-only
LIB_DIR="${STS2_LIB_PATH:-$EMU/out}"       # native.py:173-175 searches STS2_LIB_PATH, then out/
LIB="$LIB_DIR/Sts2Emulator.so"             # native.py:13
PIN="b745217"

N="${N:-$(nproc)}"
PHYS="${PHYS:-$(lscpu -p=CORE,SOCKET 2>/dev/null | grep -v '^#' | sort -u | wc -l | tr -d ' ')}"
[ -n "$PHYS" ] && [ "$PHYS" -gt 0 ] 2>/dev/null || PHYS="$N"
POOL="${POOL:-$(( N > 2 ? N - 2 : 1 ))}"   # processes for the c-sweep (results do not depend on it)
RUNS="${RUNS:-10}"                         # probe_throughput seeds per budget (step 05)
SEARCH_FIGHTS="${SEARCH_FIGHTS:-16}"       # one per Overgrowth weak+normal encounter (step 06)
SCALE_FIGHTS="${SCALE_FIGHTS:-8}"          # fights EACH worker plays per level (step 07)
C_VALUES="${C_VALUES:-0.1,1.4}"            # add 0.0,0.6 for the full FINDINGS.md:114-119 table
CSWEEP_FIGHTS="${CSWEEP_FIGHTS:-240}"
CRN_PAIRS="${CRN_PAIRS:-1500}"
STEP_TIMEOUT="${STEP_TIMEOUT:-5400}"       # seconds; a hung step is killed, not waited on
STEPS="${STEPS:-}"                         # empty = all

if [ -z "${WORKERS_LIST:-}" ]; then
  WORKERS_LIST="$(printf '%s\n' 1 2 4 6 8 "$PHYS" "$N" | awk -v n="$N" '$1>=1 && $1<=n' | sort -n -u | paste -sd, -)"
fi

HOST="$(hostname -s 2>/dev/null || hostname)"
STAMP="$HOST-$(date +%F)"
OUT="${OUT:-$BENCH_DIR/results/$STAMP}"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ] && [ -z "${RESUME:-}" ]; then
  OUT="$OUT-$(date +%H%M%S)"               # never overwrite an earlier run (RESUME=1 to reuse)
fi
mkdir -p "$OUT"

# One thread per process everywhere: N workers x a BLAS pool each would oversubscribe.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
export STS2_EMU="$EMU"                     # sts2bench.py reads it

TIMEV=()
# Peak RSS per step from GNU time (Ubuntu: apt install time). BSD time has no -v.
if [ -x /usr/bin/time ] && /usr/bin/time -v true >/dev/null 2>&1; then TIMEV=(/usr/bin/time -v); fi

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$OUT/steps.log"; }
load1() { cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo NA; }

want() {
  local name="$1" tok
  [ -z "$STEPS" ] && return 0
  for tok in $STEPS; do
    case "$name" in "$tok"*) return 0 ;; esac
  done
  return 1
}

# run_step NAME COMMAND...  -- stdout+stderr to $OUT/NAME.log, a row in steps.tsv
run_step() {
  local name="$1"; shift
  want "$name" || return 0
  local t0 t1 rc l0 l1
  l0="$(load1)"; t0="$(date +%s)"
  log "START $name (load $l0): $*"
  ( cd "$EMU" && timeout --signal=TERM --kill-after=60 "$STEP_TIMEOUT" ${TIMEV[@]+"${TIMEV[@]}"} "$@" ) 2>&1 \
    | tee "$OUT/$name.log"
  rc=${PIPESTATUS[0]}
  t1="$(date +%s)"; l1="$(load1)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$rc" "$t0" "$t1" "$((t1 - t0))" "$l0" "$l1" >> "$OUT/steps.tsv"
  if [ "$rc" -ne 0 ]; then log "FAIL  $name rc=$rc after $((t1 - t0)) s (see $OUT/$name.log)"
  else log "done  $name in $((t1 - t0)) s"; fi
  return 0
}

record_env() {
  echo "date: $(date -Is)"
  echo "host: $HOST"
  echo "uname: $(uname -a)"
  if grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl: yes"; else echo "wsl: no"; fi
  echo "nproc: $N"
  echo "physical_cores: $PHYS"
  echo "cpu_model: $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | sed 's/^ *//')"
  echo "mem_total_kb: $(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null)"
  echo "loadavg: $(cat /proc/loadavg 2>/dev/null)"
  echo "pid1: $(ps -p 1 -o comm= 2>/dev/null)"
  echo "emu: $EMU"
  echo "emu_head: $(git -C "$EMU" rev-parse HEAD 2>/dev/null)"
  echo "emu_dirty_files: $(git -C "$EMU" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  echo "lib: $LIB"
  echo "lib_sha256: $(sha256sum "$LIB" 2>/dev/null | cut -d' ' -f1)"
  echo "lib_mtime: $(stat -c %y "$LIB" 2>/dev/null)"
  echo "python: $("$PY" -c 'import sys; print(sys.version.split()[0])' 2>&1)"
  echo "numpy: $("$PY" -c 'import numpy; print(numpy.__version__)' 2>&1)"
  echo "gymnasium: $("$PY" -c 'import gymnasium; print(gymnasium.__version__)' 2>&1)"
  echo "workers_list: $WORKERS_LIST"
  echo "csweep_pool: $POOL"
  echo "windows_cpu: $(timeout 20 powershell.exe -NoProfile -Command '(Get-CimInstance Win32_Processor).Name' 2>/dev/null | tr -d '\r')"
  echo "windows_game_running: $(timeout 20 tasklist.exe 2>/dev/null | grep -ci 'SlayTheSpire2' || true)"
  echo "--- lscpu"; lscpu 2>/dev/null
  echo "--- free -m"; free -m 2>/dev/null
}

# ------------------------------------------------------------------ preflight
log "results -> $OUT"
log "EMU=$EMU  PY=$PY  LIB=$LIB  N=$N  PHYS=$PHYS  WORKERS_LIST=$WORKERS_LIST  POOL=$POOL"
needs_emu=1
if [ -n "$STEPS" ]; then
  needs_emu=0
  for tok in $STEPS; do case "$tok" in 00*|11*) ;; *) needs_emu=1 ;; esac; done
fi
if [ "$needs_emu" = 1 ]; then
  bad=0
  [ -f "$EMU/rl/run_train/probe_throughput.py" ] || { log "ERROR: no emulator checkout at EMU=$EMU"; bad=1; }
  [ -x "$PY" ] || { log "ERROR: no python at PY=$PY (uv sync in the emulator repo, or set PY)"; bad=1; }
  [ -f "$LIB" ] || { log "ERROR: no $LIB (bash scripts/build.sh linux-x64, or set STS2_LIB_PATH)"; bad=1; }
  if [ "$bad" = 0 ] && ! "$PY" -c 'import numpy, gymnasium' >/dev/null 2>&1; then
    log "ERROR: $PY cannot import numpy and gymnasium"; bad=1
  fi
  [ "$bad" = 0 ] || exit 2
  head="$(git -C "$EMU" rev-parse HEAD 2>/dev/null || echo unknown)"
  case "$head" in "$PIN"*) ;; *) log "WARNING: emulator HEAD $head is not the pin $PIN" ;; esac
  case "$EMU" in /mnt/*) log "WARNING: EMU is on the Windows filesystem (/mnt/...): every import walks src/ over 9P; clone into ~ instead" ;; esac
  awk -v l="$(load1)" 'BEGIN { exit !(l > 1.0) }' && log "WARNING: 1-min load $(load1) > 1.0 before starting; numbers will be low"
fi

# ------------------------------------------------------------------ steps
EMUPY=("$PY" -u)
BENCH=("$PY" -u "$BENCH_DIR/sts2bench.py")

want 00_env && { record_env > "$OUT/00_env.txt" 2>&1; log "wrote 00_env.txt"; }

# Correctness gates first (design 1071): clone independence / faithfulness / resampling.
run_step 01_verify_combat "${EMUPY[@]}" rl/combat_mcts.py --verify
run_step 01_verify_run    "${EMUPY[@]}" rl/mcts_probe.py --section invariants

# Single core, quiet machine.
run_step 02_agent_probe   "${EMUPY[@]}" rl/agent_probe.py
run_step 03_micro         "${EMUPY[@]}" rl/run_train/probe_throughput.py --micro-only --json "$OUT/03_micro.json"
run_step 04_mcts_search   "${EMUPY[@]}" rl/mcts_probe.py --section search --sims 300
run_step 04_mcts_pressure "${EMUPY[@]}" rl/mcts_probe.py --section pressure
run_step 05_runs          "${EMUPY[@]}" rl/run_train/probe_throughput.py --sims 60,300 --runs "$RUNS" \
                            --no-micro --workers 8 --json "$OUT/05_runs.json"
run_step 06_search        "${BENCH[@]}" search --sims 60,300 --fights "$SEARCH_FIGHTS" --json "$OUT/06_search.json"

# Many processes.
run_step 07_scale         "${BENCH[@]}" scale --workers-list "$WORKERS_LIST" --sims 60 \
                            --fights "$SCALE_FIGHTS" --json "$OUT/07_scale.json"
if [ "$N" -ge 8 ]; then
  run_step 08_parallel_8  "${EMUPY[@]}" rl/run_train/probe_throughput.py --sims 60 --runs 8 --no-micro \
                            --workers 8 --parallel 8 --json "$OUT/08_parallel_8.json"
fi
if [ "$N" -ne 8 ]; then
  run_step 08_parallel_N  "${EMUPY[@]}" rl/run_train/probe_throughput.py --sims 60 --runs 8 --no-micro \
                            --workers "$N" --parallel "$N" --json "$OUT/08_parallel_N.json"
fi

# The c = 0.1 vs 1.4 reproduction (design 1073-1074), same fights at every c, two settings.
run_step 09_csweep_historical "${BENCH[@]}" csweep --c-values "$C_VALUES" --fights "$CSWEEP_FIGHTS" --sims 60 \
                            --rollout uniform --crn-fraction 0 --select visits --workers "$POOL" \
                            --json "$OUT/09_csweep_historical.json"
run_step 09_csweep_current "${BENCH[@]}" csweep --c-values "$C_VALUES" --fights "$CSWEEP_FIGHTS" --sims 60 \
                            --rollout tempo --crn-fraction 0.2 --select value --workers "$POOL" \
                            --json "$OUT/09_csweep_current.json"

# CRN variance reduction at the fogmog seed-406 opening (FINDINGS.md:282-304).
run_step 10_crn_tempo     "${BENCH[@]}" crn --encounter 29 --seed 406 --pairs "$CRN_PAIRS" --rollout tempo \
                            --json "$OUT/10_crn_tempo.json"
run_step 10_crn_uniform   "${BENCH[@]}" crn --encounter 29 --seed 406 --pairs "$CRN_PAIRS" --rollout uniform \
                            --json "$OUT/10_crn_uniform.json"

if want 11_collect; then
  "$SYS_PY" "$BENCH_DIR/collect.py" "$OUT" 2>&1 | tee "$OUT/11_collect.log"
fi
log "finished; results in $OUT"
