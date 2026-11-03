"""The boss-entry instrument (tools/boss_entry.py, tools/boss_entry_report.py): readers, the exam fifth, cohorts, suppression."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import boss_entry as be  # noqa: E402
import boss_entry_report as rep  # noqa: E402

TYPES = {"STRIKE_IRONCLAD": "Attack", "DEFEND_IRONCLAD": "Skill", "BASH": "Attack", "ASCENDERS_BANE": "Curse", "ANGER": "Attack",
         "ARMAMENTS": "Skill", "INFLAME": "Power", "SHRUG_IT_OFF": "Skill", "TWIN_STRIKE": "Attack"}
CARDS = be.Cards(TYPES, {30: "BASH", 131: "DEFEND_IRONCLAD", 472: "STRIKE_IRONCLAD", 13: "ANGER", 18: "ARMAMENTS", 10: "INFLAME"},
                 {"BURNING_BLOOD", "ANCHOR"})


def pt(kind: str, hp: int = 60, mhp: int = 80, gold: int = 100, model: str | None = None, **stats) -> dict:
    out = {"map_point_type": kind, "player_stats": [{"current_hp": hp, "max_hp": mhp, "current_gold": gold, "hp_healed": 0, **stats}]}
    if model:
        out["rooms"] = [{"model_id": model}]
    return out


def card(name: str, level: int = 0) -> dict:
    return {"id": f"CARD.{name}", **({"current_upgrade_level": level} if level else {})}


def human_run(rid: str = "r1", killed_boss: bool = True, died_early: bool = False, win: bool = False) -> dict:
    act1 = [pt("ancient", 80, 80, 99, cards_gained=[card("ANGER")]),
            pt("monster", 70, 80, 110, card_choices=[{"card": card("INFLAME"), "was_picked": True}, {"card": card("ARMAMENTS"), "was_picked": False}],
               cards_gained=[card("INFLAME")]),
            pt("rest_site", 80, 80, 110, rest_site_choices=["SMITH"], upgraded_cards=["CARD.BASH"], hp_healed=0),
            pt("elite", 50, 80, 150, card_choices=[{"card": card("TWIN_STRIKE"), "was_picked": False}], relic_choices=[{"choice": "RELIC.ANCHOR", "was_picked": True}]),
            pt("rest_site", 80, 80, 150, rest_site_choices=["HEAL"], hp_healed=30),
            pt("shop", 80, 80, 40, cards_gained=[card("SHRUG_IT_OFF")], cards_removed=[card("STRIKE_IRONCLAD")], bought_relics=[]),
            ]
    if not died_early:
        act1.append(pt("boss", 55, 80, 160, model="ENCOUNTER.VANTOM_BOSS"))
    else:
        act1[-1:] = [pt("monster", 0, 80, 40, model="ENCOUNTER.NIBBITS_WEAK")]
    acts = [act1]
    if killed_boss and not died_early:
        acts.append([pt("ancient", 80, 80, 160), pt("monster", 70, 80, 170)])
    deck = [{"id": "CARD.BASH", "current_upgrade_level": 1}]
    return {"ascension": 10, "game_mode": "standard", "was_abandoned": False, "modifiers": [], "win": win,
            "killed_by_encounter": "NONE.NONE" if win else "ENCOUNTER.X", "killed_by_event": "NONE.NONE", "run_hash": rid,
            "map_point_history": acts,
            "players": [{"character": "CHARACTER.IRONCLAD", "deck": deck,
                         "relics": [{"id": "RELIC.BURNING_BLOOD", "floor_added_to_deck": 1}, {"id": "RELIC.ANCHOR", "floor_added_to_deck": 4},
                                    {"id": "RELIC.ANCHOR", "floor_added_to_deck": 30}]}]}


def test_exam_fifth_is_fixed_and_about_a_fifth() -> None:
    ids = [f"run{i}" for i in range(10000)]
    assert [be.exam_bucket(i) for i in ids[:50]] == [be.exam_bucket(i) for i in ids[:50]]
    share = sum(be.is_exam(i) for i in ids) / len(ids)
    assert 0.18 < share < 0.22
    assert {be.exam_bucket(i) for i in ids} == {0, 1, 2, 3, 4}


def test_human_filter() -> None:
    r = human_run()
    assert be.human_ok(r)
    for key, bad in (("ascension", 9), ("game_mode", "daily"), ("was_abandoned", True), ("modifiers", ["x"])):
        assert not be.human_ok({**r, key: bad})
    assert not be.human_ok({**r, "players": r["players"] * 2})
    assert not be.human_ok({**r, "players": [{**r["players"][0], "character": "CHARACTER.SILENT"}]})
    assert be.human_summary({**r, "ascension": 5}) is None


def test_replay_deck_applies_gains_removals_upgrades_and_transforms() -> None:
    pts = [pt("ancient", cards_gained=[card("ANGER")]),
           pt("shop", cards_removed=[card("STRIKE_IRONCLAD")], cards_gained=[card("INFLAME")]),
           pt("rest_site", upgraded_cards=["CARD.BASH"]),
           pt("unknown", cards_transformed=[{"original_card": card("DEFEND_IRONCLAD"), "final_card": card("ARMAMENTS")}])]
    deck = be.replay_deck(pts)
    assert sum(deck.values()) == 11 + 1 - 1 + 1
    assert deck[("BASH", 1)] == 1 and deck[("BASH", 0)] == 0
    assert deck[("STRIKE_IRONCLAD", 0)] == 4 and deck[("DEFEND_IRONCLAD", 0)] == 3
    assert deck[("ARMAMENTS", 0)] == 1 and deck[("INFLAME", 0)] == 1 and deck[("ANGER", 0)] == 1
    assert deck[("ASCENDERS_BANE", 0)] == 1


def test_human_summary_boss_entry_state() -> None:
    s = be.human_summary(human_run())
    a = s["a"][0]
    assert (a["r"], a["k"], a["at"], a["boss"]) == (1, 1, "boss", "VANTOM_BOSS")
    assert (a["hp"], a["mhp"], a["gold"]) == (80, 80, 40)  # the state after the room before the boss
    assert a["rel"] == 2  # the relic added on floor 30 is not held yet
    assert len(a["deck"]) == 11 + 1 + 1 + 1 - 1 and "BASH+" in a["deck"] and "INFLAME" in a["deck"]
    assert a["path"] == "MRERS"
    assert a["rests"] == [[1.0, "smith"], [0.625, "heal"]]  # 50 hp + 30 healed = 80; before = 50 / 80
    assert a["offers"] == [["INFLAME", ["INFLAME", "ARMAMENTS"]], [None, ["TWIN_STRIKE"]]]
    assert a["shop"] == {"v": 1, "c": 1, "r": 0, "x": 1}
    assert s["tot"]["taken"] == 1 and s["tot"]["skipped"] == 1 and s["tot"]["smith"] == 1 and s["tot"]["heal"] == 1
    assert s["a"][1]["r"] == 0 and s["a"][1]["at"] == "death"  # act 2 entered, the run ended there before its boss


def test_human_summary_lost_at_boss_and_death_before() -> None:
    lost = be.human_summary(human_run(killed_boss=False))
    assert lost["a"][0]["r"] == 1 and lost["a"][0]["k"] == 0 and lost["a"][1] is None
    early = be.human_summary(human_run(died_early=True))
    a = early["a"][0]
    assert a["r"] == 0 and a["at"] == "death" and a["k"] is None
    assert be.in_cohort(a, "before") and not be.in_cohort(a, "boss")
    assert a["path"] == "MRER"  # the room that ended the run is not counted


def test_ai_summary_and_cohorts() -> None:
    deck = [[30, 1, 0, 0], [131, 0, 0, 0], [472, 0, 0, 0], [13, 0, 0, 0]]

    def state(floor: int, act: int = 0, hp: int = 60) -> dict:
        return {"act_index": act, "floor": floor, "hp": hp, "max_hp": 80, "gold": 99, "deck": deck, "relics": [36, 5], "potions": [4],
                "boss": 83}

    def dec(kind: str, options: list[dict], chosen: int, floor: int, hp: int = 60) -> dict:
        return {"type": kind, "state": state(floor, hp=hp), "options": options, "chosen": chosen}

    rec = {"seed": "S", "generation": 9, "outcome": {"final_floor": 17, "won": False, "died": True, "truncated": False},
           "decisions": [dec("map", [{"kind": "map.node", "node": [0, 1, 2]}], 0, 1),
                         dec("card_reward", [{"kind": "card.take", "card": [18, 0, 0, 0]}, {"kind": "card.skip"}], 1, 2),
                         dec("rest", [{"kind": "rest.heal"}, {"kind": "rest.smith"}], 1, 8, hp=32),
                         dec("map", [{"kind": "map.node", "node": [0, 9, 4]}], 0, 9),
                         dec("map", [{"kind": "map.node", "node": [0, 16, 6]}], 0, 16),
                         dec("card_reward", [{"kind": "card.take", "card": [10, 0, 0, 0]}], 0, 17)],
           "fights": [{"floor": 17, "node_type": 6, "won": False, "state": state(17, hp=44)}]}
    s = be.ai_summary(rec, CARDS)
    a = s["a"][0]
    assert (a["r"], a["k"], a["at"], a["boss"], a["hp"], a["rel"], a["pot"]) == (1, 0, "boss", "VANTOM_BOSS", 44, 2, 1)
    assert a["path"] == "ES"  # the boss node and the boss reward are not before-boss choices
    assert a["rests"] == [[0.4, "smith"]] and a["offers"] == [[None, ["ARMAMENTS"]]]
    assert a["deck"] == ["ANGER", "BASH+", "DEFEND_IRONCLAD", "STRIKE_IRONCLAD"]
    assert s["a"][1] is None and s["tot"]["taken"] == 1 and s["tot"]["skipped"] == 1
    c = be.cell([s], 0, "lost", CARDS)
    assert c["n"] == 1 and c["upgraded"] == 1 and c["attack"] == 3 and c["skill"] == 1 and c["basic"] == 2


def test_night_rows_and_node_split() -> None:
    assert be.split_nodes("MM?RB MS?B".replace(" ", "")) == ["MM?R", "MS?", ""]
    row = {"seed": "X", "floor": 20, "win": False, "end": "death", "boss_damage_acts": [[0, 1.0]], "nodes": "MM?RBME",
           "cards": [[2, "ANGER"], [5, "skip"], [17, "INFLAME"], [19, "ARMAMENTS+"]], "rests": [[4, "smith"], [19, "heal"]]}
    s = be.night_summary(row)
    assert s["a"][0]["r"] == 1 and s["a"][0]["k"] == 1 and s["a"][0]["path"] == "MM?R"
    assert s["a"][0]["offers"] == [["ANGER", None], [None, None]]  # the boss reward (floor 17) is not a before-boss pick
    assert s["a"][1]["r"] == 0 and s["a"][1]["path"] == "ME" and s["a"][1]["rests"] == [[None, "heal"]]
    assert be.night_summary({**row, "crash": True}) is None


def test_small_human_cells_are_suppressed() -> None:
    runs = [be.human_summary(human_run(f"x{i}")) for i in range(be.MIN_CELL - 1)]
    rows = rep.entry_rows("Humans", runs, 0, CARDS, ("boss",))
    assert "suppressed" in rows[0][2]
    assert all("x0" not in " ".join(r) for r in rows)  # no run id in a table
    more = [be.human_summary(human_run(f"y{i}")) for i in range(be.MIN_CELL)]
    assert "suppressed" not in rep.entry_rows("Humans", more, 0, CARDS, ("boss",))[0][2]
    assert rep.headline_row("Humans", runs)[2] == "suppressed"
    assert "id" not in be.cell(more, 0, "boss", CARDS)


def test_logistic_fit_finds_the_signal() -> None:
    import random

    rnd = random.Random(1)
    rows = []
    for _ in range(3000):
        hp = rnd.random()
        rows.append({"r": 1, "k": int(rnd.random() < (0.15 + 0.7 * hp)), "hp": hp * 80, "mhp": 80, "gold": 100, "rel": 4, "pot": 1,
                     "deck": ["BASH+", "ANGER", "DEFEND_IRONCLAD"] * 6})
    coef = be.kill_model(rows, CARDS)
    assert coef[1 + be.FEATURES.index("hp_frac")] > 1.0
    cur = be.mean_vector(rows, CARDS)
    target = list(cur)
    target[0] += 0.2
    eff = be.shift_effects(coef, rows, target, CARDS)
    assert 0.05 < eff["hp_frac"] < 0.25 and abs(eff["gold"]) < 1e-9 and abs(eff["all"] - eff["hp_frac"]) < 1e-6
    assert be.kill_model(rows[:50], CARDS) is None


def test_rest_by_hp_and_pick_rates() -> None:
    runs = [{"a": [{"r": 1, "rests": [[0.3, "heal"], [0.9, "smith"], [0.5, "smith"]],
                    "offers": [["ANGER", ["ANGER", "INFLAME"]], [None, ["INFLAME"]]]}, None]}]
    r = be.rest_by_hp(runs, 0)
    assert r["<40%"] == [1, 0.0] and r[">=80%"] == [1, 1.0] and r["40-60%"] == [1, 1.0]
    p = be.pick_rates(runs, 0)
    assert p["ANGER"] == [1, 1] and p["INFLAME"] == [2, 0]
    assert Counter(be.hp_bin(x) for x in (0.1, 0.5, 0.7, 1.0)) == Counter({"<40%": 1, "40-60%": 1, "60-80%": 1, ">=80%": 1})


# ---------------------------------------------------------------------------------------------- the per-decision exam


def test_human_specs_for_the_exam() -> None:
    import boss_entry_exam as exam

    ids = exam.Ids({"STRIKE_IRONCLAD": 472, "DEFEND_IRONCLAD": 131, "BASH": 30, "ANGER": 13, "INFLAME": 10, "ARMAMENTS": 18,
                    "TWIN_STRIKE": 99, "ASCENDERS_BANE": 1, "SHRUG_IT_OFF": 98}, {"BURNING_BLOOD": 36, "ANCHOR": 3}, {})
    run = {**human_run(), "acts": ["ACT.OVERGROWTH", "ACT.HIVE"]}
    run["players"][0]["deck"] = [{"id": "CARD.BASH"}]
    specs = exam.human_specs(run, ids, CARDS)
    assert [(s["type"], s["floor"]) for s in specs] == [("card_reward", 2), ("rest", 3), ("card_reward", 4), ("rest", 5)]
    first = specs[0]
    assert first["offered"] == [10, 18] and first["picked"] == 0 and first["region"] == 1 and first["act"] == 0
    assert first["boss"] == 83  # the run met Vantom, so the act's boss is known
    assert len(first["deck"]) == 12 and [13, 0] in first["deck"] and first["relics"] == [36]  # the Anger from the Ancient, no Inflame yet
    assert (first["hp"], first["max_hp"]) == (70, 80)
    smith, elite, heal = specs[1], specs[2], specs[3]
    assert smith["chose"] == "smith" and smith["smith_card"] == 30 and smith["hp"] == 80
    assert elite["picked"] is None and elite["offered"] == [99]
    assert heal["chose"] == "heal" and heal["hp"] == 50 and heal["relics"] == [3, 36]  # HP before the heal; the Anchor is held by then
    assert len(heal["deck"]) == 13 and [30, 1] in heal["deck"]
    assert exam.replay_potions([pt("monster", potion_choices=[{"choice": "POTION.FIRE_POTION", "was_picked": True}],
                                   potion_used=["POTION.FIRE_POTION"])]) == Counter()


def test_agreement_measures_are_paired_by_decision() -> None:
    import boss_entry_exam as exam

    p = exam.paired([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0])
    assert (p["n"], p["candidate"], p["incumbent"], p["diff"]) == (4, 0.5, 0.25, 0.25) and abs(p["se"] - 0.25) < 1e-9
    assert exam.paired([], [])["n"] == 0 and exam.paired([1.0, 0.0], [1.0, 0.0])["se"] == 0.0
    card = {"top": 1, "human": 1, "ai_skip": False}
    rest = {"ai_smith": True, "human_smith": False, "ai_skip": None}
    assert exam.agree_flag(card, "card_reward") == 1.0 and exam.agree_flag(rest, "rest") == 0.0
    inc = [("card_reward", card), ("card_reward", {"top": 0, "human": 1, "ai_skip": True}), ("rest", rest), ("rest", None)]
    cand = [("card_reward", card), ("card_reward", card), ("rest", {"ai_smith": False, "human_smith": False, "ai_skip": None}), ("rest", rest)]
    doc = exam.agreement_doc([cand, inc], ["candidate-0"])
    assert doc["scored"] == 3 and doc["skipped_without_donor_maps"] == 1  # a decision any head could not score is left out of all
    m = doc["candidates"][0]["measures"]
    assert m["card_reward"]["n"] == 2 and m["card_reward"]["candidate"] == 1.0 and m["card_reward"]["incumbent"] == 0.5
    assert m["rest"]["n"] == 1 and m["rest"]["diff"] == 1.0
    assert doc["incumbent"]["agreement"] == {"card_reward": 0.5, "rest": 0.0}


def test_the_exam_fifth_specs_are_read_once_and_cached(tmp_path) -> None:
    import gzip
    import json

    import boss_entry_exam as exam

    ids = exam.Ids({"STRIKE_IRONCLAD": 472, "DEFEND_IRONCLAD": 131, "BASH": 30, "ANGER": 13, "INFLAME": 10, "ARMAMENTS": 18,
                    "TWIN_STRIKE": 99, "ASCENDERS_BANE": 1, "SHRUG_IT_OFF": 98}, {"BURNING_BLOOD": 36, "ANCHOR": 3}, {})
    corpus = tmp_path / "runs.jsonl.gz"
    with gzip.open(corpus, "wt", encoding="utf-8") as fh:
        for rid in ("in-fifth", "outside"):
            run = {**human_run(rid), "acts": ["ACT.OVERGROWTH", "ACT.HIVE"]}
            run["players"][0]["deck"] = [{"id": "CARD.BASH"}]
            fh.write(json.dumps(run, separators=(",", ":")) + "\n")
    ids_file = tmp_path / "fifth.txt"
    ids_file.write_text("in-fifth\n")
    cache = tmp_path / "cache" / "specs.jsonl.gz"
    got = exam.exam_specs(corpus, ids_file, cache, cards=CARDS, idm=ids)
    assert list(got) == ["in-fifth"] and [s["type"] for s in got["in-fifth"]] == ["card_reward", "rest", "card_reward", "rest"]
    assert cache.is_file()
    again = exam.exam_specs(corpus, ids_file, cache, cards=CARDS, idm=ids)  # from the cache
    assert again == got
    ids_file.write_text("in-fifth\noutside\n")
    wider = exam.exam_specs(corpus, ids_file, cache, cards=CARDS, idm=ids)  # another id list: the cache does not match
    assert sorted(wider) == ["in-fifth", "outside"]


def test_exam_table_from_rows(tmp_path) -> None:
    import json

    rows = ([{"type": "card_reward", "act": 0, "floor": 2, "top": 0, "human": 0, "rank": 0, "regret": 0.0, "ai_skip": False,
              "human_skip": False, "ai_card": 7, "human_card": 7, "offered": [7, 8]}] * 160 +
            [{"type": "card_reward", "act": 0, "floor": 3, "top": 2, "human": 1, "rank": 1, "regret": 0.5, "ai_skip": True,
              "human_skip": False, "ai_card": None, "human_card": 8, "offered": [7, 8]}] * 160 +
            [{"type": "rest", "act": 0, "floor": 5, "ai_smith": False, "human_smith": True, "hp_frac": 0.7, "heal_minus_best_smith": 0.1}] * 30)
    path = tmp_path / "exam.json"
    path.write_text(json.dumps({"runs": 10, "skipped": 0, "rows": rows}))
    idm = tmp_path / "id_map.json"
    idm.write_text(json.dumps({"cards": {"Anger": 7, "Inflame": 8}}))
    text, nums = rep.exam_section(path, idm)
    assert nums["card_Act 1"]["n"] == 320 and abs(nums["card_Act 1"]["same_choice"] - 0.5) < 1e-9
    assert abs(nums["card_Act 1"]["ai_skip"] - 0.5) < 1e-9 and nums["rest"]["human_smith"] == 1.0 and nums["rest"]["ai_smith"] == 0.0
    assert "Anger" in text and "60-80%" in text


def test_dose_rows_suppress_small_human_cells() -> None:
    def visit(k: int, hp: int) -> dict:
        return {"r": 1, "k": k, "hp": hp, "mhp": 80, "gold": 1, "rel": 4, "pot": 1, "deck": ["BASH+", "ANGER"]}

    ai = [{"a": [visit(i % 2, 60), None]} for i in range(100)]
    hum = [{"a": [visit(1, 20), None]} for _ in range(5)]
    rows = rep.dose_rows(ai, hum, 0, CARDS)
    hp_rows = [r for r in rows if r[1] in ("under 50%", "50-70%", "70-85%", "85% or more")]
    assert any(r[4] == "suppressed" for r in hp_rows)
    assert all(r[4] == "suppressed" or int(r[4].replace(",", "")) >= be.MIN_CELL for r in rows)


def test_replay_matches_the_final_deck() -> None:
    run = human_run()
    deck = be.replay_deck([p for a in run["map_point_history"] for p in a])
    run["players"][0]["deck"] = [{"id": f"CARD.{c}", **({"current_upgrade_level": lv} if lv else {})} for (c, lv), n in deck.items() for _ in range(n)]
    assert be.check_replay(run) == (True, True)
    run["players"][0]["deck"].append({"id": "CARD.ANGER"})
    assert be.check_replay(run)[0] is False
