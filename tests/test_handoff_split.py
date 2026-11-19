"""tools/handoff_split.py on a small made-up HANDOFF: stamps, blocks, the alerts block, CRLF, the archive, the backup, a changed file.

The fixture (`TEXT`, written with CRLF) has a title, an alerts block holding an old stamped line, a review section with an introduction and
nine stamped lines (some with indented continuation lines, one with an undated sub-bullet, one without an asterisk, two with a date only),
and a plan section without stamps. With now = 2026-11-19 02:00Z and 7 days, the cutoff is 2026-11-12 02:00Z.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import handoff_split as hs  # noqa: E402

NOW = datetime(2026, 11, 19, 2, 0, tzinfo=timezone.utc)

TEXT = "\n".join([
    "# Title",
    "",
    "Intro line of the page.",
    "",
    "## Open alerts and unactioned failures (kept current)",
    "",
    "- *2026-10-01 01:00Z, orchestrator.* An old alert line that must stay.",
    "- **Fight practice stalled** an unstamped alert.",
    "",
    "## 0. Week review",
    "",
    "Review introduction paragraph.",
    "| a | b |",
    "",
    "- *2026-11-01 10:00Z, orchestrator.* Old line one.",
    "  an indented continuation of line one",
    "",
    "- *05:22Z undated sub-bullet of line one*",
    "- 2026-11-05T07:42Z lane W5 plain stamp, no asterisk, old.",
    "  | x | y |",
    "  | 1 | 2 |",
    "",
    "- *2026-11-10, late.* A date-only stamp before the cutoff day.",
    "- *2026-11-12, today.* A date-only stamp on the cutoff day: its day is not over, so it stays.",
    "- *2026-11-12 03:00Z, worker.* Just newer than the cutoff.",
    "- *2026-11-18T16:12Z, worker.* Recent.",
    "  continuation of the recent one",
    "- *2026-11-19 01:43Z, orchestrator.* The newest line.",
    "",
    "## 1. Goal",
    "",
    "Plan prose that has no stamps and stays.",
    "",
])


def write(path: Path, text: str, style: str = "\r\n") -> bytes:
    data = text.replace("\n", style).encode("utf-8")
    path.write_bytes(data)
    return data


@pytest.fixture
def files(tmp_path: Path) -> tuple[Path, Path]:
    h = tmp_path / "HANDOFF.md"
    write(h, TEXT)
    return h, tmp_path / "HANDOFF-archive.md"


def run(files_: tuple[Path, Path], *extra: str, apply: bool = False) -> int:
    h, a = files_
    return hs.main(["--handoff", str(h), "--archive", str(a), "--now", "2026-11-19T02:00:00Z", *extra, "--apply" if apply else "--dry-run"])


# ----------------------------------------------------------------------------------------------------- stamps
def test_parse_stamp_forms():
    p = hs.parse_stamp
    assert p("- *2026-11-18 12:47Z, orchestrator.* x") == datetime(2026, 11, 18, 12, 47, tzinfo=timezone.utc)
    assert p("- *2026-10-28T15:55Z, GPU lane,* x") == datetime(2026, 10, 28, 15, 55, tzinfo=timezone.utc)
    assert p("- *2026-10-23, late.* x") == datetime(2026, 10, 23, 23, 59, 59, tzinfo=timezone.utc)  # date only: the last second of the day
    assert p("- 2026-10-28T07:05Z lane W5 x") == datetime(2026, 10, 28, 7, 5, tzinfo=timezone.utc)
    assert p("- 2026-10-28 prose bullet with a date but no time and no asterisk") is None
    assert p("- *05:22Z undated*") is None and p("Some prose 2026-11-01 10:00Z") is None and p("- **bold** line") is None
    assert p("- *2026-13-45 10:00Z* an impossible date") is None


# ----------------------------------------------------------------------------------------------------- dry run and apply
def test_dry_run_prints_counts_and_writes_nothing(files, capsys):
    h, a = files
    before = h.read_bytes()
    assert run(files) == 0
    out = capsys.readouterr().out
    assert "dry run (nothing written)" in out and "cutoff: 2026-11-12 02:00Z" in out
    assert "stamped blocks: 7; moving 3; keeping 4" in out  # moving 11-01, 11-05 and 11-10; keeping 11-12 (two), 11-18 and 11-19; the alerts line is not a block
    assert h.read_bytes() == before and not a.exists() and not list(h.parent.glob("*.bak"))
    assert str(h.parent) not in out  # no absolute path in the output


def test_apply_moves_old_blocks_in_order_and_keeps_the_rest(files, capsys):
    h, a = files
    original = h.read_bytes()
    assert run(files, apply=True) == 0
    live = h.read_bytes().decode("utf-8")
    arch = a.read_bytes().decode("utf-8")
    bak = list(h.parent.glob("HANDOFF.md.*.bak"))
    assert len(bak) == 1 and bak[0].read_bytes() == original
    # kept: title, alerts (including its old stamped line), the review's introduction, the three recent blocks, the plan section, headers
    for kept in ("# Title", "## Open alerts", "An old alert line that must stay.", "an unstamped alert", "## 0. Week review", "Review introduction paragraph.",
                 "| a | b |", "A date-only stamp on the cutoff day", "Just newer than the cutoff.", "continuation of the recent one", "The newest line.",
                 "## 1. Goal", "Plan prose that has no stamps"):
        assert kept in live, kept
    # moved: the stamped lines before the cutoff with their continuation lines, the undated sub-bullet and the plain-stamp lines
    for gone in ("Old line one.", "an indented continuation of line one", "undated sub-bullet of line one", "plain stamp, no asterisk", "| 1 | 2 |",
                 "A date-only stamp before the cutoff day"):
        assert gone not in live and gone in arch, gone
    # the archive keeps the file's order and names the section the blocks came from
    pos = [arch.index(x) for x in ("Old line one.", "undated sub-bullet", "plain stamp", "| 1 | 2 |", "before the cutoff day")]
    assert pos == sorted(pos)
    assert "### 0. Week review" in arch and "## Archived 2026-11-19 02:00Z from HANDOFF.md" in arch and "(3 blocks)" in arch
    # the header keeps its gap: a blank line before `## 1. Goal`
    assert "\r\n\r\n## 1. Goal" in live
    # CRLF everywhere, zero bare LF, in both files
    for text in (live, arch):
        assert text.count("\n") == text.count("\r\n") and text.endswith("\r\n")
    out = capsys.readouterr().out
    assert "APPLIED" in out and "bare LF in the input: 0, in the output: 0" in out and "backup: HANDOFF.md." in out


def test_a_second_run_moves_nothing_and_an_archive_grows_at_the_end(files):
    h, a = files
    run(files, apply=True)
    live1, arch1 = h.read_bytes(), a.read_bytes()
    assert run(files, apply=True) == 0
    assert h.read_bytes() == live1 and a.read_bytes() == arch1 and len(list(h.parent.glob("*.bak"))) == 1  # nothing to move: nothing written
    # a month later the recent blocks are old: they are appended after the first batch, under a second heading
    assert hs.main(["--handoff", str(h), "--archive", str(a), "--now", "2026-12-19T02:00:00Z", "--keep-days", "7", "--apply"]) == 0
    arch2 = a.read_bytes()
    assert arch2.startswith(arch1) and arch2.count(b"## Archived ") == 2 and b"The newest line." in arch2[len(arch1):]


def test_newline_styles_and_mixed_input(tmp_path: Path):
    h, a = tmp_path / "HANDOFF.md", tmp_path / "arch.md"
    data = write(h, TEXT)
    mixed = data.replace(b"Old line one.\r\n", b"Old line one.\n")  # one bare LF inside a CRLF file
    h.write_bytes(mixed)
    plan = hs.make_plan(h, a, 7, NOW)
    assert plan.style == "\r\n" and plan.bare_lf == 1
    hs.apply_plan(plan)
    live = h.read_bytes()
    assert live.count(b"\n") == live.count(b"\r\n")  # every break is CRLF again
    # an LF file stays LF, and a new archive takes its style
    h2, a2 = tmp_path / "H2.md", tmp_path / "a2.md"
    write(h2, TEXT, "\n")
    hs.apply_plan(hs.make_plan(h2, a2, 7, NOW))
    assert b"\r" not in h2.read_bytes() and b"\r" not in a2.read_bytes()
    # an existing LF archive keeps LF even when the live file is CRLF
    h3, a3 = tmp_path / "H3.md", tmp_path / "a3.md"
    write(h3, TEXT)
    a3.write_bytes(b"# older archive\n")
    hs.apply_plan(hs.make_plan(h3, a3, 7, NOW))
    assert b"\r" not in a3.read_bytes() and a3.read_bytes().startswith(b"# older archive\n")


def test_the_file_changing_after_it_was_read_stops_everything(files):
    h, a = files
    plan = hs.make_plan(h, a, 7, NOW)
    with open(h, "ab") as fh:
        fh.write(b"- *2026-11-19 01:59Z, worker.* appended meanwhile\r\n")
    with pytest.raises(hs.Changed):
        hs.apply_plan(plan)
    assert not a.exists() and not list(h.parent.glob("*.bak"))
    assert run(files, apply=True) == 0 and a.exists()  # a fresh run reads the new line and goes ahead


def test_bytes_that_are_not_utf8_pass_through(tmp_path: Path):
    h, a = tmp_path / "HANDOFF.md", tmp_path / "arch.md"
    raw = TEXT.replace("\n", "\r\n").encode("utf-8").replace(b"Old line one.", b"Old \x96 line one.").replace(b"The newest line.", b"The \x96 newest line.")
    h.write_bytes(raw)
    hs.apply_plan(hs.make_plan(h, a, 7, NOW))
    assert b"The \x96 newest line." in h.read_bytes() and b"Old \x96 line one." in a.read_bytes()


def test_no_stamp_lines_means_nothing_to_do(tmp_path: Path):
    h, a = tmp_path / "HANDOFF.md", tmp_path / "arch.md"
    data = write(h, "# T\n\n## 1. Goal\n\nprose only\n")
    plan = hs.make_plan(h, a, 7, NOW)
    assert not plan.moved and hs.apply_plan(plan) is None and h.read_bytes() == data and not a.exists()


# ----------------------------------------------------------------------------------------------------- the options
def test_max_words_moves_newer_blocks_newest_kept_first(files):
    h, a = files
    full = hs.make_plan(h, a, 7, NOW)
    kept_all = sum(hs.words(b.lines) for b in full.blocks if not b.move)
    fixed = hs.words(full.live_lines) - kept_all
    # room for the newest block only: the two recent blocks before it move
    newest = max((b for b in full.blocks if not b.move), key=lambda b: b.stamp)
    plan = hs.make_plan(h, a, 7, NOW, max_words=fixed + hs.words(newest.lines))
    kept = [b for b in plan.blocks if not b.move]
    assert [b.stamp for b in kept] == [newest.stamp]
    assert hs.words(plan.live_lines) <= fixed + hs.words(newest.lines)
    # no room at all: every stamped block moves, the fixed part stays
    none = hs.make_plan(h, a, 7, NOW, max_words=1)
    assert not [b for b in none.blocks if not b.move] and "## 1. Goal" in "\n".join(none.live_lines)


def test_archive_sections_and_intros_leave_pointers(files):
    h, a = files
    plan = hs.make_plan(h, a, 7, NOW, archive_sections=r"^1\.")
    live = "\n".join(plan.live_lines)
    assert "Plan prose that has no stamps" not in live and "## 1. Goal" in live and "the body of this section moved to HANDOFF-archive.md" in live
    # intros through the main entry point
    assert run(files, "--archive-intros", apply=True) == 0
    live2 = h.read_bytes().decode("utf-8")
    assert "Review introduction paragraph." not in live2 and "the introduction moved to HANDOFF-archive.md" in live2
    assert "Review introduction paragraph." in a.read_text(encoding="utf-8") and "## 0. Week review" in live2


def test_alerts_block_is_never_moved_even_by_archive_sections(files):
    h, a = files
    plan = hs.make_plan(h, a, 7, NOW, archive_sections=r"alerts|^1\.|^0\.")
    live = "\n".join(plan.live_lines)
    assert "An old alert line that must stay." in live and "an unstamped alert" in live
    assert all("alert" not in b.section.lower() for b in plan.moved)


def test_alerts_header_is_a_regex_option(files):
    h, a = files
    plan = hs.make_plan(h, a, 7, NOW, alerts_header=r"week review")  # make the review the protected block: its old lines stay
    assert "Old line one." in "\n".join(plan.live_lines)


# ----------------------------------------------------------------------------------------------------- the command line
def test_main_missing_file_and_exclusive_flags(tmp_path: Path, capsys):
    assert hs.main(["--handoff", str(tmp_path / "none.md"), "--archive", str(tmp_path / "a.md")]) == 2
    with pytest.raises(SystemExit):
        hs.main(["--handoff", str(tmp_path / "h.md"), "--archive", str(tmp_path / "a.md"), "--apply", "--dry-run"])


def test_default_is_a_dry_run(files):
    h, a = files
    before = h.read_bytes()
    assert hs.main(["--handoff", str(h), "--archive", str(a), "--now", "2026-11-19T02:00:00Z"]) == 0
    assert h.read_bytes() == before and not a.exists()
