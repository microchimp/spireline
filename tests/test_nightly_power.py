"""tools/morning_report.py: the nightly exam's power (2026-11-04): the copy arm as a control variate for the real arm's mean floor,
the progress score with its SEs and z, and the --check second path over both.

The arithmetic tests use small synthetic pairs whose slope, correlation and residuals are known by construction; the night tests
use the morning-report fixture (tests/fixtures/morning_report) and small labs written here.
"""

from __future__ import annotations

import json
import math
import random
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import morning_report as mr  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "morning_report"
LAB = FIX / "root" / "referee" / "LAB"
NIGHT = LAB / "nightly" / "2026-11-04"
NOW = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)

# Pairs with a known fit: x centred on 0, y = 10 + 2 x + e, and e orthogonal to both 1 and x (sum e = 0, sum x e = 0), so the least
# squares slope is exactly 2 and the residuals are exactly e.
X = [-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]
E = [1.0, -2.0, 1.0, 1.0, -2.0, 1.0]
Y = [10.0 + 2.0 * x + e for x, e in zip(X, E)]
SXX, SEE = 70.0, 12.0  # sums of squares of x (about its mean 0) and of e
SYY = 4.0 * SXX + SEE  # 292
RHO = 2.0 * SXX / math.sqrt(SXX * SYY)


@pytest.fixture(scope="module")
def rep() -> dict:
    return mr.build_report(NIGHT, None, LAB, None, "none", None, NOW)


# ---------------------------------------------------------------------------------------------------- the arithmetic
def test_control_variate_known_slope_and_correlation_with_no_extra_copy_runs():
    cv = mr.control_variate(Y, X, X)
    assert cv["beta"] == pytest.approx(2.0) and cv["rho"] == pytest.approx(RHO) and cv["saving"] == pytest.approx(1 - RHO**2)
    assert (cv["pairs"], cv["copy_runs"], cv["extra_copy_runs"]) == (6, 6, 0)
    # the copy mean of the pairs is the copy mean of all: no correction, the raw mean (10)
    assert cv["real_mean_paired"] == pytest.approx(10.0) and cv["mean_cv"] == pytest.approx(10.0)
    raw_se = math.sqrt(SYY / 5 / 6)
    assert cv["raw_se"] == pytest.approx(raw_se)
    s2_res = SEE / 4  # residual variance, n - 2 degrees of freedom
    assert cv["se_cv_known_copy_mean"] == pytest.approx(math.sqrt(s2_res / 6))
    assert cv["se_cv"] == pytest.approx(math.sqrt(s2_res / 6 + 4.0 * (SXX / 5) / 6))  # no gain: about the raw SE
    assert cv["se_cv"] == pytest.approx(raw_se, rel=0.01)
    assert cv["variance_factor"] == pytest.approx(1.0)  # (1 - rho^2) + rho^2 * n / N with N = n


def test_control_variate_with_extra_copy_runs_moves_the_mean_by_beta_times_the_copy_gap():
    extra = [4.0, 8.0]  # copy runs on seeds the real arm did not end
    x_all = X + extra
    cv = mr.control_variate(Y, X, x_all)
    assert (cv["pairs"], cv["copy_runs"], cv["extra_copy_runs"]) == (6, 8, 2)
    assert cv["copy_mean_paired"] == pytest.approx(0.0) and cv["copy_mean_all"] == pytest.approx(1.5)
    assert cv["mean_cv"] == pytest.approx(10.0 - 2.0 * (0.0 - 1.5))  # 13: the real mean follows the copy mean up
    var_all = statistics.variance(x_all)
    assert cv["se_cv"] == pytest.approx(math.sqrt(SEE / 4 / 6 + 4.0 * var_all / 8))
    assert cv["variance_factor"] == pytest.approx((1 - RHO**2) + RHO**2 * 6 / 8)


def test_control_variate_degenerate_inputs():
    flat = mr.control_variate([1.0, 2.0, 4.0, 5.0], [3.0, 3.0, 3.0, 3.0], [3.0, 3.0, 3.0, 3.0, 3.0])
    assert flat["beta"] is None and flat["rho"] is None and flat["mean_cv"] == pytest.approx(3.0) and flat["se_cv"] == flat["raw_se"]
    two = mr.control_variate([1.0, 2.0], [1.0, 2.0], [1.0, 2.0])
    assert two["pairs"] == 2 and two["mean_cv"] is None and two["rho"] is None and two["extra_copy_runs"] == 0
    assert mr.control_variate([], [], [])["pairs"] == 0
    const_y = mr.control_variate([5.0, 5.0, 5.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert const_y["beta"] == 0.0 and const_y["rho"] is None and const_y["mean_cv"] == pytest.approx(5.0)


def draw_pairs(rng: random.Random, n: int, extra: int, mu_x: float = 20.0, sd_x: float = 5.0, slope: float = 0.8, sd_e: float = 4.0):
    xs = [rng.gauss(mu_x, sd_x) for _ in range(n + extra)]
    ys = [3.0 + slope * x + rng.gauss(0.0, sd_e) for x in xs[:n]]
    return ys, xs[:n], xs


def test_control_variate_recovers_slope_and_rho_on_a_large_sample():
    ys, xs, _ = draw_pairs(random.Random(11), 6000, 0)
    cv = mr.control_variate(ys, xs, xs)
    true_rho = 0.8 * 5.0 / math.sqrt(0.64 * 25.0 + 16.0)  # 0.7071
    assert cv["beta"] == pytest.approx(0.8, abs=0.03) and cv["rho"] == pytest.approx(true_rho, abs=0.02)
    assert cv["saving"] == pytest.approx(1 - true_rho**2, abs=0.03)


def test_control_variate_se_matches_the_spread_of_the_estimate_over_repeated_draws():
    """n = 100 pairs and 300 extra copy runs, 400 repeats: the estimate's SD is the SE the formula gives, and below the raw SD."""
    rng = random.Random(5)
    thetas, raws, ses = [], [], []
    for _ in range(400):
        ys, xs, x_all = draw_pairs(rng, 100, 300)
        cv = mr.control_variate(ys, xs, x_all)
        thetas.append(cv["mean_cv"])
        raws.append(cv["real_mean_paired"])
        ses.append(cv["se_cv"])
    true_se = math.sqrt(16.0 / 100 + 0.64 * 25.0 / 400)  # sqrt(0.20)
    raw_true = math.sqrt((0.64 * 25.0 + 16.0) / 100)  # sqrt(0.32)
    assert statistics.fmean(thetas) == pytest.approx(3.0 + 0.8 * 20.0, abs=0.08)  # unbiased for the real mean (19)
    assert statistics.stdev(thetas) == pytest.approx(true_se, rel=0.12)
    assert statistics.fmean(ses) == pytest.approx(true_se, rel=0.06)
    assert statistics.stdev(raws) == pytest.approx(raw_true, rel=0.12)
    assert statistics.stdev(thetas) < statistics.stdev(raws)


def test_runs_to_see_a_change():
    z = 1.959964 + 0.841621
    assert mr.runs_to_see(8.0, 1.0) == math.ceil(2 * (z * 8.0) ** 2) == 1005
    assert mr.runs_to_see(8.0, 0.5) == 4019 and mr.runs_to_see(8.0, 1.0, nights=1) == 503
    assert mr.runs_to_see(8.0, 1.0, factor=0.75) == math.ceil(0.75 * 2 * (z * 8.0) ** 2)
    p = mr.power_figures(8.0, {"rho": 0.5, "pairs": 500, "copy_runs": 500, "variance_factor": 1.0})
    assert p["half_floor"]["raw"] == 4019 and p["half_floor"]["adjusted_this_design"] == 4019
    assert p["half_floor"]["adjusted_copy_mean_known"] == math.ceil(0.75 * 2 * (z * 8.0 / 0.5) ** 2)
    assert p["one_floor"]["raw"] == 1005 and p["one_floor"]["vs_fixed_reference_raw"] == 503
    assert mr.power_figures(None, {}) is None
    assert mr.power_figures(8.0, {"rho": None})["one_floor"]["adjusted_this_design"] is None


# ---------------------------------------------------------------------------------------------------- the fixture night
def test_control_variate_on_the_fixture_night(rep):
    # real floors of the 8 ended seeds, and the copy arm's floors on the same seeds (real minus copy: 0 -3 0 17 0 0 0 -5)
    y = [10, 17, 25, 34, 51, 12, 17, 20]
    x = [10, 20, 25, 17, 51, 12, 17, 25]
    cv = rep["control_variate"]
    assert cv["available"] and (cv["pairs"], cv["copy_runs"], cv["extra_copy_runs"]) == (8, 10, 2)
    fit = statistics.linear_regression(x, y)
    assert cv["beta"] == pytest.approx(fit.slope, abs=1e-4) and cv["rho"] == pytest.approx(statistics.correlation(x, y), abs=1e-4)
    assert rep["paired"]["rho"] == cv["rho"] and rep["paired"]["beta"] == cv["beta"]
    assert cv["copy_mean_all"] == pytest.approx(21.1) and cv["copy_mean_paired"] == pytest.approx(statistics.fmean(x), abs=1e-4)
    theta = statistics.fmean(y) - fit.slope * (statistics.fmean(x) - 21.1)
    assert cv["mean_cv"] == pytest.approx(theta, abs=1e-3) and rep["real"]["mean_floor_cv"] == cv["mean_cv"]
    assert cv["adjustment"] == pytest.approx(theta - statistics.fmean(y), abs=1e-3)
    resid = [b - (fit.intercept + fit.slope * a) for a, b in zip(x, y)]
    assert 211 - sum(x) == 34  # the copy arm's 10 floors sum to 211; the two beyond the pairs (the real crash seeds) hold 34
    s2 = sum(r * r for r in resid) / 6
    assert cv["se_cv_known_copy_mean"] == pytest.approx(math.sqrt(s2 / 8), abs=1e-3)
    assert rep["real"]["mean_floor_cv_se"] == cv["se_cv"] and cv["se_cv"] > cv["se_cv_known_copy_mean"]
    assert cv["raw_se"] == pytest.approx(statistics.stdev(y) / math.sqrt(8), abs=1e-3) == pytest.approx(rep["real"]["mean_floor_se"], abs=1e-3)
    assert "2 copy runs beyond the 8 pairs" in cv["note"]
    p = cv["power"]
    assert p["half_floor"]["raw"] == mr.runs_to_see(statistics.stdev(y), 0.5)
    assert p["half_floor"]["adjusted_copy_mean_known"] < p["half_floor"]["adjusted_this_design"] <= p["half_floor"]["raw"]


def test_progress_score_on_the_fixture_night(rep):
    pr = rep["progress"]
    m = pr["measures"]
    sd = statistics.stdev([10, 17, 25, 34, 51, 12, 17, 20])
    assert m["mean_floor"]["value"] == pytest.approx(23.25) and m["mean_floor"]["se"] == pytest.approx(sd / math.sqrt(8), abs=1e-3)
    assert m["act1_reach"]["value"] == pytest.approx(100 * 5 / 8) and m["act1_reach"]["se"] == pytest.approx(100 * math.sqrt(0.625 * 0.375 / 8), abs=1e-3)
    assert m["act1_kill_of_reached"]["value"] == pytest.approx(60.0) and m["act1_kill_of_reached"]["se"] == pytest.approx(100 * math.sqrt(0.6 * 0.4 / 5), abs=1e-3)
    assert m["act2_reach"]["value"] == pytest.approx(25.0) and m["act2_kill_of_reached"]["value"] == pytest.approx(50.0)
    assert m["wins"]["value"] == pytest.approx(12.5) and m["wins"]["se"] == pytest.approx(100 * math.sqrt(0.125 * 0.875 / 8), abs=1e-3)
    assert m["boss_recorded"] is True and pr["previous_night"]["nights"] == ["2026-11-03"]


def test_progress_differences_against_the_previous_generation_pooled(rep):
    d = rep["progress"]["previous_generation_pooled"]
    assert d["generation"] == 9 and d["nights"] == ["2026-11-02", "2026-11-03"] and d["base_runs"] == 9
    base = rep["comparison"]["previous_generation_pooled"]["real"]["base"]
    cur = {"mean_floor": [10, 17, 25, 34, 51, 12, 17, 20], "n": 8}
    floors = [20, 30, 17, 40, 10, 17, 17, 34, 21]
    se = math.sqrt(statistics.variance(cur["mean_floor"]) / 8 + statistics.variance(floors) / 9)
    f = d["diffs"]["mean_floor"]
    assert f["diff"] == pytest.approx(statistics.fmean(cur["mean_floor"]) - statistics.fmean(floors), abs=1e-3)
    assert f["se"] == pytest.approx(se, abs=1e-3) and f["z"] == pytest.approx(f["diff"] / se, abs=2e-3)
    # rates: (count, over) tonight against the base pool, unpaired
    rates = {"act1_reach": ((5, 8), (base["a1_reached"], 9)), "act1_kill_of_reached": ((3, 5), (base["a1_killed"], base["a1_reached"])),
             "act2_reach": ((2, 8), (base["a2_reached"], 9)), "act2_kill_of_reached": ((1, 2), (base["a2_killed"], base["a2_reached"])),
             "wins": ((1, 8), (base["wins"], 9))}
    for key, ((k1, n1), (k2, n2)) in rates.items():
        p1, p2 = k1 / n1, k2 / n2
        se_ = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        got = d["diffs"][key]
        assert got["diff"] == pytest.approx(100 * (p1 - p2), abs=1e-3), key
        assert got["se"] == pytest.approx(100 * se_, abs=1e-3), key
        assert got["z"] == pytest.approx((p1 - p2) / se_, abs=2e-3), key
    assert (base["a1_reached"], base["a1_killed"], base["a2_reached"], base["a2_killed"]) == (7, 4, 3, 1)


def test_comparison_blocks_keep_the_old_fields_and_add_the_new_ones_with_se_and_z(rep):
    blk = rep["comparison"]["previous_generation_pooled"]["real"]
    for key in ("floor_ended", "floor_counted", "act1_of_runs", "act1_of_reached", "act2_of_runs"):  # the older fields
        assert key in blk
    for key in ("act1_reach", "act2_reach", "act2_of_reached", "wins"):
        assert set(blk[key]) == {"diff_pts", "se_pts", "z"} and blk[key]["se_pts"] is not None and blk[key]["z"] is not None
    assert blk["boss_recorded"] == {"current": True, "base": True}
    # a night against no base at all has no progress differences
    assert rep["progress"]["previous_night"]["diffs"]["mean_floor"]["se"] is not None
    first = mr.build_report(LAB / "nightly" / "2026-11-01", None, LAB, None, "none", None, NOW)
    assert first["progress"]["previous_night"] is None and first["progress"]["previous_generation_pooled"] is None


# ---------------------------------------------------------------------------------------------------- the boss rule
def runs_past_boss(n_past: int, with_entry: int) -> list[dict]:
    rows = []
    for i in range(n_past):
        acts = [[0, 1.0]] if i < with_entry else []
        rows.append({"floor": 20 + i % 5, "boss_damage_acts": acts, "end": "death"})
    return rows


def test_a_block_that_never_recorded_the_boss_has_unknown_boss_rates_not_zero():
    bad = mr.make_agg(runs_past_boss(30, 0))
    ok = mr.make_agg(runs_past_boss(30, 30))
    few = mr.make_agg(runs_past_boss(10, 0))  # under 20 runs past the boss: too few to judge
    mixed = mr.make_agg(runs_past_boss(40, 37))  # 3 in 40 lack the entry: under the 10% line
    assert (bad.boss_recorded, ok.boss_recorded, few.boss_recorded, mixed.boss_recorded) == (False, True, True, True)
    blk = mr.progress_block(bad)
    assert blk["boss_recorded"] is False and blk["mean_floor"]["value"] is not None
    assert all(blk[k]["value"] is None and blk[k]["se"] is None for k in ("act1_reach", "act1_kill_of_reached", "act2_reach"))
    assert blk["wins"]["value"] == 0.0
    cmp_bad = mr.compare_blocks(ok, bad)  # a good night against a base that recorded no bosses
    assert cmp_bad["floor_ended"]["diff"] is not None and cmp_bad["wins"]["diff_pts"] is not None
    for key in ("act1_of_runs", "act1_of_reached", "act2_of_runs", "act1_reach", "act2_reach", "act2_of_reached"):
        assert cmp_bad[key] == {"diff_pts": None, "se_pts": None, "z": None}, key
    assert cmp_bad["boss_recorded"] == {"current": True, "base": False}
    assert mr.compare_blocks(ok, ok)["act1_reach"]["diff_pts"] == 0.0
    assert (bad + ok).boss_recorded is False  # 30 of 60 past the boss lack the entry


# ---------------------------------------------------------------------------------------------------- labs written here
def boss_acts(floor: int) -> list[list]:
    if floor <= mr.ACT1_BOSS_FLOOR:
        return []
    acts = [[0, 1.0 if floor >= 20 else 0.5]]
    if floor >= 34:
        acts.append([1, 1.0 if floor >= 40 else 0.4])
    return acts


def write_night(lab: Path, date: str, agent: str, real: dict[str, int], emu: dict[str, int] | None, record_bosses: bool = True,
                crash_seeds: tuple[str, ...] = ()) -> Path:
    night = lab / "nightly" / date
    arm = night / agent
    arm.mkdir(parents=True)
    acts = (lambda f: boss_acts(f)) if record_bosses else (lambda f: [])
    rows = [{"ev": "end", "w": 0, "seed": s, "character": "IRONCLAD", "end": "death", "floor": f, "asked": 10, "boss_damage_acts": acts(f),
             "stats": {"decisions": 10, "diverged": 0, "reanchors": 0, "reanchor_failed": 0}} for s, f in real.items()]
    rows += [{"ev": "crash", "w": 0, "seed": s, "error": "TimeoutError('x')", "t_end": 0.0} for s in crash_seeds]
    (arm / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (arm / "summary.json").write_text("{}", encoding="utf-8")
    if emu is not None:
        earm = night / f"{agent}-emu"
        earm.mkdir()
        erows = [{"seed": s, "ix": i, "win": False, "floor": f, "end": "death", "decisions": 10, "crash": False,
                  "boss_damage_acts": boss_acts(f)} for i, (s, f) in enumerate(emu.items())]
        (earm / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in erows), encoding="utf-8")
        (earm / "summary.json").write_text("{}", encoding="utf-8")
    return night


def correlated_floors(rng: random.Random, n: int, mean: float = 22.0, sd: float = 8.0, rho: float = 0.5) -> tuple[dict, dict]:
    """(real, copy) floors by seed, ints from 1 up, with a shared part so the pairs correlate."""
    real, emu = {}, {}
    for i in range(n):
        shared = rng.gauss(0, 1)
        real[f"S{i:04d}"] = max(1, round(mean + sd * (math.sqrt(rho) * shared + math.sqrt(1 - rho) * rng.gauss(0, 1))))
        emu[f"S{i:04d}"] = max(1, round(mean + sd * (math.sqrt(rho) * shared + math.sqrt(1 - rho) * rng.gauss(0, 1))))
    return real, emu


def test_a_night_whose_copy_arm_is_exactly_its_pairs_says_the_adjustment_gains_nothing(tmp_path):
    lab = tmp_path / "LAB"
    real, emu = correlated_floors(random.Random(3), 300)
    night = write_night(lab, "2026-11-04", "g11", real, emu)
    r = mr.build_report(night, None, lab, None, "none", None, NOW)
    cv = r["control_variate"]
    assert cv["extra_copy_runs"] == 0 and cv["mean_cv"] == pytest.approx(cv["real_mean_paired"], abs=1e-3) and cv["adjustment"] == pytest.approx(0, abs=1e-3)
    assert "no copy run beyond the pairs" in cv["note"] and "adjustment term is zero" in cv["note"]
    assert cv["rho"] == pytest.approx(statistics.correlation(list(emu.values()), list(real.values())), abs=1e-4)
    assert cv["se_cv"] == pytest.approx(cv["raw_se"], rel=0.02)  # no gain at all with no copy run beyond the pairs
    assert cv["se_cv_known_copy_mean"] < 0.9 * cv["raw_se"]  # the gain is there only with the copy mean known
    text = mr.edition_figures(r)
    assert "control variate" in text and "No copy run beyond the pairs" in text and "seed correlation rho" in text
    assert "real runs a night needs to see a change (two nights of fresh seeds compared, 80% power, 5% level" in text
    assert f"one floor {cv['power']['one_floor']['raw']:,}, {cv['power']['one_floor']['adjusted_this_design']:,}" in text


def test_a_night_with_no_copy_arm_still_reports_and_says_why(tmp_path):
    lab = tmp_path / "LAB"
    shutil.copytree(LAB, lab)
    shutil.rmtree(lab / "nightly/2026-11-04/g11-emu")
    (lab / "nightly/2026-11-04/g11/compare.json").unlink()  # the copy arm is gone, so is its comparison file
    night = lab / "nightly" / "2026-11-04"
    r = mr.build_report(night, None, lab, None, "none", None, NOW)
    cv = r["control_variate"]
    assert cv["available"] is False and cv["reason"] == "no copy arm rows for this night" and cv["pairs"] == 0 and cv["copy_runs"] == 0
    assert r["real"]["mean_floor_cv"] is None and r["real"]["mean_floor_cv_se"] is None and r["paired"]["rho"] is None
    assert r["real"]["mean_floor"] == pytest.approx(23.25) and r["progress"]["measures"]["mean_floor"]["value"] == pytest.approx(23.25)
    text = mr.edition_figures(r)
    assert "control variate (the copy arm's floors as covariate for the real arm's): not computed, no copy arm rows for this night" in text
    assert "Progress score" in text
    out, code = mr.run_check(night, None, lab, NOW)
    assert code == 0 and "0 mismatches" in out and "control variate: seed correlation (rho)" in out
    assert mr.main([str(night), "--winlog", "none", "--now", "2026-11-04T01:00:00Z", "--out", str(tmp_path / "o")]) == 0
    data = json.loads((tmp_path / "o" / "morning_report.json").read_text(encoding="utf-8"))
    assert data["control_variate"]["available"] is False and data["real"]["mean_floor_cv"] is None


def test_two_pairs_only_and_a_copy_arm_that_never_varies(tmp_path):
    lab = tmp_path / "LAB"
    night = write_night(lab, "2026-11-04", "g11", {"A": 10, "B": 30}, {"A": 12, "B": 28, "C": 5})
    r = mr.build_report(night, None, lab, None, "none", None, NOW)
    cv = r["control_variate"]
    assert cv["available"] and cv["pairs"] == 2 and cv["copy_runs"] == 3 and cv["mean_cv"] is None and cv["rho"] is None
    assert cv["power"] is None and "real runs a night needs" not in mr.edition_figures(r)  # no fit, no power table
    assert "not enough" not in mr.edition_figures(r)  # prints without raising
    assert mr.run_check(night, None, lab, NOW)[1] == 0
    lab2 = tmp_path / "LAB2"
    real = {f"S{i}": f for i, f in enumerate([10, 14, 20, 25, 31, 12, 18])}
    night2 = write_night(lab2, "2026-11-04", "g11", real, {s: 17 for s in real})
    r2 = mr.build_report(night2, None, lab2, None, "none", None, NOW)
    cv2 = r2["control_variate"]
    assert cv2["beta"] is None and cv2["rho"] is None and cv2["mean_cv"] == pytest.approx(cv2["real_mean_paired"], abs=1e-3)
    assert cv2["se_cv"] == cv2["raw_se"] and mr.run_check(night2, None, lab2, NOW)[1] == 0


def four_night_lab(tmp_path: Path) -> tuple[Path, Path]:
    """Four nights of three generations; the first night did not record the real arm's bosses; the last has copy runs beyond its pairs
    and a real crash row."""
    lab = tmp_path / "LAB"
    rng = random.Random(21)
    plan = [("2026-11-01", "g5", 120, 19.0, False), ("2026-11-02", "g7", 140, 21.0, True), ("2026-11-03", "g7", 150, 22.0, True),
            ("2026-11-04", "g9", 160, 24.0, True)]
    last = None
    for date, agent, n, mean, rec in plan:
        real, emu = correlated_floors(rng, n, mean=mean)
        crash = ()
        if date == "2026-11-04":
            crash = (f"S{n - 1:04d}",)
            real.pop(crash[0])  # the real run on this seed crashed: its copy run stays beyond the pairs
        last = write_night(lab, date, agent, real, emu, record_bosses=rec, crash_seeds=crash)
    return lab, last


def test_progress_rules_on_a_written_lab_and_the_check_agrees(tmp_path):
    lab, night = four_night_lab(tmp_path)
    r = mr.build_report(night, None, lab, None, "none", None, NOW)
    pr = r["progress"]
    assert pr["previous_night"]["nights"] == ["2026-11-03"] and pr["previous_night"]["generation"] == 7
    assert pr["previous_generation_pooled"]["generation"] == 7 and pr["previous_generation_pooled"]["nights"] == ["2026-11-02", "2026-11-03"]
    assert pr["previous_generation_pooled"]["base_boss_recorded"] is True and r["control_variate"]["extra_copy_runs"] == 1
    first = mr.build_report(lab / "nightly" / "2026-11-02", None, lab, None, "none", None, NOW)
    assert first["progress"]["previous_night"]["base_boss_recorded"] is False  # the night before it recorded no bosses
    assert first["progress"]["previous_night"]["diffs"]["act1_reach"] == {"diff": None, "se": None, "z": None}
    assert first["progress"]["previous_night"]["diffs"]["mean_floor"]["z"] is not None
    text = mr.edition_figures(first)
    assert "the previous night did not record the boss fights" in text
    for night_ in (lab / "nightly" / d for d in ("2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04")):
        out, code = mr.run_check(night_, None, lab, NOW)
        assert code == 0 and "0 mismatches" in out, out
    out, _ = mr.run_check(night, None, lab, NOW)
    assert "progress: Act 1 boss reached (of runs) (points), against previous generation pooled, z" in out
    assert "control variate: SE of the adjusted mean floor" in out


def test_edition_text_carries_the_control_variate_and_the_progress_score(tmp_path):
    lab, night = four_night_lab(tmp_path)
    text = mr.edition_figures(mr.build_report(night, None, lab, None, "none", None, NOW))
    assert "control variate (the copy arm's floor on the same seed as covariate" in text and "1 copy runs beyond the 159 pairs" in text
    assert "Progress score (ended runs; value (SE); difference against each base (SE, z)" in text
    for label in ("mean floor", "Act 1 boss reached (of runs)", "Act 1 boss killed (of those reached)", "Act 2 boss reached (of runs)",
                  "Act 2 boss killed (of those reached)", "wins (of runs)"):
        assert f"- {label}: " in text
    assert "against the previous night (11-03, generation 7" in text and "against the previous generation pooled (11-02+11-03, generation 7" in text


# ---------------------------------------------------------------------------------------------------- --check covers the new figures
def test_check_lists_every_new_figure_with_a_match_on_the_fixture_night():
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 0 and "0 mismatches" in text
    for name in mr.CV_NAMES.values():
        assert name in text, name
    rows = {r["figure"]: r for r in mr.check_rows(mr.report_check_figures(mr.build_report(NIGHT, None, LAB, None, "none", None, NOW)),
                                                  mr.independent_figures(NIGHT, "g11"))}
    assert "SE of mean floor, ended, real" in rows
    expect = [f"progress: {label}{' (points)' if unit == 'points' else ''}, {what}" for _k, label, unit, _f in mr.PROGRESS
              for what in ["value", "SE"] + [f"against {tag}, {w}" for _b, tag in mr.BASE_TAGS for w in ("difference", "SE", "z")]]
    assert len(expect) == 6 * 8 and all(name in rows and rows[name]["ok"] for name in expect)
    cv_rows = [rows[n] for n in list(mr.CV_NAMES.values()) + list(mr.POWER_NAMES.values())]
    assert len(mr.CV_NAMES) == 13 and len(mr.POWER_NAMES) == 8 and len(cv_rows) == 21
    assert all(r["ok"] and r["first"] is not None and r["second"] is not None for r in cv_rows)


def test_check_catches_a_wrong_control_variate_or_progress_figure(monkeypatch):
    real_cv, real_pr = mr._cv_second_path, mr._progress_second_path

    def bad_cv(a, b):
        out = real_cv(a, b)
        out[mr.CV_NAMES["rho"]] += 0.01
        out[mr.CV_NAMES["se_cv"]] *= 1.1
        return out

    monkeypatch.setattr(mr, "_cv_second_path", bad_cv)
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 1 and "2 mismatches: control variate: seed correlation (rho); control variate: SE of the adjusted mean floor" in text
    monkeypatch.setattr(mr, "_cv_second_path", real_cv)

    def bad_runs(a, b):
        out = real_cv(a, b)
        out[mr.POWER_NAMES[("one_floor", "raw")]] += 1
        return out

    monkeypatch.setattr(mr, "_cv_second_path", bad_runs)
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 1 and "1 mismatch: control variate: runs a night needs to see one floor, raw" in text
    monkeypatch.setattr(mr, "_cv_second_path", real_cv)

    def bad_pr(night, agent, real):
        out = real_pr(night, agent, real)
        key = "progress: mean floor, against previous night, z"
        out[key] += 0.01
        out["progress: wins (of runs) (points), value"] += 0.01
        return out

    monkeypatch.setattr(mr, "_progress_second_path", bad_pr)
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 1 and "2 mismatches" in text and "progress: mean floor, against previous night, z" in text


def test_check_tolerates_the_reports_own_rounding_only():
    assert mr._same(0.5521, 0.55213) and not mr._same(0.5521, 0.5523)
    assert mr._same(1.2344, 1.23449, mr._tol_of("progress: x (points), value")) and mr._same(1.234, 1.2344, mr._tol_of("progress: x, against previous night, z"))
    assert not mr._same(1.234, 1.236, mr._tol_of("progress: x (points), SE"))
    assert mr._tol_of("control variate: seed correlation (rho)") == mr.CHECK_TOL


def test_the_nine_night_figures_carry_no_paths(tmp_path):
    lab, night = four_night_lab(tmp_path)
    out = tmp_path / "rep"
    assert mr.main([str(night), "--winlog", "none", "--now", "2026-11-04T01:00:00Z", "--out", str(out)]) == 0
    blob = "".join((out / n).read_text(encoding="utf-8") for n in ("morning_report.json", "handoff_line.md", "edition_figures.md"))
    for bad in (str(tmp_path), str(tmp_path).replace("\\", "/"), "Users", "C:\\"):
        assert bad not in blob, bad
