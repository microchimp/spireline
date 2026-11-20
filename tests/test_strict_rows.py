"""The strict reading of a real-game row when the referee lost track of the game (tools/strict_rows.py, Act 3 week, lane 8).

A lost row is credited with the bosses whose floor is below the floor where tracking was lost and with nothing at or after it; a crash row
with nothing; a clean row above floor 48 with all three. The three readers (morning_report, boss_entry, weekly_numbers) and the morning
report's `--check` second path must agree row by row."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import boss_entry as be  # noqa: E402
import morning_report as mr  # noqa: E402
import strict_rows as sr  # noqa: E402
import weekly_numbers as wn  # noqa: E402

FULL = [[0, 1.0], [1, 1.0], [2, 1.0]]


def real_row(floor: int, loss_at: int | None = None, *, end: str = "death", bar=FULL, decision: int = 100, **extra) -> dict:
    """A real-game row. `loss_at`: the floor where the referee lost track (a `lost` row with its first_loss and divergence entry)."""
    row: dict = {"ev": "end", "seed": "S", "end": end, "floor": floor, "boss_damage_acts": [list(e) for e in bar]}
    if loss_at is not None:
        row["lost"] = "state_diverged"
        row["stats"] = {"first_loss": {"decision": decision, "reason": "state_diverged"}}
        row["divergences"] = [{"decision": decision - 40, "floor": max(loss_at - 5, 1)}, {"decision": decision, "floor": loss_at}]
    row.update(extra)
    return row


def passed(row: dict) -> tuple[bool, bool, bool]:
    return tuple(sr.went_past(row, a) for a in (0, 1, 2))  # type: ignore[return-value]


# ---------------------------------------------------------------------------------------------------- the rule
def test_a_lost_row_counts_the_bosses_below_the_loss_floor_and_nothing_at_or_after_it():
    assert passed(real_row(50, 29)) == (True, False, False)  # lost on floor 29, ended on 50 with a full bar: Act 1 only
    assert passed(real_row(30, 29)) == (True, False, False)
    assert passed(real_row(50, 10)) == (False, False, False)  # lost on floor 10: nothing, whatever the ending floor
    assert passed(real_row(50, 17)) == (False, False, False)  # lost on the Act 1 boss's own floor: it was played by the stand-in in part
    assert passed(real_row(50, 18)) == (True, False, False)
    assert passed(real_row(50, 34)) == (True, True, False)
    assert passed(real_row(50, 48)) == (True, True, False)  # lost at the first Act 3 boss: not credited
    assert passed(real_row(50, 49)) == (True, True, True)  # lost on the second Act 3 boss's floor: the first one is credited


def test_a_crash_row_counts_nothing_and_a_clean_row_above_48_counts_all_three():
    assert passed({"ev": "crash", "seed": "S", "error": "GameDied: x", "floor": 50, "boss_damage_acts": FULL}) == (False, False, False)
    assert passed({"crash": True, "floor": 50, "boss_damage_acts": FULL}) == (False, False, False)
    assert passed(real_row(49)) == (True, True, True)
    assert passed(real_row(48)) == (True, True, False)  # on the first Act 3 boss's floor: not past it
    assert passed(real_row(48, bar=[[0, 1.0], [1, 1.0]])) == (True, True, False)


def test_a_lost_row_whose_loss_floor_cannot_be_read_counts_nothing_and_is_counted_unknown():
    no_first_loss = real_row(50, 29)
    del no_first_loss["stats"]
    assert sr.loss_floor(no_first_loss) is None and passed(no_first_loss) == (False, False, False)
    assert sr.loss_floor_unknown(no_first_loss)
    no_entry = real_row(50, 29)
    no_entry["divergences"] = []
    assert sr.loss_floor(no_entry) is None and passed(no_entry) == (False, False, False) and sr.loss_floor_unknown(no_entry)
    no_floor = real_row(50, 29)
    for e in no_floor["divergences"]:
        e["floor"] = None
    assert sr.loss_floor(no_floor) is None and sr.loss_floor_unknown(no_floor)
    assert not sr.loss_floor_unknown(real_row(50, 29)) and not sr.loss_floor_unknown(real_row(50))
    # the copy arm's lost worker (no ev, floor 0, no data) is not a tracking loss and is not counted
    worker = {"seed": "S", "floor": 0, "end": "lost", "lost": True, "win": False}
    assert not sr.loss_floor_unknown(worker) and passed(worker) == (False, False, False)


def test_the_loss_floor_is_the_entry_of_the_first_loss_decision_else_the_last_entry_before_it():
    row = real_row(50, 29, decision=200)
    row["divergences"] = [{"decision": 50, "floor": 9}, {"decision": 150, "floor": 25}, {"decision": 200, "floor": 29}, {"decision": 300, "floor": 41}]
    assert sr.loss_floor(row) == 29  # the entry of the decision itself, not the later ones
    row["divergences"] = [{"decision": 50, "floor": 9}, {"decision": 150, "floor": 25}, {"decision": 300, "floor": 41}]
    assert sr.loss_floor(row) == 25  # no entry for decision 200: the last one at or before it
    row["divergences"] = [{"decision": 150, "floor": None}, {"decision": 160, "floor": 26}, {"decision": 300, "floor": 41}]
    assert sr.loss_floor(row) == 26
    assert sr.loss_floor(real_row(50)) is None  # a row that did not end lost has no loss floor


def test_deadline_rows_are_read_by_floor_and_wins_count_every_boss_below_a_known_loss_floor():
    assert passed(real_row(48, 48, end="fight_unfinished")) == (True, True, False)
    assert passed(real_row(49, 49, end="fight_unfinished")) == (True, True, True)
    assert passed(real_row(39, end="fight_unfinished", bar=[[0, 1.0], [1, 1.0]])) == (True, True, False)
    assert passed(real_row(49, end="victory")) == (True, True, True)  # the real game's end message for a won run
    assert passed(real_row(49, 30, end="victory")) == (True, False, False)  # a won run the stand-in finished: only what the agent played
    assert sr.is_win(real_row(49, end="victory")) and sr.is_win({"win": True}) and sr.is_win({"end": "win"}) and not sr.is_win({"end": "death"})


def test_the_bar_rule_and_the_complete_room_string_still_apply():
    assert passed(real_row(35, bar=[[0, 1.0], [1, 0.8]])) == (True, False, False)  # a lost fight is never beaten
    long_act2 = "M" * 15 + "B" + "A" + "M" * 16 + "B" + "A" + "M" * 13 + "B"  # boss floors 17, 35, 50
    assert passed(real_row(50, nodes=long_act2)) == (True, True, False)
    assert passed(real_row(50, 36, nodes=long_act2)) == (True, True, False)
    assert passed(real_row(50, 35, nodes=long_act2)) == (True, False, False)  # lost on the Act 2 boss's own floor (35 here)
    assert passed({"floor": "x", "boss_damage_acts": [["a", None], 5]}) == (False, False, False)  # malformed rows read as nothing, no raise


# ---------------------------------------------------------------------------------------------------- the readers agree
ROWS = [real_row(50, 29), real_row(30, 29), real_row(50, 10), real_row(50, 17), real_row(50, 34), real_row(50, 48), real_row(50, 49),
        real_row(49), real_row(48), real_row(48, 48, end="fight_unfinished"), real_row(49, 49, end="fight_unfinished"),
        real_row(49, end="victory"), real_row(49, 30, end="victory"), real_row(20, bar=[[0, 1.0]]), real_row(12, bar=[[0, 1.0]]),
        real_row(35, bar=[[0, 1.0], [1, 0.8]]), real_row(50, 29, nodes="M" * 49), {"ev": "crash", "seed": "S", "error": "x"},
        {"seed": "S", "floor": 0, "end": "lost", "lost": True, "win": False}, real_row(50, 20, stats={"first_loss": {"decision": 7}})]


def test_the_three_readers_and_the_second_path_agree_on_every_row():
    for i, row in enumerate(ROWS):
        for act in (0, 1, 2):
            want = sr.went_past(row, act)
            assert mr.went_past(row, act) == want, (i, act)
            assert mr.boss_hit(row, act)[1] == (want and any(e[0] == act for e in row.get("boss_damage_acts") or [])), (i, act)
            assert mr._boss_of_act(row, act)[1] == mr.boss_hit(row, act)[1], (i, act)  # the --check path, written separately
            if "nodes" not in row or act < 2:
                if row.get("ev") != "crash" and "floor" in row:
                    assert be.went_past({**row, "win": sr.is_win(row)}, act) == want, (i, act)
        if row.get("ev") != "crash":
            assert wn.norm_row(row)["passed"] == sr.went_past(row, 2), i
    assert be.night_summary(real_row(50, 29))["a"][0]["k"] == 1 and be.night_summary(real_row(50, 29))["a"][1]["k"] == 0
    assert be.night_summary(real_row(49, end="victory"))["won"] is True


def test_make_agg_counts_the_lost_rows_and_how_many_of_them_now_count_a_boss():
    rows = [real_row(50, 29), real_row(50, 10), real_row(50, 49), real_row(49), real_row(50, 20, stats={"first_loss": {"decision": 7}})]
    g = mr.make_agg(rows)
    assert (g.n, g.lost, g.lost_unknown, g.lost_credited) == (5, 4, 1, 2)
    assert (g.a1k, g.a2k, g.a3k) == (3, 2, 2)  # the clean row, the row lost on 49, and the row lost on 29 (Act 1 only)
    assert g.a1k_plain == 5  # with the loss rule off every row here (full bar, floor above 17) beat the Act 1 boss, as the lab's summary counts
    fig = mr.arm_figures(rows, [], True)
    assert (fig["lost_rows"], fig["lost_loss_floor_unknown"], fig["lost_rows_credited"]) == (4, 1, 2)


def test_check_second_path_matches_the_report_path_on_a_night_of_lost_rows(tmp_path):
    arm = tmp_path / "g1"
    arm.mkdir()
    lines = [json.dumps({**r, "seed": f"S{i}"}) for i, r in enumerate(ROWS)]
    (arm / "runs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    second = mr._arm_second_path(arm / "runs.jsonl", True)
    ended, crashes = mr.split_rows(mr.read_jsonl(arm / "runs.jsonl"), True)
    first = mr.arm_figures(ended, crashes, True)
    for key_first, key_second in (("act1_killed", "act1_killed"), ("act2_killed", "act2_killed"), ("act3_killed", "act3_killed"),
                                  ("act3_reached", "act3_reached"), ("wins", "wins"), ("lost_rows", "lost_rows"),
                                  ("lost_loss_floor_unknown", "lost_unknown"), ("lost_rows_credited", "lost_credited")):
        assert first[key_first] == second[key_second], key_first
    assert first["lost_rows"] > 0 and first["lost_rows_credited"] > 0
