"""tools/landing_evidence.py on a made-up lab root (two tiny git repos, a few logs, a HANDOFF, a paper); nothing real is read.

The root built by `lab` holds

  fork/sts2         main: c1, c2 (c2 adds two files); branch `side`: c3 on top of c2 (not on main)
  spireline         main: s1
  logs              gate-py-old/run.log and gate-py-new/run.log both name c2 (the newer one wins); gate-py-nosummary/publish.log
                    names c3 without any test summary; gym-loop/status
  referee           gym-loop/loop.log (30 lines), LAB/runner.log (50 lines), backlog/HANDOFF.md
  spireline/docs/paper/spireline-paper.html   two changelog entries
"""

from __future__ import annotations

import getpass
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import landing_evidence as le  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
                       capture_output=True, text=True, env=ENV, check=True)
    return p.stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for name, body in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(body, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    root = tmp_path_factory.mktemp("lab")
    fork = root / "fork" / "sts2"
    fork.mkdir(parents=True)
    git(fork, "init", "-b", "main")
    c1 = commit(fork, {"a.txt": "one\n"}, "first commit")
    c2 = commit(fork, {"b.txt": "two\n", "c/d.txt": "three\n"}, "Second commit: adds two files")
    git(fork, "checkout", "-b", "side")
    c3 = commit(fork, {"e.txt": "four\n"}, "Third commit on a side branch")
    git(fork, "checkout", "main")
    sp = root / "spireline"
    sp.mkdir()
    git(sp, "init", "-b", "main")
    s1 = commit(sp, {"README.md": "x\n"}, "docs: first")

    logs = root / "logs"
    for name, mtime in (("gate-py-old", 1_700_000_000), ("gate-py-new", 1_700_100_000)):
        d = logs / name
        d.mkdir(parents=True)
        f = d / "run.log"
        f.write_text(f"tip {c2[:8]} base {c1[:8]} engine files changed: 0 start 22:07:25Z\n"
                     f"python: Ran {4000 if name.endswith('old') else 4044} tests in 9.0s / FAILED (failures=5); new 0, known engine.py:760 1, flakes 0\n"
                     "test_x.py rc=0 OK\nend 22:33:11Z\n", encoding="utf-8")
        os.utime(f, (mtime, mtime))
    (logs / "gate-py-nosummary").mkdir()
    (logs / "gate-py-nosummary" / "publish.log").write_text(f"publish at {c3[:8]} done\n", encoding="utf-8")
    (logs / "gym-loop").mkdir()
    (logs / "gym-loop" / "status").write_text('{\n "pid": 4242,\n "root": "D:\\\\spireline\\\\referee\\\\gym-loop",\n "commit": "%s"\n}' % c2[:8],
                                              encoding="utf-8")
    (root / "referee" / "gym-loop").mkdir(parents=True)
    (root / "referee" / "gym-loop" / "loop.log").write_text("".join(f"2026-11-04T01:{i:02d}:00Z loop line {i}\n" for i in range(30)),
                                                            encoding="utf-8")
    (root / "referee" / "LAB").mkdir(parents=True)
    (root / "referee" / "LAB" / "runner.log").write_text("".join(f"2026-11-04T02:{i:02d}:00Z runner line {i}\n" for i in range(50)),
                                                         encoding="utf-8")
    (root / "referee" / "backlog").mkdir(parents=True)
    (root / "referee" / "backlog" / "HANDOFF.md").write_text(
        "# Handoff\n"
        "- *2026-11-04 01:00Z, worker (D51, alpha).* **Alpha landed** on fork main `abc12345`. Usage at start about 1% all; end: 3% all at 01:05Z.\n"
        "- *2026-11-04 01:30Z, orchestrator.* Checked alpha. Usage 3% all at 01:30Z.\n"
        "- *2026-11-03 22:00Z, worker (D49, beta).* **Beta.** Usage at start 86% all / 61% Fable at 02:30Z; end: (orchestrator).\n"
        "- *2026-11-03 21:00Z, worker (D49, gamma).* **Gamma.** Usage at start 80% all; end: (orchestrator).\n"
        "Plain line mentioning alpha but not a dated one; end: (orchestrator).\n", encoding="utf-8")
    page = root / "spireline" / "docs" / "paper"
    page.mkdir(parents=True)
    (page / "spireline-paper.html").write_text(
        "<html>\n<script>\nconst P = {\n  title: \"x\",\n  changelog: [\n"
        "    {when:\"2026-11-04 01:00Z\", what:\"Landing. The newest entry (fork abc12345).\"},\n"
        "    {when:\"2026-11-03 22:35Z\", what:\"An older entry.\"},\n  ],\n};\n</script>\n</html>\n", encoding="utf-8")
    return {"root": root, "fork": fork, "c1": c1, "c2": c2, "c3": c3, "s1": s1}


def run(lab, capsys, *args: str) -> str:
    assert le.main([*args, "--root", str(lab["root"])]) == 0
    return capsys.readouterr().out


# ---------------------------------------------------------------------------------------------------- commits
def test_a_commit_on_main(lab, capsys):
    out = run(lab, capsys, "--fork-commit", lab["c2"][:8])
    assert f"fork commit {lab['c2'][:8]}" in out
    assert "on main: YES" in out and "local branches holding it: main, side" in out
    assert "subject: Second commit: adds two files" in out
    assert "files changed: 2: b.txt, c/d.txt" in out
    assert "committed: 20" in out and out.count("Z") >= 1  # a UTC stamp


def test_a_commit_off_main(lab, capsys):
    out = run(lab, capsys, "--fork-commit", lab["c3"])
    assert "on main: NO" in out and "local branches holding it: side" in out


def test_unknown_and_malformed_hashes(lab, capsys):
    out = run(lab, capsys, "--fork-commit", "deadbeef", "zzz-not-hex")
    assert "NOT FOUND in the repository" in out and "NOT A HASH" in out


def test_spireline_commit(lab, capsys):
    out = run(lab, capsys, "--spireline-commit", lab["s1"][:7])
    assert "Spireline commit" in out and "on main: YES" in out and "subject: docs: first" in out
    assert "gate: no log under logs/ names" in out


def test_gate_summary_comes_from_the_newest_log(lab, capsys):
    out = run(lab, capsys, "--fork-commit", lab["c2"][:8])
    assert "gate: newest summary in logs/gate-py-new/run.log" in out and "2 log(s) name" in out
    assert "Ran 4044 tests" in out and "Ran 4000 tests" not in out
    assert "older gate logs naming it: logs/gate-py-old/run.log" in out


def test_a_log_without_a_summary_is_said_so(lab, capsys):
    out = run(lab, capsys, "--fork-commit", lab["c3"])
    assert "none carries a test summary line" in out and "logs/gate-py-nosummary/publish.log" in out


# ---------------------------------------------------------------------------------------------------- loop, runner, HANDOFF, paper
def test_loop(lab, capsys):
    out = run(lab, capsys, "--loop")
    assert '"pid": 4242' in out and "loop line 29" in out and "loop line 15" in out and "loop line 14" not in out
    assert out.count("loop line") == 15


def test_runner_tail(lab, capsys):
    out = run(lab, capsys, "--runner", "4")
    assert "last 4 lines of referee/LAB/runner.log" in out
    assert "runner line 49" in out and "runner line 46" in out and "runner line 45" not in out


def test_handoff_lines_and_placeholders(lab, capsys):
    out = run(lab, capsys, "--handoff", "alpha")
    assert "HANDOFF lines holding 'alpha': 3" in out  # the dated pair and the plain line
    assert "line 2:" in out and "Usage at start about 1% all" in out
    assert "unfilled 'end: (orchestrator)' placeholders: 2" in out and "(lines 4, 5)" in out  # the plain line is not counted


def test_handoff_no_match(lab, capsys):
    out = run(lab, capsys, "--handoff", "no such text")
    assert "HANDOFF lines holding 'no such text': 0" in out


def test_paper_newest_entry(lab, capsys):
    out = run(lab, capsys, "--paper")
    assert "when 2026-11-04 01:00Z" in out and "The newest entry (fork abc12345)." in out
    assert "An older entry" not in out and "the entry after it is dated 2026-11-03 22:35Z" in out


# ---------------------------------------------------------------------------------------------------- shape of the output
def test_output_is_capped_and_has_no_paths_or_names(lab, capsys):
    me = getpass.getuser()
    (lab["root"] / "referee" / "LAB" / "runner.log").write_text(
        "".join(f"line {i} in C:/Users/{me}/work and D:/spireline/referee/x by {me}\n" for i in range(400)), encoding="utf-8")
    out = run(lab, capsys, "--runner", "400", "--loop", "--fork-commit", lab["c2"])
    lines = out.splitlines()
    assert len(lines) <= le.MAX_LINES and "output cut at 200 lines" in lines[-1]
    assert "line 399 in <home>/work and referee/x by <user>" not in out  # cut away (only the first 200 lines remain)
    assert "in <home>/work and referee/x by <user>" in out
    for needle in ("Users", "D:/spireline", "D:\\spireline", me, str(lab["root"])):
        assert needle not in out


def test_scrub():
    assert le.scrub("see D:/spireline/referee/x and D:\\spireline\\logs\\y") == "see referee/x and logs\\y"
    assert le.scrub('"root": "D:\\\\spireline\\\\referee\\\\gym-loop"') == '"root": "referee\\\\gym-loop"'
    assert le.scrub("C:/Users/someone/work/f.py") == "<home>/work/f.py"
    assert le.scrub("microchimp/spireline-sim") == "microchimp/spireline-sim"  # a repository name is not a path
    assert le.scrub("/d/spireline/logs/z") == "logs/z"


def test_nothing_asked(lab, capsys):
    assert "nothing asked for" in run(lab, capsys)


def test_missing_pieces_are_said_not_raised(tmp_path, capsys):
    assert le.main(["--root", str(tmp_path), "--loop", "--runner", "3", "--handoff", "x", "--paper",
                    "--fork-commit", "abcdef1"]) == 0
    out = capsys.readouterr().out
    assert "no status file" in out and "runner log: not found" in out and "HANDOFF: not found" in out
    assert "paper: not found" in out and "repository not found" in out
