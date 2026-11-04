"""Read-only evidence lines for checking a worker's landing report (D52 item 1).

    python tools/landing_evidence.py [--fork-commit HASH ...] [--spireline-commit HASH ...] [--loop] [--runner N]
        [--handoff TEXT] [--paper] [--root DIR]

It gathers what an orchestrator looks at to verify a report and prints it as plain text, so a small model can judge each
claim without reading whole logs. It runs no gate, test or game, writes nothing and touches no network. Sections, each only
when asked for:

  --fork-commit HASH...        for each: on `main` of <root>/fork/sts2?, the local and remote branches that hold it, the
                               subject line, the number of files changed, and the newest gate summary in <root>/logs that
                               names the commit (its `run.log` / `gate.out` / `results.json` style lines: tip, python
                               counts, C# and EmuDump counts, corpus, byte proof), and the worker's saved test summary
                               <root>/logs/fork-tests/<short hash>.txt when there is one
  --spireline-commit HASH...   the same for <root>/spireline (the logs rarely name these; "none" then), with the saved
                               summary <root>/logs/spireline-tests/<short hash>.txt (the last lines of the pytest output)
  --loop                       the gym loop's status file and the last 15 lines of its log
  --runner N                   the last N lines of the lab runner's log
  --handoff TEXT               the HANDOFF.md lines holding TEXT (line number, the line cut to a readable length and its
                               usage tail) and the count of unfilled `end: (orchestrator)` placeholders
  --paper                      the newest changelog entry of docs/paper/spireline-paper.html (the first entry after the
                               `  changelog: [` marker; the rest of the page is not read)

Output stays under about 200 lines. Paths print relative to <root> (default D:/spireline); the host name, the user name and
absolute paths are scrubbed from every line.
"""

from __future__ import annotations

import argparse
import getpass
import re
import socket
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path("D:/spireline")
MAX_LINES = 200
LINE_CUT = 300
HANDOFF_CUT = 1400
HANDOFF_TAIL = 260
MAX_HANDOFF_MATCHES = 8
TEST_FILE_LINES = 8
TEST_FILE_MAX = 3
LOOP_LOG_TAIL = 15
LOG_SIZE_CAP = 2_000_000
HASH_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
SUMMARY_RE = re.compile(
    r"(python:|Ran \d+ tests|Passed!|Failed:\s+\d|tests_csharp|tests_emudump|tests_python|new failures|"
    r"corpus|byte_proof|byte proof|sites check|flakes|C# \d)", re.I)
UNFILLED_RE = re.compile(r"end:\s*\(orchestrator\)")
DRIVE_ROOT_RE = re.compile(r"(?:[A-Za-z]:|/[a-z](?=/))[\\/]+spireline(?:[\\/]+|(?![\w-]))")
HOME_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+")


# ---------------------------------------------------------------------------------------------------- small helpers
def scrub(text: str) -> str:
    """Drops the lab root from absolute paths and hides the home folder, user name and host name."""
    text = DRIVE_ROOT_RE.sub("", text)
    text = HOME_RE.sub("<home>", text)
    for secret, tag in ((_safe(getpass.getuser), "<user>"), (_safe(socket.gethostname), "<host>")):
        if secret and len(secret) >= 3:
            text = re.sub(re.escape(secret), tag, text, flags=re.I)
    return text


def _safe(fn) -> str:
    try:
        return fn() or ""
    except Exception:  # noqa: BLE001 - any failure to learn the name just means there is nothing to hide
        return ""


def cut(text: str, n: int = LINE_CUT) -> str:
    text = text.rstrip("\r\n")
    return text if len(text) <= n else text[: n - 1] + f"~ [+{len(text) - n + 1} chars]"


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def utc_stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%MZ")


def tail_lines(path: Path, n: int) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [ln.rstrip("\r\n") for ln in deque(fh, maxlen=n)]


def git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=60,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, f"git unavailable: {type(exc).__name__}"
    return p.returncode, (p.stdout if p.returncode == 0 else p.stderr).strip()


# ---------------------------------------------------------------------------------------------------- commits
def gate_evidence(logs: Path, root: Path, full_hash: str) -> list[str]:
    """The newest gate-style log under `logs` that names the commit and carries a test summary, with its summary lines."""
    key = full_hash[:8]
    if not logs.is_dir():
        return ["gate: no logs folder"]
    candidates: list[Path] = []
    for pat in ("*/run.log", "*/gate.out", "*/results.json", "*/publish.log", "*.out", "*.log", "*/*.status", "*.status"):
        candidates += [p for p in logs.glob(pat) if p.is_file()]
    seen, hits = set(), []
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        try:
            st = p.stat()
            if st.st_size > LOG_SIZE_CAP:
                continue
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not any(key in ln for ln in lines):
            continue
        summary = [ln for ln in lines if SUMMARY_RE.search(ln)]
        hits.append((st.st_mtime, p, lines, summary))
    if not hits:
        return [f"gate: no log under logs/ names {key}"]
    with_summary = sorted((h for h in hits if h[3]), key=lambda h: h[0], reverse=True)
    out: list[str] = []
    if not with_summary:
        out.append(f"gate: {len(hits)} log(s) name {key} but none carries a test summary line (newest: "
                   f"{rel(max(hits, key=lambda h: h[0])[1], root)})")
        return out
    mtime, path, lines, summary = with_summary[0]
    named = [ln for ln in lines if key in ln][:2]
    out.append(f"gate: newest summary in {rel(path, root)} (modified {utc_stamp(mtime)}); {len(hits)} log(s) name {key}")
    for ln in named + [s for s in summary if s not in named][:6]:
        out.append("  | " + cut(ln, 260))
    if len(with_summary) > 1:
        out.append("  older gate logs naming it: " + ", ".join(rel(h[1], root) for h in with_summary[1:4]))
    return out


def test_file_evidence(logs: Path, folder: str, full_hash: str, root: Path) -> list[str]:
    """The summary lines a worker saved after its suite or gate passed: logs/<folder>/<short hash>.txt.

    The file name is any hex prefix (7 or more digits) of the landed commit, so a 7, 8 or 12 digit short hash all match.
    """
    d = logs / folder
    shown = f"logs/{folder}/{full_hash[:8]}.txt"
    if not d.is_dir():
        return [f"tests: no saved summary ({folder} folder not found; the worker saves one at {shown})"]
    files = sorted((p for p in d.glob("*.txt") if p.is_file() and len(p.stem) >= 7 and HASH_RE.match(p.stem)
                    and full_hash.lower().startswith(p.stem.lower())), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return [f"tests: no saved summary (no file {shown}; the worker saves the last 5 summary lines there)"]
    out: list[str] = []
    for p in files[:TEST_FILE_MAX]:
        try:
            lines = [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        except OSError:
            out.append(f"tests: {rel(p, root)} unreadable")
            continue
        out.append(f"tests: saved summary {rel(p, root)} (modified {utc_stamp(p.stat().st_mtime)}):")
        out += ["  | " + cut(ln, 260) for ln in lines[:TEST_FILE_LINES]]
        if len(lines) > TEST_FILE_LINES:
            out.append(f"  | ... {len(lines) - TEST_FILE_LINES} more lines in the file")
    if len(files) > TEST_FILE_MAX:
        out.append(f"  ({len(files) - TEST_FILE_MAX} more files match this commit)")
    return out


def commit_evidence(repo: Path, label: str, commit: str, root: Path, logs: Path | None,
                    tests_folder: str | None = None) -> list[str]:
    out = [f"{label} commit {commit}"]
    if not HASH_RE.match(commit):
        return out + ["  NOT A HASH (7 to 40 hex digits expected)"]
    if not (repo / ".git").exists():
        return out + [f"  repository not found at {rel(repo, root)}"]
    rc, full = git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}")
    if rc != 0 or not full:
        return out + ["  NOT FOUND in the repository"]
    rc, on_main = git(repo, "merge-base", "--is-ancestor", full, "main")
    out.append(f"  resolved: {full[:12]}; on main: {'YES' if rc == 0 else 'NO'}")
    rc, tip = git(repo, "rev-parse", "--short=12", "main")
    out[-1] += f" (main tip {tip if rc == 0 else '?'})"
    rc, branches = git(repo, "branch", "--format=%(refname:short)", "--contains", full)
    names = [b for b in branches.splitlines() if b] if rc == 0 else []
    out.append("  local branches holding it: " + (", ".join(names[:8]) + (f" (+{len(names) - 8} more)" if len(names) > 8 else "")
                                                  if names else "none"))
    rc, remotes = git(repo, "branch", "-r", "--format=%(refname:short)", "--contains", full)
    rnames = [b for b in remotes.splitlines() if b and "/" in b and "->" not in b] if rc == 0 else []
    out.append("  remote branches holding it (as last fetched): "
               + (", ".join(rnames[:6]) + (f" (+{len(rnames) - 6} more)" if len(rnames) > 6 else "") if rnames else "none"))
    rc, subj = git(repo, "log", "-1", "--format=%ct%n%s", full)
    if rc == 0:
        when, _, subject = subj.partition("\n")
        out.append(f"  committed: {utc_stamp(int(when)) if when.isdigit() else when}")
        out.append("  subject: " + cut(subject, 220))
    rc, names_out = git(repo, "show", "--name-only", "--format=", full)
    if rc == 0:
        files = [f for f in names_out.splitlines() if f.strip()]
        out.append(f"  files changed: {len(files)}" + (": " + ", ".join(files[:6]) + (" ..." if len(files) > 6 else "")
                                                       if files else ""))
    if logs is not None:
        out += ["  " + ln if i == 0 else ln for i, ln in enumerate(gate_evidence(logs, root, full))]
        if tests_folder:
            out += ["  " + ln if i == 0 else ln for i, ln in enumerate(test_file_evidence(logs, tests_folder, full, root))]
    return out


# ---------------------------------------------------------------------------------------------------- loop, runner, HANDOFF, paper
def loop_evidence(root: Path) -> list[str]:
    out = ["gym loop"]
    status = root / "logs" / "gym-loop" / "status"
    if status.is_file():
        out.append(f"  status ({rel(status, root)}, modified {utc_stamp(status.stat().st_mtime)}):")
        out += ["    " + cut(ln, 200) for ln in status.read_text(encoding="utf-8", errors="replace").splitlines()[:30]]
    else:
        out.append(f"  no status file at {rel(status, root)}")
    log = root / "referee" / "gym-loop" / "loop.log"
    if log.is_file():
        out.append(f"  last {LOOP_LOG_TAIL} lines of {rel(log, root)}:")
        out += ["    " + cut(ln) for ln in tail_lines(log, LOOP_LOG_TAIL)]
    else:
        out.append(f"  no log at {rel(log, root)}")
    return out


def runner_evidence(root: Path, n: int) -> list[str]:
    log = root / "referee" / "LAB" / "runner.log"
    if not log.is_file():
        return [f"runner log: not found at {rel(log, root)}"]
    return [f"last {n} lines of {rel(log, root)} (modified {utc_stamp(log.stat().st_mtime)}):"] + \
           ["  " + cut(ln) for ln in tail_lines(log, max(1, n))]


def handoff_evidence(root: Path, text: str) -> list[str]:
    path = root / "referee" / "backlog" / "HANDOFF.md"
    if not path.is_file():
        return [f"HANDOFF: not found at {rel(path, root)}"]
    needle = text.lower()
    hits, unfilled = [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            ln = ln.rstrip("\r\n")
            if needle and needle in ln.lower():
                hits.append((i, ln))
            if UNFILLED_RE.search(ln) and ln.startswith("- *"):
                unfilled.append((i, ln))
    out = [f"HANDOFF lines holding {text!r}: {len(hits)}"]
    for i, ln in hits[:MAX_HANDOFF_MATCHES]:
        body = ln if len(ln) <= HANDOFF_CUT else ln[:HANDOFF_CUT] + f" ~ [+{len(ln) - HANDOFF_CUT} chars] ... " + ln[-HANDOFF_TAIL:]
        out.append(f"  line {i}: {body}")
    if len(hits) > MAX_HANDOFF_MATCHES:
        out.append(f"  (+{len(hits) - MAX_HANDOFF_MATCHES} more matching lines, first at line {hits[MAX_HANDOFF_MATCHES][0]})")
    out.append(f"unfilled 'end: (orchestrator)' placeholders: {len(unfilled)}"
               + (" (lines " + ", ".join(str(i) for i, _ in unfilled[:12]) + (" ..." if len(unfilled) > 12 else "") + ")"
                  if unfilled else ""))
    for i, ln in unfilled[:12]:
        out.append(f"  line {i}: {cut(ln[:ln.find('*', 3) + 1] if '*' in ln[3:] else ln, 150)}")
    return out


def paper_evidence(root: Path) -> list[str]:
    path = root / "spireline" / "docs" / "paper" / "spireline-paper.html"
    if not path.is_file():
        return [f"paper: not found at {rel(path, root)}"]
    entries: list[str] = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if not entries and ln.rstrip().endswith("changelog: ["):
                entries.append("")  # marker seen
                continue
            if entries:
                s = ln.strip()
                if s.startswith("{when:"):
                    entries.append(s)
                    if len(entries) == 3:
                        break
                elif s.startswith("]"):
                    break
    found = entries[1:]
    if not found:
        return [f"paper: no changelog entry found after the marker in {rel(path, root)}"]
    m = re.match(r'\{when:"([^"]*)"\s*,\s*what:"(.*)', found[0])
    when, what = (m.group(1), m.group(2)) if m else ("?", found[0])
    out = [f"paper: newest changelog entry of {rel(path, root)} (when {when}):"]
    out.append("  " + cut(what.rstrip(' ,}"') if what else found[0], 1800))
    if len(found) > 1:
        m2 = re.match(r'\{when:"([^"]*)"', found[1])
        out.append(f"  (the entry after it is dated {m2.group(1) if m2 else '?'})")
    return out


# ---------------------------------------------------------------------------------------------------- CLI
def build(args: argparse.Namespace) -> list[str]:
    root = args.root.resolve() if args.root else DEFAULT_ROOT
    logs = root / "logs"
    out: list[str] = [f"landing evidence, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}"]
    for c in args.fork_commit or []:
        out += commit_evidence(root / "fork" / "sts2", "fork", c, root, logs, "fork-tests")
    for c in args.spireline_commit or []:
        out += commit_evidence(root / "spireline", "Spireline", c, root, logs, "spireline-tests")
    if args.loop:
        out += loop_evidence(root)
    if args.runner:
        out += runner_evidence(root, args.runner)
    if args.handoff is not None:
        out += handoff_evidence(root, args.handoff)
    if args.paper:
        out += paper_evidence(root)
    if len(out) == 1:
        out.append("nothing asked for; see --help")
    lines = [scrub(ln) for ln in out]
    if len(lines) > MAX_LINES:
        lines = lines[: MAX_LINES - 1] + [f"... output cut at {MAX_LINES} lines ({len(lines) - MAX_LINES + 1} more)"]
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only evidence lines for checking a worker's landing report.")
    ap.add_argument("--fork-commit", nargs="+", metavar="HASH", help="commit(s) to look up in the fork (<root>/fork/sts2)")
    ap.add_argument("--spireline-commit", nargs="+", metavar="HASH", help="commit(s) to look up in <root>/spireline")
    ap.add_argument("--loop", action="store_true", help="the gym loop's status and the last 15 lines of its log")
    ap.add_argument("--runner", type=int, metavar="N", help="the last N lines of the lab runner's log")
    ap.add_argument("--handoff", metavar="TEXT", help="HANDOFF.md lines holding TEXT, and the unfilled placeholder count")
    ap.add_argument("--paper", action="store_true", help="the newest changelog entry of the paper")
    ap.add_argument("--root", type=Path, help="the lab root (default D:/spireline); for tests")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print("\n".join(build(args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
