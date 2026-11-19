"""tools/weekly_numbers.py on a made-up lab root: small synthetic folders for each of the five numbers; nothing real is read or copied.

The root built by `make_root` holds (all under referee/)

  LAB/nightly/2026-11-01/g9 + g9-emu           an older block (the 'previous block' of the alarm), 40 real runs, 40 copy runs
  LAB/nightly/2026-11-06T0852/g12, g13, g13-emu  the newest block: g12 (no copy arm), g13 with a copy arm on 40 of its 42 seeds
  agent/current.json                           the champion: generation 14, folder gen14/cand-new
  agent/promotions.tsv                         gen13 promoted (cand-old); gen14 refused once and promoted (cand-new) on E2
  agent/gen13/cand-old/arms/E1-a3-v1, E2-a3-v1, E3-a3-v1   the previous champion's arms
  agent/gen14/cand-new/arms/E1-a3-v1, E2-a3-v1, E3-a3-v1   the champion's arms (E1 judged an earlier attempt, E2 promoted it, E3 is fresh)
  seed-exam/2026-11-12-gen13/summary.json, 2026-11-14-gen14/summary.json
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import weekly_numbers as wn  # noqa: E402

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
SEED_PREFIX = "ZQSEED"  # no seed of the fixtures may reach an output


# ----------------------------------------------------------------------------------------------------- fixture builders
def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def real_end(seed: str, floor: int, end: str = "death", acts: list | None = None) -> dict:
    return {"ev": "end", "seed": seed, "end": end, "floor": floor, "boss_damage_acts": acts or []}


def real_crash(seed: str) -> dict:
    return {"ev": "crash", "seed": seed, "error": "boom"}


def copy_row(seed: str, floor: int, win: bool = False, acts: list | None = None, crash: bool = False) -> dict:
    return {"seed": seed, "floor": floor, "win": win, "end": "win" if win else "death", "crash": crash, "boss_damage_acts": acts or []}


def seed(i: int) -> str:
    return "%s%03d" % (SEED_PREFIX, i)


def arm_rows(prefix: str, spec: list[tuple]) -> list[dict]:
    """spec: (floor, win) per seed in order."""
    return [copy_row("%s%03d" % (prefix, i), f, w) for i, (f, w) in enumerate(spec)]


def promotions(rows: list[dict]) -> str:
    cols = ["written", "cand_gen", "base_gen", "seed_block", "seeds", "decision", "cand_dir", "rule"]
    lines = ["\t".join(cols)]
    for r in rows:
        lines.append("\t".join(str(r.get(c, "")) for c in cols))
    return "\n".join(lines) + "\n"


def make_root(tmp_path: Path, with_fresh: bool = True) -> Path:
    root = tmp_path / "lab"
    nightly = root / "referee" / "LAB" / "nightly"
    # previous block: 40 pairs, real ends and copy ends mostly agree
    prev_real = [real_end(seed(i), 10 if i < 20 else 25) for i in range(40)]
    prev_copy = [copy_row(seed(i), 11 if i < 20 else 24) for i in range(40)]
    write_jsonl(nightly / "2026-11-01" / "g9" / "runs.jsonl", prev_real)
    write_jsonl(nightly / "2026-11-01" / "g9-emu" / "runs.jsonl", prev_copy)
    # newest block: g12 (real only) and g13 (real 42 rows incl. 1 crash; copy on the first 40 seeds)
    new = nightly / "2026-11-06T0852"
    write_jsonl(new / "g12" / "runs.jsonl", [real_end(seed(i), 12) for i in range(5)])
    real13 = []
    for i in range(40):
        if i < 10:
            real13.append(real_end(seed(i), 10))  # Act 1
        elif i < 20:
            real13.append(real_end(seed(i), 20))  # Act 2
        elif i < 30:
            real13.append(real_end(seed(i), 40))  # Act 3, not at the boss
        elif i < 34:
            real13.append(real_end(seed(i), 48, acts=[[0, 1.0], [1, 1.0], [2, 0.4]]))  # at the Act 3 boss, died there
        elif i < 36:
            real13.append(real_end(seed(i), 49, acts=[[2, 1.0]]))  # got past
        else:
            real13.append(real_end(seed(i), 33))  # Act 2 boss floor
    real13.append(real_end(seed(40), 49, end="win"))  # a win; not in the copy arm
    real13.append(real_crash(seed(41)))
    write_jsonl(new / "g13" / "runs.jsonl", real13)
    copy13 = []
    for i in range(40):
        if i < 8:
            copy13.append(copy_row(seed(i), 12))  # same act as real (Act 1)
        elif i < 10:
            copy13.append(copy_row(seed(i), 25))  # real Act 1, copy Act 2
        elif i < 18:
            copy13.append(copy_row(seed(i), 22))  # same act (Act 2)
        elif i < 20:
            copy13.append(copy_row(seed(i), 12))  # real Act 2, copy Act 1
        elif i < 30:
            copy13.append(copy_row(seed(i), 41))  # same act (Act 3)
        elif i < 32:
            copy13.append(copy_row(seed(i), 48, acts=[[2, 0.9]]))  # arrived, died
        elif i < 33:
            copy13.append(copy_row(seed(i), 49, acts=[[2, 1.0]]))  # passed where real died
        elif i < 34:
            copy13.append(copy_row(seed(i), 40))
        elif i < 35:
            copy13.append(copy_row(seed(i), 49, acts=[[2, 1.0]]))  # both passed
        elif i < 36:
            copy13.append(copy_row(seed(i), 48, acts=[[2, 0.5]]))  # real passed, copy did not
        else:
            copy13.append(copy_row(seed(i), 33))
    write_jsonl(new / "g13-emu" / "runs.jsonl", copy13)
    # the champion
    agent = root / "referee" / "agent"
    (agent).mkdir(parents=True, exist_ok=True)
    (agent / "current.json").write_text(json.dumps({"generation": 14, "dir": "D:\\anything\\referee\\agent\\gen14\\cand-new",
                                                    "promoted": "2026-11-18T16:05:04Z"}), encoding="utf-8")
    (agent / "promotions.tsv").write_text(promotions([
        {"written": "2026-11-15T10:00:00Z", "cand_gen": 13, "base_gen": 12, "seed_block": "E0", "decision": "promoted", "cand_dir": "cand-old"},
        {"written": "2026-11-17T10:00:00Z", "cand_gen": 14, "base_gen": 13, "seed_block": "E1", "decision": "rejected", "cand_dir": "cand-new"},
        {"written": "2026-11-18T16:05:04Z", "cand_gen": 14, "base_gen": 13, "seed_block": "E2", "decision": "promoted", "cand_dir": "cand-new",
         "rule": "v3 | pooled E2 (4) + E1 (4) = 8 pairs | funnel"},
    ]), encoding="utf-8")

    def arms(gen: str, name: str, block: str, spec: list[tuple]) -> None:
        write_jsonl(agent / gen / name / "arms" / (block + "-a3-v1") / "runs.jsonl", arm_rows(block, spec))

    # block E1 / E2: 4 pairs each; E3: 6 pairs (fresh). (floor, win): a pass is floor 49 or a win
    arms("gen14", "cand-new", "E1", [(49, False), (48, False), (30, False), (10, False)])
    arms("gen13", "cand-old", "E1", [(48, False), (48, False), (49, False), (10, False)])
    arms("gen14", "cand-new", "E2", [(49, True), (49, False), (48, False), (20, False)])
    arms("gen13", "cand-old", "E2", [(49, False), (30, False), (30, False), (20, False)])
    if with_fresh:
        arms("gen14", "cand-new", "E3", [(49, False), (49, False), (48, False), (48, False), (30, False), (49, True)])
        arms("gen13", "cand-old", "E3", [(49, False), (48, False), (48, False), (30, False), (30, False), (48, False)])
    # exams
    for name, gen, written, diff, won_draws in (("2026-11-12-gen13", 13, "2026-11-12T08:00:00Z", -20.0, 0), ("2026-11-14-gen14", 14, "2026-11-14T08:00:00Z", -18.5, 1)):
        exam = {"agent": {"generation": gen}, "written": written, "draws": 2,
                "ours": {"won": {"runs": 400, "win_rate": won_draws / 400.0}},
                "paired": {"won": {"seeds": 200, "floor_diff": {"n": 200, "mean": diff, "lo": diff - 1.2, "hi": diff + 1.2}, "some_draw_won": won_draws}}}
        (root / "referee" / "seed-exam" / name).mkdir(parents=True, exist_ok=True)
        (root / "referee" / "seed-exam" / name / "summary.json").write_text(json.dumps(exam), encoding="utf-8")
    return root


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return make_root(tmp_path)


# ----------------------------------------------------------------------------------------------------- statistics and rows
def test_wilson_known_values():
    assert wn.wilson(0, 0) is None
    lo, hi = wn.wilson(0, 2000)
    assert lo == 0.0 and hi == pytest.approx(0.001919, abs=2e-6)  # the 0 of 1,995 / 2,000 upper bound is about 0.19 in 100
    lo, hi = wn.wilson(50, 100)
    assert (lo + hi) / 2 == pytest.approx(0.5, abs=1e-9) and hi - lo == pytest.approx(0.1928, abs=2e-3)


def test_rate_has_k_n_per100_and_interval():
    r = wn.rate(52, 2000)
    assert (r["k"], r["n"], r["per100"]) == (52, 2000, 2.6)
    assert r["lo"] < 2.6 < r["hi"]
    z = wn.rate(0, 0)
    assert z["per100"] is None and z["lo"] is None


def test_act_of_boundaries():
    assert [wn.act_of(f, False) for f in (1, 17, 18, 33, 34, 48, 49)] == [1, 1, 2, 2, 3, 3, 3]
    assert wn.act_of(5, True) == 3


def test_norm_row_arrival_and_strict_pass():
    assert wn.norm_row(real_end("a", 47))["arrived"] is False
    at48 = wn.norm_row(real_end("a", 48))
    assert at48["arrived"] and not at48["passed"]  # at the boss, died there: arrived, not passed (a full bar of damage does not count)
    by_entry = wn.norm_row(real_end("a", 40, acts=[[2, 0.3]]))
    assert by_entry["arrived"] and not by_entry["passed"]
    assert wn.norm_row(real_end("a", 49))["passed"]
    won = wn.norm_row(real_end("a", 48, end="win"))
    assert won["passed"] and won["win"] and won["arrived"]
    assert wn.norm_row({}, crash=True) == {"floor": 0, "win": False, "arrived": False, "passed": False, "crash": True}
    assert wn.norm_row({"floor": "x"})["floor"] == 0  # a bad floor reads as 0, not an error


def test_load_real_counts_crashes_and_later_end_replaces_crash(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in [
        {"ev": "boot", "seed": "x"}, real_end("a", 30), real_crash("b"), real_end("b", 12), real_crash("c")]) + "\nnot json\n", encoding="utf-8")
    rows = wn.load_real(p)
    assert set(rows) == {"a", "b", "c"}
    assert rows["b"]["crash"] is False and rows["b"]["floor"] == 12
    assert rows["c"]["crash"] is True


def test_load_arm_skips_foreign_events(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    write_jsonl(p, [copy_row("a", 49), {"ev": "boot", "seed": "z"}, copy_row("b", 5, crash=True)])
    rows = wn.load_arm(p)
    assert set(rows) == {"a", "b"} and rows["b"]["crash"] and rows["a"]["passed"]


# ----------------------------------------------------------------------------------------------------- number 1
def test_number1_prefers_the_champions_block_and_ages_it(tmp_path: Path):
    root = make_root(tmp_path)
    nightly = root / "referee" / "LAB" / "nightly"
    # the champion (generation 14) has an older block of its own; the newest block lacks it
    write_jsonl(nightly / "2026-11-03" / "g14" / "runs.jsonl", [real_end(seed(i), 20, end="win" if i < 2 else "death") for i in range(10)] + [real_crash(seed(10))])
    champ = wn.champion_of(root)
    assert champ["generation"] == 14 and champ["dir"] == "gen14/cand-new"
    n1 = wn.number1(root, champ, wn.list_blocks(nightly), NOW)
    assert n1["status"] == "ok" and n1["champion_has_real_block"] is True
    assert n1["block"] == "2026-11-03" and n1["generation"] == 14
    assert n1["wins"]["k"] == 2 and n1["wins"]["n"] == 11  # the crash is in the denominator, as a loss
    assert n1["crash_rows"] == 1 and n1["end_rows"] == 10
    assert n1["age_days"] == 16.5  # 2026-11-03 00:00 to 2026-11-19 12:00
    assert n1["summary_json"] is False and "may still be running" in n1["note"]


def test_number1_without_the_champion_shows_the_newest_blocks_top_generation(root: Path):
    n1 = wn.number1(root, wn.champion_of(root), wn.list_blocks(root / "referee" / "LAB" / "nightly"), NOW)
    assert n1["status"] == "not the champion" and n1["champion_has_real_block"] is False
    assert n1["generation"] == 13 and n1["block"] == "2026-11-06T0852"
    assert n1["wins"]["k"] == 1 and n1["wins"]["n"] == 42  # the win row counts; the crash row is a loss
    assert n1["age_days"] == 13.1  # 2026-11-06 08:52 to 2026-11-19 12:00
    assert "no real block holds generation 14" in n1["reason"]
    assert n1["folder"] == "referee/LAB/nightly/2026-11-06T0852/g13"


def test_a_block_just_started_with_an_empty_runs_file_is_skipped(root: Path):
    nightly = root / "referee" / "LAB" / "nightly"
    (nightly / "2026-11-19T1100" / "g14").mkdir(parents=True)
    (nightly / "2026-11-19T1100" / "g14" / "runs.jsonl").write_text("", encoding="utf-8")
    n1 = wn.number1(root, wn.champion_of(root), wn.list_blocks(nightly), NOW)
    assert n1["block"] == "2026-11-06T0852"  # the empty block is not read; its rows will count once the first run ends
    write_jsonl(nightly / "2026-11-19T1100" / "g14" / "runs.jsonl", [real_end(seed(0), 30), real_end(seed(1), 49, end="win")])
    n1 = wn.number1(root, wn.champion_of(root), wn.list_blocks(nightly), NOW)
    assert n1["block"] == "2026-11-19T1100" and n1["status"] == "ok" and n1["wins"]["k"] == 1 and n1["wins"]["n"] == 2
    assert "may still be running" in n1["note"] and n1["age_days"] == 0.0


def test_number1_no_blocks(tmp_path: Path):
    n1 = wn.number1(tmp_path, None, wn.list_blocks(tmp_path / "nothing"), NOW)
    assert n1["status"] == wn.NO_DATA and "no real block" in n1["reason"]


def test_block_names_both_forms():
    assert wn.block_start("2026-11-06") == datetime(2026, 11, 6, tzinfo=timezone.utc)
    assert wn.block_start("2026-11-06T0852") == datetime(2026, 11, 6, 8, 52, tzinfo=timezone.utc)
    assert wn.block_start("last-ok") is None and wn.block_start("2026-13-40") is None


# ----------------------------------------------------------------------------------------------------- number 2
def test_number2_real_and_copy_on_the_same_seeds(root: Path):
    blocks = wn.list_blocks(root / "referee" / "LAB" / "nightly")
    sel = wn.select_block(blocks, 14)  # the champion (14) has no block here: the newest block's top generation (13) is read
    n1 = wn.number1(root, wn.champion_of(root), blocks, NOW)
    n2 = wn.number2(root, sel, n1)
    # real, all 42 rows: arrivals = 4 at floor 48 + 2 at 49 + 1 win = 7; passes = 2 + 1 win = 3
    assert n2["real_all"]["runs"] == 42 and n2["real_all"]["arrivals"] == 7 and n2["real_all"]["passed"] == 3
    assert n2["paired_seeds"] == 40  # the win row and the crash row are not in the copy arm
    # real on the 40 shared seeds: arrivals 6, passes 2; copy: arrivals 2 (floor 48) + 1 + 1 + 1 = 5, passes 2
    assert (n2["real_paired"]["arrivals"], n2["real_paired"]["passed"]) == (6, 2)
    assert (n2["copy_paired"]["arrivals"], n2["copy_paired"]["passed"]) == (5, 2)
    assert n2["copy_paired"]["per_100_runs"]["per100"] == 5.0
    assert n2["copy_paired"]["per_100_arrivals"]["per100"] == 40.0
    assert n2["discordant"] == {"both": 1, "real_only": 1, "copy_only": 1}
    assert n2["status"] == "not the champion"  # the champion is generation 14


def test_number2_real_only_when_no_copy_arm(root: Path):
    blocks = wn.list_blocks(root / "referee" / "LAB" / "nightly")
    sel = wn.select_block(blocks, 12)
    n2 = wn.number2(root, sel, {})
    assert n2["status"] == "real only" and "no copy arm" in n2["reason"] and n2["real_all"]["runs"] == 5


# ----------------------------------------------------------------------------------------------------- number 3
def test_honesty_by_act_shares_and_floor_difference(root: Path):
    blocks = wn.list_blocks(root / "referee" / "LAB" / "nightly")
    sel = wn.select_block(blocks, 13)
    h = wn.honesty_by_act(wn.load_real(sel["agent"]["real"]), wn.load_arm(sel["agent"]["copy"]))
    by = {r["act"]: r for r in h["rows"]}
    assert h["pairs"] == 40
    assert by[1]["runs"] == 10 and by[1]["same_act"]["k"] == 8  # two real-Act-1 runs went to Act 2 on the copy
    # real Act 2: ten runs on floor 20 (eight stay in Act 2 on the copy, two fall to Act 1) and four on floor 33 (all stay)
    assert by[2]["runs"] == 14 and by[2]["same_act"]["k"] == 12
    # real Act 3: sixteen runs, every one of them also ends in Act 3 on the copy
    assert by[3]["runs"] == 16 and by[3]["same_act"]["k"] == 16
    assert by["all"]["runs"] == 40 and by["all"]["same_act"]["k"] == 36
    assert by[1]["floor_diff"]["mean"] == pytest.approx((8 * 2 + 2 * 15) / 10)  # +2 on eight seeds, +15 on two
    assert by["all"]["same_act"]["per100"] == pytest.approx(100.0 * by["all"]["same_act"]["k"] / 40, abs=1e-3)


def test_number3_alarm_flags_a_move_over_two_points(root: Path):
    blocks = wn.list_blocks(root / "referee" / "LAB" / "nightly")
    sel = wn.select_block(blocks, 14)
    n3 = wn.number3(root, sel, blocks, wn.champion_of(root))
    assert n3["previous"]["block"] == "2026-11-01" and n3["previous"]["pairs"] == 40
    # previous block: all 40 pairs end in the same act, so Act 1 and Act 2 shares are 100; now Act 1 is 80 and Act 2 85.7
    assert n3["alarm"]["flag"] is True
    assert any("Act 1 same-act share moved" in r for r in n3["alarm"]["reasons"])
    mv1 = next(m for m in n3["alarm"]["moves"] if m["act"] == 1)
    assert mv1["same_act_move_points"] == pytest.approx(-20.0)
    assert mv1["same_act_beyond_noise"] in (True, False)  # reported, not assumed


def test_alarm_quiet_when_the_blocks_agree():
    row = lambda act, k, n, fd: {"act": act, "runs": n, "same_act": wn.rate(k, n), "same_act_se_points": 5.0, "floor_diff": {"mean": fd, "se": 0.5}}  # noqa: E731
    a = {"rows": [row(1, 80, 100, 1.0), row(2, 70, 100, -1.0), row(3, 3, 10, -5.0), row("all", 150, 210, 0.0)]}
    b = {"rows": [row(1, 79, 100, 1.5), row(2, 71, 100, -1.2), row(3, 9, 10, -2.0), row("all", 160, 210, 0.2)]}
    al = wn.alarm(a, b)
    assert al["flag"] is False and al["reasons"] == []  # moves of 1 point and 0.5 floors; Act 3 is never alarmed
    c = {"rows": [row(1, 84, 100, 1.0), row(2, 70, 100, -4.5), row(3, 3, 10, 0.0), row("all", 0, 1, 0.0)]}
    al2 = wn.alarm(c, a)
    assert al2["flag"] and len(al2["reasons"]) == 2  # Act 1 share +4 points, Act 2 floors -3.5


def test_number3_without_an_earlier_block_has_no_alarm(tmp_path: Path):
    root = make_root(tmp_path)
    import shutil
    shutil.rmtree(root / "referee" / "LAB" / "nightly" / "2026-11-01")
    blocks = wn.list_blocks(root / "referee" / "LAB" / "nightly")
    n3 = wn.number3(root, wn.select_block(blocks, 13), blocks, wn.champion_of(root))
    assert n3["previous"] is None and n3["alarm"]["flag"] is False and "no earlier block" in n3["alarm"]["note"]


# ----------------------------------------------------------------------------------------------------- number 4
def test_number4_newest_exam_and_the_champion_mismatch(root: Path):
    champ = wn.champion_of(root)
    n4 = wn.number4(root, champ, NOW)
    assert n4["exam_generation"] == 14 and n4["status"] == "ok"  # the champion is generation 14: its exam is the newest
    assert n4["floors_behind_on_human_won_seeds"]["mean"] == 18.5
    assert n4["floors_behind_on_human_won_seeds"]["lo"] == 17.3 and n4["floors_behind_on_human_won_seeds"]["hi"] == 19.7
    assert (n4["seeds_won_by_some_draw"], n4["seeds_human_won"], n4["draws_won"], n4["draws_played"]) == (1, 200, 1, 400)
    assert n4["age_days"] == 5.2 and n4["folder"] == "referee/seed-exam/2026-11-14-gen14"
    stale = wn.number4(root, {"generation": 15, "dir": "gen15/x"}, NOW)
    assert stale["status"] == "not the champion" and "no exam of generation 15" in stale["reason"]


def test_number4_none(tmp_path: Path):
    n4 = wn.number4(tmp_path, None, NOW)
    assert n4["status"] == wn.NO_DATA


def test_number4_ignores_files_that_are_not_exams(root: Path):
    (root / "referee" / "seed-exam" / "2026-11-30-x").mkdir()
    (root / "referee" / "seed-exam" / "2026-11-30-x" / "summary.json").write_text(json.dumps({"runs": 5}), encoding="utf-8")  # an envproto-style summary
    assert wn.number4(root, None, NOW)["written"] == "2026-11-14T08:00:00Z"


# ----------------------------------------------------------------------------------------------------- number 5
def test_number5_pooled_pairs_and_the_selection_block(root: Path):
    champ = wn.champion_of(root)
    n5 = wn.number5(root, champ, {})
    assert n5["champion"] == "gen14/cand-new" and n5["previous"] == "gen13/cand-old"
    assert set(n5["promotion_judged_blocks"]) == {"E1", "E2"}  # the seed_block column plus the pooled blocks of the rule text
    blocks = {b["block"]: b for b in n5["blocks"]}
    assert blocks["E1"]["fresh"] is False and blocks["E2"]["fresh"] is False and blocks["E3"]["fresh"] is True
    # E3: the champion's floors are 49, 49, 48, 48, 30 and a win on 49: three passes (48 is at the boss, not past it); the previous champion passes once
    e3 = blocks["E3"]
    assert e3["pairs"] == 6 and e3["champion"]["passed"]["k"] == 3 and e3["previous"]["passed"]["k"] == 1
    assert e3["champion"]["wins"]["k"] == 1 and e3["previous"]["wins"]["k"] == 0
    assert e3["champion"]["arrivals"] == 5 and e3["previous"]["arrivals"] == 4
    # pooled over all three blocks: 14 pairs
    assert n5["pooled_all"]["pairs"] == 14 and n5["pooled_fresh"]["pairs"] == 6
    d = n5["pooled_fresh"]["diff_passed_per_100"]
    assert d["n"] == 6 and d["mean"] == pytest.approx(100.0 * (3 - 1) / 6, abs=1e-2)
    assert n5["status"] == "ok"
    # the paired standard error by hand: differences (+1 on two seeds, 0 on four) x 100
    diffs = [100.0, 100.0, 0.0, 0.0, 0.0, 0.0]
    m = sum(diffs) / 6
    se = math.sqrt(sum((x - m) ** 2 for x in diffs) / 5 / 6)
    assert d["se"] == pytest.approx(se, abs=1e-3)


def test_number5_only_the_selection_block_is_not_fresh(tmp_path: Path):
    root = make_root(tmp_path, with_fresh=False)
    n5 = wn.number5(root, wn.champion_of(root), {})
    assert n5["pooled_fresh"] is None and n5["status"].startswith("selection block only")
    assert "best of several candidates" in n5["reason"]
    assert n5["pooled_all"]["pairs"] == 8


def test_number5_no_data_cases(tmp_path: Path):
    assert wn.number5(tmp_path, None, {})["status"] == wn.NO_DATA
    root = make_root(tmp_path)
    (root / "referee" / "agent" / "promotions.tsv").write_text(promotions([]), encoding="utf-8")
    assert "no promotions.tsv row" in wn.number5(root, wn.champion_of(root), {})["reason"]


def test_stop_rule_distance(root: Path):
    n5 = wn.number5(root, wn.champion_of(root), {})
    sr = wn.stop_rule(n5, {"champion_has_real_block": False}, NOW)
    assert sr["basis"] == "fresh pairs" and sr["fresh_pairs"] == 6 and sr["pairs_needed"] == 4000
    assert sr["now_per_100_arrivals"] == pytest.approx(100.0 * 3 / 5)
    assert sr["gap_to_target_points"] == pytest.approx(30.0 - 60.0)
    assert sr["real_block_of_champion"] is False and sr["days_left"] == 13.5  # to the end of 2026-12-02 from 2026-11-19 12:00


# ----------------------------------------------------------------------------------------------------- the report
def test_build_markdown_json_and_privacy(root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out = tmp_path / "out"
    rc = wn.main(["--root", str(root), "--now", "2026-11-19T12:00:00Z", "--out-dir", str(out)])
    assert rc == 0
    printed = capsys.readouterr().out
    md = (out / "weekly-numbers-2026-11-19.md").read_text(encoding="utf-8")
    doc = json.loads((out / "weekly-numbers-2026-11-19.json").read_text(encoding="utf-8"))
    assert printed == md
    for token in ("| 1 |", "| 2 |", "| 3 |", "| 4 |", "| 5 |", "The stop rule"):
        assert token in md
    assert set(doc) >= {"n1", "n2", "n3", "n4", "n5", "stop_rule", "champion", "humans"}
    blob = md + json.dumps(doc)
    assert SEED_PREFIX not in blob and str(tmp_path) not in blob and ":/Users" not in blob and ":\\Users" not in blob
    assert "no data for generation 14" in md  # no real block of the champion: the headline says so, the figure shown is the newest block's


def test_main_on_an_empty_root_prints_no_data_everywhere(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    rc = wn.main(["--root", str(tmp_path), "--now", "2026-11-19T12:00:00Z", "--no-write"])
    assert rc == 0
    text = capsys.readouterr().out
    assert text.count(wn.NO_DATA) >= 5
    assert not (tmp_path / "referee" / "backlog" / "weekly").exists()  # --no-write writes nothing


def test_fill_template_tokens_and_the_leading_comment(root: Path):
    doc = wn.build(root, NOW)
    t = ("<!-- how to fill {{n1.wins.per100:2}} -->\n# wins {{n1.wins.per100:2}} of {{n1.wins.n}}; gen {{n5.champion}}; missing {{n9.x}}; "
         "yes {{n1.champion_has_real_block}}; stop {{stop_rule.days_left}}; first row {{n3.rows.0.runs}}")
    out = wn.fill_template(t, doc)
    assert out == "# wins 2.38 of 42; gen gen14/cand-new; missing no data; yes no; stop 13.5; first row 10"


def test_the_scoreboard_template_resolves_every_token(root: Path):
    """Every {{token}} of docs/paper/SCOREBOARD-TEMPLATE.md names a key the report really has (a renamed key would print 'no data' here)."""
    template = (Path(__file__).resolve().parents[1] / "docs" / "paper" / "SCOREBOARD-TEMPLATE.md").read_text(encoding="utf-8")
    filled = wn.fill_template(template, wn.build(root, NOW))
    assert "{{" not in filled and wn.NO_DATA not in filled
    assert "# Scoreboard, 2026-11-19T12:00:00Z" in filled and "<!--" not in filled
    empty = wn.fill_template(template, wn.build(root.parent / "nowhere", NOW))
    assert empty.count(wn.NO_DATA) >= 20  # an empty lab prints "no data", never a number
