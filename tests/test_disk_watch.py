"""tools/disk_watch.py on small made-up folders; nothing real is read except the free space of the drive holding tmp_path."""

from __future__ import annotations

import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import disk_watch as dw  # noqa: E402

Usage = namedtuple("Usage", "total used free")


def put(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def make_link(link: Path, target: Path) -> bool:
    """A folder link (junction on Windows, symlink elsewhere); False when the machine will not make one."""
    try:
        if sys.platform == "win32":
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
            return r.returncode == 0
        link.symlink_to(target, target_is_directory=True)
        return True
    except OSError:
        return False


def test_walk_counts_files_folders_and_bytes(tmp_path):
    put(tmp_path / "a.bin", 10)
    put(tmp_path / "sub" / "b.bin", 20)
    put(tmp_path / "sub" / "deeper" / "c.bin", 30)
    (tmp_path / "empty").mkdir()
    s = dw.walk(tmp_path)
    assert (s["files"], s["dirs"], s["bytes"], s["links"], s["errors"]) == (3, 3, 60, 0, 0)
    assert "3 files in 3 folders" in dw.tree_line("t", s) and "60 bytes" in dw.tree_line("t", s)


def test_walk_of_a_missing_folder(tmp_path):
    s = dw.walk(tmp_path / "nope")
    assert not s["exists"] and dw.tree_line("gone", s) == "  gone: not found"


def test_walk_counts_a_folder_link_once_and_does_not_follow_it(tmp_path):
    real, top = tmp_path / "real", tmp_path / "top"
    put(real / "big.bin", 1000)
    put(top / "a.bin", 5)
    if not make_link(top / "link", real):
        pytest.skip("this machine will not make a folder link")
    s = dw.walk(top)
    assert s["files"] == 1 and s["bytes"] == 5 and s["links"] == 1
    assert "1 folder link(s) not followed" in dw.tree_line("t", s)


def test_walk_keeps_a_listing_by_relative_path(tmp_path):
    put(tmp_path / "x" / "y.bin", 7)
    assert dw.walk(tmp_path, keep_files=True)["listing"] == {"x/y.bin": 7}
    assert dw.walk(tmp_path)["listing"] == {}


def test_drive_warning_under_the_threshold(monkeypatch):
    monkeypatch.setattr(dw.shutil, "disk_usage", lambda d: Usage(100 * dw.GIB, 90 * dw.GIB, 10 * dw.GIB))
    lines, warnings = dw.drive_lines(["C:/", "D:/"], 15)
    assert "  C: 10.0 GiB free of 100.0 GiB (10.0% free; 90.0 GiB used)" in lines
    assert [w.split(" has ")[0] for w in warnings] == ["WARNING: C:", "WARNING: D:"]
    assert dw.drive_lines(["C:/"], 10)[1] == []  # 10.0% free is not under 10%


def test_no_warning_when_there_is_room(monkeypatch):
    monkeypatch.setattr(dw.shutil, "disk_usage", lambda d: Usage(100 * dw.GIB, 20 * dw.GIB, 80 * dw.GIB))
    assert dw.drive_lines(["D:/"], 15)[1] == []


def test_an_unreadable_drive_is_said_not_raised(monkeypatch):
    def boom(d):
        raise OSError("no such drive")
    monkeypatch.setattr(dw.shutil, "disk_usage", boom)
    lines, warnings = dw.drive_lines(["Q:/"], 15)
    assert lines[1] == "  Q: not readable" and warnings == []


@pytest.fixture
def lab(tmp_path):
    """root/referee/<name>.old-2026-11-03 against ssd/<name>; the old runs lacks nothing but the target has two extra files,
    the old corpus has one file the target lacks and one with another size."""
    root, ssd = tmp_path / "root", tmp_path / "ssd"
    for name in ("runs", "corpus", "refset"):
        folder = {"runs": "referee", "corpus": "referee", "refset": "referee"}[name]
        put(root / folder / f"{name}.old-2026-11-03" / "a.bin", 10)
        put(root / folder / f"{name}.old-2026-11-03" / "d" / "b.bin", 20)
        put(ssd / name / "a.bin", 10)
        put(ssd / name / "d" / "b.bin", 20)
    put(ssd / "runs" / "new1.bin", 5)
    put(ssd / "runs" / "d" / "new2.bin", 5)
    put(root / "referee" / "corpus.old-2026-11-03" / "gone.bin", 40)
    put(root / "referee" / "corpus.old-2026-11-03" / "d" / "b.bin", 21)
    return root, ssd


def test_old_copy_lines_report_counts_and_the_difference(lab):
    root, ssd = lab
    out = "\n".join(dw.old_copy_lines(root, ssd, diff=False))
    assert "referee/runs.old-2026-11-03  against  ssd/runs  (junction referee/LAB/runs)" in out
    assert "old copy: 2 files in 1 folders, 0.0 GiB (30 bytes)" in out
    assert "SSD target: 4 files in 1 folders, 0.0 GiB (40 bytes)" in out
    assert "old minus target: -2 files" in out and "(-10 bytes)" in out
    assert "by path" not in out  # only with --diff


def test_old_copy_diff_by_path_and_size(lab):
    root, ssd = lab
    out = "\n".join(dw.old_copy_lines(root, ssd, diff=True))
    corpus = out.split("referee/corpus.old-2026-11-03")[1].split("referee/refset.old-2026-11-03")[0]
    assert "by path: 1 old files missing from the target" in corpus and "1 present with another size" in corpus
    assert "missing example: gone.bin" in corpus and "other size: d/b.bin (old 21 bytes, target 20 bytes)" in corpus
    runs = out.split("referee/runs.old-2026-11-03")[1].split("referee/corpus.old-2026-11-03")[0]
    assert "by path: 0 old files missing" in runs and "2 target files not in the old copy" in runs


def test_old_copy_missing_folders_are_said(tmp_path):
    out = "\n".join(dw.old_copy_lines(tmp_path / "root", tmp_path / "ssd", diff=True))
    assert out.count("old copy: not found") == 3 and out.count("SSD target: not found") == 3
    assert "old minus target" not in out


def test_main_prints_and_check_sets_the_exit_status(lab, monkeypatch, capsys):
    root, ssd = lab
    base = ["--root", str(root), "--ssd", str(ssd), "--drives", str(root)]
    assert dw.main([*base, "--warn-pct", "0", "--check"]) == 0
    out = capsys.readouterr().out
    assert "free space" in out and "SSD folder" in out and "WARNING" not in out
    assert "old copies against the SSD folders" in out
    assert dw.main([*base, "--warn-pct", "101", "--check", "--no-old"]) == 1
    out = capsys.readouterr().out
    assert "WARNING" in out and "old copies" not in out
    assert dw.main([*base, "--warn-pct", "101", "--no-old"]) == 0  # a warning alone is not a failure without --check


def test_the_ssd_listing_names_each_subfolder(lab, capsys):
    root, ssd = lab
    dw.main(["--root", str(root), "--ssd", str(ssd), "--drives", str(root), "--no-old"])
    out = capsys.readouterr().out
    assert "  total: 8 files in 6 folders" in out and "  runs: 4 files in 1 folders" in out
    assert "  corpus: 2 files in 1 folders" in out and "  refset: 2 files in 1 folders" in out
