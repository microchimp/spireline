"""tools/morning_report.py: the night block's chance covariate, stage 1 (2026-11-04, brief 4c).

The real arm's floor is corrected by a sum of chance terms read from the game-log copies: the act's variant, each hallway, elite and boss
encounter drawn, valued by a table of the previous generation's runs, minus its expectation under the draws' frequencies over earlier
nights. These tests build the table and the terms by hand on a few runs, check the regression arithmetic against a known fit, and write
small labs (rows plus game-log copies) where the boss alone decides the floor, where nothing does, and where no copy exists.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import morning_report as mr  # noqa: E402

NOW = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)
BOSSES = ["B1_BOSS", "B2_BOSS", "B3_BOSS"]
WEAK = ["W1_WEAK", "W2_WEAK", "W3_WEAK", "W4_WEAK"]
CHANCE_Z = 3.0  # the mean of the correction must sit within this many SE of zero


# ---------------------------------------------------------------------------------------------------- what a draw is
def test_classes_and_events_of_a_run():
    assert [mr.chance_class(e) for e in ("X_BOSS", "X_ELITE", "X_WEAK", "X_NORMAL", "OVERGROWTH_CRAWLERS", "X_EVENT_ENCOUNTER")] == \
        ["boss", "elite", "weak", "normal", "normal", None]
    rooms = ["A_WEAK", "DENSE_EVENT_ENCOUNTER", "B_NORMAL", "C_ELITE", "ONE_BOSS", "D_WEAK", "TWO_BOSS", "E_NORMAL"]
    assert mr.chance_events(rooms) == [(1, "weak", "A_WEAK"), (1, "normal", "B_NORMAL"), (1, "elite", "C_ELITE"), (1, "boss", "ONE_BOSS"),
                                       (2, "weak", "D_WEAK"), (2, "boss", "TWO_BOSS"), (3, "normal", "E_NORMAL")]
    assert [mr.chance_kind(c) for c in ("weak", "normal", "elite", "boss")] == ["hallway", "hallway", "elite", "boss"]
    # the pre-existing classifier is untouched: the unsuffixed pool name is still "other" there
    assert mr.encounter_kind("OVERGROWTH_CRAWLERS") == "other"


# ---------------------------------------------------------------------------------------------------- the table and the terms, by hand
def ev(weak: list[str], boss: str) -> list[tuple[int, str, str]]:
    return [(1, "weak", w) for w in weak] + [(1, "boss", boss)]


VALUE_RUNS = [(ev(["X_WEAK", "Y_WEAK"], "P_BOSS"), 10.0), (ev(["Y_WEAK", "X_WEAK"], "P_BOSS"), 20.0),
              (ev(["X_WEAK", "Z_WEAK"], "Q_BOSS"), 30.0), (ev(["Z_WEAK", "Y_WEAK"], "Q_BOSS"), 40.0),
              (ev(["Y_WEAK", "Z_WEAK"], "P_BOSS"), 50.0)]


def test_table_values_expectations_and_the_small_cell_rule():
    t = mr.build_chance_table(VALUE_RUNS, min_cell=2)
    assert sorted(t["pools"]) == ["1|P_BOSS|boss", "1|P_BOSS|weak"]  # the variant is named by its smallest encounter id
    weak = t["pools"]["1|P_BOSS|weak"]
    # X met in the runs of floors 10 20 30 (mean 20), Y in 10 20 40 50 (30), Z in 30 40 50 (40); the pool mean over its 10 draws is 30
    assert {e: (c["n"], c["mean_floor"], c["value"]) for e, c in weak["cells"].items()} == {
        "X_WEAK": (3, 20.0, 20.0), "Y_WEAK": (4, 30.0, 30.0), "Z_WEAK": (3, 40.0, 40.0)}
    assert weak["mean_floor"] == pytest.approx(30.0) and weak["expect"] == pytest.approx((3 * 20 + 4 * 30 + 3 * 40) / 10)
    boss = t["pools"]["1|P_BOSS|boss"]
    assert boss["cells"]["P_BOSS"]["mean_floor"] == pytest.approx(80 / 3, abs=1e-5) and boss["cells"]["Q_BOSS"]["value"] == pytest.approx(35.0)
    assert boss["expect"] == pytest.approx(30.0)
    # one variant (everything met together): one variant cell, its value the mean of all 5 floors, its term always 0
    assert len(t["variants"]) == 1 and next(iter(t["variants"].values()))["n"] == 5
    assert t["variant_expect"]["1"] == pytest.approx(30.0) and t["runs"] == 5 and t["draws"] == 15
    # a cell under min_cell draws takes the pool mean: with min_cell 4 only Y_WEAK (4 draws) keeps its own mean
    t4 = mr.build_chance_table(VALUE_RUNS, min_cell=4)
    w4 = next(v for k, v in t4["pools"].items() if k.endswith("|weak"))["cells"]
    assert (w4["X_WEAK"]["value"], w4["Y_WEAK"]["value"], w4["Z_WEAK"]["value"]) == (30.0, 30.0, 30.0)
    assert w4["X_WEAK"]["mean_floor"] == 20.0  # the cell's own mean stays on record


def test_terms_are_the_value_minus_the_expectation_over_the_encounters_not_yet_drawn():
    t = mr.build_chance_table(VALUE_RUNS, min_cell=2)
    got = mr.chance_terms(t, ev(["X_WEAK", "Y_WEAK"], "P_BOSS"))
    first = 20.0 - 30.0  # X against the whole weak pool
    second = 30.0 - (4 * 30.0 + 3 * 40.0) / 7  # Y against Y and Z (X is drawn): without replacement
    boss = 80 / 3 - 30.0
    assert got["hallway"] == pytest.approx(first + second, abs=1e-4) and got["boss"] == pytest.approx(boss, abs=1e-4)
    assert got["elite"] == 0.0 and got["variant"] == pytest.approx(0.0, abs=1e-9)
    assert got["total"] == pytest.approx(first + second + boss, abs=1e-4) and (got["draws"], got["unknown"]) == (3, 0)
    # an encounter the table never saw is counted and left out
    odd = mr.chance_terms(t, ev(["NEW_WEAK"], "P_BOSS"))
    assert (odd["draws"], odd["unknown"]) == (2, 1) and odd["hallway"] == 0.0 and odd["boss"] == pytest.approx(boss, abs=1e-4)
    # an act the table never saw: all its draws unknown, no term
    far = mr.chance_terms(t, [(3, "boss", "P_BOSS")])
    assert far["unknown"] == 1 and far["total"] == 0.0


def test_the_odds_come_from_the_odds_runs_and_the_values_from_the_value_runs():
    odds_runs = [(ev(["X_WEAK"], "P_BOSS"), 99.0)] * 6 + [(ev(["Y_WEAK"], "Q_BOSS"), 99.0)] * 2  # X in 6 draws, Y in 2, no Z
    t = mr.build_chance_table(VALUE_RUNS, min_cell=2, odds_runs=odds_runs)
    weak = next(v for k, v in t["pools"].items() if k.endswith("|weak"))
    assert weak["cells"]["X_WEAK"]["value"] == 20.0 and weak["cells"]["X_WEAK"]["odds_n"] == 6 and weak["cells"]["Z_WEAK"]["odds_n"] == 0
    assert weak["expect"] == pytest.approx((6 * 20.0 + 2 * 30.0) / 8)  # the first draw's expectation, at the odds
    first = mr.chance_terms(t, [(1, "weak", "X_WEAK")])
    assert first["hallway"] == pytest.approx(20.0 - (6 * 20.0 + 2 * 30.0) / 8, abs=1e-4)
    z = mr.chance_terms(t, [(1, "weak", "Z_WEAK")])  # Z has a value but no odds: a known draw, against the encounters the odds do hold
    assert z["unknown"] == 0 and z["hallway"] == pytest.approx(40.0 - (6 * 20.0 + 2 * 30.0) / 8, abs=1e-4)
    assert t["odds_runs"] == 8 and t["runs"] == 5


def test_two_variants_are_found_from_the_runs_and_each_is_valued():
    runs = []
    for i in range(30):
        runs.append(([(1, "weak", "A_WEAK"), (1, "boss", "A_BOSS")], 10.0 + i % 2))
        runs.append(([(1, "weak", "B_WEAK"), (1, "boss", "B_BOSS")], 30.0 + i % 2))
    t = mr.build_chance_table(runs)
    assert sorted(t["variants"]) == ["1|A_BOSS", "1|B_BOSS"] and t["variant_of"]["1|A_WEAK"] == "A_BOSS" == t["variant_of"]["1|A_BOSS"]
    assert t["variants"]["1|A_BOSS"]["members"] == ["A_BOSS", "A_WEAK"]
    assert t["variants"]["1|A_BOSS"]["value"] == pytest.approx(10.5) and t["variants"]["1|B_BOSS"]["value"] == pytest.approx(30.5)
    assert t["variant_expect"]["1"] == pytest.approx(20.5)
    a = mr.chance_terms(t, [(1, "weak", "A_WEAK"), (1, "boss", "A_BOSS")])
    assert a["variant"] == pytest.approx(10.5 - 20.5) and a["hallway"] == pytest.approx(0.0, abs=1e-9) and a["boss"] == pytest.approx(0.0, abs=1e-9)
    # a pool of one encounter has nothing to be lucky about: weak and boss terms are 0, the variant carries the whole difference
    assert mr.chance_terms(t, [(1, "weak", "B_WEAK")])["variant"] == pytest.approx(10.0)


# ---------------------------------------------------------------------------------------------------- the regression arithmetic
X = [-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]
E = [1.0, -2.0, 1.0, 1.0, -2.0, 1.0]
Y = [10.0 + 2.0 * x + e for x, e in zip(X, E)]
SXX, SEE = 70.0, 12.0
SYY = 4.0 * SXX + SEE
RHO = 2.0 * SXX / math.sqrt(SXX * SYY)


def test_adjustment_recovers_a_known_fit_with_the_covariate_mean_known():
    a = mr.chance_adjustment(Y, X, {"k": X})
    assert a["beta"] == pytest.approx(2.0) and a["rho"] == pytest.approx(RHO) and a["share_left"] == pytest.approx(1 - RHO**2)
    assert a["mean_raw"] == pytest.approx(10.0) and a["mean_corrected"] == pytest.approx(10.0) and a["mean_correction"] == pytest.approx(0.0)
    assert a["raw_se"] == pytest.approx(math.sqrt(SYY / 5 / 6)) and a["se_corrected"] == pytest.approx(math.sqrt(SEE / 4 / 6))
    d = [b - x for x, b in zip(X, Y)]
    assert a["mean_aivat"] == pytest.approx(10.0) and a["se_aivat"] == pytest.approx(statistics.stdev(d) / math.sqrt(6))
    assert a["share_left_by_kind"]["k"] == pytest.approx(1 - RHO**2) and a["z_correction"] == pytest.approx(0.0)
    assert a["se_corrected"] < a["raw_se"]


def test_adjustment_with_estimated_odds_adds_their_sampling_error_and_moves_the_mean_by_beta_times_the_offset():
    shifted = [x + 1.5 for x in X]  # the corrections average 1.5 instead of 0: the odds were off by that much
    a = mr.chance_adjustment(Y, shifted, odds_runs=24)
    assert a["mean_correction"] == pytest.approx(1.5) and a["mean_corrected"] == pytest.approx(10.0 - 2.0 * 1.5)
    var_c = SXX / 5
    assert a["se_correction"] == pytest.approx(math.sqrt(var_c * (1 / 6 + 1 / 24)))
    assert a["z_correction"] == pytest.approx(1.5 / a["se_correction"])
    assert a["se_corrected"] == pytest.approx(math.sqrt(SEE / 4 / 6 + 4.0 * var_c / 24))
    exact = mr.chance_adjustment(Y, shifted)
    assert exact["se_corrected"] == pytest.approx(math.sqrt(SEE / 4 / 6)) and exact["se_corrected"] < a["se_corrected"]


def test_adjustment_degenerate_inputs():
    flat = mr.chance_adjustment([1.0, 2.0, 4.0, 5.0], [0.0, 0.0, 0.0, 0.0])
    assert flat["beta"] is None and flat["mean_corrected"] == pytest.approx(3.0) and flat["se_corrected"] == flat["raw_se"] and flat["share_left"] == 1.0
    assert mr.chance_adjustment([1.0, 2.0], [0.0, 1.0])["mean_corrected"] is None
    assert mr.chance_adjustment([], [])["n"] == 0
    const_y = mr.chance_adjustment([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
    assert const_y["beta"] == 0.0 and const_y["rho"] is None and const_y["mean_corrected"] == pytest.approx(5.0)


def test_power_follows_the_share_of_variance_left():
    p = mr.chance_power(8.0, 0.75)
    assert p["one_floor"]["raw"] == mr.runs_to_see(8.0, 1.0) and p["one_floor"]["corrected"] == mr.runs_to_see(8.0, 1.0, 0.75)
    assert p["half_floor"]["corrected"] < p["half_floor"]["raw"] and mr.chance_power(8.0, None)["one_floor"]["corrected"] is None


# ---------------------------------------------------------------------------------------------------- unbiased, and tighter
def draw_run(rng: random.Random, effect: dict[str, float], noise: float = 6.0) -> tuple[list[tuple[int, str, str]], float]:
    boss = rng.choice(BOSSES)
    weak = rng.sample(WEAK, 3)
    return ev(weak, boss), 20.0 + effect[boss] + rng.gauss(0.0, noise)


def test_the_corrected_mean_is_unbiased_and_tighter_over_repeated_nights():
    rng = random.Random(8)
    effect = {"B1_BOSS": -6.0, "B2_BOSS": 0.0, "B3_BOSS": 6.0}
    earlier = [draw_run(rng, effect) for _ in range(20000)]
    table = mr.build_chance_table(earlier)
    raws, cors, means_c, ses = [], [], [], []
    for _ in range(300):
        night = [draw_run(rng, effect) for _ in range(200)]
        y = [f for _e, f in night]
        c = [mr.chance_terms(table, e)["total"] for e, _f in night]
        a = mr.chance_adjustment(y, c, odds_runs=len(earlier))
        raws.append(a["mean_raw"])
        cors.append(a["mean_corrected"])
        means_c.append(a["mean_correction"])
        ses.append(a["se_corrected"])
    assert statistics.fmean(cors) == pytest.approx(20.0, abs=0.12)  # the true mean floor is 20
    assert statistics.fmean(means_c) == pytest.approx(0.0, abs=0.12)  # the correction has mean zero
    assert statistics.stdev(cors) < 0.92 * statistics.stdev(raws)  # the boss explains 24 of the 60 variance: SD ratio about 0.77
    assert statistics.fmean(ses) == pytest.approx(statistics.stdev(cors), rel=0.15)  # and the SE the formula gives is the spread seen


# ---------------------------------------------------------------------------------------------------- labs: rows plus game-log copies
def write_log(logs_root: Path, date: str, rooms: dict[str, list[str]]) -> None:
    d = logs_root / f"w5-night-{date.replace('-', '')}-stdout"
    d.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for seed, encs in rooms.items():
        lines.append("[referee] run decision 0 start ")
        for i, e in enumerate(encs):
            lines += [f"[INFO] Creating NCombatRoom with mode=ActiveCombat encounter={e}.", f"[referee] run decision {i + 1} combat x"]
        lines.append(f"[referee] run {seed} ended: death after 10 decisions, floor 5")
    (d / "p00r0.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_real_night(lab: Path, date: str, agent: str, floors: dict[str, int]) -> Path:
    night = lab / "nightly" / date
    arm = night / agent
    arm.mkdir(parents=True)
    rows = [{"ev": "end", "w": 0, "seed": s, "character": "IRONCLAD", "end": "death", "floor": f, "asked": 10, "boss_damage_acts": [],
             "stats": {"decisions": 10, "diverged": 0, "reanchors": 0, "reanchor_failed": 0}} for s, f in floors.items()]
    (arm / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (arm / "summary.json").write_text("{}", encoding="utf-8")
    return night


def world(root: Path, plan: list[tuple[str, str, int]], floor_of, seed: int = 4, logs: bool = True) -> tuple[Path, Path]:
    """root/referee/LAB and root/logs; plan = [(date, agent, runs)]; floor_of(boss, rng) -> floor. Returns (lab, logs_root)."""
    rng = random.Random(seed)
    lab, logs_root = root / "referee" / "LAB", root / "logs"
    for date, agent, n in plan:
        rooms, floors = {}, {}
        for i in range(n):
            boss = rng.choice(BOSSES)
            sd = f"S{date[5:].replace('-', '')}{i:05d}"
            rooms[sd] = rng.sample(WEAK, 3) + [boss]
            floors[sd] = floor_of(boss, rng)
        write_real_night(lab, date, agent, floors)
        if logs:
            write_log(logs_root, date, rooms)
    return lab, logs_root


def test_when_the_boss_alone_decides_the_floor_the_corrected_se_is_near_zero(tmp_path):
    """Floors 17, 22, 30 by boss and nothing else. Tonight 60 runs; the previous generation (10,000 runs) values the bosses and gives
    their odds. The corrected mean is the table's expectation, its SE only the odds' sampling error: under a tenth of the raw SE."""
    exact = {"B1_BOSS": 17, "B2_BOSS": 22, "B3_BOSS": 30}
    lab, logs_root = world(tmp_path, [("2026-11-01", "g5", 10000), ("2026-11-02", "g7", 60)], lambda b, rng: exact[b])
    night = lab / "nightly" / "2026-11-02"
    rep = mr.build_report(night, None, lab, logs_root / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs_root)
    cc = rep["chance_covariate"]
    assert cc["available"] and cc["status"] == "measured" and cc["table_nights"] == ["2026-11-01"] and cc["table_generation"] == 5
    assert (cc["runs_used"], cc["ended_runs"], cc["coverage"], cc["unknown_draws"]) == (60, 60, 1.0, 0)
    assert cc["raw_se"] > 0.4 and cc["share_left"] < 1e-6 and cc["rho"] == pytest.approx(1.0, abs=1e-6)
    assert cc["corrected_se"] < 0.1 * cc["raw_se"]
    assert cc["by_kind"]["boss"]["share_left_alone"] < 1e-6 and cc["by_kind"]["hallway"]["share_left_alone"] > 0.9
    assert cc["odds_check"]["within_3_se"] and abs(cc["odds_check"]["z"]) < CHANCE_Z
    # the corrected mean is the expectation of the floor over the bosses' odds: near their average, 23 (SE 5.4 / sqrt(10,000) from the odds)
    assert cc["corrected_mean"] == pytest.approx(23.0, abs=0.25)
    # exactly known odds (an infinite odds sample) leave only the hallway terms' tiny noise: the corrected SE stays under 2 in 100 of the raw SE
    y = [float(r["floor"]) for r in mr.read_jsonl(night / "g7" / "runs.jsonl")]
    enc = mr.encounters_by_seed(mr.parse_logs(logs_root / "w5-night-20261102-stdout")[0])
    table = cc["table"]
    c = [mr.chance_terms(table, mr.chance_events(enc[r["seed"]]))["total"] for r in mr.read_jsonl(night / "g7" / "runs.jsonl")]
    assert mr.chance_adjustment(y, c)["se_corrected"] < 0.01 < 0.02 * cc["raw_se"]


def test_when_nothing_in_the_draws_matters_the_correction_changes_nothing(tmp_path):
    lab, logs_root = world(tmp_path, [("2026-11-01", "g5", 3000), ("2026-11-02", "g7", 1500)], lambda b, rng: max(1, round(rng.gauss(20, 6))), seed=2)
    rep = mr.build_report(lab / "nightly" / "2026-11-02", None, lab, logs_root / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs_root)
    cc = rep["chance_covariate"]
    assert cc["available"] and cc["share_left"] > 0.98 and 0.98 < cc["se_ratio"] < 1.02
    assert abs(cc["odds_check"]["z"]) < CHANCE_Z and cc["corrected_mean"] == pytest.approx(cc["raw_mean"], abs=0.3)
    text = mr.edition_figures(rep)
    assert "chance covariate, stage 1" in text and "1 - rho^2 = " in text and "the correction averages" in text


def test_a_night_with_no_game_logs_reads_not_measured(tmp_path):
    lab, logs_root = world(tmp_path, [("2026-11-01", "g5", 50), ("2026-11-02", "g7", 50)], lambda b, rng: 10, logs=False)
    night = lab / "nightly" / "2026-11-02"
    rep = mr.build_report(night, None, lab, None, "none", None, NOW, logs_root=logs_root)
    cc = rep["chance_covariate"]
    assert cc["available"] is False and cc["status"].startswith("not measured: no copy of this night's game logs")
    assert "not measured: no copy of this night's game logs" in mr.edition_figures(rep)
    # the same without any logs root at all (how the older callers and the fixture tests call it)
    assert mr.build_report(night, None, lab, None, "none", None, NOW)["chance_covariate"]["available"] is False


def test_a_night_with_logs_but_no_earlier_generation_with_logs_reads_not_measured(tmp_path):
    lab, logs_root = world(tmp_path, [("2026-11-01", "g7", 80), ("2026-11-02", "g7", 80)], lambda b, rng: 10 + rng.randrange(5))
    rep = mr.build_report(lab / "nightly" / "2026-11-02", None, lab, logs_root / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs_root)
    cc = rep["chance_covariate"]
    assert cc["available"] is False and "no earlier generation" in cc["status"] and cc["status"].startswith("not measured")
    # an earlier generation exists but kept no copy
    lab2, logs2 = world(tmp_path / "b", [("2026-11-01", "g5", 80), ("2026-11-02", "g7", 80)], lambda b, rng: 10 + rng.randrange(5))
    (logs2 / "w5-night-20261101-stdout" / "p00r0.log").unlink()
    rep2 = mr.build_report(lab2 / "nightly" / "2026-11-02", None, lab2, logs2 / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs2)
    assert rep2["chance_covariate"]["available"] is False and "no night with a game-log copy" in rep2["chance_covariate"]["status"]


def test_the_table_rule_values_from_the_previous_generation_and_takes_the_odds_from_every_earlier_night(tmp_path):
    plan = [("2026-11-01", "g3", 20), ("2026-11-02", "g5", 20), ("2026-11-03", "g5", 20), ("2026-11-04", "g7", 20), ("2026-11-05", "g7", 20)]
    lab, logs_root = world(tmp_path, plan, lambda b, rng: 10)
    entries = {d: mr.load_arm_pair(lab / "nightly" / d, a) for d, a, _n in plan}
    cur = entries["2026-11-05"]
    others = [h for d, h in entries.items() if d != "2026-11-05"]
    value, odds, how = mr.chance_table_nights(cur, others, logs_root)
    assert [h["date"] for h in value] == ["2026-11-02", "2026-11-03"] and [h["date"] for h in odds] == ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"]
    assert "previous generation (g5)" in how
    v2, o2, how2 = mr.chance_table_nights(entries["2026-11-02"], [h for d, h in entries.items() if d != "2026-11-02"], logs_root)
    assert [h["date"] for h in v2] == ["2026-11-01"] and [h["date"] for h in o2] == ["2026-11-01"]
    v1, o1, how1 = mr.chance_table_nights(entries["2026-11-01"], [h for d, h in entries.items() if d != "2026-11-01"], logs_root)
    assert v1 == [] and o1 == [] and how1 == "no earlier generation"
    # the sensitivity reading uses every other night, later ones too
    vs, os_, hows = mr.chance_table_nights(cur, others, logs_root, "other_nights")
    assert len(vs) == 4 and vs == os_ and "sensitivity" in hows
    # a missing copy drops the night from both lists
    (logs_root / "w5-night-20261103-stdout" / "p00r0.log").unlink()
    value, odds, _ = mr.chance_table_nights(cur, others, logs_root)
    assert [h["date"] for h in value] == ["2026-11-02"] and "2026-11-03" not in [h["date"] for h in odds]


def test_the_reading_over_a_folder_of_nights(tmp_path, capsys):
    exact = {"B1_BOSS": 15, "B2_BOSS": 20, "B3_BOSS": 28}
    plan = [("2026-11-01", "g5", 300), ("2026-11-02", "g7", 300), ("2026-11-03", "g7", 300)]
    lab, logs_root = world(tmp_path / "root", plan, lambda b, rng: exact[b] + rng.randrange(3))
    reading = mr.chance_reading(lab / "nightly", logs_root)
    rows = reading["by_rule"]["previous_generation"]["nights"]
    assert [r["available"] for r in rows] == [False, True, True] and rows[1]["table_nights"] == ["2026-11-01"]
    assert rows[1]["share_left"] < 0.1 and reading["by_rule"]["previous_generation"]["pooled"]["nights"] == 2
    other = reading["by_rule"]["other_nights"]["nights"]
    assert all(r["available"] for r in other) and all(r["share_left"] < 0.1 for r in other)
    md = mr.chance_reading_md(reading)
    assert "corrected SE / raw SE" in md and "Pooled over 2 nights" in md and "not measured: no table can be fixed" in md
    out = tmp_path / "out"
    assert mr.main([str(lab / "nightly" / "2026-11-03"), "--chance-read", "--out", str(out)]) == 0
    data = json.loads((out / "chance_reading.json").read_text(encoding="utf-8"))
    assert (out / "chance_reading.md").is_file() and "table" not in data["by_rule"]["previous_generation"]["nights"][1]
    blob = (out / "chance_reading.md").read_text(encoding="utf-8") + (out / "chance_reading.json").read_text(encoding="utf-8")
    for bad in (str(tmp_path), str(tmp_path).replace("\\", "/"), "Users", "C:\\"):
        assert bad not in blob, bad


def test_cli_writes_the_table_beside_the_report_and_no_paths(tmp_path, capsys):
    exact = {"B1_BOSS": 15, "B2_BOSS": 20, "B3_BOSS": 28}
    lab, logs_root = world(tmp_path / "root", [("2026-11-01", "g5", 400), ("2026-11-02", "g7", 200)], lambda b, rng: exact[b] + rng.randrange(4))
    out = tmp_path / "rep"
    assert mr.main([str(lab / "nightly" / "2026-11-02"), "--winlog", "none", "--now", "2026-11-04T01:00:00Z", "--out", str(out)]) == 0
    table = json.loads((out / "chance_table.json").read_text(encoding="utf-8"))
    rep = json.loads((out / "morning_report.json").read_text(encoding="utf-8"))
    assert table == rep["chance_covariate"]["table"] and table["runs"] == 400 and set(table) >= {"pools", "variants", "variant_of", "min_cell"}
    blob = "".join((out / n).read_text(encoding="utf-8") for n in ("morning_report.json", "handoff_line.md", "edition_figures.md", "chance_table.json"))
    for bad in (str(tmp_path), str(tmp_path).replace("\\", "/"), "Users", "C:\\"):
        assert bad not in blob, bad
    # a night without a copy writes no table
    out2 = tmp_path / "rep2"
    lab2, _ = world(tmp_path / "root2", [("2026-11-01", "g5", 40), ("2026-11-02", "g7", 40)], lambda b, rng: 10, logs=False)
    assert mr.main([str(lab2 / "nightly" / "2026-11-02"), "--winlog", "none", "--now", "2026-11-04T01:00:00Z", "--out", str(out2)]) == 0
    assert not (out2 / "chance_table.json").exists()


# ---------------------------------------------------------------------------------------------------- the older figures do not move
def test_every_older_figure_of_the_report_is_what_it_was_with_or_without_the_logs(tmp_path):
    exact = {"B1_BOSS": 15, "B2_BOSS": 20, "B3_BOSS": 28}
    lab, logs_root = world(tmp_path, [("2026-11-01", "g5", 300), ("2026-11-02", "g7", 300)], lambda b, rng: exact[b] + rng.randrange(4))
    night = lab / "nightly" / "2026-11-02"
    bare = mr.build_report(night, None, lab, None, "none", None, NOW)
    full = mr.build_report(night, None, lab, logs_root / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs_root)
    assert full["chance_covariate"]["available"] and not bare["chance_covariate"]["available"]
    for key in ("real", "emu", "paired", "control_variate", "progress", "comparison", "runs", "crashes", "history"):
        assert full[key] == bare[key], key
    assert set(full) == set(bare) and "chance_covariate" in bare


# ---------------------------------------------------------------------------------------------------- --check covers the new figures
def test_check_lists_the_chance_figures_with_a_match_and_catches_a_wrong_one(tmp_path, monkeypatch):
    exact = {"B1_BOSS": 15, "B2_BOSS": 20, "B3_BOSS": 28}
    lab, logs_root = world(tmp_path / "root", [("2026-11-01", "g5", 400), ("2026-11-02", "g7", 300)], lambda b, rng: exact[b] + rng.randrange(6))
    night = lab / "nightly" / "2026-11-02"
    text, code = mr.run_check(night, None, lab, NOW)
    assert code == 0 and "0 mismatches" in text, text
    for name in mr.CHANCE_NAMES.values():
        assert name in text, name
    # the first path's and the second path's figures are equal as the check compares them
    rep = mr.build_report(night, None, lab, logs_root / "w5-night-20261102-stdout", "none", None, NOW, logs_root=logs_root)
    first, second = mr._chance_figures_first(rep), mr._chance_second_path(night, "g7", logs_root)
    assert set(first) == set(second) == set(mr.CHANCE_NAMES.values())
    assert all(mr._same(first[k], second[k]) for k in first), [(k, first[k], second[k]) for k in first if not mr._same(first[k], second[k])]
    real = mr._chance_second_path

    def bad(night_, agent, root):
        out = real(night_, agent, root)
        out[mr.CHANCE_NAMES["corrected_se"]] *= 1.1
        out[mr.CHANCE_NAMES["unknown_draws"]] += 1
        return out

    monkeypatch.setattr(mr, "_chance_second_path", bad)
    text, code = mr.run_check(night, None, lab, NOW)
    assert code == 1 and "2 mismatches" in text and "chance covariate: SE of the corrected mean floor" in text
    monkeypatch.setattr(mr, "_chance_second_path", real)
    # a night with no copy adds no chance rows to either path and still checks clean
    lab2, _ = world(tmp_path / "root2", [("2026-11-01", "g5", 40), ("2026-11-02", "g7", 40)], lambda b, rng: 10 + rng.randrange(5), logs=False)
    text2, code2 = mr.run_check(lab2 / "nightly" / "2026-11-02", None, lab2, NOW)
    assert code2 == 0 and "chance covariate" not in text2


def test_second_path_reads_the_logs_by_itself(tmp_path):
    write_log(tmp_path, "2026-11-02", {"S1": ["A_WEAK", "X_EVENT_ENCOUNTER", "A_BOSS"], "S2": ["B_NORMAL"]})
    rooms = mr._read_draws_second(tmp_path / "w5-night-20261102-stdout")
    assert rooms == {"S1": ["A_WEAK", "X_EVENT_ENCOUNTER", "A_BOSS"], "S2": ["B_NORMAL"]}
    assert mr._draws_second(rooms["S1"]) == [(1, "weak", "A_WEAK"), (1, "boss", "A_BOSS")]
    assert mr.encounters_by_seed(mr.parse_logs(tmp_path / "w5-night-20261102-stdout")[0]) == rooms
