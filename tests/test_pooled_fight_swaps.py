"""The pooled whole-run reading of fight-only swaps (tools/pooled_fight_swaps.py, Act 3 week, lane 26).

Every test builds a small project folder in a temporary directory (agent.json, promotion records, arms' runs.jsonl, the ledger, the gym's
loop.log) and reads it; none reads the real referee folder. The seeds below are made up and must never reach the output."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pooled_fight_swaps as pfs  # noqa: E402

POLICY = "a" * 64
CHAMP_POLICY = "b" * 64
SEEDS = ["SEEDQ1", "SEEDQ2", "SEEDQ3", "SEEDQ4"]


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def write_arm(folder: Path, floors: dict[str, int], **extra) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"seed": s, "floor": f, "win": False, "crash": False, **extra}) for s, f in floors.items()]
    (folder / "runs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def agent_json(name="v4", policy=POLICY, champion="gen20/candidate-chain", swap="fight", ckpt="c0380", when="2026-11-20T19:03:29Z", root: Path | None = None) -> dict:
    return {"generation": 21, "built": {"why": f"the fight loop's player {name} (checkpoint {ckpt}), promoted {when}: queued", "trained": False, "swap": swap,
                                         "prior": {"dir": f"D:/somewhere/players/{name}", "policy_sha256": policy},
                                         "base": {"dir": f"{(root or Path('D:/x')).as_posix()}/referee/agent/{champion}", "policy_sha256": CHAMP_POLICY},
                                         "tag": f"fight-{name}"}}


def record(policy=POLICY, written="2026-11-21T10:00:00Z", decision="rejected", route="", block="E-T1", champion="gen20/candidate-chain", **extra) -> dict:
    r = {"written": written, "seed_block": block, "config": "a3-v1", "paired_seeds": 4, "cand_sha": policy, "decision_text": decision,
         "decision": {"route": route}, "base": {"agent": {"dir": champion}}, "keep_v2": {"rule": "keep-v3-2026-11-18", "boss_reading": "strict-2026-11-19"}}
    r.update(extra)
    return r


# Four pairs. The candidate passes the first Act 3 boss (floor above 48) on seeds 1 and 4, the champion on seed 3: paired differences
# +100, 0, -100, +100 per 100 runs; arrivals (floor 48 or more): 3 and 3 of 4.
CAND_FLOORS = dict(zip(SEEDS, [60, 48, 30, 60], strict=True))
BASE_FLOORS = dict(zip(SEEDS, [48, 48, 60, 30], strict=True))
DIFFS = [100.0, 0.0, -100.0, 100.0]
HAND_DIFF = statistics.fmean(DIFFS)
HAND_SE = statistics.stdev(DIFFS) / math.sqrt(4)


def make_candidate(root: Path, gen: int, name: str, *, champion="gen20/candidate-chain", rec: dict | None = None, extra_files: dict | None = None,
                   cand_floors=None, base_floors=None, arms: bool = True, agent: dict | None = None, **agent_kw) -> Path:
    cand = root / "referee" / "agent" / f"gen{gen}" / f"candidate-fight-{name}"
    write_json(cand / "agent.json", agent if agent is not None else agent_json(name, root=root, champion=champion, **agent_kw))
    if rec is not None:
        write_json(cand / "promotion.json", rec)
    for fname, obj in (extra_files or {}).items():
        write_json(cand / fname, obj)
    if arms:
        write_arm(cand / "arms" / "E-T1-a3-v1", cand_floors or CAND_FLOORS)
        write_arm(root / "referee" / "agent" / champion / "arms" / "E-T1-a3-v1", base_floors or BASE_FLOORS)
    return cand


def margins_block(diff, se, pairs, cand, base, arr_c, arr_b) -> dict:
    return {"z": 2.0, "pairs": pairs, "B3a": {"cand": cand, "base": base, "diff": diff, "se": se, "pm2se": 2 * se}, "arrivals": {"cand": arr_c, "base": arr_b}}


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "referee" / "agent").mkdir(parents=True)
    (tmp_path / "referee" / "gym-loop").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------------------------------- the pool
def test_the_pool_weights_each_figure_by_its_precision():
    p = pfs.precision_pool([(1.0, 1.0), (3.0, 0.5)])
    assert p["estimate"] == pytest.approx((1.0 * 1 + 3.0 * 4) / 5)
    assert p["se"] == pytest.approx(1 / math.sqrt(5))
    assert p["pm2se"] == pytest.approx(2 / math.sqrt(5))
    assert (p["lower"], p["upper"]) == pytest.approx((p["estimate"] - p["pm2se"], p["estimate"] + p["pm2se"]))


def test_a_figure_without_a_usable_se_is_not_pooled():
    p = pfs.precision_pool([(1.0, 1.0), (50.0, 0.0), (9.0, None), (7.0, math.inf)])
    assert p["rows"] == 1 and p["estimate"] == 1.0
    assert pfs.precision_pool([(1.0, 0.0)]) is None
    assert pfs.precision_pool([]) is None


def test_the_review_pooled_figure_follows_from_its_three_rows():
    """-0.4 plus or minus 0.8 is what the three rows read with v4's margin taken as 2 SE = 2.0 (the review's own figures)."""
    p = pfs.precision_pool([(0.5, 1.0), (-0.25, 1.277 / 2), (-0.85, 1.212 / 2)])
    assert round(p["estimate"], 1) == -0.4 and round(p["pm2se"], 1) == 0.8


# ---------------------------------------------------------------------------------------------------- the strict reading of a row
def test_went_past_reads_the_floor_cut_and_the_boss_bar_and_a_win():
    assert pfs.went_past({"floor": 49}, 2) and not pfs.went_past({"floor": 48}, 2)
    assert pfs.went_past({"floor": 50, "win": True}, 2)
    assert not pfs.went_past({"floor": 60, "crash": True}, 2) and not pfs.went_past({"floor": 60, "lost": "x"}, 2)
    lost_fight = {"floor": 60, "boss_damage_acts": [[0, 1.0], [1, 1.0], [2, 0.6]]}
    assert not pfs.went_past(lost_fight, 2) and pfs.went_past(lost_fight, 1)


def test_a_complete_node_string_names_the_boss_floors_and_arrival():
    usual = "M" * 15 + "B" + "M" * 15 + "B" + "M" * 14 + "B"  # bosses on floors 17, 33 and 48
    row = {"floor": len(usual) + 1, "nodes": usual}
    assert pfs.boss_floors(usual) == [17, 33, 48] and pfs.arrived_b3a(row) and not pfs.went_past(row, 2)  # ended at the boss's floor, not past it
    assert pfs.went_past({"floor": len(usual) + 2, "nodes": usual + "M"}, 2)
    long_act2 = "M" * 15 + "B" + "M" * 17 + "B" + "M" * 14 + "B"  # one run in about four hundred: bosses on 17, 35 and 50
    assert pfs.boss_floors(long_act2) == [17, 35, 50]
    on_50 = {"floor": len(long_act2) + 1, "nodes": long_act2}
    assert on_50["floor"] == 50 and pfs.arrived_b3a(on_50) and not pfs.went_past(on_50, 2)  # floor 50 is above the cut 48 and still not past the boss
    assert pfs.went_past({"floor": 51, "nodes": long_act2 + "M"}, 2)
    assert pfs.arrived_b3a({"floor": 48}) and not pfs.arrived_b3a({"floor": 47})


def test_the_paired_figure_matches_a_hand_calculation():
    c = {s: {"seed": s, "floor": f} for s, f in CAND_FLOORS.items()}
    b = {s: {"seed": s, "floor": f} for s, f in BASE_FLOORS.items()}
    fig = pfs.paired_b3a([c], [b])
    assert fig["pairs"] == 4 and (fig["cand"], fig["base"]) == (2, 1)
    assert fig["diff"] == pytest.approx(HAND_DIFF) and fig["se"] == pytest.approx(HAND_SE)
    assert (fig["arrivals_cand"], fig["arrivals_base"]) == (3, 3)
    assert pfs.paired_b3a([{"S": {"seed": "S", "floor": 50}}], [{"S": {"seed": "S", "floor": 10}}]) is None  # one pair has no SE


# ---------------------------------------------------------------------------------------------------- which candidates are read
def test_only_a_marked_fight_only_swap_is_a_row(root: Path):
    make_candidate(root, 21, "v4", rec=record())
    make_candidate(root, 18, "v3", agent={"generation": 18, "macro": "m"}, arms=False)  # no built.swap: left out, and said so
    rep = pfs.build_report(root)
    assert [r["fighter"] for r in rep["rows"]] == ["v4"]
    assert rep["left_out"] == ["gen18/candidate-fight-v3: not marked a fight-only swap in its agent.json"]


def test_rows_are_in_fighter_order_not_folder_order(root: Path):
    for gen, name, ck in ((22, "v7", "c4"), (21, "v5", "c2"), (21, "v4", "c1"), (22, "v6", "c3")):
        make_candidate(root, gen, name, rec=None, arms=False, ckpt=ck)
    assert [r["fighter"] for r in pfs.build_report(root)["rows"]] == ["v4", "v5", "v6", "v7"]


def test_the_champion_is_named_relative_to_the_agent_folder(root: Path):
    make_candidate(root, 21, "v4", rec=record())
    row = pfs.build_report(root)["rows"][0]
    assert row["champion"] == "gen20/candidate-chain" and row["candidate"] == "gen21/candidate-fight-v4"
    assert row["promoted"] == "2026-11-20" and row["judged"] == "2026-11-21"


# ---------------------------------------------------------------------------------------------------- the judgement record
def test_a_record_naming_another_network_is_not_the_candidates_judgement(root: Path):
    cand = make_candidate(root, 22, "v7", rec=None, arms=False)
    write_json(cand / "promotion-rejected-2026-11-21.json", record(policy="c" * 64, decision="rejected"))  # a build copied its parent's file in
    row = pfs.build_report(root)["rows"][0]
    assert row["verdict"] == "pending" and row["whole_run"] is None and row["route"] == "pending"
    assert any("name another candidate's network" in n for n in row["notes"])
    assert any("pending" in n for n in row["notes"])


def test_the_newest_record_of_a_candidate_is_its_judgement(root: Path):
    cand = make_candidate(root, 21, "v5", rec=record(written="2026-11-22T09:00:00Z", decision="promoted", route="S"))
    write_json(cand / "promotion-rejected-2026-11-21.json", record(written="2026-11-21T21:00:00Z", decision="rejected"))
    row = pfs.build_report(root)["rows"][0]
    assert (row["verdict"], row["route"], row["judged"]) == ("promoted", "S", "2026-11-22")
    assert any("superseded" in n for n in row["notes"])


def test_a_refusal_with_no_route_says_none_held(root: Path):
    make_candidate(root, 21, "v4", rec=record())
    assert pfs.build_report(root)["rows"][0]["route"] == "none held"


def test_the_ledger_gives_a_verdict_when_there_is_no_record_and_flags_a_disagreement(root: Path):
    head = "written\tcand_gen\tbase_gen\tseed_block\tseeds\tdecision\tcand_sha\tcand_dir\troute\n"
    (root / "referee" / "agent" / "promotions.tsv").write_text(
        head + f"2026-11-21T10:00:00Z\t21\t20\tE\t4\trejected\t{POLICY}\tcandidate-fight-v4\t\n"
        + f"2026-11-22T10:00:00Z\t21\t20\tE\t4\tpromoted\t{'c' * 64}\tcandidate-fight-v5\tS\n", encoding="utf-8")
    make_candidate(root, 21, "v4", rec=None, arms=False)
    row = pfs.build_report(root)["rows"][0]
    assert row["verdict"] == "rejected" and any("from the ledger" in n for n in row["notes"])
    make_candidate(root, 21, "v4", rec=record(decision="promoted", route="A"))  # the record now says the opposite
    row = pfs.build_report(root)["rows"][0]
    assert row["verdict"] == "promoted" and any("ledger's last row says rejected" in n for n in row["notes"])


# ---------------------------------------------------------------------------------------------------- the whole-run figure
def test_the_records_own_margins_are_used_as_written(root: Path):
    rec = record(keep_v2={"rule": "keep-v3-2026-11-18", "margins": margins_block(-0.25, 0.64, 2000, 130, 135, 478, 462)})
    make_candidate(root, 21, "v5", rec=rec, arms=False)
    w = pfs.build_report(root)["rows"][0]["whole_run"]
    assert w["source"] == "record margins" and w["pairs"] == 2000 and (w["cand"], w["base"]) == (130, 135)
    assert (w["diff"], w["se"], w["pm2se"]) == (-0.25, 0.64, pytest.approx(1.28))
    assert w["cand_per_100"] == pytest.approx(6.5) and w["base_per_100"] == pytest.approx(6.75)
    assert w["arrival_share"] == pytest.approx((478 + 462) / 4000)


def test_a_record_without_margins_is_read_from_the_arms(root: Path):
    make_candidate(root, 21, "v4", rec=record())
    w = pfs.build_report(root)["rows"][0]["whole_run"]
    assert w["source"].startswith("arms re-read") and w["pairs"] == 4 and (w["cand"], w["base"]) == (2, 1)
    assert w["diff"] == pytest.approx(HAND_DIFF) and w["se"] == pytest.approx(HAND_SE) and w["pm2se"] == pytest.approx(2 * HAND_SE)
    assert w["arrival_share"] == pytest.approx(6 / 8)


def test_the_arms_of_every_pooled_block_are_read(root: Path):
    rec = record(pooled={"blocks": [{"block": "E-T1", "role": "judged"}, {"block": "E-T2", "role": "pooled"}]}, paired_seeds=8)
    cand = make_candidate(root, 21, "v4", rec=rec)
    write_arm(cand / "arms" / "E-T2-a3-v1", {f"B{s}": f for s, f in CAND_FLOORS.items()})
    write_arm(root / "referee" / "agent" / "gen20" / "candidate-chain" / "arms" / "E-T2-a3-v1", {f"B{s}": f for s, f in BASE_FLOORS.items()})
    w = pfs.build_report(root)["rows"][0]["whole_run"]
    assert w["pairs"] == 8 and (w["cand"], w["base"]) == (4, 2)
    assert w["se"] == pytest.approx(statistics.stdev(DIFFS * 2) / math.sqrt(8))


def test_recompute_reads_the_arms_even_when_the_record_has_margins(root: Path):
    rec = record(keep_v2={"rule": "keep-v3-2026-11-18", "margins": margins_block(HAND_DIFF, HAND_SE, 4, 2, 1, 3, 3)})
    make_candidate(root, 21, "v5", rec=rec)
    from_record = pfs.build_report(root)["rows"][0]["whole_run"]
    from_arms = pfs.build_report(root, recompute=True)["rows"][0]["whole_run"]
    assert from_record["source"] == "record margins" and from_arms["source"] == "arms re-read"
    for k in ("pairs", "cand", "base", "diff", "se", "arrivals_cand", "arrivals_base"):
        assert from_arms[k] == pytest.approx(from_record[k])


def test_a_record_with_neither_margins_nor_arms_has_no_whole_run_figure(root: Path):
    make_candidate(root, 21, "v4", rec=record(), arms=False)
    row = pfs.build_report(root)["rows"][0]
    assert row["whole_run"] is None and any("unavailable" in n for n in row["notes"])
    assert pfs.pooled([row])["whole_run"] is None


def test_a_record_that_is_not_final_is_shown_and_not_pooled(root: Path):
    """A block stopped early or extended is biased or provisional (the judge's own note): it stays out of the standing pool."""
    rec = record(keep_v2={"rule": "keep-v3-2026-11-18", "final": False, "margins": margins_block(-3.0, 0.5, 1100, 58, 70, 200, 210)})
    make_candidate(root, 21, "v5", rec=rec, arms=False)
    rep = pfs.build_report(root)
    row = rep["rows"][0]
    assert row["provisional"] is True and row["whole_run"]["diff"] == -3.0 and any("not final" in n for n in row["notes"])
    assert rep["pooled"]["whole_run"] is None
    assert "1,100 (provisional)" in pfs.render(rep)


def test_a_record_that_predates_the_strict_reading_says_so(root: Path):
    rec = record()
    rec["keep_v2"] = {"rule": "keep-v2-2026-11-05"}
    make_candidate(root, 18, "v3", rec=rec)
    row = pfs.build_report(root)["rows"][0]
    assert any("predates the strict boss reading" in n for n in row["notes"]) and row["keep_rule"] == "keep-v2-2026-11-05"


# ---------------------------------------------------------------------------------------------------- the gate gain
V5_LINE = ("2026-11-21T18:55:32Z gate c0390: stage 2 (era 0; part h draws 0-7, part a3 draws 0-3) promote by route F: part h 59.2 / 58.1 "
           "(+1.11 points, SE 0.53; HP -0.04) on 4000 games; part a3 23.5 / 22.8 (+0.64 points, SE 0.77; HP -0.60) on 1656 games\n")
V4_LINE = ("2026-11-20T19:03:29Z gate c0380: stage 2 (draws 0-7) promote: cand 65.3 inc 64.0 of 3200 games on 400 starts "
           "(+1.34 points, SE 0.66); 90% lower bound +0.50 points; HP lost a fight -0.52 (SE 0.19)\n")


def test_the_gate_gain_is_read_from_the_promote_line(tmp_path: Path):
    log = tmp_path / "loop.log"
    log.write_text("noise\n2026-11-21T18:31:53Z gate c0390: stage 1 (era 0; part h draws 0-1) continue: part h 58.2 / 56.8 (+1.41 points, SE 1.07; HP -0.20)\n"
                   + V5_LINE + V4_LINE, encoding="utf-8")
    g5 = pfs.gate_gains(log, "c0390")
    assert [(g["part"], g["gain"], g["se"]) for g in g5] == [("h", 1.11, 0.53), ("a3", 0.64, 0.77)]
    assert g5[0]["pm2se"] == pytest.approx(1.06)
    g4 = pfs.gate_gains(log, "c0380")
    assert [(g["part"], g["gain"], g["se"]) for g in g4] == [("h", 1.34, 0.66)]
    assert pfs.gate_gains(log, "c9999") is None and pfs.gate_gains(tmp_path / "none.log", "c0390") is None and pfs.gate_gains(log, None) is None


def test_a_continue_line_is_not_a_promotion(tmp_path: Path):
    log = tmp_path / "loop.log"
    log.write_text("2026-11-24T20:46:33Z gate c0475: stage 2 (era 2; part h draws 32-39) continue: part h 58.4 / 58.7 (-0.35 points, SE 0.46; HP +0.01) on 4000 games; "
                   "route A3: the 97.5% lower bound -0.07 points is not above 0; part a3 gains at least its near bar, so stage 3\n", encoding="utf-8")
    assert pfs.gate_gains(log, "c0475") is None


def test_the_gate_gain_reaches_the_row(root: Path):
    (root / "referee" / "gym-loop" / "loop.log").write_text(V4_LINE, encoding="utf-8")
    make_candidate(root, 21, "v4", rec=record())
    assert pfs.build_report(root)["rows"][0]["gate"][0]["gain"] == 1.34


# ---------------------------------------------------------------------------------------------------- the boss-door exam
def test_s1_is_read_from_s1_json_and_holds_by_the_rule(root: Path):
    cand = make_candidate(root, 21, "v5", rec=record(), arms=False)
    write_json(cand / "s1.json", {"mean": 1.1, "se": 0.4, "starts": 1126, "pairs": 6756, "candidate": POLICY, "complete": True})
    s1 = pfs.build_report(root)["rows"][0]["s1"]
    assert (s1["gain"], s1["se"], s1["starts"]) == (1.1, 0.4, 1126) and s1["pm2se"] == pytest.approx(0.8)
    assert s1["holds"] is True  # at least +1.0 and 1.1 - 2.576 x 0.4 above 0
    write_json(cand / "s1.json", {"mean": 1.19, "se": 0.66, "starts": 464, "candidate": POLICY})
    assert pfs.build_report(root)["rows"][0]["s1"]["holds"] is False  # the 0.005 bound is below 0


def test_s1_falls_back_to_the_record_then_to_the_exams_results(root: Path):
    make_candidate(root, 21, "v5", rec=record(s1={"mean": 0.9, "se": 0.3, "starts": 10, "candidate": POLICY}), arms=False)
    assert pfs.build_report(root)["rows"][0]["s1"]["gain"] == 0.9
    cand = make_candidate(root, 22, "v7", rec=None, arms=False)
    write_json(cand / "s1" / "results.json", {"candidate": {"policy_sha256": POLICY}, "first_boss": {"points": 1.19, "se_points": 0.66, "starts": 464, "pairs": 2784,
                                                                                                      "complete": True, "reads": {"hold": False, "reversal": False}}})
    row = [r for r in pfs.build_report(root)["rows"] if r["fighter"] == "v7"][0]
    assert row["s1"]["gain"] == 1.19 and row["s1"]["holds"] is False and row["verdict"] == "pending"


def test_an_s1_that_names_another_network_or_is_incomplete_is_not_used(root: Path):
    cand = make_candidate(root, 21, "v5", rec=record(), arms=False)
    write_json(cand / "s1.json", {"mean": 1.1, "se": 0.4, "starts": 5, "candidate": "d" * 64})
    row = pfs.build_report(root)["rows"][0]
    assert row["s1"] is None and any("another candidate's network" in n for n in row["notes"])
    write_json(cand / "s1.json", {"mean": 1.1, "se": 0.4, "starts": 5, "candidate": POLICY, "complete": False})
    assert pfs.build_report(root)["rows"][0]["s1"] is None


# ---------------------------------------------------------------------------------------------------- the carryover reference and the pooled report
def two_row_root(root: Path) -> Path:
    r5 = record(policy="e" * 64, keep_v2={"rule": "keep-v3-2026-11-18", "margins": margins_block(-0.25, 0.64, 2000, 130, 135, 478, 462)}, decision="promoted", route="S")
    r6 = record(keep_v2={"rule": "keep-v3-2026-11-18", "margins": margins_block(-0.85, 0.61, 2000, 111, 128, 434, 466)})
    c5 = make_candidate(root, 21, "v5", rec=r5, arms=False, policy="e" * 64)
    write_json(c5 / "s1.json", {"mean": 1.1, "se": 0.4, "starts": 1000, "pairs": 6000, "candidate": "e" * 64})
    make_candidate(root, 22, "v6", rec=r6, arms=False)
    return root


def test_the_row_reference_is_the_door_gain_times_the_arrival_share(root: Path):
    rep = pfs.build_report(two_row_root(root))
    v5, v6 = rep["rows"]
    share = (478 + 462) / 4000
    assert v5["carryover"]["estimate"] == pytest.approx(1.1 * share) and v5["carryover"]["se"] == pytest.approx(0.4 * share)
    assert v5["carryover"]["pm2se"] == pytest.approx(0.8 * share)
    assert v6["carryover"] is None  # no door exam played


def test_the_pooled_report_and_its_summary_line(root: Path):
    rep = pfs.build_report(two_row_root(root))
    w = rep["pooled"]["whole_run"]
    want = pfs.precision_pool([(-0.25, 0.64), (-0.85, 0.61)])
    assert w["estimate"] == pytest.approx(want["estimate"]) and w["se"] == pytest.approx(want["se"]) and w["pairs"] == 4000 and w["fighters"] == ["v5", "v6"]
    assert rep["pooled"]["door"]["estimate"] == pytest.approx(1.1) and rep["pooled"]["door"]["starts"] == 1000
    share = (478 + 462 + 434 + 466) / 8000
    assert rep["pooled"]["full_carryover"]["estimate"] == pytest.approx(1.1 * share)
    assert rep["pooled"]["full_carryover"]["arrival_share"] == pytest.approx(share)
    line = pfs.summary_line(rep)
    assert line.startswith("pooled whole-run effect ") and "2 rows, 4,000 pairs" in line and "against a full-carryover reference of +0.2" in line
    assert "upper bound " in line


def test_the_reading_says_whether_the_upper_bound_excludes_full_carryover(root: Path):
    rep = pfs.build_report(two_row_root(root))
    assert rep["pooled"]["whole_run"]["upper"] > rep["pooled"]["full_carryover"]["estimate"]
    assert rep["pooled"]["reading"].startswith("not excluded")
    assert rep["pooled"]["rows_to_settle"] > 0

    def row(name, diff, se, s1=None):
        return {"fighter": name, "keep_rule": "v3", "s1": s1, "whole_run": {"diff": diff, "se": se, "pairs": 2000, "arrival_share": 0.25}}

    strong = pfs.pooled([row("a", -2.0, 0.3, {"gain": 2.0, "se": 0.5, "starts": 100}), row("b", -2.0, 0.3)])
    assert strong["whole_run"]["upper"] < strong["full_carryover"]["estimate"] and strong["reading"].startswith("excluded")
    assert strong["rows_to_settle"] == 0


def test_the_keep_rule_v3_subset_is_pooled_beside_the_older_rows(root: Path):
    old = record(keep_v2={"rule": "keep-v2-2026-11-05"})
    make_candidate(root, 18, "v3", rec=old)
    two_row_root(root)
    p = pfs.build_report(root)["pooled"]
    assert p["whole_run"]["fighters"] == ["v3", "v5", "v6"] and p["whole_run_keep_v3"]["fighters"] == ["v5", "v6"]


def test_no_rows_is_a_report_not_a_crash(root: Path):
    rep = pfs.build_report(root)
    assert rep["rows"] == [] and rep["pooled"]["whole_run"] is None
    assert "no rows yet" in pfs.summary_line(rep) and "no row with a whole-run figure" in pfs.render(rep)


# ---------------------------------------------------------------------------------------------------- --check
def known_rows(effects=((0.5, 2.0, 4000), (-0.25, 1.277, 2000), (-0.85, 1.212, 2000))) -> dict:
    rows = []
    for name, (eff, pm2, pairs) in zip(("v4", "v5", "v6"), effects, strict=True):
        rows.append({"fighter": name, "whole_run": {"diff": eff, "se": pm2 / 2, "pm2se": pm2, "pairs": pairs, "source": "test"}})
    return {"rows": rows}


def test_check_passes_when_every_figure_rounds_to_the_reviews():
    figures, code = pfs.check(known_rows())
    assert code == 0 and all(f["ok"] for f in figures) and len(figures) == 11


def test_check_allows_the_reviews_rounding_and_no_more():
    ok = known_rows(((0.524, 2.04, 4000), (-0.253, 1.2751, 2000), (-0.8549, 1.2149, 2000)))
    assert pfs.check(ok)[1] == 0
    for bad in (((0.56, 2.0, 4000), (-0.25, 1.277, 2000), (-0.85, 1.212, 2000)),   # v4's effect, 0.06 off at one decimal
                ((0.5, 2.0, 4000), (-0.25, 1.30, 2000), (-0.85, 1.212, 2000)),      # v5's margin, 0.02 off at two decimals
                ((0.5, 2.0, 3999), (-0.25, 1.277, 2000), (-0.85, 1.212, 2000))):    # v4's pairs
        assert pfs.check(known_rows(bad))[1] == 1


def test_check_exits_1_on_the_real_state_of_v4s_margin():
    """v4's own paired margin (plus or minus 0.78 on 4,000 pairs) is not the review's 2.0, and the pooled figure follows it."""
    figures, code = pfs.check(known_rows(((0.525, 0.78, 4000), (-0.25, 1.277, 2000), (-0.85, 1.212, 2000))))
    bad = [f["figure"] for f in figures if f["ok"] is False]
    assert code == 1 and bad == ["v4 plus or minus 2 SE", "pooled effect (v4, v5, v6)", "pooled plus or minus 2 SE"]


def test_check_exits_2_when_a_known_row_is_missing():
    rep = known_rows()
    rep["rows"] = rep["rows"][:2]
    figures, code = pfs.check(rep)
    assert code == 2 and any(f["ok"] is None for f in figures)
    rep["rows"][0]["whole_run"] = None
    assert pfs.check(rep)[1] == 2


def test_the_check_text_explains_a_mismatch_through_the_pooled_figure():
    text, code = pfs.check_text(known_rows(((0.525, 0.78, 4000), (-0.25, 1.277, 2000), (-0.85, 1.212, 2000))))
    assert code == 1 and "MISMATCH" in text and "the review's v4 margin read as 2 SE = 2.0" in text and "-0.39 +/-0.80" in text
    assert text.rstrip().endswith("check: MISMATCH beyond rounding (exit 1)")


# ---------------------------------------------------------------------------------------------------- the command line and what it leaves out
def lab_root(root: Path) -> Path:
    make_candidate(root, 21, "v4", rec=record())
    two_row_root(root)
    (root / "referee" / "gym-loop" / "loop.log").write_text(V4_LINE, encoding="utf-8")
    return root


def test_the_text_and_json_hold_no_seeds_no_block_names_no_paths(root: Path, capsys):
    lab_root(root)
    for argv in ([], ["--json"], ["--check"], ["--recompute"]):
        pfs.main(["--root", str(root), *argv])
        out = capsys.readouterr().out
        assert out.strip()
        for forbidden in (*SEEDS, "E-T1", "a3-v1", str(root), root.as_posix(), "D:/", "C:", "Users", "runs.jsonl", POLICY):
            assert forbidden not in out, (argv, forbidden)


def test_json_is_the_report(root: Path, capsys):
    lab_root(root)
    assert pfs.main(["--root", str(root), "--json"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert [r["fighter"] for r in rep["rows"]] == ["v4", "v5", "v6"]
    assert rep["pooled"]["whole_run"]["pairs"] == 4 + 2000 + 2000
    assert rep["rows"][0]["whole_run"]["source"].startswith("arms re-read")


def test_check_through_the_command_line_sets_the_exit_code(root: Path, capsys):
    lab_root(root)
    assert pfs.main(["--root", str(root), "--check"]) == 1  # v4's four pairs are not the review's 4,000
    assert "MISMATCH" in capsys.readouterr().out
    assert pfs.main(["--root", str(root), "--check", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["exit"] == 1


def test_a_root_without_the_referee_folder_exits_2(tmp_path: Path, capsys):
    assert pfs.main(["--root", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "no referee/agent folder" in err and str(tmp_path) not in err


def test_the_text_table_names_every_row_and_the_pending_one(root: Path, capsys):
    lab_root(root)
    make_candidate(root, 22, "v7", rec=None, arms=False, ckpt="c0475", when="2026-11-24T21:49:57Z")
    pfs.main(["--root", str(root)])
    out = capsys.readouterr().out
    for name in ("v4", "v5", "v6", "v7"):
        assert name in out
    assert "pending" in out and "pooled whole run (" in out and "pooled whole-run effect " in out
