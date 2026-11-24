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


def test_a_stalled_row_is_a_deadline_row_read_by_floor():
    for end in ("fight_unfinished", "stalled"):
        assert sr.is_deadline(real_row(48, end=end))
        assert passed(real_row(48, end=end)) == (True, True, False)  # on the first Act 3 boss's floor: an arrival, not past it
        assert passed(real_row(49, end=end)) == (True, True, True)
        assert passed(real_row(48, 48, end=end)) == (True, True, False)  # lost on the boss's floor: Acts 1 and 2 only
        assert passed(real_row(40, end=end, bar=[[0, 1.0], [1, 1.0]])) == (True, True, False)
    assert not sr.is_deadline(real_row(48)) and not sr.is_deadline({"floor": 3})
    assert wn.norm_row(real_row(48, end="stalled"))["arrived"] and not wn.norm_row(real_row(48, end="stalled"))["passed"]


# ================================================================================================ lane 23: who played the boss fight
# A boss counts as beaten by our player when the run went past it and no decision of its fight was answered by the stand-in. New rows say
# so themselves (`stats.boss_fights`); older rows are read from the loss intervals of their divergence records; rows with neither fall
# back to the first loss (the rule before lane 23).
def rec(decision: int, floor: int, *, room: str = "combat", reanchored: bool = False, last: int | None = None, count: int | None = None,
        encounter: str | None = None) -> dict:
    """A divergence record. A loss (not re-anchored) lasts to `last` (default: its own decision) and carries its not-ranked span."""
    d: dict = {"decision": decision, "floor": floor, "room": room, "type": "combat", "reanchored": reanchored, "encounter": encounter}
    if not reanchored:
        end = decision if last is None else last
        d["not_ranked_span"] = {"first": decision, "last": end, "count": end - decision + 1 if count is None else count}
    return d


def rec_row(floor: int, records: list[dict], *, lost: str | None = None, end: str = "death", bar=FULL, decisions: int = 400, failed: int = 0,
            fights: list[dict] | None = None, **extra) -> dict:
    """A real-game row with divergence records (the shape the fork writes), `lost` when the run ended lost."""
    losses = [d for d in records if not d.get("reanchored")]
    stats: dict = {"decisions": decisions, "reanchor_failed": failed}
    if losses:
        stats["first_loss"] = {"decision": losses[0]["decision"], "reason": "state_diverged"}
        stats["losses"] = {"state_diverged": len(losses)}
    if fights is not None:
        stats["boss_fights"] = fights
    row: dict = {"ev": "end", "seed": "S", "end": end, "floor": floor, "boss_damage_acts": [list(e) for e in bar], "stats": stats,
                 "divergences": records}
    if lost:
        row["lost"] = lost
    row.update(extra)
    return row


def fight(act: int, floor: int, stand_in: int = 0, decisions: int = 20) -> dict:
    return {"act": act, "floor": floor, "first": 100, "decisions": decisions, "stand_in": stand_in, "first_stand_in": 100 if stand_in else None}


def first_loss_reading(row: dict) -> tuple[bool, bool, bool]:
    return tuple(sr.went_past_first_loss(row, a) for a in (0, 1, 2))  # type: ignore[return-value]


# ---------------------------------------------------------------------------------------------------- the boss-fight record (new rows)
def test_a_boss_fight_with_no_stand_in_decision_is_the_players_and_a_lost_row_keeps_it():
    # lost at floor 10 and recovered before the bosses, lost again at the second Act 3 boss: the old reading credits nothing, the record all three
    row = rec_row(50, [rec(40, 10, last=44), rec(350, 49, last=399)], lost="state_diverged",
                  fights=[fight(0, 17), fight(1, 33), fight(2, 48), fight(2, 49, stand_in=12)])
    assert first_loss_reading(row) == (False, False, False)
    assert passed(row) == (True, True, True)
    assert [sr.fight_reading(row, a) for a in (0, 1, 2)] == [(True, "boss_fights")] * 3
    assert sr.row_basis(row) == "boss_fights"


def test_a_fight_the_stand_in_answered_part_of_is_not_credited_whatever_the_floor_says():
    row = rec_row(50, [], fights=[fight(0, 17), fight(1, 33, stand_in=3), fight(2, 48, stand_in=1), fight(2, 49)])
    assert passed(row) == (True, False, False)  # never lost at the end, but the search gave nothing in two fights: those are the stand-in's
    assert sr.fought_by_player(row, 0) and not sr.fought_by_player(row, 1) and not sr.fought_by_player(row, 2)
    # a fight that was split in two entries (a non-fight decision between its decisions) counts only when both are clean
    split = rec_row(50, [], fights=[fight(2, 48), fight(2, 48, stand_in=2)])
    assert passed(split)[2] is False


def test_a_boss_fight_entry_beats_the_loss_records_and_a_missing_entry_falls_back_to_them():
    covered = rec_row(50, [rec(300, 48, last=399)], lost="state_diverged", fights=[fight(2, 48)])  # the record says the player played it
    assert passed(covered)[2] is True
    missing = rec_row(50, [rec(300, 48, last=399)], lost="state_diverged", fights=[fight(0, 17)])  # no entry for floor 48: the loss records decide
    assert passed(missing)[2] is False and sr.fight_reading(missing, 2) == (False, "loss_records")
    assert sr.fight_reading(missing, 0) == (True, "boss_fights")


def test_a_boss_that_the_run_did_not_get_past_is_not_credited_but_its_fight_can_still_be_the_players():
    row = rec_row(48, [], fights=[fight(2, 48, decisions=40)], bar=[[0, 1.0], [1, 1.0], [2, 0.4]])  # died in the fight, the player played all of it
    assert passed(row) == (True, True, False) and sr.fought_by_player(row, 2) and sr.arrived(row)
    lost_in = rec_row(48, [rec(300, 48, last=340)], lost="state_diverged", fights=[fight(2, 48, stand_in=20)], bar=[[0, 1.0], [1, 1.0], [2, 0.4]])
    assert passed(lost_in)[2] is False and not sr.fought_by_player(lost_in, 2)


# ---------------------------------------------------------------------------------------------------- the loss records (old rows)
def test_a_loss_recovered_before_the_boss_and_a_loss_at_the_second_boss_do_not_void_the_first_boss():
    row = rec_row(50, [rec(100, 20, last=105), rec(330, 49, last=399)], lost="state_diverged")
    assert first_loss_reading(row) == (True, False, False)  # the first loss was at floor 20: nothing at or after it
    assert passed(row) == (True, True, True)
    assert sr.fight_reading(row, 2) == (True, "loss_records") and sr.row_basis(row) == "loss_records"
    assert sr.reading_change(row, 2) == (False, True, "recovered before the fight; lost at the second boss")


def test_a_loss_that_opened_inside_the_boss_fight_or_before_it_and_never_recovered_covers_the_fight():
    assert passed(rec_row(48, [rec(300, 48, last=399)], lost="state_diverged"))[2] is False  # inside the fight
    in_fight_recovered = rec_row(50, [rec(300, 48, last=310)])  # not lost at the end: opened in the fight, recovered after it
    assert passed(in_fight_recovered) == (True, True, False)
    assert sr.reading_change(in_fight_recovered, 2) == (True, False, "a loss inside the fight, recovered after it")
    before = rec_row(50, [rec(100, 30, last=399)], lost="state_diverged")  # lost at floor 30 and never recovered: the stand-in played the rest
    assert passed(before) == (True, False, False)
    assert sr.fight_reading(before, 2) == (False, "loss_records")


def test_a_loss_recovered_before_the_first_act_3_boss_never_covers_it_and_one_on_the_reward_screens_is_after_the_fight():
    assert passed(rec_row(50, [rec(100, 20, last=105)])) == (True, True, True)
    assert passed(rec_row(50, [rec(280, 47, last=300)])) == (True, True, True)  # recovered at the boss's own fight start
    rewards = rec_row(49, [rec(390, 17, room="non_combat", last=399)], lost="state_diverged")  # a loss on the Act 1 boss floor's reward screens
    assert passed(rewards) == (True, False, False)  # lost at 17 and never recovered: Act 1 played in full, nothing after
    assert first_loss_reading(rewards) == (False, False, False)  # the old rule read the loss floor as the boss's own
    after = rec_row(49, [rec(390, 48, room="non_combat", last=399)], lost="state_diverged")
    assert passed(after)[2] is True and sr.reading_change(after, 2) == (False, True, "lost after the fight")


def test_a_longer_act_3_map_moves_the_first_boss_one_floor_on():
    long_map = rec_row(50, [rec(300, 48, last=310, encounter="FROG_KNIGHT")])  # floor 48 held an ordinary fight; the boss is on 49
    assert passed(long_map)[2] is True
    boss_lost = rec_row(50, [rec(300, 48, last=310, encounter="FROG_KNIGHT"), rec(330, 49, last=340, encounter="TEST_SUBJECT")])
    assert passed(boss_lost)[2] is False  # a loss inside the real boss's fight, on 49
    plain = rec_row(50, [rec(300, 48, last=310, encounter="TEST_SUBJECT")])
    assert passed(plain)[2] is False  # the ordinary map: floor 48's fight is the boss's


def test_for_the_first_two_bosses_a_recovered_loss_counts_only_when_it_could_have_run_past_the_boss():
    # lost at floor 15 for 3 decisions and recovered; the run is past the Act 1 boss (floor 17): the loss was too short to reach it
    assert passed(rec_row(30, [rec(100, 15, last=102)], bar=[[0, 1.0]]))[0] is True
    # 31 decisions from floor 31, the Act 2 boss on 33, and a failed re-anchor in the run: it could have lasted into the fight
    row = rec_row(40, [rec(100, 31, last=130)], bar=[[0, 1.0], [1, 1.0]], failed=2)
    assert sr.fight_reading(row, 1) == (False, "unclear") and passed(row)[1] is False
    assert sr.reading_change(row, 1) == (True, False, "a loss recovered before the fight may have lasted into it (unclear)")
    assert sr.fight_reading({**row, "stats": {**row["stats"], "reanchor_failed": 0}}, 1) == (True, "loss_records")  # no failed re-anchor: it cannot
    # a later record on or below the boss floor shows the referee tracking again before the fight
    tracked = rec_row(40, [rec(100, 31, last=130), rec(140, 32, reanchored=True)], bar=[[0, 1.0], [1, 1.0]], failed=2)
    assert sr.fight_reading(tracked, 1) == (True, "loss_records")
    # 5 decisions cannot cross the 23 floors between floor 10 and the Act 2 boss
    far = rec_row(40, [rec(100, 10, last=104)], bar=[[0, 1.0], [1, 1.0]], failed=3)
    assert sr.fight_reading(far, 1) == (True, "loss_records")


# ---------------------------------------------------------------------------------------------------- the fallback and the bookkeeping
def test_a_row_without_usable_records_is_read_by_its_first_loss_and_says_so():
    old = real_row(50, 29)  # records without a not-ranked span (this file's old fixtures): the first-loss rule
    assert sr.loss_records(old) is None and sr.row_basis(old) == "first_loss"
    assert passed(old) == first_loss_reading(old) == (True, False, False)
    nothing = real_row(50, 29)
    del nothing["stats"], nothing["divergences"]
    assert sr.row_basis(nothing) == "unreadable" and sr.loss_floor_unknown(nothing) and passed(nothing) == (False, False, False)
    win = real_row(49, end="victory", lost="x")  # a win nothing can place is still a win
    assert sr.row_basis(win) == "unreadable" and passed(win) == (True, True, True)
    clean = real_row(50)
    assert sr.row_basis(clean) == "no_loss" and passed(clean) == (True, True, True)
    recovered_without_records = real_row(50, stats={"first_loss": {"decision": 7}})  # lost track once, rows hold no records, not lost at the end
    assert sr.row_basis(recovered_without_records) == "first_loss" and passed(recovered_without_records) == (True, True, True)


def test_the_plain_reading_ignores_who_played():
    row = rec_row(50, [rec(100, 30, last=399)], lost="state_diverged")
    assert tuple(sr.went_past_plain(row, a) for a in (0, 1, 2)) == (True, True, True)
    assert tuple(sr.went_past(row, a) for a in (0, 1, 2)) == (True, False, False)
    assert not sr.went_past_plain({"ev": "crash", "floor": 50}, 0)


def test_arrivals_are_a_win_or_floor_48_or_an_act_3_bar():
    assert sr.arrived(real_row(48)) and sr.arrived(real_row(50)) and sr.arrived(real_row(49, end="victory"))
    assert sr.arrived(real_row(30, bar=[[0, 1.0], [1, 1.0], [2, 0.3]]))
    assert not sr.arrived(real_row(47, bar=[[0, 1.0], [1, 1.0]])) and not sr.arrived({"ev": "crash", "floor": 50})
    for row in ROWS:
        if row.get("ev") != "crash" and "floor" in row:
            assert sr.arrived(row) == wn.norm_row(row)["arrived"], row  # the weekly table's arrival is this one


def divergence_lines(row: dict) -> str:
    return "\n".join(json.dumps({**d, "seed": row["seed"]}) for d in row["divergences"]) + "\n"


def test_the_block_divergence_file_fills_rows_that_lack_their_records(tmp_path):
    arm = tmp_path / "g1"
    arm.mkdir()
    full = rec_row(50, [rec(100, 20, last=105), rec(330, 49, last=399)], lost="state_diverged", seed="A1")
    full2 = rec_row(50, [rec(100, 30, last=399)], lost="state_diverged", seed="B2")
    bare = [{k: v for k, v in r.items() if k != "divergences"} for r in (full, full2)]
    (arm / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in bare) + "\n", encoding="utf-8")
    ended, crashes, filled = sr.read_block(arm)  # no file: the rows stay bare
    assert (filled, [sr.row_basis(r) for r in ended]) == (0, ["unreadable", "unreadable"])  # no records and no first-loss floor: they count nothing
    (arm / "divergences.jsonl").write_text(divergence_lines(full) + divergence_lines(full2), encoding="utf-8")
    ended, crashes, filled = sr.read_block(arm / "runs.jsonl")
    assert filled == 2 and [sr.row_basis(r) for r in ended] == ["loss_records", "loss_records"]
    assert passed(ended[0]) == (True, True, True) and passed(ended[1]) == (True, False, False)
    kept = [{**full, "seed": "A1"}]  # a row that carries the key keeps it
    assert sr.attach_block_divergences(kept, arm) == 0


def test_weekly_numbers_and_boss_entry_read_the_records_from_the_block_file(tmp_path):
    full = rec_row(50, [rec(100, 20, last=105), rec(330, 49, last=399)], lost="state_diverged", seed="A1")
    bare = {k: v for k, v in full.items() if k != "divergences"}
    arm = tmp_path / "g1"
    arm.mkdir()
    (arm / "runs.jsonl").write_text(json.dumps(bare) + "\n", encoding="utf-8")
    (arm / "divergences.jsonl").write_text(divergence_lines(full), encoding="utf-8")
    assert wn.load_real(arm / "runs.jsonl")["A1"]["passed"] is True
    night = tmp_path / "nightly" / "2026-11-20" / "g1"
    night.mkdir(parents=True)
    (night / "runs.jsonl").write_text(json.dumps(bare) + "\n", encoding="utf-8")
    (night / "divergences.jsonl").write_text(divergence_lines(full), encoding="utf-8")
    out = tmp_path / "nights.jsonl"

    class Args:
        nightly = str(tmp_path / "nightly")

    Args.out = str(out)
    assert be.cmd_nights(Args) == 0  # type: ignore[arg-type]
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["a"][1]["k"] == 1  # the Act 2 boss: past it, and played (the loss at floor 20 was recovered, the one at 49 is after)


# ---------------------------------------------------------------------------------------------------- the readers and the second path
NEW_ROWS = [rec_row(50, [rec(40, 10, last=44), rec(350, 49, last=399)], lost="state_diverged", fights=[fight(0, 17), fight(1, 33), fight(2, 48)]),
            rec_row(50, [], fights=[fight(0, 17), fight(1, 33, stand_in=3), fight(2, 48, stand_in=1)]),
            rec_row(50, [rec(100, 20, last=105), rec(330, 49, last=399)], lost="state_diverged"),
            rec_row(48, [rec(300, 48, last=399)], lost="state_diverged"), rec_row(50, [rec(300, 48, last=310)]),
            rec_row(50, [rec(100, 30, last=399)], lost="state_diverged"), rec_row(50, [rec(100, 20, last=105)]),
            rec_row(49, [rec(390, 17, room="non_combat", last=399)], lost="state_diverged"),
            rec_row(50, [rec(300, 48, last=310, encounter="FROG_KNIGHT")]),
            rec_row(40, [rec(100, 31, last=130)], bar=[[0, 1.0], [1, 1.0]], failed=2),
            rec_row(40, [rec(100, 31, last=130), rec(140, 32, reanchored=True)], bar=[[0, 1.0], [1, 1.0]], failed=2),
            rec_row(49, [rec(40, 10, last=44), rec(300, 30, last=399)], lost="state_diverged", end="victory"),
            rec_row(48, [], bar=[[0, 1.0], [1, 1.0], [2, 0.4]], fights=[fight(2, 48)])]


def test_the_three_readers_and_the_second_path_agree_on_rows_with_records_and_boss_fights():
    names = {"boss_fights": "fights", "loss_records": "records", "first_loss": "first", "unreadable": "unreadable", "no_loss": "none"}
    for i, row in enumerate(NEW_ROWS):
        for act in (0, 1, 2):
            want = sr.went_past(row, act)
            assert mr.went_past(row, act) == want and be.went_past({**row, "win": sr.is_win(row)}, act) == want, (i, act)
            assert mr._boss_of_act(row, act)[1] == mr.boss_hit(row, act)[1], (i, act)  # the --check path, written separately
            assert mr._played_of_act(row, act) == sr.fought_by_player(row, act), (i, act)
        assert wn.norm_row(row)["passed"] == sr.went_past(row, 2), i
        assert mr._basis_second(row) == names[sr.row_basis(row)], i


def test_make_agg_counts_how_lost_rows_were_read_and_the_arrivals_our_player_played():
    rows = [NEW_ROWS[0], NEW_ROWS[2], NEW_ROWS[3], real_row(50, 29), real_row(50, 20, stats={"first_loss": {"decision": 7}})]
    g = mr.make_agg(rows)
    assert (g.lost, g.lost_by_fights, g.lost_by_records, g.lost_by_first, g.lost_unknown) == (5, 1, 2, 1, 1)
    assert g.a3_arrivals == 5 and g.a3_played == 2 and g.a3_passes == 2  # rows 0 and 2 played the first boss and passed; row 3 lost inside it, the others are stand-in rows
    fig = mr.arm_figures(rows, [], True)
    assert (fig["lost_read_by_boss_fights"], fig["lost_read_by_loss_records"], fig["lost_read_by_first_loss"]) == (1, 2, 1)
    assert (fig["act3_arrivals"], fig["act3_passes"], fig["act3_fought_by_player"], fig["act3_lost_track"]) == (5, 2, 2, 3)
    assert (fig["act3_passes_of_arrivals"], fig["act3_passes_of_fought"]) == (0.4, 1.0)


def test_check_second_path_matches_the_report_path_on_rows_with_records_and_boss_fights(tmp_path):
    arm = tmp_path / "g1"
    arm.mkdir()
    rows = [{**r, "seed": f"S{i}"} for i, r in enumerate(NEW_ROWS)]
    (arm / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    second = mr._arm_second_path(arm / "runs.jsonl", True)
    ended, crashes = mr.split_rows(mr.read_jsonl(arm / "runs.jsonl"), True)
    first = mr.arm_figures(ended, crashes, True)
    for a, b in (("act1_killed", "act1_killed"), ("act2_killed", "act2_killed"), ("act3_killed", "act3_killed"), ("act3_reached", "act3_reached"),
                 ("lost_rows", "lost_rows"), ("lost_rows_credited", "lost_credited"), ("lost_read_by_boss_fights", "lost_fights"),
                 ("lost_read_by_loss_records", "lost_records"), ("lost_read_by_first_loss", "lost_first"),
                 ("act3_fought_by_player", "act3_played"), ("act3_arrivals", "act3_arrivals"), ("act3_passes", "act3_passes"),
                 ("lost_loss_floor_unknown", "lost_unknown")):
        assert first[a] == second[b], a
    assert first["act3_killed"] > 0 and first["lost_read_by_loss_records"] > 0 and first["lost_read_by_boss_fights"] > 0


def test_the_second_path_fills_missing_records_from_the_block_file_by_itself(tmp_path):
    full = rec_row(50, [rec(100, 20, last=105), rec(330, 49, last=399)], lost="state_diverged", seed="A1")
    bare = {k: v for k, v in full.items() if k != "divergences"}
    arm = tmp_path / "2026-11-20" / "g1"
    arm.mkdir(parents=True)
    (arm / "runs.jsonl").write_text(json.dumps(bare) + "\n", encoding="utf-8")
    assert mr._arm_second_path(arm / "runs.jsonl", True)["act3_killed"] == 0  # no file: read by the first loss, at floor 20
    (arm / "divergences.jsonl").write_text(divergence_lines(full), encoding="utf-8")
    assert mr._arm_second_path(arm / "runs.jsonl", True)["act3_killed"] == 1
    assert sum(1 for r in mr.load_arm_pair(arm.parent, "g1")["real_end"] if sr.went_past(r, 2)) == 1  # and the first path reads the file too


# ---------------------------------------------------------------------------------------------------- --check
def test_check_lists_the_rows_whose_credit_changed_with_their_reasons(tmp_path, capsys):
    arm = tmp_path / "nightly" / "2026-11-20T1904" / "g20"
    arm.mkdir(parents=True)
    rows = [{**NEW_ROWS[2], "seed": "AAA"},  # recovered before the fight, lost at the second boss: credited now
            {**NEW_ROWS[3], "seed": "BBB"},  # lost inside the first boss: not credited, as before
            {**NEW_ROWS[4], "seed": "CCC"},  # not lost, a loss inside the fight recovered after it: not credited now
            {**NEW_ROWS[1], "seed": "DDD"},  # the stand-in answered a decision of the fight: not credited now
            {**real_row(50), "seed": "EEE"},  # clean
            {**real_row(30, bar=[[0, 1.0]]), "seed": "FFF"}]  # did not arrive
    (arm / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    ids = tmp_path / "ids.json"
    ids.write_text(json.dumps({"AAA": ["QUEEN_BOSS", "AEONGLASS_BOSS"], "BBB": ["AEONGLASS_BOSS", "QUEEN_BOSS"], "CCC": ["TEST_SUBJECT_BOSS", "QUEEN_BOSS"],
                               "DDD": ["TEST_SUBJECT_BOSS", "QUEEN_BOSS"], "EEE": ["QUEEN_BOSS", "TEST_SUBJECT_BOSS"]}), encoding="utf-8")
    assert sr.main(["--check", str(arm), "--bosses", str(ids), "--list"]) == 0
    out = capsys.readouterr().out
    assert "5 arrivals" in out
    assert "first Act 3 boss: passes 2 of 5 arrivals = 40.0 per 100 (first-loss reading 3 of 5 = 60.0)" in out
    assert "fights our player played to the end: 2 of 5; passes among them 2 of 2" in out
    assert "lost-track arrivals (a stand-in answered part of the fight): 3 of 5" in out
    assert "the Queen: passes 2 of 2 arrivals; of the fights our player finished 2 of 2; lost-track 0 of 2 (first-loss reading passes 1)" in out
    assert "Act 3 boss, credited now: 1 (recovered before the fight; lost at the second boss)" in out
    assert "Act 3 boss, no longer credited: 1 (a loss inside the fight, recovered after it)" in out
    assert "Act 3 boss, no longer credited: 1 (the stand-in answered 1 decision of the fight)" in out
    assert "AAA Act 3 old no -> yes" in out and "C:/" not in out and "D:/" not in out


def test_morning_report_check_prints_the_reading_change_above_the_mismatch_count():
    text = mr.check_text(Path("2026-11-20"), "g20", [{"figure": "x", "first": 1, "second": 1, "ok": True}], "strict_rows --check: the change list")
    assert "strict_rows --check: the change list" in text and text.rstrip().endswith("1 figures, 0 mismatches")
