"""Allow-list firewall: STS2MCP schema-4 payload -> InfoState.

Source of truth for field names and nesting: r33hab/STS2MCP @ 5a63f92 (spire-coach branch),
McpMod.StateBuilder.cs, McpMod.StateExtras.cs, McpMod.Selection.cs, McpMod.Warnings.cs and
docs/raw-full.md. Citations below are file:line at that commit.

Rules (design v1.1 §1.1, §2.2 invariants, §3.2):

1. **Allow-list.** A payload key that is not explicitly read here is dropped and logged.
2. **Never values in logs.** The drop log holds `(path, reason, count)` with list indices
   collapsed to `[]`. It never holds a value, so a canary planted in a dropped field can
   only surface if the field was admitted. Key *presence* can itself depend on hidden
   state (a nullable ai_field is omitted when null, McpMod.StateExtras.cs:642; a hidden-UI
   power appears only when it has a stack), so the drop log is for allow-list curation and
   must never feed priors, values or features.
3. **Output depends on admitted fields only.** No admitted field is computed from a dropped
   one (e.g. the state_log trim below does not look at `move_id`). tests/test_firewall.py
   checks this by perturbing every hidden value and comparing InfoState hashes.
4. **Piles are multisets.** draw/discard/exhaust/play piles and the master deck become
   sorted `(CardKey, count)` pairs. Beyond the documented `*_ordered` lists this also
   closes a quieter channel: `draw_pile` is sorted by (rarity, id) with `List.Sort`
   (McpMod.StateBuilder.cs:1733-1737), which is not stable, so the relative order of
   same-id cards that differ in upgrade or enchantment can depend on the true draw order.
5. **Always dropped:** every `seed` (game_over.seed, McpMod.StateBuilder.cs:535-539),
   `draw_pile_ordered` (hidden read only, McpMod.StateBuilder.cs:1760-1761),
   `move_follow_up_id` (hidden read only, McpMod.StateExtras.cs:229-230), the other
   `*_ordered` lists (McpMod.StateBuilder.cs:1762-1769), `run.start_time`
   (McpMod.StateBuilder.cs:698-700; wall-clock run start, a possible seed correlate).
6. **Per-monster allow-lists, initially empty:** `move_id` (McpMod.StateExtras.cs:216-228;
   admitted only after L8 shows the displayed intent identifies the move) and `ai_fields`
   (McpMod.StateExtras.cs:316-330; every primitive member of the monster class, admitted
   key by key after L7 shows it deducible from observed history).
7. **state_log.** Its last entry is normally the current, rolled-but-unexecuted move
   (docs/raw-full.md:718-722), i.e. the same information as `move_id`. The firewall always
   trims the last entry, using no hidden field to decide. This can only lose information
   (a move installed without a roll, e.g. a stun, is not logged); stunned, dead and
   enemy-turn reads are flagged `state_log_trim_unverified:*` until live captures confirm.
8. **Conservative extras.** Powers the game hides from the HUD (`hidden_in_ui`,
   McpMod.StateBuilder.cs:4214-4220, 4265-4266), `revive.in_turns` (walks `FollowUpState`,
   the edge `move_follow_up_id` exposes, McpMod.StateBuilder.cs:2669-2686), relic raw
   `saved`/`fields` (McpMod.StateExtras.cs:394-441; the displayed `counter` is kept), and
   card dynamic vars `vs_targets[].values` (McpMod.StateBuilder.cs:2096-2110) each have an
   allow-list, initially empty.
9. **Screens.** v0 admits combat (`monster`/`elite`/`boss`), `hand_select` and an
   in-combat `card_select`. A grid over the draw pile is re-sorted canonically, because a
   screen sort over draw order can leave ties in draw order (McpMod.StateBuilder.cs:3692-3716).
   Every other screen block is dropped and the InfoState is marked `supported=False`.

The adapter must never request `?hidden=1` (McpMod.Helpers.cs:177-178). If a payload
carries hidden-read fields anyway, they are dropped and `hidden_read_detected` is flagged.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping

from .schema import (
    BattleState,
    CardKey,
    Creature,
    DamageCap,
    HandCard,
    InfoState,
    Intent,
    Orb,
    Pet,
    PlayerState,
    Potion,
    Power,
    Relic,
    Revive,
    RunInfo,
    SelectCard,
    SelectionState,
    TargetPreview,
    multiset,
    multiset_size,
)

log = logging.getLogger("spireline.infoset.firewall")

EXPECTED_SCHEMA_VERSION = 4  # McpMod.cs:55
COMBAT_SCREENS = frozenset({"monster", "elite", "boss"})
SELECTION_SCREENS = frozenset({"hand_select", "card_select"})

# ----------------------------------------------------------------------------- reasons

R_SEED = "seed: always dropped (design §3.2; McpMod.StateBuilder.cs:535-539)"
R_HIDDEN_READ = "hidden-information field, present only on ?hidden=1 reads (docs/raw-full.md:86-101)"
R_ORDERED = "ordered pile list: piles are multisets (design §1.1; McpMod.StateBuilder.cs:1750-1769)"
R_NOT_LISTED = "not on the allow-list"
R_DISPLAY_TEXT = "display text, derivable from ids; not kept"
R_REDUNDANT = "redundant with a kept field or derivable from the card id"
R_PILE_UID = "pile card uid: piles are multisets, card identity is not kept"
R_INTERNAL_ID = "internal id, not displayed (entity_id is kept for targeting)"
R_MOVE_ID = "move_id: monster not on the move_id allow-list (L8; design §3.2)"
R_AI_FIELD = "ai_fields entry not on the per-monster deducible list (L7; design §3.2)"
R_PENDING_MOVE = "state_log tail: the current rolled move, not yet executed (docs/raw-full.md:718-722)"
R_HIDDEN_POWER = "power hidden in the game UI (McpMod.StateBuilder.cs:4214-4220, 4265-4266)"
R_REVIVE_TURNS = "revive.in_turns walks FollowUpState (McpMod.StateBuilder.cs:2669-2686); not on the allow-list"
R_RELIC_RAW = "relic raw state not on the per-relic allow-list; the displayed counter is kept"
R_DYNVARS = "card dynamic vars at preview (McpMod.StateBuilder.cs:2096-2110); damage/hits/block kept"
R_CLOCK = "run.start_time: wall-clock run start, not displayed, a possible seed correlate"
R_SCREEN = "screen block not allow-listed in firewall v0 (combat screens only)"
R_ADAPTER = "UI-flow field for the action adapter, not part of the information state"
R_PROVENANCE = "provenance, moved to meta (not part of the information state)"
R_BAD_TYPE = "unexpected JSON type for this field; dropped"

_FORBIDDEN_KEYS: dict[str, str] = {
    "seed": R_SEED,
    "draw_pile_ordered": R_HIDDEN_READ,
    "move_follow_up_id": R_HIDDEN_READ,
    "hand_ordered": R_ORDERED,
    "discard_pile_ordered": R_ORDERED,
    "exhaust_pile_ordered": R_ORDERED,
    "rng": R_NOT_LISTED,
    "rng_state": R_NOT_LISTED,
    "draw_order": R_NOT_LISTED,
}
_DISPLAY_TEXT_KEYS = frozenset(
    {"name", "description", "title", "keywords", "prompt", "character", "message", "power_name", "note",
     "capped_by_text", "upgrade_preview", "preview_cards"}
)
_SCREEN_BLOCK_KEYS = frozenset(
    {"map", "rewards", "card_reward", "event", "rest_site", "shop", "fake_merchant", "treasure",
     "card_select", "bundle_select", "relic_select", "crystal_sphere", "game_over", "overlay",
     "hand_select", "battle", "menu_screen", "loaded_mods", "room_type", "character_select"}
)
_COST_OVERRIDE_KEYS = frozenset({"cost_this_turn", "cost_until_played", "cost_for_combat"})  # StateExtras.cs:147-163
_POWER_FIELD_KEYS = frozenset(  # McpMod.StateExtras.cs:458-492
    {"has_gained_block_this_turn", "facing", "stolen", "stolen_card", "stolen_card_upgraded", "stolen_gold"}
)
_HISTORY_KEYS = frozenset(  # McpMod.StateExtras.cs:548-555
    {"cards_played_this_turn", "attacks_played_this_turn", "skills_played_this_turn",
     "powers_played_this_turn", "cards_played_this_combat"}
)
_ENTITY_SUFFIX = re.compile(r"_\d+$")  # entity_id = f"{Monster.Id.Entry}_{n}", McpMod.StateBuilder.cs:2437-2450


# ----------------------------------------------------------------------------- policy


def _freeze_map(m: Mapping[str, Any] | None) -> tuple[tuple[str, frozenset[str]], ...]:
    if not m:
        return ()
    return tuple(sorted((k, frozenset(v)) for k, v in m.items()))


@dataclass(frozen=True)
class FirewallPolicy:
    """Every allow-list the firewall consults. All start empty; each entry needs evidence.

    - `move_id_allow`: monster ids whose displayed intent identifies the current move (L8).
    - `ai_fields_allow`: monster id -> ai_fields keys proven deducible from history (L7),
      e.g. a candidate is TWO_TAILED_RAT: {"CallForBackupCount"} (design §3.2), not yet admitted.
    - `relic_saved_allow` / `relic_fields_allow`: relic id -> raw keys proven deducible.
    - `hidden_power_allow`: power ids admitted although the HUD hides them.
    - `revive_in_turns_allow`: power ids whose revive countdown is a fixed rule (e.g. a
      candidate is REATTACH_POWER), not yet admitted.
    - `dynvar_allow`: card dynamic-var names admitted from `vs_targets[].values`.
    """

    move_id_allow: frozenset[str] = frozenset()
    ai_fields_allow: tuple[tuple[str, frozenset[str]], ...] = ()
    relic_saved_allow: tuple[tuple[str, frozenset[str]], ...] = ()
    relic_fields_allow: tuple[tuple[str, frozenset[str]], ...] = ()
    hidden_power_allow: frozenset[str] = frozenset()
    revive_in_turns_allow: frozenset[str] = frozenset()
    dynvar_allow: frozenset[str] = frozenset()
    expected_schema_version: int = EXPECTED_SCHEMA_VERSION

    @classmethod
    def make(
        cls,
        *,
        move_id_allow=(),
        ai_fields_allow: Mapping[str, Any] | None = None,
        relic_saved_allow: Mapping[str, Any] | None = None,
        relic_fields_allow: Mapping[str, Any] | None = None,
        hidden_power_allow=(),
        revive_in_turns_allow=(),
        dynvar_allow=(),
        expected_schema_version: int = EXPECTED_SCHEMA_VERSION,
    ) -> "FirewallPolicy":
        return cls(
            move_id_allow=frozenset(move_id_allow),
            ai_fields_allow=_freeze_map(ai_fields_allow),
            relic_saved_allow=_freeze_map(relic_saved_allow),
            relic_fields_allow=_freeze_map(relic_fields_allow),
            hidden_power_allow=frozenset(hidden_power_allow),
            revive_in_turns_allow=frozenset(revive_in_turns_allow),
            dynvar_allow=frozenset(dynvar_allow),
            expected_schema_version=expected_schema_version,
        )

    def _lookup(self, table: tuple[tuple[str, frozenset[str]], ...], key: str) -> frozenset[str]:
        for k, v in table:
            if k == key:
                return v
        return frozenset()

    def ai_fields_for(self, monster_id: str) -> frozenset[str]:
        return self._lookup(self.ai_fields_allow, monster_id)

    def relic_saved_for(self, relic_id: str) -> frozenset[str]:
        return self._lookup(self.relic_saved_allow, relic_id)

    def relic_fields_for(self, relic_id: str) -> frozenset[str]:
        return self._lookup(self.relic_fields_allow, relic_id)

    def to_jsonable(self) -> dict[str, Any]:
        def m(t):
            return {k: sorted(v) for k, v in t}

        return {
            "move_id_allow": sorted(self.move_id_allow),
            "ai_fields_allow": m(self.ai_fields_allow),
            "relic_saved_allow": m(self.relic_saved_allow),
            "relic_fields_allow": m(self.relic_fields_allow),
            "hidden_power_allow": sorted(self.hidden_power_allow),
            "revive_in_turns_allow": sorted(self.revive_in_turns_allow),
            "dynvar_allow": sorted(self.dynvar_allow),
            "expected_schema_version": self.expected_schema_version,
        }

    @property
    def policy_hash(self) -> str:
        blob = json.dumps(self.to_jsonable(), sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode()).hexdigest()


DEFAULT_POLICY = FirewallPolicy()


# ----------------------------------------------------------------------------- result


@dataclass(frozen=True, slots=True)
class Drop:
    path: str
    reason: str
    count: int


@dataclass(frozen=True, slots=True)
class PayloadMeta:
    """Provenance and settle information. Not part of the InfoState or its hash."""

    schema_version: int | None = None
    mod_version: str | None = None
    mod_commit: str | None = None
    action_log_seq: int | None = None
    time_scale: float | None = None
    rooms_entered: int | None = None
    is_resolving: bool | None = None
    resolving_reasons: tuple[str, ...] = ()
    warning_contexts: tuple[str, ...] = ()  # the context part of each mod warning only


@dataclass(frozen=True)
class FirewallResult:
    info_state: InfoState
    drops: tuple[Drop, ...]
    flags: tuple[str, ...]
    meta: PayloadMeta
    policy_hash: str

    @property
    def dropped_paths(self) -> frozenset[str]:
        return frozenset(d.path for d in self.drops)

    def drops_by_path(self) -> dict[str, Drop]:
        return {d.path: d for d in self.drops}

    def audit_text(self) -> str:
        """Everything this result could hand downstream, as one string (for canary audits)."""
        return "\n".join(
            [
                self.info_state.canonical_json(),
                json.dumps([[d.path, d.reason, d.count] for d in self.drops]),
                json.dumps(list(self.flags)),
                repr(self.meta),
                repr(self),
            ]
        )


class FirewallError(ValueError):
    """The payload cannot be read as an information state at all."""


# ----------------------------------------------------------------------------- walking


class _Drops:
    def __init__(self) -> None:
        self._c: Counter[tuple[str, str]] = Counter()

    def add(self, path: str, reason: str, n: int = 1) -> None:
        self._c[(path, reason)] += n

    def freeze(self) -> tuple[Drop, ...]:
        return tuple(Drop(p, r, n) for (p, r), n in sorted(self._c.items()))


def _reason_for(key: str) -> str:
    if key in _FORBIDDEN_KEYS:
        return _FORBIDDEN_KEYS[key]
    if key in _DISPLAY_TEXT_KEYS:
        return R_DISPLAY_TEXT
    if key in _SCREEN_BLOCK_KEYS:
        return R_SCREEN
    return R_NOT_LISTED


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _scan_forbidden(obj: Any, path: str, drops: _Drops) -> None:
    """Inside a subtree dropped wholesale, still name every forbidden key it contained."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = _join(path, k)
            if k in _FORBIDDEN_KEYS:
                drops.add(p, _FORBIDDEN_KEYS[k])
            _scan_forbidden(v, p, drops)
    elif isinstance(obj, list):
        for v in obj:
            _scan_forbidden(v, f"{path}[]", drops)


class _R:
    """Reads a payload object; whatever it does not read is logged as dropped on finish()."""

    __slots__ = ("d", "path", "drops", "used")

    def __init__(self, d: Any, path: str, drops: _Drops) -> None:
        self.d = d if isinstance(d, dict) else {}
        self.path = path
        self.drops = drops
        self.used: set[str] = set()

    def has(self, key: str) -> bool:
        return key in self.d

    def raw(self, key: str) -> Any:
        self.used.add(key)
        return self.d.get(key)

    def drop(self, key: str, reason: str) -> None:
        self.used.add(key)
        if key in self.d:
            self.drops.add(_join(self.path, key), reason)
            _scan_forbidden(self.d[key], _join(self.path, key), self.drops)

    def int(self, key: str) -> int | None:
        v = self.raw(key)
        return v if isinstance(v, int) and not isinstance(v, bool) else None

    def num(self, key: str) -> float | None:
        v = self.raw(key)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    def str(self, key: str) -> str | None:
        v = self.raw(key)
        return v if isinstance(v, str) else None

    def bool(self, key: str) -> bool | None:
        v = self.raw(key)
        return v if isinstance(v, bool) else None

    def obj(self, key: str) -> "_R":
        v = self.raw(key)
        p = _join(self.path, key)
        if v is not None and not isinstance(v, dict):
            self.drops.add(p, R_BAD_TYPE)
        return _R(v, p, self.drops)

    def items(self, key: str) -> list["_R"]:
        v = self.raw(key)
        p = _join(self.path, key)
        if v is None:
            return []
        if not isinstance(v, list):
            self.drops.add(p, R_BAD_TYPE)
            return []
        out = []
        for x in v:
            if isinstance(x, dict):
                out.append(_R(x, f"{p}[]", self.drops))
            else:
                self.drops.add(f"{p}[]", R_BAD_TYPE)
        return out

    def finish(self) -> None:
        for k, v in self.d.items():
            if k not in self.used:
                p = _join(self.path, k)
                self.drops.add(p, _reason_for(k))
                _scan_forbidden(v, p, self.drops)


def _monster_id(entity_id: str) -> str:
    return _ENTITY_SUFFIX.sub("", entity_id)


def _scalar_or_tuple(v: Any) -> Any:
    if isinstance(v, list):
        return tuple(_scalar_or_tuple(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _scalar_or_tuple(x)) for k, x in v.items()))
    return v


def _filtered_fields(r: _R, allowed: frozenset[str], reason: str) -> tuple[tuple[str, Any], ...]:
    """Admit only `allowed` keys of a raw dict; log each other key by name (never its value)."""
    kept = []
    for k in sorted(r.d):
        r.used.add(k)
        if k in allowed:
            kept.append((k, _scalar_or_tuple(r.d[k])))
        else:
            r.drops.add(_join(r.path, k), reason)
    return tuple(kept)


class _Firewall:
    def __init__(self, policy: FirewallPolicy) -> None:
        self.p = policy
        self.drops = _Drops()
        self.flags: set[str] = set()

    # ---- cards

    def card_key(self, r: _R) -> CardKey:
        cid = r.str("id") or "<missing>"
        if cid == "<missing>":
            self.flags.add(f"missing_card_id:{r.path}")
        level = r.int("upgrade_level")
        upgraded = r.bool("is_upgraded")  # read for the fallback only; the level carries it
        if level is None:
            level = 1 if upgraded else 0
        ench = r.obj("enchantment")
        ench_id, ench_amt = ench.str("id"), ench.int("amount")
        ench.finish()
        overrides: tuple = ()
        if r.has("fields"):
            fr = r.obj("fields")
            overrides = _filtered_fields(fr, _COST_OVERRIDE_KEYS, R_NOT_LISTED)
        return CardKey(
            id=cid,
            upgrade_level=level,
            enchantment_id=ench_id,
            enchantment_amount=ench_amt,
            affliction=r.str("affliction"),
            cost_overrides=overrides,
            unplayable=r.bool("unplayable"),
        )

    def pile_card(self, r: _R) -> CardKey:
        """Pile Card Object (McpMod.StateBuilder.cs:2234-2254) or Deck Card Object (1931-1950, 1907-1908)."""
        r.drop("uid", R_PILE_UID)
        for k in ("cost", "star_cost", "type", "rarity", "is_upgradable", "max_upgrade_level", "index"):
            r.drop(k, R_REDUNDANT)
        k = self.card_key(r)
        r.finish()
        return k

    def pile(self, parent: _R, key: str) -> tuple:
        return multiset(self.pile_card(c) for c in parent.items(key))

    def hand_card(self, r: _R) -> HandCard:
        """Card Object in hand (McpMod.StateBuilder.cs:1986-2003)."""
        uid = r.str("uid") or ""
        for k in ("index", "rarity", "is_upgradable", "max_upgrade_level"):
            r.drop(k, R_REDUNDANT)
        key = self.card_key(r)
        previews = tuple(self.target_preview(t) for t in r.items("vs_targets"))
        hc = HandCard(
            uid=uid,
            key=key,
            type=r.str("type"),
            cost=r.str("cost"),
            star_cost=r.str("star_cost"),
            target_type=r.str("target_type"),
            can_play=r.bool("can_play"),
            unplayable_reason=r.str("unplayable_reason"),
            vs_targets=previews,
        )
        r.finish()
        return hc

    def target_preview(self, r: _R) -> TargetPreview:
        """vs_targets entry (McpMod.StateBuilder.cs:2042-2078)."""
        r.drop("combat_id", R_INTERNAL_ID)
        if r.has("values"):
            vr = r.obj("values")
            _filtered_fields(vr, self.p.dynvar_allow, R_DYNVARS)
        cap = None
        if r.has("damage_cap") and isinstance(r.d.get("damage_cap"), dict):
            cr = r.obj("damage_cap")
            cap = DamageCap(
                capped_by=cr.str("capped_by"),
                power_id=cr.str("power_id"),
                per_hit_max=cr.int("per_hit_max"),
                per_turn_max=cr.int("per_turn_max"),
                effective_damage=cr.int("effective_damage"),
            )
            cr.finish()
        else:
            r.raw("damage_cap")
        tp = TargetPreview(
            target=r.str("target") or "",
            damage=r.int("damage"),
            hits=r.int("hits"),
            total_damage=r.int("total_damage"),
            block=r.int("block"),
            damage_cap=cap,
        )
        r.finish()
        return tp

    # ---- powers, relics, potions, orbs

    def powers(self, parent: _R, key: str) -> tuple[Power, ...]:
        """Power Objects (McpMod.StateBuilder.cs:4209-4281)."""
        out = []
        for r in parent.items(key):
            pid = r.d.get("id") if isinstance(r.d.get("id"), str) else None
            if r.d.get("hidden_in_ui") is True and pid not in self.p.hidden_power_allow:
                self.drops.add(r.path, R_HIDDEN_POWER)  # the whole entry; its keys are not walked
                continue
            r.raw("hidden_in_ui")
            r.drop("description_unavailable", R_DISPLAY_TEXT)
            fields: tuple | None = ()
            if r.has("fields"):
                raw = r.d.get("fields")
                if raw is None:
                    r.raw("fields")
                    fields = None
                else:
                    fields = _filtered_fields(r.obj("fields"), _POWER_FIELD_KEYS, R_NOT_LISTED)
            out.append(
                Power(
                    id=r.str("id") or "<missing>",
                    amount=r.int("amount"),
                    type=r.str("type"),
                    display_amount=r.int("display_amount"),
                    fields=fields,
                )
            )
            r.finish()
        return tuple(out)

    def relic(self, r: _R) -> Relic:
        """Relic object (McpMod.StateBuilder.cs:1817-1833, McpMod.StateExtras.cs:375-441)."""
        rid = r.str("id") or "<missing>"
        saved: tuple = ()
        if r.has("saved"):
            if isinstance(r.d.get("saved"), dict):
                saved = _filtered_fields(r.obj("saved"), self.p.relic_saved_for(rid), R_RELIC_RAW)
            else:
                r.raw("saved")
        fields: tuple = ()
        if r.has("fields"):
            if isinstance(r.d.get("fields"), dict):
                fields = _filtered_fields(r.obj("fields"), self.p.relic_fields_for(rid), R_RELIC_RAW)
            else:
                r.raw("fields")
        rel = Relic(
            id=rid,
            counter=r.int("counter"),
            status=r.str("status"),
            is_used_up=r.bool("is_used_up"),
            stack_count=r.int("stack_count"),
            saved=saved,
            fields=fields,
        )
        r.finish()
        return rel

    def potion(self, r: _R) -> Potion:
        """Potion object (McpMod.StateBuilder.cs:1836-1855)."""
        slot = r.int("slot")
        p = Potion(
            id=r.str("id") or "<missing>",
            slot=slot if slot is not None else -1,
            can_use_in_combat=r.bool("can_use_in_combat"),
            target_type=r.str("target_type"),
        )
        r.finish()
        return p

    def orb(self, r: _R) -> Orb:
        """Orb object (McpMod.StateBuilder.cs:1771-1801)."""
        o = Orb(id=r.str("id") or "<missing>", passive_val=r.int("passive_val"), evoke_val=r.int("evoke_val"))
        r.finish()
        return o

    def pet(self, r: _R) -> Pet:
        """Pet (McpMod.StateBuilder.cs:4315-4338)."""
        p = Pet(
            id=r.str("id") or "<missing>",
            alive=bool(r.bool("alive")),
            hp=r.int("hp") or 0,
            max_hp=r.int("max_hp") or 0,
            block=r.int("block") or 0,
            powers=self.powers(r, "status"),
        )
        r.finish()
        return p

    # ---- player

    def player(self, r: _R) -> PlayerState | None:
        """Player Object (McpMod.StateBuilder.cs:1686-1861)."""
        if not r.d:
            return None
        r.drop("draw_pile_ordered", R_HIDDEN_READ)
        if "draw_pile_ordered" in r.d:
            self.flags.add("hidden_read_detected")
        for k in ("hand_ordered", "discard_pile_ordered", "exhaust_pile_ordered"):
            r.drop(k, R_ORDERED)
        hand = tuple(self.hand_card(c) for c in r.items("hand"))
        draw, discard = self.pile(r, "draw_pile"), self.pile(r, "discard_pile")
        exhaust, play = self.pile(r, "exhaust_pile"), self.pile(r, "play_pile")
        deck = self.pile(r, "deck")
        ps = PlayerState(
            character_id=r.str("character_id"),
            hp=r.int("hp") or 0,
            max_hp=r.int("max_hp") or 0,
            block=r.int("block") or 0,
            gold=r.int("gold"),
            energy=r.int("energy"),
            max_energy=r.int("max_energy"),
            stars=r.int("stars"),
            hand=hand,
            draw_pile=draw,
            discard_pile=discard,
            exhaust_pile=exhaust,
            play_pile=play,
            draw_pile_count=r.int("draw_pile_count"),
            discard_pile_count=r.int("discard_pile_count"),
            exhaust_pile_count=r.int("exhaust_pile_count"),
            orbs=tuple(self.orb(o) for o in r.items("orbs")),
            orb_slots=r.int("orb_slots"),
            orb_empty_slots=r.int("orb_empty_slots"),
            pets=tuple(self.pet(p) for p in r.items("pets")),
            powers=self.powers(r, "status"),
            relics=tuple(self.relic(x) for x in r.items("relics")),
            potions=tuple(self.potion(x) for x in r.items("potions")),
            max_potion_slots=r.int("max_potion_slots"),
            deck_count=r.int("deck_count"),
            deck=deck,
        )
        for name, ms, n in (
            ("draw_pile", draw, ps.draw_pile_count),
            ("discard_pile", discard, ps.discard_pile_count),
            ("exhaust_pile", exhaust, ps.exhaust_pile_count),
            ("deck", deck, ps.deck_count),
        ):
            if n is not None and r.has(name) and multiset_size(ms) != n:
                self.flags.add(f"pile_count_mismatch:{name}")
        r.finish()
        return ps

    # ---- battle

    def creature(self, r: _R, turn: str | None) -> Creature:
        """Enemy or ally (McpMod.StateBuilder.cs:2507-2571, McpMod.StateExtras.cs:212-240)."""
        entity_id = r.str("entity_id") or "<missing>"
        mid = _monster_id(entity_id)
        r.drop("combat_id", R_INTERNAL_ID)
        r.drop("move_follow_up_id", R_HIDDEN_READ)
        if "move_follow_up_id" in r.d:
            self.flags.add("hidden_read_detected")

        alive = bool(r.bool("alive")) if r.has("alive") else True
        is_stunned = r.bool("is_stunned")

        if mid in self.p.move_id_allow:
            move_id = r.str("move_id")
        else:
            move_id = None
            r.drop("move_id", R_MOVE_ID)

        executed: tuple[str, ...] | None = None
        raw_log = r.raw("state_log")
        if isinstance(raw_log, list):
            if raw_log:
                self.drops.add(f"{r.path}.state_log[-1]", R_PENDING_MOVE)
                if is_stunned:
                    self.flags.add("state_log_trim_unverified:stunned")
                if not alive:
                    self.flags.add("state_log_trim_unverified:dead")
                if turn != "player":
                    self.flags.add(f"state_log_trim_unverified:turn={turn}")
            executed = tuple(x for x in raw_log[:-1] if isinstance(x, str))

        ai: tuple = ()
        if r.has("ai_fields"):
            if isinstance(r.d.get("ai_fields"), dict):
                ai = _filtered_fields(r.obj("ai_fields"), self.p.ai_fields_for(mid), R_AI_FIELD)
            else:
                r.raw("ai_fields")

        revive = None
        if r.has("revive") and isinstance(r.d.get("revive"), dict):
            rr = r.obj("revive")
            pid = rr.str("power_id")
            if pid in self.p.revive_in_turns_allow:
                in_turns = rr.int("in_turns")
            else:
                in_turns = None
                rr.drop("in_turns", R_REVIVE_TURNS)
            revive = Revive(power_id=pid, hp=rr.int("hp"), in_turns=in_turns)
            rr.finish()

        intents = []
        for ir in r.items("intents"):
            intents.append(
                Intent(
                    type=ir.str("type") or "<missing>",
                    label=ir.str("label"),
                    title=ir.str("title"),
                    description=ir.str("description"),
                    damage=ir.int("damage"),
                    base_damage=ir.int("base_damage"),
                    hits=ir.int("hits"),
                )
            )
            ir.finish()

        c = Creature(
            entity_id=entity_id,
            monster_id=mid,
            alive=alive,
            hp=r.int("hp") or 0,
            max_hp=r.int("max_hp") or 0,
            block=r.int("block") or 0,
            powers=self.powers(r, "status"),
            intents=tuple(intents),
            is_stunned=is_stunned,
            slot=r.int("slot"),
            state_log_executed=executed,
            move_id=move_id,
            ai_fields=ai,
            revive=revive,
        )
        r.finish()
        return c

    def battle(self, r: _R) -> BattleState | None:
        """Battle block (McpMod.StateBuilder.cs:1636-1681)."""
        if not r.d:
            return None
        if r.has("error"):
            self.flags.add("battle_error")
            r.drop("error", R_NOT_LISTED)
        turn = r.str("turn")
        history = None
        if r.has("history") and isinstance(r.d.get("history"), dict):
            history = _filtered_fields(r.obj("history"), _HISTORY_KEYS, R_NOT_LISTED)
        else:
            r.raw("history")
        b = BattleState(
            round=r.int("round"),
            turn=turn,
            is_play_phase=r.bool("is_play_phase"),
            enemies=tuple(self.creature(e, turn) for e in r.items("enemies")),
            allies=tuple(self.creature(a, turn) for a in r.items("allies")),
            history=history,
        )
        r.finish()
        return b

    # ---- selection screens

    def selection(self, screen: str, r: _R) -> SelectionState:
        """hand_select (McpMod.StateBuilder.cs:3898-3960) or card_select (3659-3760); selection
        object (McpMod.Selection.cs:101-139; docs/raw-full.md:1209-1260)."""
        sel = r.obj("selection")
        src = sel.obj("source")
        source = (src.str("type"), src.str("id"), src.str("uid"))
        src.finish()
        selected = []
        for s in sel.items("selected"):
            uid = s.str("uid")
            s.raw("id")
            if uid is not None:
                selected.append(uid)
            s.finish()
        kind, pile = sel.str("kind"), sel.str("pile")
        smin, smax, can_skip, prompt_key = sel.int("min"), sel.int("max"), sel.bool("can_skip"), sel.str("prompt_key")
        sel.finish()

        cards = []
        for c in r.items("cards"):
            uid = c.str("uid")
            selected_flag = c.bool("selected")
            for k in ("index", "type", "cost", "star_cost", "rarity", "is_upgradable", "max_upgrade_level"):
                c.drop(k, R_REDUNDANT)
            key = self.card_key(c)
            c.finish()
            cards.append(SelectCard(uid=uid, key=key, selected=selected_flag))
        canonical = False
        if pile == "DRAW":
            cards.sort(key=lambda sc: (sc.key.sort_key(), sc.uid or ""))
            canonical = True

        mode = r.str("mode") if screen == "hand_select" else r.str("screen_type")
        min_select, max_select = r.int("min_select"), r.int("max_select")  # card_select only
        if smin is None:
            smin = min_select
        if smax is None:
            smax = max_select
        for k in ("selected_cards", "selected_count", "required_count"):
            r.drop(k, R_REDUNDANT)
        for k in ("can_cancel", "preview_showing", "selected_outside_grid", "can_skip"):
            r.drop(k, R_ADAPTER)
        st = SelectionState(
            screen=screen,
            mode=mode,
            kind=kind,
            pile=pile,
            prompt_key=prompt_key,
            source_type=source[0],
            source_id=source[1],
            source_uid=source[2],
            min=smin,
            max=smax,
            can_skip=can_skip,
            can_confirm=r.bool("can_confirm"),
            selected=tuple(selected),
            cards=tuple(cards),
            cards_canonicalized=canonical,
        )
        r.finish()
        return st

    # ---- top level

    def run_info(self, r: _R) -> RunInfo:
        """`run` block (McpMod.StateBuilder.cs:692-701)."""
        r.drop("start_time", R_CLOCK)
        mc = r.obj("map_coord")
        col, row = mc.int("col"), mc.int("row")
        mc.finish()
        ri = RunInfo(
            act=r.int("act"),
            floor=r.int("floor"),
            ascension=r.int("ascension"),
            map_coord=(col, row) if col is not None and row is not None else None,
        )
        r.finish()
        return ri

    def meta(self, top: _R) -> PayloadMeta:
        """Build stamp and settle fields (McpMod.StateBuilder.cs:73-86, 103, 796-839; McpMod.Warnings.cs:79-88)."""
        warnings = top.raw("warnings")
        contexts: list[str] = []
        if isinstance(warnings, list):
            for w in warnings:
                if not isinstance(w, str):
                    continue
                ctx = "suppressed" if w.startswith("... ") else w.split(":", 1)[0].strip()
                contexts.append(ctx)
                self.flags.add(f"mod_warning:{ctx}")
        reasons = top.raw("resolving_reasons")
        return PayloadMeta(
            schema_version=top.int("schema_version"),
            mod_version=top.str("mod_version"),
            mod_commit=top.str("mod_commit"),
            action_log_seq=top.int("action_log_seq"),
            time_scale=top.num("time_scale"),
            rooms_entered=top.int("rooms_entered"),
            is_resolving=top.bool("is_resolving"),
            resolving_reasons=tuple(x for x in reasons if isinstance(x, str)) if isinstance(reasons, list) else (),
            warning_contexts=tuple(contexts),
        )

    def run(self, payload: dict[str, Any]) -> FirewallResult:
        if not isinstance(payload, dict):
            raise FirewallError("payload must be a JSON object")
        top = _R(payload, "", self.drops)
        state_type = top.str("state_type") or "unknown"
        meta = self.meta(top)
        if meta.schema_version != self.p.expected_schema_version:
            self.flags.add(f"schema_version_mismatch:{meta.schema_version}")
        if meta.is_resolving:
            self.flags.add("payload_resolving")

        in_combat = top.bool("in_combat")
        supported = state_type in COMBAT_SCREENS or state_type == "hand_select" or (
            state_type == "card_select" and in_combat is True
        )
        run = self.run_info(top.obj("run"))
        player = self.player(top.obj("player"))
        battle = None
        selection = None
        if supported:
            battle = self.battle(top.obj("battle"))
            if battle is None:
                self.flags.add("battle_missing")
            if state_type in SELECTION_SCREENS:
                selection = self.selection(state_type, top.obj(state_type))
        else:
            self.flags.add(f"unsupported_screen:{state_type}")
        top.finish()

        info = InfoState(
            state_type=state_type,
            supported=supported,
            run=run,
            player=player,
            battle=battle,
            selection=selection,
        )
        drops = self.drops.freeze()
        result = FirewallResult(
            info_state=info,
            drops=drops,
            flags=tuple(sorted(self.flags)),
            meta=meta,
            policy_hash=self.p.policy_hash,
        )
        for d in drops:
            log.debug("dropped %s x%d: %s", d.path, d.count, d.reason)
        log.info(
            "firewall %s: %d fields dropped across %d paths; flags=%s",
            state_type,
            sum(d.count for d in drops),
            len(drops),
            ",".join(result.flags) or "-",
        )
        return result


def apply_firewall(payload: dict[str, Any], policy: FirewallPolicy = DEFAULT_POLICY) -> FirewallResult:
    """Filter one STS2MCP GET /api/v1/singleplayer payload into an InfoState."""
    return _Firewall(policy).run(payload)


__all__ = [
    "EXPECTED_SCHEMA_VERSION",
    "FirewallPolicy",
    "DEFAULT_POLICY",
    "Drop",
    "PayloadMeta",
    "FirewallResult",
    "FirewallError",
    "apply_firewall",
]
