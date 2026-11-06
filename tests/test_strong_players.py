"""The strong-player set (tools/spire_codex/strong_players.py): the exam rule, the shrunk rank, the selection, suppression, and that no
player id leaves the process (D55 addendum 7). Synthetic runs only."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "spire_codex"))
import boss_entry as be  # noqa: E402
import fifths as ff  # noqa: E402
import filter_a10 as fa  # noqa: E402
import strong_players as sp  # noqa: E402


def run(rid: str, token: str | None, win: bool, acts: int = 1, char: str = "CHARACTER.IRONCLAD") -> dict:
    return {"run_hash": rid, "player_token": token, "ascension": 10, "game_mode": "standard", "was_abandoned": False, "modifiers": [],
            "build_id": "v0.107.1", "win": win, "players": [{"character": char, "badges": [1]}],
            "map_point_history": [[{"map_point_type": "monster"}] for _ in range(acts)]}


def ids_in_fifth(fifth: int, n: int, tag: str) -> list[str]:
    out, i = [], 0
    while len(out) < n:
        rid = f"{tag}{i:06d}"
        if sp.exam_bucket(rid) == fifth:
            out.append(rid)
        i += 1
    return out


def test_fifth_rule_equals_the_published_one():
    for rid in ("0016540b2159554f", "abc", "seed:123", "zzzz9"):
        assert sp.exam_bucket(rid) == be.exam_bucket(rid)
        assert sp.is_exam(rid, frozenset()) == be.is_exam(rid)
    assert sp.EXAM_SALT == be.EXAM_SALT and sp.EXAM_BUCKET == be.EXAM_BUCKET


def test_shrunk_is_the_beta_posterior_mean():
    assert sp.shrunk(0, 0, 0.1, 20) == 0.1
    assert abs(sp.shrunk(10, 20, 0.1, 20) - (10 + 2) / 40) < 1e-12
    # more evidence moves the rate further from the pool's
    assert sp.shrunk(50, 100, 0.1, 20) > sp.shrunk(5, 10, 0.1, 20)
    assert sp.shrunk(5, 10, 0.1, 20) < 0.5


def test_boss_reach():
    assert sp.reached(run("r", "t", False, acts=1)) == (0, 0)
    assert sp.reached(run("r", "t", False, acts=2)) == (1, 0)
    assert sp.reached(run("r", "t", False, acts=3)) == (1, 1)
    assert sp.reached(run("r", "t", True, acts=1)) == (1, 1)


def build_file(tmp_path: Path) -> tuple[str, str, set[str]]:
    """30 players with 20 or more runs: players P00..P07 win 60 in 100, the other 22 win 5 in 100; one player of 5 runs; some exam runs."""
    runs, strong_players = [], set()
    pool = [rid for f in (1, 2, 3, 4) for rid in ids_in_fifth(f, 200, f"p{f}")]
    k = 0
    for p in range(30):
        tok = f"PLAYER{p:02d}"
        rate = 0.6 if p < 8 else 0.05
        if p < 8:
            strong_players.add(tok)
        for j in range(25):
            runs.append(run(pool[k], tok, j < round(25 * rate), acts=2 if j % 2 else 1))
            k += 1
    for j in range(5):
        runs.append(run(pool[k], "SMALL", True))
        k += 1
    exam = ids_in_fifth(0, 30, "x")
    for j, rid in enumerate(exam):
        runs.append(run(rid, "PLAYER00", True))  # exam runs of a strong player: never counted into the selection
    runs.append(run("other-char", "PLAYER00", True, char="CHARACTER.SILENT"))
    path = tmp_path / "a10.jsonl.gz"
    with gzip.open(path, "wt") as fh:
        for r in runs:
            fh.write(json.dumps(r) + "\n")
    ids = tmp_path / "exam.txt"
    ids.write_text("\n".join(exam[:10]) + "\n")
    return str(path), str(ids), strong_players


def test_selection_and_report(tmp_path):
    src, ids, strong = build_file(tmp_path)
    out = tmp_path / "out"
    assert sp.main([src, ids, str(out), "--write-corpus"]) == 0
    rep = json.loads((out / "aggregates.json").read_text())
    assert rep["players"]["with_token"] == 31 and rep["players"]["eligible"] == 30 and rep["players"]["under_threshold"] == 1
    assert rep["players"]["strong"] == 8  # ceil(0.25 * 30)
    assert rep["read"]["exam_fifth_runs"] == 30  # the ids file lists 10 of them, the hash rule the other 20; the Silent run is not Ironclad
    assert rep["groups"]["strong"]["runs"] == 8 * 25
    assert rep["groups"]["strong"]["wins"] == 8 * 15
    # exam runs of the strong player are reported as the exam only, never in the pool
    assert rep["exam_fifth_of_strong_players"]["runs"] == 30
    assert rep["groups"]["pool"]["runs"] == 30 * 25 + 5
    # the corpus: strong players' non-exam runs, no token
    lines = [json.loads(x) for x in gzip.open(out / "strong_corpus.jsonl.gz", "rt")]
    assert len(lines) == 8 * 25 and all("player_token" not in r for r in lines)
    assert not any(sp.is_exam(sp.run_id(r), frozenset()) for r in lines)


def test_no_player_id_in_the_report(tmp_path):
    src, ids, _ = build_file(tmp_path)
    out = tmp_path / "out"
    sp.main([src, ids, str(out)])
    text = (out / "aggregates.json").read_text()
    assert "PLAYER" not in text and "SMALL" not in text


def test_small_cells_are_suppressed():
    t = sp.Tally()
    for _ in range(sp.MIN_CELL - 1):
        t.add(1, 1, 1)
    assert t.row()["suppressed"] and t.row()["runs"] is None and t.row()["wins_per_100"] is None
    t.add(0, 1, 0)
    row = t.row()
    assert row["runs"] == sp.MIN_CELL and row["wins_per_100"] == 95.0 and row["act2_boss_per_100"] == 95.0


def test_filter_keeps_the_token_only_with_the_flag(tmp_path):
    src = tmp_path / "in.jsonl.gz"
    with gzip.open(src, "wt") as fh:
        fh.write(json.dumps(run("a1", "TOKEN-A", True)) + "\n")
    for flag, name in ((False, "plain"), (True, "kept")):
        out = tmp_path / name
        fa.main(str(src), str(out), flag)
        (row,) = [json.loads(x) for x in gzip.open(out / "a10_standard_single.jsonl.gz", "rt")]
        assert ("player_token" in row) == flag
        assert "badges" not in row["players"][0]
        stats = json.loads((out / "stats.json").read_text())
        assert "TOKEN-A" not in json.dumps(stats)
        assert stats.get("kept_with_player_token") == (1 if flag else None)


def test_fifths_follow_the_published_rule_and_old_exam_ids_stay(tmp_path):
    src = tmp_path / "v.jsonl.gz"
    fifth_ids = {f: ids_in_fifth(f, 25, f"f{f}") for f in range(5)}
    with gzip.open(src, "wt") as fh:
        for f, ids in fifth_ids.items():
            for j, rid in enumerate(ids):
                fh.write(json.dumps(run(rid, None, j < 5, acts=1 + (j % 3))) + "\n")
        fh.write(json.dumps(run("silent-run", None, True, char="CHARACTER.SILENT")) + "\n")
    gone = "an-old-exam-run-no-longer-in-the-file"
    old = tmp_path / "old.txt"
    old.write_text("\n".join([fifth_ids[0][0], gone]) + "\n")
    ff.main(str(src), str(old), str(tmp_path / "o"))
    out = json.loads((tmp_path / "o" / "fifths.json").read_text())
    assert [out["fifths"][str(f)]["runs"] for f in range(5)] == [25] * 5
    assert out["ironclad_a10_runs"] == 125 and out["exam_ids_old_still_in_file"] == 1
    ids = (tmp_path / "o" / "exam_ids.txt").read_text().split()
    assert set(ids) == set(fifth_ids[0]) | {gone} and len(ids) == 26  # the old ids stay exam, the file's bucket 0 joins
    assert all(ff.exam_bucket(r) == be.exam_bucket(r) for r in fifth_ids[3])
