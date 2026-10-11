"""Allow-list firewall over the STS2MCP schema-4 payload (leak test L6 and friends).

Fixture: tests/fixtures/sts2mcp_payload_example.json, SYNTHETIC, built from the mod's code
(r33hab/STS2MCP @ 5a63f92). Replace with recorded live payloads after the mod review.
"""

import copy
import logging
import random

import pytest

from spireline.infoset import firewall as fw
from spireline.infoset.canary import CANARY_PREFIX, assert_no_leaks, audit, plant_canaries, plant_control_canary
from spireline.infoset.schema import CardKey, det_seed, multiset_size


def K(card_id, **kw):
    """A CardKey as the fixture's cards produce it (the mod sends unplayable: false)."""
    kw.setdefault("unplayable", False)
    return CardKey(card_id, **kw)


def run(payload, policy=fw.DEFAULT_POLICY):
    return fw.apply_firewall(payload, policy)


def enemy(result, entity_id):
    return next(e for e in result.info_state.battle.enemies if e.entity_id == entity_id)


def reasons(result):
    return {d.path: d.reason for d in result.drops}


# --------------------------------------------------------------------------- fixture


def test_fixture_is_marked_synthetic(fixture_doc):
    assert fixture_doc["_synthetic"].startswith("SYNTHETIC FIXTURE")
    assert "5a63f92" in fixture_doc["_source"]["repo"]


def test_combat_payload_is_admitted(combat):
    r = run(combat)
    info = r.info_state
    assert info.supported and info.state_type == "monster"
    assert info.player.character_id == "DEFECT"
    assert [e.entity_id for e in info.battle.enemies] == ["TOADPOLE_0", "TWO_TAILED_RAT_0", "DECIMILLIPEDE_SEGMENT_1"]
    assert enemy(r, "TOADPOLE_0").monster_id == "TOADPOLE"
    assert enemy(r, "TOADPOLE_0").intents[0].damage == 10
    assert info.run.map_coord == (3, 2)
    assert r.meta.schema_version == 4 and r.meta.mod_commit == "5a63f92"
    assert "mod_warning:relic.fields.CrackedCore" in r.flags
    assert "hidden_read_detected" in r.flags  # the fixture carries hidden-read fields on purpose


# --------------------------------------------------------------------------- the four required properties


def test_seed_dropped(game_over, combat):
    r = run(game_over)
    assert not r.info_state.supported
    assert "seed" not in r.info_state.canonical_json()
    assert "7QK2M9XW4H" not in r.audit_text()
    assert reasons(r)["game_over.seed"] == fw.R_SEED
    assert "unsupported_screen:game_over" in r.flags
    # A seed planted anywhere, under any admitted block, is dropped with the seed reason.
    combat["seed"] = "AAAA111122"
    combat["battle"]["seed"] = "BBBB222233"
    combat["player"]["seed"] = "CCCC333344"
    r2 = run(combat)
    rs = reasons(r2)
    assert rs["seed"] == rs["battle.seed"] == rs["player.seed"] == fw.R_SEED
    for s in ("AAAA111122", "BBBB222233", "CCCC333344"):
        assert s not in r2.audit_text()


def test_ordered_piles_become_multisets(combat):
    r = run(combat)
    p = r.info_state.player
    assert p.draw_pile == (
        (K("COLD_SNAP"), 1),
        (K("DEFEND_DEFECT"), 2),
        (K("STRIKE_DEFECT"), 1),
        (K("STRIKE_DEFECT", upgrade_level=1), 1),
    )
    assert multiset_size(p.draw_pile) == p.draw_pile_count == 5
    assert p.discard_pile == ((K("DEFEND_DEFECT"), 1), (K("ZAP", cost_overrides=(("cost_this_turn", 0),)), 1))
    assert multiset_size(p.deck) == p.deck_count == 12
    rs = reasons(r)
    assert rs["player.draw_pile_ordered"] == fw.R_HIDDEN_READ
    for k in ("hand_ordered", "discard_pile_ordered", "exhaust_pile_ordered"):
        assert rs[f"player.{k}"] == fw.R_ORDERED
    assert rs["player.draw_pile[].uid"] == fw.R_PILE_UID
    assert not any(k for k in ("pile_count_mismatch:draw_pile",) if k in r.flags)
    # No permutation of either pile list (sorted view or true order) changes the InfoState.
    base = r.info_state.info_state_hash
    rng = random.Random(7)
    for _ in range(25):
        c = copy.deepcopy(combat)
        rng.shuffle(c["player"]["draw_pile"])
        rng.shuffle(c["player"]["draw_pile_ordered"])
        rng.shuffle(c["player"]["discard_pile"])
        rng.shuffle(c["player"]["deck"])
        assert run(c).info_state.info_state_hash == base


def test_move_follow_up_id_dropped(combat):
    r = run(combat)
    js = r.info_state.canonical_json()
    assert "REATTACH_MOVE" not in js  # the only follow-up id that appears nowhere else in the fixture
    assert reasons(r)["battle.enemies[].move_follow_up_id"] == fw.R_HIDDEN_READ
    assert next(d for d in r.drops if d.path == "battle.enemies[].move_follow_up_id").count == 3


def test_unknown_fields_dropped_and_logged(combat, caplog):
    combat["brand_new_top_level"] = {"x": 1}
    combat["player"]["novel_player_field"] = 5
    combat["player"]["hand"][0]["novel_card_field"] = "zzz"
    combat["battle"]["enemies"][0]["novel_enemy_field"] = [1, 2]
    combat["battle"]["enemies"][0]["intents"][0]["novel_intent_field"] = True
    combat["battle"]["enemies"][0]["status"][0]["fields"]["novel_power_field"] = 1
    with caplog.at_level(logging.DEBUG, logger="spireline.infoset.firewall"):
        r = run(combat)
    rs = reasons(r)
    expected = [
        "brand_new_top_level",
        "player.novel_player_field",
        "player.hand[].novel_card_field",
        "battle.enemies[].novel_enemy_field",
        "battle.enemies[].intents[].novel_intent_field",
        "battle.enemies[].status[].fields.novel_power_field",
    ]
    for path in expected:
        assert rs[path] == fw.R_NOT_LISTED, path
        assert any(path in rec.getMessage() for rec in caplog.records), f"{path} not logged"
    js = r.info_state.canonical_json()
    assert "novel" not in js and "zzz" not in js


# --------------------------------------------------------------------------- canaries (L6)


def test_canaries_never_leak(combat, game_over, caplog):
    for payload in (combat, game_over):
        planted, canaries = plant_canaries(payload)
        with caplog.at_level(logging.DEBUG, logger="spireline.infoset.firewall"):
            r = run(planted)
        assert_no_leaks(r, canaries, extra_texts=[caplog.text])
    planted, canaries = plant_canaries(combat)
    paths = {c.path for c in canaries}
    must = {
        "battle.enemies[0].move_id",
        "battle.enemies[0].move_follow_up_id",
        "battle.enemies[0].state_log[1]",
        "battle.enemies[1].ai_fields.CallForBackupCount",
        "battle.enemies[1].status[0].amount",
        "battle.enemies[2].revive.in_turns",
        "player.draw_pile_ordered[0].id",
        "player.relics[1].saved.AttacksPlayed",
        "player.hand[0].vs_targets[0].values.Damage",
        "run.start_time",
    }
    assert must <= paths, must - paths
    assert len(canaries) >= 40
    _, go_canaries = plant_canaries(game_over)
    assert "game_over.seed" in {c.path for c in go_canaries}


def test_control_canary_is_detected(combat):
    planted, control = plant_control_canary(combat)
    r = run(planted)
    leaks = audit(r, [control])
    assert leaks and leaks[0].canary.path == "battle.enemies[0].intents[0].label"
    assert CANARY_PREFIX in r.info_state.canonical_json()


def test_admitted_move_id_canary_is_reported_unless_declared(combat):
    policy = fw.FirewallPolicy.make(move_id_allow={"TOADPOLE"})
    planted, canaries = plant_canaries(combat)
    r = run(planted, policy)
    leaks = audit(r, canaries)
    assert {lk.canary.path for lk in leaks} == {"battle.enemies[0].move_id"}
    assert not audit(r, canaries, admitted_paths={"battle.enemies[0].move_id"})


# --------------------------------------------------------------------------- output depends on admitted fields only


def _perturb_hidden(payload, rng):
    p = copy.deepcopy(payload)
    pl, bt = p["player"], p["battle"]
    rng.shuffle(pl["draw_pile_ordered"])
    rng.shuffle(pl["draw_pile"])
    for e in bt["enemies"]:
        e["move_id"] = rng.choice(["A_MOVE", "B_MOVE", "C_MOVE"])
        e["move_follow_up_id"] = rng.choice(["X_MOVE", "Y_MOVE", None])
        e["combat_id"] = rng.randrange(1000)
        if e["state_log"]:
            e["state_log"][-1] = rng.choice(["P_MOVE", "Q_MOVE"])
        for k, v in list(e["ai_fields"].items()):
            e["ai_fields"][k] = (not v) if isinstance(v, bool) else rng.randrange(-5, 50)
        for s in e["status"]:
            if s.get("hidden_in_ui"):
                s["amount"] = rng.randrange(1, 9)
        if "revive" in e:
            e["revive"]["in_turns"] = rng.randrange(1, 4)
    p["run"]["start_time"] = rng.randrange(1_700_000_000, 1_800_000_000)
    for rel in pl["relics"]:
        if isinstance(rel.get("saved"), dict):
            for k in rel["saved"]:
                rel["saved"][k] = rng.randrange(100)
        for k in rel["fields"]:
            rel["fields"][k] = rng.randrange(100)
    for c in pl["hand"]:
        for vt in c.get("vs_targets", []):
            vt["combat_id"] = rng.randrange(1000)
            vt["values"] = {k: rng.randrange(30) for k in vt["values"]}
    return p


def test_hidden_values_do_not_change_info_state(combat):
    base = run(combat)
    rng = random.Random(2026)
    for _ in range(40):
        r = run(_perturb_hidden(combat, rng))
        assert r.info_state == base.info_state
        assert r.info_state.info_state_hash == base.info_state.info_state_hash
        assert r.drops == base.drops
        assert r.flags == base.flags


def test_hidden_read_equals_normal_read(combat):
    normal = copy.deepcopy(combat)
    del normal["player"]["draw_pile_ordered"]
    for e in normal["battle"]["enemies"]:
        del e["move_follow_up_id"]
    a, b = run(combat), run(normal)
    assert a.info_state == b.info_state
    assert "hidden_read_detected" in a.flags and "hidden_read_detected" not in b.flags


# --------------------------------------------------------------------------- per-field rules


def test_move_id_needs_the_per_monster_allow_list(combat):
    r = run(combat)
    assert all(e.move_id is None for e in r.info_state.battle.enemies)
    js = r.info_state.canonical_json()
    assert "WHIRL_MOVE" not in js and "CALL_FOR_BACKUP_MOVE" not in js and "DEAD_MOVE" not in js
    assert reasons(r)["battle.enemies[].move_id"] == fw.R_MOVE_ID
    r2 = run(combat, fw.FirewallPolicy.make(move_id_allow={"TOADPOLE"}))
    assert enemy(r2, "TOADPOLE_0").move_id == "WHIRL_MOVE"
    assert enemy(r2, "TWO_TAILED_RAT_0").move_id is None


def test_state_log_keeps_executed_moves_only(combat):
    r = run(combat)
    assert enemy(r, "TOADPOLE_0").state_log_executed == ("SPIKEN_MOVE",)
    rat = enemy(r, "TWO_TAILED_RAT_0")
    assert rat.state_log_executed == ("SCRATCH_MOVE",)
    assert "CALL_FOR_BACKUP_MOVE" not in r.info_state.canonical_json()  # pending move behind a Buff intent
    assert reasons(r)["battle.enemies[].state_log[-1]"] == fw.R_PENDING_MOVE
    assert "state_log_trim_unverified:dead" in r.flags  # the segment's last rolled move


def test_ai_fields_need_the_per_monster_allow_list(combat):
    r = run(combat)
    assert all(e.ai_fields == () for e in r.info_state.battle.enemies)
    rs = reasons(r)
    assert rs["battle.enemies[].ai_fields.CallForBackupCount"] == fw.R_AI_FIELD
    assert rs["battle.enemies[].ai_fields._isFront"] == fw.R_AI_FIELD
    policy = fw.FirewallPolicy.make(ai_fields_allow={"TWO_TAILED_RAT": {"CallForBackupCount"}})
    r2 = run(combat, policy)
    assert enemy(r2, "TWO_TAILED_RAT_0").ai_fields == (("CallForBackupCount", 0),)
    assert enemy(r2, "TOADPOLE_0").ai_fields == ()
    assert r2.policy_hash != r.policy_hash


def test_hidden_ui_power_dropped(combat):
    r = run(combat)
    assert enemy(r, "TWO_TAILED_RAT_0").powers == ()
    assert reasons(r)["battle.enemies[].status[]"] == fw.R_HIDDEN_POWER
    assert "RAT_BOOKKEEPING_POWER" not in r.info_state.canonical_json()
    r2 = run(combat, fw.FirewallPolicy.make(hidden_power_allow={"RAT_BOOKKEEPING_POWER"}))
    assert [p.id for p in enemy(r2, "TWO_TAILED_RAT_0").powers] == ["RAT_BOOKKEEPING_POWER"]


def test_revive_and_relic_raw_state_are_allow_listed(combat):
    r = run(combat)
    seg = enemy(r, "DECIMILLIPEDE_SEGMENT_1")
    assert seg.revive.power_id == "REATTACH_POWER" and seg.revive.hp == 25 and seg.revive.in_turns is None
    pen = next(x for x in r.info_state.player.relics if x.id == "PEN_NIB")
    assert pen.counter == 3 and pen.saved == () and pen.fields == ()
    r2 = run(combat, fw.FirewallPolicy.make(revive_in_turns_allow={"REATTACH_POWER"},
                                            relic_saved_allow={"PEN_NIB": {"AttacksPlayed"}}))
    assert enemy(r2, "DECIMILLIPEDE_SEGMENT_1").revive.in_turns == 2
    assert next(x for x in r2.info_state.player.relics if x.id == "PEN_NIB").saved == (("AttacksPlayed", 13),)


def test_hand_is_ordered_and_keeps_uids(combat):
    r = run(combat)
    hand = r.info_state.player.hand
    assert [c.uid for c in hand] == ["STRIKE_DEFECT#0", "ZAP#0", "DUALCAST#0", "DEFEND_DEFECT#1", "STRIKE_DEFECT#2"]
    assert hand[4].key.enchantment_id == "SHARP" and hand[4].key.enchantment_amount == 3
    assert [t.target for t in hand[0].vs_targets] == ["TOADPOLE_0", "TWO_TAILED_RAT_0"]
    assert reasons(r)["player.hand[].vs_targets[].values.Damage"] == fw.R_DYNVARS


def test_card_select_over_draw_pile_is_canonicalized(combat):
    def payload(order):
        p = copy.deepcopy(combat)
        p["state_type"] = "card_select"
        p["in_combat"] = True
        cards = [
            {"index": 0, "uid": "STRIKE_DEFECT#3", "id": "STRIKE_DEFECT", "name": "Strike+", "type": "Attack", "cost": "1",
             "star_cost": None, "description": "synthetic description", "rarity": "Basic", "is_upgraded": True, "upgrade_level": 1,
             "selected": False, "keywords": [], "enchantment": None, "affliction": None, "fields": {}, "unplayable": False},
            {"index": 1, "uid": "STRIKE_DEFECT#1", "id": "STRIKE_DEFECT", "name": "Strike", "type": "Attack", "cost": "1",
             "star_cost": None, "description": "synthetic description", "rarity": "Basic", "is_upgraded": False, "upgrade_level": 0,
             "selected": False, "keywords": [], "enchantment": None, "affliction": None, "fields": {}, "unplayable": False},
        ]
        cards = [cards[i] for i in order]
        for i, c in enumerate(cards):
            c["index"] = i
        p["card_select"] = {
            "screen_type": "simple_select", "prompt": "Choose a card.", "cards": cards, "selected_count": 0,
            "min_select": 1, "max_select": 1, "required_count": 1, "preview_showing": False, "can_confirm": False,
            "can_cancel": False,
            "selection": {"kind": "GRID", "pile": "DRAW", "prompt_key": "cards.SEEKER_STRIKE.selectionScreenPrompt",
                          "source": {"type": "card", "id": "SEEKER_STRIKE", "uid": "SEEKER_STRIKE#0"},
                          "min": 1, "max": 1, "can_skip": False, "selected": []}}
        return p

    a, b = run(payload([0, 1])), run(payload([1, 0]))
    assert a.info_state.supported and a.info_state.selection.cards_canonicalized
    assert a.info_state == b.info_state
    assert [c.uid for c in a.info_state.selection.cards] == ["STRIKE_DEFECT#1", "STRIKE_DEFECT#3"]


def test_unsupported_screen_and_schema_mismatch(combat):
    combat["state_type"] = "map"
    combat["map"] = {"nodes": [], "seed": "ZZZZ999999"}
    combat["schema_version"] = 3
    r = run(combat)
    assert not r.info_state.supported and r.info_state.battle is None
    rs = reasons(r)
    assert rs["map"] == fw.R_SCREEN and rs["map.seed"] == fw.R_SEED
    assert "unsupported_screen:map" in r.flags and "schema_version_mismatch:3" in r.flags


def test_info_state_is_hashable_and_stable(combat):
    a, b = run(combat).info_state, run(copy.deepcopy(combat)).info_state
    assert hash(a) == hash(b) and a.info_state_hash == b.info_state_hash
    assert len(a.info_state_hash) == 64
    s = [det_seed(a.info_state_hash, k) for k in range(4)]
    assert s == [det_seed(b.info_state_hash, k) for k in range(4)] and len(set(s)) == 4
    with pytest.raises(ValueError):
        det_seed(a.info_state_hash, -1)


def test_drop_log_never_holds_values(combat):
    planted, canaries = plant_canaries(combat)
    r = run(planted)
    blob = repr(r.drops)
    assert CANARY_PREFIX not in blob
    assert all("[" not in d.path or "[]" in d.path or "[-1]" in d.path for d in r.drops)


def test_malformed_entries_are_logged_not_silently_lost(combat):
    combat["player"]["hand"].append("not-a-card")
    combat["player"]["relics"] = {"oops": 1}
    combat["battle"]["enemies"][0]["revive"] = "soon"
    r = run(combat)
    rs = reasons(r)
    assert rs["player.hand[]"] == fw.R_BAD_TYPE
    assert rs["player.relics"] == fw.R_BAD_TYPE
    assert len(r.info_state.player.hand) == 5 and r.info_state.player.relics == ()
    assert "soon" not in r.info_state.canonical_json()
    assert rs["battle.enemies[].revive"] == fw.R_NOT_LISTED
