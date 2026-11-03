"""tools/subproblems.py: the sub-problem board's readers on tiny synthetic inputs, and the table's rendering (no real run is read)."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import boss_entry as be  # noqa: E402
import subproblems as sp  # noqa: E402

TYPES = {"STRIKE_IRONCLAD": "Attack", "DEFEND_IRONCLAD": "Skill", "BASH": "Attack", "ANGER": "Attack", "ARMAMENTS": "Skill"}
CARDS = be.Cards(TYPES, {30: "BASH", 131: "DEFEND_IRONCLAD", 472: "STRIKE_IRONCLAD", 13: "ANGER", 18: "ARMAMENTS"}, {"BURNING_BLOOD"})
N = 25  # over the suppression line (MIN_CELL = 20)


# ------------------------------------------------------------------------------------------------ builders


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def run_record(seed: str, boss_won: bool = True) -> dict:
    """A self-play RunRecord: a hallway fight on floor 2 entered with one potion and left with none (used), an elite on floor 5 entered
    with none, the Act 1 boss on floor 17 entered with one potion (kept when the boss is won; a lost boss leaves no state after it)."""
    deck = [[30, 1, 0, 0], [131, 0, 0, 0], [472, 0, 0, 0], [13, 0, 0, 0]]

    def state(floor: int, pots: list[int], hp: int = 60) -> dict:
        return {"act_index": 0, "floor": floor, "hp": hp, "max_hp": 80, "gold": 99, "deck": deck, "relics": [36, 5], "potions": pots, "boss": 83}

    def dec(kind: str, options: list[dict], chosen: int, floor: int, pots: list[int]) -> dict:
        return {"type": kind, "state": state(floor, pots), "options": options, "chosen": chosen}

    node = lambda t: [{"kind": "map.node", "node": [0, 1, t]}]  # noqa: E731
    decisions = [dec("map", node(1), 0, 1, [4]), dec("rewards", [{"kind": "reward.proceed"}], 0, 2, []),
                 dec("map", node(2), 0, 2, []), dec("card_reward", [{"kind": "card.take", "card": [18, 0, 0, 0]}, {"kind": "card.skip"}], 1, 5, []),
                 dec("map", node(6), 0, 5, [])]
    fights = [{"floor": 2, "node_type": 1, "won": True, "state": state(2, [4])}, {"floor": 5, "node_type": 2, "won": True, "state": state(5, [])},
              {"floor": 17, "node_type": 6, "won": boss_won, "state": state(17, [7], hp=64)}]
    if boss_won:
        decisions.append(dec("rewards", [{"kind": "reward.proceed"}], 0, 17, [7]))
    return {"seed": seed, "generation": 11, "outcome": {"final_floor": 17, "won": False, "died": not boss_won, "truncated": False},
            "decisions": decisions, "fights": fights}


def night_row(i: int) -> dict:
    return {"seed": f"S{i}", "floor": 20, "end": "death", "win": False, "boss_damage_acts": [[0, 1.0]], "nodes": "MEEMRB",
            "cards": [[2, "ANGER"], [5, "skip"], [8, "skip"]], "rests": [[4, "heal"]]}


def human_run(rid: str, win: bool = False) -> dict:
    def pt(kind: str, **stats) -> dict:
        return {"map_point_type": kind, "player_stats": [{"current_hp": 50, "max_hp": 80, "current_gold": 99, **stats}]}

    act1 = [pt("ancient"), pt("monster", potion_choices=[{"was_picked": True}]), pt("monster", potion_used=["POTION.X"]), pt("unknown"), pt("elite")]
    return {"ascension": 10, "game_mode": "standard", "was_abandoned": False, "modifiers": [], "win": win, "run_hash": rid,
            "killed_by_encounter": "NONE.NONE" if win else "ENCOUNTER.ELITE", "killed_by_event": "NONE.NONE", "map_point_history": [act1],
            "players": [{"character": "CHARACTER.IRONCLAD", "deck": [], "relics": []}]}


def morning_doc() -> dict:
    cell = lambda act, kind, f, s: {"act": act, "kind": kind, "fights": f, "survived": s, "win_rate": s / f if f else None, "suppressed": f < 20}  # noqa: E731
    return {"night": {"date": "2026-11-04", "agent": "g11", "generation": 11, "folder": "nightly/2026-11-04"},
            "real": {"ended": 100, "mean_floor": 23.0, "act1_reached": 90, "act1_killed": 45, "act2_reached": 30, "act2_killed": 6},
            "fights": {"real": [cell(1, "boss", 90, 45), cell(2, "hallway", 200, 150), cell(2, "elite", 40, 20), cell(2, "boss", 30, 6),
                                cell(3, "boss", 5, 0)],
                       "emu": [cell(2, "boss", 40, 4)]}}


# ------------------------------------------------------------------------------------------------ the night


def test_survival_reads_the_morning_json_and_suppresses_small_cells() -> None:
    out = sp.survival(morning_doc())
    assert out["real"]["a2.hallway"]["value"] == pytest.approx(0.75) and out["real"]["a2.hallway"]["n"] == 200
    assert out["real"]["a2.boss"]["k"] == 6 and out["real"]["a2.boss"]["n"] == 30
    assert out["real"]["a3.boss"]["status"] == "suppressed"  # five fights: never published
    assert out["emu"]["a2.boss"]["value"] == pytest.approx(0.1)
    head = sp.night_header(morning_doc())
    assert head["generation"] == 11 and head["act1_boss_kill_of_reached"]["value"] == pytest.approx(0.5)
    assert head["act2_boss_kill_of_reached"]["n"] == 30


def test_newest_finished_night_needs_both_arms_and_the_summary_files(tmp_path: Path) -> None:
    (tmp_path / "2026-11-02" / "g9").mkdir(parents=True)
    for f in ("result.json", "summary.json"):
        (tmp_path / "2026-11-02" / "g9" / f).write_text("{}", encoding="utf-8")
    write_jsonl(tmp_path / "2026-11-02" / "g9-emu" / "runs.jsonl", [{}])
    write_jsonl(tmp_path / "2026-11-03" / "g11" / "runs.jsonl", [{}])  # a running night: rows only, no result or summary
    write_jsonl(tmp_path / "2026-11-03" / "g11-emu" / "runs.jsonl", [{}])
    (tmp_path / "notes").mkdir()
    assert sp.newest_finished_night(tmp_path) == (tmp_path / "2026-11-02", "g9")
    assert sp.newest_finished_night(tmp_path / "2026-11-03") is None
    # a newer finished night of two rows, and a bigger older one: min_rows picks the night that measures over the one that checks
    for f in ("result.json", "summary.json"):
        (tmp_path / "2026-11-04" / "g11").mkdir(parents=True, exist_ok=True)
        (tmp_path / "2026-11-04" / "g11" / f).write_text("{}", encoding="utf-8")
    write_jsonl(tmp_path / "2026-11-04" / "g11" / "runs.jsonl", [{}, {}])
    write_jsonl(tmp_path / "2026-11-04" / "g11-emu" / "runs.jsonl", [{}, {}])
    write_jsonl(tmp_path / "2026-11-02" / "g9" / "runs.jsonl", [{}] * 5)
    assert sp.newest_finished_night(tmp_path) == (tmp_path / "2026-11-04", "g11")
    assert sp.newest_finished_night(tmp_path, min_rows=5) == (tmp_path / "2026-11-02", "g9")
    assert sp.newest_finished_night(tmp_path, min_rows=50) is None


def test_run_morning_reads_the_json_the_script_wrote(tmp_path: Path) -> None:
    class Done:
        returncode = 0

    def runner(cmd, **kw):
        out = Path(cmd[cmd.index("--out") + 1])
        (out / "morning_report.json").write_text(json.dumps(morning_doc()), encoding="utf-8")
        assert "--winlog" in cmd and cmd[cmd.index("--winlog") + 1] == "none" and cmd[cmd.index("--agent") + 1] == "g11"
        return Done()

    assert sp.run_morning(tmp_path, "g11", runner=runner)["night"]["generation"] == 11

    class Failed:
        returncode = 2

    assert sp.run_morning(tmp_path, "g11", runner=lambda cmd, **kw: Failed()) is None


def test_route_and_pick_figures_from_nightly_rows(tmp_path: Path) -> None:
    rows = sp.night_rows(write_jsonl(tmp_path / "runs.jsonl", [night_row(i) for i in range(N)] + [{"seed": "C", "crash": True}]))
    assert len(rows) == N  # the crash row is dropped
    route = sp.route_figures(rows, CARDS, "emu rows", "2026-11-04")
    assert route["a1"]["n"] == N and route["a1"]["elites"] == pytest.approx(2.0) and route["a1"]["fights"] == pytest.approx(4.0)
    assert route["a2"]["status"] == "suppressed"  # no run reached the Act 2 boss
    picks = sp.pick_figures(rows, CARDS, "real rows", "2026-11-04")
    assert picks["a1"]["taken"] == pytest.approx(1.0) and picks["a1"]["skipped"] == pytest.approx(2.0)
    assert picks["a1"]["skip_rate"] == pytest.approx(2 / 3)


# ------------------------------------------------------------------------------------------------ the shards


def write_job(root: Path, name: str, gen: int, runs: list[dict], eps: float | None = None) -> Path:
    shards = root / name / "shards"
    shards.mkdir(parents=True)
    agent = {"generation": gen} | ({"eps": eps} if eps is not None else {})
    (shards / "shards.json").write_text(json.dumps({"generation": gen, "agent": agent}), encoding="utf-8")
    with gzip.open(shards / "r0000.jsonl.gz", "wt", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(r) + "\n" for r in runs))
    return shards


def test_shard_jobs_pick_the_generation_and_leave_exploring_jobs_out(tmp_path: Path) -> None:
    keep = write_job(tmp_path, "a-selfplay", 11, [run_record("A")])
    write_job(tmp_path, "b-selfplay", 11, [run_record("B")], eps=0.02)
    write_job(tmp_path, "c-selfplay", 9, [run_record("C")])
    assert sp.shard_jobs(tmp_path, 11) == [keep]
    assert len(sp.shard_jobs(tmp_path, 11, exploring=True)) == 2
    assert sp.shard_jobs(tmp_path, 7) == []


def test_potion_fights_count_the_potions_left_by_the_next_state() -> None:
    won, lost = sp.potion_fights(run_record("W")), sp.potion_fights(run_record("L", boss_won=False))
    assert won == [(0, "hallway", 1, 1), (0, "elite", 0, 0), (0, "boss", 1, 0)]  # a drink in the hallway, none at the elite, one kept at the boss
    assert lost[2] == (0, "boss", 1, None)  # a lost fight ends the run: its potion use is not recorded
    assert sp.potion_fights({"fights": [{"node_type": 7, "state": {"potions": []}}]}) == []  # events are not hallway, elite or boss fights


def test_door_and_potion_figures_from_shards(tmp_path: Path) -> None:
    shards = [write_job(tmp_path, "a-selfplay", 11, [run_record(f"W{i}") for i in range(N)] + [run_record(f"L{i}", boss_won=False) for i in range(N)])]
    summaries, pots, budgets = sp.read_shards(shards, CARDS)
    assert len(summaries) == 2 * N and len(pots) == 6 * N and len(budgets) == 2 * N
    door = sp.door_figures(summaries, CARDS, "shards", "2026-11-04")
    a1 = door["a1"]
    assert a1["n"] == 2 * N and a1["kill"]["k"] == N and a1["kill"]["value"] == pytest.approx(0.5)
    assert a1["potions"] == pytest.approx(1.0) and a1["relics"] == pytest.approx(2.0) and a1["gold"] == pytest.approx(99.0)
    assert a1["elites"] == pytest.approx(1.0) and a1["attack"] == pytest.approx(3.0)
    assert door["a2"]["status"] == "suppressed"
    use = sp.potion_use_figures(pots, "shards", "2026-11-04")
    assert use["a1.hallway"]["used_when_held"]["value"] == pytest.approx(1.0)  # every hallway fight that began with a potion used it
    assert use["a1.boss"]["fights"] == 2 * N and use["a1.boss"]["observed_after"] == pytest.approx(0.5)
    assert use["a1.boss"]["used_when_held"]["n"] == N and use["a1.boss"]["used_when_held"]["value"] == 0.0  # the won boss fights kept theirs
    assert "used_when_held" not in use["a1.elite"]  # no potion held there: nothing to say about use
    assert sp.potion_use_figures(pots[:5], "shards")["a1.hallway"]["status"] == "suppressed"
    b = sp.budget_figures(budgets, "shards", "2026-11-04")
    assert b["n"] == 2 * N and b["used_hallway"] == pytest.approx(1.0) and b["used_elite"] == 0.0 and b["held_at_door"] == pytest.approx(1.0)
    assert b["hallway_share_of_used"] == pytest.approx(1.0) and b["gained"] == 0.0 and b["drops_explained_by_fights"] == pytest.approx(1.0)
    assert sp.budget_figures(budgets[:5], "shards")["status"] == "suppressed"


def test_potion_budget_of_one_run() -> None:
    # the potion held in the first state is drunk in the floor-2 fight; nothing is gained; the boss reward on floor 17 is not before the boss
    assert sp.potion_budget(run_record("W")) == {"hallway": 1, "elite": 0, "door": 1, "gained": 0, "dropped": 1}
    assert sp.potion_budget(run_record("L", boss_won=False)) == {"hallway": 1, "elite": 0, "door": 1, "gained": 0, "dropped": 1}  # the lost boss fight adds nothing
    assert sp.potion_budget({"fights": [{"node_type": 1, "state": {"act_index": 0, "floor": 2, "potions": [1]}, "won": True}], "decisions": []}) is None


# ------------------------------------------------------------------------------------------------ the board and the gym


def test_board_figures_per_version(tmp_path: Path) -> None:
    def rows(player: str, wins: int) -> list[dict]:
        return [{"cat": "act1-boss", "player": player, "start": f"S{i % 5}|f17", "won": i < wins, "start_potions": 1 if i % 2 else 0,
                 "potions_used": 1 if i % 4 == 1 else 0} for i in range(50)] + [{"cat": "act1-elite", "player": player, "start": "E|f5", "won": True}]

    write_jsonl(tmp_path / "fp-v1.jsonl", rows("c0001", 20))
    write_jsonl(tmp_path / "fp-v2.jsonl", rows("c0019", 25))
    out = sp.board_figures(tmp_path)
    assert [v["version"] for v in out["versions"]] == ["v1", "v2"] and out["latest"]["players"] == ["c0019"]
    assert out["latest"]["games"] == 50 and out["latest"]["starts"] == 5 and out["latest"]["replays_per_start"] == 10
    assert out["latest"]["overall"]["value"] == pytest.approx(0.5) and out["versions"][0]["overall"]["k"] == 20  # elite rows are not the boss board
    assert out["latest"]["potions"]["games_with_potion"] == 25 and out["latest"]["potions"]["used_any"]["k"] == 13
    assert sp.board_figures(tmp_path / "none") == {"versions": [], "latest": None}


def test_gym_kinds_win_rates_from_weights(tmp_path: Path) -> None:
    w = tmp_path / "weights.json"
    w.write_text(json.dumps({"player": "v2", "config": "a3-v1", "written": "2026-11-03T01:05:15Z",
                             "games": {"act1-boss": 100, "act2-boss": 10}, "win": {"act1-boss": 0.54, "act2-boss": 0.1}}), encoding="utf-8")
    out = sp.gym_kinds(w)
    assert out["kinds"]["act1-boss"]["k"] == 54 and out["kinds"]["act1-boss"]["n"] == 100
    assert out["kinds"]["act2-boss"] == {"status": "suppressed"}  # ten games
    assert sp.gym_kinds(tmp_path / "missing.json")["status"] == "not measured"


# ------------------------------------------------------------------------------------------------ the exam


def exam_doc() -> dict:
    card = lambda act, same, hs, ais: {"type": "card_reward", "act": act, "top": 0, "human": 0 if same else 1, "human_skip": hs, "ai_skip": ais,  # noqa: E731
                                       "offered": [1, 2, 3], "regret": 0.5, "rank": 0 if same else 2}
    rest = lambda act, h, a: {"type": "rest", "act": act, "human_smith": h, "ai_smith": a}  # noqa: E731
    rows = [card(0, i < 10, False, i < 5) for i in range(N)] + [card(1, i < 5, i < 15, i < 2) for i in range(N)]
    rows += [rest(0, i < 20, i < 10) for i in range(N)] + [{"type": "card_reward", "act": 2, "top": 0, "human": 0, "human_skip": False, "ai_skip": False,
                                                           "offered": [1], "regret": 0.0, "rank": 0}]
    return {"runs": 7, "skipped": 0, "rows": rows}


def test_exam_figures_by_act() -> None:
    out = sp.exam_figures(exam_doc(), "exam rows", "2026-11-02")
    assert out["card_a1"]["same_pick"]["value"] == pytest.approx(10 / N) and out["card_a1"]["chance"] == pytest.approx(0.25)
    assert out["card_a1"]["first_or_second"]["k"] == 10 and out["card_a1"]["ai_skip"]["k"] == 5 and out["card_a2"]["human_skip"]["value"] == pytest.approx(0.6)
    assert out["card_a2"]["ai_skip"]["value"] == pytest.approx(2 / N)
    assert out["rest_a1"]["human_upgrade"]["value"] == pytest.approx(0.8) and out["rest_a1"]["same_choice"]["value"] == pytest.approx(0.6)
    assert "rest_a2" not in out  # no rest decisions in Act 2
    ag = sp.agreement_figures({"runs": 3, "scored": 90, "incumbent": {"agreement": {"card_reward": 0.3, "rest": 0.6}},
                               "candidates": [{"label": "candidate-0", "measures": {"card_reward": {"diff": 0.01}}}], "sha256": "x"}, "agreement.json")
    assert ag["incumbent"]["card_reward"] == 0.3 and ag["candidates"][0]["label"] == "candidate-0" and "sha256" not in ag


# ------------------------------------------------------------------------------------------------ the humans


def door_summary(i: int, kills: int = 15, ex: int = 1) -> dict:
    """A human cache line (as `boss_entry.py human` writes it) for a run that reached the Act 1 boss."""
    return {"src": "h", "ex": ex, "id": f"h{i}", "floor": 20, "won": False, "end": "death", "tot": {}, "a": [
        {"r": 1, "k": int(i < kills), "at": "boss", "hp": 40, "mhp": 80, "gold": 150, "pot": 2, "rel": 6, "deck": ["ANGER", "BASH+"], "path": "MEER",
         "rests": [], "offers": [], "shop": {"v": 1, "c": 1, "r": 1, "x": 0}, "pots": [3, 1]}, None]}


def write_cache(path: Path, door_runs: int) -> Path:
    be.write_jsonl(path, [door_summary(i) for i in range(door_runs)] + [door_summary(0, ex=0)])
    return path


def test_human_door_reads_only_the_exam_fifth(tmp_path: Path) -> None:
    runs = [door_summary(i) for i in range(N)] + [{**door_summary(0), "ex": 0, "a": [{**door_summary(0)["a"][0], "rel": 99}, None]}]
    cache = tmp_path / "human.jsonl.gz"
    be.write_jsonl(cache, runs)
    out = sp.human_door(cache, CARDS)
    assert out["a1"]["n"] == N and out["a1"]["relics"] == pytest.approx(6.0) and out["a1"]["potions"] == pytest.approx(2.0)  # the 99-relic run is not in the fifth
    assert out["a1"]["kill"]["k"] == 15 and out["a1"]["elites"] == pytest.approx(2.0) and out["a1"]["shop_relics"] == pytest.approx(1.0)
    assert out["a2"]["status"] == "suppressed"
    assert sp.human_door(tmp_path / "nope.jsonl.gz", CARDS) is None


def test_human_fight_events_and_figures() -> None:
    ev = sp.human_fight_events(human_run("x"))
    # the two monster rooms (a potion picked in the first, drunk in the second), the unknown room is not a fight, the elite killed the run
    assert ev == [(0, "hallway", False, 0, 0), (0, "hallway", False, 1, 1), (0, "elite", True, 0, 0)]
    assert [e[2] for e in sp.human_fight_events(human_run("y", win=True))] == [False, False, False]
    fig = sp.human_fight_figures((human_run(f"r{i}") for i in range(N)), "corpus")
    assert fig["runs"] == N
    assert fig["survival"]["a1.hallway"]["value"] == 1.0 and fig["survival"]["a1.elite"]["value"] == 0.0 and fig["survival"]["a1.elite"]["n"] == N
    assert fig["potion_use"]["a1.hallway"]["used_when_held"]["n"] == N and fig["potion_use"]["a1.hallway"]["used_when_held"]["value"] == 1.0
    small = sp.human_fight_figures((human_run(f"r{i}") for i in range(5)), "corpus")
    assert small["survival"]["a1.hallway"]["status"] == "suppressed"


def test_human_potion_budget() -> None:
    def pt(kind: str, **stats) -> dict:
        return {"map_point_type": kind, "player_stats": [{"current_hp": 50, "max_hp": 80, **stats}]}

    run = {**human_run("b"), "map_point_history": [[pt("ancient"), pt("monster", potion_choices=[{"was_picked": True}, {"was_picked": True}]),
                                                     pt("elite", potion_used=["POTION.A"]), pt("monster", potion_used=["POTION.B"]), pt("boss")]]}
    assert sp.human_potion_budget(run) == {"hallway": 1, "elite": 1, "door": 0}  # two picked, two drunk: none left at the boss room
    assert sp.human_potion_budget(human_run("c")) is None  # never reached the boss


def test_humans_command_passes_over_a_corpus_file(tmp_path: Path) -> None:
    ids = [f"run{i}" for i in range(400)]
    exam = [i for i in ids if be.is_exam(i)][:N]
    other = [i for i in ids if not be.is_exam(i)][:10]
    lines = [json.dumps(human_run(i), separators=(",", ":")) for i in exam + other]
    lines.append(json.dumps({**human_run("zz"), "ascension": 5}, separators=(",", ":")))  # not Ascension 10: skipped before parsing
    corpus = tmp_path / "corpus.jsonl.gz"
    with gzip.open(corpus, "wt", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    out = tmp_path / "humans.json"
    assert sp.main(["humans", "--corpus", str(corpus), "--out", str(out)]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["runs"] == N and doc["survival"]["a1.elite"]["n"] == N and "date" in doc


# ------------------------------------------------------------------------------------------------ build and render


def full_doc(tmp_path: Path, humans: dict | None = None) -> dict:
    nightly = tmp_path / "nightly" / "2026-11-04"
    write_jsonl(nightly / "g11" / "runs.jsonl", [night_row(i) for i in range(N)])
    write_jsonl(nightly / "g11-emu" / "runs.jsonl", [night_row(i) for i in range(N)])
    shards = [write_job(tmp_path / "runs", "a-selfplay", 11, [run_record(f"W{i}") for i in range(N)])]
    write_jsonl(tmp_path / "board" / "fp-v1.jsonl", [{"cat": "act1-boss", "player": "c1", "start": f"S{i % 5}|f17", "won": i % 2 == 0} for i in range(50)])
    w = tmp_path / "weights.json"
    w.write_text(json.dumps({"games": {"act2-boss": 100}, "win": {"act2-boss": 0.09}, "written": "2026-11-03T01:05:15Z"}), encoding="utf-8")
    cache = write_cache(tmp_path / "human.jsonl.gz", N)
    exam = tmp_path / "exam-rows.json"
    exam.write_text(json.dumps(exam_doc()), encoding="utf-8")
    return sp.build((nightly, "g11"), morning_doc(), 11, CARDS, shards, tmp_path / "board", w, cache, exam, humans, None)


HUMANS = {"runs": 500, "survival": {"a2.hallway": sp.rate(180, 200, "pass"), "a2.elite": sp.rate(60, 100, "pass"), "a2.boss": sp.rate(30, 40, "pass")},
          "potion_use": {"a1.boss": {"used_when_held": sp.rate(30, 40, "pass")}},
          "potion_budget": {"n": 400, "used_hallway": 0.3, "used_elite": 0.9, "held_at_door": 1.6, "hallway_share_of_used": 0.25}}


def test_build_and_the_table_say_not_measured_where_nothing_was_read(tmp_path: Path) -> None:
    doc = full_doc(tmp_path)
    assert doc["inputs"]["shards"] == {"generation": 11, "jobs": 1, "runs": N} and doc["human_fights"]["status"] == "not measured"
    rows = sp.table_rows(doc)
    assert [r[0].split(".")[0] for r in rows] == ["1", "2", "3", "4", "5", "6"]
    assert rows[0][2] == "50.0% (night 2026-11-04, 90 fights)" and rows[0][3] == "60.0% (25 visits)" and rows[0][4] == "-10.0"
    assert rows[1][2] == "75.0% / 50.0% / 20.0% (night 2026-11-04, 30 boss fights)"
    assert rows[1][3] == "not measured / not measured / not measured (? boss visits)"  # no human pass yet, and no Act 2 boss in the tiny cache
    assert rows[1][4] == "not measured / not measured / not measured"
    assert rows[2][2] == "2.00 (emulator arm, night 2026-11-04, 25 runs)" and rows[2][3] == "2.00 (25 runs)" and rows[2][4] == "+0.00 elites"
    assert rows[3][2].startswith("40% / 20% (a coin: 25%); would skip 8%") and rows[3][3].startswith("skip 60% (25 Act 2 decisions)")
    assert rows[3][4] == "-52.0 (skip share)"
    assert rows[4][2] == "1.0 held (25 visits); 1.0 used a run before it, 1.0 in hallway fights" and rows[4][4] == "-1.0 potions"
    assert rows[4][3] == "2.0 held (25 visits); use not measured"
    assert rows[5][2] == "2.0 held, 0.00 bought (25 visits)" and rows[5][3] == "6.0 held, 1.00 bought (25 visits)" and rows[5][4] == "-4.0 relics"


def test_the_human_pass_fills_the_unmeasured_cells(tmp_path: Path) -> None:
    rows = sp.table_rows(full_doc(tmp_path, HUMANS))
    assert rows[1][3] == "90.0% / 60.0% / not measured (? boss visits)"  # the pass has Act 2 hallway and elite; the cache has no Act 2 boss here
    assert rows[1][4] == "-15.0 / -10.0 / not measured"  # the real arm's 75% and 50% against the humans' 90% and 60%
    assert rows[4][3] == "2.0 held (25 visits); 1.2 used a run before it, 0.3 in hallway fights"


def test_render_replaces_only_between_the_markers() -> None:
    text = f"# Title\n\nintro\n\n{sp.MARK_START}\nold table\n{sp.MARK_END}\n\nprose that stays\n"
    out = sp.render_into(text, "| a | b |")
    assert out == f"# Title\n\nintro\n\n{sp.MARK_START}\n| a | b |\n{sp.MARK_END}\n\nprose that stays\n"
    assert sp.render_into(out, "| a | b |") == out  # idempotent
    for bad in ("no markers", f"{sp.MARK_END} {sp.MARK_START}", f"{sp.MARK_START} {sp.MARK_START} {sp.MARK_END}"):
        with pytest.raises(ValueError):
            sp.render_into(bad, "x")


def test_render_table_and_the_render_command(tmp_path: Path) -> None:
    doc = full_doc(tmp_path)
    table = sp.render_table(doc)
    lines = table.splitlines()
    assert lines[0].startswith("| Piece |") and lines[1].startswith("|---|") and sum(1 for ln in lines if ln.startswith("| ") and "." in ln[:6]) >= 6
    assert all(ln.count("|") == lines[0].count("|") for ln in lines[:8])  # every row has the header's columns
    assert "not measured" in table and "newest finished night 2026-11-04" in table
    js, md = tmp_path / "sp.json", tmp_path / "SUBPROBLEMS.md"
    js.write_text(json.dumps(doc), encoding="utf-8")
    md.write_text(f"intro\n{sp.MARK_START}\nstale\n{sp.MARK_END}\ntail\n", encoding="utf-8")
    assert sp.main(["render", "--json", str(js), "--doc", str(md)]) == 0
    got = md.read_text(encoding="utf-8")
    assert got.startswith("intro\n") and got.endswith("tail\n") and "stale" not in got and "| 6. Shops and relics |" in got


def test_the_agreement_baseline_joins_the_card_row(tmp_path: Path) -> None:
    doc = full_doc(tmp_path)
    doc["agreement"] = sp.agreement_figures({"runs": 1000, "scored": 14013, "incumbent": {"agreement": {"card_reward": 0.306, "rest": 0.607}}, "candidates": []},
                                            "agreement.json")
    assert sp.table_rows(doc)[3][2].endswith("; fast-test baseline 30.6% cards / 60.7% rests (14,013 decisions)")


def test_an_empty_document_renders_all_six_rows_as_not_measured() -> None:
    rows = sp.table_rows({})
    assert len(rows) == 6 and all("not measured" in " ".join(r[2:5]) for r in rows)
    assert sp.rel("D:/spireline/referee/LAB/nightly/2026-11-03") .startswith("referee/") and "D:" not in sp.rel("C:/somewhere/else/file.json")
