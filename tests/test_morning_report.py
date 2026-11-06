"""tools/morning_report.py on a synthetic lab (tests/fixtures/morning_report, built by build_fixture.py; no real run is in it).

The night under test is 2026-11-04 (generation 11): 10 seeds, real arm 8 ended runs (floors 10 17 25 34 51 12 17 20) and 2 crash
rows, emulator arm 10 runs. The earlier nights are generation 7 (11-01) and generation 9 (11-02, 11-03). Every expected number
below is worked by hand from those rows (see the builder's docstring and comments).
"""

from __future__ import annotations

import base64
import json
import math
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
WINLOG = FIX / "winlog.json"
LOGS = FIX / "root" / "logs" / "w5-night-20261104-stdout"
NOW = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def rep() -> dict:
    return mr.build_report(NIGHT, None, LAB, LOGS, str(WINLOG), "test usage", NOW)


@pytest.fixture(scope="module")
def rep_1103() -> dict:
    """The generation-9 night 2026-11-03 as the night under test: an earlier night of its own generation exists."""
    return mr.build_report(LAB / "nightly" / "2026-11-03", None, LAB, None, "none", None, NOW)


# ---------------------------------------------------------------------------------------------------- counts and rates
def test_run_counts(rep):
    assert rep["runs"] == {"planned": 10, "emu_planned": 10, "real_rows": 10, "real_ended": 8, "real_crash_rows": 2, "emu_rows": 10, "emu_ended": 10,
                           "emu_crash_rows": 0, "seeds_with_rows_real": 10, "seeds_with_rows_emu": 10, "seeds_with_rows_both": 10}
    r = rep["real"]
    assert (r["ended"], r["crashes"], r["wins"], r["fight_unfinished"], r["chest_stop"]) == (8, 2, 1, 1, 0)
    assert r["decisions"] == 960 and r["diverged"] == 4 and r["reanchors"] == 9 and r["reanchor_failed"] == 2


def test_floors_ended_and_counted(rep):
    r = rep["real"]
    assert r["mean_floor"] == pytest.approx(23.25) and r["median_floor"] == 18.5
    assert r["mean_floor_counted"] == pytest.approx(18.6)  # 186 over 10 seeds, the crash rows as floor 0
    assert r["sd_floor"] == pytest.approx(statistics.stdev([10, 17, 25, 34, 51, 12, 17, 20]), abs=1e-3)
    e = rep["emu"]
    assert e["mean_floor"] == pytest.approx(21.1) and e["mean_floor_counted"] == pytest.approx(21.1) and e["crashes"] == 0


def test_boss_rates(rep):
    r, e = rep["real"], rep["emu"]
    assert (r["act1_reached"], r["act1_killed"]) == (5, 3)
    assert r["act1_killed_of_runs"] == pytest.approx(3 / 8) and r["act1_killed_of_reached"] == pytest.approx(0.6)
    assert (r["act2_reached"], r["act2_killed"], r["act3_reached"], r["act3_killed"]) == (2, 1, 1, 1)
    assert (e["act1_reached"], e["act1_killed"]) == (7, 4)
    assert e["act1_killed_of_runs"] == pytest.approx(0.4) and e["act1_killed_of_reached"] == pytest.approx(4 / 7, abs=1e-4)
    assert (e["act2_reached"], e["act2_killed"], e["wins"]) == (1, 1, 1)


def test_deck_proxy_counts_picks_before_floor_17(rep):
    # picks on floors <= 16 among the 5 runs that reached the Act 1 boss: SEED0001 took two; SEED0002's only pick is on floor 20
    # (after the boss) and SEED0000's pick does not count since that run never reached it
    assert rep["real"]["act1_picks_mean"] == pytest.approx(2 / 5)
    assert rep["real"]["deck_proxy"] == pytest.approx(11 + 2 / 5)


def test_aggregates_match_statistics_module():
    floors = [3, 9, 9, 14, 20, 20, 41]
    g = mr.make_agg([{"floor": f} for f in floors], crashes=2)
    assert g.mean() == pytest.approx(statistics.fmean(floors)) and g.sd() == pytest.approx(statistics.stdev(floors))
    counted = floors + [0, 0]
    assert g.mean(True) == pytest.approx(statistics.fmean(counted)) and g.sd(True) == pytest.approx(statistics.stdev(counted))
    pooled = g + g
    assert pooled.n == 14 and pooled.sd() == pytest.approx(statistics.stdev(floors * 2))


def test_margin_and_rate_diff():
    assert mr.margin95_pts(2000) == pytest.approx(2.19, abs=0.01) and mr.margin95_pts(498) == pytest.approx(4.39, abs=0.01)
    d = mr.rate_diff(30, 100, 20, 100)
    assert d["diff_pts"] == pytest.approx(10.0) and d["se_pts"] == pytest.approx(100 * math.sqrt(0.21 / 100 + 0.16 / 100), abs=1e-3)
    assert mr.rate_diff(1, 0, 1, 5)["diff_pts"] is None


# ---------------------------------------------------------------------------------------------------- comparison
def test_previous_generation_pooled_comparison(rep):
    c = rep["comparison"]["previous_generation_pooled"]
    assert c["generation"] == 9 and c["nights"] == ["2026-11-02", "2026-11-03"]
    floors = [20, 30, 17, 40, 10, 17, 17, 34, 21]  # both generation-9 nights, ended rows (the fight_unfinished row is an ended run)
    base = c["real"]["base"]
    assert base["runs"] == 9 and base["mean_floor"] == pytest.approx(statistics.fmean(floors))
    assert (base["a1_reached"], base["a1_killed"], base["a2_reached"], base["a2_killed"]) == (7, 4, 3, 1)
    cur = [10, 17, 25, 34, 51, 12, 17, 20]
    se = math.sqrt(statistics.variance(cur) / 8 + statistics.variance(floors) / 9)
    f = c["real"]["floor_ended"]
    assert f["diff"] == pytest.approx(statistics.fmean(cur) - statistics.fmean(floors), abs=1e-3)
    assert f["se"] == pytest.approx(se, abs=1e-3) and f["z"] == pytest.approx(f["diff"] / se, abs=2e-3)
    a1 = c["real"]["act1_of_runs"]
    p1, p2 = 3 / 8, 4 / 9
    assert a1["diff_pts"] == pytest.approx(100 * (p1 - p2), abs=1e-2)
    assert a1["se_pts"] == pytest.approx(100 * math.sqrt(p1 * (1 - p1) / 8 + p2 * (1 - p2) / 9), abs=1e-2)
    counted = c["real"]["floor_counted"]  # the crash rows as floor 0 on both sides (the generation-9 nights have one each)
    assert counted["diff"] == pytest.approx(18.6 - 206 / 11, abs=1e-3)
    assert c["emu"]["base"]["runs"] == 9


def test_previous_night_and_no_same_generation(rep):
    pn = rep["comparison"]["previous_night"]
    assert pn["nights"] == ["2026-11-03"] and pn["generation"] == 9 and pn["real"]["base"]["runs"] == 5
    assert rep["comparison"]["same_generation_earlier"] is None  # the first night of generation 11


def test_same_generation_comparison_on_an_earlier_night(rep_1103):
    c = rep_1103["comparison"]
    assert c["same_generation_earlier"]["nights"] == ["2026-11-02"] and c["same_generation_earlier"]["real"]["base"]["runs"] == 4
    assert c["previous_generation_pooled"]["generation"] == 7 and c["previous_generation_pooled"]["real"]["base"]["runs"] == 4
    assert c["previous_night"]["nights"] == ["2026-11-02"]
    assert rep_1103["real"]["ended"] == 5 and rep_1103["real"]["crashes"] == 1


# ---------------------------------------------------------------------------------------------------- pairing
def test_paired_ended_and_counted(rep):
    p = rep["paired"]["ended"]
    assert p["seeds"] == 8
    assert (p["act1_both"], p["act1_real_only"], p["act1_emu_only"], p["act1_neither"]) == (2, 1, 2, 3)
    assert p["act1_agreement"] == pytest.approx(5 / 8)
    # real minus emulator floors on the 8 ended seeds: 0 -3 0 17 0 0 0 -5
    diffs = [0, -3, 0, 17, 0, 0, 0, -5]
    assert p["floor_real_minus_emu_mean"] == pytest.approx(statistics.fmean(diffs)) and p["floor_sd"] == pytest.approx(statistics.pstdev(diffs), abs=1e-3)
    c = rep["paired"]["counted"]
    assert c["seeds"] == 10 and c["floor_emu_minus_real_mean"] == pytest.approx(2.5)  # 211 - 186 over 10 seeds


def test_rows_agree_with_summary_files(rep):
    checks = rep["cross_checks"]
    assert len(checks) >= 15 and all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]
    assert any("compare.floor_gap" in c["check"] and c["file"] == 2.5 for c in checks)


def test_cross_check_flags_a_disagreement(tmp_path):
    import shutil

    lab = tmp_path / "LAB"
    shutil.copytree(LAB, lab)
    s = json.loads((lab / "nightly/2026-11-04/g11/summary.json").read_text())
    s["crashes"] = 3
    (lab / "nightly/2026-11-04/g11/summary.json").write_text(json.dumps(s))
    r = mr.build_report(lab / "nightly" / "2026-11-04", None, lab, None, "none", None, NOW)
    bad = [c["check"] for c in r["cross_checks"] if c["ok"] is False]
    assert bad == ["real crash rows = summary.crashes"]
    assert mr.main([str(lab / "nightly" / "2026-11-04"), "--winlog", "none", "--now", "2026-11-04T01:00:00Z"]) == 1


# ---------------------------------------------------------------------------------------------------- crashes
def test_crash_kinds_and_exit_codes():
    assert mr.crash_kind("RuntimeError: the engine refused action 24 in phase 5") == {"kind": "engine refused action", "action": 24, "phase": 5}
    k = mr.crash_kind("GameDied: game exited (3221225501)")
    assert (k["kind"], k["exit_hex"], k["exit_name"]) == ("game exited", "0xC000001D", "illegal instruction")
    k = mr.crash_kind("GameDied: game exited (3221225477)")
    assert (k["exit_hex"], k["exit_name"]) == ("0xC0000005", "access violation")
    k = mr.crash_kind("GameDied: game exited (4294930433)")
    assert k["exit_hex"] == "0xFFFF7001" and k["exit_name"] is None  # not a named status
    assert mr.crash_kind("worker process exited 3221225477 (0xC0000005)")["kind"] == "worker process exited"
    assert mr.crash_kind("worker deadline: no result after 900 s")["kind"] == "worker deadline"
    assert mr.crash_kind("TimeoutError('no message in 100 s')")["kind"] == "timeout"
    assert mr.crash_kind("something else")["kind"] == "other"
    assert mr.hex_exit(-1073741819) == "0xC0000005"


def test_crash_rows_listed_with_seed_kind_and_log_entry(rep):
    rows = {c["seed"]: c for c in rep["crashes"]["rows"]}
    assert set(rows) == {"SEED0008", "SEED0009"} and rep["crashes"]["by_kind"] == {"engine refused action": 1, "game exited": 1}
    a, g = rows["SEED0008"], rows["SEED0009"]
    assert (a["action"], a["phase"], a["worker"], a["where"]) == (24, 5, 2, "agent") and a["log_entry"] is None
    assert (g["exit"], g["exit_hex"], g["exit_name"]) == (3221225477, "0xC0000005", "access violation")
    assert g["log_entry"]["app"] == "SlayTheSpire2.exe" and g["log_entry"]["top_frame"] == "Godot.GodotObject.Dispose"
    assert g["utc"] == "2026-11-03T22:46:08Z"


def test_crash_kind_tally_over_earlier_nights(rep):
    cu = rep["crashes"]["cumulative"]["engine refused action"]
    # one on 11-02 (OLD905), one on 11-03 (NEW906), one tonight; rows from the first of those nights on: 5 + 6 + 10
    assert cu["since"] == "2026-11-02" and cu["count"] == 3 and cu["real_rows"] == 21
    assert cu["by_night"] == {"2026-11-02": 1, "2026-11-03": 1, "2026-11-04": 1}


def test_fight_unfinished_with_history(rep):
    fu = rep["fight_unfinished"]
    assert fu["this_night"] == [{"seed": "SEED0007", "worker": 0, "floor": 20, "streak": {"n": 10, "screen": "shop", "action": 0}}]
    assert fu["earlier_nights"]["2026-11-03"] == {"fight_unfinished": 1, "ended_rows": 5}
    assert fu["earlier_nights"]["2026-11-01"] == {"fight_unfinished": 0, "ended_rows": 4}


# ---------------------------------------------------------------------------------------------------- per-fight tables
def test_emulator_fight_table_from_nodes(rep):
    cells = mr.fight_table_from_nodes([r for r in mr.read_jsonl(NIGHT / "g11-emu" / "runs.jsonl")])
    t = {(a, k): tuple(v) for (a, k), v in cells.items()}
    assert t == {(1, "hallway"): (15, 12), (1, "elite"): (3, 3), (1, "boss"): (7, 4), (2, "hallway"): (4, 2), (2, "elite"): (1, 0),
                 (2, "boss"): (1, 1), (3, "hallway"): (1, 1), (3, "boss"): (1, 1)}
    # the boss cell agrees with the rows' own kill count (7 reached, 4 killed)
    assert rep["emu"]["act1_reached"] == 7 and rep["emu"]["act1_killed"] == 4
    shown = mr.cells_json(cells, min_cell=1)
    assert {"act": 1, "kind": "hallway", "fights": 15, "survived": 12, "win_rate": 0.8, "suppressed": False} in shown


def test_cells_under_twenty_fights_are_suppressed(rep):
    assert all(c["suppressed"] and c["survived"] is None and c["win_rate"] is None for c in rep["fights"]["emu"])
    assert len(rep["fights"]["emu"]) == 8
    big = mr.cells_json({(1, "hallway"): [20, 19], (1, "elite"): [19, 19]})
    assert big[0]["suppressed"] is False and big[0]["win_rate"] == 0.95 and big[1]["suppressed"] is True


def test_real_fight_table_from_copied_logs(rep):
    fights, seen = mr.parse_logs(LOGS)
    assert len(fights) == 10 and seen["runs ended in logs"] == 3
    cells, notes, kinds = mr.real_fight_table(fights)
    t = {k: tuple(v) for k, v in cells.items()}
    assert t == {(1, "hallway"): (4, 3), (1, "elite"): (1, 1), (1, "boss"): (2, 1), (2, "hallway"): (1, 1)}
    assert notes == {"event fights (not in the table)": 1, "other fights (not in the table)": 1}
    n = rep["fights"]["real_notes"]
    assert n["runs_ended_in_logs"] == 3 and n["run_ends_by_last_screen"] == {"death, last screen combat": 2, "death, last screen event": 1}
    assert n["event_or_other"] == ["MYSTERY_EVENT_ENCOUNTER", "OVERGROWTH_CRAWLERS"]
    assert mr.encounter_kind("X_WEAK") == "hallway" and mr.encounter_kind("X_BOSS") == "boss" and mr.encounter_kind("ODD") == "other"


# ---------------------------------------------------------------------------------------------------- Windows log
def test_windows_log_counts(rep):
    w = rep["winlog"]
    assert w["status"] == "read" and w["window"] == ["2026-11-03T19:55:00Z", "2026-11-04T00:02:00Z"]
    # inside: an EndTurn fail-fast and its Application Error companion (one death), a GetReadyAction fail-fast, a native fault
    # alone, the game's death and an unrelated VSS entry; the entry before the window is left out
    assert w["events_in_window"] == 6 and w["process_deaths"] == 4
    assert (w["emulator_failfasts"], w["emulator_endturn_0x25aa"], w["emulator_getreadyaction"], w["game_deaths"]) == (3, 1, 1, 1)
    assert w["emulator_by_top_frame"] == {"Sts2Emulator.Core.CombatEngine.EndTurn + 0x25aa": 1,
                                          "Sts2Emulator.Core2.ActionQueueSet.GetReadyAction + 0x287": 1,
                                          "Sts2Emulator.dll native fault 0xc0000409": 1}
    p = rep["winlog_previous_night"]
    assert p["date"] == "2026-11-03" and p["emulator_failfasts"] == 1 and p["emulator_getreadyaction"] == 1 and p["played_rows"] == 11


def test_classify_event_ignores_what_is_not_a_death():
    assert mr.classify_event({"provider": "VSS", "id": 8224, "msg": "x", "utc": "2026-11-03T20:00:00Z"}) is None
    d = mr.classify_event({"provider": ".NET Runtime", "id": 1023, "utc": "2026-11-03T20:00:00Z",
                           "msg": "Application: SlayTheSpire2.exe\nDescription: internal error in the .NET Runtime with exit code 0xc000001d."})
    assert d["kind"] == "game" and d["top_frame"] is None
    d = mr.classify_event({"provider": ".NET Runtime", "id": 1026, "utc": "2026-11-03T20:00:00Z", "msg": "Application: python.exe\nStack:\n   at Foo.Bar()"})
    assert d["kind"] == "python-other"


def test_powershell_reader_builds_an_encoded_command_and_parses_one_event(monkeypatch):
    calls = []

    class Done:
        returncode = 0
        stdout = json.dumps({"total": 2, "events": {"utc": "2026-11-03T21:00:00.0000000Z", "id": 1026, "provider": ".NET Runtime",
                                                    "msg": "Application: pythonw.exe\nat Sts2Emulator.Core2.ActionQueueSet.GetReadyAction() + 0x287"}})

    def runner(argv, **kw):
        calls.append(argv)
        return Done()

    monkeypatch.setattr(mr.sys, "platform", "win32")
    s, e = datetime(2026, 11, 3, 20, 0, tzinfo=timezone.utc), datetime(2026, 11, 4, 0, 0, tzinfo=timezone.utc)
    out = mr.read_winlog("auto", s, e, runner)
    argv = calls[0]
    assert argv[0] == "powershell.exe" and "-EncodedCommand" in argv and "-NonInteractive" in argv
    script = base64.b64decode(argv[-1]).decode("utf-16-le")
    assert "Get-WinEvent" in script and "2026-11-03T20:00:00Z" in script and "2026-11-04T00:00:00Z" in script
    assert out["status"] == "read" and out["events_in_window"] == 2 and out["emulator_failfasts"] == 1 and out["emulator_getreadyaction"] == 1


def test_unreadable_log_is_reported_not_invented(monkeypatch):
    class Bad:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(mr.sys, "platform", "win32")
    s, e = datetime(2026, 11, 3, 20, 0, tzinfo=timezone.utc), datetime(2026, 11, 4, 0, 0, tzinfo=timezone.utc)
    assert mr.read_winlog("auto", s, e, lambda *a, **k: Bad())["status"] == "not read: RuntimeError"
    assert mr.read_winlog("none", s, e)["status"].startswith("skipped")
    r = mr.build_report(NIGHT, None, LAB, None, "none", None, NOW)
    figs = [i["figure"] for i in r["not_computed"]]
    assert any("application-log" in f for f in figs) and any("per-fight survival of the real arm" in f for f in figs)
    assert any("usage readout" in f for f in figs) and r["fights"]["real"] is None


# ---------------------------------------------------------------------------------------------------- lockstep, groups, job
def test_lockstep_figures_and_clipped_monster_key(rep):
    lk = rep["lockstep"]
    assert (lk["decisions"], lk["diverged"], lk["reanchors"], lk["reanchor_failed"], lk["gaps"]) == (960, 4, 9, 2, 3)
    assert lk["divergence_pct"] == pytest.approx(100 * 4 / 960, abs=1e-3)
    # the rows clip the key to MONSTER_ALPHA_SEG; the rows' other mentions complete it
    assert lk["reanchor_fail_labels"] == {"no emulator id for MONSTER_ALPHA_SEGMENT": 1, "to-map": 1}
    assert lk["no_emulator_id_failures_by_earlier_night"] == {"2026-11-01": 0, "2026-11-02": 1, "2026-11-03": 2}
    assert mr.reanchor_label("fight_start:diff:.potions", "") == ".potions"
    assert mr.reanchor_label("room_entry:to_map", "") == "to-map"


def test_groups_and_the_d11c_proof(rep):
    g = rep["groups"]
    assert g["present"] and g["groups"] == 3 and g["total_weight"] == 1000.0
    assert g["d11c"]["Strike"] == {"id": "Gdb57549c26", "rank": 2, "weight": 300.0, "decisions_affected": 12, "records": 2}
    assert g["d11c"]["Defend"]["rank"] == 3 and g["d11c_together_weight"] == 400.0 and g["d11c_share"] == 0.4
    assert [t["id"] for t in g["top_groups"]] == ["Gother00000", "Gdb57549c26", "G2f160e9505"]
    assert [f["family"] for f in g["top_families"]] == ["F06", "F08"]
    # two records where the game has more, one where the emulator has more, one mixed record left out
    hc = g["hand_count"]
    assert (hc["game_more"], hc["emulator_more"], hc["same_size"]) == (2, 1, 0)
    assert hc["per_100k_decisions"] == pytest.approx(100000 * 3 / 960, abs=0.01)


def test_job_window_tree_and_next_night(rep):
    n = rep["night"]
    assert n["job"]["tree"] == "01234567" and n["job"]["name"] == "20261103T2000-nightly-real"
    assert (n["start_utc"], n["end_utc"]) == ("2026-11-03T20:00:00Z", "2026-11-04T00:00:00Z")
    assert n["wall_min"] == {"real_arm": 120.0, "emulator_arm": 60.0}
    assert n["interruptions"]["count"] == 1 and n["interruptions"]["stops"][0]["utc"] == "2026-11-03T22:00:00Z"  # the 01:00 stop is later
    assert n["next_night"] == {"known": True, "every_h": 20, "earliest_start_utc": "2026-11-04T16:00:00Z",
                               "landings_safe_until_utc": "2026-11-04T16:00:00Z", "on_promotion": True}
    assert rep["machine"]["samples"] == 3 and rep["machine"]["cpu_pct_max"] == 80.0 and rep["machine"]["avail_mb_min"] == 7000


def test_hp_is_reported_as_not_recorded(rep):
    assert rep["hp_recorded"] is False
    assert any("HP entering a boss" in i["figure"] for i in rep["not_computed"])
    assert mr.hp_recorded([{"hp": 5}]) and mr.hp_recorded([{"max_hp": 5}]) and not mr.hp_recorded([{"boss_damage": 0.5, "phase": 2}])


# ---------------------------------------------------------------------------------------------------- text and CLI
def test_handoff_line_carries_the_figures(rep):
    line = mr.handoff_line(rep)
    head, tables = line.split("\n\n", 1)
    assert head.startswith("- 2026-11-04T01:00Z morning_report.py") and "tree 01234567" in head and "usage test usage" in head
    for piece in ("8 ended runs (all but 2 crash rows)", "mean floor 23.25", "18.600", "Act 1 boss kill 37.5% (3)", "emulator arm, 10 runs: 21.10",
                  "Generation 9 pooled over its 2 real-arm nights (9 runs", "(SE 5.77, 0.1 SE)", "both 2, real only 1, emu only 2, neither 3 (agreement 62.5%)",
                  "10 of 10 seeds have rows in both arms", "3 emulator fail-fast", "1 at `EndTurn + 0x25aa`", "SEED0008 action 24 phase 5",
                  "SEED0009 exit 3221225477 = 0xC0000005 (access violation), Windows log: SlayTheSpire2.exe at 22:46:08Z in Godot.GodotObject.Dispose",
                  "seed SEED0007 (worker 0, floor 20, 10 identical actions in a row on a shop screen)", "MONSTER_ALPHA_SEGMENT",
                  "Strike rank 2, weight 300.0 (2 records)", "Defend rank 3, weight 100.0 (1 record)", "1 stop(s) of the step",
                  "from 16:00Z on 11-04"):
        assert piece in line, piece
    assert "\n" not in head  # the lane's line is one line; the tables follow it
    assert tables.startswith("  **Night 2026-11-04/g11: run numbers**")
    assert "  | human R1 | | 27.05 | | 54.6% | 29.1% | 11.3% | | |" in tables
    assert "  | real 2026-11-04 | 8 | 23.25 | 18 | 37.5% (3) | 12.5% (1) | 12.5% (1) | 2 | 0 |" in tables
    assert "  | 1 | hallway | 4 | 3 | 75.0% |" not in tables  # cells under 20 fights are suppressed in the tables
    assert "| 1 | hallway | 15 | suppressed | suppressed |" in tables


def test_pairing_is_judged_on_the_copy_arm_prefix(rep):
    # --emu-runs N: the copy arm plays the first N of the block's seeds, so "rows in both arms" is out of N, not the real arm's plan
    import copy
    r = copy.deepcopy(rep)
    r["runs"]["emu_planned"] = 5
    r["runs"]["seeds_with_rows_both"] = 5
    line = mr.handoff_line(r)
    assert "5 of 5 seeds have rows in both arms (the copy arm plays 5 of the 10 seeds)" in line
    assert "10 seeds planned" in line
    # without the field the line reads as before
    assert "10 of 10 seeds have rows in both arms;" in mr.handoff_line(rep)


def test_edition_figures_list(rep):
    text = mr.edition_figures(rep)
    assert text.startswith("Edition figures: night 2026-11-04 (g11, generation 11)")
    for piece in ("floors: real 23.25 on 8 ended runs (18.600 counted, 2 crash rows as floor 0, of 10); emulator 21.10 on 10 runs",
                  "Act 1 boss kill of runs: real 37.5% (3), emulator 40.0% (4)", "agreement of the two arms on the Act 1 boss: 62.5% of 8 seeds",
                  "+2.500 (emulator minus real, crash = 0) on 10 seeds", "crashes: 2 of 10 real rows", "emulator fail-fasts in the Windows application log",
                  "One line: Generation 11 against generation 9 pooled: +0.36 floors (0.1 SE)"):
        assert piece in text, piece


def test_cli_writes_three_files_and_no_paths(tmp_path, capsys):
    out = tmp_path / "rep"
    rc = mr.main([str(NIGHT), "--winlog", str(WINLOG), "--now", "2026-11-04T01:00:00Z", "--usage", "test usage", "--out", str(out)])
    assert rc == 0
    assert sorted(p.name for p in out.iterdir()) == ["edition_figures.md", "handoff_line.md", "morning_report.json"]
    data = json.loads((out / "morning_report.json").read_text(encoding="utf-8"))
    assert data["night"]["folder"] == "nightly/2026-11-04" and data["real"]["ended"] == 8
    assert data["fights"]["real"] is not None  # the copied logs were found beside the lab, as on the real machine
    blob = "".join((out / n).read_text(encoding="utf-8") for n in ("morning_report.json", "handoff_line.md", "edition_figures.md"))
    for bad in (str(FIX), str(FIX).replace("\\", "/"), "Users", "pmpal", "C:\\", ":/"):
        assert bad not in blob, bad
    assert "wrote morning_report.json" in capsys.readouterr().out


def test_cli_prints_when_no_out(capsys):
    assert mr.main([str(NIGHT), "--winlog", "none", "--logs", str(LOGS), "--now", "2026-11-04T01:00:00Z"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("- 2026-11-04T01:00Z morning_report.py") and "Edition figures" in out and "Windows application log: skipped" in out


def test_a_block_that_has_not_closed_makes_no_report(tmp_path):
    import shutil

    lab = tmp_path / "LAB"
    shutil.copytree(LAB, lab)
    (lab / "nightly/2026-11-04/g11/summary.json").unlink()
    with pytest.raises(SystemExit, match="no summary.json yet"):
        mr.build_report(lab / "nightly" / "2026-11-04", None, lab, None, "none", None, NOW)
    with pytest.raises(SystemExit, match="name one with --agent"):
        shutil.copytree(lab / "nightly/2026-11-04/g11", lab / "nightly/2026-11-04/g12")
        mr.build_report(lab / "nightly" / "2026-11-04", None, lab, None, "none", None, NOW)


# ---------------------------------------------------------------------------------------------------- --check: the second path
def test_check_matches_on_the_fixture_night(capsys):
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 0 and "MISMATCH" not in text and text.rstrip().endswith("0 mismatches")
    row = {ln.split("  ")[0].strip(): ln for ln in text.splitlines()}
    assert "MATCH" in row["ended runs, real"] and "8" in row["ended runs, real"]
    assert "MATCH" in row["Act 1 boss agreement of the arms"]


def test_second_path_gives_the_hand_worked_figures():
    f = mr.independent_figures(NIGHT, "g11")  # straight from the rows; the numbers are the hand-worked ones of the tests above
    assert (f["ended runs, real"], f["crash rows, real"], f["ended runs, emulator"], f["crash rows, emulator"]) == (8, 2, 10, 0)
    assert f["mean floors, ended, real"] == pytest.approx(23.25) and f["mean floors, counted (crash = 0), real"] == pytest.approx(18.6)
    assert f["mean floors, ended, emulator"] == pytest.approx(21.1)
    assert (f["Act 1 boss reached, real"], f["Act 1 boss killed, real"]) == (5, 3)
    assert f["Act 1 boss killed, share of runs, real"] == pytest.approx(3 / 8)
    assert f["Act 1 boss killed, share of those reached, real"] == pytest.approx(0.6)
    assert (f["Act 1 boss reached, emulator"], f["Act 1 boss killed, emulator"]) == (7, 4)
    assert f["seeds with rows, both arms"] == 10 and f["paired seeds, ended on both arms"] == 8
    assert sum(v for k, v in f.items() if k.startswith("crash rows of kind")) == 2


def test_check_matches_on_the_generation_9_night():
    text, code = mr.run_check(LAB / "nightly" / "2026-11-03", None, LAB, NOW)
    assert code == 0 and "0 mismatches" in text and "crash rows of kind" in text


def test_check_exits_1_and_names_the_figure_when_a_path_differs(monkeypatch, capsys):
    real = mr.independent_figures

    def off_by_one(night, agent):
        out = real(night, agent)
        out["ended runs, real"] += 1
        out["mean floors, counted (crash = 0), real"] += 0.01
        return out

    monkeypatch.setattr(mr, "independent_figures", off_by_one)
    text, code = mr.run_check(NIGHT, None, LAB, NOW)
    assert code == 1 and text.count("MISMATCH") == 2 and "2 mismatches: ended runs, real; mean floors, counted" in text
    assert mr.main([str(NIGHT), "--check", "--now", "2026-11-04T01:00:00Z"]) == 1
    assert "MISMATCH" in capsys.readouterr().out


def test_check_cli_prints_both_paths_and_no_paths(capsys):
    assert mr.main([str(NIGHT), "--check", "--now", "2026-11-04T01:00:00Z"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("morning_report --check: night 2026-11-04 (g11)") and "path 1" in out and "path 2" in out
    for bad in (str(FIX), str(FIX).replace("\\", "/"), "Users", "pmpal", "C:\\"):
        assert bad not in out, bad


def test_check_rows_compare_counts_exactly_and_rates_to_the_reports_rounding():
    rows = {r["figure"]: r["ok"] for r in mr.check_rows(
        {"a": 5, "b": 0.5521, "c": None, "d": 1, "e": 2.0},
        {"a": 6, "b": 0.55213, "c": None, "f": 3, "e": 2.0001})}
    assert rows == {"a": False, "b": True, "c": True, "d": False, "f": False, "e": False}


def test_second_path_crash_labels_agree_with_the_reports():
    for err in ("RuntimeError: the engine refused action 6 in phase 5", "GameDied: game exited (3221225477)",
                "worker process exited 1 (0x1)", "worker deadline 3600 s", "TimeoutError('no message in 180 s')",
                "ValueError: something else", ""):
        assert mr._crash_label(err) == mr.crash_kind(err)["kind"], err


def test_second_path_skips_torn_lines_and_reads_missing_files(tmp_path):
    arm = tmp_path / "g1"
    arm.mkdir()
    (arm / "runs.jsonl").write_text(
        '{"ev": "end", "seed": "A", "floor": 10, "boss_damage_acts": [[0, 1.0]]}\n'
        '{"ev": "end", "seed": "B", "floor": 20, "boss_damage_acts": [[0, 0.4], [1, 0.2]]}\n'
        '{"ev": "crash", "seed": "C", "error": "TimeoutError(\'x\')"}\n{"ev": "end", "seed": "D", "fl\n', encoding="utf-8")
    f = mr.independent_figures(tmp_path, "g1")  # no emulator arm file at all
    assert (f["ended runs, real"], f["crash rows, real"], f["seeds with rows, real arm"]) == (2, 1, 3)
    assert f["mean floors, ended, real"] == 15 and f["mean floors, counted (crash = 0), real"] == pytest.approx(10.0)
    assert (f["Act 1 boss reached, real"], f["Act 1 boss killed, real"]) == (2, 1)
    assert f["ended runs, emulator"] == 0 and f["mean floors, ended, emulator"] is None
    assert f["Act 1 boss agreement of the arms"] is None


# ---------------------------------------------------------------------------------------------------- --out in every mode, absent ranks
def test_check_with_out_writes_the_files_and_keeps_the_table_and_exit_code(tmp_path, capsys):
    out = tmp_path / "rep"
    assert mr.main([str(NIGHT), "--check", "--now", "2026-11-04T01:00:00Z", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("morning_report --check: night 2026-11-04 (g11)") and "0 mismatches" in printed
    assert "wrote morning_report.json, handoff_line.md, edition_figures.md" in printed
    assert {"edition_figures.md", "handoff_line.md", "morning_report.json"} <= {p.name for p in out.iterdir()}
    data = json.loads((out / "morning_report.json").read_text(encoding="utf-8"))
    assert data["night"]["folder"] == "nightly/2026-11-04" and data["real"]["ended"] == 8
    blob = "".join((out / n).read_text(encoding="utf-8") for n in ("morning_report.json", "handoff_line.md", "edition_figures.md"))
    for bad in (str(FIX), str(FIX).replace("\\", "/"), "Users", "pmpal", "C:\\", ":/"):
        assert bad not in blob, bad


def test_check_with_out_still_exits_1_on_a_mismatch_and_writes(tmp_path, monkeypatch, capsys):
    real = mr.independent_figures

    def off_by_one(night, agent):
        out = real(night, agent)
        out["ended runs, real"] += 1
        return out

    monkeypatch.setattr(mr, "independent_figures", off_by_one)
    out = tmp_path / "rep"
    assert mr.main([str(NIGHT), "--check", "--now", "2026-11-04T01:00:00Z", "--out", str(out)]) == 1
    assert "MISMATCH" in capsys.readouterr().out and (out / "morning_report.json").is_file()


def test_check_without_out_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert mr.main([str(NIGHT), "--check", "--now", "2026-11-04T01:00:00Z"]) == 0
    assert "wrote " not in capsys.readouterr().out and list(tmp_path.iterdir()) == []


def test_chance_read_with_out_writes_the_report_files_beside_the_reading(tmp_path, capsys):
    out = tmp_path / "rep"
    assert mr.main([str(NIGHT), "--chance-read", "--now", "2026-11-04T01:00:00Z", "--winlog", "none", "--out", str(out)]) == 0
    names = {p.name for p in out.iterdir()}
    assert {"chance_reading.md", "chance_reading.json", "morning_report.json", "handoff_line.md", "edition_figures.md"} <= names
    assert "wrote " in capsys.readouterr().out


def test_a_missing_rank_reads_absent_not_none(rep):
    import copy

    r = copy.deepcopy(rep)
    r["groups"]["d11c"]["Strike"].update(rank=None, weight=0, records=0)
    for text in (mr.edition_figures(r), mr.handoff_line(r)):
        assert "Strike absent" in text and "rank None" not in text and "Defend rank 3" in text
    assert "Strike rank 2" in mr.edition_figures(rep)
    assert mr.rank_text("Strike", None) == "Strike absent" and mr.rank_text("Defend", 7) == "Defend rank 7"


# ---------------------------------------------------------------------------------------------------- keep test v2: headline, confirmation, ledger
LEDGER_V1 = ("written", "cand_gen", "base_gen", "seed_block", "seeds", "d_floor", "floor_lower", "p_floor", "boss_cand", "boss_base", "p_boss",
             "wins_cand", "wins_base", "decision", "cand_sha", "cand_dir", "attempt", "drift", "guard", "run_head_sha", "macro")
LEDGER_V2 = LEDGER_V1 + ("rule", "frontier", "route", "k2_cand", "k2_base", "d_deep", "deep_lower", "p_deep", "floor_lower95")
OLD_ROW = {"written": "2026-11-05T17:49:35Z", "cand_gen": "12", "base_gen": "11", "seed_block": "E12-2026-11-05-r3", "seeds": "2000", "d_floor": "-0.3060",
           "floor_lower": "-0.7660", "p_floor": "0.93900", "boss_cand": "965", "boss_base": "1043", "p_boss": "0.99944", "wins_cand": "0", "wins_base": "0",
           "decision": "rejected", "cand_dir": "candidate-imit-l05", "attempt": "1", "drift": "clear", "guard": "kill FIRES"}
V2_ROW = {**OLD_ROW, "written": "2026-11-06T01:02:03Z", "decision": "promoted", "rule": "v2", "frontier": "B2", "route": "A", "k2_cand": "107", "k2_base": "49",
          "d_deep": "3.0500", "deep_lower": "1.5000", "p_deep": "0.00005", "floor_lower95": "-0.6325"}


def write_ledger(path: Path, header: tuple[str, ...], rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\t".join(header) + "\n" + "".join("\t".join(r.get(c, "") for c in header) + "\n" for r in rows), encoding="utf-8")
    return path


def test_headline_is_act2_kills_per_100_runs(rep):
    # the night: 1 Act 2 boss kill in 8 ended runs; generation 9 pooled over its two nights: 1 in 9 (the fixture's hand-worked rows)
    assert mr.PROGRESS[0][0] == "act2_of_runs" and mr.PROGRESS[0][2] == "points"
    m = rep["progress"]["measures"]["act2_of_runs"]
    p1, p2 = 1 / 8, 1 / 9
    se = math.sqrt(p1 * (1 - p1) / 8 + p2 * (1 - p2) / 9)
    assert m["value"] == pytest.approx(12.5) and m["n"] == 8 and m["se"] == pytest.approx(100 * math.sqrt(p1 * (1 - p1) / 8), abs=1e-3)
    d = rep["progress"]["previous_generation_pooled"]["diffs"]["act2_of_runs"]
    assert d["diff"] == pytest.approx(100 * (p1 - p2), abs=1e-2) and d["se"] == pytest.approx(100 * se, abs=1e-2) and d["z"] == pytest.approx((p1 - p2) / se, abs=2e-3)
    assert rep["progress"]["previous_night"]["diffs"]["act2_of_runs"]["diff"] is not None
    head = rep["act2_headline"]
    assert head.startswith("Act 2 boss beaten per 100 runs: 12.50 (1 of 8 ended runs); generation 9 pooled over its 2 real-arm nights 11.11 (1 of 9); "
                           "difference +1.39 points (SE ")
    assert f"z {(p1 - p2) / se:+.1f})" in head
    # it comes first: in the HANDOFF line (after the preamble and the run times), in the edition list, in the progress score
    line = mr.handoff_line(rep)
    assert line.index(f"**{head}.**") < line.index("**Generation 11, real arm")
    assert line.startswith("- 2026-11-04T01:00Z morning_report.py")
    edition = mr.edition_figures(rep)
    assert edition.splitlines()[2] == f"- {head}"
    assert mr.progress_lines(rep)[1].startswith("- Act 2 boss beaten (of runs): 12.5 (SE ")
    assert "against the previous generation pooled (" in mr.progress_lines(rep)[1]
    # a night whose rows did not record the boss fights has no headline figure, not a zero
    import copy

    r = copy.deepcopy(rep)
    r["progress"]["measures"]["boss_recorded"] = False
    assert mr.act2_headline(r) == "Act 2 boss beaten per 100 runs: unknown (this night's rows did not record the boss fights)"
    r = copy.deepcopy(rep)
    r["comparison"]["previous_generation_pooled"] = None
    assert mr.act2_headline(r).endswith("(1 of 8 ended runs); no earlier generation to compare with")
    # the second path agrees with the report on the new measure
    text, code = mr.run_check(NIGHT, None, LAB, NOW, rep)
    assert code == 0 and "progress: Act 2 boss beaten (of runs) (points), value" in text and "MISMATCH" not in text


def _pools(night_kills: int, night_runs: int, night_floor: float, pool_kills: int, pool_runs: int, pool_floor: float, sd: float = 8.8) -> dict:
    """A comparison entry from two pools' sums (the report's own `compare_blocks`), for the confirmation's arithmetic."""
    def agg(kills, runs, floor):
        total = round(floor * runs)
        return mr.Agg(n=runs, s=total, ss=round(sd * sd * (runs - 1) + total * total / runs), a2k=kills)

    cur, base = agg(night_kills, night_runs, night_floor), agg(pool_kills, pool_runs, pool_floor)
    return {"generation": 11, "nights": ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"], "real": mr.compare_blocks(cur, base),
            "emu": None}


def _rep_for(entry: dict | None, kills: int, runs: int, floor: float, generation: int = 12, earlier: bool = False) -> dict:
    return {"night": {"generation": generation}, "progress": {"measures": {"boss_recorded": True}}, "real": {"act2_killed": kills, "ended": runs, "mean_floor": floor},
            "comparison": {"previous_generation_pooled": entry, "same_generation_earlier": {"nights": ["x"]} if earlier else None}}


def test_confirmation_block_after_route_a_promotion(tmp_path):
    rows = [{**V2_ROW, "cand_gen": "12", "decision": "promoted"}]
    # the design's example: generation 11's pool 119 in 3,500 runs (3.40 per 100, floor 23.33); the night, at the copy's ratio, about 7.4
    ok = mr.confirmation_block(_rep_for(_pools(148, 2000, 23.2, 119, 3500, 23.33), 148, 2000, 23.2), rows)
    assert ok["verdict"] == "confirmed" and ok["failed"] == [] and ok["route"] == "A" and ok["generation"] == 12 and ok["previous_generation"] == 11
    a = ok["act2"]
    assert (a["night_per_100"], a["pool_per_100"], a["pool_kills"], a["pool_runs"]) == (7.4, 3.4, 119, 3500)
    se = 100 * math.sqrt(0.074 * 0.926 / 2000 + (119 / 3500) * (1 - 119 / 3500) / 3500)
    assert a["diff_pts"] == pytest.approx(4.0, abs=1e-3) and a["lower95"] == pytest.approx(4.0 - 1.645 * se, abs=2e-3) and a["holds"] is True
    assert ok["floor"]["diff"] == pytest.approx(-0.13, abs=1e-3) and ok["floor"]["holds"] is True
    text = mr.confirmation_text(ok)
    assert "Confirmation of the route A promotion of generation 12 (E12-2026-11-05-r3; frontier B2): **confirmed.**" in text
    assert "7.40 per 100 runs (148 of 2,000) against generation 11 pooled 3.40 (119 of 3,500): +4.00 points" in text and "needs above 0" in text
    # not confirmed: the Act 2 boss rate does not beat the pool's (lower bound under 0) ...
    bad = mr.confirmation_block(_rep_for(_pools(80, 2000, 23.2, 119, 3500, 23.33), 80, 2000, 23.2), rows)
    assert bad["verdict"] == "NOT confirmed" and bad["failed"] == ["the Act 2 boss rate"] and bad["act2"]["holds"] is False and bad["floor"]["holds"] is True
    assert "restores the previous current.json" in mr.confirmation_text(bad)
    # ... or the mean floor is more than 1.0 under the pool's at 95% (here -1.3, SE 0.27: lower bound -1.7)
    low = mr.confirmation_block(_rep_for(_pools(148, 2000, 22.03, 119, 3500, 23.33), 148, 2000, 22.03), rows)
    assert low["verdict"] == "NOT confirmed" and low["failed"] == ["the mean floor"] and low["floor"]["lower95"] < -1.0
    # no previous generation to pool: not measured, never confirmed
    assert mr.confirmation_block(_rep_for(None, 148, 2000, 23.2), rows)["verdict"] == "not measured"
    # it applies only to the first night after a route A promotion by the rule v2 of this generation
    entry = _pools(148, 2000, 23.2, 119, 3500, 23.33)
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2, earlier=True), rows) is None  # not the first night
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2, generation=13), rows) is None  # another generation
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2), [{**rows[0], "route": "F"}]) is None  # route F is not confirmed in the game
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2), [{**rows[0], "route": "AF"}])["verdict"] == "confirmed"
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2), [{**rows[0], "rule": ""}]) is None  # a v1 promotion
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2), [{**rows[0], "decision": "rejected"}]) is None
    assert mr.confirmation_block(_rep_for(entry, 148, 2000, 23.2), []) is None
    # through the report: the fixture's night is generation 11, the first of its generation; with a route A row in a ledger it carries the block
    ledger = write_ledger(tmp_path / "agent" / "promotions.tsv", LEDGER_V2, [{**V2_ROW, "cand_gen": "11", "decision": "promoted"}])
    r = mr.build_report(NIGHT, None, LAB, LOGS, str(WINLOG), "test usage", NOW, agent_root=ledger.parent)
    c = r["confirmation"]
    assert c["applies"] is True and c["generation"] == 11 and c["previous_generation"] == 9 and c["act2"]["night_kills"] == 1 and c["act2"]["pool_runs"] == 9
    assert c["verdict"] == "NOT confirmed"  # 8 runs against 9: nothing can be confirmed on a toy night
    assert "Confirmation of the route A promotion of generation 11" in mr.handoff_line(r)
    assert f"- {mr.confirmation_text(c)}" in mr.edition_figures(r)
    # without a ledger, or with one that holds no such promotion, the block is absent and the report is as before
    plain = mr.build_report(NIGHT, None, LAB, LOGS, str(WINLOG), "test usage", NOW)
    assert plain["confirmation"] is None and "Confirmation of" not in mr.handoff_line(plain)
    other = write_ledger(tmp_path / "other" / "promotions.tsv", LEDGER_V2, [{**V2_ROW, "cand_gen": "11", "decision": "promoted", "route": "F"}])
    assert mr.build_report(NIGHT, None, LAB, LOGS, str(WINLOG), "test usage", NOW, agent_root=other.parent)["confirmation"] is None


def test_ledger_line_reads_old_and_v2_rows(tmp_path, capsys):
    # an old file (no v2 columns): the newest row reads as v1, the floor figures stand and the Act 2 boss is said not to be recorded
    old = write_ledger(tmp_path / "old" / "promotions.tsv", LEDGER_V1, [OLD_ROW])
    led = mr.ledger_figures(mr.read_ledger(old))
    assert led["available"] and led["rule"] == "v1" and led["decision"] == "rejected" and led["route"] is None and led["k2_cand"] is None
    assert led["line"] == ("Newest ledger row (2026-11-05T17:49Z, block E12-2026-11-05-r3, generation 12 against 11, 2000 seeds): rule v1 (the floor test), "
                           "floor -0.31 (99% lower bound -0.77), Act 1 boss 965 against 1043, Act 2 boss kills not recorded in the row, decision rejected.")
    # a file with the v2 columns whose newest row is v2: rule, frontier, route, K2, deep_f and its bound, the floor bound, the decision
    new = write_ledger(tmp_path / "new" / "promotions.tsv", LEDGER_V2, [OLD_ROW, V2_ROW])
    led = mr.ledger_figures(mr.read_ledger(new))
    assert led["rule"] == "v2" and led["rows"] == 2 and (led["frontier"], led["route"], led["k2_cand"], led["k2_base"]) == ("B2", "A", "107", "49")
    assert (led["d_deep"], led["deep_lower"], led["floor_lower95"]) == (3.05, 1.5, -0.6325)
    assert led["line"] == ("Newest ledger row (2026-11-06T01:02Z, block E12-2026-11-05-r3, generation 12 against 11, 2000 seeds): rule v2, frontier B2, "
                           "route A, Act 2 boss 107 against 49, deep +3.05 per 100 (0.005 bound +1.50), floor 95% lower bound -0.63, decision promoted.")
    # the same file when an old row is the newest (its nine cells are empty): v1 again; and a v2 row that took no route reads "route none"
    mixed = write_ledger(tmp_path / "mixed" / "promotions.tsv", LEDGER_V2, [V2_ROW, OLD_ROW])
    assert mr.ledger_figures(mr.read_ledger(mixed))["rule"] == "v1"
    refused = write_ledger(tmp_path / "refused" / "promotions.tsv", LEDGER_V2, [{**V2_ROW, "route": "", "decision": "rejected"}])
    assert "route none" in mr.ledger_figures(mr.read_ledger(refused))["line"]
    # a torn or missing figure reads "n/a", a missing file says so
    odd = write_ledger(tmp_path / "odd" / "promotions.tsv", LEDGER_V2, [{**V2_ROW, "d_deep": "", "floor_lower95": "x"}])
    odd_line = mr.ledger_figures(mr.read_ledger(odd))["line"]
    assert "deep n/a per 100" in odd_line and "floor 95% lower bound n/a" in odd_line
    assert mr.ledger_figures(mr.read_ledger(tmp_path / "none" / "promotions.tsv")) == {"available": False, "line": "no promotions ledger was found"}
    # in the report: the line is in the HANDOFF line, the edition list and the JSON, and no path is
    out = tmp_path / "rep"
    assert mr.main([str(NIGHT), "--winlog", str(WINLOG), "--now", "2026-11-04T01:00:00Z", "--agent-root", str(new.parent), "--out", str(out)]) == 0
    capsys.readouterr()
    for name in ("handoff_line.md", "edition_figures.md"):
        assert led["line"] in (out / name).read_text(encoding="utf-8"), name
    data = json.loads((out / "morning_report.json").read_text(encoding="utf-8"))
    assert data["ledger"]["rule"] == "v2" and data["confirmation"] is None  # the ledger's promoted row is generation 12; the night is 11
    blob = "".join((out / n).read_text(encoding="utf-8") for n in ("morning_report.json", "handoff_line.md", "edition_figures.md"))
    for bad in (str(tmp_path), str(tmp_path).replace("\\", "/"), "Users", "pmpal", "C:\\"):
        assert bad not in blob, bad
    # without a ledger beside the lab the report says so and is otherwise unchanged
    assert mr.build_report(NIGHT, None, LAB, LOGS, str(WINLOG), "test usage", NOW)["ledger"] == {"available": False, "line": "no promotions ledger was found"}


# ---------------------------------------------------------------------------------------------------- night folders named by start time
def test_night_folders_named_by_date_or_by_start_time_are_both_nights(tmp_path):
    for name in ("2026-11-05", "2026-11-06", "2026-11-06T0312", "2026-11-06T2359"):
        (tmp_path / name).mkdir()
    for name in ("last-ok", "pending", "2026-11-06T03", "2026-11-06-g4"):
        (tmp_path / name).mkdir()
    (tmp_path / "2026-11-07").write_text("a file, not a night")
    assert [p.name for p in mr.list_nights(tmp_path)] == ["2026-11-05", "2026-11-06", "2026-11-06T0312", "2026-11-06T2359"]


def test_a_block_named_by_its_start_time_is_reported_like_a_dated_night(tmp_path):
    import shutil

    lab = tmp_path / "referee" / "LAB"
    shutil.copytree(LAB, lab)
    new = "2026-11-04T0312"
    shutil.move(str(lab / "nightly" / "2026-11-04"), str(lab / "nightly" / new))
    for d in (lab / "runs").glob("*-nightly-real"):  # the job record names its block by the result's date
        res = json.loads((d / "result.json").read_text(encoding="utf-8")) if (d / "result.json").is_file() else None
        if res and res.get("date") == "2026-11-04":
            res["date"] = new
            (d / "result.json").write_text(json.dumps(res), encoding="utf-8")
    night = lab / "nightly" / new
    assert [p.name for p in mr.list_nights(lab / "nightly")][-1] == new
    r = mr.build_report(night, None, lab, None, "none", None, NOW)
    assert r["night"]["date"] == new and r["night"]["folder"] == f"nightly/{new}"
    assert r["night"]["job"]["name"] == "20261103T2000-nightly-real"  # found by the result's date
    assert r["real"]["ended"] == 8 and r["runs"]["real_rows"] == 10
    assert all(c["ok"] is not False for c in r["cross_checks"])
    # the earlier nights are still its history (they sort before it), and a block of the same day does not hide them
    assert r["tables"]["prev_night_date"] == "2026-11-03"
