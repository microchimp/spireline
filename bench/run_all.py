#!/usr/bin/env python3
"""run_all.py -- the day-4 benchmarks on native Windows (no WSL); the port of run_all.sh.

Same steps, flags and outputs as run_all.sh, so collect.py reads either. Standard library only.
Run it with the emulator's own venv python (the locked checkout blocks `uv run`):

    D:\\spireline\\src\\sts2\\.venv\\Scripts\\python.exe bench\\run_all.py                # every step
    ... run_all.py --steps "00 01"                  # only steps whose names start 00 / 01
    ... run_all.py --detach                         # relaunch detached; progress in STATUS.txt

Differences from run_all.sh, all Windows-only:
  - winshim/ goes on PYTHONPATH, so probe_throughput's workers get os.nice (sitecustomize.py).
  - "load" is busy cores (CPU busy fraction over 1 s x logical CPUs); Windows has no loadavg.
  - Peak RSS is the step's top process (peak working set), not its spawned workers, and is not
    reported at all when PY is a venv launcher (the default); 07_scale records workers' own.
  - A hung step gets CTRL_BREAK, then its process tree is killed; rc 124 as with timeout(1).
  - Results hold no host name and no absolute paths: logs and JSON are scrubbed after each step.
The emulator checkout is only read; everything is written under bench/results/<run>/.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
SHIM_DIR = BENCH_DIR / "winshim"
PIN = "b745217"
WIN = sys.platform == "win32"

if not WIN:
    raise SystemExit("run_all.py is the native-Windows driver; use run_all.sh on Linux/WSL")

K32 = ctypes.WinDLL("kernel32", use_last_error=True)


# ------------------------------------------------------------------ Windows helpers


class _FILETIME(ctypes.Structure):
    _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]


def _ft(f: _FILETIME) -> int:
    return (f.hi << 32) | f.lo


def busy_cores(n: int, window: float = 1.0) -> float | None:
    """CPU busy fraction over `window` seconds times logical CPUs: a stand-in for load1."""
    def sample():
        idle, kern, user = _FILETIME(), _FILETIME(), _FILETIME()
        if not K32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
            return None
        return _ft(idle), _ft(kern) + _ft(user)  # kernel time includes idle time
    a = sample()
    time.sleep(window)
    b = sample()
    if not a or not b or b[1] <= a[1]:
        return None
    busy = 1.0 - (b[0] - a[0]) / (b[1] - a[1])
    return round(max(0.0, busy) * n, 2)


class _PMC(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
        (name, ctypes.c_size_t)
        for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                     "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                     "PagefileUsage", "PeakPagefileUsage")
    ]


K32.K32GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD)
K32.K32GetProcessMemoryInfo.restype = wintypes.BOOL


def peak_rss_kb(proc: subprocess.Popen) -> int | None:
    handle = getattr(proc, "_handle", None)
    if handle is None:
        return None
    pmc = _PMC()
    pmc.cb = ctypes.sizeof(_PMC)
    if not K32.K32GetProcessMemoryInfo(int(handle), ctypes.byref(pmc), pmc.cb):
        return None
    return pmc.PeakWorkingSetSize // 1024


K32.SetThreadExecutionState.argtypes = (wintypes.DWORD,)
K32.SetThreadExecutionState.restype = wintypes.DWORD
NO_WINDOW = subprocess.CREATE_NO_WINDOW  # the detached driver has no console; keep children windowless


def keep_awake(on: bool) -> None:
    """Per-process request (cleared when this process exits); not a power setting."""
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    K32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


def kill_tree(proc: subprocess.Popen, grace: float = 60.0) -> None:
    try:
        proc.send_signal(signal.CTRL_BREAK_EVENT)
        proc.wait(timeout=grace)
        return
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], creationflags=NO_WINDOW,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def run_text(cmd: list, timeout: float = 30.0, cwd=None, env=None) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env,
                           creationflags=NO_WINDOW, stdin=subprocess.DEVNULL,
                           encoding="utf-8", errors="replace", check=False)
        return (r.stdout or r.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"error: {exc!r}"


def win_hw() -> dict:
    ps = ("$p = Get-CimInstance Win32_Processor; $c = Get-CimInstance Win32_ComputerSystem; "
          "@{name = ($p | Select-Object -First 1).Name; cores = ($p | Measure-Object NumberOfCores -Sum).Sum; "
          "logical = ($p | Measure-Object NumberOfLogicalProcessors -Sum).Sum; "
          "mem = $c.TotalPhysicalMemory} | ConvertTo-Json -Compress")
    try:
        return json.loads(run_text(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps], 60))
    except ValueError:
        return {}


# ------------------------------------------------------------------ scrubbing


class Scrubber:
    """Replace absolute paths and the host name in result files with placeholders."""

    def __init__(self, pairs: list) -> None:
        subs = []
        for value, label in pairs:
            if not value:
                continue
            value = str(value)
            forms = {value, value.replace("\\", "/"), value.replace("\\", "\\\\")}
            if len(value) > 2 and value[1] == ":":  # D:\x as Git Bash prints it: /d/x
                forms.add("/" + value[0].lower() + value[2:].replace("\\", "/"))
            for f in forms:
                subs.append((f, label))
        subs.sort(key=lambda s: -len(s[0]))  # longest first: OUT before BENCH before HOME
        self.subs = subs

    def text(self, s: str) -> str:
        for value, label in self.subs:
            if re.fullmatch(r"[A-Za-z0-9_-]+", value):  # a bare host or user name: whole words only
                s = re.sub(rf"(?i)(?<![A-Za-z0-9_-]){re.escape(value)}(?![A-Za-z0-9_-])", label, s)
            else:
                s = re.compile(re.escape(value), re.IGNORECASE).sub(lambda _m, l=label: l, s)
        return s

    def file(self, path: Path) -> None:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        new = self.text(raw)
        if new != raw:
            path.write_text(new, encoding="utf-8")

    def tree(self, root: Path) -> None:
        for p in root.iterdir():
            if p.is_file() and p.suffix in (".log", ".json", ".txt", ".tsv"):
                self.file(p)


# ------------------------------------------------------------------ driver


class Run:
    def __init__(self, a: argparse.Namespace) -> None:
        self.a = a
        self.emu = Path(a.emu).resolve()
        self.py = Path(a.py) if a.py else self.emu / ".venv" / "Scripts" / "python.exe"
        self.lib_dir = Path(os.environ.get("STS2_LIB_PATH") or self.emu / "out")
        self.lib = self.lib_dir / "Sts2Emulator.dll"  # native.py:12
        # A venv's python.exe is a launcher that runs the base interpreter as a child, so its
        # peak working set says nothing about the step: report peak RSS only without one.
        self.launcher = (self.py.parent.parent / "pyvenv.cfg").is_file()
        self.n = os.cpu_count() or 1
        hw = win_hw()
        self.hw = hw
        self.phys = int(hw.get("cores") or 0) or self.n
        self.pool = a.pool or (self.n - 2 if self.n > 2 else 1)
        if a.workers_list:
            self.workers_list = a.workers_list
        else:
            ws = sorted({w for w in (1, 2, 4, 6, 8, self.phys, self.n) if 1 <= w <= self.n})
            self.workers_list = ",".join(map(str, ws))
        self.out = Path(a.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.steps_filter = a.steps.split() if a.steps else []
        self.rows: list = []
        self.current = None
        self.state = "starting"
        self.t_start = time.time()
        self.scrub = Scrubber([
            (self.out, "<out>"), (BENCH_DIR, "<bench>"), (self.py, "<py>"), (self.emu, "<emu>"),
            (BENCH_DIR.parent, "<repo>"), (BENCH_DIR.parent.parent, "<ws>"), (Path.home(), "<home>"), (sys.prefix, "<py-prefix>"),
            (getattr(sys, "base_prefix", ""), "<py-base>"),
            (socket.gethostname(), "<host>"), (os.environ.get("COMPUTERNAME"), "<host>"),
            (os.environ.get("USERNAME"), "<user>"),
        ])
        self.env = self._child_env()

    def _child_env(self) -> dict:
        env = dict(os.environ)
        # One thread per process everywhere: N workers x a BLAS pool each would oversubscribe.
        for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            env[k] = "1"
        env.update(PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
                   PYTHONUTF8="1", STS2_EMU=str(self.emu))
        env["PYTHONPATH"] = os.pathsep.join([str(SHIM_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
        env.pop("VIRTUAL_ENV", None)
        return env

    # ---- bookkeeping

    def log(self, msg: str) -> None:
        line = f"[{dt.datetime.now():%H:%M:%S}] {self.scrub.text(msg)}"
        print(line, flush=True)
        with open(self.out / "steps.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def status(self) -> None:
        el = time.time() - self.t_start
        lines = [
            f"run: {self.out.name}",
            f"state: {self.state}",
            f"started: {dt.datetime.fromtimestamp(self.t_start):%Y-%m-%d %H:%M:%S}",
            f"updated: {dt.datetime.now():%Y-%m-%d %H:%M:%S}",
            f"elapsed_s: {el:.0f}",
            f"current: {self.current or '-'}",
            f"steps_done: {len(self.rows)}",
            f"steps_failed: {sum(1 for r in self.rows if r[1] != 0)}",
            "",
            "step\trc\tseconds",
        ] + [f"{r[0]}\t{r[1]}\t{r[4]}" for r in self.rows]
        tmp = self.out / "STATUS.txt.tmp"
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, self.out / "STATUS.txt")

    def want(self, name: str) -> bool:
        return not self.steps_filter or any(name.startswith(t) for t in self.steps_filter)

    # ---- steps

    def step(self, name: str, *cmd) -> None:
        if not self.want(name):
            return
        cmd = [str(c) for c in cmd]
        self.current = name
        self.status()
        l0 = busy_cores(self.n)
        t0 = int(time.time())
        self.log(f"START {name} (busy cores {l0}): {subprocess.list2cmdline(cmd)}")
        log_path = self.out / f"{name}.log"
        rc = None
        with open(log_path, "wb") as f:
            try:
                proc = subprocess.Popen(cmd, cwd=self.emu, env=self.env, stdout=f, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL,
                                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | NO_WINDOW)
            except OSError as exc:
                f.write(f"could not start: {exc!r}\n".encode())
                proc = None
                rc = 127
            if proc is not None:
                try:
                    rc = proc.wait(timeout=self.a.step_timeout)
                except subprocess.TimeoutExpired:
                    kill_tree(proc)
                    rc = 124
                rss = peak_rss_kb(proc)
                if rss is not None and not self.launcher:
                    f.write(f"\n\tMaximum resident set size (kbytes): {rss}\n".encode())
        t1 = int(time.time())
        l1 = busy_cores(self.n)
        self.scrub.tree(self.out)
        self.rows.append((name, rc, t0, t1, t1 - t0, l0 if l0 is not None else "NA", l1 if l1 is not None else "NA"))
        with open(self.out / "steps.tsv", "a", encoding="utf-8") as f:
            f.write("\t".join(map(str, self.rows[-1])) + "\n")
        if rc != 0:
            self.log(f"FAIL  {name} rc={rc} after {t1 - t0} s (see {name}.log)")
        else:
            self.log(f"done  {name} in {t1 - t0} s")
        self.current = None
        self.status()

    def record_env(self) -> str:
        py = str(self.py)
        def pyval(expr: str) -> str:
            return run_text([py, "-c", expr], 60, cwd=self.out, env=self.env)
        git = ["git", "--no-optional-locks", "-C", str(self.emu)]
        dirty = run_text(git + ["status", "--porcelain"], 60)
        lib_mtime = dt.datetime.fromtimestamp(self.lib.stat().st_mtime).isoformat() if self.lib.exists() else ""
        game = run_text(["tasklist", "/FI", "IMAGENAME eq SlayTheSpire2.exe", "/NH"], 20)
        shim = SHIM_DIR / "sitecustomize.py"
        shim_check = run_text([py, "-c", "import os, sitecustomize; print(hasattr(os, 'nice'), "
                                         "os.path.basename(os.path.dirname(sitecustomize.__file__)))"],
                              60, cwd=self.out, env=self.env)
        lines = [
            f"date: {dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
            "host: <redacted>",
            f"uname: {platform.system()} {platform.release()} {platform.version()} {platform.machine()}",
            "wsl: no",
            f"nproc: {self.n}",
            f"physical_cores: {self.phys}",
            f"cpu_model: {(self.hw.get('name') or '').strip()}",
            f"mem_total_kb: {int(self.hw.get('mem') or 0) // 1024}",
            f"loadavg: busy cores {busy_cores(self.n)} (Windows: CPU busy fraction x nproc over 1 s)",
            "pid1: n/a (Windows)",
            "emu: <emu>",
            f"emu_head: {run_text(git + ['rev-parse', 'HEAD'], 30)}",
            f"emu_dirty_files: {len([ln for ln in dirty.splitlines() if ln.strip()])}",
            "lib: <emu>/out/Sts2Emulator.dll" if self.lib_dir == self.emu / "out" else "lib: <STS2_LIB_PATH>/Sts2Emulator.dll",
            f"lib_sha256: {sha256(self.lib)}",
            f"lib_mtime: {lib_mtime}",
            f"python: {pyval('import sys; print(sys.version.split()[0])')}",
            f"numpy: {pyval('import numpy; print(numpy.__version__)')}",
            f"gymnasium: {pyval('import gymnasium; print(gymnasium.__version__)')}",
            f"workers_list: {self.workers_list}",
            f"csweep_pool: {self.pool}",
            f"winshim_sha256: {sha256(shim)}",
            f"winshim_check: {shim_check}",
            f"step_timeout_s: {self.a.step_timeout}",
            f"windows_cpu: {(self.hw.get('name') or '').strip()}",
            f"windows_game_running: {0 if 'No tasks' in game or 'SlayTheSpire2' not in game else 1}",
            f"power_scheme: {run_text(['powercfg', '/getactivescheme'], 20)}",
            "--- hw",
            json.dumps(self.hw),
        ]
        return "\n".join(lines) + "\n"

    def preflight(self) -> bool:
        self.log(f"results -> {self.out}")
        self.log(f"EMU={self.emu}  PY={self.py}  LIB={self.lib}  N={self.n}  PHYS={self.phys}  "
                 f"WORKERS_LIST={self.workers_list}  POOL={self.pool}")
        needs_emu = not self.steps_filter or any(not t.startswith(("00", "11")) for t in self.steps_filter)
        if not needs_emu:
            return True
        bad = False
        if not (self.emu / "rl" / "run_train" / "probe_throughput.py").is_file():
            self.log(f"ERROR: no emulator checkout at {self.emu}"); bad = True
        if not self.py.is_file():
            self.log(f"ERROR: no python at {self.py}"); bad = True
        if not self.lib.is_file():
            self.log(f"ERROR: no {self.lib}"); bad = True
        if not bad:
            r = subprocess.run([str(self.py), "-c", "import numpy, gymnasium, os; assert hasattr(os, 'nice')"],
                               env=self.env, cwd=self.out, capture_output=True, check=False,
                               creationflags=NO_WINDOW)
            if r.returncode != 0:
                self.log(f"ERROR: {self.py} cannot import numpy and gymnasium, or the os.nice shim is not loaded")
                bad = True
        if bad:
            return False
        head = run_text(["git", "--no-optional-locks", "-C", str(self.emu), "rev-parse", "HEAD"], 30)
        if not head.startswith(PIN):
            self.log(f"WARNING: emulator HEAD {head} is not the pin {PIN}")
        load = busy_cores(self.n)
        if load is not None and load > 1.0:
            self.log(f"WARNING: {load} busy cores before starting; numbers will be low")
        return True

    def run(self) -> int:
        keep_awake(True)
        self.state = "running"
        self.status()
        try:
            if not self.preflight():
                self.state = "failed preflight"
                return 2
            out, emupy = self.out, [str(self.py), "-u"]
            bench = [str(self.py), "-u", str(BENCH_DIR / "sts2bench.py")]
            if self.want("00_env"):
                (out / "00_env.txt").write_text(self.record_env(), encoding="utf-8")
                self.scrub.file(out / "00_env.txt")
                self.log("wrote 00_env.txt")

            # Correctness gates first (design 1071): clone independence / faithfulness / resampling.
            self.step("01_verify_combat", *emupy, "rl/combat_mcts.py", "--verify")
            self.step("01_verify_run", *emupy, "rl/mcts_probe.py", "--section", "invariants")

            # Single core, quiet machine.
            self.step("02_agent_probe", *emupy, "rl/agent_probe.py")
            self.step("03_micro", *emupy, "rl/run_train/probe_throughput.py", "--micro-only",
                      "--json", out / "03_micro.json")
            self.step("04_mcts_search", *emupy, "rl/mcts_probe.py", "--section", "search", "--sims", "300")
            self.step("04_mcts_pressure", *emupy, "rl/mcts_probe.py", "--section", "pressure")
            self.step("05_runs", *emupy, "rl/run_train/probe_throughput.py", "--sims", "60,300",
                      "--runs", self.a.runs, "--no-micro", "--workers", "8", "--json", out / "05_runs.json")
            self.step("06_search", *bench, "search", "--sims", "60,300", "--fights", self.a.search_fights,
                      "--json", out / "06_search.json")

            # Many processes.
            self.step("07_scale", *bench, "scale", "--workers-list", self.workers_list, "--sims", "60",
                      "--fights", self.a.scale_fights, "--json", out / "07_scale.json")
            if self.n >= 8:
                self.step("08_parallel_8", *emupy, "rl/run_train/probe_throughput.py", "--sims", "60",
                          "--runs", "8", "--no-micro", "--workers", "8", "--parallel", "8",
                          "--json", out / "08_parallel_8.json")
            if self.n != 8:
                self.step("08_parallel_N", *emupy, "rl/run_train/probe_throughput.py", "--sims", "60",
                          "--runs", "8", "--no-micro", "--workers", self.n, "--parallel", self.n,
                          "--json", out / "08_parallel_N.json")

            # The c = 0.1 vs 1.4 reproduction (design 1073-1074), same fights at every c, two settings.
            self.step("09_csweep_historical", *bench, "csweep", "--c-values", self.a.c_values,
                      "--fights", self.a.csweep_fights, "--sims", "60", "--rollout", "uniform",
                      "--crn-fraction", "0", "--select", "visits", "--workers", self.pool,
                      "--json", out / "09_csweep_historical.json")
            self.step("09_csweep_current", *bench, "csweep", "--c-values", self.a.c_values,
                      "--fights", self.a.csweep_fights, "--sims", "60", "--rollout", "tempo",
                      "--crn-fraction", "0.2", "--select", "value", "--workers", self.pool,
                      "--json", out / "09_csweep_current.json")

            # CRN variance reduction at the fogmog seed-406 opening (FINDINGS.md:282-304).
            self.step("10_crn_tempo", *bench, "crn", "--encounter", "29", "--seed", "406",
                      "--pairs", self.a.crn_pairs, "--rollout", "tempo", "--json", out / "10_crn_tempo.json")
            self.step("10_crn_uniform", *bench, "crn", "--encounter", "29", "--seed", "406",
                      "--pairs", self.a.crn_pairs, "--rollout", "uniform", "--json", out / "10_crn_uniform.json")

            if self.want("11_collect"):
                self.current = "11_collect"
                self.status()
                with open(out / "11_collect.log", "wb") as f:
                    subprocess.run([sys.executable, str(BENCH_DIR / "collect.py"), str(out)], stdout=f,
                                   stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                                   check=False, creationflags=NO_WINDOW)
                self.scrub.tree(out)
                self.current = None
            self.state = "finished"
            self.log(f"finished; results in {out.name}")
            return 0
        except BaseException as exc:
            self.state = f"driver error: {exc!r}"
            self.log(self.state)
            raise
        finally:
            self.status()
            keep_awake(False)


def parse(argv=None) -> argparse.Namespace:
    env = os.environ.get
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--emu", default=env("EMU") or env("STS2_EMU") or str(BENCH_DIR.parent.parent / "src" / "sts2"))
    ap.add_argument("--py", default=env("PY"), help="default <emu>/.venv/Scripts/python.exe")
    ap.add_argument("--out", default=env("OUT"), help="default bench/results/pc-<date>-<time>")
    ap.add_argument("--steps", default=env("STEPS", ""), help='e.g. "00 01"; empty = all')
    ap.add_argument("--workers-list", default=env("WORKERS_LIST"))
    ap.add_argument("--pool", type=int, default=int(env("POOL", "0")))
    ap.add_argument("--runs", type=int, default=int(env("RUNS", "10")))
    ap.add_argument("--search-fights", type=int, default=int(env("SEARCH_FIGHTS", "16")))
    ap.add_argument("--scale-fights", type=int, default=int(env("SCALE_FIGHTS", "8")))
    ap.add_argument("--c-values", default=env("C_VALUES", "0.1,1.4"))
    ap.add_argument("--csweep-fights", type=int, default=int(env("CSWEEP_FIGHTS", "240")))
    ap.add_argument("--crn-pairs", type=int, default=int(env("CRN_PAIRS", "1500")))
    ap.add_argument("--step-timeout", type=float, default=float(env("STEP_TIMEOUT", "5400")))
    ap.add_argument("--detach", action="store_true", help="relaunch detached and return")
    a = ap.parse_args(argv)
    if not a.out:
        a.out = str(BENCH_DIR / "results" / f"pc-{dt.datetime.now():%Y%m%d-%H%M%S}")
    return a


def detach(a: argparse.Namespace, argv: list) -> int:
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    args = [x for x in argv if x != "--detach"] + ["--out", str(out)]
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    with open(out / "driver.log", "ab") as log:
        for extra in (subprocess.CREATE_BREAKAWAY_FROM_JOB, 0):
            try:
                p = subprocess.Popen([sys.executable, str(Path(__file__).resolve())] + args, cwd=str(out),
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=flags | extra, close_fds=True)
                break
            except OSError:
                if not extra:
                    raise
    print(f"detached pid {p.pid}; progress in {out.name}{os.sep}STATUS.txt")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    a = parse(argv)
    if a.detach:
        return detach(a, argv)
    return Run(a).run()


if __name__ == "__main__":
    sys.exit(main())
