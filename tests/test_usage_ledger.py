"""tools/usage_ledger.py on a made-up HANDOFF (every line below is invented) and one run over the real file.

The fixture's timeline (weeks reset Tuesdays 21:00Z; 2026-11-03 and 2026-11-10 are Tuesdays):

  week of 2026-11-03 21:00Z   T1 alone (1 -> 3, start read from the orchestrator's 08:00Z reading); T2 and T3 overlap
                              (3 -> 6 and 3 -> 8, so the bar moved 5 across the group); T4 never got its end figure; the
                              last reading of the week is 40
  week of 2026-11-10 21:00Z   T6 straddles the reset (n/a); T7 alone (2 -> 4)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import usage_ledger as ul  # noqa: E402

HANDOFF = """\
# Handoff (made up)

- **An undated heading line that mentions usage 99% all.**
- *2026-11-04 08:00Z, orchestrator.* **Reset passed.** Usage 1% all / 0% Fable at 08:00Z (ceiling 65, stop 63).
- *2026-11-04 09:00Z, worker (T1, solo job).* **Done.** Spireline main abc1234. Usage at start about 1% all; end: 3% all / 1% Fable at 09:05Z.
- *2026-11-04 09:30Z, orchestrator.* **Landed T1.** Usage about 3 all / 1 Fable at 09:30Z.
- *2026-11-04 11:00Z, worker C (T2, left half), part 1.* **Done.** Usage at start 3% all / 1% Fable (09:30Z); end 6% all / 3% Fable at 11:00Z (shared span with T3).
- *2026-11-04 11:30Z, worker (T3, right half).* **Done.** Usage at start 3% all / 1% Fable at 2026-11-04 10:00Z; end: 8% all / 4% Fable at 11:30Z.
- *2026-11-04 12:00Z, orchestrator (owner: "go on").* Usage 8 in 100 all / 4 in 100 Fable at 12:00Z.
- *2026-11-04 13:00Z, worker (T4, no end yet).* **Running.** Usage at start 8% all / 4% Fable at 12:00Z; end: (orchestrator).
- *2026-11-04 14:00Z, worker (T5, no figures).* **Did a thing.** Nothing about the bar here.
- *2026-11-04.* Notes with no time and no figures.
- *2026-11-10 20:30Z, orchestrator.* Usage 40% all / 30% Fable at 20:30Z (ceiling 65).
- *2026-11-11 00:30Z, worker (T6, across the reset).* **Done.** Usage at start 40% all / 30% Fable at 2026-11-10 20:30Z; end: 2% all / 1% Fable at 00:25Z.
- *2026-11-11 01:00Z, orchestrator.* Usage 2% all / 1% Fable at 01:00Z.
- *2026-11-11 03:00Z, worker (T7, odd phrasing).* **Done.** Usage at start 2% all / 1% Fable at 01:00Z; end 4% all / 2% Fable at 03:00Z.
"""

REAL = Path(__file__).resolve().parents[2] / "referee" / "backlog" / "HANDOFF.md"
NOW_W1 = datetime(2026, 11, 5, 0, 0, tzinfo=timezone.utc)


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


@pytest.fixture(scope="module")
def parsed() -> ul.Parsed:
    return ul.parse_handoff(HANDOFF)


def item(parsed: ul.Parsed, tag: str) -> ul.Item:
    return next(it for it in parsed.items if it.label.startswith(tag))


# ---------------------------------------------------------------------------------------------------- weeks
def test_the_reset_is_tuesday_2100z():
    assert utc("2026-11-03T21:00Z").weekday() == 1 and utc("2026-11-10T21:00Z").weekday() == 1
    assert ul.week_start(utc("2026-11-10T21:00Z")) == utc("2026-11-10T21:00Z")
    assert ul.week_start(utc("2026-11-10T20:59Z")) == utc("2026-11-03T21:00Z")
    assert ul.week_start(utc("2026-11-04T01:30Z")) == utc("2026-11-03T21:00Z")
    assert ul.week_start(utc("2026-11-03T20:46Z")) == utc("2026-10-27T21:00Z")


# ---------------------------------------------------------------------------------------------------- parsing
def test_lines_and_counts(parsed):
    assert parsed.lines_read == 13  # the heading line is not a dated line
    assert [it.label.split(",")[0] for it in parsed.items] == ["T1", "T2", "T3", "T4", "T6", "T7"]
    assert parsed.lines_with_figures == 11  # the T5 line and the note have none


def test_about_and_missing_percent_and_in_100():
    p = ul.parse_handoff(
        "- *2026-11-04 09:30Z, orchestrator.* Usage about 93 all / 63 Fable at 09:30Z.\n"
        "- *2026-11-04 10:00Z, orchestrator.* usage 15% all / 22% Fable.\n"
        "- *2026-11-04 11:00Z, orchestrator.* Usage 8 in 100 all / 4 in 100 Fable at 11:00Z.\n"
        "- *2026-11-04 12:00Z, orchestrator.* Usage reading: weekly all models 5%, Fable 8%\n"
        "- *2026-11-04 13:00Z, orchestrator.* Usage 2% all at 13:00Z (ceiling 65).\n"
        "- *2026-11-04 14:00Z, orchestrator.* Usage page 61% weekly at 14:00Z; usage was 62% at 14:30Z.\n")
    got = [(r.when.strftime("%H:%M"), r.all, r.fable, r.approx) for r in p.readings]
    assert got == [("09:30", 93.0, 63.0, True), ("10:00", 15.0, 22.0, False), ("11:00", 8.0, 4.0, False),
                   ("12:00", 5.0, 8.0, False), ("13:00", 2.0, None, False), ("14:00", 61.0, None, False),
                   ("14:30", 62.0, None, False)]


def test_a_time_before_midnight_belongs_to_the_day_before_a_line_stamped_after_it():
    p = ul.parse_handoff("- *2026-11-04 00:25Z, orchestrator.* Usage 85% all / 60% Fable at 23:50Z.\n")
    assert p.readings[0].when == utc("2026-11-03T23:50Z")


def test_item_labels():
    assert ul.item_label("worker (D51, loop library move).") == ("D51, loop library move", "worker")
    assert ul.item_label("worker C (reset order, D45), part 1") == ("reset order, D45, part 1", "worker C")
    assert ul.item_label("orchestrator") == ("orchestrator", "worker")


def test_items_start_end_and_inferred_start(parsed):
    t1 = item(parsed, "T1")
    assert (t1.start_all, t1.end_all, t1.start_fable, t1.end_fable) == (1.0, 3.0, None, 1.0)
    assert t1.start_inferred and t1.start_when == utc("2026-11-04T08:00Z")  # the orchestrator's 1% reading
    assert t1.end_when == utc("2026-11-04T09:05Z") and t1.points == 2.0 and t1.fable_points is None
    t2 = item(parsed, "T2")
    assert not t2.start_inferred and t2.start_when == utc("2026-11-04T09:30Z") and t2.says_shared
    t3 = item(parsed, "T3")
    assert t3.start_when == utc("2026-11-04T10:00Z") and (t3.end_all, t3.end_fable) == (8.0, 4.0)
    t4 = item(parsed, "T4")
    assert t4.unfilled and t4.end_all is None
    t7 = item(parsed, "T7")
    assert (t7.end_all, t7.end_when) == (4.0, utc("2026-11-11T03:00Z"))  # "end 4% ..." without the colon


def test_classification_and_groups(parsed):
    kinds = ul.classify(parsed.items)
    by_tag = {it.label.split(",")[0]: kinds[id(it)] for it in parsed.items}
    assert by_tag == {"T1": "solo", "T2": "shared", "T3": "shared", "T4": "unfilled", "T6": "spans reset", "T7": "solo"}
    groups = ul.groups_of_shared(parsed.items)
    assert len(groups) == 1 and {it.label.split(",")[0] for it in groups[0]} == {"T2", "T3"}


def test_touching_intervals_do_not_overlap():
    a = (utc("2026-11-04T08:00Z"), utc("2026-11-04T09:00Z"))
    b = (utc("2026-11-04T09:00Z"), utc("2026-11-04T10:00Z"))
    assert not ul.overlaps(a, b) and ul.overlaps(a, (utc("2026-11-04T08:59Z"), utc("2026-11-04T10:00Z")))


# ---------------------------------------------------------------------------------------------------- the markdown
def rows(text: str, heading: str) -> list[list[str]]:
    """The cells of the table under `## heading`, without its two header rows."""
    block = text.split(f"## {heading}\n", 1)[1].strip().split("\n\n")[0]
    return [[c.strip() for c in ln.strip("|").split("|")] for ln in block.splitlines()[2:]]


def test_ledger_items_table(parsed):
    text = ul.ledger(parsed, None, NOW_W1, "HANDOFF.md")
    items = {r[0].split(",")[0]: r for r in rows(text, "Items")}
    assert items["T1"][2:6] == ["~2026-11-04 08:00Z", "2026-11-04 09:05Z", "+2", "n/a"]
    assert items["T2"][4] == "shared" and items["T3"][4] == "shared"
    assert "T3" in items["T2"][6] and "the line says so too" in items["T2"][6]
    assert items["T4"][4] == "n/a" and "not filled" in items["T4"][6]
    assert items["T6"][4] == "n/a" and "different weeks" in items["T6"][6]
    assert items["T7"][4] == "+2" and items["T7"][5] == "+1"
    assert "T5" not in items  # no figures: skipped


def test_ledger_weeks_table(parsed):
    text = ul.ledger(parsed, None, utc("2026-11-11T04:00Z"), "HANDOFF.md")
    weeks = {r[0]: r for r in rows(text, "Weeks")}
    w1, w2 = weeks["2026-11-03 21:00Z (last)"], weeks["2026-11-10 21:00Z (current)"]
    assert w1[2].startswith("40 / 30 at 2026-11-10 20:30Z")
    assert w1[3] == "1 items, 2 pts" and w1[4] == "2 items 5 pts" and w1[5] == "7 pts" and w1[6] == "33 pts" and w1[7] == "1"
    assert w2[2].startswith("4 / 2 at 2026-11-11 03:00Z")
    assert w2[3] == "1 items, 2 pts" and w2[4] == "none" and w2[6] == "2 pts"
    groups = rows(text, "Shared groups")
    assert groups == [["1", "2", "2026-11-04 09:30Z to 2026-11-04 11:30Z", "3 -> 8", "5"]]


def test_since_drops_older_items_and_weeks(parsed):
    text = ul.ledger(parsed, utc("2026-11-11T00:00Z"), utc("2026-11-11T04:00Z"), "HANDOFF.md")
    assert {r[0].split(",")[0] for r in rows(text, "Items")} == {"T6", "T7"}
    assert [r[0] for r in rows(text, "Weeks")] == ["2026-11-10 21:00Z (current)"]


def test_cli_prints_markdown_and_no_paths(tmp_path, capsys):
    f = tmp_path / "HANDOFF.md"
    f.write_text(HANDOFF, encoding="utf-8")
    assert ul.main([str(f), "--since", "2026-11-01", "--now", "2026-11-11T04:00Z"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Usage ledger: HANDOFF.md (since 2026-11-01)") and "## Items" in out and "## Weeks" in out
    assert str(tmp_path) not in out


def test_empty_and_figureless_files_do_not_crash(tmp_path):
    for text in ("", "nothing here\n", "- *2026-11-04 10:00Z, worker (X).* **No figures.**\n"):
        p = ul.parse_handoff(text)
        assert not p.items
        assert "## Items" in ul.ledger(p, None, NOW_W1, "x")


def test_the_real_file_does_not_crash():
    if not REAL.is_file():
        pytest.skip("no HANDOFF.md beside this checkout")
    p = ul.parse_handoff(REAL.read_text(encoding="utf-8", errors="replace"))
    text = ul.ledger(p, None, datetime.now(timezone.utc), REAL.name)
    assert p.lines_read > 50 and "## Weeks" in text
    for w in rows(text, "Weeks"):
        assert len(w) == 8
