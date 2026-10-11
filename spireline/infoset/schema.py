"""InfoState: the only thing priors, values, features and search roots may read.

Every type here is a frozen, slotted dataclass built only from tuples, strings, ints,
bools, floats and None, so an InfoState is hashable and has one canonical JSON form.
`info_state_hash` is blake2b-256 over that form; CRN world seeds derive from it
(`det_seed`, design §2.1 worlds.py and §4.4 item 4), never from the game's seed.

The shapes follow what the firewall admits from the STS2MCP schema-4 payload
(r33hab/STS2MCP @ 5a63f92; see `firewall.py` for the per-field citations):

- piles (draw, discard, exhaust, play) and the master deck are **multisets** of
  `CardKey`: sorted `(CardKey, count)` pairs, no uid, no order;
- the hand is ordered (the game shows it in order) and keeps each card's uid, because
  actions name cards by uid (McpMod.StateBuilder.cs:1992; docs/raw-full.md:328-339);
- an enemy carries what is displayed plus the moves it has already executed
  (`state_log_executed`); `move_id` is filled only for monsters on the firewall's
  per-monster allow-list (initially empty), and `ai_fields` only with allow-listed keys.

`FrozenFields` is a sorted tuple of `(key, value)` pairs standing in for a small dict.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

SCHEMA_ID = "spireline-infostate/0"

Scalar = str | int | float | bool | None
FrozenFields = tuple[tuple[str, Scalar], ...]


def freeze_fields(d: dict[str, Scalar] | None) -> FrozenFields | None:
    if d is None:
        return None
    return tuple(sorted(d.items()))


# --------------------------------------------------------------------------- cards


@dataclass(frozen=True, slots=True)
class CardKey:
    """What identifies a card for play: id, upgrade, enchantment, affliction, cost overrides.

    Two cards with equal keys are interchangeable for every rule the player can see, so a
    pile is fully described by key counts. Display text (name, description, keywords) is
    derivable from the key and is not kept.
    """

    id: str
    upgrade_level: int = 0
    enchantment_id: str | None = None
    enchantment_amount: int | None = None
    affliction: str | None = None
    cost_overrides: FrozenFields = ()
    unplayable: bool | None = None

    def sort_key(self) -> tuple:
        return (
            self.id,
            self.upgrade_level,
            self.enchantment_id or "",
            -1 if self.enchantment_amount is None else self.enchantment_amount,
            self.affliction or "",
            self.cost_overrides,
            -1 if self.unplayable is None else int(self.unplayable),
        )


CardMultiset = tuple[tuple[CardKey, int], ...]


def multiset(keys: Iterable[CardKey]) -> CardMultiset:
    """Sorted (key, count) pairs. The input order is discarded by construction."""
    counts: dict[CardKey, int] = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    return tuple(sorted(counts.items(), key=lambda kv: kv[0].sort_key()))


def multiset_size(ms: CardMultiset) -> int:
    return sum(n for _, n in ms)


@dataclass(frozen=True, slots=True)
class DamageCap:
    capped_by: str | None = None
    power_id: str | None = None
    per_hit_max: int | None = None
    per_turn_max: int | None = None
    effective_damage: int | None = None


@dataclass(frozen=True, slots=True)
class TargetPreview:
    """`vs_targets[]`: the hover preview of a hand card against one living enemy."""

    target: str
    damage: int | None = None
    hits: int | None = None
    total_damage: int | None = None
    block: int | None = None
    damage_cap: DamageCap | None = None


@dataclass(frozen=True, slots=True)
class HandCard:
    uid: str
    key: CardKey
    type: str | None = None
    cost: str | None = None
    star_cost: str | None = None
    target_type: str | None = None
    can_play: bool | None = None
    unplayable_reason: str | None = None
    vs_targets: tuple[TargetPreview, ...] = ()


# --------------------------------------------------------------------------- creatures


@dataclass(frozen=True, slots=True)
class Power:
    id: str
    amount: int | None
    type: str | None = None
    display_amount: int | None = None
    fields: FrozenFields | None = ()


@dataclass(frozen=True, slots=True)
class Intent:
    """An intent as displayed: category, label and hover tip, attack numbers."""

    type: str
    label: str | None = None
    title: str | None = None
    description: str | None = None
    damage: int | None = None
    base_damage: int | None = None
    hits: int | None = None


@dataclass(frozen=True, slots=True)
class Revive:
    power_id: str | None = None
    hp: int | None = None
    in_turns: int | None = None  # only for powers on the firewall's revive allow-list


@dataclass(frozen=True, slots=True)
class Creature:
    """An enemy, or an ally such as Osty, as the firewall admits it."""

    entity_id: str
    monster_id: str
    alive: bool
    hp: int
    max_hp: int
    block: int
    powers: tuple[Power, ...] = ()
    intents: tuple[Intent, ...] = ()
    is_stunned: bool | None = None
    slot: int | None = None
    state_log_executed: tuple[str, ...] | None = None
    move_id: str | None = None  # None unless the monster is on the move_id allow-list
    ai_fields: FrozenFields = ()  # allow-listed keys only
    revive: Revive | None = None


@dataclass(frozen=True, slots=True)
class Orb:
    id: str
    passive_val: int | None = None
    evoke_val: int | None = None


@dataclass(frozen=True, slots=True)
class Pet:
    id: str
    alive: bool
    hp: int
    max_hp: int
    block: int
    powers: tuple[Power, ...] = ()


@dataclass(frozen=True, slots=True)
class Relic:
    id: str
    counter: int | None = None
    status: str | None = None
    is_used_up: bool | None = None
    stack_count: int | None = None
    saved: FrozenFields = ()  # allow-listed keys only
    fields: FrozenFields = ()  # allow-listed keys only


@dataclass(frozen=True, slots=True)
class Potion:
    id: str
    slot: int
    can_use_in_combat: bool | None = None
    target_type: str | None = None


# --------------------------------------------------------------------------- blocks


@dataclass(frozen=True, slots=True)
class RunInfo:
    act: int | None = None
    floor: int | None = None
    ascension: int | None = None
    map_coord: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class PlayerState:
    character_id: str | None
    hp: int
    max_hp: int
    block: int
    gold: int | None = None
    energy: int | None = None
    max_energy: int | None = None
    stars: int | None = None
    hand: tuple[HandCard, ...] = ()
    draw_pile: CardMultiset = ()
    discard_pile: CardMultiset = ()
    exhaust_pile: CardMultiset = ()
    play_pile: CardMultiset = ()
    draw_pile_count: int | None = None
    discard_pile_count: int | None = None
    exhaust_pile_count: int | None = None
    orbs: tuple[Orb, ...] = ()  # ordered: evocation order is on screen
    orb_slots: int | None = None
    orb_empty_slots: int | None = None
    pets: tuple[Pet, ...] = ()
    powers: tuple[Power, ...] = ()
    relics: tuple[Relic, ...] = ()
    potions: tuple[Potion, ...] = ()
    max_potion_slots: int | None = None
    deck_count: int | None = None
    deck: CardMultiset = ()


@dataclass(frozen=True, slots=True)
class BattleState:
    round: int | None
    turn: str | None
    is_play_phase: bool | None
    enemies: tuple[Creature, ...] = ()
    allies: tuple[Creature, ...] = ()
    history: FrozenFields | None = None


@dataclass(frozen=True, slots=True)
class SelectCard:
    uid: str | None
    key: CardKey
    selected: bool | None = None


@dataclass(frozen=True, slots=True)
class SelectionState:
    """hand_select / in-combat card_select, game terms only (no localized prompt)."""

    screen: str  # "hand_select" | "card_select"
    mode: str | None = None  # hand_select.mode or card_select.screen_type
    kind: str | None = None  # HAND | GRID | CHOOSE
    pile: str | None = None  # DRAW | DISCARD | EXHAUST | None
    prompt_key: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    source_uid: str | None = None
    min: int | None = None
    max: int | None = None
    can_skip: bool | None = None
    can_confirm: bool | None = None
    selected: tuple[str, ...] = ()  # uids, in pick order (shown on screen)
    cards: tuple[SelectCard, ...] = ()
    cards_canonicalized: bool = False  # True when screen order was replaced (draw-pile grid)


@dataclass(frozen=True, slots=True)
class InfoState:
    """Canonical, firewall-filtered information state for one decision point.

    Holds a single observation. The history part of I_t that the game keeps on screen
    (moves executed, card plays this turn and combat) is inside it; the full tape
    canon(o_0, a_0, ..., o_t) is assembled by the live adapter (Phase 1).
    """

    state_type: str
    supported: bool
    run: RunInfo
    player: PlayerState | None
    battle: BattleState | None = None
    selection: SelectionState | None = None
    schema: str = SCHEMA_ID

    def to_jsonable(self) -> dict[str, Any]:
        return _jsonable(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_jsonable(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @property
    def info_state_hash(self) -> str:
        return hashlib.blake2b(self.canonical_json().encode("utf-8"), digest_size=32).hexdigest()


def _jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, (tuple, list)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, float) and obj != obj:  # NaN has no canonical JSON form
        raise ValueError("NaN in InfoState")
    return obj


def det_seed(info_state_hash: str, k: int, *, digest_size: int = 8) -> int:
    """CRN world seed k for a position: blake2b(info_state_hash, k) as an unsigned int.

    Synthetic and derived only from the information state (design §4.4 item 4), so the
    same position always gets the same world bank and the game's seed never enters.
    """
    if k < 0:
        raise ValueError("k must be >= 0")
    h = hashlib.blake2b(digest_size=digest_size, person=b"spireline-crn")
    h.update(info_state_hash.encode("ascii"))
    h.update(k.to_bytes(8, "little"))
    return int.from_bytes(h.digest(), "little")


__all__ = [
    "SCHEMA_ID",
    "Scalar",
    "FrozenFields",
    "freeze_fields",
    "CardKey",
    "CardMultiset",
    "multiset",
    "multiset_size",
    "DamageCap",
    "TargetPreview",
    "HandCard",
    "Power",
    "Intent",
    "Revive",
    "Creature",
    "Orb",
    "Pet",
    "Relic",
    "Potion",
    "RunInfo",
    "PlayerState",
    "BattleState",
    "SelectCard",
    "SelectionState",
    "InfoState",
    "det_seed",
]
