"""The daily health check of the unattended machine (lights-out, D69/D70).

    python tools/health_check.py                      the daily check: read, repair the practice loop, write status/, push it
    python tools/health_check.py --start-daemon       start the practice loop (the fight-loop daemon) if none runs
    python tools/health_check.py --dry-run            print the report; write, repair and push nothing

The daily check reads the lab runner's files, the practice loop's log, the agent folders, the processes and the disk; it plays
nothing and touches no network except `git fetch` and `git push` of its own three status files. It writes (in the Spireline repo)

    status/latest.md    the plain-language status, line 1 `# Spireline status: GREEN|AMBER|RED (YYYY-MM-DD HH:MMZ)`
    status/latest.json  every figure
    status/history.csv  one row a day

and a log under <root>/logs/health (not in the repo). The practice loop is restarted through the scheduled task "Spireline gym daemon"
when it is absent (never from this process). Colours: RED when the runner has been silent two hours, the practice loop is down and
could not be started, disk is under 100 GB, a judge job is stuck, the newest weekly real-game test is over 10 days old, or an alert
file is new; AMBER for a failed job in the last day, a stale QUIET line, a test over 8 days old, a restart by this check, a stop on
purpose (referee/health/STOP), a PAUSE or HALT file, an unreadable process list or a silent practice-loop log; else GREEN.

Everything written passes through tools/landing_evidence.scrub, so no home folder, user name or host name reaches a file.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import landing_evidence as le  # noqa: E402  (scrub: home folder, user name and host name out of every line)
import strict_rows  # noqa: E402  (the shared strict reading of a real block's rows)

UTC = timezone.utc
DEFAULT_ROOT = Path("D:/spireline")

# The practice loop's start line: the one place its arguments live (`--gate-procs` must equal `--procs`).
DAEMON_ARGS: tuple[str, ...] = (
    "rl/gym_loop.py", "run", "--root", "D:/spireline/referee/gym-loop",
    "--max-epochs", "8", "--gate-every-min", "120",
    "--teacher-store", "D:/spireline/referee/run-teacher",
    "--procs", "12", "--gate-procs", "12",
    "--trainer-extra-rows-root", "D:/spireline/referee/run-cheap",
    "--trainer-extra-window", "150000",
    "--rule", "v5",
)
DAEMON_PYTHON = "D:/spireline/src/sts2/.venv/Scripts/python.exe"
DAEMON_CWD = "D:/spireline/fork/wt-gym-loop-run"
DAEMON_NEEDLE = " ".join(DAEMON_ARGS[:4]).lower()  # "rl/gym_loop.py run --root d:/spireline/referee/gym-loop"
RUNNER_NEEDLE = "tools/lab/runner.py"
DAEMON_TASK = "Spireline gym daemon"
SELFTEST_ARGS = ("-c", "import time; time.sleep(300)")

BLOCK_ANCHOR = datetime(2026, 11, 20, 19, 3, tzinfo=UTC)  # the weekly real-game block: every 168 h from here
BLOCK_PERIOD = timedelta(hours=168)
RUNNER_SILENT_S = 2 * 3600
STUCK_LOCK_S = 24 * 3600
DISK_MIN_GB = 100.0
BLOCK_RED_DAYS = 10.0
BLOCK_AMBER_DAYS = 8.0
GYM_SILENT_S = 36 * 3600
RESTART_WAIT_S = 90.0
JANUARY_CONTINUE = 35.0  # D69: player-finished passes per 100 at the first Act 3 boss: 35 or more continues, under 32 closes
JANUARY_CLOSE = 32.0
STATUS_FILES = ("status/latest.md", "status/latest.json", "status/history.csv")
HISTORY_COLUMNS = ("date", "colour", "runner_alive", "daemon_alive", "fights_last_day", "promotions_total", "newest_generation",
                   "last_block", "door_rate_player_finished", "door_rate_all", "disk_free_gb", "repairs")

NO_WINDOW = 0x08000000
BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
NEW_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)

ISO = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"
ISO_RE = re.compile(ISO)
LOG_LINE_RE = re.compile(rf"^({ISO}) (.*)$")
STATUS_RE = re.compile(rf"^({ISO})\s+(\S+)\s*(.*)$")
JOB_FINISHED_RE = re.compile(r"^job (\S+) finished rc=(-?\d+)")
BACKOFF_RE = re.compile(r"^(\S+): not runnable \(backing off")
LIMIT_RE = re.compile(r"killed (?:at|after) (?:its |the )?(\d+)s limit")
STEP_FAILED_RE = re.compile(r"^(\S+): rc=(-?\d+) .*\(FAILED\)\s*$")
TREE_RE = re.compile(r"main moved to ([0-9a-f]{7,40})")
DAILY_RE = re.compile(rf"^({ISO}) daily (\d{{4}}-\d\d-\d\d): (\d+) segments, (\d+) fights played; played ([\d.]+) h.*?waited ([\d.]+) h")
PROMOTED_RE = re.compile(rf"^({ISO}) promoted (c\d+) as v(\d+) over v(\d+) by rule (\S+)(?: \(([^)]*)\))?")
BLOCK_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)(?:T(\d\d)(\d\d))?$")
PID_RE = re.compile(r"\bpid=(\d+)")


# --------------------------------------------------------------------------------------------------------- small helpers
def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except (ValueError, AttributeError):
        return None


def day(s: str | None) -> str:
    return (s or "")[:10]


def stamp(s: str | None) -> str:
    """'2026-11-20T19:04:00Z' -> '2026-11-20 19:04Z'."""
    return f"{s[:10]} {s[11:16]}Z" if s and len(s) >= 16 else (s or "?")


def human_age(seconds: float | None) -> str:
    if seconds is None:
        return "an unknown time"
    s = max(0.0, float(seconds))
    if s < 90:
        return "under two minutes"
    if s < 2 * 3600:
        return f"{round(s / 60)} minutes"
    if s < 48 * 3600:
        return f"{s / 3600:.1f} hours"
    return f"{s / 86400:.1f} days"


def n_(k: int | float) -> str:
    return f"{int(k):,}"


def rate(k: int, n: int) -> dict[str, Any]:
    """k of n as a rate per 100 with two standard errors (the normal approximation the project quotes)."""
    if n <= 0:
        return {"k": k, "n": n, "per100": None, "two_se": None}
    p = k / n
    return {"k": k, "n": n, "per100": round(100.0 * p, 1), "two_se": round(200.0 * math.sqrt(p * (1 - p) / n), 1)}


def read_tail(path: Path, max_bytes: int = 16_000_000) -> str:
    """The text of a file, or its last `max_bytes` (from the first whole line)."""
    with open(path, "rb") as fh:
        size = fh.seek(0, os.SEEK_END)
        cut = size > max_bytes
        fh.seek(max(0, size - max_bytes))
        data = fh.read()
    text = data.decode("utf-8", errors="replace")
    if cut and "\n" in text:
        text = text.split("\n", 1)[1]
    return text


def norm_cmd(s: str | None) -> str:
    return (s or "").replace("\\", "/").lower()


class Env:
    """Where everything lives (a root for the tests, D:/spireline in life)."""

    def __init__(self, root: Path | str = DEFAULT_ROOT, repo: Path | str | None = None):
        self.root = Path(root)
        self.repo = Path(repo) if repo else Path(__file__).resolve().parent.parent
        self.referee = self.root / "referee"
        self.lab = self.referee / "lab"
        self.quiet = self.referee / "QUIET.lock"
        self.gym = self.referee / "gym-loop"
        self.agent = self.referee / "agent"
        self.health = self.referee / "health"
        self.logs = self.root / "logs" / "health"
        self.daemon_out = self.root / "logs" / "gym-loop" / "daemon.out"
        self.daemon_cwd = Path(DAEMON_CWD)
        self.daemon_python = DAEMON_PYTHON

    @property
    def stop_file(self) -> Path:
        return self.health / "STOP"

    @property
    def state_file(self) -> Path:
        return self.health / "state.json"


class Log:
    """health-<date>.log under <root>/logs/health: every line scrubbed, never in the repo; also to stdout where there is one."""

    def __init__(self, env: Env, now: datetime, echo: bool = True, write: bool = True):
        self.path = env.logs / f"health-{now.strftime('%Y-%m-%d')}.log"
        self.echo = echo
        self.write = write
        self.lines: list[str] = []

    def __call__(self, msg: str) -> None:
        line = le.scrub(f"{iso(utc_now())} {msg}")
        self.lines.append(line)
        if self.echo and sys.stdout is not None:
            try:
                print(line)
            except (OSError, UnicodeError, ValueError):
                pass
        if self.write:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
                    fh.write(line + "\n")
            except OSError:
                pass


# ---------------------------------------------------------------------------------------------------------- the processes
PS_SCRIPT = (
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
    "$all=@(Get-CimInstance Win32_Process); "
    "$py=@($all | Where-Object { $_.Name -match '^pythonw?\\.exe$' } | ForEach-Object { "
    "[pscustomobject]@{ProcessId=$_.ProcessId;ParentProcessId=$_.ParentProcessId;Name=$_.Name;CommandLine=$_.CommandLine;"
    "Started=$(if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')}else{''})} }); "
    "[pscustomobject]@{pids=@($all | ForEach-Object { $_.ProcessId }); py=$py} | ConvertTo-Json -Depth 4 -Compress"
)


def parse_started(v: Any) -> str | None:
    """CreationDate as PowerShell 5.1 prints it: our ISO string, '/Date(ms)/' or an ISO with an offset."""
    if not v:
        return None
    s = str(v)
    m = re.search(r"/Date\((-?\d+)", s)
    if m:
        return iso(datetime.fromtimestamp(int(m.group(1)) / 1000.0, UTC))
    if ISO_RE.fullmatch(s):
        return s
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return iso(t if t.tzinfo else t.replace(tzinfo=UTC))
    except ValueError:
        return None


def parse_processes(text: str) -> dict[str, Any]:
    """{'ok', 'procs': [{pid, ppid, name, cmd, started}], 'pids': set | None, 'why'} from the PowerShell JSON (our object, or a bare
    list of processes)."""
    try:
        data = json.loads((text or "").lstrip("\ufeff").strip())
    except ValueError:
        return {"ok": False, "procs": [], "pids": None, "why": "the process list was not readable JSON"}
    if isinstance(data, list):
        py, pids = data, None
    elif isinstance(data, dict):
        py = data.get("py") or []
        pids = data.get("pids")
        if isinstance(py, dict):
            py = [py]
        if isinstance(pids, int):
            pids = [pids]
    else:
        return {"ok": False, "procs": [], "pids": None, "why": "the process list had an unexpected shape"}
    procs = []
    for p in py:
        if not isinstance(p, dict):
            continue
        procs.append({"pid": p.get("ProcessId"), "ppid": p.get("ParentProcessId"), "name": str(p.get("Name") or ""),
                      "cmd": str(p.get("CommandLine") or ""), "started": parse_started(p.get("Started") or p.get("CreationDate"))})
    if pids is None:
        pids = [p["pid"] for p in procs]
    return {"ok": True, "procs": procs, "pids": {int(x) for x in pids if isinstance(x, int)}, "why": ""}


def list_processes() -> dict[str, Any]:
    """Python and pythonw processes with command line and start time, and every process id (Windows PowerShell, read-only)."""
    try:
        cp = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=180, creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "procs": [], "pids": None, "why": f"PowerShell could not be run ({type(e).__name__})"}
    if cp.returncode != 0:
        return {"ok": False, "procs": [], "pids": None, "why": f"PowerShell returned {cp.returncode}"}
    return parse_processes(cp.stdout)


def find_procs(procs: list[dict[str, Any]], needle: str) -> list[dict[str, Any]]:
    """Processes whose command line holds `needle` (slashes and case do not matter). A venv process shows twice (the venv exe and the
    interpreter it starts), so callers read 'at least one' as alive."""
    return [p for p in procs if needle in norm_cmd(p.get("cmd"))]


def run_schtasks(args: list[str]) -> tuple[int, str]:
    try:
        cp = subprocess.run(["schtasks", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                            creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, f"schtasks could not be run ({type(e).__name__})"
    return cp.returncode, (cp.stdout + cp.stderr).strip()


# ---------------------------------------------------------------------------------------------------------- the readers
def read_status(env: Env, now: datetime) -> dict[str, Any]:
    """LAB/status.txt, first line: `<UTC> running|idle ... job=<name> step=<step> since=<UTC> tree=<sha> ...`; its age says the runner lives."""
    p = env.lab / "status.txt"
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        first = lines[0] if lines else ""
    except OSError:
        return {"ok": False, "why": "LAB/status.txt cannot be read"}
    m = STATUS_RE.match(first)
    if not m:
        return {"ok": False, "why": "the first line of LAB/status.txt is not in the usual form"}
    t = parse_iso(m.group(1))
    kv = dict(re.findall(r"(\w+)=(\S+)", m.group(3).split(" | ")[0]))
    job = kv.get("job")
    return {"ok": True, "time": m.group(1), "age_s": round((now - t).total_seconds()) if t else None, "mode": m.group(2),
            "job": job, "job_kind": job.split("-", 1)[1] if job and "-" in job else None, "step": kv.get("step"),
            "since": kv.get("since"), "tree": kv.get("tree")}


def read_runner_log(env: Env, now: datetime, status: dict[str, Any]) -> dict[str, Any]:
    """LAB/runner.log over the last 24 hours: jobs finished and failed, steps that failed, kinds backing off, jobs killed at their limit,
    and the tree the last presort checked out."""
    p = env.lab / "runner.log"
    try:
        text = read_tail(p, 4_000_000)
    except OSError:
        return {"ok": False, "why": "LAB/runner.log cannot be read"}
    since = now - timedelta(hours=24)
    out: dict[str, Any] = {"ok": True, "jobs_finished_24h": 0, "failed_jobs": [], "failed_steps": [], "backoff_kinds": [],
                           "limit_kills": [], "tree": None, "last_line": None}
    for line in text.splitlines():
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        t = parse_iso(m.group(1))
        body = m.group(2)
        out["last_line"] = m.group(1)
        tm = TREE_RE.search(body)
        if tm:
            out["tree"] = tm.group(1)
        if t is None or t < since:
            continue
        jm = JOB_FINISHED_RE.match(body)
        if jm:
            out["jobs_finished_24h"] += 1
            if int(jm.group(2)) != 0:
                out["failed_jobs"].append({"time": m.group(1), "job": jm.group(1), "rc": int(jm.group(2))})
            continue
        sm = STEP_FAILED_RE.match(body)
        if sm:
            out["failed_steps"].append({"time": m.group(1), "step": sm.group(1), "rc": int(sm.group(2))})
            continue
        bm = BACKOFF_RE.match(body)
        if bm:
            if bm.group(1) not in out["backoff_kinds"]:
                out["backoff_kinds"].append(bm.group(1))
            continue
        if LIMIT_RE.search(body) and body.startswith("ALERT"):
            out["limit_kills"].append({"time": m.group(1), "text": body[:160]})
    if not out["tree"] and status.get("tree"):
        out["tree"] = status["tree"]
    out["failed_any"] = bool(out["failed_jobs"] or out["failed_steps"] or out["backoff_kinds"] or out["limit_kills"])
    return out


def read_alerts(env: Env) -> list[dict[str, Any]]:
    """LAB/alerts: every file there is an open alert (name, mtime)."""
    d = env.lab / "alerts"
    out = []
    try:
        for f in sorted(d.iterdir()):
            if f.is_file():
                out.append({"name": f.name, "mtime": iso(datetime.fromtimestamp(f.stat().st_mtime, UTC))})
    except OSError:
        pass
    return out


def block_start(name: str) -> datetime | None:
    m = BLOCK_RE.match(name)
    if not m:
        return None
    y, mo, d, hh, mm = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0), tzinfo=UTC)
    except ValueError:
        return None


def block_generations(folder: Path) -> list[int]:
    out = []
    try:
        for sub in folder.iterdir():
            m = re.fullmatch(r"g(\d+)", sub.name)
            if m and sub.is_dir():
                out.append(int(m.group(1)))
    except OSError:
        pass
    return sorted(out)


def next_block_due(start: datetime | None) -> datetime:
    """The first scheduled slot (every 168 h from the anchor) more than a day after the newest block began."""
    k = 0
    ref = (start or BLOCK_ANCHOR) + timedelta(hours=24)
    while BLOCK_ANCHOR + k * BLOCK_PERIOD <= ref:
        k += 1
    return BLOCK_ANCHOR + k * BLOCK_PERIOD


def read_blocks(env: Env, now: datetime) -> dict[str, Any]:
    """LAB/nightly: the newest real block (a folder named by its start that holds a g<N> folder), `last-ok`, whether one runs now, and the
    next scheduled start."""
    nightly = env.lab / "nightly"
    found: list[tuple[datetime, str, list[int]]] = []
    try:
        for d in nightly.iterdir():
            st = block_start(d.name)
            if st is not None and d.is_dir():
                found.append((st, d.name, block_generations(d)))
    except OSError:
        return {"ok": False, "why": "LAB/nightly cannot be read", "active": False}
    found.sort()
    real = [b for b in found if b[2]]
    pick = (real or found or [None])[-1]
    last_ok = None
    try:
        last_ok = ISO_RE.search((nightly / "last-ok").read_text(encoding="utf-8", errors="replace"))
        last_ok = last_ok.group(0) if last_ok else None
    except OSError:
        pass
    out: dict[str, Any] = {"ok": pick is not None, "active": (nightly / "active").exists(), "last_ok": last_ok, "count": len(found)}
    if pick is None:
        out["why"] = "no block folder under LAB/nightly"
        out["next_due"] = iso(next_block_due(None))
        return out
    st, name, gens = pick
    nd = next_block_due(st)
    out.update({"name": name, "start": iso(st), "age_days": round((now - st).total_seconds() / 86400, 2), "generations": gens,
                "next_due": iso(nd), "overdue": now > nd + timedelta(hours=12) and not (nightly / "active").exists()})
    return out


def read_quiet(env: Env, now: datetime, pids: set[int] | None, status: dict[str, Any]) -> list[dict[str, Any]]:
    """QUIET.lock lines `<tag> <UTC> pid=<windows pid>`: age, whether the pid lives, stale (pid gone), stuck judge (a `lab-train` or
    `lab-nightly` line over 24 h old with no matching job in status.txt)."""
    try:
        text = env.quiet.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    kind = status.get("job_kind") or ""
    out = []
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        t = parse_iso(parts[1]) if len(parts) > 1 else None
        m = PID_RE.search(line)
        pid = int(m.group(1)) if m else None
        age = (now - t).total_seconds() if t else None
        alive = None if (pid is None or pids is None) else pid in pids
        matches = (kind == "train") if parts[0] == "lab-train" else (kind.startswith("nightly") if parts[0] == "lab-nightly" else True)
        out.append({"tag": parts[0], "time": parts[1] if t else None, "age_s": None if age is None else round(age), "pid": pid,
                    "pid_alive": alive, "stale": alive is False,
                    "stuck": parts[0] in ("lab-train", "lab-nightly") and age is not None and age > STUCK_LOCK_S and not matches})
    return out


def read_gym(env: Env, now: datetime) -> dict[str, Any]:
    """gym-loop/loop.log: the daily lines (fights, hours played and waited), the fighters promoted, the last line's age."""
    p = env.gym / "loop.log"
    try:
        text = read_tail(p, 16_000_000)
    except OSError:
        return {"ok": False, "why": "gym-loop/loop.log cannot be read", "daily": [], "promoted": []}
    daily: list[dict[str, Any]] = []
    promoted: list[dict[str, Any]] = []
    last = None
    for line in text.splitlines():
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        last = m.group(1)
        dm = DAILY_RE.match(line)
        if dm:
            daily.append({"written": dm.group(1), "date": dm.group(2), "segments": int(dm.group(3)), "fights": int(dm.group(4)),
                          "played_h": float(dm.group(5)), "waited_h": float(dm.group(6))})
            continue
        pm = PROMOTED_RE.match(line)
        if pm:
            promoted.append({"time": pm.group(1), "candidate": pm.group(2), "version": int(pm.group(3)), "over": int(pm.group(4)),
                             "rule": pm.group(5), "route": (pm.group(6) or "")[:60]})
    t = parse_iso(last) if last else None
    return {"ok": True, "daily": daily[-7:], "daily_total": len(daily), "promoted": promoted[-8:], "promotions_total": len(promoted),
            "newest_version": max((x["version"] for x in promoted), default=None), "last_line": last,
            "last_line_age_s": round((now - t).total_seconds()) if t else None}


def read_agent(env: Env) -> dict[str, Any]:
    """referee/agent: the newest gen<N> folder, current.json (the champion), promotions.tsv (the whole-run judge's rows)."""
    out: dict[str, Any] = {"ok": True, "newest_generation": None, "champion": None, "judgements": []}
    try:
        gens = [int(m.group(1)) for d in env.agent.iterdir() if d.is_dir() and (m := re.fullmatch(r"gen(\d+)", d.name))]
        out["newest_generation"] = max(gens) if gens else None
    except OSError:
        out["ok"] = False
        out["why"] = "referee/agent cannot be read"
        return out
    try:
        cur = json.loads((env.agent / "current.json").read_text(encoding="utf-8", errors="replace"))
        out["champion"] = {"generation": cur.get("generation"), "promoted": cur.get("promoted"),
                           "folder": Path(str(cur.get("dir", "")).replace("\\", "/")).name}
    except (OSError, ValueError):
        pass
    try:
        with open(env.agent / "promotions.tsv", encoding="utf-8", errors="replace", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        out["judgement_count"] = len(rows)
        out["judgements"] = [{"written": r.get("written"), "cand_gen": r.get("cand_gen"), "candidate": r.get("cand_dir"),
                              "seeds": r.get("seeds"), "decision": r.get("decision")} for r in rows[-12:]]
    except OSError:
        out["judgement_count"] = 0
    return out


def door_reading(env: Env, log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """The newest finished real block read by the strict reader (tools/strict_rows.py): passes of the first Act 3 boss per 100 arrivals,
    per 100 fights the player finished itself, lost-track arrivals; the January rule's reading of the player-finished figure."""
    nightly = env.lab / "nightly"
    cands: list[tuple[datetime, str, Path, int]] = []
    try:
        for d in nightly.iterdir():
            st = block_start(d.name)
            gens = block_generations(d) if st else []
            for g in reversed(gens):
                gd = d / f"g{g}"
                if (gd / "runs.jsonl").is_file() and ((gd / "summary.json").is_file() or (gd / "result.json").is_file()):
                    cands.append((st, d.name, gd, g))
                    break
    except OSError:
        return {"ok": False, "why": "LAB/nightly cannot be read"}
    if not cands:
        return {"ok": False, "why": "no finished real block holds runs.jsonl"}
    cands.sort(key=lambda c: c[0])
    st, name, gd, g = cands[-1]
    try:
        ended, crashes, _filled = strict_rows.read_block(gd)
        g_ = strict_rows.block_reading(ended)
    except Exception as e:  # noqa: BLE001  (a reading that fails must not stop the check)
        if log:
            log(f"door reading failed: {type(e).__name__}: {e}")
        return {"ok": False, "why": f"the strict reader failed ({type(e).__name__})", "block": name, "generation": g}
    arr = g_["arrivals"]
    fin = g_["finished"]
    pf = rate(g_["finished_passes"], fin)
    al = rate(g_["passes"], arr)
    if pf["per100"] is None:
        verdict = "no reading"
    elif pf["per100"] >= JANUARY_CONTINUE:
        verdict = "continue"
    elif pf["per100"] < JANUARY_CLOSE:
        verdict = "close"
    else:
        verdict = "one more block"
    return {"ok": True, "block": name, "generation": g, "ended_rows": g_["ended"], "crash_rows": len(crashes), "arrivals": arr,
            "all": al, "player_finished": pf, "lost_track": rate(g_["lost_track"], arr), "january": verdict}


# --------------------------------------------------------------------------------------------------------------- collecting
def daemon_info(env: Env, procs: dict[str, Any]) -> dict[str, Any]:
    found = find_procs(procs["procs"], DAEMON_NEEDLE) if procs.get("ok") else []
    starts = [p["started"] for p in found if p.get("started")]
    return {"process_list_ok": bool(procs.get("ok")), "why": procs.get("why", ""), "pids": sorted(int(p["pid"]) for p in found if p.get("pid")),
            "alive": bool(found), "started": min(starts) if starts else None, "stop_file": env.stop_file.exists(),
            "halt_file": (env.lab / "HALT").exists(), "restarted": False, "restart_pid": None, "restart_tried": False,
            "could_not_start": False, "restart_note": ""}


def collect(env: Env, now: datetime, procs: dict[str, Any], disk_fn: Callable[[str], Any], log: Callable[[str], None]) -> dict[str, Any]:
    """Every figure the check reads, in one dict (the content of status/latest.json before the colour and the repairs are added)."""
    status = read_status(env, now)
    pids = procs.get("pids") if procs.get("ok") else None
    runner_procs = find_procs(procs["procs"], RUNNER_NEEDLE) if procs.get("ok") else []
    alive = bool(status.get("ok") and status.get("age_s") is not None and status["age_s"] <= RUNNER_SILENT_S)
    try:
        du = disk_fn(env.root.anchor or str(env.root))
        disk = {"ok": True, "free_gb": round(du.free / 2**30, 1), "total_gb": round(du.total / 2**30, 1)}
    except OSError:
        disk = {"ok": False, "free_gb": None, "total_gb": None}
    fig: dict[str, Any] = {
        "checked": iso(now), "date": now.strftime("%Y-%m-%d"),
        "runner": {"alive": alive, "status": status, "process_pids": sorted(int(p["pid"]) for p in runner_procs if p.get("pid")),
                   "log": read_runner_log(env, now, status)},
        "daemon": daemon_info(env, procs),
        "gym": read_gym(env, now),
        "agent": read_agent(env),
        "blocks": read_blocks(env, now),
        "quiet": read_quiet(env, now, pids, status),
        "alerts": read_alerts(env),
        "disk": disk,
        "files": {"health_stop": env.stop_file.exists(), "lab_halt": (env.lab / "HALT").exists(), "lab_pause": (env.lab / "PAUSE").exists()},
    }
    fig["door"] = door_reading(env, log)
    return fig


# ----------------------------------------------------------------------------------------------------------------- state
def load_state(env: Env) -> dict[str, Any]:
    try:
        d = json.loads(env.state_file.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def new_state(fig: dict[str, Any], colour: str, git: dict[str, Any]) -> dict[str, Any]:
    gym, agent, blocks = fig["gym"], fig["agent"], fig["blocks"]
    return {"checked": fig["checked"], "colour": colour, "alerts": {a["name"]: a["mtime"] for a in fig["alerts"]},
            "fighter_promotions_total": gym.get("promotions_total"), "newest_generation": agent.get("newest_generation"),
            "champion_generation": (agent.get("champion") or {}).get("generation"), "judgement_count": agent.get("judgement_count"),
            "last_block": blocks.get("name"), "last_push": {"time": fig["checked"], "status": git.get("status"), "why": git.get("why", "")}}


def since_last(fig: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """What changed since the previous check (everything is new when there is no earlier check)."""
    first = not state
    prev_t = state.get("checked") or ""
    prev_alerts = state.get("alerts") or {}
    alerts = fig["alerts"]
    new_alerts = [a for a in alerts if a["name"] not in prev_alerts or (prev_t and a["mtime"] > prev_t)]
    gone = sorted(n for n in prev_alerts if n not in {a["name"] for a in alerts})
    gym, agent, blocks = fig["gym"], fig["agent"], fig["blocks"]
    promoted = [p for p in gym.get("promoted", []) if first or p["time"] > prev_t]
    judgements = [j for j in agent.get("judgements", []) if first or (j.get("written") or "") > prev_t]
    newest = agent.get("newest_generation")
    champ = (agent.get("champion") or {}).get("generation")
    return {"first_check": first, "previous_check": prev_t or None, "new_alerts": new_alerts, "alerts_gone": gone,
            "promotions": promoted if not first else [], "judgements": judgements if not first else [],
            "new_generation": None if first or newest is None or newest == state.get("newest_generation") else newest,
            "champion_changed": None if first or champ is None or champ == state.get("champion_generation") else champ,
            "new_block": None if first or not blocks.get("name") or blocks.get("name") == state.get("last_block") else blocks["name"],
            "previous_push": state.get("last_push")}


# ------------------------------------------------------------------------------------------------------------------ repairs
def ensure_daemon(env: Env, fig: dict[str, Any], *, procs_fn: Callable[[], dict[str, Any]], schtasks_fn: Callable[[list[str]], tuple[int, str]],
                  sleep: Callable[[float], None], log: Callable[[str], None], wait_s: float = RESTART_WAIT_S, poll_s: float = 5.0) -> list[str]:
    """When no practice loop runs (and no STOP or HALT file asks for that), start it through the scheduled task and wait for its process."""
    d = fig["daemon"]
    if d["alive"]:
        return []
    if not d["process_list_ok"]:
        log(f"the process list could not be read ({d['why']}): the practice loop is not restarted")
        return []
    if d["stop_file"] or d["halt_file"]:
        why = "referee/health/STOP" if d["stop_file"] else "LAB/HALT"
        d["restart_note"] = f"not started: {why} exists"
        log(f"the practice loop is down and {why} exists: left stopped")
        return []
    d["restart_tried"] = True
    rc, out = schtasks_fn(["/run", "/tn", DAEMON_TASK])
    log(f"schtasks /run '{DAEMON_TASK}': rc={rc} {out[:200]}")
    if rc != 0:
        d["could_not_start"] = True
        d["restart_note"] = f"the scheduled task '{DAEMON_TASK}' could not be run ({out[:120] or 'no output'})"
        return [d["restart_note"]]
    for _ in range(max(1, int(wait_s // poll_s))):
        sleep(poll_s)
        pr = procs_fn()
        found = find_procs(pr["procs"], DAEMON_NEEDLE) if pr.get("ok") else []
        if found:
            d.update(alive=True, restarted=True, pids=sorted(int(p["pid"]) for p in found if p.get("pid")),
                     started=min((p["started"] for p in found if p.get("started")), default=None))
            d["restart_pid"] = d["pids"][0] if d["pids"] else None
            d["restart_note"] = f"the practice loop was down; started through the scheduled task '{DAEMON_TASK}' (process {d['restart_pid']})"
            log(d["restart_note"])
            return [d["restart_note"]]
    d["could_not_start"] = True
    d["restart_note"] = f"the scheduled task '{DAEMON_TASK}' ran but no practice loop process appeared within {int(wait_s)} seconds"
    log(d["restart_note"])
    return [d["restart_note"]]


# ------------------------------------------------------------------------------------------------------------------ colour
def decide(fig: dict[str, Any], since: dict[str, Any]) -> tuple[str, list[tuple[str, str]]]:
    """(colour, [(level, plain reason)]) by the brief's rules; RED beats AMBER beats GREEN."""
    R: list[tuple[str, str]] = []
    r, d, g, b = fig["runner"], fig["daemon"], fig["gym"], fig["blocks"]
    st = r["status"]
    if not r["alive"]:
        if st.get("ok"):
            R.append(("RED", f"the lab runner has not reported for {human_age(st.get('age_s'))} (it reports every five minutes)"))
        else:
            R.append(("RED", f"the lab runner's status file cannot be read ({st.get('why')})"))
    if d["process_list_ok"] and not d["alive"] and not d["stop_file"] and not d["halt_file"]:
        R.append(("RED", "the practice loop is not running" + (f" and could not be started ({d['restart_note']})" if d["restart_note"] else "")))
    free = fig["disk"].get("free_gb")
    if free is not None and free < DISK_MIN_GB:
        R.append(("RED", f"only {free:.0f} GB of disk is free (the limit is {DISK_MIN_GB:.0f} GB)"))
    for q in fig["quiet"]:
        if q["stuck"]:
            R.append(("RED", f"a judge job looks stuck: the '{q['tag']}' line in the machine's lock file is {human_age(q['age_s'])} old and no matching job runs"))
    if not b.get("ok"):
        R.append(("RED", f"no weekly real-game test was found ({b.get('why')})"))
    elif b["age_days"] > BLOCK_RED_DAYS:
        R.append(("RED", f"the newest weekly real-game test began {b['age_days']:.1f} days ago (the limit is {BLOCK_RED_DAYS:.0f})"))
    for a in since["new_alerts"]:
        R.append(("RED", f"a new alert file appeared: {a['name']}"))
    rl = r["log"]
    if rl.get("ok") and rl.get("failed_any"):
        bits = []
        if rl["failed_jobs"]:
            bits.append(f"{len(rl['failed_jobs'])} job(s) ended with an error")
        if rl["failed_steps"]:
            bits.append(f"{len(rl['failed_steps'])} step(s) failed")
        if rl["backoff_kinds"]:
            bits.append("backing off after repeated failures: " + ", ".join(rl["backoff_kinds"]))
        if rl["limit_kills"]:
            bits.append(f"{len(rl['limit_kills'])} job(s) killed at their time limit")
        R.append(("AMBER", "the lab runner's log shows trouble in the last day (" + "; ".join(bits) + ")"))
    for q in fig["quiet"]:
        if q["stale"]:
            R.append(("AMBER", f"a stale line stands in the machine's lock file: '{q['tag']}' names process {q['pid']}, which is gone"))
    if b.get("ok") and BLOCK_AMBER_DAYS < b["age_days"] <= BLOCK_RED_DAYS:
        R.append(("AMBER", f"the newest weekly real-game test began {b['age_days']:.1f} days ago (a week is due)"))
    if d["restarted"]:
        R.append(("AMBER", "this check had to restart the practice loop"))
    if d["stop_file"]:
        R.append(("AMBER", "stopped on purpose: the file referee/health/STOP exists, so the practice loop is not restarted"))
    if fig["files"]["lab_halt"]:
        R.append(("AMBER", "the lab has a HALT file: it does no work until the file is removed"))
    if fig["files"]["lab_pause"]:
        R.append(("AMBER", "the lab has a PAUSE file: it waits until the file is removed"))
    if not d["process_list_ok"]:
        R.append(("AMBER", f"the process list could not be read ({d['why']}), so the practice loop was not checked"))
    if d["alive"] and g.get("ok") and g.get("last_line_age_s") is not None and g["last_line_age_s"] > GYM_SILENT_S:
        R.append(("AMBER", f"the practice loop's log has been silent for {human_age(g['last_line_age_s'])}"))
    if d["alive"] and not g.get("ok"):
        R.append(("AMBER", f"the practice loop's log cannot be read ({g.get('why')})"))
    colour = "RED" if any(lv == "RED" for lv, _ in R) else "AMBER" if R else "GREEN"
    return colour, R


# ----------------------------------------------------------------------------------------------------------------- writing
JOB_WORDS = {
    "train": "a whole-run judgement of a new fighter", "nightly-real": "the weekly real-game test", "presort": "a routine check of the code tree",
    "teacher": "plain full runs that teach the learner", "runs": "plain full runs", "student": "a student check", "selfplay": "self-play",
    "fights": "aimed fights", "invariants": "invariant checks", "mutation": "mutation checks", "score-real": "a real-game scoring job",
    "bench-emu": "a speed benchmark", "bench-env": "a speed benchmark",
}


def job_words(kind: str | None) -> str:
    return JOB_WORDS.get(kind or "", f"a '{kind}' job" if kind else "no job")


def rate_words(r: dict[str, Any] | None) -> str:
    """'26.2 in 100, give or take 5.4'."""
    if not r or r.get("per100") is None:
        return "no reading"
    return f"{r['per100']:.1f} in 100, give or take {r['two_se']:.1f}"


def per100(r: dict[str, Any] | None) -> str:
    if not r or r.get("per100") is None:
        return "no reading"
    return f"{r['k']} of {r['n']}, {r['per100']:.1f} in 100, give or take {r['two_se']:.1f}"


def paragraphs(fig: dict[str, Any], since: dict[str, Any], now: datetime) -> list[str]:
    r, d, g, a, b, door = fig["runner"], fig["daemon"], fig["gym"], fig["agent"], fig["blocks"], fig["door"]
    st = r["status"]
    P: list[str] = []
    # the lab runner
    if r["alive"]:
        what = ("idle" if st.get("mode") == "idle" else f"busy with {job_words(st.get('job_kind'))}")
        txt = f"**The lab runner** (the scheduler that runs the judge and the weekly test) is working: it last reported {human_age(st.get('age_s'))} ago and is {what}."
    elif st.get("ok"):
        txt = (f"**The lab runner** (the scheduler that runs the judge and the weekly test) has not reported for {human_age(st.get('age_s'))}; "
               "it normally reports every five minutes. The Windows task 'Spireline fix lab' should restart it; it needs a look.")
    else:
        txt = f"**The lab runner** could not be checked: {st.get('why')}."
    rl = r["log"]
    if rl.get("ok"):
        txt += f" In the last day it finished {rl['jobs_finished_24h']} jobs" + ("; none failed." if not rl["failed_any"] else
               f"; trouble: {len(rl['failed_jobs'])} ended with an error, {len(rl['failed_steps'])} steps failed, {len(rl['backoff_kinds'])} kinds are backing off, {len(rl['limit_kills'])} were killed at their time limit.")
    P.append(txt)
    # the practice loop
    if d["alive"]:
        since_txt = f" (since {stamp(d['started'])})" if d["started"] else ""
        txt = f"**The practice loop** (the loop that plays fights to train the fighter) is running{since_txt}."
        if d["restarted"]:
            txt = (f"**The practice loop** (the loop that plays fights to train the fighter) was not running; this check started it through its scheduled task "
                   f"and it is running now (process {d['restart_pid']}).")
        daily = (g.get("daily") or [])[-1:] if g.get("ok") else []
        if daily:
            x = daily[0]
            txt += (f" Its newest daily summary, for {x['date']}, says it played {n_(x['fights'])} fights: {x['played_h']:.1f} hours playing, "
                    f"{x['waited_h']:.1f} hours waiting (it waits while the judge or the weekly test holds the machine).")
            try:
                lag = (now.date() - datetime.strptime(x["date"], "%Y-%m-%d").date()).days
            except ValueError:
                lag = 1
            if lag > 1:
                txt += f" That summary is {lag} days old, so at least one day's summary is missing."
        else:
            txt += " It has written no daily summary yet."
        if g.get("ok") and g.get("last_line_age_s") is not None:
            txt += f" Its log last wrote {human_age(g['last_line_age_s'])} ago."
        if g.get("ok") and g.get("promotions_total"):
            p = g["promoted"][-1]
            txt += f" {g['promotions_total']} fighter versions have been promoted in all; the newest is v{p['version']} ({day(p['time'])})."
    elif d["stop_file"] or d["halt_file"]:
        txt = ("**The practice loop** is stopped on purpose (" + ("the file referee/health/STOP exists" if d["stop_file"] else "the lab's HALT file exists")
               + "); this check does not restart it.")
    elif not d["process_list_ok"]:
        txt = f"**The practice loop** could not be checked: the process list was unreadable ({d['why']})."
    else:
        txt = "**The practice loop** is NOT running" + (f" and could not be started: {d['restart_note']}." if d["restart_note"] else ".")
    P.append(txt)
    # the whole-run judge and the champion
    champ = a.get("champion") or {}
    txt = "**The whole-run judge** (the test that decides whether a new fighter is kept) "
    if a.get("ok") and champ:
        txt += f"has the champion at generation {champ.get('generation')} (promoted {day(champ.get('promoted'))}); the newest generation folder is gen{a.get('newest_generation')}."
        j = (a.get("judgements") or [])[-1:]
        if j:
            txt += (f" It has finished {a.get('judgement_count', 0)} judgements in all; the last, on {day(j[0]['written'])}, was {j[0]['decision']} "
                    f"for {j[0]['candidate']} on {j[0]['seeds']} paired runs.")
    else:
        txt += f"could not be read ({a.get('why', 'no champion file')})."
    running = [q for q in fig["quiet"] if q["tag"] in ("lab-train", "lab-nightly")]
    if running:
        q = running[0]
        txt += (f" A judge job is running now (its lock line is {human_age(q['age_s'])} old)." if not q["stuck"]
                else f" A judge job looks stuck (its lock line is {human_age(q['age_s'])} old).")
    P.append(txt)
    # the weekly real-game test
    if b.get("ok"):
        due = parse_iso(b["next_due"])
        until = (due - now).total_seconds() if due else None
        txt = f"**The weekly real-game test** last ran on {day(b['start'])} (it began {stamp(b['start'])}"
        txt += f" and finished {stamp(b['last_ok'])})." if b.get("last_ok") and b["last_ok"] >= b["start"] else ")."
        if b.get("active"):
            txt += " One is running right now."
        txt += f" The next is due {day(b['next_due'])}" + (f", in {human_age(until)}" if until and until > 0 and not b.get("active") else "")
        txt += ". It is overdue." if b.get("overdue") else "."
    else:
        txt = f"**The weekly real-game test** could not be found ({b.get('why')})."
    P.append(txt)
    # the first Act 3 boss
    if door.get("ok"):
        pf, al, lt = door["player_finished"], door["all"], door["lost_track"]
        bs = block_start(door["block"])
        reading = {"continue": "a case to continue", "close": "under the stop line", "one more block": "between the two lines, so one more test"}.get(
            door["january"], "not available")
        txt = (f"**Getting past the first Act 3 boss.** In the newest finished test ({bs.strftime('%Y-%m-%d') if bs else door['block']}, "
               f"generation {door['generation']}, {door['ended_rows'] + door['crash_rows']} runs) the player got past the first Act 3 boss in "
               f"{pf['k']} of the {pf['n']} fights it finished itself: {rate_words(pf)}. "
               f"Counting every arrival at that boss, including fights where the referee lost its place and a stand-in played on, it is "
               f"{al['k']} of {al['n']}: {rate_words(al)}; the stand-in played on in {lt['k']} of those {lt['n']} arrivals. "
               f"The January rule says {JANUARY_CONTINUE:.0f} or more in 100 means continue and under {JANUARY_CLOSE:.0f} means stop; "
               f"in between, one more test. The reading today is {reading}.")
    else:
        txt = f"**Getting past the first Act 3 boss.** The newest test could not be read ({door.get('why')})."
    P.append(txt)
    # disk and alerts
    dk = fig["disk"]
    P.append(f"**Disk.** {dk['free_gb']:.0f} GB free of {dk['total_gb']:.0f} GB." if dk.get("ok") else "**Disk.** The free space could not be read.")
    if fig["alerts"]:
        P.append("**Open alerts.** " + ", ".join(f"{x['name']} (changed {day(x['mtime'])})" for x in fig["alerts"]) + ".")
    else:
        P.append("**Open alerts.** None.")
    return P


def since_lines(since: dict[str, Any]) -> list[str]:
    if since["first_check"]:
        return ["This is the first check, so there is nothing earlier to compare with."]
    out = [f"Since the check of {stamp(since['previous_check'])}:"]
    n0 = len(out)
    for p in since["promotions"]:
        out.append(f"- The practice loop promoted fighter v{p['version']} over v{p['over']} on {stamp(p['time'])}.")
    if since["new_generation"] is not None:
        out.append(f"- A new generation folder appeared: gen{since['new_generation']}.")
    if since["champion_changed"] is not None:
        out.append(f"- The champion changed: generation {since['champion_changed']} now leads.")
    for j in since["judgements"]:
        out.append(f"- The whole-run judge finished a judgement on {j['candidate']} ({stamp(j['written'])}): {j['decision']}, {j['seeds']} paired runs.")
    if since["new_block"]:
        out.append(f"- A new weekly real-game test folder appeared: {since['new_block']}.")
    for a in since["new_alerts"]:
        out.append(f"- New alert: {a['name']}.")
    for name in since["alerts_gone"]:
        out.append(f"- Alert cleared: {name}.")
    if len(out) == n0:
        out.append("- Nothing new.")
    return out


def raw_rows(fig: dict[str, Any], colour: str) -> list[tuple[str, str]]:
    r, d, g, a, b, door = fig["runner"], fig["daemon"], fig["gym"], fig["agent"], fig["blocks"], fig["door"]
    st, rl = r["status"], r["log"]
    daily = (g.get("daily") or [])[-1:] if g.get("ok") else []
    rows = [
        ("colour", colour), ("checked", stamp(fig["checked"])),
        ("runner status age (s)", str(st.get("age_s"))), ("runner processes", str(len(r["process_pids"]))),
        ("runner job now", f"{st.get('job')} ({st.get('step')})" if st.get("ok") else "unknown"),
        ("jobs finished, last 24 h", str(rl.get("jobs_finished_24h")) if rl.get("ok") else "unknown"),
        ("failed jobs / steps, last 24 h", f"{len(rl.get('failed_jobs', []))} / {len(rl.get('failed_steps', []))}" if rl.get("ok") else "unknown"),
        ("kinds backing off", ", ".join(rl.get("backoff_kinds", [])) or "none"), ("last tree checked out", str(rl.get("tree"))),
        ("practice loop processes", str(len(d["pids"]))), ("practice loop running since", stamp(d["started"]) if d["started"] else "n/a"),
        ("practice loop log age (s)", str(g.get("last_line_age_s"))),
        ("newest daily summary", f"{daily[0]['date']}: {daily[0]['fights']} fights, {daily[0]['played_h']} h played, {daily[0]['waited_h']} h waited" if daily else "none"),
        ("fighters promoted in all", str(g.get("promotions_total"))), ("newest fighter version", str(g.get("newest_version"))),
        ("champion generation", str((a.get("champion") or {}).get("generation"))), ("newest generation folder", str(a.get("newest_generation"))),
        ("judgements finished", str(a.get("judgement_count"))),
        ("newest weekly test", str(b.get("name"))), ("weekly test age (days)", str(b.get("age_days"))), ("next weekly test due", stamp(b.get("next_due"))),
        ("test running now", "yes" if b.get("active") else "no"),
        ("door passes, player-finished", per100(door.get("player_finished")) if door.get("ok") else "no reading"),
        ("door passes, all arrivals", per100(door.get("all")) if door.get("ok") else "no reading"),
        ("lost-track arrivals", per100(door.get("lost_track")) if door.get("ok") else "no reading"),
        ("disk free (GB)", str(fig["disk"].get("free_gb"))),
        ("lock-file lines", ", ".join(f"{q['tag']} ({human_age(q['age_s'])})" for q in fig["quiet"]) or "none"),
        ("open alert files", str(len(fig["alerts"]))),
    ]
    return rows


def render_markdown(fig: dict[str, Any], colour: str, reasons: list[tuple[str, str]], since: dict[str, Any], repairs: list[str],
                    now: datetime) -> str:
    L = [f"# Spireline status: {colour} ({stamp(fig['checked'])})", "",
         "Written by the daily health check from the machine's own files. It plays nothing: it reads, restarts the practice loop if that is down, and publishes this page.", ""]
    if colour == "GREEN":
        L += ["**In short.** GREEN: everything is running and nothing needs attention.", ""]
    else:
        L += [f"**In short.** {colour}: " + ("something needs attention." if colour == "RED" else "worth a look, but the machine is working."), ""]
        L += [f"- {lv}: {text}" for lv, text in reasons] + [""]
    for p in paragraphs(fig, since, now):
        L += [p, ""]
    L += ["## Since the last check", ""] + since_lines(since) + [""]
    L += ["## Repairs", ""] + ([f"- {x}" for x in repairs] if repairs else ["- Nothing needed repair."]) + [""]
    L += ["## The figures", "", "| figure | value |", "| --- | --- |"] + [f"| {k} | {v} |" for k, v in raw_rows(fig, colour)] + [""]
    return "\n".join(L)


def scrub_text(text: str) -> str:
    return "\n".join(le.scrub(line) for line in text.split("\n"))


def history_row(fig: dict[str, Any], colour: str, repair_codes: list[str]) -> dict[str, Any]:
    door, g, a, b = fig["door"], fig["gym"], fig["agent"], fig["blocks"]
    daily = (g.get("daily") or [])[-1:] if g.get("ok") else []
    return {"date": fig["date"], "colour": colour, "runner_alive": "yes" if fig["runner"]["alive"] else "no",
            "daemon_alive": "yes" if fig["daemon"]["alive"] else "no", "fights_last_day": daily[0]["fights"] if daily else "",
            "promotions_total": g.get("promotions_total", ""), "newest_generation": a.get("newest_generation") or "",
            "last_block": b.get("name") or "",
            "door_rate_player_finished": (door.get("player_finished") or {}).get("per100", "") if door.get("ok") else "",
            "door_rate_all": (door.get("all") or {}).get("per100", "") if door.get("ok") else "",
            "disk_free_gb": fig["disk"].get("free_gb", ""), "repairs": ";".join(repair_codes) or "none"}


def write_history(path: Path, row: dict[str, Any]) -> None:
    """status/history.csv: one row a day (a second check the same day replaces that day's row)."""
    rows: list[dict[str, str]] = []
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r.get("date") != row["date"]]
    except OSError:
        pass
    rows.append({k: str(row.get(k, "")) for k in HISTORY_COLUMNS})
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(HISTORY_COLUMNS), lineterminator="\n")
        w.writeheader()
        w.writerows({k: le.scrub(str(v)) for k, v in r.items()} for r in rows)


def write_outputs(env: Env, md: str, doc: dict[str, Any], row: dict[str, Any]) -> None:
    d = env.repo / "status"
    d.mkdir(parents=True, exist_ok=True)
    (d / "latest.md").write_text(scrub_text(md) + ("" if md.endswith("\n") else "\n"), encoding="utf-8", newline="\n")
    (d / "latest.json").write_text(scrub_text(json.dumps(doc, indent=1, default=str)) + "\n", encoding="utf-8", newline="\n")
    write_history(d / "history.csv", row)


def save_state(env: Env, state: dict[str, Any]) -> None:
    env.health.mkdir(parents=True, exist_ok=True)
    tmp = env.state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
    os.replace(tmp, env.state_file)


# ---------------------------------------------------------------------------------------------------------------------- git
def make_git(repo: Path) -> Callable[[list[str]], tuple[int, str]]:
    def git(args: list[str]) -> tuple[int, str]:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        try:
            cp = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=300, env=env, creationflags=NO_WINDOW)
        except (OSError, subprocess.SubprocessError) as e:
            return 1, f"git could not be run ({type(e).__name__})"
        # stdout alone when it worked (a warning on stderr must not become a line of `status --porcelain`); only the trailing end is
        # trimmed, because the first column of a porcelain line is a space for an unstaged change
        return cp.returncode, (cp.stdout if cp.returncode == 0 else cp.stdout + cp.stderr).rstrip()
    return git


def parse_porcelain(text: str) -> tuple[list[str], list[str]]:
    """(staged, modified) tracked paths outside status/ from `git status --porcelain` (untracked files are neither: nothing here adds them)."""
    staged, modified = [], []
    for line in text.splitlines():
        if len(line) < 4:
            continue
        xy, path = line[:2], line[3:].split(" -> ")[-1].strip('"')
        if path.startswith("status/") or xy == "??" or xy == "!!":
            continue
        if xy[0] not in " ?":
            staged.append(path)
        if xy[1] not in " ?":
            modified.append(path)
    return staged, modified


def git_preflight(git: Callable[[list[str]], tuple[int, str]], allow_dirty: bool, log: Callable[[str], None]) -> dict[str, Any]:
    """Whether the status files may be committed and pushed: after `git fetch origin`, HEAD is main and is origin/main (or ahead of it by
    this check's own status commits only), and nothing is staged or modified outside status/ (unless `allow_dirty`: the commit then names
    only the three status files, so other work is neither committed nor touched). A clean main that is behind origin/main is brought
    forward with `merge --ff-only`."""
    out: dict[str, Any] = {"status": "skipped", "can_push": False, "why": "", "notes": []}
    rc, txt = git(["fetch", "origin"])
    if rc != 0:
        out["why"] = f"git fetch failed ({txt[:120]})"
        log(out["why"])
        return out
    rc, branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0 or branch.strip() != "main":
        out["why"] = f"the repo is on '{branch.strip()[:40]}', not main"
        log(out["why"])
        return out
    rc, counts = git(["rev-list", "--left-right", "--count", "origin/main...HEAD"])
    try:
        behind, ahead = (int(x) for x in counts.split()[:2])
    except ValueError:
        out["why"] = f"could not compare HEAD with origin/main ({counts[:80]})"
        log(out["why"])
        return out
    rc, porcelain = git(["status", "--porcelain"])
    staged, modified = parse_porcelain(porcelain)
    if (staged or modified) and not allow_dirty:
        names = ", ".join((staged + modified)[:3])
        out["why"] = (f"the tree has {len(staged)} staged and {len(modified)} modified file(s) outside status/ ({names}); "
                      "the push is skipped until they are committed or reverted")
        log(out["why"])
        return out
    if staged or modified:
        out["notes"].append(f"the tree holds {len(staged)} staged and {len(modified)} modified file(s) outside status/; they are left alone")
    if behind and ahead:
        out["why"] = f"local main and origin/main have both moved (behind {behind}, ahead {ahead}); needs a person"
        log(out["why"])
        return out
    if ahead:
        rc, subjects = git(["log", "--format=%s", "origin/main..HEAD"])
        if rc != 0 or any(not s.startswith("status: ") for s in subjects.splitlines() if s.strip()):
            out["why"] = f"local main is {ahead} commit(s) ahead of origin/main and they are not all status commits"
            log(out["why"])
            return out
        out["notes"].append(f"{ahead} earlier status commit(s) were not pushed yet; they go with this one")
    if behind:
        if staged or modified:
            out["why"] = f"local main is {behind} commit(s) behind origin/main and the tree is not clean, so it cannot be brought forward"
            log(out["why"])
            return out
        rc, txt = git(["merge", "--ff-only", "origin/main"])
        if rc != 0:
            out["why"] = f"local main is {behind} commit(s) behind origin/main and 'merge --ff-only' failed ({txt[:100]})"
            log(out["why"])
            return out
        out["notes"].append(f"local main was {behind} commit(s) behind origin/main and was brought forward (fast-forward)")
    out["can_push"] = True
    out["status"] = "ready"
    return out


def git_publish(git: Callable[[list[str]], tuple[int, str]], date: str, colour: str, log: Callable[[str], None]) -> dict[str, Any]:
    """Add the three status files, commit them (only them) and push main; a failed push is logged and the commit stays for the next check."""
    paths = list(STATUS_FILES)
    rc, txt = git(["add", "--", *paths])
    if rc != 0:
        log(f"git add failed: {txt[:160]}")
        return {"status": "add-failed", "why": txt[:160]}
    rc, _ = git(["diff", "--cached", "--quiet", "--", *paths])
    if rc == 0:
        log("nothing new in the status files; no commit")
        return {"status": "unchanged", "why": "the status files did not change"}
    rc, txt = git(["commit", "-m", f"status: {date} {colour}", "--", *paths])
    if rc != 0:
        log(f"git commit failed: {txt[:160]}")
        return {"status": "commit-failed", "why": txt[:160]}
    rc, txt = git(["push", "origin", "main"])
    if rc != 0:
        log(f"git push failed (the commit stays for the next check): {txt[:200]}")
        return {"status": "push-failed", "why": txt[:200]}
    rc, sha = git(["rev-parse", "--short", "HEAD"])
    log(f"pushed status: {date} {colour} ({sha.strip()[:12]})")
    return {"status": "pushed", "why": "", "commit": sha.strip()[:12]}


# ---------------------------------------------------------------------------------------------------------------- the daily check
def run_check(env: Env, *, now: datetime | None = None, procs_fn: Callable[[], dict[str, Any]] = list_processes,
              schtasks_fn: Callable[[list[str]], tuple[int, str]] = run_schtasks, git: Callable[[list[str]], tuple[int, str]] | None = None,
              disk_fn: Callable[[str], Any] = shutil.disk_usage, sleep: Callable[[float], None] = time.sleep, dry_run: bool = False,
              no_git: bool = False, no_restart: bool = False, allow_dirty: bool = False, log: Callable[[str], None] | None = None) -> dict[str, Any]:
    now = now or utc_now()
    log = log or Log(env, now, echo=True, write=not dry_run)
    state = load_state(env)
    fig = collect(env, now, procs_fn(), disk_fn, log)
    repairs: list[str] = []
    codes: list[str] = []
    if not dry_run and not no_restart:
        r = ensure_daemon(env, fig, procs_fn=procs_fn, schtasks_fn=schtasks_fn, sleep=sleep, log=log)
        repairs += r
        if r:
            codes.append("daemon-restarted" if fig["daemon"]["restarted"] else "daemon-restart-failed")
    since = since_last(fig, state)
    colour, reasons = decide(fig, since)
    prev = since.get("previous_push") or {}
    if prev.get("status") in ("push-failed", "commit-failed", "add-failed", "skipped") and prev.get("why"):
        repairs.append(f"The previous check could not publish its status ({prev['status']}: {prev['why']}).")
    gitinfo: dict[str, Any] = {"status": "not tried", "why": "no git step in this mode"}
    if git is None and not dry_run and not no_git:
        git = make_git(env.repo)
    if git is not None and not dry_run and not no_git:
        gitinfo = git_preflight(git, allow_dirty, log)
        for note in gitinfo.get("notes", []):
            repairs.append(note[0].upper() + note[1:] + ".")
        if gitinfo["status"] == "skipped":
            repairs.append(f"Not published to GitHub: {gitinfo['why']}.")
            codes.append("push-skipped")
    md = scrub_text(render_markdown(fig, colour, reasons, since, repairs, now))
    doc = dict(fig, colour=colour, reasons=[{"level": lv, "text": t} for lv, t in reasons], since=since, repairs=repairs, git=gitinfo)
    row = history_row(fig, colour, codes)
    if dry_run:
        return {"colour": colour, "markdown": md, "figures": doc, "git": gitinfo, "history": row}
    write_outputs(env, md, doc, row)
    log(f"wrote status/latest.md: {colour}")
    if gitinfo.get("can_push"):
        gitinfo.update(git_publish(git, fig["date"], colour, log))
        if gitinfo["status"] != "pushed":
            codes.append("push-" + gitinfo["status"])
    save_state(env, new_state(fig, colour, gitinfo))
    return {"colour": colour, "markdown": md, "figures": doc, "git": gitinfo, "history": row}


def failure_report(env: Env, now: datetime, exc: BaseException) -> str:
    """The page written when the check itself crashed: RED, with the error's type and message."""
    return "\n".join([f"# Spireline status: RED ({stamp(iso(now))})", "",
                      "**In short.** RED: the daily health check itself failed, so nothing below was read today.", "",
                      f"The error was {type(exc).__name__}: {str(exc)[:300]}. The log under the machine's logs/health folder holds the trace.", ""])


# ----------------------------------------------------------------------------------------------------------- the daemon starter
def start_daemon(env: Env, *, selftest: bool = False, wait: bool = True, procs_fn: Callable[[], dict[str, Any]] = list_processes,
                 popen: Callable[..., Any] = subprocess.Popen, now: datetime | None = None, say: Callable[[str], None] | None = None) -> int:
    """`--start-daemon`: start the practice loop as a plain child unless one runs, or referee/health/STOP or LAB/HALT asks for it to stay down;
    `selftest` starts a harmless sleeper the same way and skips those checks. The wrapper then waits for the child (`wait`, the default) and
    returns its exit code: the 2026-11-25 self-test showed that a Windows scheduled task whose action exits is "Ready" again at once even
    though the child lives on, so only a waiting wrapper keeps the task "Running" while the loop lives and lets Task Scheduler's
    restart-on-failure see a crash. ("End task" ends the wrapper only: the loop it started carries on, so stop the loop with
    `gym_loop.py stop`.)"""
    now = now or utc_now()

    def out(msg: str) -> None:
        line = le.scrub(msg)
        if say:
            say(line)
        elif sys.stdout is not None:
            try:
                print(line)
            except (OSError, UnicodeError, ValueError):
                pass

    if not selftest:
        pr = procs_fn()
        if not pr.get("ok"):
            pr = procs_fn()
        if not pr.get("ok"):
            out(f"cannot tell whether a practice loop runs ({pr.get('why')}): nothing started")
            return 3
        found = find_procs(pr["procs"], DAEMON_NEEDLE)
        if found:
            out("a practice loop is running already (process " + ", ".join(str(p["pid"]) for p in found) + "): nothing started")
            return 0
        if env.stop_file.exists():
            out("referee/health/STOP exists: nothing started")
            return 0
        if (env.lab / "HALT").exists():
            out("LAB/HALT exists: nothing started")
            return 0
        argv = [env.daemon_python, *DAEMON_ARGS]
        cwd, outpath, logname = env.daemon_cwd, env.daemon_out, "daemon-start.log"
    else:
        argv = [env.daemon_python, *SELFTEST_ARGS]
        cwd, outpath, logname = env.health, env.health / "selftest.out", "selftest-start.log"
    env.health.mkdir(parents=True, exist_ok=True)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, "ab") as fh:
        child = popen(argv, cwd=str(cwd), creationflags=BELOW_NORMAL | NEW_GROUP | NO_WINDOW, stdin=subprocess.DEVNULL, stdout=fh,
                      stderr=subprocess.STDOUT, close_fds=True)
    line = f"{iso(now)} started pid={child.pid} {'selftest sleeper' if selftest else 'practice loop'} cwd={Path(cwd).name}"
    with open(env.health / logname, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(le.scrub(line) + "\n")
    out(line)
    if wait:
        rc = child.wait()
        with open(env.health / logname, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(le.scrub(f"{iso(utc_now())} pid={child.pid} ended rc={rc}") + "\n")
        return int(rc or 0)
    return 0


# ------------------------------------------------------------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The daily health check of the unattended machine (D70).")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="the lab root (default D:/spireline)")
    ap.add_argument("--repo", type=Path, default=None, help="the Spireline repo that gets status/ (default: the repo this file is in)")
    ap.add_argument("--start-daemon", action="store_true", help="start the practice loop if none runs, then exit")
    ap.add_argument("--selftest", action="store_true", help="with --start-daemon: start a harmless sleeper instead (the scheduled-task self-test)")
    ap.add_argument("--no-wait", action="store_true",
                    help="with --start-daemon: return at once after starting the child (default: wait for it and pass on its exit code, "
                         "so the scheduled task stays Running while the practice loop lives)")
    ap.add_argument("--dry-run", action="store_true", help="print the report; write, repair and push nothing")
    ap.add_argument("--no-git", action="store_true", help="write the files but do not fetch, commit or push")
    ap.add_argument("--no-restart", action="store_true", help="do not try to restart the practice loop")
    ap.add_argument("--allow-dirty-tree", action="store_true",
                    help="push even when other files are staged or modified: the commit names only the three status files")
    a = ap.parse_args(argv)
    env = Env(a.root, a.repo)
    if a.start_daemon:
        return start_daemon(env, selftest=a.selftest, wait=not a.no_wait)
    now = utc_now()
    try:
        res = run_check(env, now=now, dry_run=a.dry_run, no_git=a.no_git, no_restart=a.no_restart, allow_dirty=a.allow_dirty_tree)
    except Exception as e:  # noqa: BLE001  (the check must leave a RED page rather than die silently)
        log = Log(env, now, echo=True, write=not a.dry_run)
        log("the check failed: " + traceback.format_exc().replace("\n", " | ")[:1500])
        if not a.dry_run:
            try:
                d = env.repo / "status"
                d.mkdir(parents=True, exist_ok=True)
                (d / "latest.md").write_text(scrub_text(failure_report(env, now, e)), encoding="utf-8", newline="\n")
                if not a.no_git:
                    git = make_git(env.repo)
                    pre = git_preflight(git, a.allow_dirty_tree, log)
                    if pre["can_push"]:
                        paths = ["status/latest.md"]
                        git(["add", "--", *paths])
                        git(["commit", "-m", f"status: {now.strftime('%Y-%m-%d')} RED", "--", *paths])
                        git(["push", "origin", "main"])
            except Exception:  # noqa: BLE001
                log("the failure page could not be written or pushed")
        return 1
    if a.dry_run and sys.stdout is not None:
        try:
            print(scrub_text(res["markdown"]))
        except (OSError, UnicodeError, ValueError):
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
